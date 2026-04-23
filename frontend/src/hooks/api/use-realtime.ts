import { useEffect, useState, useCallback } from 'react';
import { useWebSocket } from '../use-websocket';
import type { WSMessage } from '@/types/api';

// Real-time metrics data
export interface RealtimeMetrics {
  timestamp: string;
  requests_per_minute: number;
  error_rate: number;
  avg_latency_ms: number;
  active_connections: number;
}

// Real-time alerts
export interface RealtimeAlert {
  id: string;
  level: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  source: string;
}

// Real-time predictions
export interface RealtimePrediction {
  prediction_id: string;
  model_id: string;
  timestamp: string;
  input: Record<string, unknown>;
  output: number | string;
  confidence: number;
  processing_time_ms: number;
}

// Real-time health status
export interface RealtimeHealth {
  component: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms: number;
  last_check: string;
  message?: string;
}

function parseRealtimeAlertLevel(value: unknown): RealtimeAlert['level'] {
  if (value === 'info' || value === 'warning' || value === 'error' || value === 'critical') {
    return value;
  }
  return 'info';
}

function parseRealtimeHealthStatus(value: unknown): RealtimeHealth['status'] {
  if (value === 'healthy' || value === 'degraded' || value === 'unhealthy') {
    return value;
  }
  return 'healthy';
}

function parseString(value: unknown, defaultValue: string = ''): string {
  return typeof value === 'string' ? value : defaultValue;
}

function parseNumber(value: unknown, defaultValue: number = 0): number {
  return typeof value === 'number' && !isNaN(value) ? value : defaultValue;
}

function parseOutput(value: unknown): number | string {
  if (typeof value === 'number') {return value;}
  if (typeof value === 'string') {return value;}
  return 0;
}

function parseRecord(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

export function useRealtimeMetrics(enabled = true) {
  const [metrics, setMetrics] = useState<RealtimeMetrics | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const handleMessage = useCallback((message: WSMessage) => {
    if (message.channel === 'metrics' && message.data) {
      setMetrics({
        timestamp: parseString(message.data.timestamp, new Date().toISOString()),
        requests_per_minute: parseNumber(message.data.requests_per_minute),
        error_rate: parseNumber(message.data.error_rate),
        avg_latency_ms: parseNumber(message.data.avg_latency_ms),
        active_connections: parseNumber(message.data.active_connections),
      });
    }
  }, []);

  const { isConnected: wsConnected, subscribe, unsubscribe } = useWebSocket({
    channels: enabled ? ['metrics'] : [],
    onMessage: handleMessage,
    onConnect: () => setIsConnected(true),
    onDisconnect: () => setIsConnected(false),
  });

  useEffect(() => {
    if (enabled && wsConnected) {
      subscribe('metrics');
    } else if (!enabled && wsConnected) {
      unsubscribe('metrics');
    }
  }, [enabled, wsConnected, subscribe, unsubscribe]);

  return { metrics, isConnected };
}

export function useRealtimeAlerts(enabled = true) {
  const [alerts, setAlerts] = useState<RealtimeAlert[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const handleMessage = useCallback((message: WSMessage) => {
    if (message.channel === 'alerts' && message.data) {
      const alert: RealtimeAlert = {
        id: parseString(message.data.id, crypto.randomUUID()),
        level: parseRealtimeAlertLevel(message.data.level),
        title: parseString(message.data.title, 'Alert'),
        message: parseString(message.data.message),
        timestamp: parseString(message.data.timestamp, new Date().toISOString()),
        source: parseString(message.data.source, 'system'),
      };
      setAlerts(prev => [alert, ...prev].slice(0, 100)); // Keep last 100 alerts
    }
  }, []);

  const { isConnected: wsConnected, subscribe, unsubscribe } = useWebSocket({
    channels: enabled ? ['alerts'] : [],
    onMessage: handleMessage,
    onConnect: () => setIsConnected(true),
    onDisconnect: () => setIsConnected(false),
  });

  useEffect(() => {
    if (enabled && wsConnected) {
      subscribe('alerts');
    } else if (!enabled && wsConnected) {
      unsubscribe('alerts');
    }
  }, [enabled, wsConnected, subscribe, unsubscribe]);

  const clearAlerts = useCallback(() => setAlerts([]), []);

  return { alerts, isConnected, clearAlerts };
}

export function useRealtimePredictions(modelId?: string, enabled = true) {
  const [predictions, setPredictions] = useState<RealtimePrediction[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const handleMessage = useCallback((message: WSMessage) => {
    if (message.channel === 'predictions' && message.data) {
      const pred: RealtimePrediction = {
        prediction_id: parseString(message.data.prediction_id, crypto.randomUUID()),
        model_id: parseString(message.data.model_id, modelId || 'unknown'),
        timestamp: parseString(message.data.timestamp, new Date().toISOString()),
        input: parseRecord(message.data.input),
        output: parseOutput(message.data.output),
        confidence: parseNumber(message.data.confidence),
        processing_time_ms: parseNumber(message.data.processing_time_ms),
      };
      setPredictions(prev => [pred, ...prev].slice(0, 50)); // Keep last 50 predictions
    }
  }, [modelId]);

  const { isConnected: wsConnected, subscribe, unsubscribe } = useWebSocket({
    channels: enabled ? ['predictions'] : [],
    onMessage: handleMessage,
    onConnect: () => setIsConnected(true),
    onDisconnect: () => setIsConnected(false),
  });

  useEffect(() => {
    if (enabled && wsConnected) {
      subscribe('predictions');
    } else if (!enabled && wsConnected) {
      unsubscribe('predictions');
    }
  }, [enabled, wsConnected, subscribe, unsubscribe]);

  return { predictions, isConnected };
}

export function useRealtimeHealth(enabled = true) {
  const [healthStatus, setHealthStatus] = useState<RealtimeHealth[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const handleMessage = useCallback((message: WSMessage) => {
    if (message.channel === 'health' && message.data) {
      const health: RealtimeHealth = {
        component: parseString(message.data.component, 'unknown'),
        status: parseRealtimeHealthStatus(message.data.status),
        latency_ms: parseNumber(message.data.latency_ms),
        last_check: parseString(message.data.last_check, new Date().toISOString()),
        message: parseString(message.data.message),
      };
      setHealthStatus(prev => {
        const updated = prev.filter(h => h.component !== health.component);
        return [health, ...updated];
      });
    }
  }, []);

  const { isConnected: wsConnected, subscribe, unsubscribe } = useWebSocket({
    channels: enabled ? ['health'] : [],
    onMessage: handleMessage,
    onConnect: () => setIsConnected(true),
    onDisconnect: () => setIsConnected(false),
  });

  useEffect(() => {
    if (enabled && wsConnected) {
      subscribe('health');
    } else if (!enabled && wsConnected) {
      unsubscribe('health');
    }
  }, [enabled, wsConnected, subscribe, unsubscribe]);

  return { healthStatus, isConnected };
}
