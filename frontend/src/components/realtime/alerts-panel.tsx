'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useRealtimeAlerts } from '@/hooks/api/use-realtime';
import { Bell, Trash2, AlertTriangle } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

export function RealtimeAlertsPanel() {
  const { alerts, isConnected, clearAlerts } = useRealtimeAlerts(true);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'text-red-600 bg-red-50';
      case 'error':
        return 'text-red-500 bg-red-50';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50';
      case 'info':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getLevelBadgeVariant = (level: string) => {
    switch (level) {
      case 'critical':
      case 'error':
        return 'destructive';
      case 'warning':
        return 'secondary';
      default:
        return 'default';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Real-time Alerts
          </CardTitle>
          <div className="flex gap-2">
            <Badge variant={isConnected ? 'default' : 'secondary'}>
              {isConnected ? 'Live' : 'Offline'}
            </Badge>
            {alerts.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAlerts}
                className="h-6 gap-1"
              >
                <Trash2 className="h-4 w-4" />
                Clear
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <Bell className="h-12 w-12 mx-auto mb-4 opacity-20" />
            <p>No alerts</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`rounded-lg border p-3 ${getLevelColor(alert.level)}`}
                >
                  <div className="flex items-start gap-3">
                    {alert.level === 'critical' || alert.level === 'error' ? (
                      <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                    ) : (
                      <Bell className="h-5 w-5 flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-sm truncate">{alert.title}</h4>
                        <Badge variant={getLevelBadgeVariant(alert.level)} className="text-xs">
                          {alert.level.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-xs mb-1">{alert.message}</p>
                      <div className="flex gap-2 text-xs opacity-70">
                        <span>{alert.source}</span>
                        <span>•</span>
                        <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                      </div>
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
