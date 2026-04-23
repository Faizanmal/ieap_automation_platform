"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi, modelsApi, pipelinesApi, tasksApi, healthApi, decisionsApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import {
  Brain,
  GitBranch,
  CheckCircle2,
  Clock,
  TrendingUp,
  AlertTriangle,
  Zap,
  Server,
  Cpu,
  HardDrive,
  RefreshCw,
  ArrowRight,
} from "lucide-react";
import { formatNumber, formatRelativeTime } from "@/lib/utils";
import Link from "next/link";
import {
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function DashboardPage() {
  // Constants for magic numbers
  const ANALYTICS_REFETCH_INTERVAL_MS = 30000; // Refresh every 30 seconds
  const HEALTH_REFETCH_INTERVAL_MS = 15000; // Refresh every 15 seconds
  const CHART_HEIGHT = 300;
  const BAR_CHART_HEIGHT = 250;
  const PIE_INNER_RADIUS = 60;
  const PIE_OUTER_RADIUS = 100;
  const PIE_PADDING_ANGLE = 5;
  const Y_AXIS_WIDTH = 120;
  const BAR_RADIUS = [0, 4, 4, 0];
  const STROKE_DASHARRAY = "3 3";
  const BORDER_RADIUS_PX = "8px";
  const PROGRESS_HEIGHT_CLASS = "h-2";
  const ICON_SIZE_CLASS = "h-4 w-4";
  const LARGE_ICON_SIZE_CLASS = "h-6 w-6";
  const QUICK_ACTION_SIZE_CLASS = "h-12 w-12";
  const QUICK_ACTION_ICON_SIZE_CLASS = "h-6 w-6";
  const MODEL_LIST_LIMIT = 4;
  const SKELETON_COUNT = 4;
  const CPU_USAGE_PERCENT = 45;
  const MEMORY_USAGE_PERCENT = 62;
  const STORAGE_USAGE_PERCENT = 28;
  const MOCK_RECORDS_COUNT = 12500;
  const DOMAIN_MIN = 0;
  const DOMAIN_MAX = 100;

  // Mock data constants
  const PREDICTION_TRENDS = [
    { time: "00:00", predictions: 120, accuracy: 94 },
    { time: "04:00", predictions: 85, accuracy: 92 },
    { time: "08:00", predictions: 250, accuracy: 96 },
    { time: "12:00", predictions: 380, accuracy: 95 },
    { time: "16:00", predictions: 420, accuracy: 97 },
    { time: "20:00", predictions: 290, accuracy: 93 },
    { time: "Now", predictions: 340, accuracy: 95 },
  ];

  const MODEL_PERFORMANCE = [
    { name: "Anomaly Detection", accuracy: 94, predictions: 1250 },
    { name: "Demand Forecast", accuracy: 89, predictions: 890 },
    { name: "Churn Prediction", accuracy: 92, predictions: 2100 },
    { name: "Fraud Detection", accuracy: 97, predictions: 3400 },
  ];

  // Fetch dashboard data
  const { refetch: refetchAnalytics } = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: analyticsApi.getDashboard,
    refetchInterval: ANALYTICS_REFETCH_INTERVAL_MS, // Refresh every 30 seconds
  });

  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ["models"],
    queryFn: () => modelsApi.list(),
  });

  const { data: pipelines, isLoading: pipelinesLoading } = useQuery({
    queryKey: ["pipelines"],
    queryFn: () => pipelinesApi.list(),
  });

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => tasksApi.list(),
  });

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => healthApi.checkDetailed(),
    refetchInterval: HEALTH_REFETCH_INTERVAL_MS, // Refresh every 15 seconds
  });

  const { data: decisions, isLoading: decisionsLoading } = useQuery({
    queryKey: ["decisions"],
    queryFn: () => decisionsApi.list(),
  });

  // Calculate statistics
  const modelsList = models?.models || [];
  const pipelinesList = pipelines?.pipelines || [];
  const tasksList = tasks?.tasks || [];
  const decisionsList = decisions?.decisions || [];
  
  const activeModels = modelsList.filter((m) => m.status === "deployed").length;
  const totalModels = modelsList.length;
  const runningPipelines = pipelinesList.filter((p) => p.status === "running").length;
  const totalPipelines = pipelinesList.length;
  const pendingTasks = tasksList.filter((t) => t.status === "pending").length;
  const completedTasks = tasksList.filter((t) => t.status === "completed").length;
  const pendingDecisions = decisionsList.filter((d) => d.status === "pending").length;

  const pipelineStatus = [
    { name: "Running", value: runningPipelines, color: "#10b981" },
    { name: "Completed", value: pipelinesList.filter((p) => p.status === "completed").length, color: "#3b82f6" },
    { name: "Failed", value: pipelinesList.filter((p) => p.status === "failed").length, color: "#ef4444" },
    { name: "Idle", value: pipelinesList.filter((p) => p.status === "idle" || p.status === "paused").length, color: "#f59e0b" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to IEAP - Intelligent Enterprise Automation Platform
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetchAnalytics()}>
          <RefreshCw className={`mr-2 ${ICON_SIZE_CLASS}`} />
          Refresh
        </Button>
      </div>

      {/* System Health Banner */}
      {health && (
        <Card className={health.status === "healthy" ? "border-green-500/50 bg-green-500/5" : "border-yellow-500/50 bg-yellow-500/5"}>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {health.status === "healthy" ? (
                  <CheckCircle2 className={`${LARGE_ICON_SIZE_CLASS} text-green-500`} />
                ) : (
                  <AlertTriangle className={`${LARGE_ICON_SIZE_CLASS} text-yellow-500`} />
                )}
                <div>
                  <p className="font-medium">System Status: {health.status.toUpperCase()}</p>
                  <p className="text-sm text-muted-foreground">
                    All services operational • Last checked {formatRelativeTime(new Date().toISOString())}
                  </p>
                </div>
              </div>
              <Link href="/dashboard/health">
                <Button variant="ghost" size="sm">
                  View Details
                  <ArrowRight className={`ml-2 ${ICON_SIZE_CLASS}`} />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Models</CardTitle>
            <Brain className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            {modelsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{activeModels} / {totalModels}</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-500">+2</span> deployed this week
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running Pipelines</CardTitle>
            <GitBranch className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            {pipelinesLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{runningPipelines} / {totalPipelines}</div>
                <p className="text-xs text-muted-foreground">
                  Processing {formatNumber(MOCK_RECORDS_COUNT)} records
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
            <CheckCircle2 className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            {tasksLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{completedTasks}</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-yellow-500">{pendingTasks} pending</span>
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Decisions</CardTitle>
            <Clock className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            {decisionsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{pendingDecisions}</div>
                <p className="text-xs text-muted-foreground">
                  Awaiting approval
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Predictions Trend Chart */}
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Predictions Overview</CardTitle>
            <CardDescription>Prediction volume and accuracy over the last 24 hours</CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <AreaChart data={PREDICTION_TRENDS}>
                <defs>
                  <linearGradient id="colorPredictions" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray={STROKE_DASHARRAY} className="stroke-muted" />
                <XAxis dataKey="time" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: BORDER_RADIUS_PX,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="predictions"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorPredictions)"
                />
                <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Pipeline Status Pie Chart */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Pipeline Status</CardTitle>
            <CardDescription>Current state of all pipelines</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <PieChart>
                <Pie
                  data={pipelineStatus}
                  cx="50%"
                  cy="50%"
                  innerRadius={PIE_INNER_RADIUS}
                  outerRadius={PIE_OUTER_RADIUS}
                  paddingAngle={PIE_PADDING_ANGLE}
                  dataKey="value"
                >
                  {pipelineStatus.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: BORDER_RADIUS_PX,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex justify-center gap-4 mt-4">
              {pipelineStatus.map((status) => (
                <div key={status.name} className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: status.color }} />
                  <span className="text-sm text-muted-foreground">{status.name}: {status.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Model Performance and Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Model Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Model Performance</CardTitle>
            <CardDescription>Accuracy and prediction counts by model</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={BAR_CHART_HEIGHT}>
              <BarChart data={MODEL_PERFORMANCE} layout="vertical">
                <CartesianGrid strokeDasharray={STROKE_DASHARRAY} className="stroke-muted" />
                <XAxis type="number" domain={[DOMAIN_MIN, DOMAIN_MAX]} />
                <YAxis dataKey="name" type="category" width={Y_AXIS_WIDTH} className="text-xs" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: BORDER_RADIUS_PX,
                  }}
                />
                <Bar dataKey="accuracy" fill="#3b82f6" radius={BAR_RADIUS} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Quick Actions & Recent Models */}
        <Card>
          <CardHeader>
            <CardTitle>ML Models</CardTitle>
            <CardDescription>Quick overview of deployed models</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {modelsLoading ? (
              Array.from({ length: SKELETON_COUNT }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                </div>
              ))
            ) : (
              modelsList.slice(0, MODEL_LIST_LIMIT).map((model) => (
                <div key={model.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <Brain className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{model.name}</p>
                      <p className="text-xs text-muted-foreground">v{model.version}</p>
                    </div>
                  </div>
                  <Badge variant={model.status === "deployed" ? "default" : "secondary"}>
                    {model.status}
                  </Badge>
                </div>
              ))
            )}
            <Link href="/dashboard/models">
              <Button variant="outline" className="w-full mt-2">
                View All Models
                <ArrowRight className={`ml-2 ${ICON_SIZE_CLASS}`} />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* System Resources */}
      <Card>
        <CardHeader>
          <CardTitle>System Resources</CardTitle>
          <CardDescription>Real-time resource utilization</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Cpu className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
                  <span className="text-sm font-medium">CPU Usage</span>
                </div>
                <span className="text-sm text-muted-foreground">{CPU_USAGE_PERCENT}%</span>
              </div>
              <Progress value={CPU_USAGE_PERCENT} className={PROGRESS_HEIGHT_CLASS} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
                  <span className="text-sm font-medium">Memory Usage</span>
                </div>
                <span className="text-sm text-muted-foreground">{MEMORY_USAGE_PERCENT}%</span>
              </div>
              <Progress value={MEMORY_USAGE_PERCENT} className={PROGRESS_HEIGHT_CLASS} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <HardDrive className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
                  <span className="text-sm font-medium">Storage Usage</span>
                </div>
                <span className="text-sm text-muted-foreground">{STORAGE_USAGE_PERCENT}%</span>
              </div>
              <Progress value={STORAGE_USAGE_PERCENT} className={PROGRESS_HEIGHT_CLASS} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-4">
        <Link href="/dashboard/predictions">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center gap-4 p-6">
              <div className={`${QUICK_ACTION_SIZE_CLASS} rounded-full bg-blue-500/10 flex items-center justify-center`}>
                <Zap className={`${QUICK_ACTION_ICON_SIZE_CLASS} text-blue-500`} />
              </div>
              <div>
                <p className="font-medium">New Prediction</p>
                <p className="text-sm text-muted-foreground">Run ML inference</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dashboard/pipelines">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center gap-4 p-6">
              <div className={`${QUICK_ACTION_SIZE_CLASS} rounded-full bg-green-500/10 flex items-center justify-center`}>
                <GitBranch className={`${QUICK_ACTION_ICON_SIZE_CLASS} text-green-500`} />
              </div>
              <div>
                <p className="font-medium">Create Pipeline</p>
                <p className="text-sm text-muted-foreground">Automate workflows</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dashboard/decisions">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center gap-4 p-6">
              <div className={`${QUICK_ACTION_SIZE_CLASS} rounded-full bg-yellow-500/10 flex items-center justify-center`}>
                <CheckCircle2 className={`${QUICK_ACTION_ICON_SIZE_CLASS} text-yellow-500`} />
              </div>
              <div>
                <p className="font-medium">Review Decisions</p>
                <p className="text-sm text-muted-foreground">{pendingDecisions} pending</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dashboard/analytics">
          <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
            <CardContent className="flex items-center gap-4 p-6">
              <div className={`${QUICK_ACTION_SIZE_CLASS} rounded-full bg-purple-500/10 flex items-center justify-center`}>
                <TrendingUp className={`${QUICK_ACTION_ICON_SIZE_CLASS} text-purple-500`} />
              </div>
              <div>
                <p className="font-medium">View Analytics</p>
                <p className="text-sm text-muted-foreground">Reports & insights</p>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
