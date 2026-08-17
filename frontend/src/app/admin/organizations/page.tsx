"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Building2, Search, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { components } from "@/lib/api/schema";

type AdminOrganizationOut = components["schemas"]["AdminOrganizationOut"];

export default function OrganizationsPage() {
  const [loading, setLoading] = useState(true);
  const [organizations, setOrganizations] = useState<AdminOrganizationOut[]>([]);

  useEffect(() => {
    async function fetchOrganizations() {
      try {
        const { data } = await apiClient.GET("/api/v1/admin/organizations" as any, {});
        if (data) {
          setOrganizations(data as AdminOrganizationOut[]);
        }
      } catch (err) {
        console.error("Failed to fetch organizations", err);
      } finally {
        setLoading(false);
      }
    }
    fetchOrganizations();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Organizations</h1>
          <p className="text-zinc-500 mt-1">Manage tenants across the platform.</p>
        </div>
        <Button className="bg-indigo-600 hover:bg-indigo-700">
          <Building2 className="mr-2 h-4 w-4" />
          Provision Tenant
        </Button>
      </div>

      <Card>
        <div className="p-4 border-b flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <Input className="pl-10" placeholder="Search organizations..." />
          </div>
          <Button variant="outline" size="sm">
            <Filter className="mr-2 h-4 w-4" />
            Filters
          </Button>
        </div>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Organization</TableHead>
                <TableHead>Slug</TableHead>
                <TableHead>Plan</TableHead>
                <TableHead className="text-right">Users</TableHead>
                <TableHead className="text-right">Active Jobs</TableHead>
                <TableHead className="text-right">Created</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-zinc-500">Loading organizations...</TableCell>
                </TableRow>
              ) : organizations.map((org) => (
                <TableRow key={org.id}>
                  <TableCell className="font-medium text-zinc-900">{org.name}</TableCell>
                  <TableCell className="text-zinc-500">{org.slug}</TableCell>
                  <TableCell>
                    <span className="px-2 py-1 rounded-full text-xs font-medium capitalize bg-purple-50 text-purple-700">
                      Enterprise
                    </span>
                  </TableCell>
                  <TableCell className="text-right">{org.users_count}</TableCell>
                  <TableCell className="text-right">{org.active_jobs_count}</TableCell>
                  <TableCell className="text-right text-zinc-500">{new Date(org.created_at).toLocaleDateString()}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50">
                      Manage
                    </Button>
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
