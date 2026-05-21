# Pre-Code Paste Order

Paste these files into `AIFRED_Official-` before touching implementation code.

## Step 1 — Root files

1. `.gitignore`
2. `AGENTS.md`

## Step 2 — Docs folder

Create `docs/`, then add:

1. `docs/README.md`
2. `docs/PROJECTS_INDEX.md`
3. `docs/NO_DRIFT_CONTRACT.md`
4. `docs/MASTER_IMPLEMENTATION_CHECKLIST.md`
5. `docs/MODE_CONTRACT.md`
6. `docs/SOURCE_OF_TRUTH_CONTRACT.md`
7. `docs/METRIC_RELEVANCE_CONTRACT.md`
8. `docs/REPORT_CONTRACT.md`
9. `docs/LOCAL_ONLINE_PARITY_CONTRACT.md`
10. `docs/BACKEND_SECURITY_CONTRACT.md`
11. `docs/CODEX_HANDOFF.md`
12. `docs/RELEASE_ACCEPTANCE_GATES.md`

## Step 3 — Commit

Run:

```powershell
git add .
git commit -m "Add flagship pre-code contracts"
git push
```

## Step 4 — Do not code yet

After commit, the next approved task is repo skeleton only:

- `python_brain/README.md`
- `ai_engine/README.md`
- `backend/README.md`
- `plugin/README.md`
- `admin_app/README.md`
- `website/README.md`
- `tools/README.md`
- `tests/README.md`

No implementation files until the skeleton is committed.
