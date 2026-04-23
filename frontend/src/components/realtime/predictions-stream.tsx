'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useRealtimePredictions } from '@/hooks/api/use-realtime';
import { TrendingUp } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

interface PredictionsStreamProps {
  modelId?: string;
  enabled?: boolean;
  title?: string;
}

export function PredictionsStream({ modelId, enabled = true, title = 'Real-time Predictions' }: PredictionsStreamProps) {
  const { predictions, isConnected } = useRealtimePredictions(modelId, enabled);

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) {return 'text-green-600';}
    if (confidence > 0.6) {return 'text-yellow-600';}
    return 'text-red-600';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            {title}
          </span>
          <Badge variant={isConnected ? 'default' : 'secondary'}>
            {isConnected ? 'Live' : 'Offline'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {predictions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-20" />
            <p>Awaiting predictions...</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-2">
              {predictions.map((pred) => (
                <div
                  key={pred.prediction_id}
                  className="rounded-lg border p-3 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-sm">{pred.model_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(pred.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold text-sm ${getConfidenceColor(pred.confidence)}`}>
                        {(pred.confidence * 100).toFixed(1)}%
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {pred.processing_time_ms}ms
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Output: </span>
                      <span className="font-mono">{String(pred.output).substring(0, 20)}</span>
                    </div>
                    {Object.keys(pred.input).length > 0 && (
                      <div>
                        <span className="text-muted-foreground">Inputs: </span>
                        <span className="font-mono">{Object.keys(pred.input).length} features</span>
                      </div>
                    )}
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
