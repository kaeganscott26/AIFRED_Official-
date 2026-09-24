#!/usr/bin/env node
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const exportsRoot = join(repositoryRoot, "integrations/forge/exports");
const historyRoot = join(exportsRoot, "history");
const latestRoot = join(exportsRoot, "latest");
const token = String(process.env.AIFRED_ADMIN_SESSION_TOKEN || "");
const base = String(process.env.AIFRED_API_BASE_URL || "https://north3rnlight3r.com").replace(/\/+$/, "").replace(/\/(?:api\/v1|api|v1)$/i, "");
const mode = process.argv[2] || "all";
if (!["all", "site", "tracks"].includes(mode)) throw new Error("Usage: export.mjs all|site|tracks");
if (!token) throw new Error("AIFRED_ADMIN_SESSION_TOKEN is required.");

function digest(data) {
  return createHash("sha256").update(data).digest("hex");
}

async function exportRoute(category) {
  const route = category === "site" ? "/api/v1/admin/export/site" : "/api/v1/admin/export/tracks";
  const response = await fetch(base + route, { headers: { authorization: `Bearer ${token}`, accept: "application/json" }, cache: "no-store" });
  const body = Buffer.from(await response.arrayBuffer());
  if (!response.ok) throw new Error(`${category} export failed with HTTP ${response.status}.`);
  JSON.parse(body.toString("utf8"));
  return { category, route, body, sha256: digest(body) };
}

const categories = mode === "all" ? ["site", "tracks"] : [mode];
const exports = [];
for (const category of categories) exports.push(await exportRoute(category));
const now = new Date();
const runName = now.toISOString().replaceAll(":", "-");
const stage = join(exportsRoot, `.staging-${runName}-${process.pid}`);
const destination = join(historyRoot, runName);
mkdirSync(stage, { recursive: true });
try {
  const files = [];
  for (const item of exports) {
    const name = `${item.category}.json`;
    writeFileSync(join(stage, name), item.body);
    files.push({ category: item.category, route: item.route, path: name, size: item.body.length, sha256: item.sha256 });
  }
  const run = { schema: "aifred.forge-export-run.v1", status: "completed", completed_at: now.toISOString(), api_origin: base, files };
  writeFileSync(join(stage, "run.json"), JSON.stringify(run, null, 2) + "\n");
  writeFileSync(join(stage, ".complete"), "completed\n");
  mkdirSync(historyRoot, { recursive: true });
  renameSync(stage, destination);
  const latestCandidate = `${latestRoot}.candidate-${process.pid}`;
  const latestPrevious = `${latestRoot}.previous`;
  if (existsSync(latestCandidate) || existsSync(latestPrevious)) throw new Error("Retained latest-export recovery path requires inspection.");
  mkdirSync(latestCandidate, { recursive: true });
  for (const item of exports) writeFileSync(join(latestCandidate, `${item.category}.json`), item.body);
  writeFileSync(join(latestCandidate, "run.json"), JSON.stringify(run, null, 2) + "\n");
  if (existsSync(latestRoot)) renameSync(latestRoot, latestPrevious);
  try {
    renameSync(latestCandidate, latestRoot);
    if (existsSync(latestPrevious)) rmSync(latestPrevious, { recursive: true });
  } catch (error) {
    if (!existsSync(latestRoot) && existsSync(latestPrevious)) renameSync(latestPrevious, latestRoot);
    throw error;
  }
} catch (error) {
  rmSync(stage, { recursive: true, force: true });
  throw error;
}

const rotation = spawnSync(process.execPath, [join(repositoryRoot, "tools/aifred-archive.mjs"), "rotate"], { cwd: repositoryRoot, encoding: "utf8" });
if (rotation.status !== 0) throw new Error(rotation.stderr || "Archive rotation failed.");
console.log(JSON.stringify({ ok: true, completed_run: runName, files: exports.map((item) => ({ category: item.category, size: item.body.length, sha256: item.sha256 })), rotation: JSON.parse(rotation.stdout) }, null, 2));
