"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  Settings,
  RefreshCw,
  Server,
  Database,
  HardDrive,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Activity,
  Clock,
  Zap,
  Bell,
  Loader2,
  Wrench,
} from "lucide-react";
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import { formatRelativeTime } from "@/lib/utils";

// Constants for magic numbers
const ONE_HOUR_MS = 3600000;
const TWO_HOURS_MS = 7200000;
const SECONDS_IN_DAY = 86400;
const MOCK_REQUESTS_PER_MIN = 1247;
const MOCK_CPU_USAGE = 45;
const MOCK_MEMORY_USAGE = 62;
const MOCK_DISK_USAGE = 38;

export default function AdminDashboardPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("overview");

  // Fetch admin dashboard
  const { data: dashboard, isLoading, refetch } = useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: adminApi.getDashboard,
    refetchInterval: 30000,
  });

  // Fetch system info
  const { data: systemInfo } = useQuery({
    queryKey: ["admin", "system-info"],
    queryFn: adminApi.getSystemInfo,
  });

  // Fetch maintenance status
  const { data: maintenanceStatus } = useQuery({
    queryKey: ["admin", "maintenance"],
    queryFn: adminApi.getMaintenanceStatus,
  });

  // Fetch services status
  const { data: services } = useQuery({
    queryKey: ["admin", "services"],
    queryFn: adminApi.getServicesStatus,
  });

  // Toggle maintenance mode
  const maintenanceMutation = useMutation({
    mutationFn: (enable: boolean) =>
      enable
        ? adminApi.enableMaintenanceMode({ mode: "soft", message: "System is under maintenance" })
        : adminApi.disableMaintenanceMode(),
    onSuccess: (_, enable) => {
      toast.success(enable ? "Maintenance mode enabled" : "Maintenance mode disabled");
      queryClient.invalidateQueries({ queryKey: ["admin", "maintenance"] });
    },
    onError: () => {
      toast.error("Failed to toggle maintenance mode");
    },
  });

  // Clear cache mutation
  const clearCacheMutation = useMutation({
    mutationFn: () => adminApi.clearCache(),
    onSuccess: () => {
      toast.success("Cache cleared successfully");
    },
    onError: () => {
      toast.error("Failed to clear cache");
    },
  });

  // Mock performance data
  const performanceData = [
    { time: "00:00", requests: 120, latency: 45, errors: 2 },
    { time: "04:00", requests: 80, latency: 38, errors: 1 },
    { time: "08:00", requests: 350, latency: 52, errors: 5 },
    { time: "12:00", requests: 520, latency: 65, errors: 8 },
    { time: "16:00", requests: 480, latency: 58, errors: 6 },
    { time: "20:00", requests: 280, latency: 48, errors: 3 },
  ];

  // Use state for mock data to ensure purity
  const [now] = useState(new Date());

  const alerts = useMemo(() => dashboard?.alerts || [
    { severity: "warning", message: "High memory usage detected", timestamp: now.toISOString() },
    { severity: "info", message: "Scheduled backup completed", timestamp: new Date(now.getTime() - ONE_HOUR_MS).toISOString() },
    { severity: "error", message: "Failed to connect to external API", timestamp: new Date(now.getTime() - TWO_HOURS_MS).toISOString() },
  ], [dashboard?.alerts, now]);

  const mockServices = useMemo(() => [
    { name: "API Gateway", status: "healthy", uptime: 99.99, last_check: new Date().toISOString() },
    { name: "Database", status: "healthy", uptime: 99.95, last_check: new Date().toISOString() },
    { name: "Cache (Redis)", status: "healthy", uptime: 99.98, last_check: new Date().toISOString() },
    { name: "ML Service", status: "healthy", uptime: 99.92, last_check: new Date().toISOString() },
    { name: "Task Queue", status: "degraded", uptime: 98.5, last_check: new Date().toISOString() },
    { name: "WebSocket", status: "healthy", uptime: 99.99, last_check: new Date().toISOString() },
  ], []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "degraded":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case "unhealthy":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-green-500";
      case "degraded":
        return "bg-yellow-500";
      case "unhealthy":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case "error":
        return <XCircle className="h-5 w-5 text-red-500" />;
      case "warning":
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <Bell className="h-5 w-5 text-blue-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground">
            System administration and monitoring
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Maintenance Mode Banner */}
      {maintenanceStatus?.enabled && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Wrench className="h-5 w-5 text-yellow-500" />
            <div>
              <p className="font-medium text-yellow-700">Maintenance Mode Active</p>
              <p className="text-sm text-yellow-600">{maintenanceStatus.message}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => maintenanceMutation.mutate(false)}
            disabled={maintenanceMutation.isPending}
          >
            {maintenanceMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Disable"
            )}
          </Button>
        </div>
      )}

      {/* System Status Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              <div className="flex items-center gap-2">
                {getStatusIcon(dashboard?.status || "healthy")}
                <span className="text-2xl font-bold capitalize">
                  {dashboard?.status || "Healthy"}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboard?.metrics?.uptime_seconds
                ? `${Math.floor(dashboard.metrics.uptime_seconds / SECONDS_IN_DAY)}d`
                : "99.9%"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Last 30 days</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Requests/min</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboard?.metrics?.requests_per_minute?.toLocaleString() || MOCK_REQUESTS_PER_MIN}
            </div>
            <p className="text-xs text-green-600 mt-1">+12% from last hour</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboard?.metrics?.error_rate?.toFixed(2) || "0.5"}%
            </div>
            <p className="text-xs text-green-600 mt-1">Below threshold</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="operations">Operations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 mt-4">
          {/* Resource Usage */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <Progress value={dashboard?.metrics?.cpu_usage || MOCK_CPU_USAGE} className="flex-1" />
                  <span className="text-sm font-medium">{dashboard?.metrics?.cpu_usage || MOCK_CPU_USAGE}%</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <Progress value={dashboard?.metrics?.memory_usage || MOCK_MEMORY_USAGE} className="flex-1" />
                  <span className="text-sm font-medium">{dashboard?.metrics?.memory_usage || MOCK_MEMORY_USAGE}%</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                  <Progress value={dashboard?.metrics?.disk_usage || MOCK_DISK_USAGE} className="flex-1" />
                  <span className="text-sm font-medium">{dashboard?.metrics?.disk_usage || MOCK_DISK_USAGE}%</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Performance Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Request Performance</CardTitle>
              <CardDescription>Request volume and latency over time</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="time" className="text-xs" />
                    <YAxis yAxisId="left" className="text-xs" />
                    <YAxis yAxisId="right" orientation="right" className="text-xs" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--background))",
                        border: "1px solid hsl(var(--border))",
                      }}
                    />
                    <Area
                      yAxisId="left"
                      type="monotone"
                      dataKey="requests"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.2}
                      name="Requests"
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="latency"
                      stroke="#f97316"
                      strokeWidth={2}
                      dot={false}
                      name="Latency (ms)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Recent Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts</CardTitle>
              <CardDescription>System alerts and notifications</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alerts.map((alert: Record<string, unknown>, i: number) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 p-3 rounded-lg border"
                  >
                    {getAlertIcon(alert.severity as string)}
                    <div className="flex-1">
                      <p className="text-sm">{alert.message as string}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatRelativeTime(alert.timestamp as string)}
                      </p>
                    </div>
                    <Badge
                      variant={(alert.severity as string) === "error" ? "destructive" : "outline"}
                    >
                      {alert.severity as string}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="space-y-4 mt-4">
          {/* Services Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {(services || mockServices).map((service) => (
              <Card key={service.name}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">{service.name}</CardTitle>
                    {getStatusIcon(service.status)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <Badge variant="outline" className={`${getStatusColor(service.status)} bg-opacity-10`}>
                        {service.status}
                      </Badge>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Uptime</span>
                      <span className="font-medium">{service.uptime}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Last Check</span>
                      <span>{formatRelativeTime(service.last_check)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="operations" className="space-y-4 mt-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Maintenance Mode */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wrench className="h-5 w-5" />
                  Maintenance Mode
                </CardTitle>
                <CardDescription>
                  Enable maintenance mode to prevent user access during updates
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Enable Maintenance</Label>
                    <p className="text-sm text-muted-foreground">
                      Users will see maintenance page
                    </p>
                  </div>
                  <Switch
                    checked={maintenanceStatus?.enabled || false}
                    onCheckedChange={(checked) => maintenanceMutation.mutate(checked)}
                    disabled={maintenanceMutation.isPending}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Cache Management */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HardDrive className="h-5 w-5" />
                  Cache Management
                </CardTitle>
                <CardDescription>
                  Clear application cache to refresh data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  variant="outline"
                  onClick={() => clearCacheMutation.mutate()}
                  disabled={clearCacheMutation.isPending}
                >
                  {clearCacheMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Clearing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Clear All Cache
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Database */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Database Operations
                </CardTitle>
                <CardDescription>
                  Database maintenance and migrations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    Run Vacuum
                  </Button>
                  <Button variant="outline" size="sm">
                    Check Migrations
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* System Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  System Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Version</span>
                    <span className="font-mono">{(systemInfo?.version as string) || "1.0.0"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Environment</span>
                    <Badge variant="outline">{(systemInfo?.environment as string) || "production"}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Python</span>
                    <span className="font-mono">{(systemInfo?.python_version as string) || "3.11.0"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Hostname</span>
                    <span className="font-mono">{(systemInfo?.hostname as string) || "ieap-prod-01"}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
