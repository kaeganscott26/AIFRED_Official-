# AI Engine Config

## Purpose

This folder is reserved for future AI adapter configuration documentation and safe config examples.

No runtime config implementation exists yet.

## Future Config Topics

- adapter selection
- provider availability status
- timeouts
- model names
- endpoint URLs
- API key references through environment variables or approved config references only
- local model availability flags
- no-AI fallback selection

## Rules

- No real secrets.
- No API keys.
- No committed `.env` files.
- No hardcoded personal paths.
- No hardcoded local model paths.
- No private endpoints.
- No backend routing behavior.

Future config must reference secrets indirectly through environment/config mechanisms approved by the backend/security contracts.
