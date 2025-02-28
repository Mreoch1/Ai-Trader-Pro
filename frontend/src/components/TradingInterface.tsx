import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import TradingDashboard from './TradingDashboard';
import PortfolioManager from './PortfolioManager';
import { useWebSocket } from '../hooks/useWebSocket';

interface Order {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  quantity: number;
  price?: number;
}

interface TradingInterfaceProps {
  userId: string;
}

const TradingInterface: React.FC<TradingInterfaceProps> = ({ userId }) => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const queryClient = useQueryClient();
  const { data: marketData, isConnected } = useWebSocket('market_data');

  // Fetch portfolio data
  const { data: portfolio, isLoading: isPortfolioLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trading/portfolio');
      if (!response.ok) throw new Error('Failed to fetch portfolio');
      return response.json();
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Fetch positions
  const { data: positions, isLoading: isPositionsLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trading/positions');
      if (!response.ok) throw new Error('Failed to fetch positions');
      return response.json();
    },
    refetchInterval: 5000,
  });

  // Create order mutation
  const createOrderMutation = useMutation({
    mutationFn: async (order: Order) => {
      const response = await fetch('/api/v1/trading/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(order),
      });
      if (!response.ok) throw new Error('Failed to create order');
      return response.json();
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    },
  });

  // Analyze symbol mutation
  const analyzeSymbolMutation = useMutation({
    mutationFn: async (symbol: string) => {
      const response = await fetch(`/api/v1/trading/analyze/${symbol}`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to analyze symbol');
      return response.json();
    },
  });

  const handleCreateOrder = async (order: Order) => {
    try {
      await createOrderMutation.mutateAsync(order);
    } catch (error) {
      console.error('Error creating order:', error);
    }
  };

  const handleAnalyzeSymbol = async (symbol: string) => {
    try {
      const analysis = await analyzeSymbolMutation.mutateAsync(symbol);
      // Handle the analysis results (e.g., show in UI)
      console.log('Analysis:', analysis);
    } catch (error) {
      console.error('Error analyzing symbol:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm py-4 px-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Trader Pro</h1>
          <div className="flex items-center space-x-4">
            <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600 dark:text-gray-300">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-12 gap-6">
          {/* Trading Dashboard */}
          <div className="col-span-8">
            <TradingDashboard
              userId={userId}
              onSymbolSelect={setSelectedSymbol}
              selectedSymbol={selectedSymbol}
            />
          </div>

          {/* Portfolio and Order Management */}
          <div className="col-span-4 space-y-6">
            {/* Portfolio Summary */}
            {!isPortfolioLoading && portfolio && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                  Portfolio Summary
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Total Equity</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      ${portfolio.equity.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Buying Power</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      ${portfolio.buying_power.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Positions */}
            {!isPositionsLoading && positions && (
              <PortfolioManager
                positions={positions}
                stats={portfolio}
                onCreateOrder={handleCreateOrder}
              />
            )}

            {/* Trading Actions */}
            {selectedSymbol && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
                  Trading Actions
                </h2>
                <div className="space-y-4">
                  <button
                    onClick={() => handleAnalyzeSymbol(selectedSymbol)}
                    className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg"
                  >
                    Analyze {selectedSymbol}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default TradingInterface; 