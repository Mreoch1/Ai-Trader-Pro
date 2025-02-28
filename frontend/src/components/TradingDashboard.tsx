import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWebSocket } from '../hooks/useWebSocket';
import MarketDataDisplay from './MarketDataDisplay';
import OrderForm from './OrderForm';

interface TradingDashboardProps {
  userId: string;
  onSymbolSelect?: (symbol: string) => void;
  selectedSymbol?: string;
}

const TradingDashboard: React.FC<TradingDashboardProps> = ({
  userId,
  onSymbolSelect,
  selectedSymbol = 'AAPL', // Default to AAPL if no symbol is selected
}) => {
  const [showOrderForm, setShowOrderForm] = useState(false);
  const { data: marketData, isConnected } = useWebSocket('market_data');
  
  const { data: portfolio, isLoading: isPortfolioLoading } = useQuery({
    queryKey: ['portfolio', userId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/trading/portfolio/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch portfolio');
      return response.json();
    },
  });

  // Fetch symbol analysis
  const { data: analysis, isLoading: isAnalysisLoading } = useQuery({
    queryKey: ['analysis', selectedSymbol],
    queryFn: async () => {
      const response = await fetch(`/api/v1/trading/analyze/${selectedSymbol}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to analyze symbol');
      return response.json();
    },
    enabled: !!selectedSymbol,
  });

  const handleSymbolSearch = (symbol: string) => {
    onSymbolSelect?.(symbol.toUpperCase());
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm py-4 px-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Trading Dashboard</h1>
          <div className="flex items-center space-x-4">
            <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600 dark:text-gray-300">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Symbol Search */}
        <div className="mt-4 flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Enter symbol (e.g., AAPL)"
              value={selectedSymbol}
              onChange={(e) => handleSymbolSearch(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button
            onClick={() => setShowOrderForm(!showOrderForm)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            {showOrderForm ? 'Hide Order Form' : 'New Order'}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 p-6 grid grid-cols-12 gap-6">
        {/* Market Data Section */}
        <div className={`${showOrderForm ? 'col-span-8' : 'col-span-12'} bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4`}>
          <MarketDataDisplay data={marketData?.[selectedSymbol]} />

          {/* Analysis Section */}
          {!isAnalysisLoading && analysis && (
            <div className="mt-6 bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                AI Analysis
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Market Sentiment
                  </h4>
                  <p className="text-gray-900 dark:text-white">
                    {analysis.market_sentiment}
                  </p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Recommendation
                  </h4>
                  <p className={`font-semibold ${
                    analysis.recommendation === 'buy' ? 'text-green-600' :
                    analysis.recommendation === 'sell' ? 'text-red-600' :
                    'text-gray-600'
                  }`}>
                    {analysis.recommendation.toUpperCase()}
                  </p>
                </div>
                <div className="col-span-2">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Analysis
                  </h4>
                  <p className="text-gray-900 dark:text-white">
                    {analysis.technical_analysis}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Order Form Section */}
        {showOrderForm && (
          <div className="col-span-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Place Order
            </h2>
            {!isPortfolioLoading && portfolio && marketData?.[selectedSymbol] && (
              <OrderForm
                symbol={selectedSymbol}
                currentPrice={marketData[selectedSymbol].price}
                availableFunds={portfolio.buying_power}
                onOrderSubmit={() => setShowOrderForm(false)}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingDashboard; 