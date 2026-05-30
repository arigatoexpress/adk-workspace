# ADK Workspace

Google ADK (Agent Development Kit) workspace and configuration agents for building, testing, and deploying agent-driven workflows.

## What This Does

This repo contains agent configurations, deployment scripts, and frontend integrations for Google's ADK. It includes:

- **Config agents** (`my_config_agent/`) — Reusable agent configurations for analytics, reporting, and automation
- **Frontend** (`frontend/`) — Web UI for interacting with ADK agents
- **Deployment scripts** (`deploy.sh`) — One-command deploy to GCP or local environments
- **Inspection tools** (`inspect_adk.py`, `inspect_excel.py`) — Utilities for debugging agent state and data flows

## Quick Start

```bash
# Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # if available

# Inspect an ADK agent
python3 inspect_adk.py

# Deploy to GCP
./deploy.sh
```

## Project Structure

```
my_config_agent/        # Analytics and reporting agent configs
  analytics_service.py  # Mock → production analytics pipeline
  ...
frontend/               # Web UI for agent interaction
  src/
  public/
  package.json
tests/                  # Test suite
agent.py                # Main agent entry point
deploy.sh               # Deployment script
inspect_*.py            # Debugging utilities
```

## Tech Stack

- Python 3.11+
- Google ADK
- React (frontend)
- GCP (deployment target)

## Status

Active development. Config agents use mock data for demos; production paths are documented but not wired.

---

*See [AGENTS.md](AGENTS.md) for agent collaboration notes.*
