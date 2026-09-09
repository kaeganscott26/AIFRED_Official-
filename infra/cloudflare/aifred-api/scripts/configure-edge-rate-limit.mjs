const accountId = process.env.CLOUDFLARE_ACCOUNT_ID;
const zoneId = process.env.CLOUDFLARE_ZONE_ID;
const token = process.env.CLOUDFLARE_API_TOKEN;
if (!accountId || !zoneId || !token) {
  throw new Error("CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_ZONE_ID, and CLOUDFLARE_API_TOKEN are required");
}

const api = async (path, init = {}) => {
  const response = await fetch(`https://api.cloudflare.com/client/v4${path}`, {
    ...init,
    headers: { authorization: `Bearer ${token}`, "content-type": "application/json", ...(init.headers || {}) }
  });
  const payload = await response.json();
  if (!response.ok || !payload.success) throw new Error(payload.errors?.map((item) => item.message).join("; ") || `Cloudflare API ${response.status}`);
  return payload.result;
};

const protectedPaths = [
  "/api/v1/chat/completions",
  "/api/v1/analysis",
  "/api/v1/analytics/events",
  "/api/v1/inquiries",
  "/api/v1/admin/login"
];
const expression = `http.request.method eq \"POST\" and http.request.uri.path in {${protectedPaths.map((path) => `\"${path}\"`).join(" ")}}`;
const rule = {
  ref: "aifred_api_burst_defense",
  action: "block",
  expression,
  description: "AIFRED expensive API burst protection (Free-plan consolidated rule)",
  enabled: true,
  ratelimit: {
    characteristics: ["cf.colo.id", "ip.src"],
    period: 60,
    requests_per_period: 20,
    mitigation_timeout: 60,
    requests_to_origin: false
  }
};

let entrypoint = null;
try {
  entrypoint = await api(`/zones/${zoneId}/rulesets/phases/http_ratelimit/entrypoint`);
} catch (error) {
  if (!/could not find entrypoint/i.test(error.message)) throw error;
}

if (!entrypoint) {
  const created = await api(`/zones/${zoneId}/rulesets`, {
    method: "POST",
    body: JSON.stringify({
      name: "AIFRED production API rate limiting",
      description: "Edge burst protection; authenticated route-specific limits remain in the Worker.",
      kind: "zone",
      phase: "http_ratelimit",
      rules: [rule]
    })
  });
  console.log(`Created ruleset ${created.id} with rule ${created.rules?.[0]?.id || "created"}.`);
} else {
  const existing = entrypoint.rules?.find((item) => item.ref === rule.ref);
  const path = existing
    ? `/zones/${zoneId}/rulesets/${entrypoint.id}/rules/${existing.id}`
    : `/zones/${zoneId}/rulesets/${entrypoint.id}/rules`;
  const updated = await api(path, { method: existing ? "PATCH" : "POST", body: JSON.stringify(rule) });
  console.log(`${existing ? "Updated" : "Created"} rule ${updated.id}.`);
}
