const APEX_ORIGIN = "https://north3rnlight3r.com";

function apiNotFound() {
  return Response.json(
    {
      error: {
        code: "api_route_not_served_by_pages",
        message: "The AIFRED API is served by the dedicated /api Worker route."
      }
    },
    {
      status: 404,
      headers: {
        "cache-control": "no-store",
        "x-content-type-options": "nosniff"
      }
    }
  );
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.hostname.toLowerCase() === "www.north3rnlight3r.com") {
      return Response.redirect(`${APEX_ORIGIN}${url.pathname}${url.search}`, 308);
    }

    if (
      url.pathname === "/api" ||
      url.pathname.startsWith("/api/") ||
      url.pathname === "/v1" ||
      url.pathname.startsWith("/v1/") ||
      url.pathname === "/ws" ||
      url.pathname.startsWith("/ws/")
    ) {
      return apiNotFound();
    }

    return env.ASSETS.fetch(request);
  }
};
