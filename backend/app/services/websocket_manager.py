"""
WebSocket Connection Manager for real-time updates.
Manages WebSocket connections and broadcasts prediction updates to connected clients.
"""
from fastapi import WebSocket
from typing import List, Dict, Any
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        message_str = json.dumps(message, default=str)

        disconnected = []
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)

        if disconnected:
            logger.info(f"Removed {len(disconnected)} disconnected clients")

    async def broadcast_prediction(self, prediction_data: Dict[str, Any]):
        """
        Broadcast a new prediction to all connected clients.

        Expected format:
        {
            "type": "prediction",
            "data": {
                "traffic_data_id": int,
                "threat_prediction": {...},
                "attack_prediction": {...},
                "self_healing_action": {...}
            }
        }
        """
        message = {
            "type": "prediction",
            "timestamp": prediction_data.get("timestamp"),
            "data": prediction_data
        }
        await self.broadcast(message)

    async def broadcast_stats_update(self, stats: Dict[str, Any]):
        """
        Broadcast updated statistics to all connected clients.
        """
        message = {
            "type": "stats_update",
            "data": stats
        }
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return manager
