# Kafka Consumer Troubleshooting Guide

## Issues Found and Fixed

### Issue 1: Empty Messages (JSON Parsing Error)
**Error**: `Expecting value: line 1 column 1 (char 0)`

**Root Cause**: The command was passing JSON as a shell argument instead of stdin:
```bash
# INCORRECT - JSON passed as argument
docker exec -i kafka kafka-console-producer --broker-list kafka:9092 --topic network-traffic '{"key":"value"}'
```

**Solution**: Pipe JSON to stdin:
```bash
# CORRECT - JSON piped to stdin
echo '{"key":"value"}' | docker exec -i kafka kafka-console-producer --broker-list kafka:9092 --topic network-traffic
```

### Issue 2: Multiline JSON Split into Separate Messages
**Error**: `Expecting property name enclosed in double quotes`, `Extra data: line 1 column X`

**Root Cause**: Multiline JSON was being sent as separate messages (one per line).

**Solution**: Format JSON as a single line before sending.

### Issue 3: Wrong Data Format (Feature Mismatch)
**Error**: `Cannot auto-detect model type. Threat detection match: 0/10, Attack classification match: 0/42`

**Root Cause**: The message format didn't match the expected feature names.

Your original message:
```json
{"timestamp":"2025-11-27T12:00:00Z","src":"10.0.1.10","dst":"93.184.216.34","bytes_sent":1452,"bytes_received":8901}
```

**Expected formats**:

#### Threat Detection (10 features required):
```json
{
  "service": 5,
  "flag": 2,
  "src_bytes": 1500,
  "dst_bytes": 2000,
  "count": 10,
  "same_srv_rate": 0.8,
  "diff_srv_rate": 0.1,
  "dst_host_srv_count": 50,
  "dst_host_same_srv_rate": 0.75,
  "dst_host_same_src_port_rate": 0.9
}
```

#### Attack Classification (42 features required):
```json
{
  " Destination Port": 80,
  " Flow Duration": 5000,
  " Total Fwd Packets": 50,
  "Total Length of Fwd Packets": 5000,
  " Fwd Packet Length Max": 1500,
  " Fwd Packet Length Min": 60,
  "Bwd Packet Length Max": 1500,
  " Bwd Packet Length Min": 60,
  "Flow Bytes/s": 1000,
  " Flow Packets/s": 10,
  " Flow IAT Mean": 100,
  " Flow IAT Std": 50,
  " Flow IAT Min": 10,
  "Bwd IAT Total": 500,
  " Bwd IAT Std": 25,
  "Fwd PSH Flags": 1,
  " Bwd PSH Flags": 1,
  " Fwd URG Flags": 0,
  " Bwd URG Flags": 0,
  " Fwd Header Length": 200,
  " Bwd Header Length": 200,
  " Bwd Packets/s": 5,
  " Min Packet Length": 60,
  "FIN Flag Count": 1,
  " RST Flag Count": 0,
  " PSH Flag Count": 2,
  " ACK Flag Count": 10,
  " URG Flag Count": 0,
  " Down/Up Ratio": 0.5,
  "Fwd Avg Bytes/Bulk": 500,
  " Fwd Avg Packets/Bulk": 5,
  " Fwd Avg Bulk Rate": 100,
  " Bwd Avg Bytes/Bulk": 500,
  " Bwd Avg Packets/Bulk": 5,
  "Bwd Avg Bulk Rate": 100,
  "Init_Win_bytes_forward": 8192,
  " Init_Win_bytes_backward": 8192,
  " min_seg_size_forward": 20,
  "Active Mean": 100,
  " Active Std": 50,
  " Active Max": 200,
  " Idle Std": 25
}
```

**Note**: Some feature names have leading spaces! This is important for proper matching.

## Improvements Made to Consumer Code

### Enhanced Error Handling
Added better debugging in `app/kafka/consumer.py` and `app/kafka/external_consumer.py`:

```python
# Get raw message value
raw_value = msg.value()

# Check if message is None or empty
if raw_value is None:
    logger.warning("Received None message value")
    return

if len(raw_value) == 0:
    logger.warning("Received empty message")
    return

# Decode message
decoded_msg = raw_value.decode("utf-8")
logger.debug(f"Raw decoded message: '{decoded_msg}' (length: {len(decoded_msg)})")

# Check if decoded message is empty or whitespace
if not decoded_msg or not decoded_msg.strip():
    logger.warning(f"Received empty or whitespace-only message: '{decoded_msg}'")
    return
```

This provides better visibility when debugging message issues.

## Testing

### Using the Test Script
A convenience script `test_kafka_send.sh` has been created:

```bash
# Send both message types
./test_kafka_send.sh

# Send only threat detection
./test_kafka_send.sh threat_detection

# Send only attack classification
./test_kafka_send.sh attack_classification
```

### Manual Testing
For threat detection:
```bash
echo '{"service": 5, "flag": 2, "src_bytes": 1500, "dst_bytes": 2000, "count": 10, "same_srv_rate": 0.8, "diff_srv_rate": 0.1, "dst_host_srv_count": 50, "dst_host_same_srv_rate": 0.75, "dst_host_same_src_port_rate": 0.9}' | docker exec -i threat-detection-kafka kafka-console-producer --broker-list kafka:9092 --topic network-traffic
```

### Verification
Check backend logs for successful processing:
```
2025-11-30 11:15:26,742 - app.kafka.consumer - INFO - Processed message: Traffic ID 703, Model: threat_detection, Attack: False
2025-11-30 11:15:38,937 - app.kafka.consumer - INFO - Processed message: Traffic ID 704, Model: attack_classification, Attack Type: BENIGN
```

## Feature Requirements

### Threat Detection Model
Requires exactly 10 features with at least 8 matches (80%):
- service (numeric)
- flag (numeric)
- src_bytes (non-negative)
- dst_bytes (non-negative)
- count (non-negative)
- same_srv_rate (0-1)
- diff_srv_rate (0-1)
- dst_host_srv_count (non-negative)
- dst_host_same_srv_rate (0-1)
- dst_host_same_src_port_rate (0-1)

### Attack Classification Model
Requires exactly 42 features with at least 35 matches (80%). See the full list in `app/services/preprocessor.py` at `ATTACK_CLASSIFICATION_FEATURES`.

## Quick Reference: Valid Commands

```bash
# Threat Detection Message
echo '{"service": 5, "flag": 2, "src_bytes": 1500, "dst_bytes": 2000, "count": 10, "same_srv_rate": 0.8, "diff_srv_rate": 0.1, "dst_host_srv_count": 50, "dst_host_same_srv_rate": 0.75, "dst_host_same_src_port_rate": 0.9}' | docker exec -i threat-detection-kafka kafka-console-producer --broker-list kafka:9092 --topic network-traffic

# View Messages from Beginning
docker exec threat-detection-kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic network-traffic --from-beginning

# View Latest Messages
docker exec threat-detection-kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic network-traffic

# Check Consumer Group Status
docker exec threat-detection-kafka kafka-consumer-groups --bootstrap-server kafka:9092 --group threat-detection-consumer --describe
```
