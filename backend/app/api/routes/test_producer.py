"""
Test Producer API endpoints.
Allows triggering test data streams for development and testing.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.kafka.producer import get_producer_service
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class StreamConfig(BaseModel):
    count: int = 100
    interval: float = 1.0
    model_type: str = "attack_classification"


@router.post("/test/start-stream")
async def start_test_stream(
    config: StreamConfig,
    background_tasks: BackgroundTasks
):
    """
    Start a test data stream to Kafka.
    Sends synthetic network traffic data for testing real-time processing.

    Args:
        count: Number of messages to send
        interval: Time interval between messages (seconds)
        model_type: "threat_detection" or "attack_classification"
    """
    try:
        producer = get_producer_service()

        # Run in background
        background_tasks.add_task(
            producer.send_test_data_stream,
            count=config.count,
            interval=config.interval,
            model_type=config.model_type
        )

        return {
            "message": "Test data stream started",
            "count": config.count,
            "interval": config.interval,
            "model_type": config.model_type
        }

    except Exception as e:
        logger.error(f"Error starting test stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/send-single")
async def send_single_test_message(model_type: str = "attack_classification"):
    """
    Send a single test message to Kafka.

    Args:
        model_type: "threat_detection" or "attack_classification"
    """
    try:
        producer = get_producer_service()

        if model_type == "threat_detection":
            data = producer._generate_threat_detection_data()
        elif model_type == "attack_classification":
            data = producer._generate_attack_classification_data()
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid model_type. Use 'threat_detection' or 'attack_classification'"
            )

        producer.send_message(data)

        return {
            "message": "Test message sent",
            "model_type": model_type,
            "data": data
        }

    except Exception as e:
        logger.error(f"Error sending test message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
