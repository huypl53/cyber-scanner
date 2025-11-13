"""
Kafka Producer for sending test network traffic data.
Used for testing and simulating real-time data streams.
"""
from confluent_kafka import Producer
from app.core.config import settings
from app.services.preprocessor import DataPreprocessor
import json
import logging
import time
import random

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """Kafka producer service for sending test traffic data."""

    def __init__(self):
        self.producer_config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'threat-detection-producer'
        }
        self.producer = Producer(self.producer_config)
        self.preprocessor = DataPreprocessor()

    def delivery_callback(self, err, msg):
        """Callback for message delivery confirmation."""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} "
                f"[partition {msg.partition()}]"
            )

    def send_message(self, data: dict, topic: str = None):
        """
        Send a single message to Kafka.

        Args:
            data: Dictionary containing network traffic features
            topic: Kafka topic (defaults to configured realtime topic)
        """
        if topic is None:
            topic = settings.KAFKA_TOPIC_REALTIME_DATA

        try:
            # Serialize data to JSON
            message = json.dumps(data)

            # Send message
            self.producer.produce(
                topic,
                value=message.encode('utf-8'),
                callback=self.delivery_callback
            )

            # Trigger delivery reports
            self.producer.poll(0)

            logger.debug(f"Sent message to topic {topic}")

        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def send_test_data_stream(
        self,
        count: int = 100,
        interval: float = 1.0,
        model_type: str = "attack_classification"
    ):
        """
        Send a stream of test data to Kafka.

        Args:
            count: Number of messages to send
            interval: Time interval between messages (seconds)
            model_type: "threat_detection" or "attack_classification"
        """
        logger.info(
            f"Starting test data stream: {count} messages, "
            f"{interval}s interval, type: {model_type}"
        )

        for i in range(count):
            # Generate sample data
            if model_type == "threat_detection":
                data = self._generate_threat_detection_data()
            else:
                data = self._generate_attack_classification_data()

            # Send message
            self.send_message(data)

            logger.info(f"Sent test message {i + 1}/{count}")

            # Wait before sending next message
            time.sleep(interval)

        # Flush any remaining messages
        self.producer.flush()

        logger.info("Test data stream completed")

    def _generate_threat_detection_data(self) -> dict:
        """Generate random threat detection test data (10 features)."""
        base_data = self.preprocessor.generate_sample_threat_detection_data()

        # Add some randomness
        base_data['src_bytes'] = random.randint(100, 10000)
        base_data['dst_bytes'] = random.randint(100, 10000)
        base_data['count'] = random.randint(1, 500)
        base_data['same_srv_rate'] = round(random.random(), 2)
        base_data['diff_srv_rate'] = round(random.random(), 2)

        return base_data

    def _generate_attack_classification_data(self) -> dict:
        """Generate random attack classification test data (42 features)."""
        base_data = self.preprocessor.generate_sample_attack_classification_data()

        # Add some randomness to make data more realistic
        base_data[' Destination Port'] = random.choice([21, 22, 80, 443, 8080, 3306])
        base_data[' Flow Duration'] = random.randint(1000, 100000)
        base_data[' Total Fwd Packets'] = random.randint(1, 200)
        base_data['Flow Bytes/s'] = random.randint(100, 100000)
        base_data[' Flow Packets/s'] = random.randint(1, 1000)
        base_data['FIN Flag Count'] = random.randint(0, 5)
        base_data[' RST Flag Count'] = random.randint(0, 5)
        base_data[' PSH Flag Count'] = random.randint(0, 10)
        base_data[' ACK Flag Count'] = random.randint(0, 50)

        return base_data

    def flush(self):
        """Flush any remaining messages."""
        self.producer.flush()

    def close(self):
        """Close the producer."""
        self.producer.flush()
        logger.info("Kafka producer closed")


# Global producer instance
_producer_service = None


def get_producer_service() -> KafkaProducerService:
    """Get or create the global producer service instance."""
    global _producer_service
    if _producer_service is None:
        _producer_service = KafkaProducerService()
    return _producer_service
