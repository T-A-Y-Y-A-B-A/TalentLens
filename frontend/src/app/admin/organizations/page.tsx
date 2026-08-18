"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Building2, Search, Filter, Loader2, Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { components } from "@/lib/api/schema";

type AdminOrganizationOut = components["schemas"]["AdminOrganizationOut"];

export default function OrganizationsPage() {
  const [loading, setLoading] = useState(true);
  const [organizations, setOrganizations] = useState<AdminOrganizationOut[]>([]);

  // Delete org state
  const [deleteTarget, setDeleteTarget] = useState<AdminOrganizationOut | null>(null);
  const [confirmNameInput, setConfirmNameInput] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

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

  const handleDeleteOrg = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`/api/v1/organizations/${deleteTarget.id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ confirm_name: confirmNameInput }),
      });
      if (res.ok) {
        setOrganizations((prev) => prev.filter((o) => o.id !== deleteTarget.id));
        setDeleteTarget(null);
        setConfirmNameInput("");
      } else {
        const err = await res.json().catch(() => ({}));
        setDeleteError(err?.detail ?? "Failed to delete organization");
      }
    } catch {
      setDeleteError("Error deleting organization. Please try again.");
    } finally {
      setDeleting(false);
    }
  };

  const confirmNameMatches = confirmNameInput === deleteTarget?.name;

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
                {/* Two action columns — Manage (hr_manager's domain) + Delete (platform admin) */}
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
                    {/* Option A: Manage stays for hr_manager day-to-day, Delete added for platform admin */}
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50">
                        Manage
                      </Button>
                      <Button
                        id={`delete-org-${org.id}`}
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => {
                          setDeleteTarget(org);
                          setConfirmNameInput("");
                          setDeleteError(null);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Delete Organization Confirmation Dialog — requires typing org name */}
      <AlertDialog
        open={!!deleteTarget}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTarget(null);
            setConfirmNameInput("");
            setDeleteError(null);
          }
        }}
      >
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-red-700">Delete Organization</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently soft-delete{" "}
              <span className="font-semibold text-zinc-900">{deleteTarget?.name}</span> and cascade to all jobs,
              users, interviews, and applications. All active applications will be withdrawn.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-3 py-2">
            <p className="text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2 text-sm font-medium">
              ⚠ This action cannot be undone.
            </p>
            <div className="space-y-1 pt-1">
              <label className="text-sm font-medium text-zinc-700">
                Type the organization name to confirm:
              </label>
              <Input
                id="confirm-org-name-input"
                value={confirmNameInput}
                onChange={(e) => setConfirmNameInput(e.target.value)}
                placeholder={deleteTarget?.name ?? ""}
                className={confirmNameMatches ? "border-green-400 focus:ring-green-400" : ""}
                autoComplete="off"
                spellCheck={false}
              />
              {deleteError && (
                <p className="text-sm text-red-600 mt-1">{deleteError}</p>
              )}
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              id="confirm-delete-org-btn"
              className="bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
              onClick={handleDeleteOrg}
              disabled={deleting || !confirmNameMatches}
            >
              {deleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete Organization
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
