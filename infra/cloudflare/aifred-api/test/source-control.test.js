import assert from "node:assert/strict";
import test from "node:test";
import {
  EDITABLE_WEBSITE_FILES,
  readApprovedSourceFile,
  saveApprovedSourceFile,
  sourceControlStatus,
  validateSourceDraft
} from "../src/source-control.js";

const filePath = "apps/website/assets/data/beat_catalog.json";
const sourceSha = "1".repeat(40);

function githubFile(content) {
  return {
    type: "file",
    sha: sourceSha,
    content: Buffer.from(content, "utf8").toString("base64")
  };
}

test("mobile website source inventory is an exact text-file allowlist", () => {
  assert.equal(EDITABLE_WEBSITE_FILES.length, 8);
  assert.equal(EDITABLE_WEBSITE_FILES.every((item) => item.path.startsWith("apps/website/")), true);
  assert.throws(() => validateSourceDraft("apps/website/../.env", "secret"), /not approved/);
  assert.throws(() => validateSourceDraft("apps/website/assets/brand/logo.png", "binary"), /not approved/);
});

test("source validation rejects malformed structured documents", () => {
  assert.throws(() => validateSourceDraft(filePath, "{broken"), /JSON source content is invalid/);
  assert.throws(() => validateSourceDraft("apps/website/index.html", "<main>fragment</main>"), /html document element/);
  assert.deepEqual(
    validateSourceDraft(filePath, "[]"),
    { ok: true, path: filePath, label: "Catalog", kind: "json", bytes: 2 }
  );
});

test("source read uses the configured Official repository and returns the optimistic SHA", async () => {
  let requestUrl = "";
  let authorization = "";
  const result = await readApprovedSourceFile(
    { GITHUB_TOKEN: "server-only", AIFRED_GITHUB_REPO: "kaeganscott26/AIFRED_Official-", AIFRED_GITHUB_BRANCH: "main" },
    filePath,
    async (url, init) => {
      requestUrl = url;
      authorization = init.headers.authorization;
      return Response.json(githubFile("[]"));
    }
  );
  assert.match(requestUrl, /kaeganscott26\/AIFRED_Official-\/contents\/apps\/website\/assets\/data\/beat_catalog\.json\?ref=main$/);
  assert.equal(authorization, "Bearer server-only");
  assert.equal(result.sha, sourceSha);
  assert.equal(result.content, "[]");
});

test("source save requires a loaded SHA and sends one bounded GitHub update", async () => {
  await assert.rejects(
    saveApprovedSourceFile({ GITHUB_TOKEN: "server-only" }, { path: filePath, content: "[]" }, async () => Response.json({})),
    /load the current website source/
  );

  let method = "";
  let body = {};
  const result = await saveApprovedSourceFile(
    { GITHUB_TOKEN: "server-only", AIFRED_PAGES_PROJECT: "aifred-site" },
    { path: filePath, content: "[]", expected_sha: sourceSha },
    async (_url, init) => {
      method = init.method;
      body = JSON.parse(init.body);
      return Response.json({ content: { sha: "2".repeat(40) }, commit: { sha: "3".repeat(40) } });
    }
  );
  assert.equal(method, "PUT");
  assert.equal(body.sha, sourceSha);
  assert.equal(Buffer.from(body.content, "base64").toString("utf8"), "[]");
  assert.equal(result.deployment.verified, false);
});

test("source status reports credential presence without exposing it", () => {
  const status = sourceControlStatus({ GITHUB_TOKEN: "never-return-this" });
  assert.equal(status.configured, true);
  assert.equal(status.repository, "kaeganscott26/AIFRED_Official-");
  assert.doesNotMatch(JSON.stringify(status), /never-return-this/);
});
