import React, { useEffect } from 'react';
import { useMarketData } from '../contexts/MarketDataContext';

interface MarketDataDisplayProps {
  symbols: string[];
  onSymbolClick?: (symbol: string) => void;
}

export const MarketDataDisplay: React.FC<MarketDataDisplayProps> = ({
  symbols,
  onSymbolClick,
}) => {
  const { marketData, subscribedSymbols, subscribe, unsubscribe, isConnected, error } = useMarketData();

  useEffect(() => {
    // Subscribe to symbols that aren't already subscribed
    const newSymbols = symbols.filter(symbol => !subscribedSymbols.has(symbol));
    if (newSymbols.length > 0) {
      subscribe(newSymbols);
    }

    // Unsubscribe from symbols that are no longer needed
    const removeSymbols = Array.from(subscribedSymbols)
      .filter(symbol => !symbols.includes(symbol));
    if (removeSymbols.length > 0) {
      unsubscribe(removeSymbols);
    }
  }, [symbols, subscribedSymbols, subscribe, unsubscribe]);

  if (error) {
    return (
      <div className="p-4 bg-red-100 text-red-700 rounded-lg">
        Error: {error}
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="p-4 bg-yellow-100 text-yellow-700 rounded-lg">
        Connecting to market data...
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {symbols.map(symbol => {
        const data = marketData[symbol];
        const isPositive = data?.change >= 0;

        return (
          <div
            key={symbol}
            onClick={() => onSymbolClick?.(symbol)}
            className={`
              p-4 rounded-lg shadow-lg cursor-pointer
              transition-transform duration-200 hover:scale-105
              ${data ? 'bg-white dark:bg-gray-800' : 'bg-gray-100 dark:bg-gray-700'}
            `}
          >
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-lg font-semibold">{symbol}</h3>
              {data && (
                <span
                  className={`px-2 py-1 rounded text-sm font-medium
                    ${isPositive ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100'
                                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'}`}
                >
                  {isPositive ? '▲' : '▼'} {Math.abs(data.change_percent).toFixed(2)}%
                </span>
              )}
            </div>

            {data ? (
              <>
                <div className="text-2xl font-bold mb-2">
                  ${data.price.toFixed(2)}
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Change:</span>
                    <span className={isPositive ? 'text-green-600 dark:text-green-400'
                                               : 'text-red-600 dark:text-red-400'}>
                      {' '}{isPositive ? '+' : ''}{data.change.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Volume:</span>
                    <span className="ml-1">{data.volume.toLocaleString()}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-500 dark:text-gray-400">Last Update:</span>
                    <span className="ml-1">
                      {new Date(data.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </>
            ) : (
              <div className="animate-pulse">
                <div className="h-8 bg-gray-200 dark:bg-gray-600 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-2/3"></div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}; 