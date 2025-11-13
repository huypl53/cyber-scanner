"""Tests for ML models"""
import pytest
from app.models.ml_models import EnsembleModel, DecisionTreeModel


class TestEnsembleModel:
    """Test Ensemble threat detection model"""

    def test_predict_normal_traffic(self):
        """Test prediction for normal traffic"""
        model = EnsembleModel()
        features = {
            'service': 5,
            'flag': 2,
            'src_bytes': 100,
            'dst_bytes': 200,
            'count': 5,
            'same_srv_rate': 0.8,
            'diff_srv_rate': 0.1,
            'dst_host_srv_count': 50,
            'dst_host_same_srv_rate': 0.75,
            'dst_host_same_src_port_rate': 0.9
        }

        score, is_attack = model.predict(features)

        assert 0 <= score <= 1
        assert isinstance(is_attack, bool)

    def test_predict_missing_features(self):
        """Test that missing features raise error"""
        model = EnsembleModel()
        features = {'service': 5}  # Missing most features

        with pytest.raises(ValueError):
            model.predict(features)


class TestDecisionTreeModel:
    """Test Decision Tree attack classification model"""

    def test_predict_attack_classification(self):
        """Test attack classification"""
        model = DecisionTreeModel()
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

        attack_type_encoded, attack_type_name, confidence = model.predict(features)

        assert 0 <= attack_type_encoded <= 13
        assert attack_type_name in model.ATTACK_TYPES.values()
        assert 0 <= confidence <= 1
