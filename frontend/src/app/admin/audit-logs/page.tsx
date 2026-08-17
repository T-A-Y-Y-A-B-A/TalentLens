"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, ShieldAlert, ArrowDownToLine } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { components } from "@/lib/api/schema";

type AdminAuditLogOut = components["schemas"]["AdminAuditLogOut"];

export default function AuditLogsPage() {
  const [loading, setLoading] = useState(true);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLogOut[]>([]);

  useEffect(() => {
    async function fetchLogs() {
      try {
        const { data } = await apiClient.GET("/api/v1/admin/audit_logs" as any, {});
        if (data) {
          setAuditLogs(data as AdminAuditLogOut[]);
        }
      } catch (err) {
        console.error("Failed to fetch audit logs", err);
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
          <h1 className="text-2xl font-bold text-zinc-900">System Audit Logs</h1>
          <p className="text-zinc-500 mt-1">Cross-tenant security and action logs.</p>
        </div>
        <Button variant="outline">
          <ArrowDownToLine className="mr-2 h-4 w-4" />
          Export Archive
        </Button>
      </div>

      <Card>
        <div className="p-4 border-b flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <Input className="pl-10" placeholder="Search by action, actor, or resource ID..." />
          </div>
        </div>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp (UTC)</TableHead>
                <TableHead>Organization</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Resource ID</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-zinc-500">Loading audit logs...</TableCell>
                </TableRow>
              ) : auditLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm text-zinc-500">{new Date(log.created_at).toLocaleString()}</TableCell>
                  <TableCell className="font-medium text-zinc-900">{log.org_name}</TableCell>
                  <TableCell className="text-sm text-zinc-600">{log.actor_email}</TableCell>
                  <TableCell>
                    <span className="font-mono text-xs bg-zinc-100 text-zinc-800 px-2 py-1 rounded">
                      {log.action}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-500 truncate max-w-[150px]">{log.resource_id}</TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                      log.status === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                    }`}>
                      {log.status}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
