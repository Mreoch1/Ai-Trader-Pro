import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.main import app
from app.services.websocket import manager

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_trading_service():
    with patch("app.services.trading.trading_service") as mock_service:
        # Mock get_bars
        mock_service.get_bars = AsyncMock(return_value=[
            {
                "timestamp": "2024-02-28T12:00:00",
                "open": 150.0,
                "high": 155.0,
                "low": 149.0,
                "close": 153.0,
                "volume": 1000000,
            }
        ])
        yield mock_service

def test_websocket_connection(client, mock_trading_service):
    with client.websocket_connect("/api/v1/ws/test_client") as websocket:
        # Test subscription
        websocket.send_json({
            "type": "subscribe",
            "symbols": ["AAPL"],
        })
        
        # Receive market data
        data = websocket.receive_json()
        assert data["type"] == "market_data"
        assert data["symbol"] == "AAPL"
        assert "price" in data["data"]
        assert "timestamp" in data["data"]
        assert "volume" in data["data"]
        assert "change" in data["data"]
        assert "change_percent" in data["data"]
        
        # Test unsubscription
        websocket.send_json({
            "type": "unsubscribe",
            "symbols": ["AAPL"],
        })

def test_websocket_invalid_message(client):
    with client.websocket_connect("/api/v1/ws/test_client") as websocket:
        # Send invalid message
        websocket.send_json({
            "type": "invalid",
            "data": "test",
        })
        
        # Connection should remain open
        websocket.send_json({
            "type": "subscribe",
            "symbols": ["AAPL"],
        })

@pytest.mark.asyncio
async def test_connection_manager():
    # Create mock websocket
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    
    # Test connection
    await manager.connect(websocket)
    websocket.accept.assert_called_once()
    assert websocket in manager.active_connections
    
    # Test subscription
    await manager.subscribe(websocket, ["AAPL"])
    assert "AAPL" in manager.active_connections[websocket]
    
    # Test unsubscription
    await manager.unsubscribe(websocket, ["AAPL"])
    assert "AAPL" not in manager.active_connections[websocket]
    
    # Test disconnection
    await manager.disconnect(websocket)
    assert websocket not in manager.active_connections

@pytest.mark.asyncio
async def test_broadcast():
    # Create mock websockets
    websocket1 = MagicMock()
    websocket1.send_json = AsyncMock()
    websocket2 = MagicMock()
    websocket2.send_json = AsyncMock()
    
    # Connect websockets
    await manager.connect(websocket1)
    await manager.connect(websocket2)
    
    # Test broadcast
    test_message = {"type": "test", "data": "test_message"}
    await manager.broadcast(test_message)
    
    websocket1.send_json.assert_called_once_with(test_message)
    websocket2.send_json.assert_called_once_with(test_message)
    
    # Clean up
    await manager.disconnect(websocket1)
    await manager.disconnect(websocket2) 