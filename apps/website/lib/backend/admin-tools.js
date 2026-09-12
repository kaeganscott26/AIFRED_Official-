import { HttpError, bounded } from "./http.js";
import { providerConfiguration, testOllamaProvider } from "./providers.js";
import { readApprovedSourceFile, saveApprovedSourceFile } from "./source-control.js";

const PROVIDER_CONFIG_KEY = "config:admin:provider";
const CHAT_SETTINGS_KEY = "config:admin:chat-settings";
const MAX_ADMIN_UPLOAD_BYTES = 96 * 1024 * 1024;
const CATALOG_SOURCE_PATH = "apps/website/assets/data/beat_catalog.json";

const BACKEND_ACTIONS = Object.freeze([
  { id: "help", command: "help", description: "List the current backend command allowlist" },
  { id: "health", command: "health", description: "Check live website API health" },
  { id: "catalog:list", command: "catalog:list", description: "Count beat catalog tracks" },
  { id: "models:list", command: "models:list", description: "Show configured OpenAI/Ollama model routes" },
  { id: "reference:stats", command: "reference:stats", description: "Show analyzer reference-pool status" },
  { id: "deploy:status", command: "deploy:status", description: "Show unified Pages deployment authority" },
  { id: "sales:list", command: "sales:list", description: "Show historical beta sales" },
  { id: "inquiries:list", command: "inquiries:list", description: "Show recorded contact inquiries" },
  { id: "export:site", command: "export:site", description: "Show the authenticated site export route" },
  { id: "export:tracks", command: "export:tracks", description: "Show the authenticated track-analysis export route" }
]);

function requireKv(env) {
  if (!env.AIFRED_REFERENCE_POOL?.get || !env.AIFRED_REFERENCE_POOL?.put) {
    throw new HttpError(503, "runtime_config_unavailable", "runtime configuration KV is unavailable");
  }
  return env.AIFRED_REFERENCE_POOL;
}

async function readJsonValue(env, key, fallback) {
  const kv = env.AIFRED_REFERENCE_POOL;
  if (!kv?.get) return fallback;
  try {
    const value = await kv.get(key, "json");
    return value && typeof value === "object" ? value : fallback;
  } catch {
    return fallback;
  }
}

function cleanModel(value, fallback = "") {
  return bounded(value, 120) || fallback;
}

function cleanProvider(value) {
  const provider = bounded(value, 24).toLowerCase();
  if (!new Set(["ollama", "openai"]).has(provider)) {
    throw new HttpError(400, "invalid_provider", "provider must be ollama or openai");
  }
  return provider;
}

function cleanHttpsBaseUrl(value) {
  const candidate = bounded(value, 500).replace(/\/+$/, "");
  if (!candidate) return "";
  let parsed;
  try { parsed = new URL(candidate); } catch { throw new HttpError(400, "invalid_provider_url", "provider URL is invalid"); }
  if (parsed.protocol !== "https:") {
    throw new HttpError(400, "invalid_provider_url", "production provider URL must use HTTPS");
  }
  return parsed.toString().replace(/\/+$/, "");
}

export function backendActionCatalog() {
  return BACKEND_ACTIONS.map((item) => ({ ...item }));
}

export async function runtimeProviderConfig(env) {
  const stored = await readJsonValue(env, PROVIDER_CONFIG_KEY, {});
  const provider = String(stored.provider || env.AIFRED_CHAT_PROVIDER || "ollama").toLowerCase();
  return {
    provider: new Set(["ollama", "openai"]).has(provider) ? provider : "ollama",
    ollama_base_url: bounded(stored.ollama_base_url || env.OLLAMA_BASE_URL, 500),
    ollama_model: cleanModel(stored.ollama_model || env.OLLAMA_MODEL || env.OLLMA_MODEL, "aifred:latest"),
    openai_model: cleanModel(stored.openai_model || env.OPENAI_MODEL, "gpt-5.6-luna"),
    persistence: stored.provider ? "kv" : "worker-env"
  };
}

export async function runtimeProviderEnv(env) {
  const config = await runtimeProviderConfig(env);
  return {
    ...env,
    AIFRED_CHAT_PROVIDER: config.provider,
    OLLAMA_BASE_URL: config.ollama_base_url || env.OLLAMA_BASE_URL,
    OLLAMA_MODEL: config.ollama_model || env.OLLAMA_MODEL || env.OLLMA_MODEL,
    OPENAI_MODEL: config.openai_model || env.OPENAI_MODEL
  };
}

export async function saveRuntimeProviderConfig(env, input) {
  const current = await runtimeProviderConfig(env);
  const provider = cleanProvider(input?.provider || current.provider);
  const next = {
    provider,
    ollama_base_url: current.ollama_base_url,
    ollama_model: current.ollama_model,
    openai_model: current.openai_model,
    updated_at: new Date().toISOString()
  };
  if (provider === "ollama") {
    next.ollama_base_url = cleanHttpsBaseUrl(input?.ollama_base_url || input?.base_url || current.ollama_base_url);
    next.ollama_model = cleanModel(input?.ollama_model || input?.model, current.ollama_model || "aifred:latest");
  } else {
    next.openai_model = cleanModel(input?.openai_model || input?.model, current.openai_model || "gpt-5.6-luna");
  }
  await requireKv(env).put(PROVIDER_CONFIG_KEY, JSON.stringify(next));
  return { ok: true, config: { ...next, secrets: "worker-managed" }, message: "Production provider route saved; provider secrets remain Worker-managed." };
}

export async function testRuntimeProvider(env, input = {}) {
  const provider = cleanProvider(input.provider || (await runtimeProviderConfig(env)).provider);
  const runtimeEnv = await runtimeProviderEnv(env);
  if (provider === "ollama") return testOllamaProvider(runtimeEnv);
  if (!runtimeEnv.OPENAI_API_KEY || !runtimeEnv.OPENAI_MODEL) {
    throw new HttpError(503, "provider_unconfigured", "OpenAI provider is not configured");
  }
  const started = Date.now();
  let response;
  try {
    response = await fetch("https://api.openai.com/v1/models", {
      headers: { authorization: `Bearer ${runtimeEnv.OPENAI_API_KEY}` },
      signal: AbortSignal.timeout(5_000)
    });
  } catch (error) {
    if (error?.name === "TimeoutError") throw new HttpError(504, "provider_timeout", "OpenAI provider test timed out");
    throw new HttpError(502, "provider_unavailable", "OpenAI provider is unavailable");
  }
  response.body?.cancel().catch(() => {});
  return { ok: response.ok, provider: "openai", model: runtimeEnv.OPENAI_MODEL, status: response.status, latency_ms: Date.now() - started };
}

function defaultChatSettings() {
  return {
    transport_mode: "http",
    webhook: { enabled: false, url: "", secret: "", events: ["chat.completed", "chat.failed"] },
    context: { use_previous_response_id: true, memory_window_items: 40, summary_items: 6, max_prompt_chars: 4000, compact_threshold: 12 },
    prompt: { tone: "direct", personality_mode: "professional_mentor", system_prefix: "", system_suffix: "" },
    reasoning: { enabled: true, effort: "low" },
    response: { verbosity: "low", max_output_tokens: 900 }
  };
}

function sanitizeChatSettings(input) {
  const defaults = defaultChatSettings();
  const source = input && typeof input === "object" ? input : {};
  const transport = String(source.transport_mode || defaults.transport_mode).toLowerCase();
  const tone = bounded(source.prompt?.tone || defaults.prompt.tone, 32);
  const personality = bounded(source.prompt?.personality_mode || defaults.prompt.personality_mode, 80);
  const reasoningEffort = bounded(source.reasoning?.effort || defaults.reasoning.effort, 16);
  const verbosity = bounded(source.response?.verbosity || defaults.response.verbosity, 16);
  return {
    transport_mode: new Set(["http", "websocket"]).has(transport) ? transport : "http",
    webhook: {
      enabled: Boolean(source.webhook?.enabled),
      url: bounded(source.webhook?.url, 500),
      secret: bounded(source.webhook?.secret, 500),
      events: Array.isArray(source.webhook?.events) ? source.webhook.events.map((item) => bounded(item, 80)).filter(Boolean).slice(0, 20) : defaults.webhook.events
    },
    context: {
      use_previous_response_id: source.context?.use_previous_response_id !== false,
      memory_window_items: Math.max(1, Math.min(200, Number(source.context?.memory_window_items || defaults.context.memory_window_items))),
      summary_items: Math.max(1, Math.min(50, Number(source.context?.summary_items || defaults.context.summary_items))),
      max_prompt_chars: Math.max(256, Math.min(32000, Number(source.context?.max_prompt_chars || defaults.context.max_prompt_chars))),
      compact_threshold: Math.max(1, Math.min(100, Number(source.context?.compact_threshold || defaults.context.compact_threshold)))
    },
    prompt: {
      tone,
      personality_mode: personality,
      system_prefix: bounded(source.prompt?.system_prefix, 8000),
      system_suffix: bounded(source.prompt?.system_suffix, 8000)
    },
    reasoning: {
      enabled: source.reasoning?.enabled !== false,
      effort: new Set(["minimal", "low", "medium", "high"]).has(reasoningEffort) ? reasoningEffort : "low"
    },
    response: {
      verbosity: new Set(["low", "medium", "high"]).has(verbosity) ? verbosity : "low",
      max_output_tokens: Math.max(128, Math.min(8000, Number(source.response?.max_output_tokens || defaults.response.max_output_tokens)))
    }
  };
}

export async function chatSettingsPayload(request, env, includeSecret = false) {
  const stored = await readJsonValue(env, CHAT_SETTINGS_KEY, null);
  const settings = sanitizeChatSettings(stored || defaultChatSettings());
  if (!includeSecret) settings.webhook.secret = "";
  const url = new URL(request.url);
  const websocketUrl = `${url.protocol === "https:" ? "wss:" : "ws:"}//${url.host}/ws/chat`;
  return { ok: true, settings, websocket_url: websocketUrl, persistence: stored ? "kv" : "defaults" };
}

export async function saveChatSettings(env, input) {
  const settings = sanitizeChatSettings(input);
  await requireKv(env).put(CHAT_SETTINGS_KEY, JSON.stringify(settings));
  return settings;
}

function safeFileName(value, fallback) {
  const leaf = String(value || fallback || "upload.bin").replace(/\\/g, "/").split("/").pop().trim();
  const safe = leaf.replace(/[^A-Za-z0-9._() -]/g, "-").replace(/\s+/g, " ").slice(0, 180);
  if (!safe || safe === "." || safe === "..") throw new HttpError(400, "invalid_filename", "upload filename is invalid");
  return safe;
}

function encodeAssetPath(path) {
  return path.split("/").map(encodeURIComponent).join("/");
}

async function fileBytes(file) {
  const size = Number(file?.size || 0);
  if (!file || typeof file === "string") throw new HttpError(400, "file_required", "file is required");
  if (size < 1) throw new HttpError(400, "empty_upload", "upload is empty");
  if (size > MAX_ADMIN_UPLOAD_BYTES) throw new HttpError(413, "upload_too_large", "upload exceeds the admin upload limit");
  return new Uint8Array(await file.arrayBuffer());
}

export async function uploadCatalogAudio(request, env) {
  if (!env.AIFRED_DOWNLOADS?.put) throw new HttpError(503, "r2_unavailable", "download storage is unavailable");
  const form = await request.formData();
  const file = form.get("file");
  const bytes = await fileBytes(file);
  const fileName = safeFileName(file.name, "catalog-audio.bin");
  const objectKey = `assets/audio/catalog/${fileName}`;
  const source = await readApprovedSourceFile(env, CATALOG_SOURCE_PATH);
  const tracks = JSON.parse(source.content);
  if (!Array.isArray(tracks)) throw new HttpError(502, "catalog_invalid", "catalog source is not an array");
  const streamUrl = `/api/v1/assets/${encodeAssetPath(`audio/catalog/${fileName}`)}`;
  const track = {
    key: crypto.randomUUID(),
    title: bounded(form.get("title") || fileName.replace(/\.[^.]+$/, ""), 200),
    description: bounded(form.get("description"), 1000),
    bpm: bounded(form.get("bpm"), 24),
    key_signature: bounded(form.get("key"), 24),
    tempo: bounded(form.get("tempo"), 40),
    genre: bounded(form.get("pack_type") || "North3rnLight3r", 80),
    distribution: bounded(form.get("price") || "Free MP3 download; commercial licensing by inquiry", 160),
    asset_file_name: fileName,
    public_url: streamUrl,
    full_song_url: streamUrl,
    stream_url: streamUrl,
    uploaded_at: new Date().toISOString()
  };
  await env.AIFRED_DOWNLOADS.put(objectKey, bytes, { httpMetadata: { contentType: file.type || "application/octet-stream" } });
  try {
    const commit = await saveApprovedSourceFile(env, {
      path: CATALOG_SOURCE_PATH,
      content: `${JSON.stringify([...tracks, track], null, 2)}\n`,
      expected_sha: source.sha
    });
    return { ok: true, stored_path: objectKey, public_url: streamUrl, track, commit: commit.commit_sha };
  } catch (error) {
    await env.AIFRED_DOWNLOADS.delete?.(objectKey).catch(() => {});
    throw error;
  }
}

export async function removeCatalogTrack(env, key) {
  const normalizedKey = bounded(key, 160);
  if (!normalizedKey) throw new HttpError(400, "track_key_required", "track key is required");
  const source = await readApprovedSourceFile(env, CATALOG_SOURCE_PATH);
  const tracks = JSON.parse(source.content);
  if (!Array.isArray(tracks)) throw new HttpError(502, "catalog_invalid", "catalog source is not an array");
  const removed = tracks.find((item) => String(item?.key || "") === normalizedKey);
  if (!removed) throw new HttpError(404, "track_not_found", "catalog track was not found");
  const next = tracks.filter((item) => String(item?.key || "") !== normalizedKey);
  const commit = await saveApprovedSourceFile(env, {
    path: CATALOG_SOURCE_PATH,
    content: `${JSON.stringify(next, null, 2)}\n`,
    expected_sha: source.sha
  });
  const stream = String(removed.stream_url || removed.full_song_url || removed.public_url || "");
  const marker = "/api/v1/assets/";
  if (env.AIFRED_DOWNLOADS?.delete && stream.startsWith(marker)) {
    let rel = stream.slice(marker.length);
    try { rel = decodeURIComponent(rel); } catch {}
    if (rel && !rel.includes("..") && !rel.includes("\\")) await env.AIFRED_DOWNLOADS.delete(`assets/${rel}`).catch(() => {});
  }
  return { ok: true, removed: normalizedKey, track: removed, commit: commit.commit_sha };
}

export async function uploadLicensedReference(request, env) {
  if (!env.AIFRED_REFERENCE_BUCKET?.put) throw new HttpError(503, "reference_storage_unavailable", "reference storage is unavailable");
  const form = await request.formData();
  const file = form.get("file");
  const bytes = await fileBytes(file);
  const genre = bounded(form.get("genre") || "reference", 64).toLowerCase().replace(/[^a-z0-9._-]+/g, "-") || "reference";
  const title = bounded(form.get("title") || file.name, 200);
  const fileName = safeFileName(file.name, "reference-audio.bin");
  const objectKey = `licensed/${genre}/${crypto.randomUUID()}-${fileName}`;
  await env.AIFRED_REFERENCE_BUCKET.put(objectKey, bytes, {
    httpMetadata: { contentType: file.type || "application/octet-stream" },
    customMetadata: { genre, title, uploaded_at: new Date().toISOString() }
  });
  return { ok: true, stored_path: objectKey, genre, title, message: "Licensed reference audio stored for analysis/intake." };
}

export async function historicalSales(env) {
  const kv = env.AIFRED_SALES_LOG;
  if (!kv?.list || !kv?.get) return { configured: false, sales: [], count: 0 };
  let listed;
  try { listed = await kv.list({ prefix: "sale:", limit: 200 }); } catch { return { configured: true, sales: [], count: 0, unavailable: true }; }
  const values = await Promise.all((listed.keys || []).map(async (key) => {
    try {
      const value = await kv.get(key.name, "json");
      return value && typeof value === "object" ? value : null;
    } catch { return null; }
  }));
  const sales = values.filter(Boolean).slice(0, 200);
  return { configured: true, sales, count: sales.length };
}

export async function executeAdminCommand(command, request, env) {
  const normalized = String(command || "").trim();
  const allowed = new Set(BACKEND_ACTIONS.map((item) => item.command));
  if (!allowed.has(normalized)) {
    return { ok: false, exit_code: 2, stderr: "Unsupported command. Use /api/v1/registry/actions for the allowlist." };
  }
  let output;
  if (normalized === "help") output = backendActionCatalog();
  else if (normalized === "health") output = { ok: true, service: "aifred-site", api_version: "v1" };
  else if (normalized === "catalog:list") {
    const response = await env.ASSETS.fetch(new Request(new URL("/assets/data/beat_catalog.json", request.url)));
    const tracks = await response.json();
    output = { tracks: Array.isArray(tracks) ? tracks.length : 0 };
  } else if (normalized === "models:list") output = providerConfiguration(await runtimeProviderEnv(env));
  else if (normalized === "reference:stats") {
    const row = await env.AIFRED_OPS.prepare("SELECT COUNT(*) count FROM references_catalog WHERE active = 1").first();
    output = { count: Number(row?.count || 0), r2: Boolean(env.AIFRED_REFERENCE_BUCKET), d1: Boolean(env.AIFRED_OPS) };
  } else if (normalized === "deploy:status") output = { source: "kaeganscott26/AIFRED_Official-", branch: "main", target: env.AIFRED_PAGES_PROJECT || "aifred-site", architecture: "pages-advanced-mode" };
  else if (normalized === "sales:list") output = await historicalSales(env);
  else if (normalized === "inquiries:list") {
    const result = await env.AIFRED_OPS.prepare("SELECT id, created_at, name, email, message, status FROM inquiries ORDER BY created_at DESC LIMIT 200").all();
    output = { inquiries: result.results || [], count: result.results?.length || 0 };
  } else if (normalized === "export:site") output = { route: "/api/v1/admin/export/site", method: "GET" };
  else if (normalized === "export:tracks") output = { route: "/api/v1/admin/export/tracks", method: "GET" };
  return { ok: true, exit_code: 0, stdout: JSON.stringify(output, null, 2), stderr: "" };
}
