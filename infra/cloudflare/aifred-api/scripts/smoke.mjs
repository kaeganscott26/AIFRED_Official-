import { randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const workerRoot = resolve(here, "..");
const repositoryRoot = resolve(workerRoot, "..", "..", "..");
const base = String(process.argv[2] || "").replace(/\/+$/, "");
const expectProvider = process.argv.includes("--provider");
if (!/^https:\/\//.test(base)) throw new Error("usage: node scripts/smoke.mjs https://api-base [--provider]");

const secrets = JSON.parse(await readFile(resolve(workerRoot, ".secrets.local.json"), "utf8"));
const envText = await readFile(resolve(repositoryRoot, ".env"), "utf8");
const localEnv = Object.fromEntries(envText.split(/\r?\n/).flatMap((line) => {
  const match = line.match(/^([A-Z0-9_]+)=(.*)$/);
  return match ? [[match[1], match[2]]] : [];
}));
if (!localEnv.AIFRED_ADMIN_PASSWORD) throw new Error("AIFRED_ADMIN_PASSWORD is missing from the ignored repository .env");

const results = [];
function record(name, response, details = {}) {
  const result = { name, status: response.status, ok: response.ok, ...details };
  results.push(result);
  return result;
}
async function jsonRequest(path, init = {}) {
  const response = await fetch(`${base}${path}`, init);
  const payload = await response.json().catch(() => null);
  return { response, payload };
}

for (const [name, path] of [
  ["health", "/api/health"],
  ["models", "/api/v1/models"],
  ["references", "/api/v1/references"],
  ["release-flagship", "/api/v1/releases/current?channel=flagship"],
  ["release-beta", "/api/v1/releases/current?channel=beta"]
]) {
  const { response, payload } = await jsonRequest(path);
  record(name, response, { schema_ok: Boolean(payload && (payload.ok === true || payload.object === "list")) });
}
for (const [name, path] of [
  ["download-beta-setup", "/api/v1/downloads/plugin?channel=beta&asset=setup"],
  ["download-beta-zip", "/api/v1/downloads/plugin?channel=beta&asset=zip"]
]) {
  const response = await fetch(`${base}${path}`, { method: "HEAD" });
  record(name, response, {
    attachment: response.headers.get("content-disposition") || "",
    content_type: response.headers.get("content-type") || ""
  });
  await response.body?.cancel();
}
const referenceSecond = await fetch(`${base}/api/v1/references`);
record("references-cache", referenceSecond, { cache: referenceSecond.headers.get("x-aifred-cache") || "" });
await referenceSecond.body?.cancel();

const login = await jsonRequest("/api/v1/admin/login", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ username: localEnv.AIFRED_ADMIN_USERNAME || "North3rnLight3r", password: localEnv.AIFRED_ADMIN_PASSWORD })
});
record("admin-login", login.response, { token_shape: /^[-_A-Za-z0-9]+\.[-_A-Za-z0-9]+$/.test(login.payload?.session_token || "") });
if (!login.response.ok) throw new Error("admin login failed");
const adminHeaders = { authorization: `Bearer ${login.payload.session_token}` };

for (const [name, path] of [
  ["admin-status", "/api/v1/admin/status"],
  ["admin-analytics", "/api/v1/admin/analytics"],
  ["admin-providers", "/api/v1/admin/providers"],
  ["admin-ollama", "/api/v1/admin/providers/ollama"],
  ["admin-source-files", "/api/v1/admin/source/files"],
  ["admin-source-status", "/api/v1/admin/source/status"],
  ["admin-dashboard", "/api/v1/admin/dashboard/state"],
  ["admin-site-export", "/api/v1/admin/export/site"],
  ["admin-track-export", "/api/v1/admin/export/tracks"]
]) {
  const response = await fetch(`${base}${path}`, { headers: adminHeaders });
  record(name, response, { no_store: response.headers.get("cache-control") === "no-store" });
  await response.body?.cancel();
}

const batchKey = `smoke-${randomUUID()}`;
const analyticsHeaders = {
  authorization: `Bearer ${secrets.AIFRED_ANALYTICS_API_TOKEN}`,
  "content-type": "application/json",
  "idempotency-key": batchKey,
  "x-aifred-client": "production-smoke",
  "x-aifred-product": "aifred",
  "x-aifred-channel": "official",
  "x-aifred-version": "4.0.0-alpha.2",
  "x-aifred-platform": "windows",
  "x-aifred-purpose": "deployment-smoke"
};
const analyticsBody = JSON.stringify({ events: [{ event_type: "deployment.smoke", metadata: { result: "accepted" } }] });
const accepted = await fetch(`${base}/api/v1/analytics/events`, { method: "POST", headers: analyticsHeaders, body: analyticsBody });
record("analytics-batch", accepted);
await accepted.body?.cancel();
const duplicate = await fetch(`${base}/api/v1/analytics/events`, { method: "POST", headers: analyticsHeaders, body: analyticsBody });
record("analytics-idempotency", duplicate, { expected_conflict: duplicate.status === 409 });
await duplicate.body?.cancel();

if (expectProvider) {
  const metricDefinitions = [
    ["sample_peak", "dBFS"], ["rms", "dBFS"], ["true_peak", "dBTP"],
    ["momentary_loudness", "LUFS"], ["short_term_loudness", "LUFS"], ["integrated_loudness", "LUFS"],
    ["loudness_range", "LU"], ["broadband_crest", "dB"], ["correlation", "ratio"],
    ["left_energy", "dBFS"], ["right_energy", "dBFS"], ["mid_energy", "dBFS"], ["side_energy", "dBFS"],
    ["left_right_balance", "dB"], ["side_to_mid", "dB"], ["width", "percent"]
  ];
  const measured = new Map([
    ["true_peak", -19.99999987],
    ["integrated_loudness", -22.58966596],
    ["loudness_range", 10]
  ]);
  const centres = [20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 350, 450, 600, 750, 850, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, 18000, 20000];
  const context = {
    schema: "aifred.filtered-mix.v1",
    product_channel: "official",
    product_version: "4.0.0-alpha.2",
    plugin_instance_id: `smoke-${randomUUID()}`,
    session_id: `smoke-${randomUUID()}`,
    profile_id: "MIX_BALANCED",
    profile_version: 1,
    observation_id: "native-48khz-fixture",
    observation_state: "available",
    fixture: "48 kHz stereo 1 kHz sine, 20 s at -20 dBFS peak then 20 s at -30 dBFS peak",
    session_context: [],
    metrics: metricDefinitions.map(([metric, unit]) => ({ metric, unit, available: measured.has(metric), ...(measured.has(metric) ? { typical: measured.get(metric) } : {}) })),
    bands: centres.map((centre_hz) => ({ metric: "band_energy", unit: "dBFS", available: false, centre_hz }))
  };
  const chatHeaders = {
    authorization: `Bearer ${secrets.AIFRED_API_TOKEN}`,
    "content-type": "application/json",
    "x-aifred-client": context.plugin_instance_id,
    "x-aifred-product": "aifred",
    "x-aifred-channel": "official",
    "x-aifred-version": "4.0.0-alpha.2",
    "x-aifred-platform": "windows",
    "x-aifred-purpose": "deployment-smoke"
  };
  const content = JSON.stringify({ message: "Briefly identify the measured integrated loudness, true peak, and LRA in this explicit validation fixture.", context });
  const nonStreaming = await jsonRequest("/api/v1/chat/completions", {
    method: "POST",
    headers: { ...chatHeaders, "idempotency-key": `chat-${randomUUID()}` },
    body: JSON.stringify({ model: "aifred:latest", stream: false, messages: [{ role: "user", content }] })
  });
  record("chat-json", nonStreaming.response, {
    object: nonStreaming.payload?.object || "",
    choice_count: nonStreaming.payload?.choices?.length || 0,
    finish_reason: nonStreaming.payload?.choices?.[0]?.finish_reason || "",
    content_nonempty: Boolean(nonStreaming.payload?.choices?.[0]?.message?.content)
  });
  const streaming = await fetch(`${base}/api/v1/chat/completions`, {
    method: "POST",
    headers: { ...chatHeaders, "idempotency-key": `chat-${randomUUID()}` },
    body: JSON.stringify({ model: "aifred:latest", stream: true, messages: [{ role: "user", content }] })
  });
  const streamText = await streaming.text();
  const dataLines = streamText.split(/\r?\n/).filter((line) => line.startsWith("data: "));
  let jsonValid = true;
  for (const line of dataLines) {
    const value = line.slice(6).trim();
    if (value !== "[DONE]") {
      try { JSON.parse(value); } catch { jsonValid = false; }
    }
  }
  record("chat-sse", streaming, {
    content_type: streaming.headers.get("content-type") || "",
    data_lines: dataLines.length,
    json_valid: jsonValid,
    done: dataLines.at(-1)?.trim() === "data: [DONE]"
  });
  const providerTest = await fetch(`${base}/api/v1/admin/providers/ollama/test`, { method: "POST", headers: adminHeaders });
  record("admin-provider-test", providerTest);
  await providerTest.body?.cancel();
}

const logout = await fetch(`${base}/api/v1/admin/logout`, { method: "POST", headers: adminHeaders });
record("admin-logout", logout);
await logout.body?.cancel();

const requiredFailures = results.filter((item) => !item.ok && !(item.name === "analytics-idempotency" && item.expected_conflict));
console.log(JSON.stringify({ base, results, passed: requiredFailures.length === 0 }, null, 2));
if (requiredFailures.length) process.exitCode = 1;
