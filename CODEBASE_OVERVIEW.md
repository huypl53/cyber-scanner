# AI Network Security Threat Detection System - Codebase Overview

## Project Overview

This is an **AI-powered Network Security Threat Detection System** - a full-stack application for detecting and classifying network security threats using machine learning models.

### Technology Stack

- **Backend**: FastAPI 0.109.0, Python 3.12+, UV workspace
- **Frontend**: Next.js 14.2.0 (App Router), React 18, TypeScript
- **ML/AI**: TensorFlow CPU, Keras, scikit-learn
- **Streaming**: Apache Kafka (confluent-kafka, aiokafka)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Testing**: pytest, Jest, Playwright

---

## Monorepo Structure

```
/mnt/Code/code/freelance/2511-AI-heal-network-sec/ui/
├── backend/                 # FastAPI backend application
│   ├── app/                # Main application package
│   │   ├── api/routes/    # API endpoints
│   │   ├── core/          # Configuration
│   │   ├── kafka/         # Kafka consumer/producer
│   │   ├── models/        # Database & ML models
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI entry point
│   ├── packages/ml-models/ # UV workspace ML package
│   │   └── src/ml_models/
│   │       ├── threat_classification.py
│   │       └── attack_classification.py
│   └── main.py            # Standalone entry point
└── frontend/              # Next.js frontend application
    ├── app/              # App Router pages
    ├── components/       # React components
    └── messages/         # i18n translations (en, vi)
```

---

## ML Models Architecture

### Workspace Package: `ml-models`

The backend uses a **UV workspace** configuration with a local ML models package:

**Location**: `backend/packages/ml-models/`

**Exposed Classes**:
- `ThreatDetectionPipeline` - ANN + LSTM ensemble for binary threat detection
- `AttackClassificationPipeline` - Decision tree for multi-class attack classification

**Import Pattern** (in workspace package):
```python
from ml_models import ThreatDetectionPipeline, AttackClassificationPipeline
```

### Backend Abstraction Layer

**File**: `backend/app/models/ml_models.py`

This module provides a clean abstraction over the workspace package:

```python
# Correct import pattern for backend code:
from app.models.ml_models import (
    get_ensemble_model,        # Factory for threat detection
    get_decision_tree_model,   # Factory for attack classification
    RealEnsembleModel,         # Direct class access
    RealDecisionTreeModel,
    THREAT_DETECTION_FEATURES,
    ATTACK_CLASSIFICATION_FEATURES,
    ATTACK_TYPES
)
```

### Model Types

| Model Type | Features | Classes | File |
|------------|----------|---------|------|
| Threat Detection | 10 features | Binary (Normal/Attack) | `threat_detector_ensemble.joblib` |
| Attack Classification | 42 features | 14 attack types | `attack_classifier.joblib` |

---

## Import Pattern Guide

### ✅ CORRECT Pattern (in backend)

```python
# In backend app code (app/**/*.py):
from app.models.ml_models import get_ensemble_model, get_decision_tree_model
```

### ❌ INCORRECT Pattern (in backend)

```python
# Don't import workspace package directly in backend code:
from ml_models import AttackClassificationPipeline  # WRONG!
```

### ✅ CORRECT Pattern (in workspace package)

```python
# In ml-models workspace package code:
from ml_models import ThreatDetectionPipeline, AttackClassificationPipeline
```

---

## Kafka Configuration

### Topics

| Topic | Purpose |
|-------|---------|
| `network-traffic` | Real-time network traffic data |
| `external-traffic` | External data sources |
| `predictions` | ML prediction results |

### Environment Variables

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_REALTIME_DATA=network-traffic
KAFKA_TOPIC_EXTERNAL_DATA=external-traffic
KAFKA_TOPIC_PREDICTIONS=predictions
```

### Docker Compose

```bash
# Start infrastructure only (PostgreSQL, Zookeeper, Kafka):
docker-compose -f docker-compose.dev.yml up -d

# Start full stack:
docker-compose -f docker-compose.full.yml up -d
```

---

## Backend API Endpoints

### Base Configuration
- **URL**: `http://localhost:8000`
- **API Prefix**: `/api/v1`
- **Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Basic health check |
| GET | `/api/v1/health/detailed` | Comprehensive health check |
| POST | `/api/v1/test/start-stream` | Start test data stream |
| GET | `/api/v1/predictions/recent` | Get recent predictions |
| POST | `/api/v1/upload/csv` | Upload CSV for batch predictions |
| POST | `/api/v1/models/upload` | Upload ML model |
| WS | `/ws/realtime` | Real-time prediction updates |

---

## Running the System

### 1. Start Infrastructure

```bash
cd /mnt/Code/code/freelance/2511-AI-heal-network-sec/ui
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Start Backend

```bash
cd backend
uv sync
uv run python -m app.main
# OR:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start Frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

### 4. Test the System

```bash
# Health check
curl http://localhost:8000/health

# Start test data stream
curl -X POST http://localhost:8000/api/v1/test/start-stream

# Get recent predictions
curl http://localhost:8000/api/v1/predictions/recent
```

---

## Database Schema

### Tables

1. **traffic_data** - Raw network traffic data
2. **threat_predictions** - Binary threat detection results
3. **attack_predictions** - Multi-class attack classifications
4. **self_healing_actions** - Actions for detected threats
5. **ip_whitelist** - IP access control
6. **data_source_config** - Data source configurations
7. **ml_models** - Model versioning and metadata

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
│                   http://localhost:3000                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ (HTTP/WebSocket)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                          │
│                   http://localhost:8000                     │
└───┬───────────────┬───────────────┬────────────────────────┘
    │               │               │
    ▼               ▼               ▼
┌─────────┐   ┌──────────┐   ┌──────────┐
│  ML     │   │  Kafka   │   │ Database │
│ Models  │   │ Streams  │   │(PostgreSQL)
└─────────┘   └──────────┘   └──────────┘
```

---

## Current Status

**Branch**: `feat/research/model-training`

**Recent Changes**:
- Updated backend ML models
- Cleaned up research files
- Fixed import patterns

**Known Issues**:
- `backend/main.py` uses incorrect import pattern (to be fixed)

---

## References

- **Backend README**: `backend/README.md`
- **ML Integration Guide**: `backend/packages/ml-models/BACKEND_MODEL_USAGE.md`
- **UV Workspace**: https://docs.astral.sh/uv/guides/workspaces/
