# AI Threat Detection & Self-Healing System - Technical Summary

## Executive Summary

A real-time network threat detection and automated response system that leverages machine learning to identify and classify network attacks, with built-in self-healing capabilities. The system processes network traffic data through Kafka streams, applies AI-based threat detection models, and automatically triggers remediation actions.

## System Architecture

### High-Level Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API    │────▶│   PostgreSQL    │
│   (Next.js)     │◀────│   (FastAPI)      │◀────│   Database      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │
        │                        │
        │                        ▼
        │               ┌──────────────────┐
        │               │  Kafka Consumer  │
        │               │   & Producer     │
        │               └──────────────────┘
        │                        │
        │                        ▼
        │               ┌──────────────────┐
        └──────────────▶│   WebSocket      │
         (Real-time)    │   Connection     │
                        └──────────────────┘
```

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.109.0
- **ASGI Server**: Uvicorn 0.27.0
- **Database ORM**: SQLAlchemy 2.0.25
- **Database**: PostgreSQL 15
- **Message Broker**: Apache Kafka (Confluent 7.5.0)
- **ML Libraries**:
  - NumPy 1.26.3
  - Pandas 2.2.0
  - Scikit-learn 1.4.0
- **WebSocket**: websockets 12.0
- **Testing**: pytest 7.4.4, pytest-asyncio

#### Frontend
- **Framework**: Next.js 14.2.0
- **Runtime**: React 18
- **Styling**: Tailwind CSS 3.3.0
- **Charts**: Recharts 2.12.0
- **HTTP Client**: Axios 1.6.7
- **Testing**: Jest 29.7.0, Playwright 1.41.0

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL 15 Alpine
- **Message Queue**: Kafka + Zookeeper (Confluent Platform 7.5.0)

## Core Components

### 1. Backend Service (FastAPI)

#### Main Application (`backend/app/main.py`)
- Initializes FastAPI application
- Configures CORS middleware
- Registers API routes
- Starts Kafka consumer on startup
- Manages application lifecycle

#### API Routes

**Upload Routes** (`backend/app/api/routes/upload.py`)
- `POST /api/v1/upload/csv` - Upload and process CSV files
- `GET /api/v1/upload/batches` - Retrieve batch processing history
- `GET /api/v1/upload/batch/{batch_id}` - Get specific batch predictions

**Prediction Routes** (`backend/app/api/routes/predictions.py`)
- `GET /api/v1/predictions/recent` - Recent predictions
- `GET /api/v1/predictions/stats` - Statistical overview
- `GET /api/v1/predictions/threats` - Threat-specific data
- `GET /api/v1/predictions/attacks` - Attack classifications
- `GET /api/v1/predictions/actions` - Self-healing action logs

**Test Producer Routes** (`backend/app/api/routes/test_producer.py`)
- `POST /api/v1/test/start-stream` - Generate test traffic stream
- `POST /api/v1/test/send-single` - Send single test message

**WebSocket Route** (`backend/app/api/routes/websocket.py`)
- `WS /ws/realtime` - Real-time prediction updates

#### ML Models

**Threat Detector** (`backend/app/services/threat_detector.py`)
- **Type**: Binary classification (Normal vs Attack)
- **Features**: 10 network traffic features
- **Model**: Ensemble (ANN + LSTM)
- **Input**: service, flag, src_bytes, dst_bytes, count, same_srv_rate, diff_srv_rate, dst_host_srv_count, dst_host_same_srv_rate, dst_host_same_src_port_rate

**Attack Classifier** (`backend/app/services/attack_classifier.py`)
- **Type**: Multi-class classification
- **Features**: 42 network traffic features
- **Model**: Decision Tree
- **Classes**: 14 attack types (BENIGN, DoS Hulk, DDoS, PortScan, FTP-Patator, DoS slowloris, DoS Slowhttptest, SSH-Patator, DoS GoldenEye, Web Attack – Brute Force, Bot, Web Attack – XSS, Web Attack – Sql Injection, Infiltration)

#### Data Processing

**Preprocessor** (`backend/app/services/preprocessor.py`)
- Auto-detects data format (10 or 42 features)
- Validates and normalizes input data
- Routes to appropriate model based on feature count

**Self-Healing Service** (`backend/app/services/self_healing.py`)
- Determines appropriate response actions
- Action types:
  - `restart_service` - Restart affected services (apache2, nginx)
  - `block_ip` - Block malicious IP addresses
  - `alert_admin` - Send administrator alerts
  - `log_only` - Log without execution

#### Message Queue

**Kafka Producer** (`backend/app/kafka/producer.py`)
- Sends network traffic data to Kafka topics
- Topic: `network-traffic`
- Asynchronous message delivery

**Kafka Consumer** (`backend/app/kafka/consumer.py`)
- Listens to `network-traffic` topic
- Processes incoming traffic data
- Runs predictions through ML models
- Stores results in PostgreSQL
- Broadcasts to WebSocket clients
- Runs continuously in background thread

#### WebSocket Manager (`backend/app/services/websocket_manager.py`)
- Manages active WebSocket connections
- Broadcasts real-time predictions
- Heartbeat mechanism (30s interval)
- Auto-cleanup of stale connections

#### Database Models (`backend/app/models/database.py`)
- `ThreatPrediction` - Threat detection results
- `AttackClassification` - Attack type classifications
- `SelfHealingAction` - Automated response actions
- `UploadBatch` - CSV upload tracking

### 2. Frontend Service (Next.js)

#### Pages

**Home Page** (`frontend/app/page.tsx`)
- Landing page
- CSV upload interface
- Quick start guide

**Dashboard** (`frontend/app/dashboard/page.tsx`)
- Threat statistics overview
- Attack distribution visualization
- Prediction history table
- Self-healing actions log

**Real-time Monitor** (`frontend/app/realtime/page.tsx`)
- Live WebSocket connection
- Stream test data generation
- Real-time prediction display

#### Components

**CSVUploader** (`frontend/components/CSVUploader.tsx`)
- Drag-and-drop file upload
- File validation
- Upload progress tracking
- Error handling

**ThreatDetectionChart** (`frontend/components/ThreatDetectionChart.tsx`)
- Pie chart showing threat vs normal traffic
- Recharts integration

**AttackDistributionChart** (`frontend/components/AttackDistributionChart.tsx`)
- Bar chart of attack types
- Color-coded by severity

**PredictionHistoryTable** (`frontend/components/PredictionHistoryTable.tsx`)
- Paginated table of predictions
- Sortable columns
- Timestamp formatting

**SelfHealingActionsTable** (`frontend/components/SelfHealingActionsTable.tsx`)
- Action history display
- Status indicators
- Service/IP details

#### Hooks

**useWebSocket** (`frontend/hooks/useWebSocket.ts`)
- Custom React hook for WebSocket
- Auto-reconnect logic
- Message handling
- Connection state management

#### API Client (`frontend/lib/api.ts`)
- Axios-based HTTP client
- Centralized API endpoint configuration
- Error handling
- Type-safe requests

### 3. Infrastructure Services

#### PostgreSQL Database
- **Container**: postgres:15-alpine
- **Port**: 5432
- **Database**: threat_detection_db
- **Health Check**: pg_isready
- **Persistence**: Volume-backed storage

#### Apache Kafka
- **Container**: confluentinc/cp-kafka:7.5.0
- **Ports**: 9092 (internal), 29092 (host)
- **Topics**:
  - `network-traffic` - Input data stream
  - `predictions` - Prediction results
- **Configuration**:
  - Auto-create topics enabled
  - Replication factor: 1
  - Broker ID: 1

#### Zookeeper
- **Container**: confluentinc/cp-zookeeper:7.5.0
- **Port**: 2181
- **Purpose**: Kafka cluster coordination

## Data Flow

### CSV Upload Flow
1. User uploads CSV via frontend
2. Frontend sends file to `/api/v1/upload/csv`
3. Backend validates and parses CSV
4. Data processed through preprocessor
5. Predictions run through appropriate ML model
6. Results stored in PostgreSQL
7. Response returned to frontend
8. Dashboard updated with new data

### Real-time Streaming Flow
1. Network traffic sent to Kafka topic
2. Kafka consumer picks up messages
3. Preprocessor validates and routes data
4. ML models generate predictions
5. Results saved to database
6. Predictions broadcast via WebSocket
7. Frontend receives real-time updates
8. UI updates automatically

### Self-Healing Flow
1. Threat/attack detected by ML models
2. Self-healing service determines action
3. Action logged to database
4. Action executed (or logged only)
5. Admin notified if configured
6. Result stored for audit trail

## Deployment Modes

### Development Mode (Recommended)
**Command**: `docker-compose -f docker-compose.dev.yml up -d`

**Services in Docker**:
- PostgreSQL (localhost:5432)
- Kafka (localhost:29092)
- Zookeeper (localhost:2181)

**Services Run Locally**:
- Backend (localhost:8000)
- Frontend (localhost:3000)

**Benefits**:
- Hot-reload for backend
- Fast refresh for frontend
- Easy debugging
- Quick iteration

### Production Mode
**Command**: `docker-compose -f docker-compose.full.yml up -d`

**All Services in Docker**:
- Backend container
- Frontend container
- PostgreSQL
- Kafka
- Zookeeper

**Benefits**:
- Production-like environment
- Integration testing
- Consistent deployment
- Isolated networking

## Directory Structure

```
ui/
├── backend/                    # FastAPI backend service
│   ├── alembic/               # Database migrations
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/        # API endpoint definitions
│   │   │       ├── predictions.py
│   │   │       ├── upload.py
│   │   │       ├── websocket.py
│   │   │       └── test_producer.py
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py      # Settings and environment
│   │   │   └── database.py    # DB connection setup
│   │   ├── kafka/             # Kafka integration
│   │   │   ├── consumer.py    # Message consumer
│   │   │   └── producer.py    # Message producer
│   │   ├── models/            # Data models
│   │   │   ├── database.py    # SQLAlchemy models
│   │   │   ├── ml_models.py   # ML model wrappers
│   │   │   └── schemas.py     # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── threat_detector.py
│   │   │   ├── attack_classifier.py
│   │   │   ├── preprocessor.py
│   │   │   ├── self_healing.py
│   │   │   └── websocket_manager.py
│   │   └── main.py            # Application entry point
│   ├── tests/                 # Backend tests
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # Next.js frontend
│   ├── app/                   # Next.js 14 app router
│   │   ├── dashboard/         # Dashboard page
│   │   ├── realtime/          # Real-time monitor
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Home page
│   ├── components/            # React components
│   │   ├── CSVUploader.tsx
│   │   ├── ThreatDetectionChart.tsx
│   │   ├── AttackDistributionChart.tsx
│   │   ├── PredictionHistoryTable.tsx
│   │   └── SelfHealingActionsTable.tsx
│   ├── hooks/                 # Custom React hooks
│   │   └── useWebSocket.ts
│   ├── lib/                   # Utilities
│   │   └── api.ts             # API client
│   ├── e2e/                   # Playwright tests
│   ├── __tests__/             # Jest unit tests
│   └── package.json           # Node dependencies
│
├── research/                   # Documentation and research
├── docker-compose.dev.yml     # Development infrastructure
├── docker-compose.full.yml    # Full stack deployment
├── .env.example               # Environment template
├── .env.local                 # Local environment config
├── start.sh                   # Quick start script
└── README.md                  # User documentation
```

## Key Features

### 1. Dual-Model AI Detection
- Binary threat detection (10 features)
- Multi-class attack classification (42 features)
- Auto-detection of input format
- Ensemble and decision tree algorithms

### 2. Real-time Processing
- Kafka-based streaming architecture
- WebSocket push notifications
- Sub-second detection latency
- Scalable message queue

### 3. Self-Healing Automation
- Automated threat response
- Multiple action types
- Audit logging
- Admin notifications

### 4. Interactive Dashboard
- Real-time statistics
- Visual analytics (charts/graphs)
- Prediction history
- Action tracking

### 5. Batch Processing
- CSV file upload
- Bulk data analysis
- Batch tracking
- Historical analysis

### 6. Developer-Friendly
- Comprehensive API documentation (FastAPI Swagger)
- Hot-reload development mode
- Extensive test coverage
- Docker-based deployment

## Attack Types Detected

1. **BENIGN** - Normal traffic
2. **DoS Hulk** - Denial of Service attack
3. **DDoS** - Distributed Denial of Service
4. **PortScan** - Port scanning activity
5. **FTP-Patator** - FTP brute force
6. **DoS slowloris** - Slowloris DoS attack
7. **DoS Slowhttptest** - Slow HTTP test attack
8. **SSH-Patator** - SSH brute force
9. **DoS GoldenEye** - GoldenEye DoS attack
10. **Web Attack – Brute Force** - Web brute force
11. **Bot** - Botnet activity
12. **Web Attack – XSS** - Cross-site scripting
13. **Web Attack – Sql Injection** - SQL injection
14. **Infiltration** - Network infiltration

## Configuration

### Environment Variables

#### Backend
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/threat_detection_db
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

#### Frontend
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Testing

### Backend Tests
```bash
cd backend
pytest                    # Run all tests
pytest --cov             # With coverage
pytest -v                # Verbose output
```

### Frontend Tests
```bash
cd frontend
npm test                 # Jest unit tests
npm run test:watch       # Watch mode
npm run test:e2e         # Playwright E2E tests
```

## Performance Considerations

- **Kafka**: Enables horizontal scaling of consumers
- **WebSocket**: Efficient real-time communication
- **PostgreSQL**: Indexed database for fast queries
- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Efficient database connections
- **Batch Processing**: Optimized for bulk operations

## Security Features

- CORS configuration for frontend
- Database connection encryption
- Environment-based configuration
- Input validation (Pydantic schemas)
- SQL injection protection (ORM)
- XSS protection (React)

## Monitoring & Observability

- Database health checks
- Kafka health checks
- Service health endpoints
- WebSocket connection tracking
- Self-healing action logging
- Prediction history tracking

## Future Enhancement Opportunities

1. **Model Training Pipeline**: Add automated model retraining
2. **Authentication**: Implement user authentication/authorization
3. **Advanced Self-Healing**: Execute actual remediation actions
4. **Alerting System**: Email/SMS notifications
5. **Multi-tenancy**: Support multiple organizations
6. **Advanced Analytics**: Trend analysis and reporting
7. **API Rate Limiting**: Protect against abuse
8. **Metrics & Logging**: Prometheus/Grafana integration

## License

MIT

## Technical Contact

Built with FastAPI, Next.js, Apache Kafka, and PostgreSQL.
