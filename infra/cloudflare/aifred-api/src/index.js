export default {
  async fetch(request) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return Response.json({
        ok: true,
        service: "aifred-api",
        api_version: "v1",
        status: "healthy",
        timestamp: new Date().toISOString()
      });
    }

    return Response.json(
      {
        ok: false,
        error: "route_not_found",
        method: request.method,
        path: url.pathname
      },
      { status: 404 }
    );
  }
};
