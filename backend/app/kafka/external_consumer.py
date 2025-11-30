"""
External Kafka Consumer for external data providers.
Consumes messages from external-traffic topic with IP whitelisting.
"""

from confluent_kafka import Consumer, KafkaException, KafkaError, Message
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.preprocessor import DataPreprocessor
from app.services.threat_detector import ThreatDetectorService
from app.services.attack_classifier import AttackClassifierService
from app.services.self_healing import SelfHealingService
from app.services.ip_whitelist import IPWhitelistService
from app.services.config_service import ConfigService
from app.services.websocket_manager import get_connection_manager
from app.models.database import TrafficData
from datetime import datetime
import json
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ExternalKafkaConsumerService:
    """External Kafka consumer service with IP whitelisting for external data providers."""

    def __init__(self):
        self.consumer_config = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": settings.KAFKA_EXTERNAL_CONSUMER_GROUP,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        }
        self.consumer = None
        self.preprocessor = DataPreprocessor()
        self.threat_detector = ThreatDetectorService()
        self.attack_classifier = AttackClassifierService()
        self.self_healing = SelfHealingService()
        self.ws_manager = get_connection_manager()
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=1)

    def is_enabled(self) -> bool:
        """
        Check if external Kafka consumer is enabled in configuration.

        Returns:
            bool: True if enabled, False otherwise
        """
        db = SessionLocal()
        try:
            config_service = ConfigService(db)
            return config_service.is_source_enabled("external_kafka")
        except Exception as e:
            logger.error(f"Error checking if external Kafka is enabled: {e}")
            return False
        finally:
            db.close()

    def start(self):
        """Start the external Kafka consumer if enabled."""
        if not self.is_enabled():
            logger.info("External Kafka consumer is disabled. Skipping startup.")
            return

        try:
            self.consumer = Consumer(self.consumer_config)
            self.consumer.subscribe([settings.KAFKA_TOPIC_EXTERNAL_DATA])
            self.running = True
            logger.info(
                f"External Kafka consumer started. Subscribed to topic: "
                f"{settings.KAFKA_TOPIC_EXTERNAL_DATA}"
            )
        except KafkaException as e:
            logger.error(f"Failed to start external Kafka consumer: {e}")
            raise

    def stop(self):
        """Stop the external Kafka consumer."""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("External Kafka consumer stopped")
        if self.executor:
            self.executor.shutdown(wait=False)

    def _extract_sender_ip(self, msg: Message, data: Dict[str, Any]) -> Optional[str]:
        """
        Extract sender IP from Kafka message.

        Tries multiple methods:
        1. From message headers (if producer sets it)
        2. From message payload 'sender_ip' field

        Args:
            msg: Kafka message
            data: Parsed message payload

        Returns:
            Optional[str]: Sender IP or None if not found
        """
        # Try to get from headers
        headers = msg.headers() or []
        for key, value in headers:
            if key == "sender_ip":
                try:
                    return value.decode("utf-8")
                except Exception as e:
                    logger.warning(f"Error decoding sender_ip header: {e}")

        # Try to get from payload
        if "sender_ip" in data:
            return data.get("sender_ip")

        logger.warning("No sender_ip found in message headers or payload")
        return None

    def _validate_sender_ip(self, sender_ip: Optional[str]) -> bool:
        """
        Validate sender IP against whitelist.

        Args:
            sender_ip: IP address to validate

        Returns:
            bool: True if IP is whitelisted and active, False otherwise
        """
        if not sender_ip:
            logger.warning("Cannot validate: sender IP is None")
            return False

        db = SessionLocal()
        try:
            whitelist_service = IPWhitelistService(db)
            is_allowed = whitelist_service.is_ip_allowed(sender_ip)

            if not is_allowed:
                logger.warning(f"Rejected message from non-whitelisted IP: {sender_ip}")

            return is_allowed
        except Exception as e:
            logger.error(f"Error validating sender IP {sender_ip}: {e}")
            return False
        finally:
            db.close()

    async def consume_messages(self):
        """
        Consume messages from external Kafka topic and process them.
        Only processes messages from whitelisted IPs.
        """
        if not self.consumer:
            raise RuntimeError("Consumer not started. Call start() first.")

        logger.info("Starting external message consumption...")

        try:
            loop = asyncio.get_event_loop()

            while self.running:
                # Check if still enabled (can be disabled at runtime)
                if not self.is_enabled():
                    logger.info("External Kafka consumer disabled. Stopping consumption.")
                    break

                # Run the blocking poll() call in a thread pool executor
                msg = await loop.run_in_executor(self.executor, self.consumer.poll, 1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"Reached end of partition: {msg.partition()}")
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                    continue

                # Process the message
                await self.process_message(msg)

        except KeyboardInterrupt:
            logger.info("External consumer interrupted by user")
        except Exception as e:
            logger.error(f"Error in external consumer loop: {e}")
        finally:
            self.stop()

    async def process_message(self, msg: Message):
        """
        Process a single message from external Kafka topic.
        Validates sender IP before processing.

        Args:
            msg: Kafka message

        Message format expected:
        {
            "sender_ip": "192.168.1.100",  # Required
            "timestamp": "2025-11-28T12:00:00Z",  # Optional
            "features": {
                "service": "http",
                "flag": "SF",
                "src_bytes": 1024,
                ... (10 or 42 features)
            }
        }
        """
        try:
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

            # Parse message
            data = json.loads(decoded_msg)
            logger.debug(f"Received external message: {data}")

            # Extract sender IP
            sender_ip = self._extract_sender_ip(msg, data)

            # Validate sender IP against whitelist
            if not self._validate_sender_ip(sender_ip):
                logger.warning(f"Dropping message from non-whitelisted IP: {sender_ip}")
                return

            logger.info(f"Processing message from whitelisted IP: {sender_ip}")

            # Get database session
            db = SessionLocal()

            try:
                # Extract features from message
                features_data = data.get("features", data)

                # Validate and extract features
                features, model_type = self.preprocessor.validate_and_extract_features(
                    features_data, model_type="auto"
                )

                # Store traffic data with external_kafka source
                traffic_record = TrafficData(features=features, source="external_kafka")
                db.add(traffic_record)
                db.commit()
                db.refresh(traffic_record)

                # Initialize response data
                prediction_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "traffic_data_id": traffic_record.id,
                    "source": "external_kafka",
                    "sender_ip": sender_ip,
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
                logger.info(
                    f"Processed external message: Traffic ID {traffic_record.id}, "
                    f"Source IP: {sender_ip}, Model: {model_type}"
                )

            except Exception as e:
                logger.error(f"Error processing external message: {e}")
                db.rollback()
            finally:
                db.close()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in external message: {e}")
        except Exception as e:
            logger.error(f"Error in external message processing: {e}")


# Global consumer instance
_external_consumer_service = None


def get_external_consumer_service() -> ExternalKafkaConsumerService:
    """Get or create the global external consumer service instance."""
    global _external_consumer_service
    if _external_consumer_service is None:
        _external_consumer_service = ExternalKafkaConsumerService()
    return _external_consumer_service


async def start_external_consumer_loop():
    """Start the external Kafka consumer loop. Should be run as a background task."""
    consumer = get_external_consumer_service()
    consumer.start()

    # Only consume if enabled
    if consumer.is_enabled():
        await consumer.consume_messages()
    else:
        logger.info("External Kafka consumer not started (disabled in config)")
