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
