"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Brain, Loader2, Mail, Lock, User } from "lucide-react";
import { toast } from "sonner";

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
    password2: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.password2) {
      toast.error("Passwords don't match");
      return;
    }

    if (formData.password.length < 12) {
      toast.error("Password must be at least 12 characters");
      return;
    }

    setLoading(true);

    try {
      // Register the user
      const user = await authApi.register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
      });
      
      // Automatically log in after registration
      const tokens = await authApi.login({
        email: formData.email,
        password: formData.password,
      });
      
      // Update auth store
      setAuth(user, tokens.access_token, tokens.refresh_token);
      
      toast.success(`Welcome to IEAP, ${user.username}!`);
      router.push("/dashboard");
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-pulse" style={{ animationDelay: "2s" }} />
      </div>

      <Card className="w-full max-w-md relative backdrop-blur-sm bg-background/95">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-gradient-to-br from-purple-500 to-blue-600 text-white p-4 rounded-2xl shadow-lg">
              <Brain className="h-10 w-10" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">Create your account</CardTitle>
          <CardDescription>
            Start automating with intelligent AI
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, email: e.target.value })}
                  required
                  disabled={loading}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="username"
                  type="text"
                  placeholder="johndoe"
                  value={formData.username}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, username: e.target.value })}
                  required
                  disabled={loading}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, password: e.target.value })}
                  required
                  disabled={loading}
                  className="pl-10"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                At least 12 characters
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password2">Confirm Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password2"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password2}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, password2: e.target.value })}
                  required
                  disabled={loading}
                  className="pl-10"
                />
              </div>
            </div>
            <Button 
              type="submit" 
              className="w-full bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700" 
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <div className="text-sm text-center text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:underline font-medium">
              Sign in
            </Link>
          </div>
          <p className="text-xs text-center text-muted-foreground">
            By creating an account, you agree to our{" "}
            <Link href="/terms" className="underline hover:text-primary">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="underline hover:text-primary">
              Privacy Policy
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
