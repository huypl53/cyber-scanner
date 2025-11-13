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

### Running with Docker Compose

1. Clone the repository:
```bash
cd ui
```

2. Start all services:
```bash
docker-compose up -d
```

3. Wait for services to be healthy (check with `docker-compose ps`)

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Running Locally (Development)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Usage Guide

### 1. Upload CSV Data
- Navigate to http://localhost:3000
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
- Visit http://localhost:8000/docs for interactive API documentation
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

See `.env.example` for all configuration options.

## Troubleshooting

### Services not starting
```bash
docker-compose down -v
docker-compose up -d
```

### Database connection issues
```bash
docker-compose logs postgres
```

### Kafka not receiving messages
```bash
docker-compose logs kafka
```

## License

MIT

## Contributors

Built with FastAPI, Next.js, Kafka, and PostgreSQL.
