"""Tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root(self):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "version" in data


class TestPredictionsEndpoint:
    """Test predictions endpoints"""

    def test_get_prediction_stats(self):
        """Test getting prediction statistics"""
        response = client.get("/api/v1/predictions/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_predictions" in data
        assert "total_attacks" in data
        assert "attack_rate" in data
