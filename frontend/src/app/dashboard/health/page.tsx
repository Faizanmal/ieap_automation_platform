"use client";

import { useQuery } from "@tanstack/react-query";
import { healthApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Server,
  Database,
  Cpu,
  HardDrive,
  Wifi,
  Activity,
  Zap,
  Shield,
  Globe,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

// Constants for magic numbers
const HEALTH_CHECK_INTERVAL_MS = 10000;
const MOCK_PERCENT_100 = 100;

const getStatusMessage = (status: string) => {
  switch (status) {
    case "healthy":
      return "All systems are operational";
    case "degraded":
      return "Some services are experiencing issues";
    default:
      return "Critical services are down";
  }
};

export default function HealthPage() {
  // Fetch health status
  const { data: health, isLoading: healthLoading, refetch } = useQuery({
    queryKey: ["health", "detailed"],
    queryFn: healthApi.checkDetailed,
    refetchInterval: HEALTH_CHECK_INTERVAL_MS, // Refresh every 10 seconds
  });

  // Fetch readiness
  const { data: readiness } = useQuery({
    queryKey: ["health", "readiness"],
    queryFn: healthApi.checkReadiness,
    refetchInterval: 15000,
  });

  // Fetch liveness
  const { data: liveness } = useQuery({
    queryKey: ["health", "liveness"],
    queryFn: healthApi.checkLiveness,
    refetchInterval: 15000,
  });

  // Mock metrics data
  const cpuHistory = [
    { time: "5m ago", value: 35 },
    { time: "4m ago", value: 42 },
    { time: "3m ago", value: 38 },
    { time: "2m ago", value: 55 },
    { time: "1m ago", value: 48 },
    { time: "Now", value: 45 },
  ];

  const memoryHistory = [
    { time: "5m ago", value: 58 },
    { time: "4m ago", value: 60 },
    { time: "3m ago", value: 62 },
    { time: "2m ago", value: 61 },
    { time: "1m ago", value: 63 },
    { time: "Now", value: 62 },
  ];

  const requestHistory = [
    { time: "5m ago", requests: 120, latency: 42 },
    { time: "4m ago", requests: 135, latency: 38 },
    { time: "3m ago", requests: 145, latency: 45 },
    { time: "2m ago", requests: 160, latency: 52 },
    { time: "1m ago", requests: 155, latency: 48 },
    { time: "Now", requests: 148, latency: 44 },
  ];

  const services = [
    {
      name: "API Server",
      status: "healthy",
      uptime: "99.99%",
      latency: "42ms",
      icon: Globe,
    },
    {
      name: "Database",
      status: "healthy",
      uptime: "99.95%",
      latency: "12ms",
      icon: Database,
    },
    {
      name: "Redis Cache",
      status: "healthy",
      uptime: "99.99%",
      latency: "2ms",
      icon: Zap,
    },
    {
      name: "ML Models",
      status: "healthy",
      uptime: "99.90%",
      latency: "85ms",
      icon: Cpu,
    },
    {
      name: "Message Queue",
      status: "healthy",
      uptime: "99.98%",
      latency: "8ms",
      icon: Activity,
    },
    {
      name: "Storage",
      status: "healthy",
      uptime: "99.99%",
      latency: "15ms",
      icon: HardDrive,
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "degraded":
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case "unhealthy":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "border-green-500/50 bg-green-500/5";
      case "degraded":
        return "border-yellow-500/50 bg-yellow-500/5";
      case "unhealthy":
        return "border-red-500/50 bg-red-500/5";
      default:
        return "border-gray-500/50 bg-gray-500/5";
    }
  };

  const overallStatus = health?.status || "healthy";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Health</h1>
          <p className="text-muted-foreground">
            Monitor system performance and service health
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Overall Status Banner */}
      <Card className={getStatusColor(overallStatus)}>
        <CardContent className="py-6">
          <div className="flex items-center gap-6">
            <div className="h-16 w-16 rounded-full flex items-center justify-center bg-background">
              {getStatusIcon(overallStatus, healthLoading)}
            </div>
            <div>
              <h2 className="text-2xl font-bold capitalize">
                System {overallStatus}
              </h2>
              <p className="text-muted-foreground">
                {getStatusMessage(overallStatus)}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Last checked: {formatRelativeTime(new Date().toISOString())}
              </p>
            </div>
            <div className="ml-auto grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-500">99.9%</p>
                <p className="text-sm text-muted-foreground">Uptime (30d)</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">42ms</p>
                <p className="text-sm text-muted-foreground">Avg. Latency</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold">45%</span>
              <Badge variant="secondary">Normal</Badge>
            </div>
            <Progress value={45} className="h-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold">62%</span>
              <Badge variant="secondary">Normal</Badge>
            </div>
            <Progress value={62} className="h-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold">28%</span>
              <Badge variant="secondary">Normal</Badge>
            </div>
            <Progress value={28} className="h-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Network I/O</CardTitle>
            <Wifi className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl font-bold">1.2 GB/s</span>
              <Badge variant="secondary">Normal</Badge>
            </div>
            <Progress value={35} className="h-2" />
          </CardContent>
        </Card>
      </div>

      {/* Service Status Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Service Status</CardTitle>
          <CardDescription>Health status of all platform services</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {services.map((service) => (
              <div
                key={service.name}
                className={`p-4 rounded-lg border ${getStatusColor(service.status)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-background flex items-center justify-center">
                      <service.icon className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="font-medium">{service.name}</p>
                      <p className="text-sm text-muted-foreground">
                        Latency: {service.latency}
                      </p>
                    </div>
                  </div>
                  {getStatusIcon(service.status)}
                </div>
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Uptime</span>
                  <span className="font-medium text-green-500">{service.uptime}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* CPU History */}
        <Card>
          <CardHeader>
            <CardTitle>CPU Usage History</CardTitle>
            <CardDescription>Last 5 minutes</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={cpuHistory}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="time" className="text-xs" />
                <YAxis domain={[0, MOCK_PERCENT_100]} className="text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  formatter={(value) => [`${value}%`, "CPU"]}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorCpu)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Memory History */}
        <Card>
          <CardHeader>
            <CardTitle>Memory Usage History</CardTitle>
            <CardDescription>Last 5 minutes</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={memoryHistory}>
                <defs>
                  <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="time" className="text-xs" />
                <YAxis domain={[0, MOCK_PERCENT_100]} className="text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  formatter={(value) => [`${value}%`, "Memory"]}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  fillOpacity={1}
                  fill="url(#colorMemory)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Request Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Request Metrics</CardTitle>
          <CardDescription>Request volume and response latency</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={requestHistory}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="time" className="text-xs" />
              <YAxis yAxisId="left" className="text-xs" />
              <YAxis yAxisId="right" orientation="right" className="text-xs" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="requests"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: "#3b82f6" }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="latency"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ fill: "#f59e0b" }}
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-blue-500" />
              <span className="text-sm text-muted-foreground">Requests/min</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-yellow-500" />
              <span className="text-sm text-muted-foreground">Latency (ms)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Kubernetes Probes */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Readiness Probe
            </CardTitle>
            <CardDescription>
              Indicates if the service is ready to accept traffic
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              {readiness?.ready ? (
                <CheckCircle2 className="h-12 w-12 text-green-500" />
              ) : (
                <XCircle className="h-12 w-12 text-red-500" />
              )}
              <div>
                <p className="text-lg font-medium">
                  {readiness?.ready ? "Ready" : "Not Ready"}
                </p>
                <p className="text-sm text-muted-foreground">
                  Service is {readiness?.ready ? "" : "not "}accepting requests
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Liveness Probe
            </CardTitle>
            <CardDescription>
              Indicates if the service is running and healthy
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              {liveness?.alive ? (
                <CheckCircle2 className="h-12 w-12 text-green-500" />
              ) : (
                <XCircle className="h-12 w-12 text-red-500" />
              )}
              <div>
                <p className="text-lg font-medium">
                  {liveness?.alive ? "Alive" : "Dead"}
                </p>
                <p className="text-sm text-muted-foreground">
                  Service is {liveness?.alive ? "" : "not "}running
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
