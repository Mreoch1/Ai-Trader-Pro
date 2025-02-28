from typing import Dict, List, Optional
import openai
from datetime import datetime, timedelta
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import yfinance as yf
from app.schemas.trading import TradingSignal, MarketData
from app.core.config import settings
import logging

from app.services.trading import trading_service

logger = logging.getLogger(__name__)

class AITradingService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = "gpt-4-turbo-preview"  # Using the latest GPT-4 model
        self.scaler = MinMaxScaler()
        self.lookback_period = 20  # Days of historical data to consider
        self.prediction_threshold = 0.6  # Confidence threshold for trading signals
        
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

    async def analyze_market_data(self, symbol: str) -> TradingSignal:
        """
        Analyze market data using AI/ML techniques to generate trading signals.
        """
        try:
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_period)
            df = await self._fetch_historical_data(symbol, start_date, end_date)
            
            if df.empty:
                logger.warning(f"No historical data available for {symbol}")
                return TradingSignal(
                    symbol=symbol,
                    signal="HOLD",
                    confidence=0.0,
                    timestamp=datetime.now(),
                    indicators={}
                )

            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Generate trading signal
            signal, confidence = self._generate_signal(indicators)

            return TradingSignal(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                timestamp=datetime.now(),
                indicators=indicators
            )

        except Exception as e:
            logger.error(f"Error analyzing market data for {symbol}: {str(e)}")
            raise

    async def _fetch_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch historical market data using yfinance.
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1d")
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return pd.DataFrame()

    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate technical indicators for analysis.
        """
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Calculate MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()

        # Calculate Bollinger Bands
        sma = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)

        return {
            'rsi': float(rsi.iloc[-1]),
            'macd': float(macd.iloc[-1]),
            'macd_signal': float(signal_line.iloc[-1]),
            'bb_upper': float(upper_band.iloc[-1]),
            'bb_lower': float(lower_band.iloc[-1]),
            'bb_middle': float(sma.iloc[-1]),
            'current_price': float(df['Close'].iloc[-1])
        }

    def _generate_signal(self, indicators: Dict[str, float]) -> tuple[str, float]:
        """
        Generate trading signal based on technical indicators.
        """
        signals = []
        confidences = []

        # RSI signals
        if indicators['rsi'] < 30:
            signals.append('BUY')
            confidences.append(0.7)
        elif indicators['rsi'] > 70:
            signals.append('SELL')
            confidences.append(0.7)

        # MACD signals
        if indicators['macd'] > indicators['macd_signal']:
            signals.append('BUY')
            confidences.append(0.6)
        elif indicators['macd'] < indicators['macd_signal']:
            signals.append('SELL')
            confidences.append(0.6)

        # Bollinger Bands signals
        if indicators['current_price'] < indicators['bb_lower']:
            signals.append('BUY')
            confidences.append(0.8)
        elif indicators['current_price'] > indicators['bb_upper']:
            signals.append('SELL')
            confidences.append(0.8)

        if not signals:
            return 'HOLD', 0.0

        # Aggregate signals
        buy_confidence = sum(conf for sig, conf in zip(signals, confidences) if sig == 'BUY')
        sell_confidence = sum(conf for sig, conf in zip(signals, confidences) if sig == 'SELL')

        if buy_confidence > sell_confidence and buy_confidence > self.prediction_threshold:
            return 'BUY', buy_confidence
        elif sell_confidence > buy_confidence and sell_confidence > self.prediction_threshold:
            return 'SELL', sell_confidence
        
        return 'HOLD', 0.0

    async def backtest_strategy(self, symbol: str, days: int = 30) -> Dict:
        """
        Backtest the trading strategy using historical data.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = await self._fetch_historical_data(symbol, start_date, end_date)
        if df.empty:
            return {'error': 'No historical data available for backtesting'}

        initial_balance = 100000  # $100,000 initial capital
        balance = initial_balance
        position = 0
        trades = []

        for i in range(20, len(df)):
            historical_data = df.iloc[:i+1]
            indicators = self._calculate_indicators(historical_data)
            signal, confidence = self._generate_signal(indicators)
            
            current_price = df['Close'].iloc[i]
            
            if signal == 'BUY' and position == 0:
                shares = (balance * 0.95) // current_price  # Use 95% of balance
                if shares > 0:
                    position = shares
                    balance -= shares * current_price
                    trades.append({
                        'date': df.index[i].strftime('%Y-%m-%d'),
                        'type': 'BUY',
                        'price': current_price,
                        'shares': shares,
                        'balance': balance + (position * current_price)
                    })
                    
            elif signal == 'SELL' and position > 0:
                balance += position * current_price
                trades.append({
                    'date': df.index[i].strftime('%Y-%m-%d'),
                    'type': 'SELL',
                    'price': current_price,
                    'shares': position,
                    'balance': balance
                })
                position = 0

        final_balance = balance + (position * df['Close'].iloc[-1])
        return {
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'return_pct': ((final_balance - initial_balance) / initial_balance) * 100,
            'trades': trades
        }

# Create default AI trading service instance
ai_trading_service = AITradingService(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None 