# AifredEngine

AifredEngine is AIFRED 4.0's loopback-only conversational model companion. It
listens on `127.0.0.1:8787`; the VST talks only to this engine, and the engine
routes to either Ollama or an explicitly configured OpenAI-compatible provider.

Routes:

- `GET /health`
- `POST /chat`
- `GET /v1/settings`
- `POST /v1/settings`
- `POST /v1/restart`

Settings and logs live under the current user's application-data directory.
Provider secrets are never returned by the settings endpoint and must not be
committed. Environment overrides are available as `AIFRED_PROVIDER`,
`AIFRED_PROVIDER_ENDPOINT`, `AIFRED_PROVIDER_MODEL`, and
`AIFRED_PROVIDER_API_KEY`.

The engine intentionally contains no threshold diagnosis route or canned
response selector. The user question and authoritative mode-specific context
are sent to the selected model for a natural response.

```powershell
dotnet build tools/AifredEngine/AifredEngine.csproj -c Release
```
