# AI Threat Detection & Self-Healing System

A comprehensive, real-time network threat detection system with automated self-healing capabilities.

## Features

- **Threat Detection**: Binary classification using ensemble model (ANN + LSTM)
- **Attack Classification**: Multi-class classification identifying 14 attack types
- **Self-Healing Actions**: Automated response logging for detected threats
- **Real-time Processing**: Kafka-based streaming for live threat detection
- **Interactive Dashboard**: Real-time visualization of threats and attacks
- **CSV Upload**: Batch processing of network traffic data

## Architecture

### Backend (FastAPI)

- RESTful API for data upload and predictions
- WebSocket endpoint for real-time updates
- Kafka consumer for streaming data
- PostgreSQL database for persistence
- Mock ML models (Ensemble & Decision Tree)

### Frontend (Next.js 14)

- Interactive dashboards with charts
- Real-time monitoring with WebSocket
- CSV upload interface
- Responsive design with Tailwind CSS

### Infrastructure

- PostgreSQL: Data storage
- Kafka + Zookeeper: Message streaming
- Docker Compose: Service orchestration

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Option 1: Full Stack with Docker (Production-like)

1. Clone the repository:

```bash
cd ui
```

2. Start all services:

```bash
docker-compose --env-file .env.example -f docker-compose.full.yml up -d
```

3. Wait for services to be healthy (check with `docker-compose ps`)

4. Access the application:
   - Frontend: <http://localhost:3000>
   - Backend API: <http://localhost:8000>
   - API Docs: <http://localhost:8000/docs>

### Option 2: Development Mode (Recommended)

This mode runs infrastructure services (Postgres, Kafka, Zookeeper) in Docker while allowing you to run backend and frontend locally for faster development.

#### Step 1: Start Infrastructure Services

```bash
docker-compose --env-file .env -f docker-compose.dev.yml up -d
```

This starts:

- PostgreSQL on port 5432
- Kafka on ports 9092 (internal) and 29092 (host)
- Zookeeper on port 2181

#### Step 2: Run Backend Locally

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Configure environment to connect to Docker services
export DATABASE_URL="postgresql://user:password@localhost:5432/threat_detection_db"
export KAFKA_BOOTSTRAP_SERVERS="localhost:29092"

# Run the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 3: Run Frontend Locally

```bash
cd frontend
npm install

# Run the frontend
npm run dev
```

#### Step 4: Access the Application

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>
- API Docs: <http://localhost:8000/docs>

### Stopping Services

For development mode:

```bash
# Stop backend and frontend (Ctrl+C in their terminals)
# Stop infrastructure services
docker-compose -f docker-compose.dev.yml down
```

For full stack:

```bash
docker-compose -f docker-compose.full.yml down
```

## Usage Guide

### 1. Upload CSV Data

- Navigate to <http://localhost:3000>
- Click "Upload" or drag and drop a CSV file
- Wait for processing to complete
- View results in the dashboard

### 2. View Dashboard

- Go to Dashboard tab
- See threat statistics and attack distribution
- View prediction history and self-healing actions

### 3. Monitor Real-time Traffic

- Navigate to "Real-time Monitor"
- Click "Start Test Stream" to generate sample traffic
- Watch live predictions appear

### 4. API Documentation

- Visit <http://localhost:8000/docs> for interactive API documentation
- Test endpoints directly from the browser

## API Endpoints

### Upload

- `POST /api/v1/upload/csv` - Upload CSV file for analysis
- `GET /api/v1/upload/batches` - List uploaded batches
- `GET /api/v1/upload/batch/{batch_id}` - Get batch predictions

### Predictions

- `GET /api/v1/predictions/recent` - Get recent predictions
- `GET /api/v1/predictions/stats` - Get prediction statistics
- `GET /api/v1/predictions/threats` - Get threat predictions
- `GET /api/v1/predictions/attacks` - Get attack classifications
- `GET /api/v1/predictions/actions` - Get self-healing actions

### Testing

- `POST /api/v1/test/start-stream` - Start test data stream
- `POST /api/v1/test/send-single` - Send single test message

### WebSocket

- `WS /ws/realtime` - Real-time prediction updates

## Data Formats

### Threat Detection (10 features)

```csv
service,flag,src_bytes,dst_bytes,count,same_srv_rate,diff_srv_rate,dst_host_srv_count,dst_host_same_srv_rate,dst_host_same_src_port_rate
5,2,1500,2000,10,0.8,0.1,50,0.75,0.9
```

### Attack Classification (42 features)

See research/README.md for complete feature list.

## Attack Types Detected

1. BENIGN
2. DoS Hulk
3. DDoS
4. PortScan
5. FTP-Patator
6. DoS slowloris
7. DoS Slowhttptest
8. SSH-Patator
9. DoS GoldenEye
10. Web Attack – Brute Force
11. Bot
12. Web Attack – XSS
13. Web Attack – Sql Injection
14. Infiltration

## Self-Healing Actions

- **restart_service**: Restart affected services (apache2, nginx)
- **block_ip**: Block malicious IP addresses
- **alert_admin**: Send alerts to administrators
- **log_only**: Log action without execution

## Testing

### Backend Tests (pytest)

```bash
cd backend
pytest
```

### Frontend Tests (jest)

```bash
cd frontend
npm test
```

### E2E Tests (playwright)

```bash
cd frontend
npm run test:e2e
```

## Development

### Docker Compose Files

This project includes three Docker Compose configurations:

1. **`docker-compose.yml`** (Original/Legacy)
   - Contains all services together
   - Kept for backward compatibility

2. **`docker-compose.dev.yml`** (Development - Recommended)
   - Runs only infrastructure services: PostgreSQL, Kafka, Zookeeper
   - Use when developing backend/frontend locally
   - Benefits: Hot-reloading, faster iteration, easier debugging
   - Backend connects to `localhost:5432` (Postgres) and `localhost:29092` (Kafka)

3. **`docker-compose.full.yml`** (Production-like)
   - Runs complete stack including backend and frontend containers
   - Use for integration testing or production-like environment
   - All services communicate via Docker network

### Backend Structure

```
backend/
├── app/
│   ├── api/routes/       # API endpoints
│   ├── core/             # Config and database
│   ├── kafka/            # Kafka consumer/producer
│   ├── models/           # DB and ML models
│   └── services/         # Business logic
├── tests/                # Tests
└── requirements.txt      # Dependencies
```

### Frontend Structure

```
frontend/
├── app/                  # Next.js pages
├── components/           # React components
├── hooks/                # Custom hooks
├── lib/                  # Utilities and API client
└── tests/                # Tests
```

## Environment Variables

### Development Mode (Local Backend/Frontend)

When running backend locally with `docker-compose.dev.yml`, use these environment variables:

```bash
# Backend (.env or export)
DATABASE_URL=postgresql://user:password@localhost:5432/threat_detection_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=threat_detection_db
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
KAFKA_TOPIC_REALTIME_DATA=network-traffic
KAFKA_TOPIC_PREDICTIONS=predictions
KAFKA_GROUP_ID=threat-detection-consumer
API_V1_PREFIX=/api/v1
PROJECT_NAME="AI Threat Detection System"
DEBUG=True
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
WS_HEARTBEAT_INTERVAL=30
```

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Docker Mode (Full Stack)

When using `docker-compose.full.yml`, environment variables are configured in the compose file. You can override them with a `.env` file:

```bash
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=threat_detection_db
```

See `.env.example` for all configuration options.

## Troubleshooting

### Services not starting

For development mode:

```bash
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

For full stack:

```bash
docker-compose -f docker-compose.full.yml down -v
docker-compose -f docker-compose.full.yml up -d
```

### Database connection issues

Check PostgreSQL logs:

```bash
docker-compose -f docker-compose.dev.yml logs postgres
# or
docker-compose -f docker-compose.full.yml logs postgres
```

Test connection from host:

```bash
psql -h localhost -U user -d threat_detection_db
# Password: password
```

### Kafka not receiving messages

Check Kafka logs:

```bash
docker-compose -f docker-compose.dev.yml logs kafka
```

Create sample kafka topic:

```bash
ocker exec threat-detection-kafka kafka-topics --create --topic predictions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

List Kafka topics:

```bash
docker exec threat-detection-kafka kafka-topics --list --bootstrap-server localhost:9092
```

Send message to topic:

#### Option 1: Threat Detection (10 features) - Binary classification (Normal vs Attack)

```bash
echo '{"service":5,"flag":2,"src_bytes":1500,"dst_bytes":2000,"count":10,"same_srv_rate":0.8,"diff_srv_rate":0.1,"dst_host_srv_count":50,"dst_host_same_srv_rate":0.75,"dst_host_same_src_port_rate":0.9}' \
| docker exec -i threat-detection-kafka kafka-console-producer \
    --broker-list kafka:9092 \
    --topic network-traffic
```

#### Option 2: Attack Classification (42 features) - Multi-class attack type detection

```bash
echo '{" Destination Port":80," Flow Duration":5000," Total Fwd Packets":50,"Total Length of Fwd Packets":5000," Fwd Packet Length Max":1500," Fwd Packet Length Min":60,"Bwd Packet Length Max":1500," Bwd Packet Length Min":60,"Flow Bytes/s":1000," Flow Packets/s":10," Flow IAT Mean":100," Flow IAT Std":50," Flow IAT Min":10,"Bwd IAT Total":500," Bwd IAT Std":25,"Fwd PSH Flags":1," Bwd PSH Flags":1," Fwd URG Flags":0," Bwd URG Flags":0," Fwd Header Length":200," Bwd Header Length":200," Bwd Packets/s":5," Min Packet Length":60,"FIN Flag Count":1," RST Flag Count":0," PSH Flag Count":2," ACK Flag Count":10," URG Flag Count":0," Down/Up Ratio":0.5,"Fwd Avg Bytes/Bulk":500," Fwd Avg Packets/Bulk":5," Fwd Avg Bulk Rate":100," Bwd Avg Bytes/Bulk":500," Bwd Avg Packets/Bulk":5,"Bwd Avg Bulk Rate":100,"Init_Win_bytes_forward":8192," Init_Win_bytes_backward":8192," min_seg_size_forward":20,"Active Mean":100," Active Std":50," Active Max":200," Idle Std":25}' \
| docker exec -i threat-detection-kafka kafka-console-producer \
    --broker-list kafka:9092 \
    --topic network-traffic
```

> **Note**: The system auto-detects which model to use based on available features. Send either 10 threat detection features OR 42 attack classification features.

Consume messages from topic:

```bash
docker exec threat-detection-kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic network-traffic \
  --from-beginning
```

### Backend not connecting to services

When running backend locally, ensure you're using the correct ports:

- Postgres: `localhost:5432` (not `postgres:5432`)
- Kafka: `localhost:29092` (not `kafka:9092`)

Check if services are accessible:

```bash
# Test Postgres
nc -zv localhost 5432

# Test Kafka
nc -zv localhost 29092
```

### Frontend not connecting to backend

Verify backend is running:

```bash
curl http://localhost:8000/health
```

Check environment variables in frontend:

```bash
# Should be set in .env.local or environment
echo $NEXT_PUBLIC_API_URL
echo $NEXT_PUBLIC_WS_URL
```

### Port conflicts

If ports are already in use, modify the port mappings in the compose file:

```yaml
ports:
  - "5433:5432"  # Change host port (5433) instead of container port
```

### Clearing all data

To reset everything including volumes:

```bash
docker-compose -f docker-compose.dev.yml down -v
# or
docker-compose -f docker-compose.full.yml down -v
```

## License

MIT

## Contributors

Built with FastAPI, Next.js, Kafka, and PostgreSQL.
