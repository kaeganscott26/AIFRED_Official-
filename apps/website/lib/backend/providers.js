import { HttpError, bounded } from "./http.js";

const PROVIDER_TIMEOUT_MS = 45_000;
const PROVIDER_TEST_TIMEOUT_MS = 5_000;

function ollamaHeaders(env, jsonBody = false) {
  const headers = new Headers({ authorization: `Bearer ${env.OLLAMA_API_TOKEN}` });
  if (jsonBody) headers.set("content-type", "application/json");
  if (env.OLLAMA_ACCESS_CLIENT_ID && env.OLLAMA_ACCESS_CLIENT_SECRET) {
    headers.set("CF-Access-Client-Id", env.OLLAMA_ACCESS_CLIENT_ID);
    headers.set("CF-Access-Client-Secret", env.OLLAMA_ACCESS_CLIENT_SECRET);
  }
  return headers;
}

function selectedProvider(env) {
  return bounded(env.AIFRED_CHAT_PROVIDER || "ollama", 32).toLowerCase();
}

function ollamaModel(env) {
  return bounded(env.OLLAMA_MODEL || env.OLLMA_MODEL, 120);
}

export function providerConfiguration(env) {
  const active = selectedProvider(env);
  return {
    active,
    providers: [
      {
        id: "ollama",
        configured: Boolean(env.OLLAMA_BASE_URL && ollamaModel(env) && env.OLLAMA_API_TOKEN),
        model: ollamaModel(env),
        access_service_token_configured: Boolean(env.OLLAMA_ACCESS_CLIENT_ID && env.OLLAMA_ACCESS_CLIENT_SECRET)
      },
      {
        id: "openai",
        configured: Boolean(env.OPENAI_API_KEY && env.OPENAI_MODEL),
        model: bounded(env.OPENAI_MODEL, 120)
      }
    ]
  };
}

export async function invokeChatProvider(env, body) {
  const provider = selectedProvider(env);
  const requestedModel = bounded(body.model, 120);
  let url;
  let headers;
  let model;

  if (provider === "openai") {
    if (!env.OPENAI_API_KEY || !env.OPENAI_MODEL) {
      throw new HttpError(503, "provider_unconfigured", "OpenAI provider is not configured");
    }
    url = "https://api.openai.com/v1/chat/completions";
    headers = new Headers({ authorization: `Bearer ${env.OPENAI_API_KEY}`, "content-type": "application/json" });
    model = requestedModel || bounded(env.OPENAI_MODEL, 120);
  } else if (provider === "ollama") {
    if (!env.OLLAMA_BASE_URL || !ollamaModel(env) || !env.OLLAMA_API_TOKEN) {
      throw new HttpError(503, "provider_unconfigured", "Ollama provider is not configured");
    }
    url = `${String(env.OLLAMA_BASE_URL).replace(/\/+$/, "")}/v1/chat/completions`;
    headers = ollamaHeaders(env, true);
    model = requestedModel || ollamaModel(env);
  } else {
    throw new HttpError(503, "provider_unconfigured", "configured chat provider is unsupported");
  }

  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model,
        messages: body.messages,
        stream: body.stream === true,
        ...(Number.isFinite(body.temperature) ? { temperature: body.temperature } : {}),
        ...(Number.isSafeInteger(body.max_tokens) && body.max_tokens > 0 ? { max_tokens: body.max_tokens } : {})
      }),
      signal: AbortSignal.timeout(PROVIDER_TIMEOUT_MS)
    });
  } catch (error) {
    if (error?.name === "TimeoutError") throw new HttpError(504, "provider_timeout", "chat provider timed out");
    throw new HttpError(502, "provider_unavailable", "chat provider is unavailable");
  }

  if (!response.ok) {
    response.body?.cancel().catch(() => {});
    const category = response.status === 401 || response.status === 403 ? "provider_authentication_failed" : "provider_error";
    throw new HttpError(502, category, "chat provider request failed");
  }
  return { provider, response };
}

export async function testOllamaProvider(env) {
  if (!env.OLLAMA_BASE_URL || !ollamaModel(env) || !env.OLLAMA_API_TOKEN) {
    throw new HttpError(503, "provider_unconfigured", "Ollama provider is not configured");
  }
  const started = Date.now();
  let response;
  try {
    response = await fetch(`${String(env.OLLAMA_BASE_URL).replace(/\/+$/, "")}/api/tags`, {
      headers: ollamaHeaders(env),
      signal: AbortSignal.timeout(PROVIDER_TEST_TIMEOUT_MS)
    });
  } catch (error) {
    if (error?.name === "TimeoutError") throw new HttpError(504, "provider_timeout", "Ollama provider test timed out");
    throw new HttpError(502, "provider_unavailable", "Ollama provider is unavailable");
  }
  const result = {
    ok: response.ok,
    provider: "ollama",
    model: ollamaModel(env),
    status: response.status,
    latency_ms: Date.now() - started
  };
  response.body?.cancel().catch(() => {});
  return result;
}
