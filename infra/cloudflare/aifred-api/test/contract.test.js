import assert from "node:assert/strict";
import test from "node:test";
import { validateFilteredContext } from "../src/handlers.js";
import { providerConfiguration } from "../src/providers.js";
import { consumeBatch } from "../src/telemetry.js";

const metrics = [
  ["sample_peak", "dBFS"], ["rms", "dBFS"], ["true_peak", "dBTP"],
  ["momentary_loudness", "LUFS"], ["short_term_loudness", "LUFS"], ["integrated_loudness", "LUFS"],
  ["loudness_range", "LU"], ["broadband_crest", "dB"], ["correlation", "ratio"],
  ["left_energy", "dBFS"], ["right_energy", "dBFS"], ["mid_energy", "dBFS"], ["side_energy", "dBFS"],
  ["left_right_balance", "dB"], ["side_to_mid", "dB"], ["width", "percent"]
];
const centres = [20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 350, 450, 600, 750, 850, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 10000, 12000, 14000, 16000, 18000, 20000];

function context() {
  return {
    schema: "aifred.filtered-mix.v1",
    product_channel: "official",
    product_version: "4.0.0-alpha.2",
    plugin_instance_id: "instance-1",
    session_id: "session-1",
    profile_id: "MIX_BALANCED",
    profile_version: 1,
    observation_id: "1",
    session_context: [],
    metrics: metrics.map(([metric, unit]) => ({ metric, unit, available: false })),
    bands: centres.map((centre_hz) => ({ metric: "band_energy", unit: "dBFS", available: false, centre_hz }))
  };
}

test("FilteredMixContext matches the native 16-metric and 30-band contract", () => {
  assert.equal(validateFilteredContext(context()).schema, "aifred.filtered-mix.v1");
});

test("FilteredMixContext rejects metadata-only and altered DSP identities", () => {
  assert.throws(() => validateFilteredContext({ schema: "aifred.filtered-mix.v1" }), /required/);
  const altered = context();
  altered.bands[16].centre_hz = 300;
  assert.throws(() => validateFilteredContext(altered), /frequency contract/);
});

test("provider status does not expose secret values", () => {
  const result = JSON.stringify(providerConfiguration({
    AIFRED_CHAT_PROVIDER: "ollama",
    OLLAMA_BASE_URL: "https://ollama.north3rnlight3r.com",
    OLLAMA_MODEL: "aifred:latest",
    OLLAMA_API_TOKEN: "do-not-expose",
    OLLAMA_ACCESS_CLIENT_ID: "id",
    OLLAMA_ACCESS_CLIENT_SECRET: "also-do-not-expose"
  }));
  assert.doesNotMatch(result, /do-not-expose/);
  assert.doesNotMatch(result, /also-do-not-expose/);
});

test("queue consumer binds only D1-supported values and acknowledges after the batch", async () => {
  const bound = [];
  let acknowledged = false;
  const env = {
    AIFRED_OPS: {
      prepare(sql) {
        return { bind(...values) { bound.push({ sql, values }); return { sql, values }; } };
      },
      async batch(statements) { assert.equal(statements.length, 3); }
    }
  };
  await consumeBatch({
    messages: [
      { body: { kind: "request", minute: "2026-09-09T04:30:00.000Z", route: "/health", client_key: "client", product: "", channel: "", purpose: "", status: 200, rate_limit_outcome: "not_applicable", cache_status: "BYPASS", provider_calls: 0, d1_writes: 0, queue_events: 0, r2_downloads: 0 } },
      { body: { kind: "activity", id: "event", created_at: "2026-09-09T04:30:00.000Z", event_type: "deployment.smwriter", status: 202, metadata: {} } }
    ],
    ackAll() { acknowledged = true; }
  }, env);
  assert.equal(acknowledged, true);
  assert.equal(bound.flatMap((entry) => entry.values).some((value) => value === undefined), false);
});
