"""
Kafka Consumer using aiokafka (async-native).
Consumes messages from Kafka, runs predictions, and broadcasts results via WebSocket.
"""

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.preprocessor import DataPreprocessor
from app.services.threat_detector import ThreatDetectorService
from app.services.attack_classifier import AttackClassifierService
from app.services.self_healing import SelfHealingService
from app.services.websocket_manager import get_connection_manager
from app.models.database import TrafficData
from datetime import datetime
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class AIOKafkaConsumerService:
    """Async Kafka consumer service for processing real-time network traffic data."""

    def __init__(self):
        self.consumer = None
        self.preprocessor = DataPreprocessor()
        self.threat_detector = ThreatDetectorService()
        self.attack_classifier = AttackClassifierService()
        self.self_healing = SelfHealingService()
        self.ws_manager = get_connection_manager()
        self.running = False

    async def start(self):
        """Start the Kafka consumer."""
        try:
            logger.info(f"Creating aiokafka consumer with bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
            self.consumer = AIOKafkaConsumer(
                settings.KAFKA_TOPIC_REALTIME_DATA,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_GROUP_ID,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None
            )
            await self.consumer.start()
            self.running = True
            logger.info(f"aiokafka consumer started. Subscribed to topic: {settings.KAFKA_TOPIC_REALTIME_DATA}")
        except Exception as e:
            logger.error(f"Failed to start aiokafka consumer: {e}")
            self.running = False
            raise

    async def stop(self):
        """Stop the Kafka consumer."""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("aiokafka consumer stopped")

    async def consume_messages(self):
        """
        Consume messages from Kafka and process them.
        Fully async implementation with retry logic.
        """
        retry_delay = 5  # Start with 5 second delay
        max_retry_delay = 60  # Max 60 seconds between retries

        while True:  # Outer retry loop
            try:
                # If consumer not initialized, try to start it
                if not self.consumer or not self.running:
                    logger.info("Attempting to start aiokafka consumer...")
                    try:
                        await self.start()
                    except Exception as e:
                        logger.error(f"Failed to start consumer: {e}")
                        logger.warning(f"Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_retry_delay)
                        continue

                    # Success! Reset retry delay
                    retry_delay = 5

                logger.info("Starting message consumption...")

                # Consume messages
                async for msg in self.consumer:
                    if not self.running:
                        break

                    try:
                        # msg.value is already deserialized to dict
                        data = msg.value

                        if not data:
                            logger.warning("Received empty message")
                            continue

                        logger.debug(f"Received message: {data}")

                        # Process the message
                        await self.process_message(data)

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # Continue processing other messages

            except KeyboardInterrupt:
                logger.info("Consumer interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}")
                logger.warning(f"Will retry in {retry_delay}s...")
                await self.stop()
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

        # Final cleanup
        await self.stop()

    async def process_message(self, data: dict):
        """
        Process a single Kafka message.
        Runs prediction pipeline and broadcasts results.
        """
        try:
            # Get database session
            db = SessionLocal()

            try:
                # Validate and extract features
                features, model_type = self.preprocessor.validate_and_extract_features(
                    data, model_type="auto"
                )

                # Store traffic data
                traffic_record = TrafficData(features=features, source="realtime")
                db.add(traffic_record)
                db.commit()
                db.refresh(traffic_record)

                # Initialize response data
                prediction_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "traffic_data_id": traffic_record.id,
                    "threat_prediction": None,
                    "attack_prediction": None,
                    "self_healing_action": None,
                }

                # Run threat detection if threat detection features are available
                if model_type == "threat_detection":
                    threat_prediction = self.threat_detector.predict(
                        features, db, traffic_record.id
                    )

                    prediction_data["threat_prediction"] = {
                        "id": threat_prediction.id,
                        "prediction_score": threat_prediction.prediction_score,
                        "is_attack": threat_prediction.is_attack,
                        "threshold": threat_prediction.threshold,
                    }

                # Run attack classification if classification features are available
                elif model_type == "attack_classification":
                    attack_prediction = self.attack_classifier.predict(
                        features, db, traffic_record.id
                    )

                    # Log self-healing action
                    self_healing_action = self.self_healing.log_action(
                        attack_prediction, db
                    )

                    # Add to response
                    prediction_data["attack_prediction"] = {
                        "id": attack_prediction.id,
                        "attack_type_encoded": attack_prediction.attack_type_encoded,
                        "attack_type_name": attack_prediction.attack_type_name,
                        "confidence": attack_prediction.confidence,
                    }

                    prediction_data["self_healing_action"] = {
                        "id": self_healing_action.id,
                        "action_type": self_healing_action.action_type,
                        "action_description": self_healing_action.action_description,
                        "action_params": self_healing_action.action_params,
                        "status": self_healing_action.status,
                    }

                # Broadcast to WebSocket clients
                await self.ws_manager.broadcast_prediction(prediction_data)

                # Log processing result
                if model_type == "threat_detection":
                    logger.info(
                        f"Processed message: Traffic ID {traffic_record.id}, "
                        f"Model: {model_type}, Attack: {prediction_data['threat_prediction']['is_attack']}"
                    )
                elif model_type == "attack_classification":
                    logger.info(
                        f"Processed message: Traffic ID {traffic_record.id}, "
                        f"Model: {model_type}, Attack Type: {prediction_data['attack_prediction']['attack_type_name']}"
                    )

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                db.rollback()
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in message processing: {e}")


# Global consumer instance
_consumer_service = None


def get_consumer_service() -> AIOKafkaConsumerService:
    """Get or create the global consumer service instance."""
    global _consumer_service
    if _consumer_service is None:
        _consumer_service = AIOKafkaConsumerService()
    return _consumer_service


async def start_consumer_loop():
    """Start the Kafka consumer loop. Should be run as a background task."""
    consumer = get_consumer_service()
    await consumer.consume_messages()
