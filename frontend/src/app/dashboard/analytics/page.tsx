"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BarChart3,
  TrendingUp,
  Users,
  Zap,
  Clock,
  RefreshCw,
  Download,
  Calendar,
  FileText,
  Activity,
  Target,
  DollarSign,
  Eye,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { formatDate } from "@/lib/utils";
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
  ComposedChart,
} from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

// Constants for magic numbers
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
const TWO_DAYS_MS = 2 * ONE_DAY_MS;
const MOCK_PERCENT_4 = 4;
const BORDER_RADIUS = 4;

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("7d");
  const [activeTab, setActiveTab] = useState("overview");

  // Fetch dashboard data
  const { isLoading: dashboardLoading, refetch } = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: () => analyticsApi.getDashboard(),
  });

  // Fetch reports
  const { isLoading: reportsLoading } = useQuery({
    queryKey: ["analytics", "reports"],
    queryFn: () => analyticsApi.listReports(),
  });

  // Fetch metrics
  const { isLoading: metricsLoading } = useQuery({
    queryKey: ["analytics", "metrics"],
    queryFn: () => analyticsApi.getMetrics(),
  });

  // Mock data for charts
  const revenueData = [
    { date: "Jan", revenue: 45000, predictions: 1200, cost: 12000 },
    { date: "Feb", revenue: 52000, predictions: 1450, cost: 13500 },
    { date: "Mar", revenue: 48000, predictions: 1300, cost: 11800 },
    { date: "Apr", revenue: 61000, predictions: 1650, cost: 14200 },
    { date: "May", revenue: 55000, predictions: 1520, cost: 13800 },
    { date: "Jun", revenue: 67000, predictions: 1890, cost: 15400 },
    { date: "Jul", revenue: 72000, predictions: 2100, cost: 16200 },
  ];

  const modelUsageData = [
    { name: "Fraud Detection", usage: 35, predictions: 3400 },
    { name: "Churn Prediction", usage: 28, predictions: 2100 },
    { name: "Anomaly Detection", usage: 22, predictions: 1250 },
    { name: "Demand Forecast", usage: 15, predictions: 890 },
  ];

  const hourlyActivity = [
    { hour: "00:00", requests: 120, latency: 42 },
    { hour: "03:00", requests: 85, latency: 38 },
    { hour: "06:00", requests: 180, latency: 45 },
    { hour: "09:00", requests: 420, latency: 52 },
    { hour: "12:00", requests: 580, latency: 58 },
    { hour: "15:00", requests: 520, latency: 55 },
    { hour: "18:00", requests: 380, latency: 48 },
    { hour: "21:00", requests: 220, latency: 44 },
  ];

  const userEngagement = [
    { day: "Mon", activeUsers: 145, sessions: 320 },
    { day: "Tue", activeUsers: 162, sessions: 380 },
    { day: "Wed", activeUsers: 178, sessions: 420 },
    { day: "Thu", activeUsers: 185, sessions: 450 },
    { day: "Fri", activeUsers: 172, sessions: 410 },
    { day: "Sat", activeUsers: 98, sessions: 180 },
    { day: "Sun", activeUsers: 85, sessions: 150 },
  ];

  const kpis = [
    {
      title: "Total Revenue",
      value: "$72,450",
      change: "+12.5%",
      trend: "up",
      icon: DollarSign,
    },
    {
      title: "Total Predictions",
      value: "12,847",
      change: "+8.2%",
      trend: "up",
      icon: Zap,
    },
    {
      title: "Active Users",
      value: "1,284",
      change: "+5.4%",
      trend: "up",
      icon: Users,
    },
    {
      title: "Avg. Latency",
      value: "42ms",
      change: "-15%",
      trend: "down",
      icon: Clock,
    },
  ];

  const isLoading = dashboardLoading || reportsLoading || metricsLoading;

  // Use state for mock data to ensure purity
  const [now] = useState(new Date());

  const mockReports = useMemo(() => [
    {
      id: "1",
      name: "Weekly Performance Report",
      type: "performance",
      period: "Last 7 days",
      status: "completed",
      created_at: now.toISOString(),
    },
    {
      id: "2",
      name: "Monthly Analytics Summary",
      type: "analytics",
      period: "June 2024",
      status: "completed",
      created_at: new Date(now.getTime() - ONE_DAY_MS).toISOString(),
    },
    {
      id: "3",
      name: "Model Accuracy Report",
      type: "ml",
      period: "Q2 2024",
      status: "generating",
      created_at: now.toISOString(),
    },
    {
      id: "4",
      name: "User Engagement Report",
      type: "users",
      period: "Last 30 days",
      status: "completed",
      created_at: new Date(now.getTime() - TWO_DAYS_MS).toISOString(),
    },
  ], [now]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">
            Insights and metrics for your automation platform
          </p>
        </div>
        <div className="flex gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-37.5">
              <Calendar className="mr-2 h-4 w-4" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24 hours</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        {kpis.map((kpi) => (
          <Card key={kpi.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{kpi.title}</CardTitle>
              <kpi.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-8 w-24" />
              ) : (
                <>
                  <div className="text-2xl font-bold">{kpi.value}</div>
                  <div className="flex items-center text-xs">
                    {kpi.trend === "up" ? (
                      <ArrowUpRight className="mr-1 h-3 w-3 text-green-500" />
                    ) : (
                      <ArrowDownRight className="mr-1 h-3 w-3 text-green-500" />
                    )}
                    <span className={kpi.trend === "up" ? "text-green-500" : "text-green-500"}>
                      {kpi.change}
                    </span>
                    <span className="text-muted-foreground ml-1">from last period</span>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="predictions" className="gap-2">
            <Zap className="h-4 w-4" />
            Predictions
          </TabsTrigger>
          <TabsTrigger value="users" className="gap-2">
            <Users className="h-4 w-4" />
            Users
          </TabsTrigger>
          <TabsTrigger value="reports" className="gap-2">
            <FileText className="h-4 w-4" />
            Reports
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            {/* Revenue Chart */}
            <Card className="lg:col-span-4">
              <CardHeader>
                <CardTitle>Revenue & Predictions</CardTitle>
                <CardDescription>Monthly revenue and prediction volume</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={350}>
                  <ComposedChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis yAxisId="left" className="text-xs" />
                    <YAxis yAxisId="right" orientation="right" className="text-xs" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Bar yAxisId="left" dataKey="revenue" fill="#3b82f6" radius={[BORDER_RADIUS, BORDER_RADIUS, 0, 0]} />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="predictions"
                      stroke="#10b981"
                      strokeWidth={2}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Model Usage Pie Chart */}
            <Card className="lg:col-span-3">
              <CardHeader>
                <CardTitle>Model Usage Distribution</CardTitle>
                <CardDescription>Prediction volume by model</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={modelUsageData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="usage"
                    >
                      {modelUsageData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="grid grid-cols-2 gap-2 mt-4">
                  {modelUsageData.map((model, index) => (
                    <div key={model.name} className="flex items-center gap-2 text-sm">
                      <div
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: COLORS[index] }}
                      />
                      <span className="truncate">{model.name}</span>
                      <span className="text-muted-foreground ml-auto">{model.usage}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Hourly Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Hourly Activity</CardTitle>
              <CardDescription>API requests and response latency over the day</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={hourlyActivity}>
                  <defs>
                    <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="hour" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="requests"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorRequests)"
                  />
                  <Line type="monotone" dataKey="latency" stroke="#f59e0b" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Predictions Tab */}
        <TabsContent value="predictions" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Today&apos;s Predictions</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">2,847</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-500">+18%</span> from yesterday
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Average Confidence</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">94.2%</div>
                <p className="text-xs text-muted-foreground">Across all models</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Batch Jobs</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">156</div>
                <p className="text-xs text-muted-foreground">Completed today</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Model Performance Comparison</CardTitle>
              <CardDescription>Accuracy and prediction counts by model type</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={modelUsageData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis type="number" className="text-xs" />
                  <YAxis dataKey="name" type="category" width={120} className="text-xs" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="predictions" fill="#3b82f6" radius={[0, BORDER_RADIUS, BORDER_RADIUS, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">1,284</div>
                <p className="text-xs text-muted-foreground">Currently online: 145</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">New Users</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">+89</div>
                <p className="text-xs text-muted-foreground">This week</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg. Session Duration</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">12m 34s</div>
                <p className="text-xs text-muted-foreground">
                  <span className="text-green-500">+8%</span> from last week
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>User Engagement</CardTitle>
              <CardDescription>Active users and sessions over the past week</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={userEngagement}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="day" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Bar dataKey="activeUsers" fill="#3b82f6" radius={[BORDER_RADIUS, BORDER_RADIUS, 0, 0]} />
                  <Bar dataKey="sessions" fill="#10b981" radius={[BORDER_RADIUS, BORDER_RADIUS, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Generated Reports</CardTitle>
                  <CardDescription>View and download analytics reports</CardDescription>
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Generate Report
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {reportsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Report Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Period</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {mockReports.map((report) => (
                      <TableRow key={report.id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                            {report.name}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{report.type}</Badge>
                        </TableCell>
                        <TableCell>{report.period}</TableCell>
                        <TableCell>
                          <Badge
                            variant={report.status === "completed" ? "default" : "secondary"}
                          >
                            {report.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatDate(report.created_at)}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              disabled={report.status !== "completed"}
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Plus(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14" />
      <path d="M12 5v14" />
    </svg>
  );
}
