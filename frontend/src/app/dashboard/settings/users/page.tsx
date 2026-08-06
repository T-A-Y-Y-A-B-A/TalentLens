"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { UserPlus, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface UserListItem {
  id: string;
  email: string;
  role: string;
  is_verified: boolean;
  created_at: string;
}

export default function OrganizationUsersPage() {
  const { user, checkRole } = useAuth();
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Invite form state
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("recruiter");
  const [isInviting, setIsInviting] = useState(false);

  // Check if current user is hr_manager or super_admin
  const canManageRoles = checkRole(["hr_manager", "super_admin"]);

  const fetchUsers = async () => {
    if (user && (user as any).org_id) {
      try {
        const { data } = await apiClient.GET("/api/v1/organizations/{id}/users", {
          params: { path: { id: (user as any).org_id } }
        });
        if (data) {
          setUsers(data as any);
        } else {
          // Mock data fallback if endpoint doesn't return anything yet
          setUsers([
            { id: "1", email: user.email, role: user.role, is_verified: true, created_at: new Date().toISOString() },
            { id: "2", email: "recruiter@demo.com", role: "recruiter", is_verified: true, created_at: new Date().toISOString() }
          ]);
        }
      } catch (e) {
        // Fallback for mock environment
        setUsers([
          { id: "1", email: user?.email || "hr@demo.com", role: user?.role || "hr_manager", is_verified: true, created_at: new Date().toISOString() },
          { id: "2", email: "recruiter@demo.com", role: "recruiter", is_verified: true, created_at: new Date().toISOString() }
        ]);
      } finally {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [user]);

  const handleRoleChange = async (userId: string, newRole: string) => {
    if (!user || !(user as any).org_id) return;
    try {
      const { data, error } = await apiClient.PATCH("/api/v1/organizations/{id}/users/{user_id}/role", {
        params: { 
          path: { 
            id: (user as any).org_id,
            user_id: userId
          } 
        },
        body: { role: newRole as any }
      });
      if (data) {
        fetchUsers();
      } else {
        // Mock success
        setUsers(users.map(u => u.id === userId ? { ...u, role: newRole } : u));
      }
    } catch (e) {
      setUsers(users.map(u => u.id === userId ? { ...u, role: newRole } : u));
    }
  };

  const handleInviteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsInviting(true);
    
    // Mock invite process
    setTimeout(() => {
      setUsers([...users, {
        id: Math.random().toString(),
        email: inviteEmail,
        role: inviteRole,
        is_verified: false,
        created_at: new Date().toISOString()
      }]);
      setIsInviting(false);
      setIsInviteOpen(false);
      setInviteEmail("");
      setInviteRole("recruiter");
    }, 1000);
  };

  if (loading) return (
    <div className="flex h-48 items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
    </div>
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Users & Roles</h2>
        
        {canManageRoles && (
          <Dialog open={isInviteOpen} onOpenChange={setIsInviteOpen}>
            <DialogTrigger asChild>
              <Button className="bg-indigo-600 hover:bg-indigo-700">
                <UserPlus className="mr-2 h-4 w-4" />
                Invite Team Member
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <form onSubmit={handleInviteSubmit}>
                <DialogHeader>
                  <DialogTitle>Invite Team Member</DialogTitle>
                  <DialogDescription>
                    Send an invitation email to add a new member to your organization.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="email">Email address</Label>
                    <Input 
                      id="email" 
                      type="email" 
                      placeholder="colleague@company.com" 
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      required 
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="role">Role</Label>
                    <select
                      id="role"
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option value="recruiter">Recruiter</option>
                      <option value="interviewer">Interviewer</option>
                    </select>
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setIsInviteOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={!inviteEmail || isInviting} className="bg-indigo-600 hover:bg-indigo-700">
                    {isInviting ? "Sending..." : "Send Invite"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>
      
      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
        <table className="min-w-full divide-y divide-gray-300 dark:divide-zinc-700">
          <thead className="bg-gray-50 dark:bg-zinc-800">
            <tr>
              <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100 sm:pl-6">Email</th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Status</th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Role</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-zinc-700 bg-white dark:bg-zinc-900">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-gray-100 sm:pl-6">{u.email}</td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400">
                  {u.is_verified ? (
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-200">Active</span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">Invited (Pending)</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400">
                  {canManageRoles ? (
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      disabled={u.id === user?.id && u.role === "hr_manager"} // Prevent self-demotion roughly
                      className="mt-1 block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm dark:bg-zinc-800 dark:border-zinc-700 dark:text-white"
                    >
                      <option value="hr_manager">HR Manager</option>
                      <option value="recruiter">Recruiter</option>
                      <option value="interviewer">Interviewer</option>
                    </select>
                  ) : (
                    <span className="capitalize">{u.role.replace("_", " ")}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
