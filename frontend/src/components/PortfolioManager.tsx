import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  profitLoss: number;
}

interface PortfolioStats {
  totalValue: number;
  dailyPnL: number;
  totalPnL: number;
  cashBalance: number;
}

interface PortfolioManagerProps {
  positions: Position[];
  stats: PortfolioStats;
  onCreateOrder: (order: any) => void;
}

const PortfolioManager: React.FC<PortfolioManagerProps> = ({
  positions,
  stats,
  onCreateOrder,
}) => {
  const queryClient = useQueryClient();

  const closePositionMutation = useMutation({
    mutationFn: async (symbol: string) => {
      const response = await fetch('/api/v1/trading/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          side: 'sell',
          type: 'market',
          timeInForce: 'gtc',
        }),
      });
      if (!response.ok) throw new Error('Failed to close position');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Portfolio Statistics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Value</h3>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">
            ${stats.totalValue.toLocaleString()}
          </p>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Daily P&L</h3>
          <p className={`text-lg font-semibold ${
            stats.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            ${stats.dailyPnL.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Positions List */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Symbol</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Quantity</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Avg Price</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Current</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">P&L</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {positions.map((position) => (
              <tr key={position.symbol}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                  {position.symbol}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {position.quantity}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  ${position.averagePrice.toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  ${position.currentPrice.toFixed(2)}
                </td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                  position.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${position.profitLoss.toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  <button
                    onClick={() => closePositionMutation.mutate(position.symbol)}
                    className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300"
                  >
                    Close
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PortfolioManager; 