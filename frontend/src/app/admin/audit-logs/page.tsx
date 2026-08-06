"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, ShieldAlert, ArrowDownToLine } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const AUDIT_LOGS = [
  { id: "al-1", org: "DigitalSofts", actor: "hr@digitalsofts.demo", action: "job.created", resource: "job_id_123", status: "success", timestamp: "2024-05-15 14:32:01" },
  { id: "al-2", org: "ABC Software", actor: "hr@abc-software.demo", action: "candidate.rejected", resource: "candidate_id_456", status: "success", timestamp: "2024-05-15 14:28:45" },
  { id: "al-3", org: "System", actor: "system.worker", action: "database.backup", resource: "daily_snapshot", status: "success", timestamp: "2024-05-15 08:00:00" },
  { id: "al-4", org: "XYZ Bank", actor: "unknown", action: "auth.login.failed", resource: "user_email", status: "failure", timestamp: "2024-05-15 07:12:33" },
  { id: "al-5", org: "XYZ Bank", actor: "hr@xyz-bank.demo", action: "user.invited", resource: "new_recruiter_email", status: "success", timestamp: "2024-05-14 16:40:22" },
];

export default function AuditLogsPage() {
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
              {AUDIT_LOGS.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm text-zinc-500">{log.timestamp}</TableCell>
                  <TableCell className="font-medium text-zinc-900">{log.org}</TableCell>
                  <TableCell className="text-sm text-zinc-600">{log.actor}</TableCell>
                  <TableCell>
                    <span className="font-mono text-xs bg-zinc-100 text-zinc-800 px-2 py-1 rounded">
                      {log.action}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-500 truncate max-w-[150px]">{log.resource}</TableCell>
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
