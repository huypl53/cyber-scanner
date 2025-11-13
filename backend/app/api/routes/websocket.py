"""
WebSocket API endpoint for real-time updates.
Allows frontend to receive live prediction updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.websocket_manager import get_connection_manager
from app.services.threat_detector import ThreatDetectorService
from app.services.attack_classifier import AttackClassifierService
from app.services.self_healing import SelfHealingService
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time prediction updates.

    Connected clients will receive:
    - New predictions as they are made
    - Statistics updates
    - System status updates

    Message format:
    {
        "type": "prediction" | "stats_update" | "status",
        "timestamp": "ISO datetime",
        "data": {...}
    }
    """
    manager = get_connection_manager()
    await manager.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to AI Threat Detection System",
            "connections": manager.get_connection_count()
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client (e.g., requests for data)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": str(datetime.utcnow())
                    })

                elif message.get("type") == "request_stats":
                    # Client requesting current statistics
                    # This could trigger a stats broadcast
                    await websocket.send_json({
                        "type": "stats_request_received",
                        "message": "Stats will be sent on next update"
                    })

            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error in WebSocket: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(websocket)


@router.get("/connections")
async def get_connection_stats():
    """Get statistics about active WebSocket connections."""
    manager = get_connection_manager()
    return {
        "active_connections": manager.get_connection_count()
    }


# Import datetime for timestamps
from datetime import datetime
