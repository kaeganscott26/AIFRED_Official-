import assert from "node:assert/strict";
import test from "node:test";

import backend from "../apps/website/lib/backend/index.js";
import siteWorker from "../apps/website/_worker.js";
import { sha256Hex } from "../apps/website/lib/backend/http.js";
import { releaseAsset, releaseForChannel, publicReleaseManifest } from "../apps/website/lib/release-manifest.js";
import { validateFilteredContext } from "../apps/website/lib/backend/handlers.js";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import {
  EDITABLE_WEBSITE_FILES,
  readApprovedSourceFile,
  saveApprovedSourceFile,
  validateSourceDraft
} from "../apps/website/lib/backend/source-control.js";

function context() {
  const pending = [];
  return {
    waitUntil(promise) { pending.push(Promise.resolve(promise)); },
    async flush() { await Promise.all(pending); }
  };
}

test("preview browser configuration stays on its own origin", () => {
  const window = { location: { origin: "https://recovery.aifred-site.pages.dev" } };
  vm.runInNewContext(readFileSync(new URL('../apps/website/config.js', import.meta.url), 'utf8'), { window, URL });
  assert.equal(window.AIFRED_CONFIG.apiV1Base, window.location.origin + '/api/v1');
});

test("public release listing excludes the unpublished release", () => {
  assert.deepEqual(publicReleaseManifest().map(r => r.channel), ['beta']);
});

test("the Pages backend accepts both client channels without changing measurement validation", () => {
  const metrics = [
    ['sample_peak','dBFS'], ['rms','dBFS'], ['true_peak','dBTP'],
    ['momentary_loudness','LUFS'], ['short_term_loudness','LUFS'], ['integrated_loudness','LUFS'],
    ['loudness_range','LU'], ['broadband_crest','dB'], ['correlation','ratio'],
    ['left_energy','dBFS'], ['right_energy','dBFS'], ['mid_energy','dBFS'], ['side_energy','dBFS'],
    ['left_right_balance','dB'], ['side_to_mid','dB'], ['width','percent']
  ];
  const centres = [20,30,40,50,60,70,80,90,100,150,200,250,350,450,600,750,850,1000,1500,2000,3000,4000,6000,8000,10000,12000,14000,16000,18000,20000];
  const payload = {
    schema:'aifred.filtered-mix.v1', product_version:'test', plugin_instance_id:'instance',
    session_id:'session', profile_id:'MIX_BALANCED', profile_version:1, observation_id:'1', session_context:[],
    metrics:metrics.map(([metric,unit])=>({metric,unit,available:false})),
    bands:centres.map(centre_hz=>({metric:'band_energy',unit:'dBFS',available:false,centre_hz}))
  };
  for (const channel of ['beta', 'official']) {
    payload.product_channel = channel;
    assert.equal(validateFilteredContext(payload).product_channel, channel);
  }
  payload.bands[16].centre_hz = 300;
  assert.throws(() => validateFilteredContext(payload), /frequency contract/);
});

test("website metadata submission reaches its handler without native client authentication", async () => {
  const env = adminEnv(await sha256Hex('password'));
  const response = await request(env, '/api/v1/analysis/submit', {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({metrics:{}})
  });
  assert.equal(response.status, 400);
  assert.equal((await response.json()).error, 'invalid_browser_analysis');
});

class FakeStatement {
  constructor(db, sql) {
    this.db = db;
    this.sql = sql.replace(/\s+/g, " ").trim();
    this.values = [];
  }

  bind(...values) {
    this.values = values;
    return this;
  }

  async first() {
    if (this.sql.includes("INSERT INTO rate_limits")) {
      const key = this.values.slice(0, 3).join("|");
      const count = (this.db.rateLimits.get(key) || 0) + 1;
      this.db.rateLimits.set(key, count);
      return { count };
    }
    if (this.sql.includes("FROM admin_sessions")) {
      const session = this.db.sessions.get(this.values[0]);
      return session && session.expires_at > this.values[1] ? session : null;
    }
    return null;
  }

  async all() {
    return { results: [] };
  }

  async run() {
    if (this.sql.startsWith("INSERT INTO admin_sessions")) {
      const [id, username, created_at, expires_at] = this.values;
      this.db.sessions.set(id, { id, username, created_at, expires_at });
    } else if (this.sql.startsWith("DELETE FROM admin_sessions WHERE id")) {
      this.db.sessions.delete(this.values[0]);
    }
    return { meta: { changes: 1 } };
  }

  async batchResult() {
    if (this.sql.startsWith("SELECT SUM(requests)")) return { results: [{}] };
    if (this.sql.startsWith("SELECT")) return { results: [] };
    await this.run();
    return { results: [], meta: { changes: 1 } };
  }
}

class FakeD1 {
  constructor() {
    this.sessions = new Map();
    this.rateLimits = new Map();
  }

  prepare(sql) { return new FakeStatement(this, sql); }
  async batch(statements) { return Promise.all(statements.map((statement) => statement.batchResult())); }
}

function headFor(asset) {
  return {
    size: asset.size_bytes,
    httpEtag: '"test-etag"',
    writeHttpMetadata(headers) { headers.set("content-type", asset.content_type); }
  };
}

function releaseBucket() {
  return {
    async head(key) {
      for (const name of ["setup", "zip"]) {
        const asset = releaseAsset("beta", name).asset;
        if (asset.r2_key === key) return headFor(asset);
      }
      return null;
    },
    async get(key, options) {
      const asset = ["setup", "zip"].map((name) => releaseAsset("beta", name).asset).find((item) => item.r2_key === key);
      if (!asset) return null;
      const length = Math.max(1, Math.min(options?.range?.length || 4, 1024));
      return { size: asset.size_bytes, body: new Response(new Uint8Array(length).fill(7)).body };
    }
  };
}

function adminEnv(passwordHash) {
  return {
    AIFRED_ADMIN_USERNAME: "operator",
    AIFRED_ADMIN_PASSWORD_SHA256: passwordHash,
    AIFRED_ADMIN_SESSION_SECRET: "unit-test-session-secret",
    AIFRED_OPS: new FakeD1(),
    AIFRED_DOWNLOADS: releaseBucket(),
    AIFRED_ANALYTICS: { writeDataPoint() {} },
    ASSETS: {
      async fetch(request) {
        return new URL(request.url).pathname === "/assets/data/beat_catalog.json"
          ? Response.json([{ id: "track-1", title: "Track" }])
          : new Response("not found", { status: 404 });
      }
    }
  };
}

async function request(env, path, init = {}) {
  const ctx = context();
  const response = await backend.fetch(new Request(`https://preview.example${path}`, init), env, ctx);
  await ctx.flush();
  return response;
}

test("release manifest pins the validated Windows artifacts and advertises no macOS asset", () => {
  const beta = releaseForChannel("beta");
  assert.equal(beta.tag, "v0.3.6-beta-stable");
  assert.equal(beta.assets.setup.filename, "AIFRED-VST3-Setup.exe");
  assert.equal(beta.artifact_source, "out/windows-x64/current");
  assert.equal(beta.artifact_git_sha, "ec922b930205f7dc0accdefa733fa357df95bcf6");
  assert.equal(beta.assets.setup.size_bytes, 53930848);
  assert.equal(beta.assets.setup.sha256, "d0731bfa6afdf5af02e9429bd03a847d7d06df1e549760c04fe5548bb3ae3421");
  assert.equal(beta.assets.zip.filename, "AIFRED-VST3-windows.zip");
  assert.equal(beta.assets.zip.size_bytes, 2363132);
  assert.equal(beta.assets.zip.sha256, "9cbcebbefe1928bbd7f5fd533abbc3136d7fcbcd6059ec72fbb3d108305a8d36");
  assert.equal(beta.assets.macos, undefined);
});

test("Advanced Mode dispatches backend routes and falls through to ASSETS", async () => {
  const env = adminEnv(await sha256Hex("password"));
  const ctx = context();
  const health = await siteWorker.fetch(new Request("https://preview.example/health"), env, ctx);
  assert.equal(health.status, 200);
  assert.equal((await health.json()).service, "aifred-site");
  const asset = await siteWorker.fetch(new Request("https://preview.example/assets/data/beat_catalog.json"), env, ctx);
  assert.equal(asset.status, 200);
  assert.equal((await asset.json())[0].id, "track-1");
  await ctx.flush();
});

test("the shared Android/admin contract exposes a public registry and authenticated allowlisted command route", async () => {
  const env = adminEnv(await sha256Hex("password"));
  const registry = await request(env, "/api/v1/registry/actions");
  assert.equal(registry.status, 200);
  const registryBody = await registry.json();
  assert.equal(registryBody.ok, true);
  assert.ok(registryBody.actions.some((action) => action.id === "health"));

  const settings = await request(env, "/api/v1/chat/settings");
  assert.equal(settings.status, 200);
  assert.equal((await settings.json()).settings.transport_mode, "http");

  const unauthorized = await request(env, "/api/v1/command/run", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ command_line: "health" })
  });
  assert.equal(unauthorized.status, 401);

  const login = await request(env, "/api/v1/admin/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ username: "operator", password: "password" })
  });
  const token = (await login.json()).session_token;
  const command = await request(env, "/api/v1/command/run", {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${token}` },
    body: JSON.stringify({ command_line: "health" })
  });
  assert.equal(command.status, 200);
  const commandBody = await command.json();
  assert.equal(commandBody.ok, true);
  assert.match(commandBody.stdout, /aifred-site/);
});

test("download HEAD returns exact filename, type, size, ETag, and manifest hash", async () => {
  const env = adminEnv(await sha256Hex("password"));
  for (const [name, filename, type, size] of [
    ["setup", "AIFRED-VST3-Setup.exe", "application/vnd.microsoft.portable-executable", "53930848"],
    ["zip", "AIFRED-VST3-windows.zip", "application/zip", "2363132"]
  ]) {
    const response = await request(env, `/api/v1/downloads/plugin?channel=beta&asset=${name}`, { method: "HEAD" });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("content-disposition"), `attachment; filename="${filename}"`);
    assert.equal(response.headers.get("content-type"), type);
    assert.equal(response.headers.get("content-length"), size);
    assert.equal(response.headers.get("etag"), '"test-etag"');
    assert.match(response.headers.get("x-aifred-sha256"), /^[a-f0-9]{64}$/);
  }
});

test("download range requests return 206 with bounded metadata and a nonempty body", async () => {
  const env = adminEnv(await sha256Hex("password"));
  const response = await request(env, "/api/v1/downloads/plugin?channel=beta&asset=zip", {
    headers: { range: "bytes=0-99" }
  });
  assert.equal(response.status, 206);
  assert.equal(response.headers.get("content-range"), "bytes 0-99/2363132");
  assert.equal(response.headers.get("content-length"), "100");
  assert.equal((await response.arrayBuffer()).byteLength, 100);
});

test("unknown or unpublished downloads return structured non-200 JSON", async () => {
  const env = adminEnv(await sha256Hex("password"));
  const unknown = await request(env, "/api/v1/downloads/plugin?channel=beta&asset=macos");
  assert.equal(unknown.status, 400);
  assert.equal((await unknown.json()).error, "invalid_asset");
  const unpublished = await request(env, "/api/v1/downloads/plugin?channel=flagship&asset=setup");
  assert.equal(unpublished.status, 404);
  assert.equal((await unpublished.json()).error, "release_unavailable");
});

test("missing public Beta R2 object never falls back to a stale external binary", async () => {
  const env = adminEnv(await sha256Hex("password"));
  env.AIFRED_DOWNLOADS = { async head() { return null; } };
  const response = await request(env, "/api/v1/downloads/plugin?channel=beta&asset=setup");
  assert.equal(response.status, 503);
  assert.equal((await response.json()).error, "release_artifact_unavailable");
});

test("admin login, session verification, exports, and logout use the D1 session boundary", async () => {
  const env = adminEnv(await sha256Hex("password"));
  const invalid = await request(env, "/api/v1/admin/login", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ username: "operator", password: "wrong" })
  });
  assert.equal(invalid.status, 401);

  const login = await request(env, "/api/v1/admin/login", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ username: "operator", password: "password" })
  });
  assert.equal(login.status, 200);
  const token = (await login.json()).session_token;
  assert.ok(token.includes("."));

  const status = await request(env, "/api/v1/admin/status", { headers: { authorization: `Bearer ${token}` } });
  assert.equal(status.status, 200);
  assert.equal((await status.json()).architecture, "pages-advanced-mode");

  const siteExport = await request(env, "/api/v1/admin/export/site", { headers: { authorization: `Bearer ${token}` } });
  assert.equal(siteExport.status, 200);
  assert.equal(siteExport.headers.get("content-disposition"), 'attachment; filename="aifred-site-export.json"');
  const trackExport = await request(env, "/api/v1/admin/export/tracks", { headers: { authorization: `Bearer ${token}` } });
  assert.equal(trackExport.status, 200);

  const logout = await request(env, "/api/v1/admin/logout", { method: "POST", headers: { authorization: `Bearer ${token}` } });
  assert.equal(logout.status, 200);
  const revoked = await request(env, "/api/v1/admin/status", { headers: { authorization: `Bearer ${token}` } });
  assert.equal(revoked.status, 401);
});

test("mobile source editing remains an exact existing-text-file allowlist", () => {
  assert.equal(EDITABLE_WEBSITE_FILES.length, 8);
  assert.equal(EDITABLE_WEBSITE_FILES.every((file) => file.path.startsWith("apps/website/")), true);
  assert.deepEqual(validateSourceDraft("apps/website/config.js", "window.AIFRED_CONFIG = {};"), {
    ok: true,
    path: "apps/website/config.js",
    label: "Public config",
    kind: "javascript",
    bytes: 26
  });
  assert.throws(() => validateSourceDraft("apps/website/../.env", "secret"), /not approved/);
  assert.throws(() => validateSourceDraft("apps/website/assets/brand/logo.png", "binary"), /not approved/);
  assert.throws(() => validateSourceDraft("apps/website/styles.css", "```css\nbody {}\n```"), /Markdown fences/);
  assert.throws(() => validateSourceDraft("apps/website/config.js", "<<<<<<< current\nwindow.x = 1;\n=======\nwindow.x = 2;\n>>>>>>> incoming"), /merge markers/);
});

test("mobile source read and save target Official with optimistic concurrency", async () => {
  const sha = "1".repeat(40);
  const nextSha = "2".repeat(40);
  const env = {
    GITHUB_TOKEN: "test-token",
    AIFRED_GITHUB_REPO: "kaeganscott26/AIFRED_Official-",
    AIFRED_GITHUB_BRANCH: "main",
    AIFRED_PAGES_PROJECT: "aifred-site"
  };
  const calls = [];
  const fetchImpl = async (url, init = {}) => {
    calls.push({ url, init });
    if ((init.method || "GET") === "GET") {
      return Response.json({
        type: "file",
        sha,
        content: btoa("window.AIFRED_CONFIG = {};")
      });
    }
    return Response.json({ commit: { sha: "3".repeat(40) }, content: { sha: nextSha } });
  };

  const loaded = await readApprovedSourceFile(env, "apps/website/config.js", fetchImpl);
  assert.equal(loaded.repository, "kaeganscott26/AIFRED_Official-");
  assert.equal(loaded.sha, sha);

  const saved = await saveApprovedSourceFile(env, {
    path: "apps/website/config.js",
    content: "window.AIFRED_CONFIG = {};",
    expected_sha: sha
  }, fetchImpl);
  assert.equal(saved.previous_sha, sha);
  assert.equal(saved.source_sha, nextSha);
  assert.equal(saved.deployment.verified, false);
  const update = JSON.parse(calls[1].init.body);
  assert.equal(update.sha, sha);
  assert.equal(update.branch, "main");
  assert.equal(calls[1].init.method, "PUT");
  assert.match(calls[1].url, /kaeganscott26\/AIFRED_Official-\/contents\/apps\/website\/config\.js$/);
});
