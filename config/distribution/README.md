# AIFRED User Configuration

This directory contains **blank distribution-safe configuration templates**. It must never contain an operator credential, North3rnLight3r infrastructure secret, or a user's populated provider key.

## LLM provider setup

AIFRED's DSP, observation pipeline and deterministic context do not require an LLM provider. Conversational interpretation does.

Choose one supported provider:

### Ollama

Default template:

```json
{
  "provider": "ollama",
  "endpoint": "http://127.0.0.1:11434",
  "model": "aifred:latest",
  "api_key": "",
  "timeout_ms": 180000
}
```

The model must already be installed and available through the configured Ollama endpoint.

### OpenAI

Use an OpenAI API endpoint/model and supply your own API key locally:

```json
{
  "provider": "openai",
  "endpoint": "https://api.openai.com/v1",
  "model": "YOUR_SUPPORTED_MODEL",
  "api_key": "YOUR_KEY_HERE",
  "timeout_ms": 180000
}
```

### OpenAI-compatible provider

Use `openai-compatible` with the provider's HTTPS endpoint, supported model name and any required API key.

## Where settings live

Do not edit files inside the installed VST3 bundle. AifredIntelligenceHost owns provider settings in the user's local application-data directory for the installed channel.

- Beta: `%APPDATA%/Aifred/beta/IntelligenceHost/settings.json`
- AIFRED 4 / Official: `%APPDATA%/Aifred/official/IntelligenceHost/settings.json`

The host also accepts the local environment overrides `AIFRED_PROVIDER`, `AIFRED_PROVIDER_ENDPOINT`, `AIFRED_PROVIDER_MODEL`, and `AIFRED_PROVIDER_API_KEY`.

## Context is not the model

AIFRED's measurement data, deterministic mix context, current-session state and bounded session history belong to AIFRED. The model provider only interprets the context it is given.

The intelligence architecture's active-memory contract is the **current session plus the previous nine retained sessions**. Provider failure or a provider change must not redefine measurement truth or erase AIFRED-owned context.

Context/history exports are portable user-owned data. A user may choose to provide an export to another capable application such as ChatGPT or Gemini for interpretation. Those applications are external to AIFRED and operate under their own terms and privacy policies.

## Security

- Never publish a populated `api_key`.
- Never copy North3rnLight3r operator `.env` values into this template.
- AIFRED does not need Cloudflare, GitHub or R2 credentials to run its local DSP/intelligence host.
- Distribution packages contain the blank example only.
