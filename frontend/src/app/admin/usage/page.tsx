"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Activity, Download, Search } from "lucide-react";
import { Input } from "@/components/ui/input";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { components } from "@/lib/api/schema";

type AdminUsageLogOut = components["schemas"]["AdminUsageLogOut"];

export default function UsageLogsPage() {
  const [loading, setLoading] = useState(true);
  const [usageLogs, setUsageLogs] = useState<AdminUsageLogOut[]>([]);

  useEffect(() => {
    async function fetchLogs() {
      try {
        const { data } = await apiClient.GET("/api/v1/admin/usage_logs" as any, {});
        if (data) {
          setUsageLogs(data as AdminUsageLogOut[]);
        }
      } catch (err) {
        console.error("Failed to fetch usage logs", err);
      } finally {
        setLoading(false);
      }
    }
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">AI Usage Logs</h1>
          <p className="text-zinc-500 mt-1">Monitor API consumption across all tenants.</p>
        </div>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      <Card>
        <div className="p-4 border-b flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <Input className="pl-10" placeholder="Search by org, feature, or model..." />
          </div>
        </div>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp (UTC)</TableHead>
                <TableHead>Organization</TableHead>
                <TableHead>Feature</TableHead>
                <TableHead>Model</TableHead>
                <TableHead className="text-right">Tokens</TableHead>
                <TableHead className="text-right">Estimated Cost</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-zinc-500">Loading AI usage logs...</TableCell>
                </TableRow>
              ) : usageLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm text-zinc-500">{new Date(log.created_at).toLocaleString()}</TableCell>
                  <TableCell className="font-medium text-zinc-900">{log.org_name}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                      {log.endpoint}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-600 font-mono">Any</TableCell>
                  <TableCell className="text-right text-sm text-zinc-900">{log.total_tokens.toLocaleString()}</TableCell>
                  <TableCell className="text-right text-sm font-medium text-zinc-900">N/A</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
