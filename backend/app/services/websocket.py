from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
import asyncio
import logging
from datetime import datetime
import yfinance as yf
from app.schemas.trading import MarketData
from app.services.ai_trading import ai_trading_service

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.symbols: Set[str] = set()
        self.is_running: bool = False
        self.update_interval: float = 1.0  # Update interval in seconds

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_market_data(self, market_data: MarketData):
        """
        Broadcast market data to all connected clients
        """
        disconnected_clients = set()
        
        for client_id, connections in self.active_connections.items():
            disconnected_connections = set()
            
            for connection in connections:
                try:
                    await connection.send_json(market_data.model_dump())
                except Exception as e:
                    logger.error(f"Error sending data to client {client_id}: {str(e)}")
                    disconnected_connections.add(connection)
            
            # Remove disconnected connections
            connections.difference_update(disconnected_connections)
            if not connections:
                disconnected_clients.add(client_id)
        
        # Remove clients with no active connections
        for client_id in disconnected_clients:
            del self.active_connections[client_id]

    def add_symbol(self, symbol: str):
        """
        Add a symbol to track
        """
        self.symbols.add(symbol.upper())

    def remove_symbol(self, symbol: str):
        """
        Remove a symbol from tracking
        """
        self.symbols.discard(symbol.upper())

    async def start_market_data_stream(self):
        """
        Start the market data streaming service
        """
        self.is_running = True
        
        while self.is_running and self.active_connections:
            try:
                for symbol in self.symbols:
                    # Fetch real-time data using yfinance
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period='1d', interval='1m').iloc[-1]
                    
                    # Generate market data
                    market_data = MarketData(
                        symbol=symbol,
                        price=float(data['Close']),
                        volume=float(data['Volume']),
                        timestamp=datetime.now(),
                        high=float(data['High']),
                        low=float(data['Low']),
                        open=float(data['Open'])
                    )

                    # Get AI trading signals if available
                    if ai_trading_service:
                        try:
                            signal = await ai_trading_service.analyze_market_data(symbol)
                            market_data.trading_signal = signal.signal
                            market_data.signal_confidence = signal.confidence
                            market_data.indicators = signal.indicators
                        except Exception as e:
                            logger.error(f"Error getting AI trading signals for {symbol}: {str(e)}")

                    # Broadcast the data
                    await self.broadcast_market_data(market_data)

            except Exception as e:
                logger.error(f"Error in market data stream: {str(e)}")
            
            await asyncio.sleep(self.update_interval)

    def stop_market_data_stream(self):
        """
        Stop the market data streaming service
        """
        self.is_running = False

# Create a global WebSocket manager instance
websocket_manager = WebSocketManager() 