import { adminIdentity, apiIdentity, bearer, createAdminSession, enforceRateLimit, rateLimitKey, verifyAdminCredentials } from "./auth.js";
import { HttpError, MAX_BODY, bounded, clientMetadata, json, publicCachedJson, readJson, sha256Hex } from "./http.js";
import { classifyClient, enqueueActivities, enqueueActivity } from "./telemetry.js";
import { invokeChatProvider, providerConfiguration, testOllamaProvider } from "./providers.js";
import { browserReferenceName, classifyBrowserReference, normalizeBrowserMetrics } from "./reference-gate.js";
import { EDITABLE_WEBSITE_FILES, readApprovedSourceFile, saveApprovedSourceFile, sourceControlStatus, validateSourceDraft } from "./source-control.js";
import { publicRelease, publicReleaseManifest, releaseAsset, releaseForChannel } from "../release-manifest.js";
import { backendActionCatalog, chatSettingsPayload, executeAdminCommand, historicalSales, removeCatalogTrack, saveChatSettings, saveRuntimeProviderConfig, testRuntimeProvider, uploadCatalogAudio, uploadLicensedReference } from "./admin-tools.js";

const RELEASE_CACHE_SECONDS = 900;
const MODEL_CACHE_SECONDS = 900;
const REFERENCE_CACHE_SECONDS = 300;
const METRICS = [
  ["sample_peak", "dBFS"], ["rms", "dBFS"], ["true_peak", "dBTP"],
  ["momentary_loudness", "LUFS"], ["short_term_loudness", "LUFS"], ["integrated_loudness", "LUFS"],
  ["loudness_range", "LU"], ["broadband_crest", "dB"], ["correlation", "ratio"],
  ["left_energy", "dBFS"], ["right_energy", "dBFS"], ["mid_energy", "dBFS"], ["side_energy", "dBFS"],
  ["left_right_balance", "dB"], ["side_to_mid", "dB"], ["width", "percent"]
];
const BAND_CENTRES = [20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 350, 450, 600, 750, 850, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, 18000, 20000];
const PROFILE_REVISIONS = new Map([
  ["MIX_BALANCED", 1],
  ["SPECTRUM_SURGICAL", 1],
  ["MASTERING_PRECISION", 1],
  ["STEREO_PHASE_DIAGNOSTIC", 2]
]);

function pathAfterApi(pathname) {
  if (pathname === "/api") return "/";
  return pathname.startsWith("/api/") ? pathname.slice(4) : pathname;
}

export function requestedReleaseChannel(request, fallback = "beta") {
  const value = bounded(new URL(request.url).searchParams.get("channel") || fallback, 20).toLowerCase();
  if (value !== "beta" && value !== "flagship") {
    throw new HttpError(400, "invalid_release_channel", "release channel must be beta or flagship");
  }
  return value;
}

function requireMethod(request, ...methods) {
  if (!methods.includes(request.method)) throw new HttpError(405, "method_not_allowed", "method not allowed", { allow: methods.join(", ") });
}

async function authenticateClientOrAdmin(request, env) {
  if (bearer(request).includes(".")) return adminIdentity(request, env);
  return apiIdentity(request, env);
}

async function analyticsIdentity(request, env) {
  if (bearer(request)) return apiIdentity(request, env, true);
  const origin = bounded(request.headers.get("origin"), 200);
  const fetchSite = bounded(request.headers.get("sec-fetch-site"), 24);
  const allowedOrigins = new Set([new URL(request.url).origin, env.AIFRED_PUBLIC_ORIGIN, "https://north3rnlight3r.com", "https://www.north3rnlight3r.com"]);
  if (!allowedOrigins.has(origin) || !new Set(["same-origin", "same-site"]).has(fetchSite)) {
    throw new HttpError(401, "authentication_required", "valid analytics authentication or same-site browser context is required");
  }
  const declared = bounded(request.headers.get("x-aifred-client"), 96);
  const key = await rateLimitKey(request);
  return { clientKey: await sha256Hex(`web:${key}:${declared}`), declared: declared || "website" };
}

async function useIdempotency(request, env, route, clientKey, ttlMinutes = 15) {
  const supplied = bounded(request.headers.get("idempotency-key"), 128);
  if (!supplied) throw new HttpError(400, "idempotency_key_required", "Idempotency-Key is required");
  const key = await sha256Hex(`${route}\n${clientKey}\n${supplied}`);
  const now = new Date();
  const expiresAt = new Date(now.getTime() + ttlMinutes * 60 * 1000).toISOString();
  await env.AIFRED_OPS.prepare("DELETE FROM idempotency_keys WHERE key = ? AND expires_at <= ?").bind(key, now.toISOString()).run();
  const result = await env.AIFRED_OPS.prepare(`
    INSERT INTO idempotency_keys (key, route, client_key, state, created_at, expires_at)
    VALUES (?, ?, ?, 'pending', ?, ?)
    ON CONFLICT(key) DO NOTHING
  `).bind(key, route, clientKey, now.toISOString(), expiresAt).run();
  if (Number(result.meta?.changes || 0) !== 1) throw new HttpError(409, "duplicate_request", "this operation is already in progress or complete");
  return {
    key,
    complete: () => env.AIFRED_OPS.prepare("UPDATE idempotency_keys SET state = 'complete' WHERE key = ?").bind(key).run(),
    abandon: () => env.AIFRED_OPS.prepare("DELETE FROM idempotency_keys WHERE key = ? AND state = 'pending'").bind(key).run()
  };
}

function normalizeMessages(body) {
  if (!Array.isArray(body.messages) || body.messages.length < 1 || body.messages.length > 50) {
    throw new HttpError(400, "invalid_messages", "messages must contain 1 to 50 items");
  }
  let total = 0;
  const messages = body.messages.map((item) => {
    const role = bounded(item?.role, 16);
    if (!new Set(["system", "user", "assistant", "tool"]).has(role)) throw new HttpError(400, "invalid_role", "unsupported message role");
    const content = Array.isArray(item.content)
      ? item.content.map((part) => bounded(part?.text, 24000)).join("")
      : bounded(item.content, 24000);
    total += content.length;
    return { role, content };
  });
  if (total > 80000) throw new HttpError(413, "prompt_too_large", "combined message content is too large");
  return messages;
}

function extractFilteredContext(messages) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index].role !== "user") continue;
    try {
      const parsed = JSON.parse(messages[index].content);
      if (parsed?.context?.schema === "aifred.filtered-mix.v1") return parsed.context;
    } catch {}
  }
  return null;
}

export function validateFilteredContext(context) {
  if (!context || context.schema !== "aifred.filtered-mix.v1") throw new HttpError(400, "measurement_context_required", "aifred.filtered-mix.v1 context is required");
  for (const field of ["product_channel", "product_version", "plugin_instance_id", "session_id", "profile_id", "observation_id"]) {
    if (!bounded(context[field], 160)) throw new HttpError(400, "invalid_measurement_context", `context.${field} is required`);
  }
  if (!Array.isArray(context.metrics) || context.metrics.length !== 16 || !Array.isArray(context.bands) || context.bands.length !== 30) {
    throw new HttpError(400, "invalid_measurement_context", "context must contain the 16 metric and 30 band FilteredMixContext payload");
  }
  if (!new Set(["beta", "official"]).has(context.product_channel)) throw new HttpError(400, "invalid_measurement_context", "context.product_channel must be beta or official");
  const revision = PROFILE_REVISIONS.get(context.profile_id);
  if (!revision || context.profile_version !== revision) throw new HttpError(400, "invalid_measurement_context", "context profile identity or revision is unsupported");
  if (Array.isArray(context.session_context) && context.session_context.length > 4) throw new HttpError(400, "invalid_measurement_context", "context session history exceeds its bound");
  for (let index = 0; index < METRICS.length; index += 1) {
    const metric = context.metrics[index];
    const [name, unit] = METRICS[index];
    if (!metric || metric.metric !== name || metric.unit !== unit || typeof metric.available !== "boolean" || "centre_hz" in metric) {
      throw new HttpError(400, "invalid_measurement_context", `context.metrics[${index}] identity, unit, or availability is invalid`);
    }
  }
  for (let index = 0; index < BAND_CENTRES.length; index += 1) {
    const band = context.bands[index];
    if (!band || band.metric !== "band_energy" || band.unit !== "dBFS" || typeof band.available !== "boolean" || band.centre_hz !== BAND_CENTRES[index]) {
      throw new HttpError(400, "invalid_measurement_context", `context.bands[${index}] frequency contract is invalid`);
    }
  }
  return context;
}

async function health(request) {
  requireMethod(request, "GET", "HEAD");
  return json({
    ok: true,
    service: "aifred-site",
    status: "healthy",
    api_version: "v1",
    timestamp: new Date().toISOString()
  }, { headers: { "cache-control": "no-cache, max-age=0" } });
}

async function loadCatalog(request, env) {
  const assetRequest = new Request(new URL("/assets/data/beat_catalog.json", request.url), {
    headers: { accept: "application/json" }
  });
  const response = await env.ASSETS.fetch(assetRequest);
  if (!response.ok) throw new HttpError(502, "catalog_unavailable", "the public catalog is unavailable");
  const body = await response.json();
  if (!Array.isArray(body)) throw new HttpError(502, "catalog_invalid", "the public catalog is invalid");
  return body.slice(0, 500);
}

async function catalog(request, env, ctx) {
  requireMethod(request, "GET", "HEAD");
  return publicCachedJson(request, ctx, async () => {
    const tracks = await loadCatalog(request, env);
    return { ok: true, tracks, count: tracks.length };
  }, MODEL_CACHE_SECONDS, 3600);
}

async function models(request, env, ctx) {
  requireMethod(request, "GET", "HEAD");
  const configured = [env.OLLAMA_MODEL || env.OLLMA_MODEL, env.OPENAI_MODEL].filter(Boolean);
  const created = Math.floor(Date.now() / 1000);
  return publicCachedJson(request, ctx, {
    object: "list",
    data: [...new Set(configured)].map((id) => ({ id, object: "model", created, owned_by: id.startsWith("gpt-") ? "openai" : "aifred" }))
  }, MODEL_CACHE_SECONDS, 3600);
}

async function releases(request, env, ctx, currentOnly) {
  requireMethod(request, "GET", "HEAD");
  return publicCachedJson(request, ctx, () => {
    const channel = requestedReleaseChannel(request);
    return currentOnly
      ? { ok: true, release: publicRelease(releaseForChannel(channel)) }
      : { ok: true, releases: publicReleaseManifest() };
  }, RELEASE_CACHE_SECONDS, 3600);
}

async function references(request, env, ctx, trace) {
  if (request.method === "GET" || request.method === "HEAD") {
    return publicCachedJson(request, ctx, async () => {
      const records = await loadReferenceRecords(env, 500);
      return {
        ok: true,
        schema: "aifred.reference-pool.public.v1",
        contract_version: "aifred.references.v1",
        references: records,
        records,
        reference: records[0] || null,
        count: records.length,
        source: "aifred-ops.references_catalog",
        reason: records.length ? "" : "No usable references are available."
      };
    }, REFERENCE_CACHE_SECONDS, 900);
  }
  requireMethod(request, "POST");
  const identity = await apiIdentity(request, env);
  const outcome = await enforceRateLimit(env.REFERENCE_RATE_LIMITER, await rateLimitKey(request, identity), {
    db: env.AIFRED_OPS, scope: "reference", limit: 20
  });
  const body = await readJson(request, MAX_BODY.reference);
  const idempotency = await useIdempotency(request, env, "/v1/references", identity.clientKey, 60);
  try {
    const id = bounded(body.id, 128) || crypto.randomUUID();
    const name = bounded(body.name, 200);
    if (!name || !body.metrics || typeof body.metrics !== "object") throw new HttpError(400, "invalid_reference", "name and metrics are required");
    const record = {
      available: true,
      id,
      name,
      version: bounded(body.version, 40),
      created_at: new Date().toISOString(),
      metrics: body.metrics,
      classification: body.classification && typeof body.classification === "object" ? body.classification : {}
    };
    const serialized = JSON.stringify(record);
    if (serialized.length > 200000) throw new HttpError(413, "reference_too_large", "reference record is too large");
    await env.AIFRED_OPS.prepare(`
      INSERT INTO references_catalog (id, name, version, created_at, metrics_json, classification_json, active)
      VALUES (?, ?, ?, ?, ?, ?, 1)
      ON CONFLICT(id) DO UPDATE SET
        name = excluded.name,
        version = excluded.version,
        created_at = excluded.created_at,
        metrics_json = excluded.metrics_json,
        classification_json = excluded.classification_json,
        active = 1
    `).bind(id, name, record.version, record.created_at, JSON.stringify(record.metrics), JSON.stringify(record.classification)).run();
    trace.d1Writes += 1;
    ctx.waitUntil(enqueueActivity(env, {
      id: crypto.randomUUID(),
      created_at: record.created_at,
      event_type: "reference.upload.accepted",
      request_id: trace.requestId,
      product: trace.product,
      channel: trace.channel,
      version: trace.version,
      route: "/v1/references",
      method: "POST",
      status: 201,
      metadata: { reference_id: id, name, version: record.version }
    }));
    await idempotency.complete();
    return json({ ok: true, id, contract_version: "aifred.references.v1", rate_limit: outcome }, { status: 201 });
  } catch (error) {
    await idempotency.abandon();
    throw error;
  }
}

async function loadReferenceRecords(env, limit) {
  const result = await env.AIFRED_OPS.prepare(`
    SELECT id, name, version, created_at, metrics_json, classification_json
    FROM references_catalog WHERE active = 1 ORDER BY created_at DESC LIMIT ?
  `).bind(limit).all();
  return (result.results || []).map((row) => ({
    available: true,
    id: row.id,
    name: row.name,
    version: row.version,
    created_at: row.created_at,
    metrics: JSON.parse(row.metrics_json),
    classification: JSON.parse(row.classification_json)
  }));
}

async function websiteAnalysis(request, env, ctx, trace) {
  requireMethod(request, "POST");
  trace.rateLimitOutcome = await enforceRateLimit(env.ANALYSIS_RATE_LIMITER, await rateLimitKey(request), { db: env.AIFRED_OPS, scope: "website-analysis", limit: 10 });
  const body = await readJson(request, MAX_BODY.analysis);
  const metrics = normalizeBrowserMetrics(body);
  const gate = classifyBrowserReference(metrics);
  const analysisId = crypto.randomUUID();
  const createdAt = new Date().toISOString();
  let persistence = "disposed";

  if (gate.accepted) {
    const durationSeconds = Math.max(0, Math.min(86400, Number(body.duration_seconds || 0)));
    const classification = { ...gate, duration_seconds: Number.isFinite(durationSeconds) ? durationSeconds : 0, source: "website-analyzer" };
    await env.AIFRED_OPS.prepare(`
      INSERT INTO references_catalog (id, name, version, created_at, metrics_json, classification_json, active)
      VALUES (?, ?, ?, ?, ?, ?, 1)
      ON CONFLICT(id) DO UPDATE SET
        name = excluded.name,
        version = excluded.version,
        created_at = excluded.created_at,
        metrics_json = excluded.metrics_json,
        classification_json = excluded.classification_json,
        active = 1
    `).bind(analysisId, browserReferenceName(analysisId), "website-analyzer.v1", createdAt, JSON.stringify(metrics), JSON.stringify(classification)).run();
    trace.d1Writes += 1;
    persistence = "stored";
  }

  ctx.waitUntil(enqueueActivity(env, {
    id: crypto.randomUUID(),
    created_at: createdAt,
    event_type: "website.analysis.submitted",
    request_id: bounded(body.request_id, 128) || trace.requestId,
    product: "aifred-website",
    channel: "beta",
    platform: "browser",
    route: "/v1/analysis/submit",
    method: "POST",
    status: 200,
    metadata: { analysis_id: analysisId, accepted: gate.accepted, score: gate.score, classification: gate.classification, persistence }
  }));

  return json({
    ok: true,
    accepted: gate.accepted,
    score: gate.score,
    classification: gate.classification,
    reference_utility: gate.reference_utility,
    technical_caution: gate.technical_caution,
    style_tag: gate.style_tag,
    best_use: gate.best_use,
    caution: gate.caution,
    why: gate.why,
    action: gate.accepted ? "metadata stored in the AIFRED reference pool" : "metadata rejected or kept out of the pool",
    persistence,
    checks: gate.checks,
    analysis_id: gate.accepted ? analysisId : null
  });
}

async function analysis(request, env, trace) {
  requireMethod(request, "POST");
  const identity = await apiIdentity(request, env);
  trace.clientKey = identity.clientKey.slice(0, 32);
  trace.rateLimitOutcome = await enforceRateLimit(env.ANALYSIS_RATE_LIMITER, await rateLimitKey(request, identity), {
    db: env.AIFRED_OPS, scope: "analysis", limit: 10
  });
  const body = await readJson(request, MAX_BODY.analysis);
  const context = validateFilteredContext(body.context || body.filtered_mix_context || body);
  const idempotency = await useIdempotency(request, env, "/v1/analysis", identity.clientKey, 60);
  try {
    const eventId = crypto.randomUUID();
    await enqueueActivity(env, {
      id: eventId,
      event_type: "analysis.submitted",
      request_id: trace.requestId,
      product: bounded(body.product || "aifred", 40),
      channel: bounded(context.product_channel, 24),
      version: bounded(body.version, 40),
      platform: bounded(body.platform, 40),
      route: "/v1/analysis",
      method: "POST",
      status: 202,
      metadata: {
        context_schema: context.schema,
        profile_id: bounded(context.profile_id, 160),
        plugin_instance_id_hash: (await sha256Hex(context.plugin_instance_id)).slice(0, 24),
        session_id_hash: (await sha256Hex(context.session_id)).slice(0, 24)
      }
    });
    trace.d1Writes += 1;
    await idempotency.complete();
    return json({ ok: true, accepted: true, analysis_id: eventId, context_schema: context.schema }, { status: 202 });
  } catch (error) {
    await idempotency.abandon();
    throw error;
  }
}

async function chat(request, env, trace) {
  requireMethod(request, "POST");
  const identity = await authenticateClientOrAdmin(request, env);
  trace.clientKey = identity.clientKey.slice(0, 32);
  trace.rateLimitOutcome = await enforceRateLimit(env.CHAT_RATE_LIMITER, await rateLimitKey(request, identity), {
    db: env.AIFRED_OPS, scope: "chat", limit: 15
  });
  const body = await readJson(request, MAX_BODY.chat);
  const messages = normalizeMessages(body);
  if (!bearer(request).includes(".")) validateFilteredContext(extractFilteredContext(messages));
  const idempotency = await useIdempotency(request, env, "/v1/chat/completions", identity.clientKey, 30);
  try {
    const { provider, response: providerResponse } = await invokeChatProvider(env, { ...body, messages });
    trace.provider = provider;
    trace.providerCalls += 1;
    await idempotency.complete();
    const headers = new Headers({ "cache-control": "no-store" });
    headers.set("content-type", providerResponse.headers.get("content-type") || "application/json; charset=utf-8");
    return new Response(providerResponse.body, { status: providerResponse.status, headers });
  } catch (error) {
    await idempotency.abandon();
    throw error;
  }
}

function normalizeEvent(value, common) {
  if (!value || typeof value !== "object") throw new HttpError(400, "invalid_event", "each analytics event must be an object");
  const eventType = bounded(value.event_type || value.type, 96);
  if (!/^[a-z0-9][a-z0-9._-]{1,95}$/i.test(eventType)) throw new HttpError(400, "invalid_event_type", "analytics event type is invalid");
  return {
    id: bounded(value.id || value.event_id, 128) || crypto.randomUUID(),
    created_at: new Date().toISOString(),
    event_type: eventType,
    product: bounded(value.product || common.product, 40),
    channel: bounded(value.channel || common.channel, 24),
    version: bounded(value.version || common.version, 40),
    platform: bounded(value.platform || common.platform, 40),
    route: "/v1/analytics/events",
    method: "POST",
    status: 202,
    metadata: sanitizeEventMetadata(value.metadata)
  };
}

function sanitizeEventMetadata(metadata) {
  if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) return {};
  const allowed = new Set(["surface", "action", "category", "result", "feature", "artifact", "source", "count", "duration_ms", "size_bytes"]);
  const output = {};
  for (const [key, value] of Object.entries(metadata)) {
    if (!allowed.has(key)) continue;
    if (typeof value === "number" && Number.isFinite(value)) output[key] = value;
    else if (typeof value === "string") output[key] = bounded(value, 160);
    else if (typeof value === "boolean") output[key] = value;
  }
  return output;
}

async function analytics(request, env, trace) {
  requireMethod(request, "POST");
  const identity = await analyticsIdentity(request, env);
  trace.clientKey = identity.clientKey.slice(0, 32);
  trace.rateLimitOutcome = await enforceRateLimit(env.ANALYTICS_RATE_LIMITER, await rateLimitKey(request, identity), {
    db: env.AIFRED_OPS, scope: "analytics", limit: 20
  });
  const body = await readJson(request, MAX_BODY.analytics);
  const rawEvents = Array.isArray(body.events) ? body.events : [];
  if (rawEvents.length < 1 || rawEvents.length > 50) throw new HttpError(400, "invalid_batch", "analytics batches must contain 1 to 50 events");
  const common = clientMetadata(request, body);
  const events = rawEvents.map((event) => normalizeEvent(event, common));
  const idempotency = await useIdempotency(request, env, "/v1/analytics/events", identity.clientKey, 24 * 60);
  try {
    await enqueueActivities(env, events);
    trace.d1Writes += events.length;
    await idempotency.complete();
    return json({ ok: true, accepted: events.length, batch_id: bounded(request.headers.get("idempotency-key"), 128) }, { status: 202 });
  } catch (error) {
    await idempotency.abandon();
    throw error;
  }
}

async function inquiry(request, env, trace) {
  requireMethod(request, "POST");
  const key = await rateLimitKey(request);
  trace.rateLimitOutcome = await enforceRateLimit(env.INQUIRY_RATE_LIMITER, key, {
    db: env.AIFRED_OPS, scope: "inquiry", limit: 5
  });
  const body = await readJson(request, MAX_BODY.inquiry);
  const name = bounded(body.name, 160);
  const email = bounded(body.email, 254);
  const message = bounded(body.message, 6000);
  if (!name || !/^\S+@\S+\.\S+$/.test(email) || !message) throw new HttpError(400, "invalid_inquiry", "valid name, email, and message are required");
  const idempotency = await useIdempotency(request, env, "/v1/inquiries", key, 24 * 60);
  try {
    const id = crypto.randomUUID();
    const createdAt = new Date().toISOString();
    await env.AIFRED_OPS.prepare("INSERT INTO inquiries (id, created_at, name, email, message, status) VALUES (?, ?, ?, ?, ?, 'new')")
      .bind(id, createdAt, name, email, message).run();
    trace.d1Writes += 1;
    await enqueueActivity(env, { id: crypto.randomUUID(), created_at: createdAt, event_type: "inquiry.submitted", request_id: trace.requestId, route: "/v1/inquiries", method: "POST", status: 201 });
    trace.d1Writes += 1;
    await idempotency.complete();
    return json({ ok: true, inquiry_id: id }, { status: 201 });
  } catch (error) {
    await idempotency.abandon();
    throw error;
  }
}

async function adminLogin(request, env, trace) {
  requireMethod(request, "POST");
  const key = await rateLimitKey(request);
  trace.rateLimitOutcome = await enforceRateLimit(env.ADMIN_LOGIN_RATE_LIMITER, key, {
    db: env.AIFRED_OPS, scope: "admin-login", limit: 5
  });
  const body = await readJson(request, MAX_BODY.login);
  const username = bounded(body.username, 128);
  const password = String(body.password || "").slice(0, 1024);
  if (!(await verifyAdminCredentials(username, password, env))) throw new HttpError(401, "invalid_credentials", "invalid admin credentials");
  const session = await createAdminSession(username, env);
  trace.d1Writes += 1;
  const headers = {
    "set-cookie": `aifred_admin=${session.token}; Path=/; Max-Age=43200; Secure; HttpOnly; SameSite=Strict`,
    "cache-control": "no-store"
  };
  return json({ ok: true, username, session_token: session.token, expires_at: session.expiresAt, token_type: "Bearer" }, { headers });
}

async function adminLogout(request, env, trace) {
  requireMethod(request, "POST");
  const identity = await adminIdentity(request, env);
  await env.AIFRED_OPS.prepare("DELETE FROM admin_sessions WHERE id = ?").bind(identity.id).run();
  trace.d1Writes += 1;
  return json({ ok: true }, { headers: { "set-cookie": "aifred_admin=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Strict" } });
}

async function adminData(request, env, path, trace) {
  const postPaths = new Set([
    "/v1/admin/api/config",
    "/v1/admin/api/test",
    "/v1/admin/catalog/remove",
    "/v1/admin/catalog/upload",
    "/v1/admin/chat/settings/save",
    "/v1/admin/provider/test",
    "/v1/admin/providers/ollama/test",
    "/v1/admin/reference/upload",
    "/v1/admin/source/read",
    "/v1/admin/source/validate",
    "/v1/admin/source/save"
  ]);
  const providerTestPath = path === "/v1/admin/provider/test" || path === "/v1/admin/providers/ollama/test";
  if (postPaths.has(path)) requireMethod(request, "POST");
  else requireMethod(request, "GET", "HEAD");
  const identity = trace.adminIdentity || await adminIdentity(request, env);
  trace.adminIdentity = identity;
  trace.clientKey = identity.clientKey.slice(0, 32);
  if (!trace.adminRateLimitChecked) {
    trace.rateLimitOutcome = await enforceRateLimit(env.ADMIN_RATE_LIMITER, identity.clientKey, {
      db: env.AIFRED_OPS, scope: "admin", limit: 60
    });
    trace.adminRateLimitChecked = true;
  }
  if (path === "/v1/admin/status" || path === "/v1/admin/ops/status") {
    const providers = providerConfiguration(env);
    return json({ ok: true, service: "aifred-site", api_version: "v1", authority: "kaeganscott26/AIFRED_Official-", architecture: "pages-advanced-mode", storage: { d1: Boolean(env.AIFRED_OPS), queue: false, analytics_engine: Boolean(env.AIFRED_ANALYTICS), historical_kv_read_only: Boolean(env.AIFRED_SALES_LOG), r2: Boolean(env.AIFRED_DOWNLOADS) }, provider: { active: providers.active, configured: providers.providers.some((item) => item.id === providers.active && item.configured), tested: false } });
  }
  if (path === "/v1/admin/api/config") {
    return json(await saveRuntimeProviderConfig(env, await readJson(request, MAX_BODY.provider)));
  }
  if (path === "/v1/admin/api/test") {
    const result = await testRuntimeProvider(env, await readJson(request, MAX_BODY.provider));
    trace.providerCalls += 1;
    trace.provider = result.provider || "";
    return json({ ok: Boolean(result.ok), ...result, message: result.ok ? `${result.provider || "provider"} is reachable` : `${result.provider || "provider"} test failed` }, { status: result.ok ? 200 : 502 });
  }
  if (path === "/v1/admin/chat/settings/save") {
    const settings = await saveChatSettings(env, await readJson(request, MAX_BODY.settings));
    const payload = await chatSettingsPayload(request, env, true);
    return json({ ...payload, settings });
  }
  if (path === "/v1/admin/chat/settings") {
    return json(await chatSettingsPayload(request, env, true));
  }
  if (path === "/v1/admin/catalog/upload") {
    const result = await uploadCatalogAudio(request, env);
    await enqueueActivity(env, {
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      event_type: "admin.catalog_upload.accepted",
      request_id: trace.requestId,
      route: path,
      method: "POST",
      status: 201,
      metadata: { stored_path: result.stored_path, title: result.track?.title || "", commit_sha: result.commit || "" }
    });
    trace.d1Writes += 1;
    return json(result, { status: 201 });
  }
  if (path === "/v1/admin/catalog/remove") {
    const body = await readJson(request, MAX_BODY.provider);
    const result = await removeCatalogTrack(env, body.key);
    await enqueueActivity(env, {
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      event_type: "admin.catalog_track.removed",
      request_id: trace.requestId,
      route: path,
      method: "POST",
      status: 200,
      metadata: { key: result.removed, commit_sha: result.commit || "" }
    });
    trace.d1Writes += 1;
    return json(result);
  }
  if (path === "/v1/admin/reference/upload") {
    const result = await uploadLicensedReference(request, env);
    await enqueueActivity(env, {
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      event_type: "reference.upload.accepted",
      request_id: trace.requestId,
      route: path,
      method: "POST",
      status: 201,
      metadata: { stored_path: result.stored_path, genre: result.genre, title: result.title }
    });
    trace.d1Writes += 1;
    return json(result, { status: 201 });
  }
  if (path === "/v1/admin/analytics") {
    const since = new Date(Date.now() - 60 * 60 * 1000).toISOString().slice(0, 16) + ":00.000Z";
    const [summary, routes, clients, minutes, lifetimeEvents, dailyEvents] = await env.AIFRED_OPS.batch([
      env.AIFRED_OPS.prepare("SELECT SUM(requests) requests, SUM(CASE WHEN status=429 THEN requests ELSE 0 END) rate_limited, SUM(CASE WHEN status>=400 THEN requests ELSE 0 END) errors, SUM(provider_calls) provider_calls, SUM(d1_writes) d1_writes, SUM(queue_events) queue_events, SUM(r2_downloads) r2_downloads, SUM(CASE WHEN cache_status='HIT' THEN requests ELSE 0 END) cache_hits, SUM(CASE WHEN cache_status='MISS' THEN requests ELSE 0 END) cache_misses FROM request_rollups WHERE minute >= ?").bind(since),
      env.AIFRED_OPS.prepare("SELECT route, SUM(requests) requests FROM request_rollups WHERE minute >= ? GROUP BY route ORDER BY requests DESC LIMIT 20").bind(since),
      env.AIFRED_OPS.prepare("SELECT client_key, SUM(requests) requests FROM request_rollups WHERE minute >= ? GROUP BY client_key ORDER BY requests DESC LIMIT 20").bind(since),
      env.AIFRED_OPS.prepare("SELECT minute, SUM(requests) requests FROM request_rollups WHERE minute >= ? GROUP BY minute ORDER BY minute DESC LIMIT 60").bind(since),
      env.AIFRED_OPS.prepare("SELECT event_type, SUM(count) count, MAX(last_seen) last_seen FROM analytics_rollups GROUP BY event_type ORDER BY count DESC"),
      env.AIFRED_OPS.prepare("SELECT day, event_type, SUM(count) count FROM analytics_rollups GROUP BY day, event_type ORDER BY day DESC, count DESC LIMIT 180")
    ]);
    const totals = summary.results?.[0] || {};
    const denominator = Number(totals.cache_hits || 0) + Number(totals.cache_misses || 0);
    const lifetimeByType = Object.fromEntries((lifetimeEvents.results || []).map((row) => [row.event_type, Number(row.count || 0)]));
    return json({
      ok: true,
      window_minutes: 60,
      requests_per_minute: minutes.results || [],
      top_routes: routes.results || [],
      top_clients: clients.results || [],
      totals: { ...totals, cache_hit_ratio: denominator ? Number(totals.cache_hits || 0) / denominator : 0 },
      lifetime: {
        events: Object.values(lifetimeByType).reduce((sum, value) => sum + value, 0),
        downloads: Number(lifetimeByType["plugin.download.served"] || 0),
        analyses: Number(lifetimeByType["analysis.submitted"] || 0),
        references: Number(lifetimeByType["reference.upload.accepted"] || 0),
        inquiries: Number(lifetimeByType["inquiry.submitted"] || 0),
        by_type: lifetimeByType
      },
      daily_activity: dailyEvents.results || []
    });
  }
  if (path === "/v1/admin/activity" || path === "/v1/admin/logs/list") {
    const result = await env.AIFRED_OPS.prepare("SELECT id, created_at, event_type, request_id, product, channel, version, platform, route, method, status, metadata_json FROM activity ORDER BY created_at DESC LIMIT 300").all();
    const activity = (result.results || []).map((row) => ({ ...row, metadata: JSON.parse(row.metadata_json || "{}"), metadata_json: undefined }));
    return json({ ok: true, activity, logs: activity, events: activity });
  }
  if (path === "/v1/admin/inquiries" || path === "/v1/admin/inquiries/list") {
    const result = await env.AIFRED_OPS.prepare("SELECT id, created_at, name, email, message, status FROM inquiries ORDER BY created_at DESC LIMIT 200").all();
    return json({ ok: true, inquiries: result.results || [], count: result.results?.length || 0 });
  }
  if (path === "/v1/admin/releases") {
    return json({ ok: true, releases: publicReleaseManifest() });
  }
  if (path === "/v1/admin/reference/list") {
    return json({ ok: true, references: await loadReferenceRecords(env, 200) });
  }
  if (path === "/v1/admin/catalog/list") {
    const tracks = await loadCatalog(request, env);
    return json({ ok: true, tracks, count: tracks.length, source: "official-static-catalog" });
  }
  if (path === "/v1/admin/sales/list") {
    return json({ ok: true, ...(await historicalSales(env)) });
  }
  if (path === "/v1/admin/dashboard/state") {
    const [analyticsResponse, activityResponse, inquiriesResponse, releasesResponse, referencesResponse, catalogResponse] = await Promise.all([
      adminData(request, env, "/v1/admin/analytics", trace),
      adminData(request, env, "/v1/admin/activity", trace),
      adminData(request, env, "/v1/admin/inquiries", trace),
      adminData(request, env, "/v1/admin/releases", trace),
      adminData(request, env, "/v1/admin/reference/list", trace),
      adminData(request, env, "/v1/admin/catalog/list", trace)
    ]);
    const [analyticsBody, activityBody, inquiriesBody, releasesBody, referencesBody, catalogBody] = await Promise.all([analyticsResponse.json(), activityResponse.json(), inquiriesResponse.json(), releasesResponse.json(), referencesResponse.json(), catalogResponse.json()]);
    const providers = providerConfiguration(env);
    return json({
      ok: true,
      snapshot_at: new Date().toISOString(),
      status: { ok: true, api_version: "v1" },
      analytics: analyticsBody,
      logs: { logs: activityBody.activity },
      inquiries: { count: inquiriesBody.count, items: inquiriesBody.inquiries },
      releases: releasesBody.releases,
      providers,
      models: {
        models: providers.providers.filter((item) => item.configured).map((item) => item.model),
        active_model: providers.providers.find((item) => item.id === providers.active)?.model || "",
        providers
      },
      references: { count: referencesBody.references?.length || 0, items: referencesBody.references || [] },
      catalog: { tracks: catalogBody.count || 0, items: catalogBody.tracks || [], source_available: true },
      traffic: {
        api_hits: Number(analyticsBody.totals?.requests || 0),
        downloads: Number(analyticsBody.lifetime?.downloads || 0),
        errors: Number(analyticsBody.totals?.errors || 0),
        lifetime: analyticsBody.lifetime || {},
        daily_activity: analyticsBody.daily_activity || [],
        requests_per_minute: analyticsBody.requests_per_minute || [],
        top_routes: analyticsBody.top_routes || [],
        top_clients: analyticsBody.top_clients || [],
        rate_limited: Number(analyticsBody.totals?.rate_limited || 0),
        provider_calls: Number(analyticsBody.totals?.provider_calls || 0),
        cache_hits: Number(analyticsBody.totals?.cache_hits || 0),
        cache_misses: Number(analyticsBody.totals?.cache_misses || 0),
        queue_events: Number(analyticsBody.totals?.queue_events || 0),
        d1_writes: Number(analyticsBody.totals?.d1_writes || 0),
        recent: activityBody.activity
      },
      deploy: { source: "kaeganscott26/AIFRED_Official-", target: "Cloudflare Pages aifred-site" }
    });
  }
  if (path === "/v1/admin/providers") return json({ ok: true, ...providerConfiguration(env) });
  if (path === "/v1/admin/providers/ollama") {
    const config = providerConfiguration(env).providers.find((item) => item.id === "ollama");
    return json({ ok: true, provider: config });
  }
  if (providerTestPath) {
    const result = await testOllamaProvider(env);
    trace.providerCalls += 1;
    trace.provider = "ollama";
    return json(result, { status: result.ok ? 200 : 502 });
  }
  if (path === "/v1/admin/source/files") {
    return json({ ok: true, files: EDITABLE_WEBSITE_FILES, ...sourceControlStatus(env) });
  }
  if (path === "/v1/admin/source/status") {
    return json({ ok: true, ...sourceControlStatus(env) });
  }
  if (path === "/v1/admin/source/read") {
    const body = await readJson(request, MAX_BODY.source);
    return json(await readApprovedSourceFile(env, body.path));
  }
  if (path === "/v1/admin/source/validate") {
    const body = await readJson(request, MAX_BODY.source);
    return json(validateSourceDraft(body.path, body.content));
  }
  if (path === "/v1/admin/source/save") {
    const body = await readJson(request, MAX_BODY.source);
    const idempotency = await useIdempotency(request, env, path, identity.clientKey, 60);
    try {
      const result = await saveApprovedSourceFile(env, body);
      await enqueueActivity(env, {
        id: crypto.randomUUID(),
        created_at: new Date().toISOString(),
        event_type: "admin.website_source.committed",
        request_id: trace.requestId,
        route: path,
        method: "POST",
        status: 200,
        metadata: { path: result.path, commit_sha: result.commit_sha, repository: result.repository, branch: result.branch }
      });
      trace.d1Writes += 1;
      await idempotency.complete();
      return json(result);
    } catch (error) {
      await idempotency.abandon();
      throw error;
    }
  }
  if (path === "/v1/admin/export/site") {
    const payload = {
      schema: "aifred.admin-export.site.v1",
      exported_at: new Date().toISOString(),
      authority: "kaeganscott26/AIFRED_Official-",
      analytics: await responseBody(await adminData(request, env, "/v1/admin/analytics", trace)),
      activity: await responseBody(await adminData(request, env, "/v1/admin/activity", trace)),
      inquiries: await responseBody(await adminData(request, env, "/v1/admin/inquiries", trace)),
      releases: await responseBody(await adminData(request, env, "/v1/admin/releases", trace))
    };
    return exportJson(payload, "aifred-site-export.json");
  }
  if (path === "/v1/admin/export/tracks") {
    const references = await loadReferenceRecords(env, 500);
    return exportJson({ schema: "aifred.admin-export.tracks.v1", exported_at: new Date().toISOString(), references }, "aifred-track-analysis-export.json");
  }
  throw new HttpError(404, "route_not_found", "admin route not found");
}

async function responseBody(response) {
  return response.json();
}

function exportJson(payload, filename) {
  return json(payload, {
    headers: {
      "cache-control": "no-store",
      "content-disposition": `attachment; filename="${filename}"`
    }
  });
}

function parseRange(header, size) {
  const match = String(header || "").match(/^bytes=(\d*)-(\d*)$/i);
  if (!match) return null;
  let start = match[1] ? Number(match[1]) : Math.max(0, size - Number(match[2] || 0));
  let end = match[2] ? Number(match[2]) : size - 1;
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 0 || start >= size || end < start) return false;
  end = Math.min(end, size - 1);
  return { offset: start, length: end - start + 1 };
}

async function r2Object(request, bucket, key, downloadName, trace, immutable = true) {
  if (!bucket?.head || !bucket?.get) throw new HttpError(503, "storage_unavailable", "object storage is unavailable");
  const head = await bucket.head(key);
  if (!head) throw new HttpError(404, "object_not_found", "object not found");
  const range = parseRange(request.headers.get("range"), head.size);
  if (range === false) return new Response(null, { status: 416, headers: { "content-range": `bytes */${head.size}` } });
  const headers = new Headers();
  head.writeHttpMetadata(headers);
  headers.set("etag", head.httpEtag);
  headers.set("accept-ranges", "bytes");
  headers.set("cache-control", immutable ? "public, max-age=3600, immutable" : "public, max-age=300");
  if (downloadName) headers.set("content-disposition", `attachment; filename=\"${downloadName.replace(/[\"\\]/g, "_")}\"`);
  if (range) headers.set("content-range", `bytes ${range.offset}-${range.offset + range.length - 1}/${head.size}`);
  headers.set("content-length", String(range ? range.length : head.size));
  if (request.method === "HEAD") return new Response(null, { status: range ? 206 : 200, headers });
  const object = await bucket.get(key, range ? { range } : undefined);
  if (!object || object.size === 0) throw new HttpError(502, "object_corrupt", "object is empty or unavailable");
  if (request.method === "GET") trace.r2Downloads += 1;
  return new Response(object.body, { status: range ? 206 : 200, headers });
}

async function download(request, env, ctx, trace) {
  requireMethod(request, "GET", "HEAD");
  const channel = requestedReleaseChannel(request, "beta");
  const requestedAsset = new URL(request.url).searchParams.get("asset") || "setup";
  const { release, asset, logicalName } = releaseAsset(channel, requestedAsset);
  if (!release) throw new HttpError(400, "invalid_release_channel", "release channel must be beta or flagship");
  if (channel !== "beta" || release.source_repository !== "kaeganscott26/AIFRED") {
    throw new HttpError(404, "release_unavailable", "release artifact is not published");
  }
  if (!logicalName) throw new HttpError(400, "invalid_asset", "unsupported release asset");
  if (!release.published || !asset?.published) {
    throw new HttpError(404, "release_unavailable", `${channel} release artifact is not published`);
  }
  const key = String(asset.r2_key);
  if (!new RegExp(`^releases/${channel}/[A-Za-z0-9._-]+/[A-Za-z0-9._/-]+$`).test(key) || key.includes("..")) {
    throw new HttpError(500, "invalid_release_metadata", "release artifact metadata is invalid");
  }
  const head = await env.AIFRED_DOWNLOADS?.head?.(key);
  if (!head || head.size < 1 || head.size !== asset.size_bytes) {
    throw new HttpError(503, "release_artifact_unavailable", "the release artifact is not available in the configured R2 storage");
  }
  const response = await r2Object(request, env.AIFRED_DOWNLOADS, key, asset.filename, trace, false);
  const headers = new Headers(response.headers);
  headers.set("content-type", asset.content_type);
  headers.set("x-aifred-sha256", asset.sha256);
  headers.set("x-aifred-release-tag", release.tag);
  const verifiedResponse = new Response(response.body, { status: response.status, statusText: response.statusText, headers });
  if (request.method === "GET") {
    ctx.waitUntil(enqueueActivity(env, {
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      event_type: "plugin.download.served",
      request_id: trace.requestId,
      product: "aifred",
      channel,
      version: release.version,
      route: "/v1/downloads/plugin",
      method: "GET",
      status: verifiedResponse.status,
      metadata: { asset: logicalName, tag: release.tag, key, size_bytes: asset.size_bytes }
    }));
  }
  return verifiedResponse;
}

async function asset(request, env, path, trace) {
  requireMethod(request, "GET", "HEAD");
  let decoded;
  try { decoded = decodeURIComponent(path.slice("/v1/assets/".length)); } catch { throw new HttpError(400, "invalid_asset_path", "asset path is invalid"); }
  if (!decoded || decoded.includes("..") || decoded.includes("\\") || decoded.startsWith("/")) throw new HttpError(400, "invalid_asset_path", "asset path is invalid");
  return r2Object(request, env.AIFRED_DOWNLOADS, `assets/${decoded}`, new URL(request.url).searchParams.get("download") === "1" ? decoded.split("/").pop() : "", trace);
}

export async function routeRequest(request, env, ctx, trace) {
  const path = pathAfterApi(new URL(request.url).pathname).replace(/\/+$/, "") || "/";
  trace.route = path;
  if (path === "/health" || path === "/v1/health") return health(request);
  if (path === "/v1/models" || path === "/v1/models/list") return models(request, env, ctx);
  if (path === "/v1/catalog/list") return catalog(request, env, ctx);
  if (path === "/v1/releases") return releases(request, env, ctx, false);
  if (path === "/v1/releases/current") return releases(request, env, ctx, true);
  if (path === "/v1/chat/completions" || path === "/v1/chat/ask") return chat(request, env, trace);
  if (path === "/v1/references" || path === "/v1/reference/pool") return references(request, env, ctx, trace);
  if (path === "/v1/analysis/submit" || path === "/v1/analyzer/submit") return websiteAnalysis(request, env, ctx, trace);
  if (path === "/v1/analysis") return analysis(request, env, trace);
  if (path === "/v1/analytics/events" || path === "/v1/activity/record") return analytics(request, env, trace);
  if (path === "/v1/registry/actions") {
    requireMethod(request, "GET", "HEAD");
    return json({ ok: true, actions: backendActionCatalog(), authority: "aifred-site Pages Advanced Mode" });
  }
  if (path === "/v1/chat/settings") {
    requireMethod(request, "GET", "HEAD");
    return json(await chatSettingsPayload(request, env));
  }
  if (path === "/v1/command/run") {
    requireMethod(request, "POST");
    const identity = await adminIdentity(request, env);
    trace.adminIdentity = identity;
    trace.clientKey = identity.clientKey.slice(0, 32);
    trace.rateLimitOutcome = await enforceRateLimit(env.ADMIN_RATE_LIMITER, identity.clientKey, {
      db: env.AIFRED_OPS, scope: "admin", limit: 60
    });
    const body = await readJson(request, MAX_BODY.command);
    const result = await executeAdminCommand(body.command_line || body.command, request, env);
    return json(result, { status: result.ok ? 200 : 400 });
  }
  if (path === "/v1/inquiries" || path === "/v1/inquiries/submit") return inquiry(request, env, trace);
  if (path === "/v1/downloads/plugin") return download(request, env, ctx, trace);
  if (path.startsWith("/v1/assets/")) return asset(request, env, path, trace);
  if (path === "/v1/admin/login") return adminLogin(request, env, trace);
  if (path === "/v1/admin/logout") return adminLogout(request, env, trace);
  if (path.startsWith("/v1/admin/")) return adminData(request, env, path, trace);
  throw new HttpError(404, "route_not_found", "route not found");
}

export async function initialTrace(request) {
  const metadata = clientMetadata(request);
  return {
    requestId: bounded(request.headers.get("cf-ray"), 96) || crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    route: new URL(request.url).pathname,
    method: request.method,
    status: 0,
    latencyMs: 0,
    product: metadata.product,
    clientKey: await classifyClient(request, metadata),
    channel: metadata.channel,
    version: metadata.version,
    platform: metadata.platform,
    purpose: metadata.purpose,
    provider: "",
    errorCategory: "",
    rateLimitOutcome: "not_applicable",
    cacheStatus: "BYPASS",
    providerCalls: 0,
    d1Writes: 0,
    queueEvents: 0,
    r2Downloads: 0
  };
}
