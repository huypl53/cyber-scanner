"""
Integration tests for real ML models.
Tests model loading, predictions, and performance.
"""
import pytest
import numpy as np
import time
from pathlib import Path

from app.models.model_loaders import (
    get_threat_pipeline,
    get_attack_pipeline,
    reload_models,
    predict_threat,
    predict_attack_type,
    get_model_version,
    THREAT_DETECTION_FEATURES,
    ATTACK_CLASSIFICATION_FEATURES
)


class TestThreatDetectionModel:
    """Test suite for threat detection model."""

    def test_model_loads(self):
        """Test that threat detection pipeline loads successfully."""
        pipeline = get_threat_pipeline()
        assert pipeline is not None
        assert pipeline.model_ann is not None
        assert pipeline.model_lstm is not None
        assert pipeline.artifacts is not None

    def test_model_version(self):
        """Test that model has version information."""
        version = get_model_version("threat")
        assert version is not None
        assert isinstance(version, str)
        print(f"Model version: {version}")

    def test_prediction_normal_traffic(self):
        """Test prediction on normal traffic features."""
        # Normal traffic pattern
        features = {
            'flag': 2,
            'src_bytes': 1500,
            'dst_bytes': 2000,
            'count': 10,
            'diff_srv_rate': 0.1,
            'dst_host_srv_count': 50,
            'dst_host_same_srv_rate': 0.75,
            'dst_host_diff_srv_rate': 0.1,
            'dst_host_same_src_port_rate': 0.9,
            'dst_host_srv_diff_host_rate': 0.1
        }

        score, is_attack = predict_threat(features)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert isinstance(is_attack, bool)
        print(f"Normal traffic - Score: {score:.4f}, Attack: {is_attack}")

    def test_prediction_attack_traffic(self):
        """Test prediction on suspicious traffic features."""
        # Suspicious traffic pattern
        features = {
            'flag': 4,
            'src_bytes': 50000,
            'dst_bytes': 10000,
            'count': 500,
            'diff_srv_rate': 0.8,
            'dst_host_srv_count': 255,
            'dst_host_same_srv_rate': 0.2,
            'dst_host_diff_srv_rate': 0.8,
            'dst_host_same_src_port_rate': 0.1,
            'dst_host_srv_diff_host_rate': 0.8
        }

        score, is_attack = predict_threat(features)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert isinstance(is_attack, bool)
        print(f"Attack traffic - Score: {score:.4f}, Attack: {is_attack}")

    def test_missing_features(self):
        """Test that missing features raise appropriate error."""
        # Missing required features
        features = {'flag': 2}

        with pytest.raises(ValueError, match="Missing required features"):
            predict_threat(features)

    def test_feature_validation(self):
        """Test feature validation logic."""
        # All features present
        features = {f: 0.5 for f in THREAT_DETECTION_FEATURES}
        score, is_attack = predict_threat(features)

        assert isinstance(score, float)
        assert isinstance(is_attack, bool)

    def test_prediction_latency(self):
        """Test prediction latency is within acceptable range."""
        features = {
            'flag': 2,
            'src_bytes': 1500,
            'dst_bytes': 2000,
            'count': 10,
            'diff_srv_rate': 0.1,
            'dst_host_srv_count': 50,
            'dst_host_same_srv_rate': 0.75,
            'dst_host_diff_srv_rate': 0.1,
            'dst_host_same_src_port_rate': 0.9,
            'dst_host_srv_diff_host_rate': 0.1
        }

        # Warm-up
        predict_threat(features)

        # Measure latency over 100 predictions
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            predict_threat(features)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)

        print(f"\nThreat Detection Latency:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  Min: {min(latencies):.2f}ms")
        print(f"  Max: {max(latencies):.2f}ms")

        # Should be under 100ms for p95
        assert p95_latency < 100, f"P95 latency {p95_latency:.2f}ms exceeds 100ms target"


class TestAttackClassificationModel:
    """Test suite for attack classification model."""

    def test_model_loads(self):
        """Test that attack classification pipeline loads successfully."""
        pipeline = get_attack_pipeline()
        assert pipeline is not None
        assert pipeline.model is not None
        assert pipeline.artifacts is not None

    def test_model_version(self):
        """Test that model has version information."""
        version = get_model_version("attack")
        assert version is not None
        assert isinstance(version, str)
        print(f"Model version: {version}")

    def test_prediction_benign_traffic(self):
        """Test prediction on benign traffic."""
        # Benign traffic pattern
        features = {
            ' Destination Port': 80,
            ' Flow Duration': 5000,
            ' Total Fwd Packets': 50,
            'Total Length of Fwd Packets': 5000,
            ' Fwd Packet Length Max': 1500,
            ' Fwd Packet Length Min': 60,
            'Bwd Packet Length Max': 1500,
            ' Bwd Packet Length Min': 60,
            'Flow Bytes/s': 1000,
            ' Flow Packets/s': 10,
            ' Flow IAT Mean': 100,
            ' Flow IAT Std': 50,
            ' Flow IAT Min': 10,
            'Bwd IAT Total': 500,
            ' Bwd IAT Std': 25,
            'Fwd PSH Flags': 1,
            ' Bwd PSH Flags': 1,
            ' Fwd URG Flags': 0,
            ' Bwd URG Flags': 0,
            ' Fwd Header Length': 200,
            ' Bwd Header Length': 200,
            ' Bwd Packets/s': 5,
            ' Min Packet Length': 60,
            'FIN Flag Count': 1,
            ' RST Flag Count': 0,
            ' PSH Flag Count': 2,
            ' ACK Flag Count': 10,
            ' URG Flag Count': 0,
            ' Down/Up Ratio': 0.5,
            'Fwd Avg Bytes/Bulk': 500,
            ' Fwd Avg Packets/Bulk': 5,
            ' Fwd Avg Bulk Rate': 100,
            ' Bwd Avg Bytes/Bulk': 500,
            ' Bwd Avg Packets/Bulk': 5,
            'Bwd Avg Bulk Rate': 100,
            'Init_Win_bytes_forward': 8192,
            ' Init_Win_bytes_backward': 8192,
            ' min_seg_size_forward': 20,
            'Active Mean': 100,
            ' Active Std': 50,
            ' Active Max': 200,
            ' Idle Std': 25
        }

        attack_type, attack_name, confidence = predict_attack_type(features)

        assert isinstance(attack_type, int)
        assert 0 <= attack_type <= 13
        assert isinstance(attack_name, str)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        print(f"Benign traffic - Type: {attack_type}, Name: {attack_name}, Confidence: {confidence:.4f}")

    def test_prediction_ddos_pattern(self):
        """Test prediction on DDoS-like pattern."""
        # DDoS pattern (high packet rate)
        features = {
            ' Destination Port': 80,
            ' Flow Duration': 1000,
            ' Total Fwd Packets': 5000,
            'Total Length of Fwd Packets': 500000,
            ' Fwd Packet Length Max': 1500,
            ' Fwd Packet Length Min': 60,
            'Bwd Packet Length Max': 100,
            ' Bwd Packet Length Min': 40,
            'Flow Bytes/s': 500000,
            ' Flow Packets/s': 5000,
            ' Flow IAT Mean': 1,
            ' Flow IAT Std': 0.5,
            ' Flow IAT Min': 0.1,
            'Bwd IAT Total': 100,
            ' Bwd IAT Std': 10,
            'Fwd PSH Flags': 0,
            ' Bwd PSH Flags': 0,
            ' Fwd URG Flags': 0,
            ' Bwd URG Flags': 0,
            ' Fwd Header Length': 100000,
            ' Bwd Header Length': 2000,
            ' Bwd Packets/s': 100,
            ' Min Packet Length': 40,
            'FIN Flag Count': 0,
            ' RST Flag Count': 0,
            ' PSH Flag Count': 0,
            ' ACK Flag Count': 1000,
            ' URG Flag Count': 0,
            ' Down/Up Ratio': 0.02,
            'Fwd Avg Bytes/Bulk': 1000,
            ' Fwd Avg Packets/Bulk': 10,
            ' Fwd Avg Bulk Rate': 5000,
            ' Bwd Avg Bytes/Bulk': 100,
            ' Bwd Avg Packets/Bulk': 1,
            'Bwd Avg Bulk Rate': 100,
            'Init_Win_bytes_forward': 8192,
            ' Init_Win_bytes_backward': 8192,
            ' min_seg_size_forward': 20,
            'Active Mean': 10,
            ' Active Std': 5,
            ' Active Max': 20,
            ' Idle Std': 1
        }

        attack_type, attack_name, confidence = predict_attack_type(features)

        assert isinstance(attack_type, int)
        assert isinstance(attack_name, str)
        assert isinstance(confidence, float)
        print(f"DDoS pattern - Type: {attack_type}, Name: {attack_name}, Confidence: {confidence:.4f}")

    def test_missing_features(self):
        """Test that missing features raise appropriate error."""
        # Missing required features
        features = {' Destination Port': 80}

        with pytest.raises(ValueError, match="Missing required features"):
            predict_attack_type(features)

    def test_all_attack_types(self):
        """Test that model can predict various attack types."""
        # Generate random features
        np.random.seed(42)
        predictions = set()

        for _ in range(100):
            features = {
                ' Destination Port': np.random.randint(1, 65536),
                ' Flow Duration': np.random.randint(1, 10000),
                ' Total Fwd Packets': np.random.randint(1, 1000),
                'Total Length of Fwd Packets': np.random.randint(100, 100000),
                ' Fwd Packet Length Max': np.random.randint(60, 1500),
                ' Fwd Packet Length Min': 60,
                'Bwd Packet Length Max': np.random.randint(60, 1500),
                ' Bwd Packet Length Min': 60,
                'Flow Bytes/s': np.random.rand() * 100000,
                ' Flow Packets/s': np.random.rand() * 1000,
                ' Flow IAT Mean': np.random.rand() * 1000,
                ' Flow IAT Std': np.random.rand() * 500,
                ' Flow IAT Min': np.random.rand() * 100,
                'Bwd IAT Total': np.random.rand() * 5000,
                ' Bwd IAT Std': np.random.rand() * 100,
                'Fwd PSH Flags': np.random.randint(0, 10),
                ' Bwd PSH Flags': np.random.randint(0, 10),
                ' Fwd URG Flags': np.random.randint(0, 2),
                ' Bwd URG Flags': np.random.randint(0, 2),
                ' Fwd Header Length': np.random.randint(100, 10000),
                ' Bwd Header Length': np.random.randint(100, 10000),
                ' Bwd Packets/s': np.random.rand() * 500,
                ' Min Packet Length': 60,
                'FIN Flag Count': np.random.randint(0, 10),
                ' RST Flag Count': np.random.randint(0, 10),
                ' PSH Flag Count': np.random.randint(0, 20),
                ' ACK Flag Count': np.random.randint(0, 50),
                ' URG Flag Count': np.random.randint(0, 2),
                ' Down/Up Ratio': np.random.rand(),
                'Fwd Avg Bytes/Bulk': np.random.rand() * 1000,
                ' Fwd Avg Packets/Bulk': np.random.rand() * 10,
                ' Fwd Avg Bulk Rate': np.random.rand() * 1000,
                ' Bwd Avg Bytes/Bulk': np.random.rand() * 1000,
                ' Bwd Avg Packets/Bulk': np.random.rand() * 10,
                'Bwd Avg Bulk Rate': np.random.rand() * 1000,
                'Init_Win_bytes_forward': 8192,
                ' Init_Win_bytes_backward': 8192,
                ' min_seg_size_forward': 20,
                'Active Mean': np.random.rand() * 1000,
                ' Active Std': np.random.rand() * 500,
                ' Active Max': np.random.rand() * 2000,
                ' Idle Std': np.random.rand() * 500
            }

            attack_type, attack_name, confidence = predict_attack_type(features)
            predictions.add(attack_name)

        print(f"\nUnique attack types predicted: {len(predictions)}")
        print(f"Attack types: {sorted(predictions)}")

        # Should predict at least a few different types
        assert len(predictions) >= 2

    def test_prediction_latency(self):
        """Test prediction latency is within acceptable range."""
        features = {
            ' Destination Port': 80,
            ' Flow Duration': 5000,
            ' Total Fwd Packets': 50,
            'Total Length of Fwd Packets': 5000,
            ' Fwd Packet Length Max': 1500,
            ' Fwd Packet Length Min': 60,
            'Bwd Packet Length Max': 1500,
            ' Bwd Packet Length Min': 60,
            'Flow Bytes/s': 1000,
            ' Flow Packets/s': 10,
            ' Flow IAT Mean': 100,
            ' Flow IAT Std': 50,
            ' Flow IAT Min': 10,
            'Bwd IAT Total': 500,
            ' Bwd IAT Std': 25,
            'Fwd PSH Flags': 1,
            ' Bwd PSH Flags': 1,
            ' Fwd URG Flags': 0,
            ' Bwd URG Flags': 0,
            ' Fwd Header Length': 200,
            ' Bwd Header Length': 200,
            ' Bwd Packets/s': 5,
            ' Min Packet Length': 60,
            'FIN Flag Count': 1,
            ' RST Flag Count': 0,
            ' PSH Flag Count': 2,
            ' ACK Flag Count': 10,
            ' URG Flag Count': 0,
            ' Down/Up Ratio': 0.5,
            'Fwd Avg Bytes/Bulk': 500,
            ' Fwd Avg Packets/Bulk': 5,
            ' Fwd Avg Bulk Rate': 100,
            ' Bwd Avg Bytes/Bulk': 500,
            ' Bwd Avg Packets/Bulk': 5,
            'Bwd Avg Bulk Rate': 100,
            'Init_Win_bytes_forward': 8192,
            ' Init_Win_bytes_backward': 8192,
            ' min_seg_size_forward': 20,
            'Active Mean': 100,
            ' Active Std': 50,
            ' Active Max': 200,
            ' Idle Std': 25
        }

        # Warm-up
        predict_attack_type(features)

        # Measure latency over 100 predictions
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            predict_attack_type(features)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)

        print(f"\nAttack Classification Latency:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  Min: {min(latencies):.2f}ms")
        print(f"  Max: {max(latencies):.2f}ms")

        # Should be under 100ms for p95
        assert p95_latency < 100, f"P95 latency {p95_latency:.2f}ms exceeds 100ms target"


class TestModelManagement:
    """Test suite for model management functions."""

    def test_model_reload(self):
        """Test that models can be reloaded."""
        # Get initial pipelines
        pipeline1 = get_threat_pipeline()
        pipeline2 = get_attack_pipeline()

        # Reload models
        reload_models()

        # Get new instances
        pipeline3 = get_threat_pipeline()
        pipeline4 = get_attack_pipeline()

        # Should be new instances
        assert pipeline3 is not pipeline1
        assert pipeline4 is not pipeline2

    def test_singleton_pattern(self):
        """Test that models use singleton pattern."""
        pipeline1 = get_threat_pipeline()
        pipeline2 = get_threat_pipeline()

        assert pipeline1 is pipeline2

        tree1 = get_attack_pipeline()
        tree2 = get_attack_pipeline()

        assert tree1 is tree2


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
