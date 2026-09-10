import { bounded, sha256Hex } from "./http.js";

function safeDimension(value, length = 96) {
  return bounded(value, length) || "";
}

export async function classifyClient(request, metadata, authenticatedClientKey = "") {
  if (authenticatedClientKey) return authenticatedClientKey.slice(0, 32);
  if (metadata.client) return (await sha256Hex(metadata.client)).slice(0, 32);
  return (await sha256Hex(request.headers.get("cf-connecting-ip") || "anonymous")).slice(0, 32);
}

export function writeAnalytics(env, record) {
  if (!env.AIFRED_ANALYTICS?.writeDataPoint) return;
  env.AIFRED_ANALYTICS.writeDataPoint({
    blobs: [
      safeDimension(record.route),
      safeDimension(record.clientKey),
      safeDimension(record.product, 40),
      safeDimension(record.channel, 24),
      safeDimension(record.version, 40),
      safeDimension(record.platform, 40),
      safeDimension(record.purpose, 64),
      safeDimension(record.rateLimitOutcome, 24),
      safeDimension(record.cacheStatus, 24),
      safeDimension(record.provider, 32),
      safeDimension(record.errorCategory, 48)
    ],
    doubles: [
      Number(record.status || 0),
      Number(record.latencyMs || 0),
      Number(record.providerCalls || 0),
      Number(record.d1Writes || 0),
      Number(record.queueEvents || 0),
      Number(record.r2Downloads || 0)
    ],
    indexes: [safeDimension(record.route, 64)]
  });
}

export async function enqueueRequestMetric(env, record) {
  if (!env.AIFRED_OPS?.prepare) return;
  const item = {
    kind: "request",
    id: crypto.randomUUID(),
    created_at: record.timestamp,
    minute: record.timestamp.slice(0, 16) + ":00.000Z",
    route: safeDimension(record.route),
    client_key: safeDimension(record.clientKey, 32),
    product: safeDimension(record.product, 40),
    channel: safeDimension(record.channel, 24),
    purpose: safeDimension(record.purpose, 64),
    status: Number(record.status || 0),
    rate_limit_outcome: safeDimension(record.rateLimitOutcome, 24),
    cache_status: safeDimension(record.cacheStatus, 24),
    provider_calls: Number(record.providerCalls || 0),
    d1_writes: Number(record.d1Writes || 0),
    queue_events: Number(record.queueEvents || 0),
    r2_downloads: Number(record.r2Downloads || 0)
  };
  await requestRollupStatement(env, item).run();
}

function normalizedActivity(event) {
  return {
    kind: "activity",
    id: event.id || crypto.randomUUID(),
    created_at: event.created_at || new Date().toISOString(),
    event_type: safeDimension(event.event_type),
    request_id: safeDimension(event.request_id),
    product: safeDimension(event.product, 40),
    channel: safeDimension(event.channel, 24),
    version: safeDimension(event.version, 40),
    platform: safeDimension(event.platform, 40),
    route: safeDimension(event.route),
    method: safeDimension(event.method, 12),
    status: Number(event.status || 0),
    metadata: event.metadata && typeof event.metadata === "object" ? event.metadata : {}
  };
}

export async function enqueueActivities(env, events) {
  if (!env.AIFRED_OPS?.prepare) return;
  const items = events.map(normalizedActivity);
  const cutoff = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString();
  await env.AIFRED_OPS.batch([
    ...items.flatMap((item) => [activityStatement(env, item), analyticsRollupStatement(env, item)]),
    env.AIFRED_OPS.prepare("DELETE FROM activity WHERE created_at < ? OR id IN (SELECT id FROM activity ORDER BY created_at DESC LIMIT -1 OFFSET 1000)").bind(cutoff),
    env.AIFRED_OPS.prepare("DELETE FROM request_rollups WHERE minute < ?").bind(cutoff),
    env.AIFRED_OPS.prepare("DELETE FROM idempotency_keys WHERE expires_at <= ?").bind(new Date().toISOString()),
    env.AIFRED_OPS.prepare("DELETE FROM admin_sessions WHERE expires_at <= ?").bind(new Date().toISOString()),
    env.AIFRED_OPS.prepare("DELETE FROM rate_limits WHERE window_start < ?").bind(Math.floor(Date.now() / 1000) - 86400)
  ]);
}

export async function enqueueActivity(env, event) {
  return enqueueActivities(env, [event]);
}

function requestRollupStatement(env, item, count = 1) {
  return env.AIFRED_OPS.prepare(`
    INSERT INTO request_rollups (
      minute, route, client_key, product, channel, purpose, status,
      rate_limit_outcome, cache_status, provider_calls, d1_writes,
      queue_events, r2_downloads, requests
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT (
      minute, route, client_key, product, channel, purpose, status,
      rate_limit_outcome, cache_status
    ) DO UPDATE SET
      provider_calls = provider_calls + excluded.provider_calls,
      d1_writes = d1_writes + excluded.d1_writes,
      queue_events = queue_events + excluded.queue_events,
      r2_downloads = r2_downloads + excluded.r2_downloads,
      requests = requests + excluded.requests
  `).bind(
    item.minute, item.route, item.client_key, item.product, item.channel,
    item.purpose, item.status, item.rate_limit_outcome, item.cache_status,
    item.provider_calls * count, item.d1_writes * count,
    item.queue_events * count, item.r2_downloads * count, count
  );
}

function activityStatement(env, item) {
  const metadata = JSON.stringify(item.metadata || {}).slice(0, 4096);
  return env.AIFRED_OPS.prepare(`
    INSERT INTO activity (
      id, created_at, event_type, request_id, product, channel, version,
      platform, route, method, status, metadata_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO NOTHING
  `).bind(
    safeDimension(item.id, 128) || crypto.randomUUID(),
    safeDimension(item.created_at, 40) || new Date().toISOString(),
    safeDimension(item.event_type), safeDimension(item.request_id), safeDimension(item.product, 40),
    safeDimension(item.channel, 24), safeDimension(item.version, 40), safeDimension(item.platform, 40), safeDimension(item.route), safeDimension(item.method, 12),
    Number(item.status || 0), metadata
  );
}

function analyticsRollupStatement(env, item) {
  const createdAt = safeDimension(item.created_at, 40) || new Date().toISOString();
  const day = createdAt.slice(0, 10);
  return env.AIFRED_OPS.prepare(`
    INSERT INTO analytics_rollups (day, event_type, product, channel, platform, count, last_seen)
    VALUES (?, ?, ?, ?, ?, 1, ?)
    ON CONFLICT(day, event_type, product, channel, platform)
    DO UPDATE SET count = count + 1, last_seen = excluded.last_seen
  `).bind(day, safeDimension(item.event_type), safeDimension(item.product, 40), safeDimension(item.channel, 24), safeDimension(item.platform, 40), createdAt);
}

export async function consumeBatch(batch, env) {
  const statements = [];
  const groupedRequests = new Map();
  for (const message of batch.messages) {
    const item = message.body;
    if (!item || typeof item !== "object") {
      message.ack();
      continue;
    }
    if (item.kind === "request") {
      const key = [item.minute, item.route, item.client_key, item.product, item.channel, item.purpose, item.status, item.rate_limit_outcome, item.cache_status, item.provider_calls, item.d1_writes, item.queue_events, item.r2_downloads].join("\u001f");
      const current = groupedRequests.get(key);
      groupedRequests.set(key, current ? { item: current.item, count: current.count + 1 } : { item, count: 1 });
    } else if (item.kind === "activity") {
      statements.push(activityStatement(env, item), analyticsRollupStatement(env, item));
    }
  }
  for (const { item, count } of groupedRequests.values()) statements.push(requestRollupStatement(env, item, count));
  if (statements.length) await env.AIFRED_OPS.batch(statements);
  batch.ackAll();
}

export function structuredLog(record) {
  const payload = {
    request_id: record.requestId,
    timestamp: record.timestamp,
    route: record.route,
    method: record.method,
    status: record.status,
    latency_ms: record.latencyMs,
    product: record.product,
    client: record.clientKey,
    channel: record.channel,
    version: record.version,
    platform: record.platform,
    purpose: record.purpose,
    provider: record.provider,
    error_category: record.errorCategory,
    rate_limit_outcome: record.rateLimitOutcome,
    cache_status: record.cacheStatus,
    provider_calls: record.providerCalls,
    d1_writes: record.d1Writes,
    queue_events: record.queueEvents,
    r2_downloads: record.r2Downloads
  };
  if (record.status >= 500) console.error(payload);
  else if (record.status >= 400) console.warn(payload);
  else console.log(payload);
}
