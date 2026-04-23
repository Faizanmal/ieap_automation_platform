"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores";
import { authApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function AuthCallbackPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get tokens from URL hash
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        
        const accessToken = params.get("access_token");
        const refreshToken = params.get("refresh_token");
        
        if (!accessToken || !refreshToken) {
          throw new Error("Missing tokens in callback");
        }

        // Set tokens temporarily to make authenticated request
        localStorage.setItem('ieap-auth-storage', JSON.stringify({
          state: { accessToken }
        }));
        
        // Get user info
        const user = await authApi.me();
        
        // Update auth store with user and tokens
        setAuth(user, accessToken, refreshToken);
        
        // Clear the hash
        window.history.replaceState(null, "", window.location.pathname);
        
        toast.success("Successfully signed in with Google!");
        router.push("/dashboard");
      } catch (error) {
        console.error("Auth callback error:", error);
        toast.error("Authentication failed. Please try again.");
        router.push("/login");
      }
    };

    handleCallback();
  }, [router, setAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">Signing you in...</CardTitle>
          <CardDescription>
            Please wait while we complete your authentication
          </CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </CardContent>
      </Card>
    </div>
  );
}