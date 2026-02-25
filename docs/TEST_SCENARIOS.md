# AI Threat Detection & Self-Healing System - Complete Test Scenarios

**Generated**: 2026-02-25
**System**: AI Threat Detection & Self-Healing Platform
**Stack**: FastAPI + Next.js 14 + PostgreSQL + Kafka + WebSocket

---

## Table of Contents

1. [Unit Tests - Backend](#1-unit-tests---backend)
2. [Unit Tests - Frontend](#2-unit-tests---frontend)
3. [Integration Tests](#3-integration-tests)
4. [API Tests](#4-api-tests)
5. [ML Model Tests](#5-ml-model-tests)
6. [Data Pipeline Tests](#6-data-pipeline-tests)
7. [WebSocket Tests](#7-websocket-tests)
8. [End-to-End (E2E) Tests](#8-end-to-end-e2e-tests)
9. [Performance & Load Tests](#9-performance--load-tests)
10. [Security Tests](#10-security-tests)
11. [Infrastructure Tests](#11-infrastructure-tests)
12. [Regression Tests](#12-regression-tests)

---

## 1. Unit Tests - Backend

### 1.1 Preprocessor Service (`app/services/preprocessor.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-PRE-001 | Detect threat detection features (10 features) | CSV with `flag, src_bytes, dst_bytes, count, diff_srv_rate, dst_host_srv_count, dst_host_same_srv_rate, dst_host_diff_srv_rate, dst_host_same_src_port_rate, dst_host_srv_diff_host_rate` | `model_type = "threat_detection"` | High |
| UT-PRE-002 | Detect attack classification features (42 features) | CSV with 42 CIC-IDS2017 features | `model_type = "attack_classification"` | High |
| UT-PRE-003 | Reject CSV with missing required features | CSV with only 5 of 10 threat detection features | Raise validation error with list of missing features | High |
| UT-PRE-004 | Handle extra/unknown columns gracefully | CSV with 10 valid features + 3 extra columns | Extract only required features, ignore extras | Medium |
| UT-PRE-005 | Validate numeric ranges for threat detection | `src_bytes = -1` (negative value) | Raise or clamp to valid range | Medium |
| UT-PRE-006 | Handle NaN/Inf values in features | CSV row with `NaN` in `dst_bytes` | Replace with 0 or raise descriptive error | High |
| UT-PRE-007 | Handle empty CSV | CSV with headers only, no data rows | Return empty list or raise "no data" error | Medium |
| UT-PRE-008 | Handle CSV with only one row | Single row of valid data | Process successfully, return single prediction | Low |
| UT-PRE-009 | Validate feature types (string vs numeric) | `src_bytes = "abc"` (non-numeric) | Raise type validation error | Medium |
| UT-PRE-010 | Extract features for ensemble model | Valid 10-feature dict | Return correctly ordered numpy array | High |

### 1.2 Threat Detector Service (`app/services/threat_detector.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-TD-001 | Predict normal traffic | Features representing normal traffic pattern | `is_attack = false`, `prediction_score < 0.5` | High |
| UT-TD-002 | Predict attack traffic | Features representing attack pattern (high src_bytes, abnormal flags) | `is_attack = true`, `prediction_score >= 0.5` | High |
| UT-TD-003 | Batch prediction (multiple rows) | List of 100 feature dicts | List of 100 prediction results | High |
| UT-TD-004 | Prediction includes model version | Any valid input | Response contains `model_version` field matching loaded model | Medium |
| UT-TD-005 | Prediction score is between 0 and 1 | Any valid input | `0.0 <= prediction_score <= 1.0` | High |
| UT-TD-006 | Handle missing model gracefully | No .joblib file in models/ | Fall back to mock model with warning log | Medium |
| UT-TD-007 | Singleton pattern loads model once | Call `get_ensemble_model()` twice | Same instance returned both times | Low |
| UT-TD-008 | Reload model clears cache | Call `reload_models()` then `get_ensemble_model()` | New instance loaded | Low |
| UT-TD-009 | Prediction persists to database | Valid features with db session | ThreatPrediction record created in DB | High |
| UT-TD-010 | Threshold configurable | Set threshold to 0.3 | Predictions above 0.3 classified as attack | Medium |

### 1.3 Attack Classifier Service (`app/services/attack_classifier.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-AC-001 | Classify BENIGN traffic | Features matching normal traffic | `attack_type_name = "BENIGN"`, high confidence | High |
| UT-AC-002 | Classify DoS Hulk attack | Features matching DoS Hulk pattern | `attack_type_name = "DoS Hulk"` | High |
| UT-AC-003 | Classify DDoS attack | Features matching DDoS pattern | `attack_type_name = "DDoS"` | High |
| UT-AC-004 | Classify PortScan | Features matching port scan pattern | `attack_type_name = "PortScan"` | High |
| UT-AC-005 | Classify all 14 attack types | 14 different feature sets | Each classified correctly | Medium |
| UT-AC-006 | Return confidence score | Any valid 42-feature input | `0.0 <= confidence <= 1.0` | High |
| UT-AC-007 | Return encoded + named attack type | Any attack input | Both `attack_type_encoded` (int) and `attack_type_name` (string) present | Medium |
| UT-AC-008 | Batch prediction (multiple rows) | List of 500 feature dicts | List of 500 classification results | High |
| UT-AC-009 | Prediction persists to database | Valid features with db session | AttackPrediction record created in DB | High |
| UT-AC-010 | Handle model fallback | No real model available | Fall back to mock model | Medium |

### 1.4 Self-Healing Service (`app/services/self_healing.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-SH-001 | Map DoS attack to rate limiting | Attack type = "DoS Hulk" | `action_type = "rate_limit"` or `"block_ip"` | High |
| UT-SH-002 | Map PortScan to firewall rule | Attack type = "PortScan" | `action_type = "block_ip"` or `"firewall_rule"` | High |
| UT-SH-003 | Map Web Attack to WAF alert | Attack type = "Web Attack – XSS" | `action_type = "alert_admin"` or `"waf_alert"` | High |
| UT-SH-004 | Map Infiltration to host isolation | Attack type = "Infiltration" | `action_type = "isolate_host"` or `"alert_admin"` | High |
| UT-SH-005 | BENIGN traffic triggers no action | Attack type = "BENIGN" | No self-healing action created | High |
| UT-SH-006 | Action status defaults to pending | Any attack type | `status = "pending"` | Medium |
| UT-SH-007 | Log action batch | List of 10 attack predictions | 10 SelfHealingAction records in DB (excluding BENIGN) | High |
| UT-SH-008 | Map SSH-Patator to block_ip | Attack type = "SSH-Patator" | `action_type = "block_ip"` | Medium |
| UT-SH-009 | Map Bot to alert_admin | Attack type = "Bot" | `action_type = "alert_admin"` | Medium |
| UT-SH-010 | Map SQL Injection to WAF | Attack type = "Web Attack – Sql Injection" | Appropriate action type | Medium |

### 1.5 IP Whitelist Service (`app/services/ip_whitelist.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-WL-001 | Add valid IPv4 address | `ip_address = "192.168.1.100"` | IP added to whitelist, returns record | High |
| UT-WL-002 | Add valid IPv6 address | `ip_address = "::1"` | IP added to whitelist | Medium |
| UT-WL-003 | Reject invalid IP format | `ip_address = "999.999.999.999"` | Raise ValueError | High |
| UT-WL-004 | Reject duplicate IP | Add same IP twice | Raise ValueError on second add | High |
| UT-WL-005 | Check whitelisted IP is allowed | IP exists in whitelist with `is_active = true` | `is_ip_allowed()` returns `true` | High |
| UT-WL-006 | Check non-whitelisted IP is rejected | IP not in whitelist | `is_ip_allowed()` returns `false` | High |
| UT-WL-007 | Inactive IP is rejected | IP exists but `is_active = false` | `is_ip_allowed()` returns `false` | High |
| UT-WL-008 | Delete IP from whitelist | Valid `ip_id` | Record removed, returns `true` | Medium |
| UT-WL-009 | Delete non-existent IP | Invalid `ip_id` | Returns `false` | Medium |
| UT-WL-010 | Get all IPs with active_only filter | Mix of active/inactive IPs | Only active IPs returned when `active_only=True` | Medium |

### 1.6 Config Service (`app/services/config_service.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-CS-001 | Initialize default configs | Fresh database | 3 data sources created (packet_capture, external_kafka, internal_kafka) | High |
| UT-CS-002 | Check enabled source | Source with `is_enabled = true` | `is_source_enabled()` returns `true` | High |
| UT-CS-003 | Check disabled source | Source with `is_enabled = false` | `is_source_enabled()` returns `false` | High |
| UT-CS-004 | Enable a data source | `source_name = "external_kafka"`, `is_enabled = true` | Source updated to enabled | High |
| UT-CS-005 | Disable a data source | `source_name = "internal_kafka"`, `is_enabled = false` | Source updated to disabled | High |
| UT-CS-006 | Check non-existent source | `source_name = "unknown"` | Returns `false` | Medium |
| UT-CS-007 | Idempotent default init | Call `_init_default_configs()` twice | No duplicates, same 3 records | Medium |

### 1.7 Model Validator (`app/services/model_validator.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-MV-001 | Validate valid .joblib file | Valid RandomForest .joblib | Validation passes, test prediction succeeds | High |
| UT-MV-002 | Validate valid .pkl file | Valid pickle model file | Validation passes | Medium |
| UT-MV-003 | Reject corrupt model file | Corrupted .joblib file | Validation fails with descriptive error | High |
| UT-MV-004 | Reject wrong input shape (threat) | Model expecting 20 features, declared as threat_detector (10) | Input shape mismatch error | High |
| UT-MV-005 | Reject wrong input shape (attack) | Model expecting 10 features, declared as attack_classifier (42) | Input shape mismatch error | High |
| UT-MV-006 | Reject unsupported file format | `.txt` file | Unsupported format error | Medium |
| UT-MV-007 | Validate ensemble bundle structure | Bundle with model, scaler, selected_features, metadata | All required keys present | High |
| UT-MV-008 | Validate attack classifier bundle | Bundle with model, scaler, label_encoder, attack_types | All required keys present | High |

### 1.8 Model Manager (`app/services/model_manager.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-MM-001 | Upload and store model | Valid .joblib file, model_type = "threat_detector" | Model saved to filesystem, DB record created | High |
| UT-MM-002 | Activate model (deactivates others) | Activate model ID 2 | Model 2 active, all other threat_detectors inactive | High |
| UT-MM-003 | Deactivate model | Active model ID | `is_active = false` | Medium |
| UT-MM-004 | Delete inactive model | Inactive model ID | File and DB record removed | Medium |
| UT-MM-005 | Reject delete active model | Active model ID | Error: cannot delete active model | High |
| UT-MM-006 | Get storage stats | Multiple uploaded models | Correct total count, size, breakdown by type | Medium |
| UT-MM-007 | Load active model | Active model exists | Model loaded and returned | High |
| UT-MM-008 | Load when no active model | No active models | Return None or raise error | Medium |

### 1.9 WebSocket Manager (`app/services/websocket_manager.py`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-WS-001 | Register new connection | WebSocket connection | Connection added to active set | High |
| UT-WS-002 | Remove disconnected connection | Disconnected WebSocket | Connection removed from active set | High |
| UT-WS-003 | Broadcast to all connections | Prediction message | All connected clients receive message | High |
| UT-WS-004 | Heartbeat sent on interval | 30 seconds elapsed | Heartbeat message sent to all clients | Medium |
| UT-WS-005 | Handle broadcast to 0 connections | No active connections | No errors, log message | Low |
| UT-WS-006 | Cleanup stale connections | Connection that fails to receive | Connection removed silently | Medium |

---

## 2. Unit Tests - Frontend

### 2.1 CSVUploader Component (`components/CSVUploader.tsx`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-FE-CSV-001 | Render upload form | Mount component | File input and upload button visible | High |
| UT-FE-CSV-002 | Accept .csv file | Select valid .csv file | File name displayed, upload enabled | High |
| UT-FE-CSV-003 | Reject non-CSV file | Select .txt file | Error message: only CSV files accepted | High |
| UT-FE-CSV-004 | Show upload progress | Trigger upload | Progress indicator visible during upload | Medium |
| UT-FE-CSV-005 | Display success message | Successful upload response | Success message with batch ID and stats | High |
| UT-FE-CSV-006 | Display error message | Failed upload (400/500) | Error message displayed | High |
| UT-FE-CSV-007 | Show stats after upload | Successful upload with predictions | Attacks detected count, normal traffic count displayed | High |
| UT-FE-CSV-008 | Handle null threat_prediction | Attack classification response (threat_prediction=null) | No crash, stats calculated correctly | High |
| UT-FE-CSV-009 | Drag-and-drop upload | Drop .csv file on dropzone | File accepted and ready to upload | Medium |
| UT-FE-CSV-010 | Link to dashboard after upload | Successful upload | "View Dashboard" link visible and clickable | Low |

### 2.2 Dashboard Charts

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-FE-CHART-001 | Render ThreatDetectionChart | Stats with attacks and normal traffic | Pie chart with correct proportions | High |
| UT-FE-CHART-002 | Render AttackDistributionChart | Stats with multiple attack types | Bar chart with all attack types | High |
| UT-FE-CHART-003 | Handle empty stats | No predictions in database | Empty state or "No data" message | Medium |
| UT-FE-CHART-004 | Render PredictionHistoryTable | List of recent predictions | Table with rows, sortable columns | High |
| UT-FE-CHART-005 | Render SelfHealingActionsTable | List of actions | Table with action type, status, timestamps | Medium |
| UT-FE-CHART-006 | Pagination in history table | 50+ predictions | Pagination controls visible and functional | Medium |

### 2.3 useWebSocket Hook (`hooks/useWebSocket.ts`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-FE-WS-001 | Connect to WebSocket | Valid WS URL | Connection status = "Connected" | High |
| UT-FE-WS-002 | Handle connection failure | Invalid WS URL | Connection status = "Disconnected" | High |
| UT-FE-WS-003 | Receive prediction message | Server sends prediction | `onMessage` callback invoked with parsed data | High |
| UT-FE-WS-004 | Auto-reconnect on disconnect | Server closes connection | Reconnect attempt after delay | Medium |
| UT-FE-WS-005 | Cleanup on unmount | Component unmounts | WebSocket connection closed | Medium |

### 2.4 API Client (`lib/api.ts`)

| ID | Scenario | Input | Expected Output | Priority |
|----|----------|-------|-----------------|----------|
| UT-FE-API-001 | Fetch prediction stats | Call `getStats()` | Returns stats object with total_predictions, attack_rate | High |
| UT-FE-API-002 | Upload CSV file | Call `uploadCSV(file)` | Returns batch ID and predictions | High |
| UT-FE-API-003 | Fetch data sources | Call `getDataSources()` | Returns array of 3 sources | Medium |
| UT-FE-API-004 | Add IP to whitelist | Call `addIPToWhitelist({ip_address: "1.2.3.4"})` | Returns created whitelist entry | Medium |
| UT-FE-API-005 | Handle 500 error | Server returns 500 | Error propagated to caller | High |
| UT-FE-API-006 | Handle network timeout | Server unreachable | Timeout error raised | Medium |

---

## 3. Integration Tests

### 3.1 CSV Upload → Prediction Pipeline

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| IT-001 | Upload threat detection CSV end-to-end | 1. Create 10-feature CSV 2. POST to `/api/v1/upload/csv` 3. Check response 4. Query predictions table | Predictions stored in DB, response includes prediction scores | Critical |
| IT-002 | Upload attack classification CSV end-to-end | 1. Create 42-feature CSV 2. POST to `/api/v1/upload/csv` 3. Check response | Attack types classified, self-healing actions logged | Critical |
| IT-003 | Upload → Dashboard stats update | 1. Upload CSV 2. GET `/api/v1/predictions/stats` | Stats reflect new predictions (total, attack_rate) | High |
| IT-004 | Upload → Database persistence | 1. Upload CSV with 10 rows 2. Query `traffic_data` table 3. Query `threat_predictions` table | 10 traffic records + 10 prediction records in DB | High |
| IT-005 | Batch ID tracking | 1. Upload CSV 2. GET `/api/v1/upload/batch/{batch_id}` | All predictions from upload share same batch_id | Medium |

### 3.2 Model Management Pipeline

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| IT-006 | Upload → Validate → Store model | 1. POST model .joblib to `/api/v1/models/upload` 2. Check filesystem 3. Check DB | Model file saved, validation results stored, DB record created | High |
| IT-007 | Upload → Activate → Predict with new model | 1. Upload new threat_detector model 2. Activate it 3. Upload CSV | Predictions use new model version | High |
| IT-008 | Model activation deactivates others | 1. Upload 2 threat_detector models 2. Activate model A 3. Activate model B | Only model B is active, model A deactivated | High |
| IT-009 | Model profile matches active model | 1. Activate model 2. GET `/api/v1/models/profile/threat_detector` | Profile features match active model's features | Medium |

### 3.3 Configuration Integration

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| IT-010 | Add IP → Verify whitelist check | 1. POST IP to whitelist 2. Call `is_ip_allowed()` | IP recognized as allowed | High |
| IT-011 | Toggle data source → Service state | 1. Enable external_kafka via API 2. Check consumer status | External consumer starts (or is ready) | High |
| IT-012 | Disable data source → Stop consumer | 1. Disable internal_kafka via API 2. Verify consumer stopped | Consumer no longer processing messages | Medium |

### 3.4 Database Integration

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| IT-013 | Foreign key relationships | 1. Create traffic_data record 2. Create threat_prediction linked to it | FK constraint satisfied, join query works | High |
| IT-014 | Alembic migration up/down | 1. `alembic upgrade head` 2. Verify all tables 3. `alembic downgrade -1` | Tables created and removed cleanly | High |
| IT-015 | Concurrent DB writes | 1. Upload 3 CSVs simultaneously 2. Check all data persisted | No deadlocks, all records created | Medium |

---

## 4. API Tests

### 4.1 Health & Status Endpoints

| ID | Endpoint | Method | Test | Expected | Priority |
|----|----------|--------|------|----------|----------|
| API-001 | `/health` | GET | Basic health check | `200 OK`, `{"status": "healthy"}` | Critical |
| API-002 | `/api/v1/health/detailed` | GET | Detailed health check | 200 with DB, Kafka, model status | High |
| API-003 | `/docs` | GET | Swagger UI | 200 with HTML page | Low |

### 4.2 Upload Endpoints

| ID | Endpoint | Method | Test | Expected | Priority |
|----|----------|--------|------|----------|----------|
| API-004 | `/api/v1/upload/csv` | POST | Upload valid 10-feature CSV | 200 with predictions array | Critical |
| API-005 | `/api/v1/upload/csv` | POST | Upload valid 42-feature CSV | 200 with attack classifications | Critical |
| API-006 | `/api/v1/upload/csv` | POST | Upload empty file | 400 Bad Request | High |
| API-007 | `/api/v1/upload/csv` | POST | Upload non-CSV file | 400 or 422 error | High |
| API-008 | `/api/v1/upload/csv` | POST | Upload CSV with wrong features | 400 with missing features list | High |
| API-009 | `/api/v1/upload/csv` | POST | Upload large CSV (1000+ rows) | 200 with all predictions, < 5s | High |
| API-010 | `/api/v1/upload/csv` | POST | Upload without file field | 422 Unprocessable Entity | Medium |
| API-011 | `/api/v1/upload/batches` | GET | List upload batches | 200 with array of batch summaries | Medium |
| API-012 | `/api/v1/upload/batch/{id}` | GET | Get specific batch | 200 with batch predictions | Medium |
| API-013 | `/api/v1/upload/batch/{id}` | GET | Get non-existent batch | 404 Not Found | Medium |

### 4.3 Prediction Endpoints

| ID | Endpoint | Method | Test | Expected | Priority |
|----|----------|--------|------|----------|----------|
| API-014 | `/api/v1/predictions/stats` | GET | Get prediction statistics | 200 with total_predictions, attack_rate, distribution | High |
| API-015 | `/api/v1/predictions/recent` | GET | Get recent predictions | 200 with array, newest first | High |
| API-016 | `/api/v1/predictions/threats` | GET | Get threat detections only | 200 with threat predictions array | Medium |
| API-017 | `/api/v1/predictions/attacks` | GET | Get attack classifications only | 200 with attack predictions array | Medium |
| API-018 | `/api/v1/predictions/actions` | GET | Get self-healing actions | 200 with actions array | Medium |

### 4.4 Model Management Endpoints

| ID | Endpoint | Method | Test | Expected | Priority |
|----|----------|--------|------|----------|----------|
| API-019 | `/api/v1/models/` | GET | List all models | 200 with models array | High |
| API-020 | `/api/v1/models/` | GET | Filter by model_type | 200 with filtered results | Medium |
| API-021 | `/api/v1/models/upload` | POST | Upload valid .joblib model | 200 with model record + validation results | High |
| API-022 | `/api/v1/models/upload` | POST | Upload invalid model file | 400 with validation errors | High |
| API-023 | `/api/v1/models/upload` | POST | Upload oversized file (>500MB) | 413 or 400 error | Medium |
| API-024 | `/api/v1/models/{id}` | GET | Get model details | 200 with full model metadata | Medium |
| API-025 | `/api/v1/models/{id}` | GET | Get non-existent model | 404 Not Found | Medium |
| API-026 | `/api/v1/models/{id}/activate` | POST | Activate model | 200, model becomes active | High |
| API-027 | `/api/v1/models/{id}/deactivate` | POST | Deactivate model | 200, model becomes inactive | Medium |
| API-028 | `/api/v1/models/{id}` | DELETE | Delete inactive model | 200, model removed | Medium |
| API-029 | `/api/v1/models/{id}` | DELETE | Delete active model | 400, cannot delete active model | High |
| API-030 | `/api/v1/models/stats/storage` | GET | Get storage statistics | 200 with counts and sizes | Medium |
| API-031 | `/api/v1/models/profile/threat_detector` | GET | Get threat detector profile | 200 with expected_features, class_labels | High |
| API-032 | `/api/v1/models/profile/attack_classifier` | GET | Get attack classifier profile | 200 with 42 features, 14 class_labels | High |
| API-033 | `/api/v1/models/info/supported-formats` | GET | Get supported model formats | 200 with [".pkl", ".joblib", ".h5"] | Low |

### 4.5 Configuration Endpoints

| ID | Endpoint | Method | Test | Expected | Priority |
|----|----------|--------|------|----------|----------|
| API-034 | `/api/v1/config/sources` | GET | List data sources | 200 with 3 sources (packet_capture, external_kafka, internal_kafka) | High |
| API-035 | `/api/v1/config/sources/{name}` | GET | Get specific source | 200 with source details | Medium |
| API-036 | `/api/v1/config/sources/{name}` | PATCH | Enable source | 200, `is_enabled = true` | High |
| API-037 | `/api/v1/config/sources/{name}` | PATCH | Disable source | 200, `is_enabled = false` | High |
| API-038 | `/api/v1/config/sources/invalid` | PATCH | Update non-existent source | 404 Not Found | Medium |
| API-039 | `/api/v1/config/whitelist` | GET | List whitelisted IPs | 200 with IP array | High |
| API-040 | `/api/v1/config/whitelist` | GET | Filter active only | 200 with only active IPs | Medium |
| API-041 | `/api/v1/config/whitelist` | POST | Add valid IP | 201 with created record | High |
| API-042 | `/api/v1/config/whitelist` | POST | Add invalid IP format | 400 Bad Request | High |
| API-043 | `/api/v1/config/whitelist` | POST | Add duplicate IP | 400 with "already exists" error | High |
| API-044 | `/api/v1/config/whitelist/{id}` | GET | Get specific IP entry | 200 with entry details | Medium |
| API-045 | `/api/v1/config/whitelist/{id}` | PATCH | Update IP description | 200 with updated record | Medium |
| API-046 | `/api/v1/config/whitelist/{id}` | PATCH | Toggle IP active/inactive | 200 with updated status | Medium |
| API-047 | `/api/v1/config/whitelist/{id}` | DELETE | Remove IP | 200 with success message | Medium |
| API-048 | `/api/v1/config/whitelist/999` | DELETE | Remove non-existent IP | 404 Not Found | Medium |

### 4.6 Test Producer Endpoints

| ID | Endpoint | Method | Test | Expected | Priority |
|----|----------|--------|------|----------|----------|
| API-049 | `/api/v1/test/start-stream` | POST | Start test data stream | 200, stream started | Medium |
| API-050 | `/api/v1/test/send-single` | POST | Send single test message | 200, message sent to Kafka | Medium |

---

## 5. ML Model Tests

### 5.1 Model Loading & Initialization

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| ML-001 | Load threat_detector .joblib on startup | Model loaded, log: "Loaded real threat detection model: {version}" | Critical |
| ML-002 | Load attack_classifier .joblib on startup | Model loaded, log: "Loaded real attack classification model: {version}" | Critical |
| ML-003 | Auto-discover latest model file | Finds most recent .joblib by modification time | High |
| ML-004 | Fallback to mock when no real model | Warning logged, mock model used for predictions | High |
| ML-005 | Model bundle contains all required keys | `model`, `scaler`, `selected_features`, `metadata` present | High |
| ML-006 | Attack classifier bundle has attack_types mapping | `attack_types` dict with 14 entries (0-13) | High |

### 5.2 Model Inference

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| ML-007 | Single prediction latency < 100ms | Measured inference time under SLA | Critical |
| ML-008 | Batch 100 predictions < 1 second | Batch inference within target | High |
| ML-009 | Batch 1000 predictions < 5 seconds | Large batch within target | High |
| ML-010 | Prediction output shape matches expected | Threat: single probability. Attack: class + confidence | High |
| ML-011 | Scaler correctly applied during inference | Features scaled using saved scaler before prediction | High |
| ML-012 | Label encoder correctly maps attack types | Encoded labels decoded to correct attack names | High |

### 5.3 Model Upload Pipeline

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| ML-013 | Upload .joblib threat detector | File validated, stored, DB record created | High |
| ML-014 | Upload .joblib attack classifier | File validated, stored, DB record created | High |
| ML-015 | Upload .pkl model | Pickle model loaded and validated | Medium |
| ML-016 | Upload .h5 Keras model | TensorFlow model loaded (if TF installed) | Low |
| ML-017 | Reject model with wrong feature count | Validation error: input shape mismatch | High |
| ML-018 | Model version uses timestamp format | Version format: YYYYMMDD_HHMMSS | Medium |

---

## 6. Data Pipeline Tests

### 6.1 Kafka Producer

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| DP-001 | Send message to network-traffic topic | Message delivered, offset returned | High |
| DP-002 | Generate test threat data | Valid 10-feature message published | Medium |
| DP-003 | Generate test attack data | Valid 42-feature message published | Medium |
| DP-004 | Handle Kafka broker unavailable | Error logged, no crash | High |
| DP-005 | Message serialization (JSON) | Message correctly serialized and deserializable | Medium |

### 6.2 Internal Kafka Consumer

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| DP-006 | Consume from network-traffic topic | Message received and processed | High |
| DP-007 | Process message through ML pipeline | Prediction generated and stored in DB | High |
| DP-008 | Broadcast prediction via WebSocket | Connected clients receive prediction | High |
| DP-009 | Handle malformed message | Error logged, consumer continues | High |
| DP-010 | Consumer group offset commit | Offsets committed, no duplicate processing | Medium |
| DP-011 | Consumer recovery after restart | Resumes from last committed offset | Medium |

### 6.3 External Kafka Consumer

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| DP-012 | Consume from external-traffic topic | Message received | High |
| DP-013 | Accept message from whitelisted IP | Message processed through ML pipeline | Critical |
| DP-014 | Reject message from non-whitelisted IP | Message rejected, warning logged | Critical |
| DP-015 | Extract sender_ip from message headers | IP correctly extracted from Kafka headers | High |
| DP-016 | Extract sender_ip from message payload | IP extracted from JSON payload field | High |
| DP-017 | Consumer respects enable/disable config | Disabled consumer does not process messages | High |
| DP-018 | Data source tagged as "external_kafka" | traffic_data record has `source = "external_kafka"` | Medium |

---

## 7. WebSocket Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| WS-001 | Client connects to `/ws/realtime` | Connection established, status = connected | Critical |
| WS-002 | Client receives prediction broadcast | Prediction JSON received after Kafka message processed | Critical |
| WS-003 | Multiple clients receive same broadcast | 3 connected clients all receive the prediction | High |
| WS-004 | Client disconnect handled gracefully | No errors on server, connection removed from active set | High |
| WS-005 | Heartbeat sent every 30 seconds | Client receives heartbeat ping | Medium |
| WS-006 | Reconnect after server restart | Client reconnects automatically | Medium |
| WS-007 | 100+ concurrent WebSocket connections | All connections maintained, broadcasts succeed | Medium |
| WS-008 | Prediction payload structure | Contains: traffic_data, threat_prediction, attack_prediction, self_healing_action | High |

---

## 8. End-to-End (E2E) Tests

### 8.1 CSV Upload Flow

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| E2E-001 | Upload threat detection CSV via UI | 1. Open http://localhost:3000 2. Select `threat_detection_test.csv` (10 features) 3. Click Upload 4. Verify success message | Success message: "Successfully processed N rows", batch ID shown, stats (attacks/normal) displayed | Critical |
| E2E-002 | Upload attack classification CSV via UI | 1. Open http://localhost:3000 2. Select `attack_classification_test.csv` (42 features) 3. Click Upload | Success message with attack types classified, self-healing actions noted | Critical |
| E2E-003 | Upload → View Dashboard | 1. Upload CSV 2. Click "View Dashboard" link 3. Verify dashboard updates | Dashboard shows updated total predictions, attack rate, charts reflect new data | Critical |
| E2E-004 | Upload → Dashboard stats cards | 1. Upload 10 rows (mix of attack/normal) 2. Navigate to `/dashboard` | Stats cards show: Total Predictions = N, Attacks Detected = X, Normal = Y, Attack Rate = % | High |
| E2E-005 | Upload → Prediction History Table | 1. Upload CSV 2. Navigate to dashboard 3. Scroll to prediction table | Table shows recent predictions with timestamps, scores, attack types | High |
| E2E-006 | Upload invalid file type | 1. Try to upload a .txt file via UI | Error message displayed, upload rejected | High |
| E2E-007 | Upload empty CSV | 1. Upload CSV with only headers | Appropriate error or "0 rows processed" message | Medium |
| E2E-008 | Upload large CSV (1000 rows) | 1. Upload `threat_validation_1000.csv` 2. Wait for processing 3. Check dashboard | All 1000 predictions processed, dashboard reflects data, processing < 5 seconds | High |

### 8.2 Real-Time Monitoring Flow

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| E2E-009 | WebSocket connection on realtime page | 1. Navigate to http://localhost:3000/realtime 2. Check connection status | WebSocket status indicator shows "Connected" (or "Disconnected" if Kafka disabled) | High |
| E2E-010 | Start test stream | 1. Open `/realtime` page 2. Click "Start Test Stream" 3. Observe predictions | Predictions appear in real-time, counters update live | High |
| E2E-011 | Real-time stats update | 1. Start test stream 2. Monitor stats counters | Total Received, Attacks Detected, Normal Traffic counters increment in real-time | High |
| E2E-012 | Stop and resume stream | 1. Start stream 2. Note count 3. Stop stream 4. Resume | Counts persist, new predictions append after resume | Medium |
| E2E-013 | Multiple browser tabs real-time | 1. Open `/realtime` in 2 tabs 2. Start test stream | Both tabs receive predictions simultaneously | Medium |

### 8.3 Model Management Flow

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| E2E-014 | View model profiles | 1. Navigate to http://localhost:3000/models | Storage stats displayed, model profiles for threat_detector (10 features) and attack_classifier (42 features, 14 attack types) shown | High |
| E2E-015 | Upload new model via UI | 1. Go to `/models` 2. Select model type 3. Choose .joblib file 4. Click Upload | Upload succeeds, validation results shown, model appears in list | High |
| E2E-016 | Activate uploaded model | 1. Upload model 2. Click "Activate" | Model status changes to Active, other models of same type deactivated | High |
| E2E-017 | Delete inactive model | 1. Deactivate model 2. Click Delete 3. Confirm | Model removed from list, storage stats updated | Medium |
| E2E-018 | Upload → Activate → Predict | 1. Upload new threat_detector 2. Activate it 3. Upload CSV 4. Verify predictions use new model | `model_version` in prediction response matches newly activated model | High |

### 8.4 Settings & Configuration Flow

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| E2E-019 | View settings page | 1. Navigate to http://localhost:3000/settings | Data Sources section with 3 sources, IP Whitelist section visible | High |
| E2E-020 | Toggle data source | 1. Open Settings 2. Click toggle on "External Kafka Stream" | Status changes from Disabled to Enabled (or vice versa), confirmed via API | High |
| E2E-021 | Add IP to whitelist | 1. Enter IP "192.168.1.100" 2. Enter description "Test" 3. Click "Add IP" | IP appears in whitelist table with Active status | High |
| E2E-022 | Delete IP from whitelist | 1. Click "Delete" on an IP entry | IP removed from table | Medium |
| E2E-023 | Toggle IP active/inactive | 1. Click toggle on an active IP | Status changes to Inactive | Medium |
| E2E-024 | Invalid IP validation | 1. Enter "not-an-ip" 2. Click Add | Error message: invalid IP format | High |

### 8.5 Dashboard Analytics Flow

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| E2E-025 | Empty dashboard state | 1. Fresh database 2. Navigate to `/dashboard` | All stats show 0, "No data" state for charts | Medium |
| E2E-026 | Dashboard after threat upload | 1. Upload threat CSV 2. Go to dashboard | Threat detection chart shows attack/normal distribution | High |
| E2E-027 | Dashboard after attack upload | 1. Upload attack CSV 2. Go to dashboard | Attack distribution chart shows classified attack types | High |
| E2E-028 | Dashboard refresh button | 1. View dashboard 2. Upload CSV in another tab 3. Click Refresh | Stats and charts update with latest data | Medium |
| E2E-029 | Self-healing actions on dashboard | 1. Upload attack CSV with attack detections 2. View dashboard | Self-healing actions table shows logged actions with types and pending status | Medium |

### 8.6 Navigation & UX Flow

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| E2E-030 | Navigate all pages | 1. Click Upload → Dashboard → Real-time → Models → Settings | All pages load without errors, navigation active state correct | High |
| E2E-031 | Responsive layout (desktop) | 1. View all pages at 1920x1080 | Proper layout, no overflow, readable text | Medium |
| E2E-032 | Responsive layout (tablet) | 1. View all pages at 768x1024 | Layout adapts, still usable | Low |
| E2E-033 | POC disclaimer visible | 1. Visit any page | POC disclaimer banner visible on pages | Medium |
| E2E-034 | Error handling - backend down | 1. Stop backend 2. Navigate to dashboard | Error message with retry button, not blank page | High |
| E2E-035 | Language switcher | 1. Click language switcher 2. Switch between EN/VI | UI text changes to selected language | Medium |

### 8.7 Cross-Feature E2E

| ID | Scenario | Steps | Expected Result | Priority |
|----|----------|-------|-----------------|----------|
| E2E-036 | Full threat detection lifecycle | 1. Upload threat CSV 2. View dashboard stats 3. Check prediction history 4. Verify DB records | Complete flow: upload → predict → store → display | Critical |
| E2E-037 | Full attack classification lifecycle | 1. Upload attack CSV 2. View dashboard 3. Check attack distribution 4. Check self-healing actions | Complete flow: upload → classify → self-heal → display | Critical |
| E2E-038 | Model swap and re-predict | 1. Upload CSV with model A 2. Upload new model B 3. Activate model B 4. Upload same CSV | Predictions differ between model A and B | High |
| E2E-039 | External data provider flow | 1. Add IP to whitelist 2. Enable external_kafka 3. Send message from whitelisted IP via Kafka 4. Check dashboard | Prediction appears with `source = "external_kafka"` | High |
| E2E-040 | External data rejection flow | 1. Enable external_kafka 2. Send message from non-whitelisted IP 3. Check logs 4. Check dashboard | Message rejected, no prediction created, warning logged | High |
| E2E-041 | Concurrent CSV uploads | 1. Upload 3 CSVs simultaneously from different tabs | All 3 processed successfully, separate batch IDs, no data corruption | Medium |
| E2E-042 | System recovery after restart | 1. Upload data 2. Restart backend 3. Check dashboard | Previous data still available, models re-loaded | High |

---

## 9. Performance & Load Tests

| ID | Scenario | Target | Priority |
|----|----------|--------|----------|
| PERF-001 | Single threat prediction latency | < 100ms (target: 5-10ms) | Critical |
| PERF-002 | Single attack classification latency | < 100ms (target: < 1ms) | Critical |
| PERF-003 | Batch 100 predictions | < 1 second (target: ~250ms) | High |
| PERF-004 | Batch 1000 predictions | < 5 seconds (target: ~2.5s) | High |
| PERF-005 | CSV upload 10 rows response time | < 1 second | High |
| PERF-006 | CSV upload 1000 rows response time | < 5 seconds | High |
| PERF-007 | Dashboard API response time | < 500ms | High |
| PERF-008 | Health check response time | < 200ms | Medium |
| PERF-009 | 50 concurrent CSV uploads | All succeed, no timeouts | Medium |
| PERF-010 | 100 concurrent WebSocket connections | All maintained, broadcasts succeed | Medium |
| PERF-011 | Predictions throughput (single-threaded) | 400-500 PPS | Medium |
| PERF-012 | Backend memory usage with models loaded | < 200 MB | Medium |
| PERF-013 | Backend CPU idle usage | < 5% | Low |
| PERF-014 | Frontend bundle size | < 500 KB (target: 212 KB) | Medium |
| PERF-015 | Frontend page load time | < 3 seconds | Medium |
| PERF-016 | Model loading time on startup | < 1 second per model | Medium |

---

## 10. Security Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| SEC-001 | SQL injection via CSV upload | Input sanitized, no SQL execution | Critical |
| SEC-002 | XSS via IP whitelist description | HTML escaped in frontend display | Critical |
| SEC-003 | Path traversal in model upload filename | Filename sanitized, no directory escape | Critical |
| SEC-004 | Oversized file upload (DoS prevention) | Rejected with 413 error if > 500MB | High |
| SEC-005 | Malicious .pkl model upload (pickle exploit) | Model validated before loading in production context | Critical |
| SEC-006 | CORS policy enforcement | Only allowed origins (localhost:3000) can access API | High |
| SEC-007 | Non-whitelisted IP data rejected | External Kafka messages from unknown IPs dropped | High |
| SEC-008 | API rate limiting (if implemented) | Excessive requests throttled | Medium |
| SEC-009 | Environment variables not exposed | No secrets in API responses or frontend bundle | High |
| SEC-010 | WebSocket origin validation | Only valid origins can connect | Medium |
| SEC-011 | CSV injection (formula injection) | CSV cells starting with `=`, `+`, `-`, `@` handled safely | Medium |
| SEC-012 | Integer overflow in feature values | Extremely large numeric values handled without crash | Medium |

---

## 11. Infrastructure Tests

| ID | Scenario | Expected Result | Priority |
|----|----------|-----------------|----------|
| INFRA-001 | PostgreSQL health check | Container healthy, `pg_isready` passes | Critical |
| INFRA-002 | Kafka broker health | Broker responding on port 9092/29092 | Critical |
| INFRA-003 | Zookeeper health | Responding on port 2181 | Critical |
| INFRA-004 | Docker Compose dev mode startup | All 3 infra services start and become healthy | Critical |
| INFRA-005 | Docker Compose full mode startup | All 5 services (infra + backend + frontend) start | High |
| INFRA-006 | Backend starts without Kafka | Backend starts with degraded mode (Kafka consumers disabled) | High |
| INFRA-007 | Database auto-migration on startup | `alembic upgrade head` runs automatically | High |
| INFRA-008 | Kafka topic auto-creation | `network-traffic` and `external-traffic` topics created | Medium |
| INFRA-009 | PostgreSQL data persistence | Data survives `docker-compose down` + `up` (volume) | High |
| INFRA-010 | Service restart recovery | Backend recovers after crash, models re-loaded | High |
| INFRA-011 | Network connectivity between services | Backend can reach Kafka and PostgreSQL | Critical |
| INFRA-012 | Frontend → Backend connectivity | Frontend can reach backend API on port 8000 | Critical |

---

## 12. Regression Tests

These tests cover previously identified and fixed bugs to prevent regression.

| ID | Bug Reference | Scenario | Expected Result | Priority |
|----|---------------|----------|-----------------|----------|
| REG-001 | BUG_FIX_ATTACK_CLASSIFICATION | Upload 42-feature CSV does not trigger threat detector | Attack classifier runs directly, no "Missing required features" error | Critical |
| REG-002 | BUG_FIX_ATTACK_CLASSIFICATION | `threat_prediction` is optional in response | Response with `threat_prediction: null` is valid JSON, no 422 error | Critical |
| REG-003 | END_TO_END_TEST_REPORT Bug #1 | Preprocessor features match trained model features | Feature list: `flag, src_bytes, dst_bytes, count, diff_srv_rate, dst_host_srv_count, dst_host_same_srv_rate, dst_host_diff_srv_rate, dst_host_same_src_port_rate, dst_host_srv_diff_host_rate` | Critical |
| REG-004 | END_TO_END_TEST_REPORT Bug #3 | Backend starts even when Kafka is unavailable | Backend HTTP server starts, Kafka consumers disabled gracefully | Critical |
| REG-005 | Frontend null-safety | CSVUploader handles null `threat_prediction` | No crash when attack classification response has null threat_prediction | High |
| REG-006 | Feature validation | `_validate_threat_detection_ranges()` only checks actual model features | No KeyError from checking removed features like `service` | High |
| REG-007 | Model loading singleton | Multiple calls to `get_ensemble_model()` return same instance | No memory leak from repeated model loading | Medium |
| REG-008 | Duplicate IP whitelist entry | Adding same IP twice returns error | 400 error: "IP already exists", no duplicate DB records | Medium |
| REG-009 | Active model deletion blocked | Attempting to delete an active model fails | 400 error: cannot delete active model | Medium |
| REG-010 | Config service idempotent init | Starting backend multiple times doesn't duplicate default configs | Always exactly 3 data source configs | Medium |

---

## Summary

| Category | Total Tests | Critical | High | Medium | Low |
|----------|-------------|----------|------|--------|-----|
| Unit Tests - Backend | 73 | 0 | 42 | 26 | 5 |
| Unit Tests - Frontend | 22 | 0 | 12 | 8 | 2 |
| Integration Tests | 15 | 2 | 10 | 3 | 0 |
| API Tests | 50 | 2 | 22 | 23 | 3 |
| ML Model Tests | 18 | 2 | 12 | 4 | 0 |
| Data Pipeline Tests | 18 | 2 | 11 | 5 | 0 |
| WebSocket Tests | 8 | 2 | 3 | 3 | 0 |
| E2E Tests | 42 | 4 | 22 | 14 | 2 |
| Performance Tests | 16 | 2 | 7 | 6 | 1 |
| Security Tests | 12 | 4 | 4 | 4 | 0 |
| Infrastructure Tests | 12 | 5 | 5 | 2 | 0 |
| Regression Tests | 10 | 4 | 3 | 3 | 0 |
| **TOTAL** | **296** | **29** | **153** | **101** | **13** |

---

## Implementation Priority

### Phase 1 - Critical Path (Must Have)
- All 29 Critical tests
- API-004, API-005 (CSV upload)
- E2E-001, E2E-002, E2E-003 (core upload flow)
- E2E-036, E2E-037 (full lifecycle)
- REG-001 through REG-004 (regression)

### Phase 2 - High Priority
- All High priority tests (153 tests)
- Focus on: ML model tests, integration tests, API tests

### Phase 3 - Medium Priority
- UI/UX tests, edge cases, configuration management
- Performance benchmarking
- Security hardening tests

### Phase 4 - Low Priority
- Responsive design tests
- Minor UI tests
- Edge case coverage
