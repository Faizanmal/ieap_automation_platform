"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { decisionsApi } from "@/lib/api";
import { Decision } from "@/types/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
} from "@/components/ui/dialog";
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
  CheckCircle2,
  XCircle,
  Clock,
  Search,
  Filter,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Eye,
  AlertTriangle,
  ArrowRight,
  Loader2,
  FileText,
} from "lucide-react";
import { formatDateTime, formatRelativeTime, formatPercentage } from "@/lib/utils";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

// Constants for magic numbers
const BORDER_RADIUS = 4;
const MOCK_GRID_SIZE = 8;
const ID_DISPLAY_LENGTH = 8;

export default function DecisionsPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");

  // Fetch decisions
  const { data: decisionsData, isLoading, refetch } = useQuery({
    queryKey: ["decisions"],
    queryFn: () => decisionsApi.list(),
  });

  const decisions = decisionsData?.decisions || [];

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (decisionId: string) => decisionsApi.approve(decisionId),
    onSuccess: () => {
      toast.success("Decision approved");
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
      setSelectedDecision(null);
    },
    onError: () => {
      toast.error("Failed to approve decision");
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      decisionsApi.reject(id, reason),
    onSuccess: () => {
      toast.success("Decision rejected");
      queryClient.invalidateQueries({ queryKey: ["decisions"] });
      setSelectedDecision(null);
      setRejectionReason("");
    },
    onError: () => {
      toast.error("Failed to reject decision");
    },
  });

  // Filter decisions
  const filteredDecisions = decisions?.filter((decision) => {
    const matchesSearch =
      (decision.type?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
      decision.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      decision.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || decision.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const pendingDecisions = decisions?.filter((d) => d.status === "pending") || [];
  const approvedDecisions = decisions?.filter((d) => d.status === "approved") || [];
  const rejectedDecisions = decisions?.filter((d) => d.status === "rejected") || [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "approved":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "rejected":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case "approved":
        return "default";
      case "rejected":
        return "destructive";
      case "pending":
        return "secondary";
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

  // Chart data
  const statusData = [
    { name: "Approved", value: approvedDecisions.length, color: "#10b981" },
    { name: "Rejected", value: rejectedDecisions.length, color: "#ef4444" },
    { name: "Pending", value: pendingDecisions.length, color: "#f59e0b" },
  ];

  const weeklyData = [
    { day: "Mon", approved: 12, rejected: 3, pending: 5 },
    { day: "Tue", approved: 15, rejected: 2, pending: 8 },
    { day: "Wed", approved: 18, rejected: 5, pending: 3 },
    { day: "Thu", approved: 22, rejected: 4, pending: 6 },
    { day: "Fri", approved: 19, rejected: 2, pending: 4 },
    { day: "Sat", approved: 8, rejected: 1, pending: 2 },
    { day: "Sun", approved: 5, rejected: 0, pending: 1 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Decision Engine</h1>
          <p className="text-muted-foreground">
            Review and manage autonomous system decisions
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Alert Banner for Pending Decisions */}
      {pendingDecisions.length > 0 && (
        <Card className="border-yellow-500/50 bg-yellow-500/5">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-6 w-6 text-yellow-500" />
                <div>
                  <p className="font-medium">
                    {pendingDecisions.length} decision{pendingDecisions.length !== 1 ? "s" : ""}{" "}
                    awaiting review
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Please review and approve or reject pending decisions
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStatusFilter("pending")}
              >
                View Pending
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Decisions</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{decisions?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingDecisions.length}</div>
            <p className="text-xs text-muted-foreground">Awaiting review</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{approvedDecisions.length}</div>
            <p className="text-xs text-muted-foreground">
              {decisions?.length
                ? formatPercentage(approvedDecisions.length / decisions.length)
                : "0%"}{" "}
              approval rate
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rejected</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rejectedDecisions.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Status Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Decision Distribution</CardTitle>
            <CardDescription>Current status breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
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
            <div className="flex justify-center gap-4">
              {statusData.map((status) => (
                <div key={status.name} className="flex items-center gap-2">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: status.color }}
                  />
                  <span className="text-sm text-muted-foreground">
                    {status.name}: {status.value}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Weekly Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Activity</CardTitle>
            <CardDescription>Decision outcomes over the past week</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={weeklyData}>
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
                <Bar dataKey="approved" fill="#10b981" radius={[BORDER_RADIUS, BORDER_RADIUS, 0, 0]} />
                <Bar dataKey="rejected" fill="#ef4444" radius={[BORDER_RADIUS, BORDER_RADIUS, 0, 0]} />
                <Bar dataKey="pending" fill="#f59e0b" radius={[BORDER_RADIUS, BORDER_RADIUS, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search decisions..."
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
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Decisions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Decisions</CardTitle>
          <CardDescription>
            Review and take action on system decisions
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
                  <TableHead>ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDecisions?.map((decision) => (
                  <TableRow key={decision.id}>
                    <TableCell className="font-mono text-sm">
                      {decision.id.slice(0, ID_DISPLAY_LENGTH)}...
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{decision.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(
                          decision.priority || "medium"
                        )}`}
                      >
                        {decision.priority || "medium"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(decision.status)}
                        <Badge variant={getStatusBadgeVariant(decision.status)}>
                          {decision.status}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      {decision.confidence
                        ? formatPercentage(decision.confidence)
                        : "N/A"}
                    </TableCell>
                    <TableCell>{formatRelativeTime(decision.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedDecision(decision)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {decision.status === "pending" && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-green-600 hover:text-green-700 hover:bg-green-100"
                              onClick={() => approveMutation.mutate(decision.id)}
                              disabled={approveMutation.isPending}
                            >
                              <ThumbsUp className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700 hover:bg-red-100"
                              onClick={() => setSelectedDecision(decision)}
                              disabled={rejectMutation.isPending}
                            >
                              <ThumbsDown className="h-4 w-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Decision Details Dialog */}
      <Dialog open={Boolean(selectedDecision)} onOpenChange={() => setSelectedDecision(null)}>
        <DialogContent className="sm:max-w-150">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedDecision && getStatusIcon(selectedDecision.status)}
              Decision Details
            </DialogTitle>
            <DialogDescription>
              Review decision information and take action
            </DialogDescription>
          </DialogHeader>
          {selectedDecision && (
            <div className="space-y-6">
              {/* Decision Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">ID</p>
                  <p className="font-mono text-sm">{selectedDecision.id}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Type</p>
                  <Badge variant="outline">{selectedDecision.type}</Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Status</p>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedDecision.status)}
                    <span className="font-medium capitalize">{selectedDecision.status}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Priority</p>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(
                      selectedDecision.priority || "medium"
                    )}`}
                  >
                    {selectedDecision.priority || "medium"}
                  </span>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Confidence</p>
                  <p className="font-medium">
                    {selectedDecision.confidence
                      ? formatPercentage(selectedDecision.confidence)
                      : "N/A"}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Created</p>
                  <p className="font-medium">{formatDateTime(selectedDecision.created_at)}</p>
                </div>
              </div>

              {/* Description */}
              {selectedDecision.description && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Description</p>
                  <p className="p-3 bg-muted/50 rounded-lg">{selectedDecision.description}</p>
                </div>
              )}

              {/* Context Data */}
              {selectedDecision.context && (
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Context Data</p>
                  <pre className="p-3 bg-muted/50 rounded-lg font-mono text-xs overflow-auto max-h-32">
                    {JSON.stringify(selectedDecision.context, null, 2)}
                  </pre>
                </div>
              )}

              {/* Rejection Reason Input (for pending decisions) */}
              {selectedDecision.status === "pending" && (
                <div className="border-t pt-4">
                  <Label htmlFor="rejection-reason">Rejection Reason (optional)</Label>
                  <Textarea
                    id="rejection-reason"
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="Provide a reason for rejection..."
                    rows={3}
                    className="mt-2"
                  />
                </div>
              )}

              {/* Rejection Reason Display (for rejected decisions) */}
              {selectedDecision.status === "rejected" && selectedDecision.rejection_reason && (
                <div className="border-t pt-4">
                  <p className="text-sm text-muted-foreground mb-2">Rejection Reason</p>
                  <p className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-700">
                    {selectedDecision.rejection_reason}
                  </p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedDecision(null)}>
              Close
            </Button>
            {selectedDecision?.status === "pending" && (
              <>
                <Button
                  variant="destructive"
                  onClick={() =>
                    rejectMutation.mutate({
                      id: selectedDecision.id,
                      reason: rejectionReason,
                    })
                  }
                  disabled={rejectMutation.isPending}
                >
                  {rejectMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <ThumbsDown className="mr-2 h-4 w-4" />
                  )}
                  Reject
                </Button>
                <Button
                  onClick={() => approveMutation.mutate(selectedDecision.id)}
                  disabled={approveMutation.isPending}
                >
                  {approveMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <ThumbsUp className="mr-2 h-4 w-4" />
                  )}
                  Approve
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
