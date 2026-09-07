# Private control-plane source snapshot

The private admin/control-plane tree was imported from public Beta commit
`e032e9831e8a49b187ed52d7232233d974929d90` on 2026-09-07.

Imported areas:
- `apps/admin-android/`
- `apps/admin-desktop/`
- private `/ops` website assets and their shared backend helpers
- Cloudflare operational infrastructure/configuration
- admin registry/support records and operational documentation

This snapshot contains no secret values. Deployment/provider credentials remain external
secrets/runtime configuration. The Official plugin local intelligence host is channel
`official` on port `8788`; website/admin endpoints remain the production custom domain.

Do not copy future private control-plane changes back into the public Beta repository.
