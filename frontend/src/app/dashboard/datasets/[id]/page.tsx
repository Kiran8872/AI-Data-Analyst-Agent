/* eslint-disable */
"use client";

import { useAuth } from "@/components/AuthProvider";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Sparkles, Download, LayoutDashboard, Eye } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export default function DatasetDetailsPage() {
  const { token } = useAuth();
  const params = useParams();
  const router = useRouter();
  const datasetId = params.id;
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [dataset, setDataset] = useState<any>(null);
  const [profileData, setProfileData] = useState<any>(null);
  const [sentimentData, setSentimentData] = useState<any>(null);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [sentimentLoading, setSentimentLoading] = useState(false);
  const [previewData, setPreviewData] = useState<{columns: string[], data: any[]}>({columns: [], data: []});
  const [previewLoading, setPreviewLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const dsRes = await fetch(`${apiBase}/datasets/${datasetId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (dsRes.ok) setDataset(await dsRes.json());

      const profRes = await fetch(`${apiBase}/datasets/${datasetId}/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (profRes.ok) setProfileData(await profRes.json());
      
      const sumRes = await fetch(`${apiBase}/datasets/${datasetId}/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (sumRes.ok) setAiSummary((await sumRes.json()).summary);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [token, datasetId, apiBase]);

  const fetchSentiment = useCallback(async () => {
    setSentimentLoading(true);
    try {
      const res = await fetch(`${apiBase}/datasets/${datasetId}/sentiment`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setSentimentData(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setSentimentLoading(false);
    }
  }, [token, datasetId, apiBase]);

  useEffect(() => {
    if (token && datasetId) {
      fetchData();
      fetchSentiment();
    }
  }, [token, datasetId, fetchData, fetchSentiment]);



  const openPreview = async () => {
    if (!token) return;
    setIsDialogOpen(true);
    setPreviewLoading(true);
    try {
      const res = await fetch(`${apiBase}/datasets/${datasetId}/data`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setPreviewData(await res.json());
      } else {
        setPreviewData({columns: [], data: []});
      }
    } catch (e) {
      console.error(e);
      setPreviewData({columns: [], data: []});
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleExport = () => {
    if (!profileData || !dataset) return;
    let report = `# Executive Analytics Report: ${dataset.filename}\n\n`;
    report += `## Overview\n- Total Rows: ${profileData.total_rows}\n- Total Columns: ${profileData.total_columns}\n\n`;
    
    if (sentimentData && sentimentData.status === 'success') {
      report += `## Feedback Sentiment Analysis\n`;
      report += `Analyzed Column: ${sentimentData.column}\n`;
      report += `- Positive: ${sentimentData.sentiment.positive}\n`;
      report += `- Neutral: ${sentimentData.sentiment.neutral}\n`;
      report += `- Negative: ${sentimentData.sentiment.negative}\n\n`;
    }

    report += `## Data Profile Summary\n`;
    profileData.columns.forEach((col: any) => {
      report += `- **${col.name}** (${col.type}): ${col.null_count} missing, ${col.unique_count} unique.\n`;
    });

    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${dataset.filename}_report.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return <div className="flex h-full items-center justify-center animate-pulse text-muted-foreground">Loading Analytics Suite...</div>;
  }

  if (!dataset) {
    return <div className="text-center text-destructive mt-10">Dataset not found.</div>;
  }

  // Calculate sentiment percentages for UI
  if (sentimentData?.status === 'success') {
    // ... logic hidden from UI in previous implementation ...
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" onClick={() => router.push('/dashboard/datasets')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <LayoutDashboard className="h-8 w-8 text-primary" />
              Dataset Analytics Suite
            </h1>
            <p className="text-muted-foreground">Deep profiling and cleaning for: <span className="font-semibold text-foreground">{dataset.filename}</span></p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={openPreview} className="shadow-sm transition-all hover:scale-105">
            <Eye className="mr-2 h-4 w-4" /> View Raw Data
          </Button>
          <Button onClick={handleExport} className="bg-primary hover:bg-primary/90 text-white shadow-md transition-all hover:scale-105">
            <Download className="mr-2 h-4 w-4" /> Export Executive Report
          </Button>
        </div>
      </div>

      {aiSummary && (
        <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-xl p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-5 w-5 text-indigo-500" />
            <h3 className="font-semibold text-indigo-700 dark:text-indigo-400">AI Executive Summary</h3>
          </div>
          <p className="text-muted-foreground leading-relaxed">{aiSummary}</p>
        </div>
      )}

      {/* Data Profile Table */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle>Complete Data Profile</CardTitle>
          <CardDescription>Column-level statistics</CardDescription>
        </CardHeader>
        <CardContent>
          {profileData ? (
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/50">
                    <TableHead>Column Name</TableHead>
                    <TableHead>Data Type</TableHead>
                    <TableHead>Missing</TableHead>
                    <TableHead>Unique</TableHead>
                    <TableHead>Min</TableHead>
                    <TableHead>Max</TableHead>
                    <TableHead>Mean</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {profileData.columns.map((col: any, i: number) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{col.name}</TableCell>
                      <TableCell><span className="text-xs bg-muted border px-2 py-1 rounded">{col.type}</span></TableCell>
                      <TableCell className={col.null_count > 0 ? "text-destructive font-bold" : ""}>{col.null_count}</TableCell>
                      <TableCell>{col.unique_count}</TableCell>
                      <TableCell className="text-muted-foreground">{col.min !== null ? (typeof col.min === 'number' && !Number.isInteger(col.min) ? col.min.toFixed(2) : col.min) : '-'}</TableCell>
                      <TableCell className="text-muted-foreground">{col.max !== null ? (typeof col.max === 'number' && !Number.isInteger(col.max) ? col.max.toFixed(2) : col.max) : '-'}</TableCell>
                      <TableCell className="text-muted-foreground">{col.mean !== null ? (typeof col.mean === 'number' ? col.mean.toFixed(2) : col.mean) : '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="py-8 text-center text-muted-foreground">Loading profile table...</div>
          )}
        </CardContent>
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-5xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Data Preview: {dataset.filename}</DialogTitle>
            <DialogDescription>Viewing top 100 rows of your dataset.</DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            {previewLoading ? (
              <div className="py-8 text-center text-muted-foreground animate-pulse">Loading data preview...</div>
            ) : previewData.columns.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">Failed to load data preview.</div>
            ) : (
              <div className="rounded-md border overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/50">
                      {previewData.columns.map((col, i) => (
                        <TableHead key={i} className="whitespace-nowrap">{col}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {previewData.data.map((row, i) => (
                      <TableRow key={i}>
                        {previewData.columns.map((col, j) => (
                          <TableCell key={j} className="whitespace-nowrap">
                            {String(row[col])}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
