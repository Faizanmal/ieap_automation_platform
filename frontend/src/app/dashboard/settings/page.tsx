"use client";

import { useState } from "react";
import { useAuthStore } from "@/lib/stores/auth-store";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
  User,
  Bell,
  Shield,
  Palette,
  Globe,
  Mail,
  Key,
  Smartphone,
  Moon,
  Sun,
  Monitor,
  Loader2,
  Save,
  Camera,
  Plus,
  Copy,
  Trash2,
} from "lucide-react";

export default function SettingsPage() {
  // Constants for magic numbers
  const SAVE_DELAY_MS = 1000; // Delay for save simulation
  const SESSION_TIMEOUT_2_HOURS = 120;
  const SESSION_TIMEOUT_8_HOURS = 480;
  const TEST_API_KEY_SUFFIX = 1234;
  const ICON_SIZE_CLASS = "h-4 w-4";
  const [activeTab, setActiveTab] = useState("profile");
  const [isSaving, setIsSaving] = useState(false);

  // Profile form state
  const [profile, setProfile] = useState({
    username: user?.username || "johndoe",
    email: user?.email || "john.doe@example.com",
    fullName: user?.full_name || "John Doe",
    bio: "Machine learning engineer working on enterprise automation solutions.",
    company: "IEAP Technologies",
    location: "San Francisco, CA",
    timezone: "America/Los_Angeles",
  });

  // Notification settings
  const [notifications, setNotifications] = useState({
    emailPredictions: true,
    emailPipelines: true,
    emailDecisions: true,
    emailWeeklyReport: true,
    pushEnabled: true,
    pushPredictions: false,
    pushPipelines: true,
    pushDecisions: true,
  });

  // Appearance settings
  const [appearance, setAppearance] = useState({
    theme: "system" as "light" | "dark" | "system",
    compactMode: false,
    sidebarCollapsed: false,
    language: "en",
  });

  // Security settings
  const [security, setSecurity] = useState({
    twoFactorEnabled: false,
    sessionTimeout: 30,
    loginNotifications: true,
  });

  const handleSaveProfile = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, SAVE_DELAY_MS));
    setIsSaving(false);
    toast.success("Profile updated successfully");
  };

  const handleSaveNotifications = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, SAVE_DELAY_MS));
    setIsSaving(false);
    toast.success("Notification preferences saved");
  };

  const handleSaveAppearance = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, SAVE_DELAY_MS));
    setIsSaving(false);
    toast.success("Appearance settings saved");
  };

  const handleSaveSecurity = async () => {
    setIsSaving(true);
    await new Promise((resolve) => setTimeout(resolve, SAVE_DELAY_MS));
    setIsSaving(false);
    toast.success("Security settings saved");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and preferences
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className={ICON_SIZE_CLASS} />
            Profile
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className={ICON_SIZE_CLASS} />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="appearance" className="flex items-center gap-2">
            <Palette className={ICON_SIZE_CLASS} />
            Appearance
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className={ICON_SIZE_CLASS} />
            Security
          </TabsTrigger>
          <TabsTrigger value="api-keys" className="flex items-center gap-2">
            <Key className={ICON_SIZE_CLASS} />
            API Keys
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Update your personal information and public profile
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Avatar */}
              <div className="flex items-center gap-6">
                <Avatar className="h-20 w-20">
                  <AvatarImage src={`https://avatar.vercel.sh/${profile.username}`} />
                  <AvatarFallback className="text-xl">
                    {profile.fullName.split(" ").map((n: string) => n[0]).join("")}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" size="sm">
                    <Camera className={`mr-2 ${ICON_SIZE_CLASS}`} />
                    Change Avatar
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    JPG, PNG or GIF. Max 2MB.
                  </p>
                </div>
              </div>

              <Separator />

              {/* Form Fields */}
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={profile.username}
                    onChange={(e) => setProfile({ ...profile, username: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full Name</Label>
                  <Input
                    id="fullName"
                    value={profile.fullName}
                    onChange={(e) => setProfile({ ...profile, fullName: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    value={profile.company}
                    onChange={(e) => setProfile({ ...profile, company: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    value={profile.location}
                    onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select
                    value={profile.timezone}
                    onValueChange={(value) => setProfile({ ...profile, timezone: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="America/New_York">Eastern Time</SelectItem>
                      <SelectItem value="America/Chicago">Central Time</SelectItem>
                      <SelectItem value="America/Denver">Mountain Time</SelectItem>
                      <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                      <SelectItem value="Europe/London">London</SelectItem>
                      <SelectItem value="Europe/Paris">Paris</SelectItem>
                      <SelectItem value="Asia/Tokyo">Tokyo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="bio">Bio</Label>
                  <Textarea
                    id="bio"
                    value={profile.bio}
                    onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                    rows={3}
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button onClick={handleSaveProfile} disabled={isSaving}>
                  {isSaving ? (
                    <Loader2 className={`mr-2 ${ICON_SIZE_CLASS} animate-spin`} />
                  ) : (
                    <Save className={`mr-2 ${ICON_SIZE_CLASS}`} />
                  )}
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Email Notifications
              </CardTitle>
              <CardDescription>
                Choose what updates you receive via email
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Prediction Completions</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified when predictions complete
                  </p>
                </div>
                <Switch
                  checked={notifications.emailPredictions}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...notifications, emailPredictions: checked })
                  }
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <Label>Pipeline Updates</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive updates on pipeline runs
                  </p>
                </div>
                <Switch
                  checked={notifications.emailPipelines}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...notifications, emailPipelines: checked })
                  }
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <Label>Decision Requests</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified when decisions need approval
                  </p>
                </div>
                <Switch
                  checked={notifications.emailDecisions}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...notifications, emailDecisions: checked })
                  }
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <Label>Weekly Report</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive weekly analytics summary
                  </p>
                </div>
                <Switch
                  checked={notifications.emailWeeklyReport}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...notifications, emailWeeklyReport: checked })
                  }
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-5 w-5" />
                Push Notifications
              </CardTitle>
              <CardDescription>
                Configure push notifications for real-time updates
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable Push Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Allow browser push notifications
                  </p>
                </div>
                <Switch
                  checked={notifications.pushEnabled}
                  onCheckedChange={(checked) =>
                    setNotifications({ ...notifications, pushEnabled: checked })
                  }
                />
              </div>
              {notifications.pushEnabled && (
                <>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <Label>Pipeline Alerts</Label>
                    <Switch
                      checked={notifications.pushPipelines}
                      onCheckedChange={(checked) =>
                        setNotifications({ ...notifications, pushPipelines: checked })
                      }
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Decision Alerts</Label>
                    <Switch
                      checked={notifications.pushDecisions}
                      onCheckedChange={(checked) =>
                        setNotifications({ ...notifications, pushDecisions: checked })
                      }
                    />
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={handleSaveNotifications} disabled={isSaving}>
              {isSaving ? (
                <Loader2 className={`mr-2 ${ICON_SIZE_CLASS} animate-spin`} />
              ) : (
                <Save className={`mr-2 ${ICON_SIZE_CLASS}`} />
              )}
              Save Preferences
            </Button>
          </div>
        </TabsContent>

        {/* Appearance Tab */}
        <TabsContent value="appearance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Theme</CardTitle>
              <CardDescription>
                Select your preferred color theme
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div
                  className={`p-4 rounded-lg border-2 cursor-pointer ${appearance.theme === "light"
                    ? "border-primary"
                    : "border-muted hover:border-muted-foreground"
                    }`}
                  onClick={() => setAppearance({ ...appearance, theme: "light" })}
                >
                  <div className="flex items-center gap-3">
                    <Sun className="h-5 w-5" />
                    <div>
                      <p className="font-medium">Light</p>
                      <p className="text-xs text-muted-foreground">
                        Light background with dark text
                      </p>
                    </div>
                  </div>
                </div>
                <div
                  className={`p-4 rounded-lg border-2 cursor-pointer ${appearance.theme === "dark"
                    ? "border-primary"
                    : "border-muted hover:border-muted-foreground"
                    }`}
                  onClick={() => setAppearance({ ...appearance, theme: "dark" })}
                >
                  <div className="flex items-center gap-3">
                    <Moon className="h-5 w-5" />
                    <div>
                      <p className="font-medium">Dark</p>
                      <p className="text-xs text-muted-foreground">
                        Dark background with light text
                      </p>
                    </div>
                  </div>
                </div>
                <div
                  className={`p-4 rounded-lg border-2 cursor-pointer ${appearance.theme === "system"
                    ? "border-primary"
                    : "border-muted hover:border-muted-foreground"
                    }`}
                  onClick={() => setAppearance({ ...appearance, theme: "system" })}
                >
                  <div className="flex items-center gap-3">
                    <Monitor className="h-5 w-5" />
                    <div>
                      <p className="font-medium">System</p>
                      <p className="text-xs text-muted-foreground">
                        Follow system preference
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Display Options</CardTitle>
              <CardDescription>
                Customize your viewing experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Compact Mode</Label>
                  <p className="text-sm text-muted-foreground">
                    Reduce spacing for denser layouts
                  </p>
                </div>
                <Switch
                  checked={appearance.compactMode}
                  onCheckedChange={(checked) =>
                    setAppearance({ ...appearance, compactMode: checked })
                  }
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <Label>Collapse Sidebar by Default</Label>
                  <p className="text-sm text-muted-foreground">
                    Start with a minimized sidebar
                  </p>
                </div>
                <Switch
                  checked={appearance.sidebarCollapsed}
                  onCheckedChange={(checked) =>
                    setAppearance({ ...appearance, sidebarCollapsed: checked })
                  }
                />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <Label>Language</Label>
                  <p className="text-sm text-muted-foreground">
                    Select your preferred language
                  </p>
                </div>
                <Select
                  value={appearance.language}
                  onValueChange={(value) => setAppearance({ ...appearance, language: value })}
                >
                  <SelectTrigger className="w-45">
                    <Globe className={`mr-2 ${ICON_SIZE_CLASS}`} />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="es">Spanish</SelectItem>
                    <SelectItem value="fr">French</SelectItem>
                    <SelectItem value="de">German</SelectItem>
                    <SelectItem value="ja">Japanese</SelectItem>
                    <SelectItem value="zh">Chinese</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={handleSaveAppearance} disabled={isSaving}>
              {isSaving ? (
                <Loader2 className={`mr-2 ${ICON_SIZE_CLASS} animate-spin`} />
              ) : (
                <Save className={`mr-2 ${ICON_SIZE_CLASS}`} />
              )}
              Save Appearance
            </Button>
          </div>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Password</CardTitle>
              <CardDescription>
                Update your password to keep your account secure
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="currentPassword">Current Password</Label>
                  <Input id="currentPassword" type="password" />
                </div>
                <div />
                <div className="space-y-2">
                  <Label htmlFor="newPassword">New Password</Label>
                  <Input id="newPassword" type="password" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <Input id="confirmPassword" type="password" />
                </div>
              </div>
              <Button variant="outline">
                <Key className={`mr-2 ${ICON_SIZE_CLASS}`} />
                Update Password
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Two-Factor Authentication</CardTitle>
              <CardDescription>
                Add an extra layer of security to your account
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable 2FA</Label>
                  <p className="text-sm text-muted-foreground">
                    Use an authenticator app for extra security
                  </p>
                </div>
                <Switch
                  checked={security.twoFactorEnabled}
                  onCheckedChange={(checked) =>
                    setSecurity({ ...security, twoFactorEnabled: checked })
                  }
                />
              </div>
              {!security.twoFactorEnabled && (
                <Button variant="outline">
                  <Smartphone className={`mr-2 ${ICON_SIZE_CLASS}`} />
                  Set Up 2FA
                </Button>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Session Settings</CardTitle>
              <CardDescription>
                Configure session timeout and login notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Session Timeout</Label>
                  <p className="text-sm text-muted-foreground">
                    Auto logout after inactivity
                  </p>
                </div>
                <Select
                  value={security.sessionTimeout.toString()}
                  onValueChange={(value) =>
                    setSecurity({ ...security, sessionTimeout: parseInt(value) })
                  }
                >
                  <SelectTrigger className="w-37.5">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="15">15 minutes</SelectItem>
                    <SelectItem value="30">30 minutes</SelectItem>
                    <SelectItem value="60">1 hour</SelectItem>
                    <SelectItem value={SESSION_TIMEOUT_2_HOURS.toString()}>2 hours</SelectItem>
                    <SelectItem value={SESSION_TIMEOUT_8_HOURS.toString()}>8 hours</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <Label>Login Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified of new logins to your account
                  </p>
                </div>
                <Switch
                  checked={security.loginNotifications}
                  onCheckedChange={(checked) =>
                    setSecurity({ ...security, loginNotifications: checked })
                  }
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={handleSaveSecurity} disabled={isSaving}>
              {isSaving ? (
                <Loader2 className={`mr-2 ${ICON_SIZE_CLASS} animate-spin`} />
              ) : (
                <Save className={`mr-2 ${ICON_SIZE_CLASS}`} />
              )}
              Save Security Settings
            </Button>
          </div>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                API Keys
              </CardTitle>
              <CardDescription>
                Manage API keys for programmatic access to IEAP
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                API keys allow you to authenticate requests to the IEAP API. Keep your keys secure and never share them.
              </p>
              <div className="rounded-lg bg-blue-50 p-4 border border-blue-200">
                <p className="text-sm text-blue-900">
                  📡 <strong>API Documentation</strong>: Visit our <a href="#" className="underline font-semibold">API docs</a> to learn how to use your API keys.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Create New API Key</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="keyName">Key Name</Label>
                <Input
                  id="keyName"
                  placeholder="My API Key"
                  defaultValue=""
                />
              </div>
              <div className="space-y-2">
                <Label>Permissions</Label>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" id="perm1" defaultChecked />
                    <Label htmlFor="perm1" className="font-normal cursor-pointer">
                      Read access to predictions
                    </Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" id="perm2" />
                    <Label htmlFor="perm2" className="font-normal cursor-pointer">
                      Write access to predictions
                    </Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" id="perm3" />
                    <Label htmlFor="perm3" className="font-normal cursor-pointer">
                      Admin access
                    </Label>
                  </div>
                </div>
              </div>
              <Button>
                <Plus className={`mr-2 ${ICON_SIZE_CLASS}`} />
                Generate API Key
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Your API Keys</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[1, 2].map((idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-sm">Production Key {idx}</p>
                      <p className="text-xs text-muted-foreground">
                        sk_live_****...{TEST_API_KEY_SUFFIX + idx} • Created 5 days ago
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="outline">Active</Badge>
                      <Button variant="ghost" size="sm">
                        <Copy className={ICON_SIZE_CLASS} />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Trash2 className={`${ICON_SIZE_CLASS} text-red-500`} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
