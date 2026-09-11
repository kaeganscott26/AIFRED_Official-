import assert from "node:assert/strict";
import test from "node:test";
import { corsHeaders, readJson, sha256Hex } from "../src/http.js";
import { requestedReleaseChannel, routeRequest, validateFilteredContext } from "../src/handlers.js";
import { classifyBrowserReference } from "../src/reference-gate.js";

test("public health is lightweight and does not require bindings", async () => {
  const request = new Request("https://north3rnlight3r.com/api/health");
  const response = await routeRequest(request, {}, { waitUntil() {} }, {});
  assert.equal(response.status, 200);
  assert.equal((await response.json()).service, "aifred-api");
});

test("bounded JSON reader accepts a small object", async () => {
  const request = new Request("https://example.test", { method: "POST", body: JSON.stringify({ ok: true }) });
  assert.deepEqual(await readJson(request, 64), { ok: true });
});

test("CORS only reflects approved origins", () => {
  const allowed = corsHeaders(new Request("https://north3rnlight3r.com/api/health", { headers: { origin: "https://north3rnlight3r.com" } }));
  const denied = corsHeaders(new Request("https://north3rnlight3r.com/api/health", { headers: { origin: "https://attacker.example" } }));
  assert.equal(allowed.get("access-control-allow-origin"), "https://north3rnlight3r.com");
  assert.equal(denied.get("access-control-allow-origin"), null);
});

test("SHA-256 helper returns a lowercase verifier", async () => {
  assert.match(await sha256Hex("test"), /^[a-f0-9]{64}$/);
});

test("release channel selection is explicit and bounded", () => {
  assert.equal(requestedReleaseChannel(new Request("https://example.test/api/v1/releases/current?channel=beta")), "beta");
  assert.equal(requestedReleaseChannel(new Request("https://example.test/api/v1/downloads/plugin"), "beta"), "beta");
  assert.throws(
    () => requestedReleaseChannel(new Request("https://example.test/api/v1/releases/current?channel=private")),
    /beta or flagship/
  );
});

test("both plugin channels use the same FilteredMixContext contract", () => {
  const metrics = [
    ["sample_peak", "dBFS"], ["rms", "dBFS"], ["true_peak", "dBTP"],
    ["momentary_loudness", "LUFS"], ["short_term_loudness", "LUFS"], ["integrated_loudness", "LUFS"],
    ["loudness_range", "LU"], ["broadband_crest", "dB"], ["correlation", "ratio"],
    ["left_energy", "dBFS"], ["right_energy", "dBFS"], ["mid_energy", "dBFS"], ["side_energy", "dBFS"],
    ["left_right_balance", "dB"], ["side_to_mid", "dB"], ["width", "percent"]
  ];
  const centres = [20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 350, 450, 600, 750, 850, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, 18000, 20000];
  for (const product_channel of ["beta", "official"]) {
    const context = {
      schema: "aifred.filtered-mix.v1", product_channel, product_version: "test", plugin_instance_id: "instance",
      session_id: "session", profile_id: "MIX_BALANCED", profile_version: 1, observation_id: "observation", session_context: [],
      metrics: metrics.map(([metric, unit]) => ({ metric, unit, available: false })),
      bands: centres.map((centre_hz) => ({ metric: "band_energy", unit: "dBFS", available: false, centre_hz }))
    };
    assert.equal(validateFilteredContext(context), context);
  }
});

test("public website analysis preserves the gate and persists only accepted sanitized metadata to D1", async () => {
  const inserts = [];
  const queued = [];
  const env = {
    ANALYSIS_RATE_LIMITER: { async limit() { return { success: true }; } },
    AIFRED_EVENTS_QUEUE: { async send(message) { queued.push(message); } },
    AIFRED_OPS: {
      prepare(sql) {
        return {
          bind(...values) {
            return { async run() { inserts.push({ sql, values }); return { meta: { changes: 1 } }; } };
          }
        };
      }
    }
  };
  const pending = [];
  const ctx = { waitUntil(promise) { pending.push(Promise.resolve(promise)); } };
  const trace = { requestId: "request", d1Writes: 0, queueEvents: 0, rateLimitOutcome: "not_applicable" };
  const response = await routeRequest(new Request("https://north3rnlight3r.com/api/v1/analysis/submit", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      file_name: "C:\\private\\user-name.wav",
      duration_seconds: 123.4,
      metrics: { tone_balance: 80, integrated_lufs: -11, peak_dbfs: -1, crest_factor_db: 11, stereo_width: 0.6, low_end_control: 70, harshness_control: 75, spectral_centroid_hz: 1800 }
    })
  }), env, ctx, trace);
  await Promise.all(pending);
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.accepted, true);
  assert.equal(payload.persistence, "stored");
  assert.equal(inserts.length, 1);
  assert.match(inserts[0].sql, /INSERT INTO references_catalog/);
  assert.match(inserts[0].values[1], /^Website reference /);
  assert.doesNotMatch(JSON.stringify(inserts[0].values), /user-name|private/);
  assert.equal(JSON.parse(inserts[0].values[4]).integrated_lufs, -11);
  assert.equal(JSON.parse(inserts[0].values[5]).classification, "Strong Reference");
  assert.equal(queued[0].event_type, "website.analysis.submitted");
});

test("reference gate retains the existing broad style-aware acceptance behavior", () => {
  const result = classifyBrowserReference({ tone_balance: 75, integrated_lufs: -10, peak_dbfs: -0.8, crest_factor_db: 10, stereo_width: 0.5, low_end_control: 80, harshness_control: 80, spectral_centroid_hz: 2000 });
  assert.equal(result.accepted, true);
  assert.equal(result.classification, "Strong Reference");
});
