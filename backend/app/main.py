from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import upload, predictions, websocket, config, models, health
from app.kafka.consumer_aiokafka import start_consumer_loop
from app.kafka.external_consumer import start_external_consumer_loop
import uvicorn
import asyncio
import logging
import subprocess
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create database tables (with error handling for when DB is not available)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Could not create database tables: {e}")
    logger.warning(
        "Database features will not be available. API may have limited functionality."
    )

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG,
)

# Configure CORS
# Note: allow_credentials=True cannot be used with allow_origins=["*"]
# Instead, we use allow_origin_regex to match all origins while supporting credentials
cors_kwargs = {
    "allow_credentials": False,  # Disabled to allow wildcard origins
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "allow_origins": ["*"],  # Allow all origins for development
}

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Include routers
app.include_router(health.router, tags=["health"])  # Health check (no prefix for /health)
app.include_router(upload.router, prefix=settings.API_V1_PREFIX, tags=["upload"])
app.include_router(
    predictions.router, prefix=settings.API_V1_PREFIX, tags=["predictions"]
)
app.include_router(
    config.router, prefix=f"{settings.API_V1_PREFIX}/config", tags=["configuration"]
)
app.include_router(
    models.router, tags=["models"]
)  # Models router includes its own prefix
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Include test producer router (for development/testing)
from app.api.routes import test_producer

app.include_router(
    test_producer.router, prefix=settings.API_V1_PREFIX, tags=["testing"]
)


def run_migrations():
    """Run Alembic migrations on startup."""
    try:
        # Get the backend directory (parent of app)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_ini = os.path.join(backend_dir, "alembic.ini")

        if not os.path.exists(alembic_ini):
            logger.warning(f"Alembic config not found at {alembic_ini}, skipping migrations")
            return

        logger.info("Checking for pending database migrations...")

        # Check current revision
        current_result = subprocess.run(
            ["alembic", "current"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Run migrations
        upgrade_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if upgrade_result.returncode == 0:
            logger.info("Database migrations applied successfully")
            if upgrade_result.stdout:
                logger.info(f"Migration output: {upgrade_result.stdout}")
        else:
            logger.error(f"Migration failed: {upgrade_result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("Migration command timed out")
    except FileNotFoundError:
        logger.warning("Alembic command not found. Install with: pip install alembic")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")


@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    logger.info("Starting AI Threat Detection System...")

    # Run database migrations
    try:
        run_migrations()
    except Exception as e:
        logger.error(f"Migration error (continuing anyway): {e}")

    # Start internal Kafka consumer in background (using aiokafka - async native)
    try:
        asyncio.create_task(start_consumer_loop())
        logger.info("Internal Kafka consumer task created (aiokafka)")
    except Exception as e:
        logger.warning(f"Could not create Kafka consumer task: {e}")
        logger.warning("API will function without real-time Kafka streaming")

    # Start external Kafka consumer in background (if enabled)
    try:
        asyncio.create_task(start_external_consumer_loop())
        logger.info("External Kafka consumer task created (will connect with retry)")
    except Exception as e:
        logger.warning(f"Could not create external Kafka consumer task: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("Shutting down AI Threat Detection System...")


@app.get("/")
async def root():
    return {
        "message": "AI Threat Detection System API",
        "docs": "/docs",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
