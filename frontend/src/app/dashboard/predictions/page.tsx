"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { predictionsApi, modelsApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import {
  Zap,
  Brain,
  AlertTriangle,
  TrendingUp,
  Users,
  Play,
  Copy,
  Clock,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { formatPercentage, formatDateTime } from "@/lib/utils";
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

interface PredictionResult {
  prediction: number | string;
  confidence: number;
  model_id: string;
  timestamp: string;
  features?: Record<string, unknown>;
}

export default function PredictionsPage() {
  // Constants for magic numbers
  const ICON_SIZE_CLASS = "h-4 w-4";
  const LARGE_ICON_SIZE_CLASS = "h-12 w-12";
  const HIGH_CONFIDENCE_LEVEL = 0.95;
  const LOW_CONFIDENCE_LEVEL = 0.9;
  const MOCK_PREDICTIONS_TODAY = 1284;
  const MOCK_PREDICTIONS_INCREASE = 12;
  const MOCK_LATENCY_MS = 42;
  const MOCK_P99_LATENCY_MS = 120;
  const MOCK_SUCCESS_RATE = 99.8;
  const MOCK_FAILURES_TODAY = 2;
  const PREDICTION_METRICS_DATA = [
    { time: "00:00", predictions: 45, accuracy: 94 },
    { time: "04:00", predictions: 32, accuracy: 92 },
    { time: "08:00", predictions: 78, accuracy: 96 },
    { time: "12:00", predictions: 120, accuracy: 95 },
    { time: "16:00", predictions: 145, accuracy: 97 },
    { time: "20:00", predictions: 98, accuracy: 93 },
    { time: "Now", predictions: 67, accuracy: 95 },
  ];
  const [singlePredictionInput, setSinglePredictionInput] = useState("");
  const [batchInput, setBatchInput] = useState("");
  const [selectedModel, setSelectedModel] = useState("anomaly_detection");
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);
  const [batchResults, setBatchResults] = useState<PredictionResult[] | null>(null);

  // Fetch available models
  const { data: modelsData } = useQuery({
    queryKey: ["models"],
    queryFn: () => modelsApi.list(),
  });

  const models = modelsData?.models || [];
  const activeModels = models.filter((m) => m.status === "deployed");

  // Single prediction mutation
  const singlePredictionMutation = useMutation({
    mutationFn: (data: { model_id: string; features: Record<string, unknown> }) =>
      predictionsApi.predict(data),
    onSuccess: (data) => {
      setPredictionResult(data as unknown as PredictionResult);
      toast.success("Prediction completed successfully");
    },
    onError: () => {
      toast.error("Prediction failed");
    },
  });

  // Batch prediction mutation
  const batchPredictionMutation = useMutation({
    mutationFn: (instances: Record<string, unknown>[]) =>
      predictionsApi.batchPredict({ model_id: selectedModel, instances }),
    onSuccess: (data) => {
      setBatchResults(data.predictions as unknown as PredictionResult[]);
      toast.success(`Batch prediction completed: ${data.predictions.length} results`);
    },
    onError: () => {
      toast.error("Batch prediction failed");
    },
  });

  // Anomaly detection mutation
  const anomalyMutation = useMutation({
    mutationFn: (features: Record<string, unknown>) => predictionsApi.detectAnomaly({ features }),
    onSuccess: (data) => {
      setPredictionResult({
        prediction: data.is_anomaly ? "Anomaly Detected" : "Normal",
        confidence: data.anomaly_score,
        model_id: "anomaly_detection",
        timestamp: new Date().toISOString(),
      });
      toast.success("Anomaly detection completed");
    },
    onError: () => {
      toast.error("Anomaly detection failed");
    },
  });

  // Forecast mutation
  const forecastMutation = useMutation({
    mutationFn: (params: { periods: number; frequency: string }) =>
      predictionsApi.generateForecast(params),
    onSuccess: (data) => {
      setPredictionResult({
        prediction: `${data.forecasts.length} periods forecasted`,
        confidence: data.confidence_level ? HIGH_CONFIDENCE_LEVEL : LOW_CONFIDENCE_LEVEL,
        model_id: "demand_forecasting",
        timestamp: new Date().toISOString(),
        features: { forecasts: data.forecasts },
      });
      toast.success("Forecast completed");
    },
    onError: () => {
      toast.error("Forecast failed");
    },
  });

  // Churn prediction mutation
  const churnMutation = useMutation({
    mutationFn: (customerId: string) => predictionsApi.predictChurn({ customer_id: customerId }),
    onSuccess: (data) => {
      setPredictionResult({
        prediction: data.will_churn ? "High Churn Risk" : "Low Churn Risk",
        confidence: data.churn_probability,
        model_id: "churn_prediction",
        timestamp: new Date().toISOString(),
        features: {
          risk_factors: data.risk_factors,
          top_risk_factors: data.top_risk_factors,
        },
      });
      toast.success("Churn prediction completed");
    },
    onError: () => {
      toast.error("Churn prediction failed");
    },
  });

  const handleSinglePrediction = () => {
    try {
      const features = JSON.parse(singlePredictionInput);
      singlePredictionMutation.mutate({ model_id: selectedModel, features });
    } catch {
      toast.error("Invalid JSON input");
    }
  };

  const handleBatchPrediction = () => {
    try {
      const data = JSON.parse(batchInput);
      if (!Array.isArray(data)) {
        toast.error("Batch input must be an array");
        return;
      }
      batchPredictionMutation.mutate(data);
    } catch {
      toast.error("Invalid JSON input");
    }
  };

  const renderPredictionResult = () => {
    if (predictionResult) {
      return (
        <div className="space-y-4">
          <div className="p-6 bg-muted/50 rounded-lg text-center">
            <p className="text-sm text-muted-foreground mb-2">Prediction</p>
            <p className="text-4xl font-bold">{predictionResult.prediction}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-muted/50 rounded-lg">
              <p className="text-sm text-muted-foreground">Confidence</p>
              <p className="text-2xl font-bold">
                {formatPercentage(predictionResult.confidence)}
              </p>
            </div>
            <div className="p-4 bg-muted/50 rounded-lg">
              <p className="text-sm text-muted-foreground">Model</p>
              <p className="text-lg font-medium">{predictionResult.model_id}</p>
            </div>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground mb-2">Timestamp</p>
            <p className="font-mono text-sm">
              {formatDateTime(predictionResult.timestamp)}
            </p>
          </div>
          {predictionResult.features && (
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">Additional Info</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    navigator.clipboard.writeText(
                      JSON.stringify(predictionResult.features, null, 2)
                    );
                    toast.success("Copied to clipboard");
                  }}
                >
                  <Copy className={ICON_SIZE_CLASS} />
                </Button>
              </div>
              <pre className="font-mono text-xs overflow-auto max-h-32">
                {JSON.stringify(predictionResult.features, null, 2)}
              </pre>
            </div>
          )}
        </div>
      );
    } else if (batchResults) {
      return (
        <div className="space-y-4">
          <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
            <p className="font-medium text-green-600">
              Batch Complete: {batchResults.length} predictions
            </p>
          </div>
          <div className="max-h-64 overflow-auto space-y-2">
            {batchResults.map((result, idx) => (
              <div
                key={idx}
                className="p-3 bg-muted/50 rounded-lg flex justify-between items-center"
              >
                <span>Item {idx + 1}</span>
                <Badge>{String(result.prediction)}</Badge>
              </div>
            ))}
          </div>
        </div>
      );
    } else {
      return (
        <div className="text-center py-12 text-muted-foreground">
          <Zap className={`${LARGE_ICON_SIZE_CLASS} mx-auto mb-4 opacity-50`} />
          <p>Run a prediction to see results here</p>
        </div>
      );
    }
  };

  const isLoading =
    singlePredictionMutation.isPending ||
    batchPredictionMutation.isPending ||
    anomalyMutation.isPending ||
    forecastMutation.isPending ||
    churnMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Predictions</h1>
          <p className="text-muted-foreground">
            Run ML predictions using your deployed models
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today&apos;s Predictions</CardTitle>
            <Zap className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{MOCK_PREDICTIONS_TODAY.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-500">+{MOCK_PREDICTIONS_INCREASE}%</span> from yesterday
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg. Latency</CardTitle>
            <Clock className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{MOCK_LATENCY_MS}ms</div>
            <p className="text-xs text-muted-foreground">P99: {MOCK_P99_LATENCY_MS}ms</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle2 className={`${ICON_SIZE_CLASS} text-green-500`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{MOCK_SUCCESS_RATE}%</div>
            <p className="text-xs text-muted-foreground">{MOCK_FAILURES_TODAY} failures today</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Models</CardTitle>
            <Brain className={`${ICON_SIZE_CLASS} text-muted-foreground`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeModels.length}</div>
            <p className="text-xs text-muted-foreground">Available for inference</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Prediction Input */}
        <Card>
          <CardHeader>
            <CardTitle>Run Prediction</CardTitle>
            <CardDescription>
              Select a model and provide input data to get predictions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="single">Single</TabsTrigger>
                <TabsTrigger value="batch">Batch</TabsTrigger>
                <TabsTrigger value="anomaly">Anomaly</TabsTrigger>
                <TabsTrigger value="forecast">Forecast</TabsTrigger>
                <TabsTrigger value="churn">Churn</TabsTrigger>
              </TabsList>

              <TabsContent value="single" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Model</Label>
                  <Select value={selectedModel} onValueChange={setSelectedModel}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {activeModels.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          {model.name} (v{model.version})
                        </SelectItem>
                      ))}
                      {activeModels.length === 0 && (
                        <SelectItem value="demo" disabled>
                          No active models
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Input Data (JSON)</Label>
                  <Textarea
                    placeholder='{"feature1": 0.5, "feature2": 1.2, "feature3": "value"}'
                    value={singlePredictionInput}
                    onChange={(e) => setSinglePredictionInput(e.target.value)}
                    rows={6}
                    className="font-mono text-sm"
                  />
                </div>
                <Button
                  onClick={handleSinglePrediction}
                  disabled={isLoading || !singlePredictionInput}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className={`mr-2 ${ICON_SIZE_CLASS} animate-spin`} />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Play className={`mr-2 ${ICON_SIZE_CLASS}`} />
                      Run Prediction
                    </>
                  )}
                </Button>
              </TabsContent>

              <TabsContent value="batch" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Batch Input (JSON Array)</Label>
                  <Textarea
                    placeholder='[{"feature1": 0.5}, {"feature1": 0.8}]'
                    value={batchInput}
                    onChange={(e) => setBatchInput(e.target.value)}
                    rows={8}
                    className="font-mono text-sm"
                  />
                </div>
                <Button
                  onClick={handleBatchPrediction}
                  disabled={isLoading || !batchInput}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className={`mr-2 ${ICON_SIZE_CLASS} animate-spin`} />
                      Processing Batch...
                    </>
                  ) : (
                    <>
                      <Play className={`mr-2 ${ICON_SIZE_CLASS}`} />
                      Run Batch Prediction
                    </>
                  )}
                </Button>
              </TabsContent>

              <TabsContent value="anomaly" className="space-y-4 mt-4">
                <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                  <div className="flex items-center gap-2 text-yellow-600">
                    <AlertTriangle className={ICON_SIZE_CLASS} />
                    <span className="font-medium">Anomaly Detection</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Detect unusual patterns in your data using AI
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Data Point (JSON)</Label>
                  <Textarea
                    placeholder='{"metric1": 100, "metric2": 50, "timestamp": "2024-01-15"}'
                    rows={5}
                    className="font-mono text-sm"
                    id="anomaly-input"
                  />
                </div>
                <Button
                  onClick={() => {
                    const input = document.getElementById("anomaly-input") as HTMLTextAreaElement;
                    try {
                      const data = JSON.parse(input.value);
                      anomalyMutation.mutate(data);
                    } catch {
                      toast.error("Invalid JSON");
                    }
                  }}
                  disabled={isLoading}
                  className="w-full"
                >
                  <AlertTriangle className={`mr-2 ${ICON_SIZE_CLASS}`} />
                  Detect Anomalies
                </Button>
              </TabsContent>

              <TabsContent value="forecast" className="space-y-4 mt-4">
                <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <div className="flex items-center gap-2 text-blue-600">
                    <TrendingUp className={ICON_SIZE_CLASS} />
                    <span className="font-medium">Demand Forecasting</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Predict future demand using time series analysis
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Periods</Label>
                    <Input type="number" placeholder="30" id="forecast-periods" defaultValue={30} />
                  </div>
                  <div className="space-y-2">
                    <Label>Frequency</Label>
                    <Select defaultValue="D">
                      <SelectTrigger id="forecast-frequency">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="H">Hourly</SelectItem>
                        <SelectItem value="D">Daily</SelectItem>
                        <SelectItem value="W">Weekly</SelectItem>
                        <SelectItem value="M">Monthly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button
                  onClick={() => {
                    const periods = parseInt(
                      (document.getElementById("forecast-periods") as HTMLInputElement).value
                    );
                    forecastMutation.mutate({ periods, frequency: "D" });
                  }}
                  disabled={isLoading}
                  className="w-full"
                >
                  <TrendingUp className={`mr-2 ${ICON_SIZE_CLASS}`} />
                  Generate Forecast
                </Button>
              </TabsContent>

              <TabsContent value="churn" className="space-y-4 mt-4">
                <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                  <div className="flex items-center gap-2 text-purple-600">
                    <Users className={ICON_SIZE_CLASS} />
                    <span className="font-medium">Churn Prediction</span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Predict customer churn probability and risk factors
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Customer ID</Label>
                  <Input placeholder="CUST-12345" id="customer-id" />
                </div>
                <Button
                  onClick={() => {
                    const customerId = (document.getElementById("customer-id") as HTMLInputElement)
                      .value;
                    if (!customerId) {
                      toast.error("Please enter a customer ID");
                      return;
                    }
                    churnMutation.mutate(customerId);
                  }}
                  disabled={isLoading}
                  className="w-full"
                >
                  <Users className={`mr-2 ${ICON_SIZE_CLASS}`} />
                  Predict Churn Risk
                </Button>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Prediction Result */}
        <Card>
          <CardHeader>
            <CardTitle>Prediction Result</CardTitle>
            <CardDescription>
              View the output from your prediction request
            </CardDescription>
          </CardHeader>
          <CardContent>
            {renderPredictionResult()}
          </CardContent>
        </Card>
      </div>

      {/* Historical Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Prediction Activity</CardTitle>
          <CardDescription>Predictions and accuracy over the last 24 hours</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={historicalData}>
              <defs>
                <linearGradient id="colorPred" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
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
                dataKey="predictions"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorPred)"
              />
              <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
