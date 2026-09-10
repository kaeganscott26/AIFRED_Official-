import backend from "../../../../lib/backend/index.js";

export async function onRequest(context) {
  return backend.fetch(context.request, context.env, { waitUntil: (promise) => context.waitUntil(promise) });
}
