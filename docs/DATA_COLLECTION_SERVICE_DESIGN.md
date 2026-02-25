# Data Collection Service Architecture Design

## Overview

This document outlines the architecture for a new multi-source data collection service that supports:
1. **Network packet capture** - Monitor traffic to the backend server using pcap/tcpdump
2. **External data provider** - Accept network traffic data from whitelisted external sources via Kafka
3. **Dynamic configuration** - Enable/disable data sources independently with IP whitelisting

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────┐   │
│  │ Dashboard        │  │ Settings Page    │  │ Real-time Monitor │   │
│  │ (Existing)       │  │ (NEW)            │  │ (Existing)         │   │
│  │                  │  │ - IP Whitelist   │  │                    │   │
│  │                  │  │ - Source Toggle  │  │                    │   │
│  └──────────────────┘  └──────────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                        ┌───────────┴───────────┐
                        │   REST API + WebSocket │
                        └───────────┬───────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    NEW API Endpoints                              │  │
│  │  /api/v1/config/sources         - Get/Update source status       │  │
│  │  /api/v1/config/whitelist       - CRUD IP whitelist              │  │
│  │  /api/v1/config/whitelist/{id}  - Get/Update/Delete specific IP  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                 NEW Data Collection Services                      │  │
│  │                                                                   │  │
│  │  ┌────────────────────────┐  ┌──────────────────────────────┐   │  │
│  │  │ PacketCaptureService   │  │ ExternalKafkaConsumerService │   │  │
│  │  │ - tcpdump/scapy        │  │ - Kafka consumer             │   │  │
│  │  │ - Feature extraction   │  │ - IP validation              │   │  │
│  │  │ - Enable/disable toggle│  │ - Enable/disable toggle      │   │  │
│  │  └────────────────────────┘  └──────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Existing ML Pipeline (Unchanged)                     │  │
│  │  ThreatDetector → AttackClassifier → SelfHealing                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐    ┌─────────────▼──────────┐   ┌──────────▼─────────┐
│  PostgreSQL    │    │     Kafka Cluster      │   │  Network Interface │
│  - IP Whitelist│    │  - network-traffic     │   │  (eth0/any)        │
│  - Source      │    │  - external-traffic    │   │                    │
│    Config      │    │    (NEW TOPIC)         │   │  Packet Capture    │
└────────────────┘    └────────────────────────┘   └────────────────────┘
```

## Database Schema Changes

### New Tables

#### 1. `ip_whitelist` - Store allowed external data provider IPs

```sql
CREATE TABLE ip_whitelist (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL UNIQUE,  -- Supports IPv4 and IPv6
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100),  -- For future authentication
    INDEX idx_ip_address (ip_address),
    INDEX idx_is_active (is_active)
);
```

#### 2. `data_source_config` - Store data source enable/disable state

```sql
CREATE TABLE data_source_config (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL UNIQUE,  -- 'packet_capture', 'external_kafka', 'internal_kafka'
    is_enabled BOOLEAN DEFAULT FALSE,
    description TEXT,
    config_params JSON,  -- Store source-specific config (e.g., interface name, topic name)
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_source_name (source_name)
);
```

#### 3. Update `traffic_data` table - Add source tracking

```sql
-- Add new column to existing table
ALTER TABLE traffic_data
ADD COLUMN data_source VARCHAR(50);  -- 'packet_capture', 'external_kafka', 'internal_kafka', 'upload'

CREATE INDEX idx_data_source ON traffic_data(data_source);
```

### SQLAlchemy Models

```python
# backend/app/models/database.py

class IPWhitelist(Base):
    __tablename__ = "ip_whitelist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(String(100))

class DataSourceConfig(Base):
    __tablename__ = "data_source_config"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(50), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False)
    description = Column(Text)
    config_params = Column(JSON)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### Pydantic Schemas

```python
# backend/app/models/schemas.py

class IPWhitelistCreate(BaseModel):
    ip_address: str
    description: Optional[str] = None
    is_active: bool = True

class IPWhitelistUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None

class IPWhitelistResponse(BaseModel):
    id: int
    ip_address: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    created_by: Optional[str]

class DataSourceConfigUpdate(BaseModel):
    is_enabled: bool
    config_params: Optional[Dict[str, Any]] = None

class DataSourceConfigResponse(BaseModel):
    id: int
    source_name: str
    is_enabled: bool
    description: Optional[str]
    config_params: Optional[Dict[str, Any]]
    updated_at: datetime
```

## New Services

### 1. Packet Capture Service

**File**: `backend/app/services/packet_capture.py`

**Purpose**: Capture network packets at the server interface and extract features

**Technology Options**:
- **Option A**: `tcpdump` + parsing (lightweight, requires root)
- **Option B**: `scapy` Python library (more flexible, easier integration)
- **Option C**: `pyshark` (Wireshark Python wrapper)

**Recommended**: **Scapy** for better Python integration

**Key Features**:
- Capture packets on specified interface (eth0, any, etc.)
- Filter by protocol (TCP/UDP) and ports
- Extract network features (src_ip, dst_ip, src_port, dst_port, protocol, packet_size, flags)
- Map to ML feature format (10 or 42 features)
- Async packet processing with asyncio
- Enable/disable via configuration
- Resource management (packet buffer limits)

**Implementation Outline**:
```python
from scapy.all import sniff, IP, TCP, UDP
import asyncio
from typing import Dict, Optional

class PacketCaptureService:
    def __init__(self, db: Session, config_service: ConfigService):
        self.db = db
        self.config_service = config_service
        self.is_running = False
        self.capture_task = None

    async def start_capture(self, interface: str = "any"):
        """Start packet capture on specified interface"""
        if not self.is_enabled():
            return

        self.is_running = True
        self.capture_task = asyncio.create_task(self._capture_loop(interface))

    async def stop_capture(self):
        """Stop packet capture gracefully"""
        self.is_running = False
        if self.capture_task:
            self.capture_task.cancel()

    def is_enabled(self) -> bool:
        """Check if packet capture is enabled in config"""
        return self.config_service.is_source_enabled("packet_capture")

    async def _capture_loop(self, interface: str):
        """Main capture loop"""
        while self.is_running:
            # Capture packets in batches
            packets = sniff(iface=interface, count=10, timeout=1)
            for packet in packets:
                if IP in packet:
                    features = self._extract_features(packet)
                    await self._process_packet(features)

    def _extract_features(self, packet) -> Dict:
        """Extract ML features from packet"""
        features = {}

        if IP in packet:
            features['src_ip'] = packet[IP].src
            features['dst_ip'] = packet[IP].dst
            features['protocol'] = packet[IP].proto

        if TCP in packet:
            features['src_port'] = packet[TCP].sport
            features['dst_port'] = packet[TCP].dport
            features['flags'] = packet[TCP].flags
            features['window'] = packet[TCP].window

        # Map to ML feature format (service, flag, src_bytes, etc.)
        return self._map_to_ml_features(features)

    async def _process_packet(self, features: Dict):
        """Process packet through ML pipeline"""
        # Store in database with source="packet_capture"
        # Send to prediction pipeline
        pass
```

### 2. External Kafka Consumer Service

**File**: `backend/app/kafka/external_consumer.py`

**Purpose**: Consume network traffic data from external providers via Kafka with IP validation

**Key Features**:
- Consume from new Kafka topic: `external-traffic`
- Validate sender IP against whitelist
- Enable/disable via configuration
- Same message format as existing internal consumer
- IP validation via metadata or message payload

**Implementation Outline**:
```python
from confluent_kafka import Consumer, KafkaException
from sqlalchemy.orm import Session
from app.services.ip_whitelist import IPWhitelistService

class ExternalKafkaConsumerService:
    def __init__(self, db: Session, config_service, whitelist_service: IPWhitelistService):
        self.db = db
        self.config_service = config_service
        self.whitelist_service = whitelist_service
        self.consumer = None
        self.is_running = False

    def start(self):
        """Start consuming from external-traffic topic"""
        if not self.is_enabled():
            return

        config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': 'external-traffic-consumer',
            'auto.offset.reset': 'latest'
        }

        self.consumer = Consumer(config)
        self.consumer.subscribe(['external-traffic'])
        self.is_running = True

        # Start consuming loop in background
        asyncio.create_task(self._consume_loop())

    def is_enabled(self) -> bool:
        return self.config_service.is_source_enabled("external_kafka")

    async def _consume_loop(self):
        """Main consumption loop"""
        while self.is_running:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue

            # Validate sender IP from message headers or payload
            sender_ip = self._extract_sender_ip(msg)
            if not self.whitelist_service.is_ip_allowed(sender_ip):
                logger.warning(f"Rejected message from non-whitelisted IP: {sender_ip}")
                continue

            # Process message
            await self._process_message(msg)

    def _extract_sender_ip(self, msg) -> str:
        """Extract sender IP from Kafka message"""
        # Option 1: From message headers (if producer sets it)
        headers = dict(msg.headers() or [])
        if 'sender_ip' in headers:
            return headers['sender_ip'].decode('utf-8')

        # Option 2: From message payload
        payload = json.loads(msg.value().decode('utf-8'))
        return payload.get('sender_ip', 'unknown')
```

### 3. IP Whitelist Service

**File**: `backend/app/services/ip_whitelist.py`

**Purpose**: Manage IP whitelist CRUD operations and validation

```python
from sqlalchemy.orm import Session
from app.models.database import IPWhitelist
from typing import List, Optional
import ipaddress

class IPWhitelistService:
    def __init__(self, db: Session):
        self.db = db

    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is in whitelist and active"""
        record = self.db.query(IPWhitelist).filter(
            IPWhitelist.ip_address == ip,
            IPWhitelist.is_active == True
        ).first()
        return record is not None

    def add_ip(self, ip: str, description: str = None) -> IPWhitelist:
        """Add IP to whitelist with validation"""
        # Validate IP format
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip}")

        # Check if already exists
        existing = self.db.query(IPWhitelist).filter(
            IPWhitelist.ip_address == ip
        ).first()
        if existing:
            raise ValueError(f"IP already exists: {ip}")

        whitelist_entry = IPWhitelist(
            ip_address=ip,
            description=description,
            is_active=True
        )
        self.db.add(whitelist_entry)
        self.db.commit()
        return whitelist_entry

    def get_all(self, active_only: bool = False) -> List[IPWhitelist]:
        """Get all whitelisted IPs"""
        query = self.db.query(IPWhitelist)
        if active_only:
            query = query.filter(IPWhitelist.is_active == True)
        return query.order_by(IPWhitelist.created_at.desc()).all()

    def delete_ip(self, ip_id: int) -> bool:
        """Delete IP from whitelist"""
        record = self.db.query(IPWhitelist).filter(IPWhitelist.id == ip_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            return True
        return False
```

### 4. Config Service

**File**: `backend/app/services/config_service.py`

**Purpose**: Manage data source configurations

```python
class ConfigService:
    def __init__(self, db: Session):
        self.db = db
        self._init_default_configs()

    def _init_default_configs(self):
        """Initialize default data source configs if not exist"""
        default_sources = [
            {
                "source_name": "packet_capture",
                "description": "Network packet capture from server interface",
                "is_enabled": False,
                "config_params": {"interface": "any", "buffer_size": 1000}
            },
            {
                "source_name": "external_kafka",
                "description": "External data providers via Kafka",
                "is_enabled": False,
                "config_params": {"topic": "external-traffic"}
            },
            {
                "source_name": "internal_kafka",
                "description": "Internal test data stream",
                "is_enabled": True,
                "config_params": {"topic": "network-traffic"}
            }
        ]

        for source in default_sources:
            existing = self.db.query(DataSourceConfig).filter(
                DataSourceConfig.source_name == source["source_name"]
            ).first()
            if not existing:
                config = DataSourceConfig(**source)
                self.db.add(config)

        self.db.commit()

    def is_source_enabled(self, source_name: str) -> bool:
        """Check if data source is enabled"""
        config = self.db.query(DataSourceConfig).filter(
            DataSourceConfig.source_name == source_name
        ).first()
        return config.is_enabled if config else False

    def update_source_status(self, source_name: str, is_enabled: bool):
        """Enable or disable a data source"""
        config = self.db.query(DataSourceConfig).filter(
            DataSourceConfig.source_name == source_name
        ).first()
        if config:
            config.is_enabled = is_enabled
            config.updated_at = func.now()
            self.db.commit()
```

## API Endpoints

### IP Whitelist Management

```python
# backend/app/api/routes/config.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])

@router.get("/whitelist", response_model=List[IPWhitelistResponse])
def get_whitelist(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all whitelisted IPs"""
    service = IPWhitelistService(db)
    return service.get_all(active_only=active_only)

@router.post("/whitelist", response_model=IPWhitelistResponse)
def add_ip_to_whitelist(
    data: IPWhitelistCreate,
    db: Session = Depends(get_db)
):
    """Add IP to whitelist"""
    service = IPWhitelistService(db)
    try:
        return service.add_ip(data.ip_address, data.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/whitelist/{ip_id}")
def remove_ip_from_whitelist(
    ip_id: int,
    db: Session = Depends(get_db)
):
    """Remove IP from whitelist"""
    service = IPWhitelistService(db)
    if service.delete_ip(ip_id):
        return {"message": "IP removed successfully"}
    raise HTTPException(status_code=404, detail="IP not found")

@router.patch("/whitelist/{ip_id}", response_model=IPWhitelistResponse)
def update_ip_whitelist(
    ip_id: int,
    data: IPWhitelistUpdate,
    db: Session = Depends(get_db)
):
    """Update IP whitelist entry"""
    # Implementation for updating description or active status
    pass
```

### Data Source Configuration

```python
@router.get("/sources", response_model=List[DataSourceConfigResponse])
def get_data_sources(db: Session = Depends(get_db)):
    """Get all data source configurations"""
    service = ConfigService(db)
    return service.get_all_sources()

@router.patch("/sources/{source_name}", response_model=DataSourceConfigResponse)
def update_data_source(
    source_name: str,
    data: DataSourceConfigUpdate,
    db: Session = Depends(get_db)
):
    """Enable/disable a data source"""
    service = ConfigService(db)
    service.update_source_status(source_name, data.is_enabled)

    # Trigger service start/stop based on new status
    if source_name == "packet_capture":
        packet_service = PacketCaptureService(db, service)
        if data.is_enabled:
            await packet_service.start_capture()
        else:
            await packet_service.stop_capture()

    return service.get_source(source_name)
```

## Frontend Implementation

### New Settings Page

**File**: `frontend/app/settings/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { getDataSources, updateDataSource, getWhitelist, addIPToWhitelist, deleteIP } from '@/lib/api';

export default function SettingsPage() {
  const [sources, setSources] = useState([]);
  const [whitelist, setWhitelist] = useState([]);
  const [newIP, setNewIP] = useState('');
  const [newIPDescription, setNewIPDescription] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    const [sourcesData, whitelistData] = await Promise.all([
      getDataSources(),
      getWhitelist()
    ]);
    setSources(sourcesData);
    setWhitelist(whitelistData);
  };

  const handleToggleSource = async (sourceName: string, isEnabled: boolean) => {
    await updateDataSource(sourceName, { is_enabled: !isEnabled });
    loadSettings();
  };

  const handleAddIP = async () => {
    if (!newIP) return;
    await addIPToWhitelist({ ip_address: newIP, description: newIPDescription });
    setNewIP('');
    setNewIPDescription('');
    loadSettings();
  };

  const handleDeleteIP = async (ipId: number) => {
    await deleteIP(ipId);
    loadSettings();
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      {/* Data Sources Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4">Data Sources</h2>
        <div className="bg-white rounded-lg shadow p-6">
          {sources.map((source) => (
            <div key={source.source_name} className="flex items-center justify-between py-3 border-b">
              <div>
                <h3 className="font-medium">{source.source_name.replace('_', ' ').toUpperCase()}</h3>
                <p className="text-sm text-gray-600">{source.description}</p>
              </div>
              <button
                onClick={() => handleToggleSource(source.source_name, source.is_enabled)}
                className={`px-4 py-2 rounded ${
                  source.is_enabled ? 'bg-green-500 text-white' : 'bg-gray-300'
                }`}
              >
                {source.is_enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* IP Whitelist Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">IP Whitelist (External Data Providers)</h2>

        {/* Add IP Form */}
        <div className="bg-white rounded-lg shadow p-6 mb-4">
          <h3 className="font-medium mb-3">Add New IP</h3>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="IP Address (e.g., 192.168.1.100)"
              value={newIP}
              onChange={(e) => setNewIP(e.target.value)}
              className="flex-1 border px-3 py-2 rounded"
            />
            <input
              type="text"
              placeholder="Description (optional)"
              value={newIPDescription}
              onChange={(e) => setNewIPDescription(e.target.value)}
              className="flex-1 border px-3 py-2 rounded"
            />
            <button
              onClick={handleAddIP}
              className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600"
            >
              Add IP
            </button>
          </div>
        </div>

        {/* IP List */}
        <div className="bg-white rounded-lg shadow">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left">IP Address</th>
                <th className="px-6 py-3 text-left">Description</th>
                <th className="px-6 py-3 text-left">Status</th>
                <th className="px-6 py-3 text-left">Created At</th>
                <th className="px-6 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {whitelist.map((entry) => (
                <tr key={entry.id} className="border-b">
                  <td className="px-6 py-3 font-mono">{entry.ip_address}</td>
                  <td className="px-6 py-3">{entry.description || '-'}</td>
                  <td className="px-6 py-3">
                    <span className={`px-2 py-1 rounded text-sm ${
                      entry.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {entry.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-3">{new Date(entry.created_at).toLocaleString()}</td>
                  <td className="px-6 py-3">
                    <button
                      onClick={() => handleDeleteIP(entry.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
```

### Update Navigation

**File**: `frontend/app/layout.tsx`

Add Settings link to navigation:
```typescript
<nav>
  <Link href="/">Upload</Link>
  <Link href="/dashboard">Dashboard</Link>
  <Link href="/realtime">Real-time</Link>
  <Link href="/settings">Settings</Link> {/* NEW */}
</nav>
```

### API Client Updates

**File**: `frontend/lib/api.ts`

```typescript
// Data Source Configuration
export async function getDataSources() {
  const response = await api.get('/api/v1/config/sources');
  return response.data;
}

export async function updateDataSource(sourceName: string, data: { is_enabled: boolean }) {
  const response = await api.patch(`/api/v1/config/sources/${sourceName}`, data);
  return response.data;
}

// IP Whitelist Management
export async function getWhitelist(activeOnly: boolean = false) {
  const response = await api.get('/api/v1/config/whitelist', {
    params: { active_only: activeOnly }
  });
  return response.data;
}

export async function addIPToWhitelist(data: { ip_address: string; description?: string }) {
  const response = await api.post('/api/v1/config/whitelist', data);
  return response.data;
}

export async function deleteIP(ipId: number) {
  const response = await api.delete(`/api/v1/config/whitelist/${ipId}`);
  return response.data;
}
```

## Docker and Infrastructure Updates

### New Kafka Topic

**File**: `docker-compose.full.yml`

Add topic creation for external-traffic:
```yaml
kafka:
  environment:
    KAFKA_CREATE_TOPICS: "network-traffic:1:1,external-traffic:1:1,predictions:1:1"
```

### Packet Capture Service

Since packet capture requires root/network privileges, add to docker-compose:

```yaml
# backend/Dockerfile - Add scapy
RUN pip install scapy

# docker-compose.full.yml - Add network capabilities
backend:
  cap_add:
    - NET_ADMIN
    - NET_RAW
  network_mode: "host"  # Or use bridge with proper configuration
```

## Security Considerations

1. **Packet Capture Permissions**:
   - Requires root or CAP_NET_RAW capability
   - Should be isolated in Docker container
   - Consider using non-privileged user with capabilities

2. **IP Validation**:
   - Validate IP format before storing
   - Support both IPv4 and IPv6
   - Consider subnet whitelisting (e.g., 192.168.1.0/24)

3. **Rate Limiting**:
   - Implement rate limiting on external Kafka topic
   - Prevent DoS from whitelisted IPs
   - Monitor data volume per IP

4. **Authentication** (Future):
   - Add API key authentication for external producers
   - JWT tokens for frontend API calls
   - Role-based access control for settings

## Data Flow Examples

### Packet Capture Flow
```
Server receives HTTP request
    ↓
Packet captured by scapy (if enabled)
    ↓
Extract features (IP, port, protocol, flags)
    ↓
Map to ML feature format (10 or 42 features)
    ↓
Store in TrafficData (source="packet_capture")
    ↓
Run through ML pipeline
    ↓
Broadcast prediction via WebSocket
```

### External Provider Flow
```
External system produces to Kafka topic "external-traffic"
    ↓
ExternalKafkaConsumer receives message
    ↓
Extract sender IP from message/headers
    ↓
Validate against IP whitelist (if not whitelisted, reject)
    ↓
Store in TrafficData (source="external_kafka")
    ↓
Run through ML pipeline
    ↓
Broadcast prediction via WebSocket
```

## Migration Path

1. **Phase 1**: Database schema migration (Alembic)
2. **Phase 2**: Implement IP whitelist service and API
3. **Phase 3**: Implement config service and API
4. **Phase 4**: Implement packet capture service
5. **Phase 5**: Implement external Kafka consumer
6. **Phase 6**: Build frontend settings page
7. **Phase 7**: Integration testing
8. **Phase 8**: Update documentation

## Testing Strategy

1. **Unit Tests**:
   - IP validation logic
   - Feature extraction from packets
   - Whitelist CRUD operations

2. **Integration Tests**:
   - Packet capture → ML pipeline
   - External Kafka → Validation → ML pipeline
   - API endpoints

3. **Manual Tests**:
   - Toggle sources on/off via UI
   - Add/remove IPs from whitelist
   - Send test data from external producer
   - Verify packet capture with tcpdump

## Performance Considerations

1. **Packet Capture**:
   - Buffer size limits (prevent memory overflow)
   - Batch processing (process packets in groups)
   - Async processing (don't block capture loop)

2. **Kafka Consumer**:
   - Consumer group for scaling
   - Batch commits for performance
   - Error handling and retries

3. **Database**:
   - Index on ip_address for fast lookup
   - Index on source_name and is_active
   - Connection pooling

## Next Steps

1. Review and approve this design
2. Create database migration scripts
3. Implement backend services incrementally
4. Build frontend settings UI
5. Test each component independently
6. Integration testing with all sources
7. Documentation and deployment guide
