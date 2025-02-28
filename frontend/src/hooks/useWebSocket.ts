import { useState, useEffect, useCallback, useRef } from 'react';

export interface MarketData {
  price: number;
  timestamp: string;
  volume: number;
  change: number;
  change_percent: number;
}

export interface WebSocketMessage {
  type: string;
  symbol?: string;
  data?: MarketData;
  status?: string;
  client_id?: string;
  message?: string;
}

export interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  autoReconnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

// Get the WebSocket URL from environment variables
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = API_URL.replace('http', 'ws');

export const useWebSocket = (clientId: string, options: UseWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number>();

  const {
    onMessage,
    onConnect,
    onDisconnect,
    autoReconnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 5000,
  } = options;

  const connect = useCallback(() => {
    try {
      console.log(`Connecting to WebSocket at ${WS_URL}/api/v1/ws/${clientId}`);
      const ws = new WebSocket(`${WS_URL}/api/v1/ws/${clientId}`);

      ws.onopen = () => {
        console.log('WebSocket connection established');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('Received WebSocket message:', message);
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event);
        setIsConnected(false);
        onDisconnect?.();

        if (autoReconnect && reconnectAttemptsRef.current < reconnectAttempts) {
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current + 1}/${reconnectAttempts})...`);
          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (event) => {
        const errorMsg = 'WebSocket error occurred';
        console.error(errorMsg, event);
        setError(errorMsg);
      };

      wsRef.current = ws;
    } catch (err) {
      const errorMsg = 'Failed to establish WebSocket connection';
      setError(errorMsg);
      console.error(errorMsg, err);
    }
  }, [clientId, onMessage, onConnect, onDisconnect, autoReconnect, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      console.log('Disconnecting WebSocket');
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
  }, []);

  const subscribe = useCallback((symbols: string[]) => {
    if (wsRef.current && isConnected) {
      console.log('Subscribing to symbols:', symbols);
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        symbols,
      }));
    } else {
      console.warn('Cannot subscribe: WebSocket is not connected');
    }
  }, [isConnected]);

  const unsubscribe = useCallback((symbols: string[]) => {
    if (wsRef.current && isConnected) {
      console.log('Unsubscribing from symbols:', symbols);
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        symbols,
      }));
    } else {
      console.warn('Cannot unsubscribe: WebSocket is not connected');
    }
  }, [isConnected]);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    error,
    subscribe,
    unsubscribe,
  };
}; 