from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import upload, predictions, websocket, config, models
from app.kafka.consumer import start_consumer_loop
from app.kafka.external_consumer import start_external_consumer_loop
import uvicorn
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables (with error handling for when DB is not available)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Could not create database tables: {e}")
    logger.warning("Database features will not be available. API may have limited functionality.")

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix=settings.API_V1_PREFIX, tags=["upload"])
app.include_router(predictions.router, prefix=settings.API_V1_PREFIX, tags=["predictions"])
app.include_router(config.router, prefix=f"{settings.API_V1_PREFIX}/config", tags=["configuration"])
app.include_router(models.router, tags=["models"])  # Models router includes its own prefix
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Include test producer router (for development/testing)
from app.api.routes import test_producer
app.include_router(test_producer.router, prefix=settings.API_V1_PREFIX, tags=["testing"])


@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    logger.info("Starting AI Threat Detection System...")

    # Start internal Kafka consumer in background
    try:
        asyncio.create_task(start_consumer_loop())
        logger.info("Internal Kafka consumer task started")
    except Exception as e:
        logger.warning(f"Could not start internal Kafka consumer: {e}")
        logger.warning("Internal Kafka consumer will not be available. Real-time features disabled.")

    # Start external Kafka consumer in background (if enabled)
    try:
        asyncio.create_task(start_external_consumer_loop())
        logger.info("External Kafka consumer task started")
    except Exception as e:
        logger.warning(f"Could not start external Kafka consumer: {e}")
        logger.warning("External Kafka consumer will not be available.")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("Shutting down AI Threat Detection System...")


@app.get("/")
async def root():
    return {
        "message": "AI Threat Detection System API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
