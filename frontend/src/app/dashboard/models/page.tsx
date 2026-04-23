"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { modelsApi } from "@/lib/api";
import { ModelInfo, ModelType } from "@/types/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
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
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import {
  Brain,
  Search,
  Filter,
  MoreHorizontal,
  Play,
  Pause,
  Trash2,
  BarChart3,
  RefreshCw,
  Plus,
  Eye,
  Clock,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { formatDate, formatPercentage } from "@/lib/utils";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Constants for magic numbers
const MOCK_ACCURACY = 80;
const MOCK_PRECISION = 100;

const getDialogActionButton = (model: ModelInfo | null, deployMutation: { mutate: (id: string) => void; isPending: boolean }, undeployMutation: { mutate: (id: string) => void; isPending: boolean }, setSelectedModel: (model: ModelInfo | null) => void) => {
  if (!model) return null;
  switch (model.status) {
    case "deployed":
      return (
        <Button
          variant="secondary"
          onClick={() => {
            undeployMutation.mutate(model.id);
            setSelectedModel(null);
          }}
        >
          <Pause className="mr-2 h-4 w-4" />
          Undeploy
        </Button>
      );
    case "ready":
      return (
        <Button
          onClick={() => {
            deployMutation.mutate(model.id);
            setSelectedModel(null);
          }}
        >
          <Play className="mr-2 h-4 w-4" />
          Deploy
        </Button>
      );
    default:
      return null;
  }
};

export default function ModelsPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [isTrainDialogOpen, setIsTrainDialogOpen] = useState(false);
  const [trainConfig, setTrainConfig] = useState({
    name: "",
    modelType: "anomaly_detection",
    epochs: 100,
    learningRate: 0.001,
    batchSize: 32,
  });

  // Fetch models
  const { data: modelsData, isLoading, refetch } = useQuery({
    queryKey: ["models"],
    queryFn: () => modelsApi.list(),
  });

  const models = modelsData?.models || [];

  // Deploy model mutation
  const deployMutation = useMutation({
    mutationFn: (modelId: string) => modelsApi.deploy(modelId),
    onSuccess: () => {
      toast.success("Model deployed successfully");
      queryClient.invalidateQueries({ queryKey: ["models"] });
    },
    onError: () => {
      toast.error("Failed to deploy model");
    },
  });

  // Undeploy model mutation
  const undeployMutation = useMutation({
    mutationFn: (modelId: string) => modelsApi.undeploy(modelId),
    onSuccess: () => {
      toast.success("Model undeployed successfully");
      queryClient.invalidateQueries({ queryKey: ["models"] });
    },
    onError: () => {
      toast.error("Failed to undeploy model");
    },
  });

  // Delete model mutation
  const deleteMutation = useMutation({
    mutationFn: (modelId: string) => modelsApi.delete(modelId),
    onSuccess: () => {
      toast.success("Model deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["models"] });
    },
    onError: () => {
      toast.error("Failed to delete model");
    },
  });

  // Train model mutation
  const trainMutation = useMutation({
    mutationFn: (data: typeof trainConfig) =>
      modelsApi.train({
        model_type: data.modelType as ModelType,
        name: data.name,
        config: {
          epochs: data.epochs,
          learningRate: data.learningRate,
          batchSize: data.batchSize,
        },
      }),
    onSuccess: () => {
      toast.success("Model training started");
      setIsTrainDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ["models"] });
    },
    onError: () => {
      toast.error("Failed to start training");
    },
  });

  // Filter models
  const filteredModels = models.filter((model) => {
    const matchesSearch =
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || model.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "deployed":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "training":
        return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "inactive":
        return <Pause className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  // Mock performance data for charts
  const performanceData = [
    { date: "Mon", accuracy: 92, predictions: 1200 },
    { date: "Tue", accuracy: 94, predictions: 1350 },
    { date: "Wed", accuracy: 93, predictions: 1180 },
    { date: "Thu", accuracy: 95, predictions: 1420 },
    { date: "Fri", accuracy: 96, predictions: 1560 },
    { date: "Sat", accuracy: 94, predictions: 980 },
    { date: "Sun", accuracy: 95, predictions: 1100 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">ML Models</h1>
          <p className="text-muted-foreground">
            Manage and monitor your machine learning models
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Dialog open={isTrainDialogOpen} onOpenChange={setIsTrainDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Train Model
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-125">
              <DialogHeader>
                <DialogTitle>Train New Model</DialogTitle>
                <DialogDescription>
                  Configure and start training a new machine learning model
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Model Name</Label>
                  <Input
                    id="name"
                    value={trainConfig.name}
                    onChange={(e) =>
                      setTrainConfig({ ...trainConfig, name: e.target.value })
                    }
                    placeholder="my-new-model"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="modelType">Model Type</Label>
                  <Select
                    value={trainConfig.modelType}
                    onValueChange={(value) =>
                      setTrainConfig({ ...trainConfig, modelType: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select model type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="anomaly_detection">Anomaly Detection</SelectItem>
                      <SelectItem value="demand_forecasting">Demand Forecasting</SelectItem>
                      <SelectItem value="churn_prediction">Churn Prediction</SelectItem>
                      <SelectItem value="fraud_detection">Fraud Detection</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="epochs">Epochs</Label>
                    <Input
                      id="epochs"
                      type="number"
                      value={trainConfig.epochs}
                      onChange={(e) =>
                        setTrainConfig({ ...trainConfig, epochs: parseInt(e.target.value) })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="batchSize">Batch Size</Label>
                    <Input
                      id="batchSize"
                      type="number"
                      value={trainConfig.batchSize}
                      onChange={(e) =>
                        setTrainConfig({ ...trainConfig, batchSize: parseInt(e.target.value) })
                      }
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="learningRate">Learning Rate</Label>
                  <Input
                    id="learningRate"
                    type="number"
                    step="0.0001"
                    value={trainConfig.learningRate}
                    onChange={(e) =>
                      setTrainConfig({ ...trainConfig, learningRate: parseFloat(e.target.value) })
                    }
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsTrainDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => trainMutation.mutate(trainConfig)}
                  disabled={trainMutation.isPending || !trainConfig.name}
                >
                  {trainMutation.isPending ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Training...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Start Training
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
            <CardTitle className="text-sm font-medium">Total Models</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Deployed</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {models.filter((m) => m.status === "deployed").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Training</CardTitle>
            <RefreshCw className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {models.filter((m) => m.status === "training").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Accuracy</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {models.length > 0
                ? formatPercentage(
                  models.reduce((sum, m) => sum + (m.metrics?.accuracy || 0), 0) / models.length
                )
                : "N/A"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search models..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-45">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="deployed">Deployed</SelectItem>
            <SelectItem value="ready">Ready</SelectItem>
            <SelectItem value="training">Training</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="deprecated">Deprecated</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Models Table */}
      <Card>
        <CardHeader>
          <CardTitle>Models</CardTitle>
          <CardDescription>
            A list of all your machine learning models with their current status and performance metrics
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
                  <TableHead>Type</TableHead>
                  <TableHead>Version</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredModels?.map((model) => (
                  <TableRow key={model.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4 text-muted-foreground" />
                        {model.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{model.type.replace("_", " ")}</Badge>
                    </TableCell>
                    <TableCell>v{model.version}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(model.status)}
                        <span className="capitalize">{model.status}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {model.metrics?.accuracy ? formatPercentage(model.metrics.accuracy) : "N/A"}
                    </TableCell>
                    <TableCell>{formatDate(model.updated_at)}</TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem onClick={() => setSelectedModel(model)}>
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => setSelectedModel(model)}>
                            <BarChart3 className="mr-2 h-4 w-4" />
                            View Metrics
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {getModelActionItem(model, deployMutation, undeployMutation)}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => deleteMutation.mutate(model.id)}
                            className="text-red-600"
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
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

      {/* Model Details Dialog */}
      <Dialog open={Boolean(selectedModel)} onOpenChange={() => setSelectedModel(null)}>
        <DialogContent className="sm:max-w-175">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              {selectedModel?.name}
            </DialogTitle>
            <DialogDescription>
              Model details and performance metrics
            </DialogDescription>
          </DialogHeader>
          {selectedModel && (
            <div className="space-y-6">
              {/* Model Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Type</p>
                  <p className="font-medium">{selectedModel.type.replace("_", " ")}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Version</p>
                  <p className="font-medium">v{selectedModel.version}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Status</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedModel.status)}
                    <span className="font-medium capitalize">{selectedModel.status}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Accuracy</p>
                  <p className="font-medium">
                    {selectedModel.metrics?.accuracy
                      ? formatPercentage(selectedModel.metrics.accuracy)
                      : "N/A"}
                  </p>
                </div>
              </div>

              {/* Performance Chart */}
              <div>
                <h4 className="font-medium mb-4">Performance Over Time</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="date" className="text-xs" />
                    <YAxis className="text-xs" domain={[MOCK_ACCURACY, MOCK_PRECISION]} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="accuracy"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: "#3b82f6" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Metadata */}
              <div className="border-t pt-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Created:</span>{" "}
                    {formatDate(selectedModel.created_at)}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Last Updated:</span>{" "}
                    {formatDate(selectedModel.updated_at)}
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedModel(null)}>
              Close
            </Button>
            {getDialogActionButton(selectedModel, deployMutation, undeployMutation, setSelectedModel)}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
