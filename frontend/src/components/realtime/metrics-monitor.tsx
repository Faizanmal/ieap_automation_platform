'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useRealtimeMetrics } from '@/hooks/api/use-realtime';
import { Activity } from 'lucide-react';

export function RealtimeMetricsMonitor() {
  const { metrics, isConnected } = useRealtimeMetrics(true);

  if (!metrics) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Live Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Badge variant={isConnected ? 'default' : 'secondary'}>
              {isConnected ? 'Connecting...' : 'Disconnected'}
            </Badge>
          </div>
        </CardContent>
      </Card>
    );
  }

  const errorRateColor = metrics.error_rate > 5 ? 'text-red-500' : metrics.error_rate > 2 ? 'text-yellow-500' : 'text-green-500';
  const latencyColor = metrics.avg_latency_ms > 1000 ? 'text-red-500' : metrics.avg_latency_ms > 500 ? 'text-yellow-500' : 'text-green-500';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Live Metrics
          </span>
          <Badge variant="default">
            {isConnected ? 'Live' : 'Offline'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Requests/min</p>
            <p className="text-2xl font-bold">{Math.round(metrics.requests_per_minute)}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Error Rate</p>
            <p className={`text-2xl font-bold ${errorRateColor}`}>{metrics.error_rate.toFixed(2)}%</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Avg Latency</p>
            <p className={`text-2xl font-bold ${latencyColor}`}>{Math.round(metrics.avg_latency_ms)}ms</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Active Connections</p>
            <p className="text-2xl font-bold">{metrics.active_connections}</p>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-4">
          Updated: {new Date(metrics.timestamp).toLocaleTimeString()}
        </p>
      </CardContent>
    </Card>
  );
}
