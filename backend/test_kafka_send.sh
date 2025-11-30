#!/bin/bash

# Test script to send valid Kafka messages for threat detection and attack classification
# Usage: ./test_kafka_send.sh [threat_detection|attack_classification|both]

KAFKA_CONTAINER="threat-detection-kafka"
KAFKA_BROKER="kafka:9092"
TOPIC="network-traffic"

send_threat_detection_message() {
    echo "Sending THREAT DETECTION message..."
    echo '{"service": 5, "flag": 2, "src_bytes": 1500, "dst_bytes": 2000, "count": 10, "same_srv_rate": 0.8, "diff_srv_rate": 0.1, "dst_host_srv_count": 50, "dst_host_same_srv_rate": 0.75, "dst_host_same_src_port_rate": 0.9}' | docker exec -i "$KAFKA_CONTAINER" kafka-console-producer --broker-list "$KAFKA_BROKER" --topic "$TOPIC"

    if [ $? -eq 0 ]; then
        echo "✓ Threat detection message sent successfully"
    else
        echo "✗ Failed to send threat detection message"
    fi
}

send_attack_classification_message() {
    echo "Sending ATTACK CLASSIFICATION message..."
    echo '{" Destination Port": 80, " Flow Duration": 5000, " Total Fwd Packets": 50, "Total Length of Fwd Packets": 5000, " Fwd Packet Length Max": 1500, " Fwd Packet Length Min": 60, "Bwd Packet Length Max": 1500, " Bwd Packet Length Min": 60, "Flow Bytes/s": 1000, " Flow Packets/s": 10, " Flow IAT Mean": 100, " Flow IAT Std": 50, " Flow IAT Min": 10, "Bwd IAT Total": 500, " Bwd IAT Std": 25, "Fwd PSH Flags": 1, " Bwd PSH Flags": 1, " Fwd URG Flags": 0, " Bwd URG Flags": 0, " Fwd Header Length": 200, " Bwd Header Length": 200, " Bwd Packets/s": 5, " Min Packet Length": 60, "FIN Flag Count": 1, " RST Flag Count": 0, " PSH Flag Count": 2, " ACK Flag Count": 10, " URG Flag Count": 0, " Down/Up Ratio": 0.5, "Fwd Avg Bytes/Bulk": 500, " Fwd Avg Packets/Bulk": 5, " Fwd Avg Bulk Rate": 100, " Bwd Avg Bytes/Bulk": 500, " Bwd Avg Packets/Bulk": 5, "Bwd Avg Bulk Rate": 100, "Init_Win_bytes_forward": 8192, " Init_Win_bytes_backward": 8192, " min_seg_size_forward": 20, "Active Mean": 100, " Active Std": 50, " Active Max": 200, " Idle Std": 25}' | docker exec -i "$KAFKA_CONTAINER" kafka-console-producer --broker-list "$KAFKA_BROKER" --topic "$TOPIC"

    if [ $? -eq 0 ]; then
        echo "✓ Attack classification message sent successfully"
    else
        echo "✗ Failed to send attack classification message"
    fi
}

# Main script
case "${1:-both}" in
    threat_detection)
        send_threat_detection_message
        ;;
    attack_classification)
        send_attack_classification_message
        ;;
    both)
        send_threat_detection_message
        echo ""
        send_attack_classification_message
        ;;
    *)
        echo "Usage: $0 [threat_detection|attack_classification|both]"
        echo ""
        echo "Examples:"
        echo "  $0                          # Send both types"
        echo "  $0 threat_detection         # Send only threat detection"
        echo "  $0 attack_classification    # Send only attack classification"
        exit 1
        ;;
esac

echo ""
echo "Check the backend logs to see the processing results"
