#!/usr/bin/env node
import {
  closeSync,
  existsSync,
  mkdirSync,
  openSync,
  readFileSync,
  readdirSync,
  renameSync,
  rmSync,
  statSync,
  writeFileSync
} from "node:fs";
import { createHash } from "node:crypto";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { gzipSync, gunzipSync } from "node:zlib";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(process.env.AIFRED_REPO_ROOT || fileURLToPath(new URL("..", import.meta.url)));
const configPath = resolve(process.env.AIFRED_ARCHIVE_CONFIG || join(repositoryRoot, "config/aifred-admin.json"));
const config = JSON.parse(readFileSync(configPath, "utf8"));
const archiveConfig = config.archive;
const archiveRoot = ownedPath(archiveConfig.root);
const activeRoot = ownedPath(archiveConfig.activeRoot);
const workspaceRoot = ownedPath(archiveConfig.workspace);
const manifestPath = join(archiveRoot, "manifest.json");
const maximumRecords = 1_000;
const maximumBytes = 10 * 1024 * 1024;

function ownedPath(value) {
  const result = resolve(repositoryRoot, value);
  if (result === repositoryRoot || !result.startsWith(repositoryRoot + sep)) throw new Error(`Configured path escapes repository: ${value}`);
  return result;
}

function digest(data) {
  return createHash("sha256").update(data).digest("hex");
}

function timestamp(date = new Date()) {
  return date.toISOString().replaceAll("-", "").replaceAll(":", "").replace(".", "");
}

function atomicWrite(path, data) {
  mkdirSync(dirname(path), { recursive: true });
  const pending = `${path}.pending-${process.pid}`;
  writeFileSync(pending, data);
  renameSync(pending, path);
}

function readJson(path, fallback = null) {
  if (!existsSync(path)) return fallback;
  return JSON.parse(readFileSync(path, "utf8"));
}

function emptyManifest() {
  return { schema: "aifred.archive-manifest.v1", version: "1.0.0", updated_at: null, archives: [] };
}

function manifest() {
  const current = readJson(manifestPath, emptyManifest());
  if (current.schema !== "aifred.archive-manifest.v1" || !Array.isArray(current.archives)) throw new Error("Archive manifest schema is invalid.");
  return current;
}

function walkFiles(root, current = root, output = []) {
  if (!existsSync(current)) return output;
  for (const entry of readdirSync(current, { withFileTypes: true })) {
    const path = join(current, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Symbolic links are not permitted in archive sources: ${path}`);
    if (entry.isDirectory()) walkFiles(root, path, output);
    else if (entry.isFile()) output.push(path);
  }
  return output.sort();
}

function directoryBytes(path) {
  return walkFiles(path).reduce((total, file) => total + statSync(file).size, 0);
}

function completedRun(path) {
  if (!statSync(path).isDirectory()) return false;
  if (existsSync(join(path, ".complete"))) return true;
  for (const name of ["run.json", "manifest.json"]) {
    const record = readJson(join(path, name));
    if (record && (record.status === "completed" || record.completed_at || record.completedAt)) return true;
  }
  return false;
}

function completedRuns() {
  if (!existsSync(activeRoot)) return [];
  return readdirSync(activeRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name !== "latest" && !entry.name.startsWith("."))
    .map((entry) => ({ name: entry.name, path: join(activeRoot, entry.name) }))
    .filter((entry) => completedRun(entry.path))
    .sort((left, right) => statSync(left.path).mtimeMs - statSync(right.path).mtimeMs);
}

function archiveCandidates() {
  const runs = completedRuns();
  return runs.length > 1 ? runs.slice(0, -1) : [];
}

function thresholdBytes() {
  const variable = archiveConfig.thresholdEnvironmentVariable;
  const configured = process.env[variable];
  const megabytes = configured === undefined ? archiveConfig.defaultThresholdMb : Number(configured);
  if (!Number.isFinite(megabytes) || megabytes <= 0) throw new Error(`${variable} must be a positive number.`);
  return Math.floor(megabytes * 1024 * 1024);
}

function recordCategory(path) {
  const name = path.toLowerCase();
  if (name.includes("track")) return "tracks";
  if (name.includes("site")) return "site";
  return "forge";
}

function archiveRuns(runs) {
  if (!runs.length) return { archived: false, reason: "No older completed FORGE runs are eligible." };
  const created = new Date();
  const id = `aifred-forge-context-${timestamp(created)}`;
  const records = [];
  let sourceBytes = 0;
  for (const run of runs) {
    for (const file of walkFiles(run.path)) {
      const content = readFileSync(file);
      const relativePath = relative(run.path, file).split(sep).join("/");
      sourceBytes += content.length;
      records.push({
        schema: "aifred.archive-record.v1",
        completed_run: run.name,
        category: recordCategory(relativePath),
        relative_path: relativePath,
        size: content.length,
        sha256: digest(content),
        content_base64: content.toString("base64")
      });
    }
  }
  const jsonl = Buffer.from(records.map((record) => JSON.stringify(record)).join("\n") + "\n");
  const bundle = gzipSync(jsonl, { level: 9 });
  const year = String(created.getUTCFullYear());
  const month = String(created.getUTCMonth() + 1).padStart(2, "0");
  const day = String(created.getUTCDate()).padStart(2, "0");
  const directory = join(archiveRoot, "forge-context", year, month, day);
  const bundlePath = join(directory, `${id}.jsonl.gz`);
  const metaPath = join(directory, `${id}.meta.json`);
  atomicWrite(bundlePath, bundle);
  const verified = verifyBundle(bundlePath, { expectedRecords: records.length, expectedSha256: digest(bundle) });
  const times = runs.map((run) => new Date(statSync(run.path).mtimeMs).toISOString());
  const metadata = {
    archive_id: id,
    schema: "aifred.archive.v1",
    version: "1.0.0",
    created_at: created.toISOString(),
    range_start: times.at(0),
    range_end: times.at(-1),
    completed_runs: runs.map((run) => run.name),
    record_count: verified.recordCount,
    source_bytes: sourceBytes,
    compressed_bytes: bundle.length,
    categories: [...new Set(records.map((record) => record.category))].sort(),
    sha256: digest(bundle),
    relative_path: relative(archiveRoot, bundlePath).split(sep).join("/")
  };
  atomicWrite(metaPath, JSON.stringify(metadata, null, 2) + "\n");
  const index = manifest();
  index.archives = index.archives.filter((entry) => entry.archive_id !== id);
  index.archives.push(metadata);
  index.archives.sort((left, right) => left.created_at.localeCompare(right.created_at));
  index.updated_at = new Date().toISOString();
  atomicWrite(manifestPath, JSON.stringify(index, null, 2) + "\n");
  verifyArchive(metadata);
  for (const run of runs) rmSync(run.path, { recursive: true });
  return { archived: true, archive: metadata };
}

function parseRecords(bundlePath) {
  const text = gunzipSync(readFileSync(bundlePath)).toString("utf8");
  return text.split("\n").filter(Boolean).map((line) => JSON.parse(line));
}

function verifyBundle(bundlePath, options = {}) {
  const bundle = readFileSync(bundlePath);
  if (options.expectedSha256 && digest(bundle) !== options.expectedSha256) throw new Error(`Bundle checksum mismatch: ${bundlePath}`);
  const records = parseRecords(bundlePath);
  if (options.expectedRecords !== undefined && records.length !== options.expectedRecords) throw new Error(`Bundle record count mismatch: ${bundlePath}`);
  for (const record of records) {
    if (record.schema !== "aifred.archive-record.v1" || !record.completed_run || !record.relative_path) throw new Error(`Invalid archive record: ${bundlePath}`);
    const content = Buffer.from(record.content_base64, "base64");
    if (content.length !== record.size || digest(content) !== record.sha256) throw new Error(`Archive record checksum mismatch: ${record.relative_path}`);
  }
  return { recordCount: records.length, records };
}

function verifyArchive(metadata) {
  const bundlePath = resolve(archiveRoot, metadata.relative_path);
  if (!bundlePath.startsWith(archiveRoot + sep) || !existsSync(bundlePath)) throw new Error(`Archive bundle is missing: ${metadata.archive_id}`);
  const result = verifyBundle(bundlePath, { expectedRecords: metadata.record_count, expectedSha256: metadata.sha256 });
  if (statSync(bundlePath).size !== metadata.compressed_bytes) throw new Error(`Archive byte count mismatch: ${metadata.archive_id}`);
  return result;
}

function withLock(callback) {
  mkdirSync(archiveRoot, { recursive: true });
  const lockPath = join(archiveRoot, ".archive.lock");
  let descriptor;
  try {
    descriptor = openSync(lockPath, "wx");
    return callback();
  } finally {
    if (descriptor !== undefined) {
      closeSync(descriptor);
      if (existsSync(lockPath)) rmSync(lockPath);
    }
  }
}

function parseArguments(values) {
  const result = { _: [] };
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (!value.startsWith("--")) result._.push(value);
    else if (index + 1 < values.length && !values[index + 1].startsWith("--")) result[value.slice(2)] = values[++index];
    else result[value.slice(2)] = true;
  }
  return result;
}

function boundedInteger(value, fallback, maximum, name) {
  const result = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(result) || result < 1 || result > maximum) throw new Error(`${name} must be between 1 and ${maximum}.`);
  return result;
}

function dateMatches(metadata, args) {
  const start = args.start ? Date.parse(args.start) : Number.NEGATIVE_INFINITY;
  const end = args.end ? Date.parse(args.end) : Number.POSITIVE_INFINITY;
  if (Number.isNaN(start) || Number.isNaN(end)) throw new Error("start and end must be valid timestamps.");
  return Date.parse(metadata.range_end) >= start && Date.parse(metadata.range_start) <= end;
}

function selectedRecords(args) {
  const limit = boundedInteger(args.limit, 100, maximumRecords, "limit");
  const byteLimit = boundedInteger(args["byte-limit"], 1024 * 1024, maximumBytes, "byte-limit");
  const query = String(args.query || "").toLowerCase();
  const category = String(args.category || "").toLowerCase();
  const output = [];
  let bytes = 0;
  for (const metadata of manifest().archives.filter((entry) => dateMatches(entry, args))) {
    const { records } = verifyArchive(metadata);
    for (const record of records) {
      if (category && record.category !== category) continue;
      const content = Buffer.from(record.content_base64, "base64");
      const haystack = `${record.completed_run}\n${record.relative_path}\n${content.toString("utf8")}`.toLowerCase();
      if (query && !haystack.includes(query)) continue;
      if (output.length >= limit || bytes + content.length > byteLimit) return { records: output, bytes, truncated: true };
      output.push({ metadata, record, content });
      bytes += content.length;
    }
  }
  return { records: output, bytes, truncated: false };
}

function runStatus() {
  const runs = completedRuns();
  const activeBytes = existsSync(activeRoot) ? directoryBytes(activeRoot) : 0;
  return {
    archive_root: relative(repositoryRoot, archiveRoot),
    active_root: relative(repositoryRoot, activeRoot),
    active_bytes: activeBytes,
    threshold_bytes: thresholdBytes(),
    completed_runs: runs.map((run) => run.name),
    eligible_runs: archiveCandidates().map((run) => run.name),
    archives: manifest().archives.length
  };
}

function runRestore(args) {
  if (!args.query && !args.category && !args.start && !args.end) throw new Error("restore requires query, category, start, or end filtering.");
  const selected = selectedRecords(args);
  const candidate = `${workspaceRoot}.candidate-${process.pid}`;
  const previous = `${workspaceRoot}.previous`;
  if (existsSync(candidate) || existsSync(previous)) throw new Error("Retained restore recovery path requires inspection.");
  mkdirSync(candidate, { recursive: true });
  for (const item of selected.records) {
    const destination = resolve(candidate, item.record.completed_run, item.record.relative_path);
    if (!destination.startsWith(candidate + sep)) throw new Error("Archive record path escaped the restore workspace.");
    mkdirSync(dirname(destination), { recursive: true });
    writeFileSync(destination, item.content);
  }
  atomicWrite(join(candidate, "restore.json"), JSON.stringify({ restored_at: new Date().toISOString(), records: selected.records.length, bytes: selected.bytes, truncated: selected.truncated }, null, 2) + "\n");
  if (existsSync(workspaceRoot)) renameSync(workspaceRoot, previous);
  try {
    renameSync(candidate, workspaceRoot);
    if (existsSync(previous)) rmSync(previous, { recursive: true });
  } catch (error) {
    if (!existsSync(workspaceRoot) && existsSync(previous)) renameSync(previous, workspaceRoot);
    throw error;
  }
  return { workspace: relative(repositoryRoot, workspaceRoot), records: selected.records.length, bytes: selected.bytes, truncated: selected.truncated };
}

function rebuildIndex() {
  const entries = [];
  if (existsSync(archiveRoot)) {
    for (const path of walkFiles(archiveRoot)) {
      if (!path.endsWith(".meta.json")) continue;
      const metadata = readJson(path);
      verifyArchive(metadata);
      entries.push(metadata);
    }
  }
  entries.sort((left, right) => left.created_at.localeCompare(right.created_at));
  const index = emptyManifest();
  index.updated_at = new Date().toISOString();
  index.archives = entries;
  atomicWrite(manifestPath, JSON.stringify(index, null, 2) + "\n");
  return { archives: entries.length };
}

function prune(args) {
  if (!args.confirm || !args.id) throw new Error("prune requires --id <exact-archive-id> --confirm.");
  const index = manifest();
  const metadata = index.archives.find((entry) => entry.archive_id === args.id);
  if (!metadata) throw new Error("Exact archive ID was not found.");
  verifyArchive(metadata);
  const bundlePath = resolve(archiveRoot, metadata.relative_path);
  const metaPath = bundlePath.replace(/\.jsonl\.gz$/, ".meta.json");
  const bundlePending = `${bundlePath}.pruning-${process.pid}`;
  const metaPending = `${metaPath}.pruning-${process.pid}`;
  if (existsSync(bundlePending) || existsSync(metaPending)) throw new Error("Retained prune recovery path requires inspection.");
  renameSync(bundlePath, bundlePending);
  if (existsSync(metaPath)) renameSync(metaPath, metaPending);
  index.archives = index.archives.filter((entry) => entry.archive_id !== args.id);
  index.updated_at = new Date().toISOString();
  try {
    atomicWrite(manifestPath, JSON.stringify(index, null, 2) + "\n");
  } catch (error) {
    renameSync(bundlePending, bundlePath);
    if (existsSync(metaPending)) renameSync(metaPending, metaPath);
    throw error;
  }
  rmSync(bundlePending);
  if (existsSync(metaPending)) rmSync(metaPending);
  return { pruned: args.id };
}

const [command = "status", ...rawArguments] = process.argv.slice(2);
const args = parseArguments(rawArguments);
let result;
if (command === "status") result = runStatus();
else if (command === "list") result = manifest();
else if (command === "verify") result = { verified: manifest().archives.map((entry) => ({ id: entry.archive_id, records: verifyArchive(entry).recordCount })) };
else if (command === "rotate") result = withLock(() => runStatus().active_bytes >= thresholdBytes() ? archiveRuns(archiveCandidates()) : { archived: false, reason: "Active FORGE data is below the configured threshold." });
else if (command === "archive") result = withLock(() => args.force ? archiveRuns(archiveCandidates()) : archiveRuns(runStatus().active_bytes >= thresholdBytes() ? archiveCandidates() : []));
else if (command === "search") {
  if (!args.query) throw new Error("search requires --query.");
  const selected = selectedRecords(args);
  result = { records: selected.records.map((item) => ({ archive_id: item.metadata.archive_id, completed_run: item.record.completed_run, category: item.record.category, relative_path: item.record.relative_path, size: item.record.size, sha256: item.record.sha256, preview: item.content.toString("utf8").slice(0, 500) })), bytes: selected.bytes, truncated: selected.truncated };
} else if (command === "restore") result = withLock(() => runRestore(args));
else if (command === "rebuild-index") result = withLock(rebuildIndex);
else if (command === "prune") result = withLock(() => prune(args));
else throw new Error("Usage: aifred-archive.mjs status|rotate|archive|list|verify|search|restore|rebuild-index|prune");
console.log(JSON.stringify(result, null, 2));
