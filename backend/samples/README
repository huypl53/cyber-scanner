# CSV Upload Samples

This directory contains sample CSV files for testing the AI Network Security Threat Detection System.

## Available Sample Files

### 1. `threat_detection_sample.csv`
- **Purpose**: Binary threat detection (malicious vs. benign)
- **Features**: 10 network traffic features
- **Output**: Threat score (0-1) and binary classification

### 2. `attack_classification_sample.csv`
- **Purpose**: Multi-class attack type classification
- **Features**: 42 network traffic features
- **Output**: Attack type (one of 14 categories) with confidence score

## File Format Requirements

### Threat Detection (10 Features)

Your CSV must contain these exact column headers:

```csv
protocol_type,service,flag,src_bytes,dst_bytes,count,same_srv_rate,diff_srv_rate,dst_host_srv_count,dst_host_same_srv_rate
```

**Column Descriptions:**
- `protocol_type`: Protocol type (encoded: tcp=1, udp=2, icmp=0)
- `service`: Service type (encoded numerically: e.g., ftp=5, http=20, smtp=15)
- `flag`: TCP flag (encoded numerically: 0-3)
- `src_bytes`: Source to destination bytes
- `dst_bytes`: Destination to source bytes
- `count`: Number of connections to same host
- `same_srv_rate`: Percentage of connections using same service
- `diff_srv_rate`: Percentage of connections to different services
- `dst_host_srv_count`: Number of connections to same destination host
- `dst_host_same_srv_rate`: Percentage of connections using same service on destination host

**Example:**
```csv
protocol_type,service,flag,src_bytes,dst_bytes,count,same_srv_rate,diff_srv_rate,dst_host_srv_count,dst_host_same_srv_rate
1,ftp,2,1500,2000,10,0.8,0.1,50,0.75
```

### Attack Classification (42 Features)

Your CSV must contain these exact column headers:

```csv
 Destination Port, Flow Duration, Total Fwd Packets,Total Length of Fwd Packets, Fwd Packet Length Max, Fwd Packet Length Min,Bwd Packet Length Max, Bwd Packet Length Min,Flow Bytes/s, Flow Packets/s, Flow IAT Mean, Flow IAT Std, Flow IAT Min,Bwd IAT Total, Bwd IAT Std,Fwd PSH Flags, Bwd PSH Flags, Fwd URG Flags, Bwd URG Flags, Fwd Header Length, Bwd Header Length, Bwd Packets/s, Min Packet Length,FIN Flag Count, RST Flag Count, PSH Flag Count, ACK Flag Count, URG Flag Count, Down/Up Ratio,Fwd Avg Bytes/Bulk, Fwd Avg Packets/Bulk, Fwd Avg Bulk Rate, Bwd Avg Bytes/Bulk, Bwd Avg Packets/Bulk,Bwd Avg Bulk Rate,Init_Win_bytes_forward, Init_Win_bytes_backward, min_seg_size_forward,Active Mean, Active Std, Active Max, Idle Std
```

**Important Notes:**
- Some headers have **leading spaces** (e.g., `' Destination Port'`, `' Flow Duration'`)
- Preserve the exact casing and spacing as shown above
- Total of 42 columns required

**Example (first 5 columns):**
```csv
 Destination Port, Flow Duration, Total Fwd Packets,Total Length of Fwd Packets, Fwd Packet Length Max,...
80,5000,50,5000,1500,...
```

## Header Variations Supported

The system includes flexible header mapping to handle common variations:

### Common Variations Supported
- `Destination Port` → `' Destination Port'`
- `destination_port` → `' Destination Port'`
- `flow_duration` → `' Flow Duration'`
- `total_fwd_packets` → `' Total Fwd Packets'`

### Normalization Rules
1. Case-insensitive matching
2. Underscores (`_`) are treated as spaces
3. Leading/trailing whitespace is ignored
4. Common abbreviations are mapped (e.g., `dest_port` → `' Destination Port'`)

## How to Use

### Option 1: Web Interface
1. Navigate to the upload page in the web application
2. Click "Choose File" and select your CSV
3. Click "Upload"
4. View prediction results in the dashboard

### Option 2: API Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/upload/csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/file.csv"
```

### Option 3: Download Samples
The sample files can be downloaded via the API:
```bash
# Threat detection sample
curl -O http://localhost:8000/api/v1/samples/threat_detection_sample.csv

# Attack classification sample
curl -O http://localhost:8000/api/v1/samples/attack_classification_sample.csv
```

## Validation and Error Messages

If your CSV upload fails, the error response will include:

1. **Detected Model Type**: Whether the system thinks you're uploading for threat detection or attack classification
2. **Headers Found**: List of column headers detected in your CSV
3. **Missing Features**: Which required features are not present
4. **Example Headers**: Correct format for reference
5. **Help Links**: Where to get sample files

### Example Error Response
```json
{
  "error": "CSV validation failed",
  "csv_headers_found": ["destination_port", "flow_duration", ...],
  "detected_model_type": "attack_classification",
  "missing_features": [" Fwd URG Flags", " Bwd URG Flags"],
  "sample_formats": {
    "threat_detection": { "example_header": "flag,src_bytes,..." },
    "attack_classification": { "example_header": " Destination Port, Flow Duration,..." }
  }
}
```

## Attack Types (Classification Model)

When using the 42-feature format, the system classifies traffic into one of these categories:

| Type | Name | Description |
|------|------|-------------|
| 0 | Benign | Normal traffic |
| 1 | Bot | Botnet traffic |
| 2 | DDoS | Distributed Denial of Service |
| 3 | DoS GoldenEye | GoldenEye attack |
| 4 | DoS Hulk | Hulk attack |
| 5 | DoS HTTP | HTTP flood attack |
| 6 | DoS SlowHTTP | Slow HTTP attack |
| 7 | FTP BruteForce | FTP brute force attack |
| 8 | Infiltration | Network infiltration |
| 9 | Port Scan | Port scanning activity |
| 10 | SQL Injection | SQL injection attack |
| 11 | XSS | Cross-site scripting attack |
| 12 | Password BruteForce | Password brute force attack |
| 13 | Heartbleed | Heartbleed exploit |

## Troubleshooting

### Issue: "CSV validation error: Missing required features"
**Solution**: Check that your CSV has all required columns. Use the sample files as a template.

### Issue: Headers don't match exactly
**Solution**: The system supports common variations. Check the error response for which features are missing.

### Issue: Leading spaces in attack classification headers
**Solution**: Some headers like `' Destination Port'` have leading spaces. Copy the header row from the sample file.

### Issue: Empty rows or invalid data
**Solution**: Ensure all rows have valid numeric values. Remove or fill missing data before uploading.

## Technical Details

### Auto-Detection Logic
- **Threat Detection**: Requires at least 8/10 features (80% match)
- **Attack Classification**: Requires at least 35/42 features (80% match)

### Processing Pipeline
1. CSV file is uploaded and parsed
2. Headers are normalized and validated
3. Model type is auto-detected based on feature count
4. Appropriate ML pipeline runs predictions
5. Results are stored in database and returned to client

### Response Format
Both model types return:
- `traffic_data`: Original input features
- `threat_prediction` OR `attack_prediction`: Model prediction
- `self_healing_action`: Recommended mitigation action (for attack classification)

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Backend README**: `../README.md`
- **Codebase Overview**: `../../CODEBASE_OVERVIEW.md`
