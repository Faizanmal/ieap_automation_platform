"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
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
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  Settings,
  Database,
  HardDrive,
  Server,
  Flag,
  Key,
  Shield,
  XCircle,
  Loader2,
  Plus,
  Download,
  Upload,
  Archive,
  Trash2,
  RotateCcw,
  ScrollText,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

// Constants for magic numbers
const BACKUPS_LIMIT = 10;
const BYTES_BASE = 1024;
const BYTES_IN_KB = BYTES_BASE;
const BYTES_IN_MB = BYTES_IN_KB * BYTES_IN_KB;
const BYTES_IN_GB = BYTES_IN_MB * BYTES_IN_KB;
const BYTES_IN_TB = BYTES_IN_GB * BYTES_IN_KB;
const BACKUP_SIZE_MB = 256;
const BACKUP_SIZE_MB_2 = 64;
const CACHE_SIZE_BYTES = 128 * BYTES_IN_MB;
const ONE_HOUR_MS = 60 * 60 * 1000;
const TWO_HOURS_MS = 2 * ONE_HOUR_MS;
const RETENTION_DAYS = 30;
const RETENTION_HOURS = 24;
const RETENTION_MINUTES = 60;
const RETENTION_SECONDS = 60;
const MS_IN_SECOND = 1000;
const CACHE_SIZE_MB = 15;
const CPU_CORES = 42;
const MOCK_TABLES = 42;
const DISK_SIZE_GB = 128;
const MEMORY_USAGE_PERCENT = 94.5;
const CACHE_SIZE_MB_2 = 5.5;
const BACKUP_INTERVAL_MS = MS_IN_SECOND;
const RETENTION_TOTAL_MS = RETENTION_DAYS * RETENTION_HOURS * RETENTION_MINUTES * RETENTION_SECONDS * MS_IN_SECOND;
const RETENTION_15_DAYS_MS = 15 * ONE_DAY_MS;
const MOCK_CONNECTIONS = 15;
const MOCK_SLOW_QUERIES = 3;
const MOCK_TIMEOUT_S = 30;
const MOCK_ITEMS_COUNT = 3;
const DISK_SIZE_TB = BYTES_IN_TB / BYTES_IN_GB; // 1024
const DISK_SIZE_PERCENT = 100;

export default function AdminSystemPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("config");
  const [isBackupDialogOpen, setIsBackupDialogOpen] = useState(false);

  // Fetch system config
  const { data: systemConfig } = useQuery({
    queryKey: ["admin", "system-config"],
    queryFn: adminApi.getSystemConfig,
  });

  // Fetch feature flags
  const { data: featureFlags, isLoading: flagsLoading, refetch: refetchFlags } = useQuery({
    queryKey: ["admin", "feature-flags"],
    queryFn: adminApi.getFeatureFlags,
  });

  // Fetch backups
  const { data: backups, isLoading: backupsLoading, refetch: refetchBackups } = useQuery({
    queryKey: ["admin", "backups"],
    queryFn: () => adminApi.listBackups(BACKUPS_LIMIT),
  });

  // Fetch audit logs
  const { data: auditLogs, isLoading: logsLoading } = useQuery({
    queryKey: ["admin", "audit-logs"],
    queryFn: () => adminApi.getAuditLogs({ limit: 50 }),
  });

  // Fetch API keys
  const { data: apiKeys, isLoading: keysLoading } = useQuery({
    queryKey: ["admin", "api-keys"],
    queryFn: () => adminApi.listApiKeys(),
  });

  // Fetch cache stats
  const { data: cacheStats } = useQuery({
    queryKey: ["admin", "cache-stats"],
    queryFn: adminApi.getCacheStats,
  });

  // Fetch database stats
  const { data: dbStats } = useQuery({
    queryKey: ["admin", "database-stats"],
    queryFn: adminApi.getDatabaseStats,
  });

  // Update feature flag mutation
  const updateFlagMutation = useMutation({
    mutationFn: ({ flagName, enabled }: { flagName: string; enabled: boolean }) =>
      adminApi.updateFeatureFlag(flagName, enabled),
    onSuccess: () => {
      toast.success("Feature flag updated");
      refetchFlags();
    },
    onError: () => {
      toast.error("Failed to update feature flag");
    },
  });

  // Create backup mutation
  const createBackupMutation = useMutation({
    mutationFn: () => adminApi.createBackup({ backup_type: "full", include_logs: false }),
    onSuccess: () => {
      toast.success("Backup created successfully");
      setIsBackupDialogOpen(false);
      refetchBackups();
    },
    onError: () => {
      toast.error("Failed to create backup");
    },
  });

  // Revoke API key mutation
  const revokeKeyMutation = useMutation({
    mutationFn: (keyId: string) => adminApi.revokeApiKey(keyId),
    onSuccess: () => {
      toast.success("API key revoked");
      queryClient.invalidateQueries({ queryKey: ["admin", "api-keys"] });
    },
    onError: () => {
      toast.error("Failed to revoke API key");
    },
  });

  // Mock data
  const mockFeatureFlags = featureFlags || {
    ai_predictions: true,
    batch_processing: true,
    real_time_pipeline: true,
    autonomous_decisions: false,
    advanced_analytics: true,
    webhook_integrations: true,
    multi_tenant: false,
    custom_models: true,
  };

  // Use state for mock data to ensure purity
  const [now] = useState(new Date());

  const mockBackups = useMemo(() => backups || [
    {
      backup_id: "backup-001",
      type: "full",
      size_bytes: BYTES_IN_MB * BACKUP_SIZE_MB,
      created_at: now.toISOString(),
      location: "s3://ieap-backups/2024/",
      status: "completed",
    },
    {
      backup_id: "backup-002",
      type: "incremental",
      size_bytes: BYTES_IN_MB * BACKUP_SIZE_MB_2,
      created_at: new Date(now.getTime() - ONE_DAY_MS).toISOString(),
      location: "s3://ieap-backups/2024/",
      status: "completed",
    },
  ], [backups, now]);

  const mockAuditLogs = useMemo(() => auditLogs || [
    {
      id: "log-001",
      user_id: "admin",
      event_type: "system",
      action: "cache_cleared",
      resource: "system",
      timestamp: now.toISOString(),
      details: { pattern: "*" },
    },
    {
      id: "log-002",
      user_id: "admin",
      event_type: "user",
      action: "user_deactivated",
      resource: "users/123",
      timestamp: new Date(now.getTime() - ONE_HOUR_MS).toISOString(),
      details: { reason: "inactive" },
    },
    {
      id: "log-003",
      user_id: "system",
      event_type: "backup",
      action: "backup_created",
      resource: "backups",
      timestamp: new Date(now.getTime() - TWO_HOURS_MS).toISOString(),
      details: { type: "full" },
    },
  ], [auditLogs, now]);

  const mockApiKeys = useMemo(() => apiKeys || [
    {
      id: "key-001",
      name: "Production API",
      key_prefix: "ieap_prod_",
      user_id: "admin",
      created_at: new Date(now.getTime() - RETENTION_TOTAL_MS).toISOString(),
      last_used: now.toISOString(),
      is_revoked: false,
      scopes: ["read", "write", "admin"],
    },
    {
      id: "key-002",
      name: "Analytics Service",
      key_prefix: "ieap_analytics_",
      user_id: "system",
      created_at: new Date(now.getTime() - RETENTION_15_DAYS_MS).toISOString(),
      last_used: new Date(now.getTime() - ONE_HOUR_MS).toISOString(),
      is_revoked: false,
      scopes: ["read"],
    },
  ], [apiKeys, now]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) {return "0 Bytes";}
    const k = BYTES_BASE;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))  } ${  sizes[i]}`;
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case "system":
        return <Server className="h-5 w-5 text-blue-500" />;
      case "user":
        return <Shield className="h-5 w-5 text-orange-500" />;
      default:
        return <Archive className="h-5 w-5 text-green-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
          <p className="text-muted-foreground">
            Configure system settings, feature flags, and backups
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="flags">Feature Flags</TabsTrigger>
          <TabsTrigger value="backups">Backups</TabsTrigger>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-4 mt-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Database Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Database
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Size</span>
                    <span className="font-medium">{(dbStats?.size as string) || "2.4 GB"}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Tables</span>
                    <span className="font-medium">{dbStats?.tables || MOCK_TABLES}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Connections</span>
                    <span className="font-medium">{dbStats?.connections || MOCK_CONNECTIONS}/100</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Slow Queries</span>
                    <span className="font-medium text-yellow-600">{dbStats?.slow_queries || MOCK_SLOW_QUERIES}</span>
                  </div>
                  <Button variant="outline" size="sm" className="w-full mt-2">
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Run Vacuum
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Cache Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <HardDrive className="h-5 w-5" />
                  Cache (Redis)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Size</span>
                    <span className="font-medium">{formatBytes(cacheStats?.size || CACHE_SIZE_BYTES)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Items</span>
                    <span className="font-medium">{cacheStats?.items?.toLocaleString() || "45,328"}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Hit Rate</span>
                    <span className="font-medium text-green-600">{cacheStats?.hit_rate || 94.5}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Miss Rate</span>
                    <span className="font-medium">{cacheStats?.miss_rate || 5.5}%</span>
                  </div>
                  <Button variant="outline" size="sm" className="w-full mt-2">
                    <Trash2 className="mr-2 h-4 w-4" />
                    Clear Cache
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* System Configuration */}
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  System Configuration
                </CardTitle>
                <CardDescription>
                  Current system settings and environment configuration
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-3">
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Environment</span>
                      <Badge variant="outline">{(systemConfig?.environment as string) || "production"}</Badge>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Debug Mode</span>
                      <Badge variant={(systemConfig?.debug as boolean) ? "destructive" : "secondary"}>
                        {(systemConfig?.debug as boolean) ? "Enabled" : "Disabled"}
                      </Badge>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Log Level</span>
                      <span className="font-mono text-sm">{(systemConfig?.log_level as string) || "INFO"}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Rate Limit</span>
                      <span className="font-mono text-sm">{(systemConfig?.rate_limit as string) || "1000/min"}</span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Max Batch Size</span>
                      <span className="font-mono text-sm">{(systemConfig?.max_batch_size as number) || 1000}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Timeout</span>
                      <span className="font-mono text-sm">{(systemConfig?.timeout as number) || MOCK_TIMEOUT_S}s</span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Workers</span>
                      <span className="font-mono text-sm">{(systemConfig?.workers as number) || 4}</span>
                    </div>
                    <div className="flex justify-between py-2 border-b">
                      <span className="text-muted-foreground">Max Connections</span>
                      <span className="font-mono text-sm">{(systemConfig?.max_connections as number) || 100}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Feature Flags Tab */}
        <TabsContent value="flags" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Flag className="h-5 w-5" />
                Feature Flags
              </CardTitle>
              <CardDescription>
                Enable or disable features across the platform
              </CardDescription>
            </CardHeader>
            <CardContent>
              {flagsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {Object.entries(mockFeatureFlags).map(([flag, enabled]) => (
                    <div
                      key={flag}
                      className="flex items-center justify-between p-4 rounded-lg border"
                    >
                      <div>
                        <Label className="text-base font-medium">
                          {flag
                            .split("_")
                            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                            .join(" ")}
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          {enabled ? "Feature is enabled" : "Feature is disabled"}
                        </p>
                      </div>
                      <Switch
                        checked={enabled as boolean}
                        onCheckedChange={(checked) =>
                          updateFlagMutation.mutate({ flagName: flag, enabled: checked })
                        }
                        disabled={updateFlagMutation.isPending}
                      />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Backups Tab */}
        <TabsContent value="backups" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Archive className="h-5 w-5" />
                    System Backups
                  </CardTitle>
                  <CardDescription>
                    Manage database and configuration backups
                  </CardDescription>
                </div>
                <Dialog open={isBackupDialogOpen} onOpenChange={setIsBackupDialogOpen}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      Create Backup
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create New Backup</DialogTitle>
                      <DialogDescription>
                        Create a full system backup including database and configuration
                      </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                      <p className="text-sm text-muted-foreground">
                        This will create a complete backup of the system. The process may take several minutes.
                      </p>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setIsBackupDialogOpen(false)}>
                        Cancel
                      </Button>
                      <Button
                        onClick={() => createBackupMutation.mutate()}
                        disabled={createBackupMutation.isPending}
                      >
                        {createBackupMutation.isPending ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Creating...
                          </>
                        ) : (
                          <>
                            <Archive className="mr-2 h-4 w-4" />
                            Create Backup
                          </>
                        )}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {backupsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: MOCK_ITEMS_COUNT }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Backup ID</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {mockBackups.map((backup) => (
                      <TableRow key={backup.backup_id}>
                        <TableCell className="font-mono text-sm">{backup.backup_id}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {backup.type}
                          </Badge>
                        </TableCell>
                        <TableCell>{formatBytes(backup.size_bytes)}</TableCell>
                        <TableCell>{formatRelativeTime(backup.created_at)}</TableCell>
                        <TableCell>
                          <Badge variant="default" className="bg-green-500">
                            {backup.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm">
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Upload className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="h-5 w-5" />
                    API Keys
                  </CardTitle>
                  <CardDescription>
                    Manage API keys for programmatic access
                  </CardDescription>
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Generate Key
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {keysLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: MOCK_ITEMS_COUNT }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Key Prefix</TableHead>
                      <TableHead>Scopes</TableHead>
                      <TableHead>Last Used</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {mockApiKeys.map((apiKey) => (
                      <TableRow key={apiKey.id}>
                        <TableCell className="font-medium">{apiKey.name}</TableCell>
                        <TableCell>
                          <code className="text-sm bg-muted px-2 py-1 rounded">
                            {apiKey.key_prefix}***
                          </code>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            {apiKey.scopes.map((scope) => (
                              <Badge key={scope} variant="outline" className="text-xs">
                                {scope}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>{formatRelativeTime(apiKey.last_used)}</TableCell>
                        <TableCell>
                          {apiKey.is_revoked ? (
                            <Badge variant="secondary">Revoked</Badge>
                          ) : (
                            <Badge variant="default" className="bg-green-500">Active</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          {!apiKey.is_revoked && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600"
                              onClick={() => revokeKeyMutation.mutate(apiKey.id)}
                              disabled={revokeKeyMutation.isPending}
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audit Logs Tab */}
        <TabsContent value="audit" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ScrollText className="h-5 w-5" />
                Audit Logs
              </CardTitle>
              <CardDescription>
                Track administrative actions and system events
              </CardDescription>
            </CardHeader>
            <CardContent>
              {logsLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {mockAuditLogs.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start gap-3 p-4 rounded-lg border"
                    >
                      <div className="mt-0.5">
                        {getEventIcon(log.event_type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{log.action}</span>
                          <Badge variant="outline" className="text-xs">
                            {log.event_type}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          Resource: {log.resource}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          By {log.user_id} • {formatRelativeTime(log.timestamp)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
