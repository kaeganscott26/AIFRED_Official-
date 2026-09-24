import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const sourceRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));
const tool = join(sourceRoot, "tools/aifred-archive.mjs");

function invoke(root, ...arguments_) {
  const result = spawnSync(process.execPath, [tool, ...arguments_], {
    cwd: root,
    env: { ...process.env, AIFRED_REPO_ROOT: root, AIFRED_FORGE_ACTIVE_LOG_LIMIT_MB: "0.000001" },
    encoding: "utf8"
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

function completedRun(root, name, file, content) {
  const directory = join(root, "integrations/forge/exports/history", name);
  mkdirSync(directory, { recursive: true });
  writeFileSync(join(directory, file), content);
  writeFileSync(join(directory, "run.json"), JSON.stringify({ status: "completed", completed_at: new Date().toISOString() }));
  writeFileSync(join(directory, ".complete"), "completed\n");
}

test("archive rotation verifies, searches, restores, rebuilds and prunes", () => {
  const root = mkdtempSync(join(tmpdir(), "aifred-archive-test-"));
  try {
    mkdirSync(join(root, "config"), { recursive: true });
    writeFileSync(join(root, "config/aifred-admin.json"), JSON.stringify({
      archive: {
        root: "runtime/aifred-archive",
        activeRoot: "integrations/forge/exports/history",
        workspace: "integrations/forge/archive-workspace",
        thresholdEnvironmentVariable: "AIFRED_FORGE_ACTIVE_LOG_LIMIT_MB",
        defaultThresholdMb: 25
      }
    }));
    const lockPath = join(root, "runtime/aifred-archive/.archive.lock");
    mkdirSync(join(root, "runtime/aifred-archive"), { recursive: true });
    writeFileSync(lockPath, "other process\n");
    const locked = spawnSync(process.execPath, [tool, "archive", "--force"], {
      cwd: root,
      env: { ...process.env, AIFRED_REPO_ROOT: root },
      encoding: "utf8"
    });
    assert.notEqual(locked.status, 0);
    assert.equal(readFileSync(lockPath, "utf8"), "other process\n");
    rmSync(lockPath);
    completedRun(root, "2026-09-20T00-00-00.000Z", "site.json", '{"message":"first error"}');
    completedRun(root, "2026-09-21T00-00-00.000Z", "tracks.json", '{"track":"second"}');
    completedRun(root, "2026-09-22T00-00-00.000Z", "site.json", '{"message":"newest"}');

    const archived = invoke(root, "archive", "--force");
    assert.equal(archived.archived, true);
    assert.equal(archived.archive.completed_runs.length, 2);
    assert.equal(existsSync(join(root, "integrations/forge/exports/history/2026-09-22T00-00-00.000Z")), true);

    const verified = invoke(root, "verify");
    assert.equal(verified.verified.length, 1);
    assert.equal(verified.verified[0].records, 6);

    const search = invoke(root, "search", "--query", "first error", "--limit", "10", "--byte-limit", "4096");
    assert.equal(search.records.length, 1);
    assert.equal(search.records[0].relative_path, "site.json");

    const restored = invoke(root, "restore", "--category", "site", "--limit", "10", "--byte-limit", "4096");
    assert.equal(restored.records >= 1, true);
    assert.match(readFileSync(join(root, "integrations/forge/archive-workspace/2026-09-20T00-00-00.000Z/site.json"), "utf8"), /first error/);

    const rebuilt = invoke(root, "rebuild-index");
    assert.equal(rebuilt.archives, 1);
    const listed = invoke(root, "list");
    const archiveId = listed.archives[0].archive_id;
    const pruned = invoke(root, "prune", "--id", archiveId, "--confirm");
    assert.equal(pruned.pruned, archiveId);
    assert.equal(invoke(root, "verify").verified.length, 0);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
