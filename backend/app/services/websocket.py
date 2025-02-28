from typing import Dict, List, Optional, Set
import json
from fastapi import WebSocket
import asyncio
import logging
from datetime import datetime

from app.services.trading import trading_service

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections with their subscriptions
        self.active_connections: Dict[WebSocket, Set[str]] = {}
        # Store latest data for each symbol
        self.latest_data: Dict[str, dict] = {}
        # Background task for market data updates
        self.update_task: Optional[asyncio.Task] = None
        # Lock for synchronizing access to shared resources
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket):
        """Connect a new client."""
        try:
            await websocket.accept()
            async with self._lock:
                self.active_connections[websocket] = set()
                logger.info(f"New client connected. Total connections: {len(self.active_connections)}")
            
            # Start update task if this is the first connection
            if len(self.active_connections) == 1 and not self.update_task:
                self.update_task = asyncio.create_task(self._update_market_data())
                logger.info("Started market data update task")
                
        except Exception as e:
            logger.error(f"Error connecting client: {e}")
            if not websocket.client_state.DISCONNECTED:
                await websocket.close(code=1011)
            raise
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a client."""
        async with self._lock:
            if websocket in self.active_connections:
                # Remove client's subscriptions
                del self.active_connections[websocket]
                logger.info(f"Client disconnected. Remaining connections: {len(self.active_connections)}")
                
                # Stop update task if no more connections
                if not self.active_connections and self.update_task:
                    self.update_task.cancel()
                    try:
                        await self.update_task
                    except asyncio.CancelledError:
                        pass
                    self.update_task = None
                    logger.info("Stopped market data update task")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
            
        disconnected_clients = []
        async with self._lock:
            for websocket, subscriptions in self.active_connections.items():
                try:
                    if not websocket.client_state.DISCONNECTED:
                        await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
                    disconnected_clients.append(websocket)
            
            # Clean up disconnected clients
            for websocket in disconnected_clients:
                await self.disconnect(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific client."""
        try:
            if not websocket.client_state.DISCONNECTED:
                await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)
    
    async def subscribe(self, websocket: WebSocket, symbols: List[str]):
        """Subscribe to market data for specific symbols."""
        if not symbols:
            return
            
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections[websocket].update(symbols)
                logger.info(f"Client subscribed to symbols: {symbols}")
                
                # Send latest data for newly subscribed symbols
                for symbol in symbols:
                    if symbol in self.latest_data:
                        try:
                            await self.send_personal_message(
                                {
                                    "type": "market_data",
                                    "symbol": symbol,
                                    "data": self.latest_data[symbol]
                                },
                                websocket
                            )
                        except Exception as e:
                            logger.error(f"Error sending initial data for {symbol}: {e}")
                            await self.disconnect(websocket)
                            break
    
    async def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        """Unsubscribe from market data for specific symbols."""
        if not symbols:
            return
            
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections[websocket].difference_update(symbols)
                logger.info(f"Client unsubscribed from symbols: {symbols}")
    
    async def _update_market_data(self):
        """Background task to update market data."""
        update_interval = 60  # Update every minute
        
        while True:
            try:
                # Get all unique symbols from all subscriptions
                symbols = set()
                async with self._lock:
                    for subscriptions in self.active_connections.values():
                        symbols.update(subscriptions)
                
                if not symbols:
                    await asyncio.sleep(update_interval)
                    continue
                
                # Update market data for each symbol
                for symbol in symbols:
                    try:
                        # Get latest bar
                        bars = await trading_service.get_bars(
                            symbol=symbol,
                            timeframe="1m",  # 1-minute bars for real-time data
                            limit=1
                        )
                        
                        if bars:
                            bar = bars[0]
                            new_data = {
                                "price": bar["close"],
                                "timestamp": bar["timestamp"],
                                "volume": bar["volume"],
                                "change": bar["close"] - bar["open"],
                                "change_percent": (bar["close"] - bar["open"]) / bar["open"] * 100
                            }
                            
                            # Only broadcast if data has changed
                            if symbol not in self.latest_data or self.latest_data[symbol] != new_data:
                                self.latest_data[symbol] = new_data
                                
                                # Broadcast to subscribed clients
                                async with self._lock:
                                    for websocket, subscriptions in self.active_connections.items():
                                        if symbol in subscriptions:
                                            try:
                                                await self.send_personal_message(
                                                    {
                                                        "type": "market_data",
                                                        "symbol": symbol,
                                                        "data": new_data
                                                    },
                                                    websocket
                                                )
                                            except Exception as e:
                                                logger.error(f"Error sending market data to client: {e}")
                                                await self.disconnect(websocket)
                    
                    except Exception as e:
                        logger.error(f"Error updating market data for {symbol}: {e}")
                
                # Wait before next update (rate limit compliance)
                await asyncio.sleep(update_interval)
                
            except asyncio.CancelledError:
                logger.info("Market data update task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in market data update loop: {e}")
                await asyncio.sleep(update_interval)

    def get_subscribed_symbols(self, websocket: WebSocket) -> Set[str]:
        """Get the set of symbols a client is subscribed to."""
        return self.active_connections.get(websocket, set())

# Create global connection manager
manager = ConnectionManager() 