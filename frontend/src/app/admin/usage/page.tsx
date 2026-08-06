"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Activity, Download, Search } from "lucide-react";
import { Input } from "@/components/ui/input";

const USAGE_LOGS = [
  { id: "log-1", org: "DigitalSofts", feature: "Resume Parsing", model: "gpt-4-turbo", tokens: 1450, cost: 0.0145, timestamp: "2024-05-15 14:32:01" },
  { id: "log-2", org: "ABC Software", feature: "Copilot Search", model: "gpt-3.5-turbo", tokens: 820, cost: 0.0016, timestamp: "2024-05-15 14:28:45" },
  { id: "log-3", org: "DigitalSofts", feature: "Candidate Matching", model: "text-embedding-3", tokens: 250, cost: 0.0001, timestamp: "2024-05-15 14:20:12" },
  { id: "log-4", org: "XYZ Bank", feature: "Resume Parsing", model: "gpt-4-turbo", tokens: 1680, cost: 0.0168, timestamp: "2024-05-15 13:55:09" },
  { id: "log-5", org: "ABC Software", feature: "Candidate Matching", model: "text-embedding-3", tokens: 190, cost: 0.0001, timestamp: "2024-05-15 13:40:22" },
];

export default function UsageLogsPage() {
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
              {USAGE_LOGS.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm text-zinc-500">{log.timestamp}</TableCell>
                  <TableCell className="font-medium text-zinc-900">{log.org}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center rounded-full bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                      {log.feature}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-600 font-mono">{log.model}</TableCell>
                  <TableCell className="text-right text-sm text-zinc-900">{log.tokens.toLocaleString()}</TableCell>
                  <TableCell className="text-right text-sm font-medium text-zinc-900">${log.cost.toFixed(4)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
