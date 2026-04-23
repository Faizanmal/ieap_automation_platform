'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { WSMessage, WSChannel, WSMessageType } from '@/types/api';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  channels?: WSChannel[];
  onMessage?: (message: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    channels = [],
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const connectRef = useRef<() => void>(() => { });

  const connect = useCallback(() => {
    const channelParams = channels.length > 0 ? `?channels=${channels.join(',')}` : '';
    const ws = new WebSocket(`${WS_URL}/ws${channelParams}`);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;
      onConnect?.();
    };

    ws.onclose = () => {
      setIsConnected(false);
      onDisconnect?.();

      if (autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++;
          connectRef.current();
        }, reconnectInterval);
      }
    };

    ws.onerror = (error) => {
      onError?.(error);
    };

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        setLastMessage(message);
        onMessage?.(message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    wsRef.current = ws;
  }, [channels, onConnect, onDisconnect, onError, onMessage, autoReconnect, reconnectInterval, maxReconnectAttempts]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((type: WSMessageType, channel?: WSChannel, data?: Record<string, unknown>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type,
        channel,
        data: data || {},
        timestamp: new Date().toISOString(),
        message_id: crypto.randomUUID(),
      }));
    }
  }, []);

  const subscribe = useCallback((channel: WSChannel) => {
    send('subscribe', channel);
  }, [send]);

  const unsubscribe = useCallback((channel: WSChannel) => {
    send('unsubscribe', channel);
  }, [send]);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    send,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  };
}
