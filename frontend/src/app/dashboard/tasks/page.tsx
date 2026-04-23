"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tasksApi } from "@/lib/api";
import { Task } from "@/types/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  ListTodo,
  Search,
  Filter,
  MoreHorizontal,
  XCircle,
  RefreshCw,
  Plus,
  Eye,
  Clock,
  CheckCircle2,
  Loader2,
  Bot,
  Activity,
  Timer,
  Zap,
} from "lucide-react";
import { formatDateTime, formatRelativeTime, formatNumber, formatPercentage } from "@/lib/utils";
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

export default function TasksPage() {
  // Constants for magic numbers
  const ICON_SIZE_CLASS = "h-4 w-4";
  const DEFAULT_TASK_PROGRESS = 50;
  const DEFAULT_SUCCESS_RATE = 0.95;
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("tasks");
  const [newTask, setNewTask] = useState({
    name: "",
    description: "",
    task_type: "data_processing",
    priority: "medium",
  });

  // Fetch tasks
  const { data: tasksData, isLoading: tasksLoading, refetch } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => tasksApi.list(),
  });

  const tasks = tasksData?.tasks || [];

  // Fetch agents
  const { data: agentsData, isLoading: agentsLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: () => tasksApi.listAgents(),
  });

  const agents = agentsData?.agents || [];

  // Create task mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newTask) => tasksApi.create({ ...data, type: data.task_type, priority: data.priority as import("@/types/api").TaskPriority }),
    onSuccess: () => {
      toast.success("Task created successfully");
      setIsCreateDialogOpen(false);
      setNewTask({ name: "", description: "", task_type: "data_processing", priority: "medium" });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
    onError: () => {
      toast.error("Failed to create task");
    },
  });

  // Cancel task mutation
  const cancelMutation = useMutation({
    mutationFn: (taskId: string) => tasksApi.cancel(taskId),
    onSuccess: () => {
      toast.success("Task cancelled");
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
    onError: () => {
      toast.error("Failed to cancel task");
    },
  });

  // Filter tasks
  const filteredTasks = tasks?.filter((task) => {
    const matchesSearch =
      task.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || task.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const pendingTasks = tasks?.filter((t) => t.status === "pending") || [];
  const runningTasks = tasks?.filter((t) => t.status === "running") || [];
  const completedTasks = tasks?.filter((t) => t.status === "completed") || [];
  const activeAgents = agents?.filter((a) => a.status === "active" || a.status === "busy") || [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <Loader2 className={`${ICON_SIZE_CLASS} text-blue-500 animate-spin`} />;
      case "completed":
        return <CheckCircle2 className={`${ICON_SIZE_CLASS} text-green-500`} />;
      case "failed":
        return <XCircle className={`${ICON_SIZE_CLASS} text-red-500`} />;
      case "pending":
        return <Clock className={`${ICON_SIZE_CLASS} text-yellow-500`} />;
      case "cancelled":
        return <XCircle className={`${ICON_SIZE_CLASS} text-gray-500`} />;
      default:
        return <Clock className={`${ICON_SIZE_CLASS} text-gray-500`} />;
    }
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case "running":
        return "default";
      case "completed":
        return "secondary";
      case "failed":
        return "destructive";
      default:
        return "outline";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-red-500 bg-red-500/10";
      case "medium":
        return "text-yellow-500 bg-yellow-500/10";
      case "low":
        return "text-green-500 bg-green-500/10";
      default:
        return "text-gray-500 bg-gray-500/10";
    }
  };

  // Mock chart data
  const taskTrends = [
    { time: "00:00", completed: 45, failed: 2, pending: 12 },
    { time: "04:00", completed: 32, failed: 1, pending: 8 },
    { time: "08:00", completed: 78, failed: 5, pending: 15 },
    { time: "12:00", completed: 120, failed: 8, pending: 22 },
    { time: "16:00", completed: 145, failed: 6, pending: 18 },
    { time: "20:00", completed: 89, failed: 3, pending: 10 },
    { time: "Now", completed: 110, failed: 4, pending: 14 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Task Orchestrator</h1>
          <p className="text-muted-foreground">
            Manage tasks and monitor agent performance
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className={`mr-2 ${ICON_SIZE_CLASS}`} />
            Refresh
          </Button>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className={`mr-2 ${ICON_SIZE_CLASS}`} />
                Create Task
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-125">
              <DialogHeader>
                <DialogTitle>Create New Task</DialogTitle>
                <DialogDescription>
                  Configure and schedule a new task for execution
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Task Name</Label>
                  <Input
                    id="name"
                    value={newTask.name}
                    onChange={(e) => setNewTask({ ...newTask, name: e.target.value })}
                    placeholder="my-task"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newTask.description}
                    onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                    placeholder="Describe what this task does..."
                    rows={3}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="type">Task Type</Label>
                    <Select
                      value={newTask.task_type}
                      onValueChange={(value) => setNewTask({ ...newTask, task_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="data_processing">Data Processing</SelectItem>
                        <SelectItem value="ml_training">ML Training</SelectItem>
                        <SelectItem value="ml_inference">ML Inference</SelectItem>
                        <SelectItem value="report_generation">Report Generation</SelectItem>
                        <SelectItem value="notification">Notification</SelectItem>
                        <SelectItem value="integration">Integration</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="priority">Priority</Label>
                    <Select
                      value={newTask.priority}
                      onValueChange={(value) => setNewTask({ ...newTask, priority: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select priority" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createMutation.mutate(newTask)}
                  disabled={createMutation.isPending || !newTask.name}
                >
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className={`mr-2 ${ICON_SIZE_CLASS} animate-spin`} />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className={`mr-2 ${ICON_SIZE_CLASS}`} />
                      Create Task
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
            <ListTodo className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{tasks?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <Loader2 className={`${ICON_SIZE_CLASS} text-blue-500`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{runningTasks.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className={`${ICON_SIZE_CLASS} text-yellow-500`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingTasks.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle2 className={`${ICON_SIZE_CLASS} text-green-500`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedTasks.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Bot className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAgents.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="tasks" className="gap-2">
            <ListTodo className={ICON_SIZE_CLASS} />
            Tasks
          </TabsTrigger>
          <TabsTrigger value="agents" className="gap-2">
            <Bot className={ICON_SIZE_CLASS} />
            Agents
          </TabsTrigger>
          <TabsTrigger value="metrics" className="gap-2">
            <Activity className={ICON_SIZE_CLASS} />
            Metrics
          </TabsTrigger>
        </TabsList>

        {/* Tasks Tab */}
        <TabsContent value="tasks" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className={`absolute left-3 top-1/2 -translate-y-1/2 ${ICON_SIZE_CLASS} text-muted-foreground`} />
              <Input
                placeholder="Search tasks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-45">
                <Filter className={`mr-2 ${ICON_SIZE_CLASS}`} />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Tasks Table */}
          <Card>
            <CardHeader>
              <CardTitle>Tasks</CardTitle>
              <CardDescription>View and manage all scheduled and running tasks</CardDescription>
            </CardHeader>
            <CardContent>
              {tasksLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Progress</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTasks?.map((task) => (
                      <TableRow key={task.id}>
                        <TableCell className="font-medium">
                          <div>
                            <p>{task.name}</p>
                            {task.description && (
                              <p className="text-xs text-muted-foreground truncate max-w-50">
                                {task.description}
                              </p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{task.task_type || "general"}</Badge>
                        </TableCell>
                        <TableCell>
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(
                              task.priority || "medium"
                            )}`}
                          >
                            {task.priority || "medium"}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(task.status)}
                            <Badge variant={getStatusBadgeVariant(task.status)}>
                              {task.status}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell>
                          {task.status === "running" && (
                            <div className="w-24">
                              <Progress value={task.progress || DEFAULT_TASK_PROGRESS} className="h-2" />
                            </div>
                          )}
                          {task.status === "completed" && <span className="text-green-500">100%</span>}
                          {task.status === "pending" && <span className="text-muted-foreground">-</span>}
                        </TableCell>
                        <TableCell>{formatRelativeTime(task.created_at)}</TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <MoreHorizontal className={ICON_SIZE_CLASS} />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Actions</DropdownMenuLabel>
                              <DropdownMenuItem onClick={() => setSelectedTask(task)}>
                                <Eye className={`mr-2 ${ICON_SIZE_CLASS}`} />
                                View Details
                              </DropdownMenuItem>
                              {(task.status === "pending" || task.status === "running") && (
                                <>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    onClick={() => cancelMutation.mutate(task.id)}
                                    className="text-red-600"
                                    disabled={cancelMutation.isPending}
                                  >
                                    <XCircle className={`mr-2 ${ICON_SIZE_CLASS}`} />
                                    Cancel
                                  </DropdownMenuItem>
                                </>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agents</CardTitle>
              <CardDescription>Monitor task execution agents and their status</CardDescription>
            </CardHeader>
            <CardContent>
              {agentsLoading ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <Skeleton key={i} className="h-32 w-full" />
                  ))}
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {agents?.map((agent) => (
                    <Card key={agent.id} className="relative overflow-hidden">
                      <div
                        className={`absolute top-0 left-0 right-0 h-1 ${agent.status === "active"
                          ? "bg-green-500"
                          : agent.status === "busy"
                            ? "bg-blue-500"
                            : "bg-gray-300"
                          }`}
                      />
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div
                              className={`h-10 w-10 rounded-full flex items-center justify-center ${agent.status === "active"
                                ? "bg-green-500/10"
                                : agent.status === "busy"
                                  ? "bg-blue-500/10"
                                  : "bg-gray-500/10"
                                }`}
                            >
                              <Bot
                                className={`h-5 w-5 ${agent.status === "active"
                                  ? "text-green-500"
                                  : agent.status === "busy"
                                    ? "text-blue-500"
                                    : "text-gray-500"
                                  }`}
                              />
                            </div>
                            <div>
                              <p className="font-medium">{agent.name}</p>
                              <p className="text-xs text-muted-foreground">{agent.type}</p>
                            </div>
                          </div>
                          <Badge
                            variant={
                              agent.status === "active"
                                ? "default"
                                : agent.status === "busy"
                                  ? "secondary"
                                  : "outline"
                            }
                          >
                            {agent.status}
                          </Badge>
                        </div>
                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-muted-foreground">Tasks Completed</p>
                            <p className="font-medium">{formatNumber(agent.tasks_completed || 0)}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Success Rate</p>
                            <p className="font-medium">
                              {formatPercentage(agent.success_rate || DEFAULT_SUCCESS_RATE)}
                            </p>
                          </div>
                        </div>
                        {agent.current_task && (
                          <div className="mt-4 p-2 bg-muted/50 rounded-lg">
                            <p className="text-xs text-muted-foreground">Current Task</p>
                            <p className="text-sm font-medium truncate">{agent.current_task}</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg. Execution Time</CardTitle>
                <Timer className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">2m 34s</div>
                <p className="text-xs text-muted-foreground">-12% from last week</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Throughput</CardTitle>
                <Zap className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">156/hr</div>
                <p className="text-xs text-muted-foreground">Tasks per hour</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                <CheckCircle2 className={`${ICON_SIZE_CLASS} text-green-500`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">97.2%</div>
                <p className="text-xs text-muted-foreground">+2.1% from last week</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Queue Depth</CardTitle>
                <Clock className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{pendingTasks.length}</div>
                <p className="text-xs text-muted-foreground">Waiting to execute</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Task Execution Trends</CardTitle>
              <CardDescription>Task completion and failure rates over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={taskTrends}>
                  <defs>
                    <linearGradient id="colorCompleted" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="time" className="text-xs" />
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
                    dataKey="completed"
                    stroke="#10b981"
                    fillOpacity={1}
                    fill="url(#colorCompleted)"
                  />
                  <Line type="monotone" dataKey="failed" stroke="#ef4444" strokeWidth={2} />
                  <Line type="monotone" dataKey="pending" stroke="#f59e0b" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Task Details Dialog */}
      <Dialog open={Boolean(selectedTask)} onOpenChange={() => setSelectedTask(null)}>
        <DialogContent className="sm:max-w-150">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedTask && getStatusIcon(selectedTask.status)}
              Task Details
            </DialogTitle>
            <DialogDescription>View task information and execution details</DialogDescription>
          </DialogHeader>
          {selectedTask && (
            <div className="space-y-6">
              {/* Task Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Name</p>
                  <p className="font-medium">{selectedTask.name}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Type</p>
                  <Badge variant="outline">{selectedTask.task_type || "general"}</Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Status</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedTask.status)}
                    <span className="font-medium capitalize">{selectedTask.status}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Priority</p>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(
                      selectedTask.priority || "medium"
                    )}`}
                  >
                    {selectedTask.priority || "medium"}
                  </span>
                </div>
              </div>

              {/* Progress */}
              {selectedTask.status === "running" && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>{selectedTask.progress || 50}%</span>
                  </div>
                  <Progress value={selectedTask.progress || 50} />
                </div>
              )}

              {/* Description */}
              {selectedTask.description && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Description</p>
                  <p className="p-3 bg-muted/50 rounded-lg">{selectedTask.description}</p>
                </div>
              )}

              {/* Error message */}
              {selectedTask.status === "failed" && selectedTask.error && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Error</p>
                  <p className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-700">
                    {selectedTask.error}
                  </p>
                </div>
              )}

              {/* Metadata */}
              <div className="border-t pt-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Created:</span>{" "}
                    {formatDateTime(selectedTask.created_at)}
                  </div>
                  {selectedTask.started_at && (
                    <div>
                      <span className="text-muted-foreground">Started:</span>{" "}
                      {formatDateTime(selectedTask.started_at)}
                    </div>
                  )}
                  {selectedTask.completed_at && (
                    <div>
                      <span className="text-muted-foreground">Completed:</span>{" "}
                      {formatDateTime(selectedTask.completed_at)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedTask(null)}>
              Close
            </Button>
            {selectedTask && (selectedTask.status === "pending" || selectedTask.status === "running") && (
              <Button
                variant="destructive"
                onClick={() => {
                  cancelMutation.mutate(selectedTask.id);
                  setSelectedTask(null);
                }}
                disabled={cancelMutation.isPending}
              >
                <XCircle className="mr-2 h-4 w-4" />
                Cancel Task
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
