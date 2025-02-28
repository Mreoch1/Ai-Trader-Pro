from typing import Dict, List, Optional
import openai
from datetime import datetime, timedelta

from app.config import settings
from app.services.trading import trading_service

class AITradingService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = "gpt-4-turbo-preview"  # Using the latest GPT-4 model
        
    async def analyze_market(
        self,
        symbol: str,
        timeframe: str = "1D",
        lookback_days: int = 30,
    ) -> Dict:
        """Analyze market data and generate trading suggestions."""
        try:
            # Get historical data
            end = datetime.now()
            start = end - timedelta(days=lookback_days)
            bars = await trading_service.get_bars(symbol, timeframe, start, end)
            
            # Get asset info
            asset = await trading_service.get_asset(symbol)
            
            # Prepare market data for analysis
            market_data = {
                "symbol": symbol,
                "name": asset["name"],
                "exchange": asset["exchange"],
                "historical_data": bars[-10:],  # Last 10 data points for brevity
                "current_price": bars[-1]["close"] if bars else None,
            }
            
            # Generate analysis prompt
            prompt = self._generate_analysis_prompt(market_data)
            
            # Get AI analysis
            response = await self._get_ai_analysis(prompt)
            
            # Parse and structure the response
            analysis = self._parse_ai_response(response)
            
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "current_price": market_data["current_price"],
                "analysis": analysis,
            }
        except Exception as e:
            raise Exception(f"Failed to analyze market: {str(e)}")
    
    def _generate_analysis_prompt(self, market_data: Dict) -> str:
        """Generate a prompt for market analysis."""
        return f"""
        As an AI trading expert, analyze the following market data and provide trading suggestions:

        Asset: {market_data['symbol']} ({market_data['name']})
        Exchange: {market_data['exchange']}
        Current Price: ${market_data['current_price']}

        Recent price action:
        {self._format_price_data(market_data['historical_data'])}

        Please provide:
        1. Technical Analysis
        2. Market Sentiment
        3. Trading Recommendation (Buy/Sell/Hold)
        4. Confidence Level (0-1)
        5. Risk Assessment
        6. Entry/Exit Points
        7. Reasoning

        Format the response in a clear, structured way.
        """

    async def _get_ai_analysis(self, prompt: str) -> str:
        """Get analysis from OpenAI API."""
        try:
            response = await openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert AI trading analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Failed to get AI analysis: {str(e)}")

    def _parse_ai_response(self, response: str) -> Dict:
        """Parse and structure the AI response."""
        # This is a simple parser. In production, you might want to use
        # more sophisticated parsing or structure the AI response differently
        sections = response.split("\n\n")
        analysis = {
            "technical_analysis": "",
            "market_sentiment": "",
            "recommendation": "",
            "confidence": 0.0,
            "risk_assessment": "",
            "entry_exit_points": {},
            "reasoning": "",
        }
        
        for section in sections:
            if "Technical Analysis:" in section:
                analysis["technical_analysis"] = section.split("Technical Analysis:")[1].strip()
            elif "Market Sentiment:" in section:
                analysis["market_sentiment"] = section.split("Market Sentiment:")[1].strip()
            elif "Trading Recommendation:" in section:
                rec = section.split("Trading Recommendation:")[1].strip().lower()
                analysis["recommendation"] = "buy" if "buy" in rec else "sell" if "sell" in rec else "hold"
            elif "Confidence Level:" in section:
                try:
                    conf = float(section.split("Confidence Level:")[1].strip().split()[0])
                    analysis["confidence"] = min(max(conf, 0.0), 1.0)
                except:
                    analysis["confidence"] = 0.5
            elif "Risk Assessment:" in section:
                analysis["risk_assessment"] = section.split("Risk Assessment:")[1].strip()
            elif "Entry/Exit Points:" in section:
                points = section.split("Entry/Exit Points:")[1].strip()
                try:
                    entry = float(points.split("Entry:")[1].split()[0].strip("$"))
                    exit = float(points.split("Exit:")[1].split()[0].strip("$"))
                    analysis["entry_exit_points"] = {"entry": entry, "exit": exit}
                except:
                    analysis["entry_exit_points"] = {}
            elif "Reasoning:" in section:
                analysis["reasoning"] = section.split("Reasoning:")[1].strip()
        
        return analysis

    def _format_price_data(self, bars: List[Dict]) -> str:
        """Format price data for the prompt."""
        return "\n".join([
            f"Date: {bar['timestamp']}, Open: ${bar['open']}, High: ${bar['high']}, "
            f"Low: ${bar['low']}, Close: ${bar['close']}, Volume: {bar['volume']}"
            for bar in bars
        ])

# Create default AI trading service instance
ai_trading_service = AITradingService(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None 