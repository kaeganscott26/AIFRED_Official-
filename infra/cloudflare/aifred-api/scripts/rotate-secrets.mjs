import { createHash, randomBytes } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const workerRoot = resolve(here, "..");
const repositoryRoot = resolve(workerRoot, "..", "..", "..");
const envPath = resolve(repositoryRoot, ".env");
const secretsPath = resolve(workerRoot, ".secrets.local.json");

const token = (bytes = 32) => randomBytes(bytes).toString("base64url");
const values = {
  AIFRED_API_TOKEN: token(),
  AIFRED_ANALYTICS_API_TOKEN: token(),
  OLLAMA_API_TOKEN: token(),
  AIFRED_ADMIN_SESSION_SECRET: token(48),
  AIFRED_ADMIN_PASSWORD: token(24)
};
values.AIFRED_ADMIN_PASSWORD_SHA256 = createHash("sha256").update(values.AIFRED_ADMIN_PASSWORD).digest("hex");
values.AIFRED_PROVIDER_API_KEY = values.AIFRED_API_TOKEN;

let existing = "";
try { existing = await readFile(envPath, "utf8"); } catch {}
const lines = existing ? existing.replace(/\r\n/g, "\n").split("\n") : [];
const replacements = new Map(Object.entries(values));
const seen = new Set();
const updated = lines.map((line) => {
  const match = /^([A-Z][A-Z0-9_]*)=/.exec(line);
  if (!match || !replacements.has(match[1])) return line;
  seen.add(match[1]);
  return `${match[1]}=${replacements.get(match[1])}`;
});
for (const [name, value] of replacements) if (!seen.has(name)) updated.push(`${name}=${value}`);
await writeFile(envPath, updated.join("\n").replace(/\n*$/, "\n"), { encoding: "utf8", mode: 0o600 });

const productionSecrets = {
  AIFRED_API_TOKEN: values.AIFRED_API_TOKEN,
  AIFRED_ANALYTICS_API_TOKEN: values.AIFRED_ANALYTICS_API_TOKEN,
  OLLAMA_API_TOKEN: values.OLLAMA_API_TOKEN,
  AIFRED_ADMIN_SESSION_SECRET: values.AIFRED_ADMIN_SESSION_SECRET,
  AIFRED_ADMIN_PASSWORD_SHA256: values.AIFRED_ADMIN_PASSWORD_SHA256
};
await writeFile(secretsPath, `${JSON.stringify(productionSecrets, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });

console.log("Rotated locally (values intentionally omitted):");
for (const name of Object.keys(values)) console.log(`- ${name}`);
console.log("Production secret bundle written with values omitted from console output.");
