"use client";

import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleAuth = async (action: "signin" | "signup") => {
    setError("");
    setLoading(true);

    try {
      if (action === "signup") {
        // Step 1: Create user
        const createRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        });

        if (!createRes.ok) {
          const errData = await createRes.json();
          throw new Error(errData.detail || "Failed to create account. Email might already be registered.");
        }
      }

      // Step 2: Login to get token
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
      });

      if (!res.ok) {
        throw new Error(action === "signup" ? "Account created, but failed to log in." : "Invalid credentials. Please check your email and password.");
      }

      const data = await res.json();
      
      // Step 3: Fetch user details
      const userRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/users/me/`, {
        headers: {
          "Authorization": `Bearer ${data.access_token}`
        }
      });
      const userData = await userRes.json();

      login(data.access_token, userData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-background animate-in fade-in duration-700">
      <Card className="w-full max-w-md shadow-2xl border-white/20 dark:border-slate-800/50 backdrop-blur-sm bg-card/95">
        <Tabs defaultValue="signin" className="w-full">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold tracking-tight">Welcome</CardTitle>
            <CardDescription>Sign in to your account or create a new one.</CardDescription>
            <TabsList className="grid w-full grid-cols-2 mt-4">
              <TabsTrigger value="signin">Sign In</TabsTrigger>
              <TabsTrigger value="signup">Sign Up</TabsTrigger>
            </TabsList>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input 
                id="email" 
                type="email" 
                placeholder="name@example.com" 
                required 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input 
                id="password" 
                type="password" 
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-red-500 font-medium bg-red-500/10 p-2 rounded-md">{error}</p>}
          </CardContent>
          <TabsContent value="signin" className="m-0">
            <CardFooter>
              <Button disabled={loading} onClick={() => handleAuth("signin")} className="w-full">
                {loading ? "Signing in..." : "Sign In"}
              </Button>
            </CardFooter>
          </TabsContent>
          <TabsContent value="signup" className="m-0">
            <CardFooter>
              <Button disabled={loading} onClick={() => handleAuth("signup")} className="w-full">
                {loading ? "Creating account..." : "Create Account"}
              </Button>
            </CardFooter>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
