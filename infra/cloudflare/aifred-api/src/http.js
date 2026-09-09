const encoder = new TextEncoder();

export const MAX_BODY = Object.freeze({
  analytics: 128 * 1024,
  analysis: 256 * 1024,
  chat: 192 * 1024,
  inquiry: 16 * 1024,
  login: 4 * 1024,
  reference: 256 * 1024
});

export class HttpError extends Error {
  constructor(status, code, message, headers = {}) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.code = code;
    this.headers = headers;
  }
}

export function json(body, init = {}) {
  const headers = new Headers(init.headers || {});
  headers.set("content-type", "application/json; charset=utf-8");
  if (!headers.has("cache-control")) headers.set("cache-control", "no-store");
  headers.set("x-content-type-options", "nosniff");
  return new Response(JSON.stringify(body), { ...init, headers });
}

export async function readJson(request, maxBytes) {
  const declared = Number(request.headers.get("content-length") || 0);
  if (declared > maxBytes) throw new HttpError(413, "body_too_large", `request body exceeds ${maxBytes} bytes`);
  if (!request.body) throw new HttpError(400, "missing_body", "request body is required");

  const reader = request.body.getReader();
  const chunks = [];
  let length = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    length += value.byteLength;
    if (length > maxBytes) {
      await reader.cancel("body_too_large");
      throw new HttpError(413, "body_too_large", `request body exceeds ${maxBytes} bytes`);
    }
    chunks.push(value);
  }

  const combined = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    combined.set(chunk, offset);
    offset += chunk.byteLength;
  }
  try {
    return JSON.parse(new TextDecoder().decode(combined));
  } catch {
    throw new HttpError(400, "invalid_json", "request body must be valid JSON");
  }
}

export function corsHeaders(request) {
  const origin = request.headers.get("origin");
  const allowed = new Set([
    "https://north3rnlight3r.com",
    "https://www.north3rnlight3r.com",
    "https://aifred-site.pages.dev",
    "http://127.0.0.1:8787",
    "http://127.0.0.1:8788",
    "http://localhost:8787",
    "http://localhost:8788"
  ]);
  const headers = new Headers({
    "access-control-allow-headers": "Authorization, Content-Type, Idempotency-Key, X-AIFRED-Client, X-AIFRED-Product, X-AIFRED-Channel, X-AIFRED-Version, X-AIFRED-Platform, X-AIFRED-Purpose",
    "access-control-allow-methods": "GET, HEAD, POST, OPTIONS",
    "access-control-max-age": "86400",
    vary: "Origin"
  });
  if (origin && allowed.has(origin)) {
    headers.set("access-control-allow-origin", origin);
    headers.set("access-control-allow-credentials", "true");
  }
  return headers;
}

export function withCors(response, request, requestId) {
  const headers = new Headers(response.headers);
  for (const [name, value] of corsHeaders(request)) headers.set(name, value);
  headers.set("x-request-id", requestId);
  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

export async function sha256Hex(value) {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(String(value)));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function etagFor(value) {
  return `\"${await sha256Hex(value)}\"`;
}

export async function publicCachedJson(request, ctx, payload, maxAge, staleWhileRevalidate = 300) {
  const url = new URL(request.url);
  const cacheKey = new Request(`${url.origin}${url.pathname}`, { method: "GET" });
  const cache = caches.default;
  const cached = await cache.match(cacheKey);
  if (cached) {
    const headers = new Headers(cached.headers);
    headers.set("x-aifred-cache", "HIT");
    if (request.headers.get("if-none-match") === headers.get("etag")) {
      return new Response(null, { status: 304, headers });
    }
    return new Response(request.method === "HEAD" ? null : cached.body, { status: cached.status, headers });
  }

  const resolvedPayload = typeof payload === "function" ? await payload() : payload;
  const body = JSON.stringify(resolvedPayload);
  const headers = new Headers({
    "content-type": "application/json; charset=utf-8",
    "cache-control": `public, max-age=${maxAge}, s-maxage=${maxAge}, stale-while-revalidate=${staleWhileRevalidate}`,
    etag: await etagFor(body),
    "x-aifred-cache": "MISS",
    "x-content-type-options": "nosniff"
  });
  const response = new Response(body, { headers });
  ctx.waitUntil(cache.put(cacheKey, response.clone()));
  return new Response(request.method === "HEAD" ? null : response.body, { headers });
}

export function clientMetadata(request, body = {}) {
  return {
    product: bounded(body.product || request.headers.get("x-aifred-product"), 40),
    channel: bounded(body.channel || request.headers.get("x-aifred-channel"), 24),
    version: bounded(body.version || request.headers.get("x-aifred-version"), 40),
    platform: bounded(body.platform || request.headers.get("x-aifred-platform"), 40),
    purpose: bounded(body.purpose || request.headers.get("x-aifred-purpose"), 64),
    client: bounded(body.client_id || body.client || request.headers.get("x-aifred-client"), 96)
  };
}

export function bounded(value, length) {
  return String(value || "").trim().slice(0, length);
}
