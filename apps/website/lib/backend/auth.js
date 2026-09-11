import { HttpError, bounded, sha256Hex } from "./http.js";

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function base64Url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function fromBase64Url(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  return Uint8Array.from(atob(padded), (character) => character.charCodeAt(0));
}

async function hmac(secret, value) {
  const key = await crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(value)));
}

async function safeEqual(left, right) {
  const [a, b] = await Promise.all([sha256Hex(left), sha256Hex(right)]);
  let difference = a.length ^ b.length;
  for (let index = 0; index < Math.max(a.length, b.length); index += 1) {
    difference |= (a.charCodeAt(index) || 0) ^ (b.charCodeAt(index) || 0);
  }
  return difference === 0;
}

export function bearer(request) {
  const value = request.headers.get("authorization") || "";
  return value.toLowerCase().startsWith("bearer ") ? value.slice(7).trim() : "";
}

export async function apiIdentity(request, env, allowAnalytics = false) {
  const token = bearer(request);
  const candidates = [env.AIFRED_API_TOKEN];
  if (allowAnalytics) candidates.push(env.AIFRED_ANALYTICS_API_TOKEN);
  let valid = false;
  for (const candidate of candidates.filter(Boolean)) valid ||= await safeEqual(token, candidate);
  if (!valid) throw new HttpError(401, "authentication_required", "valid client authentication is required");
  const declared = bounded(request.headers.get("x-aifred-client"), 96);
  return { clientKey: await sha256Hex(declared || token), declared: declared || "authenticated-client" };
}

export async function rateLimitKey(request, identity = null) {
  if (identity?.clientKey) return identity.clientKey;
  const declared = bounded(request.headers.get("x-aifred-client"), 96);
  if (declared) return sha256Hex(declared);
  return sha256Hex(request.headers.get("cf-connecting-ip") || "anonymous");
}

export async function enforceRateLimit(binding, key, options = {}) {
  if (binding?.limit) {
    const result = await binding.limit({ key });
    if (!result.success) throw new HttpError(429, "rate_limited", "request rate limit exceeded", { "retry-after": "60" });
    return "allowed";
  }
  const db = options.db;
  if (!db?.prepare) return "unavailable";
  const period = Math.max(1, Number(options.period || 60));
  const limit = Math.max(1, Number(options.limit || 10));
  const scope = bounded(options.scope, 48) || "default";
  const windowStart = Math.floor(Date.now() / 1000 / period) * period;
  const row = await db.prepare(`
    INSERT INTO rate_limits (scope, client_key, window_start, count)
    VALUES (?, ?, ?, 1)
    ON CONFLICT(scope, client_key, window_start)
    DO UPDATE SET count = count + 1
    RETURNING count
  `).bind(scope, bounded(key, 128), windowStart).first();
  if (Number(row?.count || 0) > limit) {
    throw new HttpError(429, "rate_limited", "request rate limit exceeded", { "retry-after": String(period) });
  }
  return "allowed";
}

export async function createAdminSession(username, env) {
  if (!env.AIFRED_ADMIN_SESSION_SECRET) throw new HttpError(503, "admin_unconfigured", "admin authentication is not configured");
  const now = Date.now();
  const id = crypto.randomUUID();
  const expiresAt = new Date(now + 12 * 60 * 60 * 1000).toISOString();
  const payload = base64Url(encoder.encode(JSON.stringify({ id, username, exp: now + 12 * 60 * 60 * 1000 })));
  const signature = base64Url(await hmac(env.AIFRED_ADMIN_SESSION_SECRET, payload));
  await env.AIFRED_OPS.prepare(
    "INSERT INTO admin_sessions (id, username, created_at, expires_at) VALUES (?, ?, ?, ?)"
  ).bind(id, username, new Date(now).toISOString(), expiresAt).run();
  return { token: `${payload}.${signature}`, id, expiresAt };
}

export async function adminIdentity(request, env) {
  const cookieToken = (request.headers.get("cookie") || "").split(/;\s*/).find((item) => item.startsWith("aifred_admin="))?.slice(13) || "";
  const token = bearer(request) || cookieToken;
  const [payload, signature] = token.split(".");
  if (!payload || !signature || !env.AIFRED_ADMIN_SESSION_SECRET) throw new HttpError(401, "admin_session_required", "admin session required");
  const expected = base64Url(await hmac(env.AIFRED_ADMIN_SESSION_SECRET, payload));
  if (!(await safeEqual(signature, expected))) throw new HttpError(401, "invalid_admin_session", "admin session is invalid");
  let session;
  try { session = JSON.parse(decoder.decode(fromBase64Url(payload))); } catch { throw new HttpError(401, "invalid_admin_session", "admin session is invalid"); }
  if (!session.id || !session.username || Number(session.exp) <= Date.now()) throw new HttpError(401, "expired_admin_session", "admin session expired");
  const row = await env.AIFRED_OPS.prepare(
    "SELECT id, username, expires_at FROM admin_sessions WHERE id = ? AND expires_at > ?"
  ).bind(session.id, new Date().toISOString()).first();
  if (!row || row.username !== session.username) throw new HttpError(401, "revoked_admin_session", "admin session is no longer active");
  return { ...session, clientKey: await sha256Hex(`admin:${session.username}`) };
}

export async function verifyAdminCredentials(username, password, env) {
  const expectedUser = String(env.AIFRED_ADMIN_USERNAME || "").trim();
  const configuredVerifier = String(env.AIFRED_ADMIN_PASSWORD_SHA256 || "").trim();
  const configuredPassword = String(env.AIFRED_ADMIN_PASSWORD || "");

  if (!expectedUser || !(await safeEqual(username, expectedUser))) return false;

  // Canonical production configuration: AIFRED_ADMIN_PASSWORD_SHA256 contains
  // the lowercase/uppercase-insensitive 64-character SHA-256 digest.
  if (/^[a-f0-9]{64}$/i.test(configuredVerifier)) {
    return safeEqual(await sha256Hex(password), configuredVerifier.toLowerCase());
  }

  // Compatibility for existing deployments that accidentally stored the raw
  // password under the legacy SHA256-named secret. This keeps production
  // recoverable without weakening the session boundary. New deployments should
  // use the digest form above.
  if (configuredVerifier) return safeEqual(password, configuredVerifier);

  // Local/dev convenience only. Production should prefer the digest secret.
  if (configuredPassword) return safeEqual(password, configuredPassword);

  return false;
}
