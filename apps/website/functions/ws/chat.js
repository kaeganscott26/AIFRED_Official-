import backend from "../../lib/backend/index.js";

function textFromCompletion(payload) {
  return String(payload?.choices?.[0]?.message?.content || payload?.message?.content || payload?.response || "").trim();
}

export async function onRequest({ request, env, ctx }) {
  if ((request.headers.get("upgrade") || "").toLowerCase() !== "websocket") {
    return Response.json({ ok: false, error: "websocket_upgrade_required" }, {
      status: 426,
      headers: { "cache-control": "no-store" }
    });
  }

  const authorization = request.headers.get("authorization") || "";
  if (!authorization.toLowerCase().startsWith("bearer ")) {
    return Response.json({ ok: false, error: "authentication_required" }, {
      status: 401,
      headers: { "cache-control": "no-store" }
    });
  }

  const pair = new WebSocketPair();
  const [client, server] = Object.values(pair);
  server.accept();
  server.send(JSON.stringify({ type: "chat.ready", transport: "websocket-compatibility", canonical: "/v1/chat/completions" }));

  server.addEventListener("message", (event) => {
    ctx.waitUntil((async () => {
      let payload;
      try {
        payload = JSON.parse(String(event.data || ""));
      } catch {
        server.send(JSON.stringify({ type: "chat.error", message: "invalid websocket payload" }));
        return;
      }
      if (payload.type === "chat.clear") {
        server.send(JSON.stringify({ type: "chat.ready", transport: "websocket-compatibility" }));
        return;
      }
      if (payload.type !== "chat.send" || !String(payload.text || "").trim()) {
        server.send(JSON.stringify({ type: "chat.error", message: "chat.send requires text" }));
        return;
      }
      const context = payload.context && typeof payload.context === "object" ? payload.context : undefined;
      const userContent = context ? JSON.stringify({ message: String(payload.text).trim(), context }) : String(payload.text).trim();
      const chatRequest = new Request(new URL("/v1/chat/completions", request.url), {
        method: "POST",
        headers: {
          authorization,
          "content-type": "application/json",
          "idempotency-key": crypto.randomUUID(),
          "x-aifred-client": request.headers.get("x-aifred-client") || "websocket-compatibility",
          "x-aifred-purpose": "user-chat"
        },
        body: JSON.stringify({
          model: payload.model || "",
          stream: false,
          messages: [
            { role: "system", content: "Use only the measured context provided with the user's request. Do not claim to have heard audio or invent measurements." },
            { role: "user", content: userContent }
          ]
        })
      });
      const response = await backend.fetch(chatRequest, env, ctx);
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        server.send(JSON.stringify({ type: "chat.error", message: body.message || body.error || `request failed (${response.status})` }));
        return;
      }
      const answer = textFromCompletion(body);
      server.send(JSON.stringify({ type: "chat.token", text: answer || "Provider returned no text." }));
    })().catch(() => server.send(JSON.stringify({ type: "chat.error", message: "chat request failed" }))));
  });

  return new Response(null, { status: 101, webSocket: client });
}
