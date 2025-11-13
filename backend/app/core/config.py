from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "AI Threat Detection System"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/threat_detection_db"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "threat_detection_db"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_REALTIME_DATA: str = "network-traffic"
    KAFKA_TOPIC_PREDICTIONS: str = "predictions"
    KAFKA_GROUP_ID: str = "threat-detection-consumer"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
