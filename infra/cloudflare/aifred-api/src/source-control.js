import { HttpError, bounded } from "./http.js";

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const GITHUB_API_VERSION = "2026-03-10";

export const EDITABLE_WEBSITE_FILES = Object.freeze([
  { label: "Home HTML", path: "apps/website/index.html", kind: "html", max_bytes: 262144 },
  { label: "Styles", path: "apps/website/styles.css", kind: "css", max_bytes: 262144 },
  { label: "App JavaScript", path: "apps/website/app.js", kind: "javascript", max_bytes: 262144 },
  { label: "Public config", path: "apps/website/config.js", kind: "javascript", max_bytes: 65536 },
  { label: "Catalog", path: "apps/website/assets/data/beat_catalog.json", kind: "json", max_bytes: 262144 },
  { label: "Release notes", path: "apps/website/assets/docs/aifred-release-notes.txt", kind: "text", max_bytes: 131072 },
  { label: "Install notes", path: "apps/website/assets/docs/aifred-installation.txt", kind: "text", max_bytes: 131072 },
  { label: "System requirements", path: "apps/website/assets/docs/aifred-system-requirements.md", kind: "markdown", max_bytes: 131072 }
]);

const editableByPath = new Map(EDITABLE_WEBSITE_FILES.map((item) => [item.path, item]));

function configuredRepository(env) {
  const repository = bounded(env.AIFRED_GITHUB_REPO || "kaeganscott26/AIFRED_Official-", 160);
  const branch = bounded(env.AIFRED_GITHUB_BRANCH || "main", 120);
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository) || !/^[A-Za-z0-9._/-]+$/.test(branch) || branch.includes("..")) {
    throw new HttpError(503, "source_control_misconfigured", "source-control repository configuration is invalid");
  }
  return { repository, branch };
}

function approvedFile(path) {
  const normalized = String(path || "").trim().replace(/\\/g, "/");
  const file = editableByPath.get(normalized);
  if (!file) throw new HttpError(403, "source_path_not_approved", "website source path is not approved for mobile editing");
  return file;
}

function encodedPath(path) {
  return path.split("/").map(encodeURIComponent).join("/");
}

function utf8ToBase64(value) {
  const bytes = encoder.encode(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

function base64ToUtf8(value) {
  const binary = atob(String(value || "").replace(/\s/g, ""));
  return decoder.decode(Uint8Array.from(binary, (character) => character.charCodeAt(0)));
}

async function githubRequest(env, apiPath, init = {}, fetchImpl = fetch) {
  if (!env.GITHUB_TOKEN) {
    throw new HttpError(503, "source_control_unconfigured", "GITHUB_TOKEN is not configured for source-control operations");
  }
  const response = await fetchImpl(`https://api.github.com${apiPath}`, {
    ...init,
    headers: {
      accept: "application/vnd.github+json",
      authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "user-agent": "aifred-api",
      "x-github-api-version": GITHUB_API_VERSION,
      ...(init.headers || {})
    }
  });
  const raw = await response.text();
  let payload = {};
  try { payload = raw ? JSON.parse(raw) : {}; } catch {}
  if (!response.ok) {
    if (response.status === 404) throw new HttpError(404, "source_file_not_found", "approved website source file was not found");
    if (response.status === 409 || response.status === 422) throw new HttpError(409, "source_conflict", "website source changed; reload the file before saving");
    throw new HttpError(502, "source_control_unavailable", `GitHub source-control request failed (${response.status})`);
  }
  return payload;
}

export function sourceControlStatus(env) {
  const { repository, branch } = configuredRepository(env);
  return {
    configured: Boolean(env.GITHUB_TOKEN),
    repository,
    branch,
    editable_files: EDITABLE_WEBSITE_FILES.length,
    write_mode: "approved-existing-files-only",
    publish_mode: "source-commit",
    pages_project: bounded(env.AIFRED_PAGES_PROJECT || "aifred-site", 120),
    deployment_verified: false
  };
}

export function validateSourceDraft(path, content) {
  const file = approvedFile(path);
  if (typeof content !== "string") throw new HttpError(400, "invalid_source_content", "source content must be text");
  const bytes = encoder.encode(content).byteLength;
  if (bytes < 1) throw new HttpError(400, "invalid_source_content", "source content must not be empty");
  if (bytes > file.max_bytes) throw new HttpError(413, "source_content_too_large", `source content exceeds ${file.max_bytes} bytes`);
  if (content.includes("\0")) throw new HttpError(400, "invalid_source_content", "source content contains a null byte");
  if (file.kind === "json") {
    try { JSON.parse(content); } catch { throw new HttpError(400, "invalid_source_json", "JSON source content is invalid"); }
  }
  if (file.kind === "html" && (!/<html[\s>]/i.test(content) || !/<\/html>/i.test(content))) {
    throw new HttpError(400, "invalid_source_html", "HTML source must contain an html document element");
  }
  return { ok: true, path: file.path, label: file.label, kind: file.kind, bytes };
}

export async function readApprovedSourceFile(env, path, fetchImpl = fetch) {
  const file = approvedFile(path);
  const { repository, branch } = configuredRepository(env);
  const payload = await githubRequest(
    env,
    `/repos/${repository}/contents/${encodedPath(file.path)}?ref=${encodeURIComponent(branch)}`,
    {},
    fetchImpl
  );
  if (payload.type !== "file" || !/^[a-f0-9]{40}$/i.test(String(payload.sha || ""))) {
    throw new HttpError(502, "invalid_source_response", "source-control response did not contain an editable file");
  }
  const content = base64ToUtf8(payload.content);
  validateSourceDraft(file.path, content);
  return {
    ok: true,
    path: file.path,
    label: file.label,
    content,
    sha: payload.sha,
    repository,
    branch,
    source: "github"
  };
}

export async function saveApprovedSourceFile(env, input, fetchImpl = fetch) {
  const validation = validateSourceDraft(input?.path, input?.content);
  const expectedSha = bounded(input?.expected_sha, 40).toLowerCase();
  if (!/^[a-f0-9]{40}$/.test(expectedSha)) {
    throw new HttpError(409, "source_reload_required", "load the current website source before saving");
  }
  const { repository, branch } = configuredRepository(env);
  const payload = await githubRequest(env, `/repos/${repository}/contents/${encodedPath(validation.path)}`, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      message: `admin: update ${validation.path}`,
      content: utf8ToBase64(input.content),
      sha: expectedSha,
      branch
    })
  }, fetchImpl);
  const commitSha = bounded(payload.commit?.sha, 64);
  if (!commitSha) throw new HttpError(502, "invalid_source_response", "source-control response did not contain a commit");
  return {
    ok: true,
    path: validation.path,
    bytes: validation.bytes,
    previous_sha: expectedSha,
    source_sha: bounded(payload.content?.sha, 40),
    commit_sha: commitSha,
    repository,
    branch,
    deployment: {
      requested_by: "source_commit",
      pages_project: bounded(env.AIFRED_PAGES_PROJECT || "aifred-site", 120),
      verified: false,
      message: "Source commit created. Confirm the Pages deployment before treating the website as published."
    }
  };
}
