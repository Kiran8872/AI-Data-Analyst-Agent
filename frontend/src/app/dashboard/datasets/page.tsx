"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/components/AuthProvider";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileSpreadsheet, HardDrive, Calendar, Eye, Trash2, BarChart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

type Dataset = {
  id: number;
  filename: string;
  size_bytes: number;
  created_at: string;
};

export default function DatasetsPage() {
  const { token, logout } = useAuth();
  const router = useRouter();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

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
    } finally {
      setLoading(false);
    }
  }, [token, logout]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDatasets();
  }, [fetchDatasets]);

  const deleteDataset = async (datasetId: number) => {
    if (!token) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/datasets/${datasetId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        fetchDatasets();
      }
    } catch (e) {
      console.error(e);
    }
  };



  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dataset Library</h1>
        <p className="text-muted-foreground">Manage and review your uploaded data files.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Datasets</CardTitle>
          <CardDescription>A complete list of datasets currently indexed in your database.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="py-8 text-center text-muted-foreground animate-pulse">Loading datasets...</div>
          ) : datasets.length === 0 ? (
            <div className="py-12 text-center border-2 border-dashed rounded-lg">
              <FileSpreadsheet className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium">No datasets found</h3>
              <p className="text-sm text-muted-foreground mt-1">Head over to the Overview page to upload your first dataset.</p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>File Name</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Upload Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {datasets.map((ds) => (
                    <TableRow 
                      key={ds.id} 
                      className="cursor-pointer hover:bg-muted/50 transition-colors" 
                      onClick={() => router.push(`/dashboard/datasets/${ds.id}`)}
                    >
                      <TableCell className="font-medium flex items-center gap-3">
                        <div className="bg-primary/10 p-2 rounded-full">
                          <FileSpreadsheet className="h-4 w-4 text-primary" />
                        </div>
                        {ds.filename}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <HardDrive className="h-3 w-3" />
                          {(ds.size_bytes / 1024).toFixed(2)} KB
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Calendar className="h-3 w-3" />
                          {new Date(ds.created_at).toLocaleDateString()}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                          Indexed
                        </span>
                      </TableCell>
                      <TableCell className="text-right whitespace-nowrap">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={(e) => { e.stopPropagation(); deleteDataset(ds.id); }} 
                          className="text-red-500 hover:text-red-600 hover:bg-red-50 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>


    </div>
  );
}
