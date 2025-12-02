# Agents Routing Guide

Use these prompts to select the right specialist for the AI Threat Detection & Self-Healing system.

## When to use each agent

- `devops-deployment-specialist`: Deploy or operate the stack (FastAPI backend, Next.js frontend, Kafka/Zookeeper, Postgres). Spin up local dev via `docker-compose.dev.yml`, run full stack via `docker-compose.full.yml`, debug CI/CD, ports, or health of API/WS/Kafka/DB.
- `ml-model-deployer`: Move models from `backend/research` into production (`backend/app/services`). Package the 10-feature binary detector and 42-feature attack classifier, define Kafka payload/output contracts, optimize inference for streaming/WebSocket, and provide handoff docs/tests.
- `threat-analysis-frontend-dev`: Build or fix the Next.js frontend. Integrate `/api/v1/*` and `/ws/realtime`, maintain CSV upload for both schemas, render threat/attack stats and self-healing logs, ensure responsive and accessible UI with Tailwind/Recharts.
- `threat-analyzer`: Perform threat analysis using system schemas. Consume Kafka `network-traffic` data or user samples (10-feature or 42-feature), classify threats/attacks, summarize findings, and demonstrate detection behavior.

## Quick decision rules
- Infra/compose/CI or deployment? → `devops-deployment-specialist`
- Model packaging, schema definitions, latency/drift, or backend model handoff? → `ml-model-deployer`
- Frontend UI/UX, WebSocket dashboard, CSV upload, charts/tables? → `threat-analysis-frontend-dev`
- Need actual threat analysis/demos on traffic data? → `threat-analyzer`
