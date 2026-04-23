'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useRealtimeHealth } from '@/hooks/api/use-realtime';
import { Heart } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

export function RealtimeHealthMonitor() {
  const { healthStatus, isConnected } = useRealtimeHealth(true);

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'default';
      case 'degraded':
        return 'secondary';
      case 'unhealthy':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Heart className="h-5 w-5" />
            System Health
          </span>
          <Badge variant={isConnected ? 'default' : 'secondary'}>
            {isConnected ? 'Live' : 'Offline'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {healthStatus.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Heart className="h-12 w-12 mx-auto mb-4 opacity-20" />
            <p>Awaiting health data...</p>
          </div>
        ) : (
          <ScrollArea className="h-75 pr-4">
            <div className="space-y-2">
              {healthStatus.map((component) => (
                <div
                  key={component.component}
                  className="rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{component.component}</p>
                      {component.message && (
                        <p className="text-xs text-muted-foreground mt-1">{component.message}</p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge variant={getStatusVariant(component.status)}>
                        {component.status.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {component.latency_ms}ms
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
