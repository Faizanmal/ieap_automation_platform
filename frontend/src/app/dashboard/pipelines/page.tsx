"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pipelinesApi } from "@/lib/api";
import { PipelineInfo } from "@/types/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
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
  GitBranch,
  Search,
  Filter,
  MoreHorizontal,
  Play,
  Square,
  Trash2,
  BarChart3,
  RefreshCw,
  Plus,
  Eye,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Database,
} from "lucide-react";
import { formatDate, formatNumber } from "@/lib/utils";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function PipelinesPage() {
  // Constants for magic numbers
  const ICON_SIZE_CLASS = "h-4 w-4";
  const MOCK_RECORDS_PROCESSED = 2450000;
  const METRICS_DATA = [
    { time: "00:00", records: 12000, duration: 45 },
    { time: "04:00", records: 8500, duration: 32 },
    { time: "08:00", records: 25000, duration: 78 },
    { time: "12:00", records: 38000, duration: 95 },
    { time: "16:00", records: 42000, duration: 110 },
    { time: "20:00", records: 28000, duration: 72 },
    { time: "Now", records: 35000, duration: 88 },
  ];
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedPipeline, setSelectedPipeline] = useState<PipelineInfo | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newPipeline, setNewPipeline] = useState({
    name: "",
    description: "",
    source_type: "database",
    schedule: "0 * * * *",
  });

  // Fetch pipelines
  const { data: pipelinesData, isLoading, refetch } = useQuery({
    queryKey: ["pipelines"],
    queryFn: () => pipelinesApi.list(),
  });

  const pipelines = pipelinesData?.pipelines || [];

  // Create pipeline mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newPipeline) =>
      pipelinesApi.create({
        ...data,
        source_type: data.source_type as import("@/types/api").DataSourceType,
        source_config: {},
        destination_config: {},
      }),
    onSuccess: () => {
      toast.success("Pipeline created successfully");
      setIsCreateDialogOpen(false);
      setNewPipeline({ name: "", description: "", source_type: "database", schedule: "0 * * * *" });
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
    },
    onError: () => {
      toast.error("Failed to create pipeline");
    },
  });

  // Run pipeline mutation
  const runMutation = useMutation({
    mutationFn: (pipelineId: string) => pipelinesApi.run(pipelineId),
    onSuccess: () => {
      toast.success("Pipeline started");
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
    },
    onError: () => {
      toast.error("Failed to start pipeline");
    },
  });

  // Stop pipeline mutation
  const stopMutation = useMutation({
    mutationFn: (pipelineId: string) => pipelinesApi.stop(pipelineId),
    onSuccess: () => {
      toast.success("Pipeline stopped");
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
    },
    onError: () => {
      toast.error("Failed to stop pipeline");
    },
  });

  // Delete pipeline mutation
  const deleteMutation = useMutation({
    mutationFn: (pipelineId: string) => pipelinesApi.delete(pipelineId),
    onSuccess: () => {
      toast.success("Pipeline deleted");
      queryClient.invalidateQueries({ queryKey: ["pipelines"] });
    },
    onError: () => {
      toast.error("Failed to delete pipeline");
    },
  });

  // Filter pipelines
  const filteredPipelines = pipelines?.filter((pipeline) => {
    const matchesSearch =
      pipeline.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pipeline.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || pipeline.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <Loader2 className={`${ICON_SIZE_CLASS} text-green-500 animate-spin`} />;
      case "completed":
        return <CheckCircle2 className={`${ICON_SIZE_CLASS} text-blue-500`} />;
      case "failed":
        return <XCircle className={`${ICON_SIZE_CLASS} text-red-500`} />;
      case "pending":
        return <Clock className={`${ICON_SIZE_CLASS} text-yellow-500`} />;
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

  // Mock metrics data
  const metricsData = METRICS_DATA;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Pipelines</h1>
          <p className="text-muted-foreground">
            Manage and monitor your data processing pipelines
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
                Create Pipeline
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-125">
              <DialogHeader>
                <DialogTitle>Create New Pipeline</DialogTitle>
                <DialogDescription>
                  Configure a new data processing pipeline
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Pipeline Name</Label>
                  <Input
                    id="name"
                    value={newPipeline.name}
                    onChange={(e) =>
                      setNewPipeline({ ...newPipeline, name: e.target.value })
                    }
                    placeholder="my-data-pipeline"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newPipeline.description}
                    onChange={(e) =>
                      setNewPipeline({ ...newPipeline, description: e.target.value })
                    }
                    placeholder="Describe what this pipeline does..."
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="source">Data Source</Label>
                  <Select
                    value={newPipeline.source_type}
                    onValueChange={(value) =>
                      setNewPipeline({ ...newPipeline, source_type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select source type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="database">Database</SelectItem>
                      <SelectItem value="api">REST API</SelectItem>
                      <SelectItem value="file">File Upload</SelectItem>
                      <SelectItem value="stream">Streaming</SelectItem>
                      <SelectItem value="webhook">Webhook</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="schedule">Schedule (Cron)</Label>
                  <Input
                    id="schedule"
                    value={newPipeline.schedule}
                    onChange={(e) =>
                      setNewPipeline({ ...newPipeline, schedule: e.target.value })
                    }
                    placeholder="0 * * * *"
                  />
                  <p className="text-xs text-muted-foreground">
                    Example: &quot;0 * * * *&quot; for every hour, &quot;0 0 * * *&quot; for daily at midnight
                  </p>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createMutation.mutate(newPipeline)}
                  disabled={createMutation.isPending || !newPipeline.name}
                >
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className={`mr-2 ${ICON_SIZE_CLASS} animate-spin`} />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className={`mr-2 ${ICON_SIZE_CLASS}`} />
                      Create Pipeline
                    </>
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Pipelines</CardTitle>
            <GitBranch className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pipelines?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <Loader2 className={`${ICON_SIZE_CLASS} text-green-500`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {pipelines?.filter((p) => p.status === "running").length || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Records Processed</CardTitle>
            <Database className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(MOCK_RECORDS_PROCESSED)}</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Duration</CardTitle>
            <Clock className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4m 32s</div>
            <p className="text-xs text-muted-foreground">Per run</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className={`absolute left-3 top-1/2 -translate-y-1/2 ${ICON_SIZE_CLASS} text-muted-foreground`} />
          <Input
            placeholder="Search pipelines..."
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
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Pipelines Table */}
      <Card>
        <CardHeader>
          <CardTitle>Pipelines</CardTitle>
          <CardDescription>
            View and manage all your data processing pipelines
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
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
                  <TableHead>Status</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Records</TableHead>
                  <TableHead>Last Run</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPipelines?.map((pipeline) => (
                  <TableRow key={pipeline.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <GitBranch className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
                        <div>
                          <p>{pipeline.name}</p>
                          {pipeline.description && (
                            <p className="text-xs text-muted-foreground truncate max-w-50">
                              {pipeline.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(pipeline.status)}
                        <Badge variant={getStatusBadgeVariant(pipeline.status)}>
                          {pipeline.status}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{pipeline.source_type || "database"}</Badge>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {pipeline.schedule || "Manual"}
                      </code>
                    </TableCell>
                    <TableCell>{formatNumber(pipeline.records_processed || 0)}</TableCell>
                    <TableCell>{pipeline.last_run ? formatDate(pipeline.last_run) : "Never"}</TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className={ICON_SIZE_CLASS} />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem onClick={() => setSelectedPipeline(pipeline)}>
                            <Eye className={`mr-2 ${ICON_SIZE_CLASS}`} />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => setSelectedPipeline(pipeline)}>
                            <BarChart3 className={`mr-2 ${ICON_SIZE_CLASS}`} />
                            View Metrics
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {pipeline.status === "running" ? (
                            <DropdownMenuItem
                              onClick={() => stopMutation.mutate(pipeline.id)}
                              disabled={stopMutation.isPending}
                            >
                              <Square className={`mr-2 ${ICON_SIZE_CLASS}`} />
                              Stop
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem
                              onClick={() => runMutation.mutate(pipeline.id)}
                              disabled={runMutation.isPending}
                            >
                              <Play className={`mr-2 ${ICON_SIZE_CLASS}`} />
                              Run Now
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => deleteMutation.mutate(pipeline.id)}
                            className="text-red-600"
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className={`mr-2 ${ICON_SIZE_CLASS}`} />
                            Delete
                          </DropdownMenuItem>
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

      {/* Pipeline Details Dialog */}
      <Dialog open={Boolean(selectedPipeline)} onOpenChange={() => setSelectedPipeline(null)}>
        <DialogContent className="sm:max-w-175">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              {selectedPipeline?.name}
            </DialogTitle>
            <DialogDescription>Pipeline details and performance metrics</DialogDescription>
          </DialogHeader>
          {selectedPipeline && (
            <div className="space-y-6">
              {/* Pipeline Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Status</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedPipeline.status)}
                    <span className="font-medium capitalize">{selectedPipeline.status}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Source Type</p>
                  <p className="font-medium">{selectedPipeline.source_type || "Database"}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Schedule</p>
                  <code className="text-sm bg-muted px-2 py-1 rounded">
                    {selectedPipeline.schedule || "Manual"}
                  </code>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Records Processed</p>
                  <p className="font-medium">
                    {formatNumber(selectedPipeline.records_processed || 0)}
                  </p>
                </div>
              </div>

              {/* Progress (if running) */}
              {selectedPipeline.status === "running" && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>67%</span>
                  </div>
                  <Progress value={67} />
                </div>
              )}

              {/* Performance Chart */}
              <div>
                <h4 className="font-medium mb-4">Processing History</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={metricsData}>
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
                    <Line
                      type="monotone"
                      dataKey="records"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: "#3b82f6" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Description */}
              {selectedPipeline.description && (
                <div className="border-t pt-4">
                  <p className="text-sm text-muted-foreground mb-1">Description</p>
                  <p>{selectedPipeline.description}</p>
                </div>
              )}

              {/* Metadata */}
              <div className="border-t pt-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Created:</span>{" "}
                    {formatDate(selectedPipeline.created_at)}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Last Run:</span>{" "}
                    {selectedPipeline.last_run
                      ? formatDate(selectedPipeline.last_run)
                      : "Never"}
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedPipeline(null)}>
              Close
            </Button>
            {selectedPipeline?.status === "running" ? (
              <Button
                variant="secondary"
                onClick={() => {
                  stopMutation.mutate(selectedPipeline.id);
                  setSelectedPipeline(null);
                }}
              >
                <Square className={`mr-2 ${ICON_SIZE_CLASS}`} />
                Stop Pipeline
              </Button>
            ) : (
              <Button
                onClick={() => {
                  if (selectedPipeline) {
                    runMutation.mutate(selectedPipeline.id);
                    setSelectedPipeline(null);
                  }
                }}
              >
                <Play className={`mr-2 ${ICON_SIZE_CLASS}`} />
                Run Now
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
