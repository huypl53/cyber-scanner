"""
Health check endpoints for monitoring system status.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.services.threat_detector import ThreatDetectorService
from app.services.attack_classifier import AttackClassifierService
from app.services.websocket_manager import get_connection_manager
from app.kafka.consumer import get_consumer_service
from app.kafka.external_consumer import get_external_consumer_service
from confluent_kafka.admin import AdminClient
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def basic_health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/api/v1/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check that verifies all system components.

    Returns:
        dict: Health status of all components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": {"status": "unknown"},
            "kafka": {"status": "unknown"},
            "consumers": {
                "internal": {"status": "unknown"},
                "external": {"status": "unknown"}
            },
            "models": {
                "threat_detector": {"loaded": False, "version": None, "is_real": False},
                "attack_classifier": {"loaded": False, "version": None, "is_real": False}
            },
            "websocket": {"status": "unknown", "connections": 0}
        }
    }

    overall_healthy = True

    # 1. Check Database
    try:
        start = time.time()
        # Simple query to test DB connectivity
        db.execute("SELECT 1")
        latency_ms = round((time.time() - start) * 1000, 2)
        health_status["checks"]["database"] = {
            "status": "ok",
            "latency_ms": latency_ms
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "error",
            "error": str(e)
        }
        overall_healthy = False

    # 2. Check Kafka Broker
    try:
        admin_client = AdminClient({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS
        })
        # Get cluster metadata (this will fail if Kafka is unreachable)
        metadata = admin_client.list_topics(timeout=5)
        broker_count = len(metadata.brokers)
        topics = list(metadata.topics.keys())

        health_status["checks"]["kafka"] = {
            "status": "ok",
            "broker_count": broker_count,
            "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "topics": topics
        }
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        health_status["checks"]["kafka"] = {
            "status": "error",
            "error": str(e),
            "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS
        }
        overall_healthy = False

    # 3. Check Internal Kafka Consumer
    try:
        internal_consumer = get_consumer_service()
        if internal_consumer.running and internal_consumer.consumer:
            health_status["checks"]["consumers"]["internal"] = {
                "status": "ok",
                "running": True,
                "topic": settings.KAFKA_TOPIC_REALTIME_DATA
            }
        else:
            health_status["checks"]["consumers"]["internal"] = {
                "status": "degraded",
                "running": False,
                "message": "Consumer not connected (will retry)",
                "topic": settings.KAFKA_TOPIC_REALTIME_DATA
            }
    except Exception as e:
        logger.error(f"Internal consumer health check failed: {e}")
        health_status["checks"]["consumers"]["internal"] = {
            "status": "error",
            "error": str(e)
        }

    # 4. Check External Kafka Consumer
    try:
        external_consumer = get_external_consumer_service()
        is_enabled = external_consumer.is_enabled()

        if not is_enabled:
            health_status["checks"]["consumers"]["external"] = {
                "status": "disabled",
                "running": False,
                "topic": settings.KAFKA_TOPIC_EXTERNAL_DATA
            }
        elif external_consumer.running and external_consumer.consumer:
            health_status["checks"]["consumers"]["external"] = {
                "status": "ok",
                "running": True,
                "enabled": True,
                "topic": settings.KAFKA_TOPIC_EXTERNAL_DATA
            }
        else:
            health_status["checks"]["consumers"]["external"] = {
                "status": "degraded",
                "running": False,
                "enabled": True,
                "message": "Consumer not connected (will retry)",
                "topic": settings.KAFKA_TOPIC_EXTERNAL_DATA
            }
    except Exception as e:
        logger.error(f"External consumer health check failed: {e}")
        health_status["checks"]["consumers"]["external"] = {
            "status": "error",
            "error": str(e)
        }

    # 5. Check ML Models
    try:
        # Threat Detector
        threat_detector = ThreatDetectorService()
        if threat_detector.model:
            # Check if it's a real model by looking for version attribute
            is_real = hasattr(threat_detector.model, 'version')
            version = getattr(threat_detector.model, 'version', 'unknown')

            health_status["checks"]["models"]["threat_detector"] = {
                "loaded": True,
                "version": version,
                "is_real": is_real,
                "model_type": type(threat_detector.model).__name__
            }
        else:
            health_status["checks"]["models"]["threat_detector"] = {
                "loaded": False,
                "error": "Model not loaded"
            }
            overall_healthy = False
    except Exception as e:
        logger.error(f"Threat detector health check failed: {e}")
        health_status["checks"]["models"]["threat_detector"] = {
            "loaded": False,
            "error": str(e)
        }
        overall_healthy = False

    try:
        # Attack Classifier
        attack_classifier = AttackClassifierService()
        if attack_classifier.model:
            # Check if it's a real model by looking for version attribute
            is_real = hasattr(attack_classifier.model, 'version')
            version = getattr(attack_classifier.model, 'version', 'unknown')

            health_status["checks"]["models"]["attack_classifier"] = {
                "loaded": True,
                "version": version,
                "is_real": is_real,
                "model_type": type(attack_classifier.model).__name__
            }
        else:
            health_status["checks"]["models"]["attack_classifier"] = {
                "loaded": False,
                "error": "Model not loaded"
            }
            overall_healthy = False
    except Exception as e:
        logger.error(f"Attack classifier health check failed: {e}")
        health_status["checks"]["models"]["attack_classifier"] = {
            "loaded": False,
            "error": str(e)
        }
        overall_healthy = False

    # 6. Check WebSocket Manager
    try:
        ws_manager = get_connection_manager()
        connection_count = len(ws_manager.active_connections)
        health_status["checks"]["websocket"] = {
            "status": "ok",
            "connections": connection_count
        }
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        health_status["checks"]["websocket"] = {
            "status": "error",
            "error": str(e),
            "connections": 0
        }

    # Determine overall status
    if not overall_healthy:
        health_status["status"] = "unhealthy"
    elif (health_status["checks"]["kafka"]["status"] != "ok" or
          health_status["checks"]["consumers"]["internal"]["status"] not in ["ok", "disabled"]):
        health_status["status"] = "degraded"

    return health_status
