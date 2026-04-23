'use client';

import { PageHeader } from '@/components/layout/page-header';
import { RealtimeMetricsMonitor } from '@/components/realtime/metrics-monitor';
import { RealtimeAlertsPanel } from '@/components/realtime/alerts-panel';
import { RealtimeHealthMonitor } from '@/components/realtime/health-monitor';
import { PredictionsStream } from '@/components/realtime/predictions-stream';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, Bell, Heart, TrendingUp } from 'lucide-react';

export default function RealtimePage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Real-time Monitoring"
        description="Live system metrics, alerts, health status, and predictions"
      />

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Activity className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="alerts" className="gap-2">
            <Bell className="h-4 w-4" />
            Alerts
          </TabsTrigger>
          <TabsTrigger value="health" className="gap-2">
            <Heart className="h-4 w-4" />
            Health
          </TabsTrigger>
          <TabsTrigger value="predictions" className="gap-2">
            <TrendingUp className="h-4 w-4" />
            Predictions
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <RealtimeMetricsMonitor />
          <RealtimeAlertsPanel />
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <RealtimeAlertsPanel />
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <RealtimeHealthMonitor />
        </TabsContent>

        <TabsContent value="predictions" className="space-y-4">
          <PredictionsStream />
        </TabsContent>
      </Tabs>
    </div>
  );
}
