# Test Data Files

This directory contains sample CSV files for testing the AI Threat Detection System.

## Files

### 1. threat_detection_test.csv
- **Purpose**: Test threat detection functionality (binary classification)
- **Features**: 10 features required for ensemble model (ANN + LSTM)
- **Rows**: 10 sample network traffic records
- **Expected Result**: All records classified as normal traffic (no attacks)

**Required columns:**
- service
- flag
- src_bytes
- dst_bytes
- count
- same_srv_rate
- diff_srv_rate
- dst_host_srv_count
- dst_host_same_srv_rate
- dst_host_same_src_port_rate

### 2. attack_classification_test.csv
- **Purpose**: Test attack classification functionality (multi-class classification)
- **Features**: 42 features required for decision tree model
- **Rows**: 10 sample network traffic records
- **Expected Result**: Detailed attack type classification for detected threats

**Required columns:**
- Destination Port, Flow Duration, Total Fwd Packets, Total Length of Fwd Packets
- Fwd Packet Length Max, Fwd Packet Length Min, Bwd Packet Length Max, Bwd Packet Length Min
- Flow Bytes/s, Flow Packets/s, Flow IAT Mean, Flow IAT Std, Flow IAT Min
- Bwd IAT Total, Bwd IAT Std, Fwd PSH Flags, Bwd PSH Flags, Fwd URG Flags, Bwd URG Flags
- Fwd Header Length, Bwd Header Length, Bwd Packets/s, Min Packet Length
- FIN Flag Count, RST Flag Count, PSH Flag Count, ACK Flag Count, URG Flag Count
- Down/Up Ratio, Fwd Avg Bytes/Bulk, Fwd Avg Packets/Bulk, Fwd Avg Bulk Rate
- Bwd Avg Bytes/Bulk, Bwd Avg Packets/Bulk, Bwd Avg Bulk Rate
- Init_Win_bytes_forward, Init_Win_bytes_backward, min_seg_size_forward
- Active Mean, Active Std, Active Max, Idle Std

## How to Use

### Using the Web Interface

1. Start the backend server (port 8000)
2. Start the frontend server:
   ```bash
   npm run dev
   ```
3. Open http://localhost:3000 in your browser
4. Navigate to the Upload page
5. Upload one of the CSV files
6. Click "Upload and Analyze"
7. View results on the Dashboard

### Using the API Directly

**Threat Detection:**
```bash
curl -X POST http://localhost:8000/api/v1/upload/csv \
  -F "file=@test_data/threat_detection_test.csv" \
  -H "accept: application/json"
```

**Attack Classification:**
```bash
curl -X POST http://localhost:8000/api/v1/upload/csv \
  -F "file=@test_data/attack_classification_test.csv" \
  -H "accept: application/json"
```

## Creating Your Own Test Files

### Threat Detection CSV
The system requires exactly 10 features with numeric values:
- Rate features (same_srv_rate, diff_srv_rate, etc.) must be between 0 and 1
- Byte and count features must be non-negative

### Attack Classification CSV
The system requires exactly 42 features with numeric values:
- Destination Port must be between 0 and 65535
- Most features should be non-negative (except ratios)
- Infinite values will be converted to 0

## Notes

- The system auto-detects which model to use based on the number of matching features
- CSV files must have headers that match the required feature names
- Feature names are case-sensitive and include leading/trailing spaces as shown above
- The backend validates all features before processing
