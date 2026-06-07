"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/components/AuthProvider";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

type SystemStats = {
  total_users: number;
  total_datasets: number;
  total_queries: number;
  status: string;
};

type AuditLog = {
  id: number;
  user_id: number;
  action: string;
  details: string;
  latency_ms: number | null;
  cost_usd: number | null;
  created_at: string;
};

export default function AdminPage() {
  const { token, user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    if (!isAuthenticated) return;
    if (user && !user.is_admin) {
      router.push("/dashboard");
      return;
    }

    if (token) {
      fetchStats();
      fetchLogs();
    }
  }, [isAuthenticated, user, token, router]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/admin/logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setLogs(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  if (!user?.is_admin) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
        <p className="text-muted-foreground">System overview and audit logs.</p>
      </div>

      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_users}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Datasets</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_datasets}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Queries</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_queries}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">System Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{stats.status}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Recent Audit Logs</CardTitle>
          <CardDescription>A complete log of system actions and queries.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="min-w-full text-sm">
              <thead className="border-b bg-muted/50">
                <tr>
                  <th className="h-10 px-4 text-left font-medium">Time</th>
                  <th className="h-10 px-4 text-left font-medium">User ID</th>
                  <th className="h-10 px-4 text-left font-medium">Action</th>
                  <th className="h-10 px-4 text-left font-medium">Details</th>
                  <th className="h-10 px-4 text-left font-medium">Latency</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-muted-foreground">No logs found.</td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="p-4 whitespace-nowrap">{new Date(log.created_at).toLocaleString()}</td>
                      <td className="p-4">{log.user_id}</td>
                      <td className="p-4 font-medium">{log.action}</td>
                      <td className="p-4 max-w-md truncate" title={log.details}>{log.details}</td>
                      <td className="p-4">{log.latency_ms ? `${log.latency_ms.toFixed(0)} ms` : '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
