"""
Kafka Consumer for real-time network traffic data.
Consumes messages from Kafka, runs predictions, and broadcasts results via WebSocket.
"""

from confluent_kafka import Consumer, KafkaException, KafkaError, Message
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
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class KafkaConsumerService:
    """Kafka consumer service for processing real-time network traffic data."""

    def __init__(self):
        self.consumer_config = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": settings.KAFKA_GROUP_ID,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
            "socket.timeout.ms": 10000,  # 10 second timeout for network operations
            "session.timeout.ms": 10000,  # 10 second session timeout
            "api.version.request.timeout.ms": 5000,  # 5 second API version request timeout
        }
        self.consumer = None
        self.preprocessor = DataPreprocessor()
        self.threat_detector = ThreatDetectorService()
        self.attack_classifier = AttackClassifierService()
        self.self_healing = SelfHealingService()
        self.ws_manager = get_connection_manager()
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=1)

    def _create_consumer_sync(self):
        """Synchronous consumer creation (to be run in thread pool)."""
        try:
            logger.info(f"Creating Kafka consumer with bootstrap servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
            consumer = Consumer(self.consumer_config)
            logger.info("Consumer created, subscribing to topic...")
            consumer.subscribe([settings.KAFKA_TOPIC_REALTIME_DATA])
            logger.info(
                f"Kafka consumer started. Subscribed to topic: "
                f"{settings.KAFKA_TOPIC_REALTIME_DATA}"
            )
            return consumer
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            raise

    async def start(self):
        """Start the Kafka consumer (async wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            # Run blocking Consumer() creation in thread pool
            self.consumer = await loop.run_in_executor(self.executor, self._create_consumer_sync)
            self.running = True
        except KafkaException as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            logger.error("Kafka consumer will retry connection during message consumption")
            # Don't raise - allow graceful degradation
            self.running = False
        except Exception as e:
            logger.error(f"Unexpected error starting Kafka consumer: {e}")
            self.running = False

    def stop(self):
        """Stop the Kafka consumer."""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer stopped")
        if self.executor:
            self.executor.shutdown(wait=False)

    async def consume_messages(self):
        """
        Consume messages from Kafka and process them.
        This should be run in a separate thread/process.
        Includes retry logic with exponential backoff.
        """
        retry_delay = 10  # Start with 10 second delay to let startup complete
        max_retry_delay = 60  # Max 60 seconds between retries

        # Give the application time to fully start up before attempting Kafka connection
        logger.info("Kafka consumer will attempt connection in 30 seconds...")
        await asyncio.sleep(30)

        while True:  # Outer retry loop
            try:
                # If consumer not initialized, try to start it
                if not self.consumer or not self.running:
                    logger.info("Attempting to start Kafka consumer...")
                    await self.start()

                    # If start() failed (sets running=False), wait and retry
                    if not self.running:
                        logger.warning(f"Kafka consumer start failed. Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_retry_delay)
                        continue

                    # Success! Reset retry delay
                    retry_delay = 10

                logger.info("Starting message consumption...")
                loop = asyncio.get_event_loop()

                while self.running:
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
                logger.info("Consumer interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}")
                logger.warning(f"Will retry in {retry_delay}s...")
                self.stop()
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)

        # Final cleanup
        self.stop()

    async def process_message(self, msg: Message):
        """
        Process a single Kafka message.
        Runs prediction pipeline and broadcasts results.
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
            logger.debug(f"Received message: {data}")

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

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error in message processing: {e}")


# Global consumer instance
_consumer_service = None


def get_consumer_service() -> KafkaConsumerService:
    """Get or create the global consumer service instance."""
    global _consumer_service
    if _consumer_service is None:
        _consumer_service = KafkaConsumerService()
    return _consumer_service


async def start_consumer_loop():
    """Start the Kafka consumer loop. Should be run as a background task."""
    consumer = get_consumer_service()
    # consume_messages() handles start() internally with retry logic
    await consumer.consume_messages()
