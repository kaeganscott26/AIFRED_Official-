import backend from "./lib/backend/index.js";
import { onRequest as wsChat } from "./functions/ws/chat.js";

const APEX_ORIGIN = "https://north3rnlight3r.com";

function isBackendPath(pathname) {
  return pathname === "/health" ||
    pathname === "/api" ||
    pathname.startsWith("/api/") ||
    pathname === "/v1" ||
    pathname.startsWith("/v1/");
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.hostname.toLowerCase() === "www.north3rnlight3r.com") {
      return Response.redirect(`${APEX_ORIGIN}${url.pathname}${url.search}`, 308);
    }

    if (url.pathname === "/ws/chat") {
      return wsChat({ request, env, ctx });
    }

    if (isBackendPath(url.pathname)) {
      return backend.fetch(request, env, ctx);
    }

    return env.ASSETS.fetch(request);
  }
};
