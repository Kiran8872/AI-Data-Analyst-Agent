"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/components/AuthProvider";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadCloud, FileText, Database, HardDrive, Activity, TrendingUp, Sparkles, Clock, ChevronRight } from "lucide-react";

type Dataset = {
  id: number;
  filename: string;
  size_bytes: number;
  created_at: string;
};

export default function DashboardPage() {
  const { token, logout } = useAuth();
  const router = useRouter();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const fetchDatasets = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/datasets/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setDatasets(await res.json());
      } else if (res.status === 401) {
        logout();
      }
    } catch (e) {
      console.error(e);
    }
  }, [token, logout]);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !token) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/datasets/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (res.ok) {
        setFile(null);
        fetchDatasets();
      } else if (res.status === 401) {
        logout();
      } else {
        console.error("Upload failed.");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setUploading(false);
    }
  };

  // Metrics calculations
  const totalSize = datasets.reduce((acc, curr) => acc + curr.size_bytes, 0) / 1024;
  const avgSize = datasets.length > 0 ? totalSize / datasets.length : 0;

  return (
    <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto pb-12">
      
      {/* Dashboard Header */}
      <div className="flex justify-between items-end border-b pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-indigo-100 text-indigo-800 text-xs font-semibold px-2.5 py-0.5 rounded dark:bg-indigo-900/30 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> AI Core Active
            </span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-slate-400 bg-clip-text text-transparent">
            Executive Command Center
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">Real-time telemetry and data ingestion overview.</p>
        </div>
      </div>

      {/* 4-Column Metric Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="shadow-sm border-l-4 border-l-indigo-500 hover:shadow-md transition-all hover:-translate-y-1 group">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Datasets</CardTitle>
            <div className="bg-indigo-500/10 p-2 rounded-full group-hover:bg-indigo-500/20 transition-colors">
              <Database className="h-4 w-4 text-indigo-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{datasets.length}</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-emerald-500" /> +{datasets.length} All Time
            </p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-l-4 border-l-purple-500 hover:shadow-md transition-all hover:-translate-y-1 group">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Storage Used</CardTitle>
            <div className="bg-purple-500/10 p-2 rounded-full group-hover:bg-purple-500/20 transition-colors">
              <HardDrive className="h-4 w-4 text-purple-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalSize.toFixed(1)} KB</div>
            <p className="text-xs text-muted-foreground mt-1">Aggregated disk footprint</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-l-4 border-l-blue-500 hover:shadow-md transition-all hover:-translate-y-1 group">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg. Dataset Size</CardTitle>
            <div className="bg-blue-500/10 p-2 rounded-full group-hover:bg-blue-500/20 transition-colors">
              <FileText className="h-4 w-4 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{avgSize.toFixed(1)} KB</div>
            <p className="text-xs text-muted-foreground mt-1">Per file average</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-l-4 border-l-emerald-500 hover:shadow-md transition-all hover:-translate-y-1 group bg-gradient-to-br from-emerald-500/5 to-transparent">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">AI Engine Status</CardTitle>
            <div className="bg-emerald-500/10 p-2 rounded-full">
              <Activity className="h-4 w-4 text-emerald-500 animate-pulse" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">Online</div>
            <p className="text-xs text-emerald-600/70 dark:text-emerald-400/70 mt-1 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Latency: &lt;50ms
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Action Area: Upload & Recent */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Sleek Upload Zone */}
        <Card className="shadow-sm border-2 border-transparent hover:border-indigo-500/20 transition-all duration-300">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><UploadCloud className="h-5 w-5 text-indigo-500" /> AI Data Ingestion</CardTitle>
            <CardDescription>Drop a CSV or Excel file here to begin the automated profiling and NLP analysis process.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpload} className="flex flex-col gap-4 h-full justify-between">
              <div className="group relative border-2 border-dashed border-indigo-200 dark:border-indigo-800/50 rounded-xl p-8 flex flex-col items-center justify-center bg-indigo-50/50 dark:bg-indigo-950/20 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:border-indigo-400 dark:hover:border-indigo-600 transition-all cursor-pointer h-48">
                <UploadCloud className="h-10 w-10 text-indigo-400 group-hover:text-indigo-600 group-hover:scale-110 transition-transform mb-4" />
                <p className="text-sm font-medium text-center">Drag & Drop your file here</p>
                <p className="text-xs text-muted-foreground text-center mt-1">Supports .csv, .xlsx</p>
                
                {/* Hidden File Input covering the area */}
                <input 
                  type="file" 
                  accept=".csv, .xlsx, .xls"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                
                {file && (
                  <div className="absolute inset-0 bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center rounded-xl border-2 border-indigo-500">
                    <div className="text-center">
                      <FileText className="h-8 w-8 text-indigo-600 mx-auto mb-2" />
                      <p className="font-semibold text-indigo-800 dark:text-indigo-200">{file.name}</p>
                      <p className="text-xs text-indigo-600 dark:text-indigo-300">Ready to ingest</p>
                    </div>
                  </div>
                )}
              </div>
              
              <Button 
                type="submit" 
                disabled={!file || uploading} 
                className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg transition-all hover:scale-[1.02] py-6 text-lg"
              >
                {uploading ? (
                  <><Activity className="mr-2 h-5 w-5 animate-spin" /> Ingesting & Analyzing...</>
                ) : (
                  <><Sparkles className="mr-2 h-5 w-5" /> Launch AI Analysis</>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Recent Datasets Activity Feed */}
        <Card className="shadow-sm flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Clock className="h-5 w-5 text-slate-500" /> Recent Activity</CardTitle>
            <CardDescription>Your latest uploaded files. Click to enter the Dedicated Analytics Suite.</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            {datasets.length === 0 ? (
              <div className="h-full flex items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg p-6">
                System is idle. Awaiting data ingestion.
              </div>
            ) : (
              <ul className="space-y-3">
                {datasets.slice(-5).reverse().map((ds) => (
                  <li 
                    key={ds.id} 
                    onClick={() => router.push(`/dashboard/datasets/${ds.id}`)}
                    className="flex items-center justify-between p-4 border rounded-xl hover:shadow-md hover:border-indigo-300 dark:hover:border-indigo-700 transition-all bg-card cursor-pointer group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="bg-indigo-500/10 p-3 rounded-full group-hover:bg-indigo-500/20 group-hover:scale-110 transition-all">
                        <FileText className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">{ds.filename}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {(ds.size_bytes / 1024).toFixed(2)} KB • {new Date(ds.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                  </li>
                ))}
              </ul>
            )}
            
            {datasets.length > 5 && (
              <Button variant="ghost" className="w-full mt-4 text-xs text-muted-foreground hover:text-foreground" onClick={() => router.push('/dashboard/datasets')}>
                View all {datasets.length} datasets <ChevronRight className="h-3 w-3 ml-1" />
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
