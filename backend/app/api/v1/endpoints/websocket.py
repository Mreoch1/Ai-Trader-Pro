import logging
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from app.services.websocket import ConnectionManager
from app.core.deps import get_current_user
from app.models import User
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()
manager = ConnectionManager()

@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time market data."""
    logger.info(f"New WebSocket connection request from client_id: {client_id}")
    
    try:
        # First connect to the manager
        await manager.connect(websocket)
        logger.info(f"WebSocket connection accepted for client_id: {client_id}")
        
        # Send the connection success message
        await manager.send_personal_message({
            "type": "connection_status",
            "status": "connected",
            "client_id": client_id
        }, websocket)
        
        # Keep the connection alive until a disconnect occurs
        while True:
            try:
                # Wait for messages with a timeout
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
                logger.debug(f"Received WebSocket message from client {client_id}: {data}")
                
                if data["type"] == "subscribe":
                    symbols = data.get("symbols", [])
                    logger.info(f"Client {client_id} subscribing to symbols: {symbols}")
                    await manager.subscribe(websocket, symbols)
                    
                elif data["type"] == "unsubscribe":
                    symbols = data.get("symbols", [])
                    logger.info(f"Client {client_id} unsubscribing from symbols: {symbols}")
                    await manager.unsubscribe(websocket, symbols)
                    
                elif data["type"] == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await manager.send_personal_message({"type": "ping"}, websocket)
                except Exception:
                    logger.info(f"Client {client_id} disconnected during ping")
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for client {client_id}")
                break
                
            except ValueError as e:
                logger.error(f"ValueError in WebSocket connection for client {client_id}: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": str(e)
                }, websocket)
                
            except Exception as e:
                logger.error(f"Error in websocket connection for client {client_id}: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error"
                }, websocket)
                break
                
    except Exception as e:
        logger.error(f"Error establishing WebSocket connection for client {client_id}: {e}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=1011)  # Internal Server Error
    
    finally:
        # Always ensure we disconnect from the manager
        await manager.disconnect(websocket)
        logger.info(f"Cleaned up connection for client {client_id}")

@router.post("/broadcast")
async def broadcast_message(
    message: dict,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Broadcast a message to all connected clients."""
    if not current_user.is_superuser:
        return {"error": "Not authorized"}
    
    logger.info(f"Broadcasting message to all clients: {message}")
    await manager.broadcast(message)
    return {"message": "Broadcast successful"}

@router.get("/test")
async def test_websocket():
    """Test endpoint to verify WebSocket route is accessible."""
    return {
        "status": "success",
        "message": "WebSocket endpoint is available",
        "websocket_url": "ws://localhost:8000/api/v1/ws/{client_id}",
        "supported_messages": {
            "subscribe": {"type": "subscribe", "symbols": ["AAPL", "GOOGL"]},
            "unsubscribe": {"type": "unsubscribe", "symbols": ["AAPL", "GOOGL"]}
        }
    } 