import React, { createContext, useContext, useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { useWebSocket, MarketData, WebSocketMessage } from '../hooks/useWebSocket';

interface MarketDataContextType {
  marketData: Record<string, MarketData>;
  subscribedSymbols: Set<string>;
  subscribe: (symbols: string[]) => void;
  unsubscribe: (symbols: string[]) => void;
  isConnected: boolean;
  error: string | null;
}

const MarketDataContext = createContext<MarketDataContextType | undefined>(undefined);

export const useMarketData = () => {
  const context = useContext(MarketDataContext);
  if (!context) {
    throw new Error('useMarketData must be used within a MarketDataProvider');
  }
  return context;
};

export const MarketDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [marketData, setMarketData] = useState<Record<string, MarketData>>({});
  const [subscribedSymbols, setSubscribedSymbols] = useState<Set<string>>(new Set());
  
  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'market_data' && message.symbol && message.data) {
      setMarketData(prev => ({
        ...prev,
        [message.symbol]: message.data,
      }));
    }
  }, []);

  const { isConnected, error, subscribe: wsSubscribe, unsubscribe: wsUnsubscribe } = useWebSocket(
    uuidv4(),
    {
      onMessage: handleMessage,
      autoReconnect: true,
      reconnectAttempts: 5,
      reconnectInterval: 5000,
    }
  );

  const subscribe = useCallback((symbols: string[]) => {
    setSubscribedSymbols(prev => {
      const newSymbols = new Set(prev);
      symbols.forEach(symbol => newSymbols.add(symbol));
      return newSymbols;
    });
    wsSubscribe(symbols);
  }, [wsSubscribe]);

  const unsubscribe = useCallback((symbols: string[]) => {
    setSubscribedSymbols(prev => {
      const newSymbols = new Set(prev);
      symbols.forEach(symbol => newSymbols.delete(symbol));
      return newSymbols;
    });
    wsUnsubscribe(symbols);
  }, [wsUnsubscribe]);

  return (
    <MarketDataContext.Provider
      value={{
        marketData,
        subscribedSymbols,
        subscribe,
        unsubscribe,
        isConnected,
        error,
      }}
    >
      {children}
    </MarketDataContext.Provider>
  );
}; 