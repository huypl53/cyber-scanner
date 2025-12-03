# AI Threat Detection System - Quick Start Guide

## Local Development Setup

### Start Infrastructure & Backend (5 minutes)

```bash
# 1. Navigate to project root
cd /mnt/Code/code/freelance/2511-AI-heal-network-sec/ui

# 2. Start Docker infrastructure (Postgres, Kafka, Zookeeper)
docker-compose -f docker-compose.dev.yml up -d

# 3. Wait for services to be healthy (~15 seconds)
docker ps --filter "name=threat-detection"
# All should show "(healthy)" status

# 4. Start backend with hot reload
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Verify backend is running (in another terminal)
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# 6. Check detailed health
curl http://localhost:8000/api/v1/health/detailed | jq
```

### Start Frontend (Optional)

```bash
cd /mnt/Code/code/freelance/2511-AI-heal-network-sec/ui/frontend
npm install  # First time only
npm run dev

# Access at: http://localhost:3000
```

---

## Service URLs

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Detailed Health**: http://localhost:8000/api/v1/health/detailed
- **Frontend**: http://localhost:3000 (if running)

---

## Docker Services

### View Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker logs threat-detection-kafka -f
docker logs threat-detection-db -f
```

### Access Containers
```bash
# Postgres
docker exec -it threat-detection-db psql -U user -d threat_detection_db

# Kafka
docker exec -it threat-detection-kafka bash

# List Kafka topics
docker exec threat-detection-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Stop/Start Services
```bash
# Stop all
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v

# Start all
docker-compose -f docker-compose.dev.yml up -d

# Restart single service
docker-compose -f docker-compose.dev.yml restart kafka
```

---

## Troubleshooting

### Backend Won't Start

**Port Already in Use**:
```bash
sudo lsof -i :8000
# Kill the process or use different port
```

**Kafka Not Ready**:
```bash
# Check Kafka health
docker ps --filter "name=threat-detection-kafka"

# If unhealthy, restart
docker-compose -f docker-compose.dev.yml restart kafka
```

### Database Issues

**Connection Refused**:
```bash
# Check Postgres is running
docker ps --filter "name=threat-detection-db"

# Test connection
docker exec threat-detection-db psql -U user -d threat_detection_db -c "SELECT 1"
```

**Reset Database**:
```bash
# WARNING: Deletes all data
docker-compose -f docker-compose.dev.yml down -v postgres_data
docker-compose -f docker-compose.dev.yml up -d postgres
```

### Kafka Issues

**Consumer Not Working**:
```bash
# Check consumer groups
docker exec threat-detection-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 --list

# Check consumer lag
docker exec threat-detection-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group threat-detection-consumer --describe
```

**Test Kafka Connectivity**:
```bash
cd backend
source .venv/bin/activate
python -c "from confluent_kafka import Consumer; c = Consumer({'bootstrap.servers': 'localhost:29092', 'group.id': 'test'}); print(c.list_topics(timeout=5))"
```

---

## Testing the System

### 1. Upload CSV for Batch Prediction
```bash
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@frontend/test_data/sample_10_features.csv"
```

### 2. Check Predictions
```bash
curl "http://localhost:8000/api/v1/predictions?limit=10" | jq
```

### 3. WebSocket Real-time Monitoring
```bash
# Install wscat if needed: npm install -g wscat
wscat -c ws://localhost:8000/ws/realtime
```

### 4. Send Test Data to Kafka
```bash
curl -X POST "http://localhost:8000/api/v1/test/start-stream?duration=60&batch_size=10"
```

---

## Environment Variables

### Backend (.env or .env.local)
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/threat_detection_db

# Kafka (localhost:29092 for host access)
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
KAFKA_TOPIC_REALTIME_DATA=network-traffic
KAFKA_TOPIC_EXTERNAL_DATA=external-traffic
KAFKA_TOPIC_PREDICTIONS=predictions

# API
API_V1_PREFIX=/api/v1
DEBUG=True

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## ML Models

### Check Model Status
```bash
curl http://localhost:8000/api/v1/health/detailed | jq '.checks.models'
```

### Expected Output
```json
{
  "threat_detector": {
    "loaded": true,
    "version": "20251202_190554",
    "is_real": true
  },
  "attack_classifier": {
    "loaded": true,
    "version": "20251202_190554",
    "is_real": true
  }
}
```

### Upload New Model
```bash
curl -X POST "http://localhost:8000/api/v1/models/upload" \
  -F "file=@models/threat_detector_YYYYMMDD_HHMMSS.joblib" \
  -F "model_type=threat_detection" \
  -F "metadata={\"description\":\"Updated model\"}"
```

---

## Common Commands

### Full Stack Restart
```bash
# Stop everything
docker-compose -f docker-compose.dev.yml down
pkill -f "uvicorn app.main"

# Start infrastructure
docker-compose -f docker-compose.dev.yml up -d

# Wait for health
sleep 15

# Start backend
cd backend && source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

### View All Logs
```bash
# Backend
tail -f backend/logs/*.log

# Docker
docker-compose -f docker-compose.dev.yml logs -f
```

---

## Next Steps

1. ✅ Verify all services healthy: `curl http://localhost:8000/api/v1/health/detailed`
2. ✅ Upload test CSV: See "Testing the System" above
3. ✅ Check predictions: `curl http://localhost:8000/api/v1/predictions`
4. ✅ Start frontend: `cd frontend && npm run dev`
5. ✅ Test WebSocket: `wscat -c ws://localhost:8000/ws/realtime`

**For detailed deployment information**, see `backend/DEPLOYMENT_FIX_REPORT.md`
