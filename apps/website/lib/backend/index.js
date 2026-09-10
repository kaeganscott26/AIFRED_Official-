import { HttpError, corsHeaders, json, withCors } from "./http.js";
import { initialTrace, routeRequest } from "./handlers.js";
import { enqueueRequestMetric, structuredLog, writeAnalytics } from "./telemetry.js";

export default {
  async fetch(request, env, ctx) {
    const started = Date.now();
    const trace = await initialTrace(request);
    let response;

    try {
      if (request.method === "OPTIONS") {
        response = new Response(null, { status: 204, headers: corsHeaders(request) });
      } else {
        response = await routeRequest(request, env, ctx, trace);
      }
    } catch (error) {
      const status = error instanceof HttpError ? error.status : 500;
      const code = error instanceof HttpError ? error.code : "internal_error";
      trace.errorCategory = code;
      if (!(error instanceof HttpError)) console.error({
        request_id: trace.requestId,
        timestamp: new Date().toISOString(),
        route: trace.route,
        error_category: code,
        error_name: error?.name || "Error",
        error_message: String(error?.message || "internal error").slice(0, 240)
      });
      response = json({
        ok: false,
        error: code,
        message: status >= 500 && !(error instanceof HttpError) ? "internal server error" : error.message,
        request_id: trace.requestId
      }, { status, headers: error instanceof HttpError ? error.headers : {} });
    }

    trace.status = response.status;
    trace.latencyMs = Date.now() - started;
    trace.cacheStatus = response.headers.get("x-aifred-cache") || "BYPASS";
    structuredLog(trace);
    writeAnalytics(env, trace);
    ctx.waitUntil(enqueueRequestMetric(env, trace).catch((error) => console.error({
      request_id: trace.requestId,
      timestamp: new Date().toISOString(),
      route: trace.route,
      error_category: "request_metric_enqueue_failed",
      error_name: error?.name || "Error"
    })));
    return withCors(response, request, trace.requestId);
  }
};
