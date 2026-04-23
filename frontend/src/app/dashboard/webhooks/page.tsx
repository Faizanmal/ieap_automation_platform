"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { webhooksApi } from "@/lib/api";
import { Webhook } from "@/types/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
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
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  Webhook as WebhookIcon,
  Plus,
  Search,
  RefreshCw,
  MoreHorizontal,
  Eye,
  Trash2,
  Send,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  Copy,
} from "lucide-react";
import { formatDateTime, formatRelativeTime } from "@/lib/utils";

const EVENT_TYPES = [
  { id: "prediction.completed", label: "Prediction Completed" },
  { id: "prediction.failed", label: "Prediction Failed" },
  { id: "model.trained", label: "Model Trained" },
  { id: "model.deployed", label: "Model Deployed" },
  { id: "pipeline.started", label: "Pipeline Started" },
  { id: "pipeline.completed", label: "Pipeline Completed" },
  { id: "pipeline.failed", label: "Pipeline Failed" },
  { id: "decision.pending", label: "Decision Pending" },
  { id: "decision.approved", label: "Decision Approved" },
  { id: "decision.rejected", label: "Decision Rejected" },
  { id: "task.completed", label: "Task Completed" },
  { id: "task.failed", label: "Task Failed" },
];

export default function WebhooksPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedWebhook, setSelectedWebhook] = useState<Webhook | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDeliveriesDialogOpen, setIsDeliveriesDialogOpen] = useState(false);
  const [newWebhook, setNewWebhook] = useState({
    name: "",
    url: "",
    events: [] as string[],
    secret: "",
    active: true,
  });

  // Fetch webhooks
  const { data: webhooksData, isLoading, refetch } = useQuery({
    queryKey: ["webhooks"],
    queryFn: () => webhooksApi.list(),
  });

  const webhooks = webhooksData?.webhooks || [];

  // Fetch deliveries for selected webhook
  const { data: deliveriesData, isLoading: deliveriesLoading } = useQuery({
    queryKey: ["webhooks", selectedWebhook?.id, "deliveries"],
    queryFn: () => (selectedWebhook ? webhooksApi.getDeliveries(selectedWebhook.id) : null),
    enabled: Boolean(selectedWebhook) && isDeliveriesDialogOpen,
  });

  const deliveries = deliveriesData?.deliveries || [];

  // Use state for mock data to ensure purity
  const [now] = useState(new Date());

  const mockDeliveries: import("@/types/api").WebhookDelivery[] = useMemo(() => [
    {
      id: "1",
      webhook_id: "mock-1",
      event: "prediction.completed" as import("@/types/api").WebhookEvent,
      payload: {},
      success: true,
      response_code: 200,
      delivered_at: now.toISOString(),
    },
    {
      id: "2",
      webhook_id: "mock-2",
      event: "model.deployed" as import("@/types/api").WebhookEvent,
      payload: {},
      success: true,
      response_code: 200,
      delivered_at: new Date(now.getTime() - 3600000).toISOString(),
    },
    {
      id: "3",
      webhook_id: "mock-3",
      event: "pipeline.completed" as import("@/types/api").WebhookEvent,
      payload: {},
      success: false,
      response_code: 500,
      delivered_at: new Date(now.getTime() - 7200000).toISOString(),
    },
  ], [now]);

  // Create webhook mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof newWebhook) => {
      const { ...rest } = data;
      return webhooksApi.create({ ...rest, events: rest.events as import("@/types/api").WebhookEvent[], name: rest.name, url: rest.url });
    },
    onSuccess: () => {
      toast.success("Webhook created successfully");
      setIsCreateDialogOpen(false);
      setNewWebhook({ name: "", url: "", events: [], secret: "", active: true });
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
    onError: () => {
      toast.error("Failed to create webhook");
    },
  });

  // Delete webhook mutation
  const deleteMutation = useMutation({
    mutationFn: (webhookId: string) => webhooksApi.delete(webhookId),
    onSuccess: () => {
      toast.success("Webhook deleted");
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
    onError: () => {
      toast.error("Failed to delete webhook");
    },
  });

  // Test webhook mutation
  const testMutation = useMutation({
    mutationFn: (webhookId: string) => webhooksApi.test(webhookId),
    onSuccess: () => {
      toast.success("Test webhook sent successfully");
    },
    onError: () => {
      toast.error("Failed to send test webhook");
    },
  });

  // Filter webhooks
  const filteredWebhooks = webhooks?.filter((webhook) => {
    return (
      webhook.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      webhook.url.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const activeWebhooks = webhooks?.filter((w) => w.status === 'active') || [];

  const handleEventToggle = (eventId: string) => {
    setNewWebhook((prev) => ({
      ...prev,
      events: prev.events.includes(eventId)
        ? prev.events.filter((e) => e !== eventId)
        : [...prev.events, eventId],
    }));
  };

  const generateSecret = () => {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    const secret = Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join("");
    setNewWebhook({ ...newWebhook, secret });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Webhooks</h1>
          <p className="text-muted-foreground">
            Configure webhooks to receive real-time event notifications
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Webhook
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-150">
              <DialogHeader>
                <DialogTitle>Create Webhook</DialogTitle>
                <DialogDescription>
                  Configure a new webhook endpoint to receive event notifications
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Webhook Name</Label>
                  <Input
                    id="name"
                    value={newWebhook.name}
                    onChange={(e) => setNewWebhook({ ...newWebhook, name: e.target.value })}
                    placeholder="My Webhook"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="url">Payload URL</Label>
                  <Input
                    id="url"
                    type="url"
                    value={newWebhook.url}
                    onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })}
                    placeholder="https://example.com/webhook"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Secret (for signature verification)</Label>
                  <div className="flex gap-2">
                    <Input
                      value={newWebhook.secret}
                      onChange={(e) => setNewWebhook({ ...newWebhook, secret: e.target.value })}
                      placeholder="Optional: webhook secret"
                      className="font-mono text-sm"
                    />
                    <Button type="button" variant="outline" onClick={generateSecret}>
                      Generate
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Used to sign webhook payloads for verification
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Events</Label>
                  <div className="grid grid-cols-2 gap-2 max-h-48 overflow-auto p-3 border rounded-lg">
                    {EVENT_TYPES.map((event) => (
                      <div key={event.id} className="flex items-center space-x-2">
                        <Checkbox
                          id={event.id}
                          checked={newWebhook.events.includes(event.id)}
                          onCheckedChange={() => handleEventToggle(event.id)}
                        />
                        <label
                          htmlFor={event.id}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                          {event.label}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Active</Label>
                    <p className="text-xs text-muted-foreground">
                      Enable or disable this webhook
                    </p>
                  </div>
                  <Switch
                    checked={newWebhook.active}
                    onCheckedChange={(checked) =>
                      setNewWebhook({ ...newWebhook, active: checked })
                    }
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createMutation.mutate(newWebhook)}
                  disabled={
                    createMutation.isPending ||
                    !newWebhook.name ||
                    !newWebhook.url ||
                    newWebhook.events.length === 0
                  }
                >
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className="mr-2 h-4 w-4" />
                      Create Webhook
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
            <CardTitle className="text-sm font-medium">Total Webhooks</CardTitle>
            <WebhookIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{webhooks?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeWebhooks.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Deliveries Today</CardTitle>
            <Send className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">98.5%</div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search webhooks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Webhooks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Webhooks</CardTitle>
          <CardDescription>
            Manage your webhook endpoints and view delivery history
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredWebhooks?.length === 0 ? (
            <div className="text-center py-12">
              <WebhookIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No webhooks configured</h3>
              <p className="text-muted-foreground mt-2">
                Create your first webhook to receive event notifications
              </p>
              <Button
                className="mt-4"
                onClick={() => setIsCreateDialogOpen(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Webhook
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>URL</TableHead>
                  <TableHead>Events</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Delivery</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredWebhooks?.map((webhook) => (
                  <TableRow key={webhook.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <WebhookIcon className="h-4 w-4 text-muted-foreground" />
                        {webhook.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <code className="text-xs bg-muted px-2 py-1 rounded max-w-50 truncate">
                          {webhook.url}
                        </code>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={() => {
                            navigator.clipboard.writeText(webhook.url);
                            toast.success("URL copied");
                          }}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {webhook.events?.length || 0} events
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {webhook.status === 'active' ? (
                        <Badge variant="default" className="bg-green-500">
                          Active
                        </Badge>
                      ) : (
                        <Badge variant="secondary">Inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {webhook.last_delivery ? (
                        <div className="flex items-center gap-2">
                          {webhook.last_delivery_success ? (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-500" />
                          )}
                          <span className="text-sm">
                            {formatRelativeTime(webhook.last_delivery)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">Never</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem
                            onClick={() => {
                              setSelectedWebhook(webhook);
                              setIsDeliveriesDialogOpen(true);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Deliveries
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => testMutation.mutate(webhook.id)}
                            disabled={testMutation.isPending}
                          >
                            <Send className="mr-2 h-4 w-4" />
                            Send Test
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => deleteMutation.mutate(webhook.id)}
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

      {/* Deliveries Dialog */}
      <Dialog open={isDeliveriesDialogOpen} onOpenChange={setIsDeliveriesDialogOpen}>
        <DialogContent className="sm:max-w-175">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <WebhookIcon className="h-5 w-5" />
              Delivery History
            </DialogTitle>
            <DialogDescription>
              Recent deliveries for {selectedWebhook?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-100 overflow-auto">
            {deliveriesLoading ? (
              <div className="space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : deliveries?.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No deliveries yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {(deliveries.length > 0 ? deliveries : mockDeliveries).map((delivery) => (
                  <div
                    key={delivery.id}
                    className="p-4 border rounded-lg"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        {delivery.success ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500" />
                        )}
                        <div>
                          <p className="font-medium">{delivery.event}</p>
                          <p className="text-sm text-muted-foreground">
                            {formatDateTime(delivery.delivered_at)}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge
                          variant={delivery.success ? "default" : "destructive"}
                        >
                          {delivery.response_code}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeliveriesDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
