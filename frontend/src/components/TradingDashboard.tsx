import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWebSocket } from '../hooks/useWebSocket';
import MarketDataDisplay from './MarketDataDisplay';

interface TradingDashboardProps {
  userId: string;
}

const TradingDashboard: React.FC<TradingDashboardProps> = ({ userId }) => {
  const { data: marketData, isConnected } = useWebSocket('market_data');
  
  const { data: portfolio, isLoading: isPortfolioLoading } = useQuery({
    queryKey: ['portfolio', userId],
    queryFn: async () => {
      const response = await fetch(`/api/v1/trading/portfolio/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch portfolio');
      return response.json();
    },
  });

  return (
    <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm py-4 px-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Trading Dashboard</h1>
        <div className="flex items-center space-x-4">
          <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600 dark:text-gray-300">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 p-6 grid grid-cols-12 gap-6">
        {/* Market Data Section */}
        <div className="col-span-8 bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
          <MarketDataDisplay data={marketData} />
        </div>

        {/* Portfolio Section */}
        <div className="col-span-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Portfolio</h2>
          {isPortfolioLoading ? (
            <div className="animate-pulse">Loading portfolio...</div>
          ) : (
            <div className="space-y-4">
              {/* Portfolio summary will be implemented here */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TradingDashboard; 