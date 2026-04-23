"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi, AdminUser } from "@/lib/api/admin";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "sonner";
import {
  Users,
  Search,
  RefreshCw,
  MoreHorizontal,
  Eye,
  UserCog,
  UserX,
  Shield,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  Filter,
  Download,
} from "lucide-react";
import { formatDate, formatDateTime, formatRelativeTime } from "@/lib/utils";

// Constants for magic numbers
const HOURS_IN_DAY = 24;
const MINUTES_IN_HOUR = 60;
const SECONDS_IN_MINUTE = 60;
const MS_IN_SECOND = 1000;
const ONE_HOUR_MS = MS_IN_SECOND * SECONDS_IN_MINUTE * MINUTES_IN_HOUR;
const ONE_DAY_MS = ONE_HOUR_MS * HOURS_IN_DAY;
const THIRTY_DAYS_MS = 30 * ONE_DAY_MS;
const TWENTY_DAYS_MS = 20 * ONE_DAY_MS;
const FIFTEEN_DAYS_MS = 15 * ONE_DAY_MS;
const FORTY_FIVE_DAYS_MS = 45 * ONE_DAY_MS;
const TEN_DAYS_MS = 10 * ONE_DAY_MS;
const TWO_HOURS_MS = 2 * ONE_HOUR_MS;

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [page, ] = useState(1);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [isDetailsDialogOpen, setIsDetailsDialogOpen] = useState(false);

  // Fetch users
  const { data: usersData, isLoading, refetch } = useQuery({
    queryKey: ["admin", "users", page, roleFilter, searchQuery],
    queryFn: () =>
      adminApi.listUsers({
        page,
        per_page: 20,
        search: searchQuery || undefined,
        role: roleFilter !== "all" ? roleFilter : undefined,
      }),
  });

  // Deactivate user mutation
  const deactivateMutation = useMutation({
    mutationFn: (userId: string) => adminApi.deactivateUser(userId),
    onSuccess: () => {
      toast.success("User deactivated");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
    onError: () => {
      toast.error("Failed to deactivate user");
    },
  });

  // Use state for mock data to ensure purity
  const [now] = useState(new Date());

  const defaultUsers = useMemo(() => [
    {
      id: "1",
      email: "admin@ieap.io",
      username: "admin",
      role: "admin",
      is_active: true,
      created_at: new Date(now.getTime() - THIRTY_DAYS_MS).toISOString(),
      last_login: now.toISOString(),
    },
    {
      id: "2",
      email: "john.doe@example.com",
      username: "johndoe",
      role: "user",
      is_active: true,
      created_at: new Date(now.getTime() - TWENTY_DAYS_MS).toISOString(),
      last_login: new Date(now.getTime() - ONE_HOUR_MS).toISOString(),
    },
    {
      id: "3",
      email: "jane.smith@example.com",
      username: "janesmith",
      role: "analyst",
      is_active: true,
      created_at: new Date(now.getTime() - FIFTEEN_DAYS_MS).toISOString(),
      last_login: new Date(now.getTime() - ONE_DAY_MS).toISOString(),
    },
    {
      id: "4",
      email: "bob.wilson@example.com",
      username: "bobwilson",
      role: "user",
      is_active: false,
      created_at: new Date(now.getTime() - FORTY_FIVE_DAYS_MS).toISOString(),
      last_login: new Date(now.getTime() - THIRTY_DAYS_MS).toISOString(),
    },
    {
      id: "5",
      email: "alice.chen@example.com",
      username: "alicechen",
      role: "manager",
      is_active: true,
      created_at: new Date(now.getTime() - TEN_DAYS_MS).toISOString(),
      last_login: new Date(now.getTime() - TWO_HOURS_MS).toISOString(),
    },
  ], [now]);

  // Mock data if API not available
  const users = usersData?.users || defaultUsers;

  const getRoleIcon = (role: string) => {
    switch (role) {
      case "admin":
        return <ShieldCheck className="h-4 w-4 text-red-500" />;
      case "manager":
        return <ShieldAlert className="h-4 w-4 text-orange-500" />;
      case "analyst":
        return <Shield className="h-4 w-4 text-blue-500" />;
      default:
        return <Users className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case "admin":
        return "destructive";
      case "manager":
        return "default";
      case "analyst":
        return "secondary";
      default:
        return "outline";
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      );
    } else if (filteredUsers.length === 0) {
      return (
        <div className="text-center py-12">
          <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium">No users found</h3>
          <p className="text-muted-foreground mt-2">
            Try adjusting your search or filters
          </p>
        </div>
      );
    } else {
      return (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Last Login</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredUsers.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={`https://avatar.vercel.sh/${user.username}`} />
                      <AvatarFallback>
                        {user.username.slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{user.username}</p>
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {getRoleIcon(user.role)}
                    <Badge variant={getRoleBadgeVariant(user.role) as "default" | "secondary" | "destructive" | "outline"}>
                      {user.role}
                    </Badge>
                  </div>
                </TableCell>
                <TableCell>
                  {user.is_active ? (
                    <Badge variant="default" className="bg-green-500">
                      Active
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Inactive</Badge>
                  )}
                </TableCell>
                <TableCell>
                  <span className="text-sm">{formatDate(user.created_at)}</span>
                </TableCell>
                <TableCell>
                  <span className="text-sm">{formatRelativeTime(user.last_login)}</span>
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
                          setSelectedUser(user);
                          setIsDetailsDialogOpen(true);
                        }}
                      >
                        <Eye className="mr-2 h-4 w-4" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <UserCog className="mr-2 h-4 w-4" />
                        Edit User
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      {user.is_active && (
                        <DropdownMenuItem
                          onClick={() => deactivateMutation.mutate(user.id)}
                          className="text-red-600"
                          disabled={deactivateMutation.isPending}
                        >
                          <UserX className="mr-2 h-4 w-4" />
                          Deactivate
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">User Management</h1>
          <p className="text-muted-foreground">
            Manage user accounts and permissions
          </p>
        </div>
        <div className="flex gap-2">
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

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.active}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Administrators</CardTitle>
            <ShieldCheck className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.admins}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">New This Month</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.newThisMonth}</div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={roleFilter} onValueChange={setRoleFilter}>
          <SelectTrigger className="w-37.5">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
            <SelectItem value="manager">Manager</SelectItem>
            <SelectItem value="analyst">Analyst</SelectItem>
            <SelectItem value="user">User</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Users</CardTitle>
          <CardDescription>
            A list of all users with their roles and status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {renderContent()}
        </CardContent>
      </Card>

      {/* User Details Dialog */}
      <Dialog open={isDetailsDialogOpen} onOpenChange={setIsDetailsDialogOpen}>
        <DialogContent className="sm:max-w-125">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserCog className="h-5 w-5" />
              User Details
            </DialogTitle>
            <DialogDescription>
              Detailed information about the user
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Avatar className="h-16 w-16">
                  <AvatarImage src={`https://avatar.vercel.sh/${selectedUser.username}`} />
                  <AvatarFallback className="text-lg">
                    {selectedUser.username.slice(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="text-lg font-semibold">{selectedUser.username}</h3>
                  <p className="text-muted-foreground">{selectedUser.email}</p>
                </div>
              </div>

              <div className="grid gap-3 py-4">
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-muted-foreground">User ID</span>
                  <span className="font-mono text-sm">{selectedUser.id}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-muted-foreground">Role</span>
                  <div className="flex items-center gap-2">
                    {getRoleIcon(selectedUser.role)}
                    <Badge variant={getRoleBadgeVariant(selectedUser.role) as "default" | "secondary" | "destructive" | "outline"}>
                      {selectedUser.role}
                    </Badge>
                  </div>
                </div>
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-muted-foreground">Status</span>
                  {selectedUser.is_active ? (
                    <Badge variant="default" className="bg-green-500">Active</Badge>
                  ) : (
                    <Badge variant="secondary">Inactive</Badge>
                  )}
                </div>
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-muted-foreground">Created</span>
                  <span>{formatDateTime(selectedUser.created_at)}</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-muted-foreground">Last Login</span>
                  <span>{formatDateTime(selectedUser.last_login)}</span>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDetailsDialogOpen(false)}>
              Close
            </Button>
            <Button>
              <UserCog className="mr-2 h-4 w-4" />
              Edit User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
