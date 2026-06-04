# ADK Workspace — Agent Notes

## What This Is

Google ADK agent workspace. Contains agent configs, a React frontend, deployment scripts, and inspection utilities.

## Key Paths

| Path | Purpose |
|------|---------|
| `my_config_agent/` | Agent configurations and services |
| `frontend/` | React web UI |
| `deploy.sh` | Deployment script for GCP/local |
| `inspect_adk.py` | ADK state inspector |
| `inspect_excel.py` | Excel/data flow inspector |
| `tests/` | Test suite |

## Dev Commands

```bash
# Python agents
python3 agent.py
python3 inspect_adk.py

# Frontend
cd frontend && npm install && npm run dev

# Deploy
./deploy.sh
```

## Safety Boundaries

- Do not commit real GCP service account keys.
- `analytics_service.py` uses mock data by design.
- Do not change deployment targets without verifying the destination project.

## Status

Active. Safe to iterate on configs and frontend.

## Operating Charter

> Guiding principles for any AI agent (or human) working in this repo. Derived from the Andrej Karpathy engineering philosophy. Tool-neutral: applies whether you drive this repo with Claude Code, goose, or by hand.

### The four rules
1. **Simplicity first.** Write the minimum code that solves the task. No speculative abstractions, no unrequested features, no single-use platforms. Extract a shared module only when there are >= 2 real call-sites today.
2. **Surgical changes, one concern per PR.** Touch only what the task requires. Do not opportunistically reformat, bump unrelated deps, or fix adjacent dead code. Small, reviewable, independently revertable diffs.
3. **Evals are the spec.** Define and run the repo verification (tests, build, typecheck, smoke) BEFORE and AFTER a change. Nothing merges unless it stays green. Keep the generate->verify loop tight and reversible.
4. **Delete > add; fewer dependencies.** Removing code, repos, and dependencies is the highest-leverage move. Every dependency is attack surface you own. Pin and lock what remains. Humans stay in the loop for irreversible / outward-facing / production steps (deletes, credential rotation, infra teardown, deploys).

### Safety
- Never use `git add .` or `git add -A` — stage changed files by explicit path (avoids sweeping in WIP or secrets).
- Never commit secrets; `.env*` stays gitignored (except `.env.example`).
- Treat anything outward-facing or irreversible as draft-then-confirm.
