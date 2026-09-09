import assert from "node:assert/strict";
import test from "node:test";
import { corsHeaders, readJson, sha256Hex } from "../src/http.js";
import { routeRequest } from "../src/handlers.js";

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
