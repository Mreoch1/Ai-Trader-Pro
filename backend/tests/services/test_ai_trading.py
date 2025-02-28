import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.ai_trading import AITradingService

pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_openai():
    with patch("openai.chat.completions") as mock_completions:
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""
                    Technical Analysis: The stock shows a bullish trend with strong momentum.
                    
                    Market Sentiment: Positive sentiment with increasing institutional interest.
                    
                    Trading Recommendation: Buy
                    
                    Confidence Level: 0.85
                    
                    Risk Assessment: Moderate risk with good risk/reward ratio.
                    
                    Entry/Exit Points: Entry: $150.00 Exit: $165.00
                    
                    Reasoning: Strong technical indicators, positive market sentiment, and favorable market conditions.
                    """
                )
            )
        ]
        mock_completions.create = AsyncMock(return_value=mock_response)
        yield mock_completions

@pytest.fixture
def mock_trading_service():
    with patch("app.services.trading.trading_service") as mock_service:
        # Mock get_bars
        mock_service.get_bars = AsyncMock(return_value=[
            {
                "timestamp": datetime.now().isoformat(),
                "open": 150.0,
                "high": 155.0,
                "low": 149.0,
                "close": 153.0,
                "volume": 1000000,
            }
        ])
        
        # Mock get_asset
        mock_service.get_asset = AsyncMock(return_value={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
        })
        
        yield mock_service

@pytest.fixture
def ai_trading_service(mock_openai, mock_trading_service):
    return AITradingService("test_key")

async def test_analyze_market(ai_trading_service):
    analysis = await ai_trading_service.analyze_market("AAPL")
    
    assert analysis["symbol"] == "AAPL"
    assert "timestamp" in analysis
    assert "current_price" in analysis
    
    result = analysis["analysis"]
    assert "technical_analysis" in result
    assert "market_sentiment" in result
    assert result["recommendation"] == "buy"
    assert result["confidence"] == 0.85
    assert "risk_assessment" in result
    assert "entry_exit_points" in result
    assert result["entry_exit_points"]["entry"] == 150.00
    assert result["entry_exit_points"]["exit"] == 165.00
    assert "reasoning" in result

async def test_generate_analysis_prompt(ai_trading_service):
    market_data = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "current_price": 150.0,
        "historical_data": [
            {
                "timestamp": datetime.now().isoformat(),
                "open": 150.0,
                "high": 155.0,
                "low": 149.0,
                "close": 153.0,
                "volume": 1000000,
            }
        ],
    }
    
    prompt = ai_trading_service._generate_analysis_prompt(market_data)
    
    assert "AAPL" in prompt
    assert "Apple Inc." in prompt
    assert "NASDAQ" in prompt
    assert "$150.0" in prompt
    assert "Technical Analysis" in prompt
    assert "Market Sentiment" in prompt
    assert "Trading Recommendation" in prompt
    assert "Confidence Level" in prompt
    assert "Risk Assessment" in prompt
    assert "Entry/Exit Points" in prompt
    assert "Reasoning" in prompt

async def test_parse_ai_response(ai_trading_service):
    response = """
    Technical Analysis: Bullish trend
    
    Market Sentiment: Positive
    
    Trading Recommendation: Buy
    
    Confidence Level: 0.85
    
    Risk Assessment: Moderate
    
    Entry/Exit Points: Entry: $150.00 Exit: $165.00
    
    Reasoning: Strong indicators
    """
    
    result = ai_trading_service._parse_ai_response(response)
    
    assert result["technical_analysis"] == "Bullish trend"
    assert result["market_sentiment"] == "Positive"
    assert result["recommendation"] == "buy"
    assert result["confidence"] == 0.85
    assert result["risk_assessment"] == "Moderate"
    assert result["entry_exit_points"]["entry"] == 150.00
    assert result["entry_exit_points"]["exit"] == 165.00
    assert result["reasoning"] == "Strong indicators"

async def test_format_price_data(ai_trading_service):
    bars = [
        {
            "timestamp": "2024-02-28T12:00:00",
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 153.0,
            "volume": 1000000,
        }
    ]
    
    formatted = ai_trading_service._format_price_data(bars)
    
    assert "2024-02-28T12:00:00" in formatted
    assert "$150.0" in formatted
    assert "$155.0" in formatted
    assert "$149.0" in formatted
    assert "$153.0" in formatted
    assert "1000000" in formatted 