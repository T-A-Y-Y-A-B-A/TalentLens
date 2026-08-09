"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { UserPlus, Loader2, Copy, Trash2, CheckCircle2 } from "lucide-react";
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
  full_name?: string;
  role: string;
  is_verified: boolean;
  created_at: string;
  is_invite?: boolean;
  status?: string;
  link?: string;
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
  const [inviteError, setInviteError] = useState("");
  const [copiedLink, setCopiedLink] = useState<string | null>(null);

  // Check if current user is hr_manager or super_admin
  const canManageRoles = checkRole(["hr_manager", "super_admin"]);

  const fetchUsers = async () => {
    if (user && (user as any).org_id) {
      try {
        let combined: UserListItem[] = [];
        
        // Fetch real users
        const { data: userData } = await apiClient.GET("/api/v1/organizations/{id}/users", {
          params: { path: { id: (user as any).org_id } }
        });
        if (userData) {
          combined = [...combined, ...(userData as any).map((u: any) => ({ ...u, is_invite: false }))];
        }

        // Fetch invites
        if (canManageRoles) {
          try {
            const { data: inviteData } = await apiClient.GET("/api/v1/invites");
            if (inviteData) {
              const pendingInvites = (inviteData as any)
                .filter((inv: any) => inv.status === 'pending')
                .map((inv: any) => ({
                  id: inv.id,
                  email: inv.email,
                  role: inv.role,
                  is_verified: false,
                  created_at: inv.created_at,
                  is_invite: true,
                  status: inv.status,
                  link: inv.link
                }));
              combined = [...combined, ...pendingInvites];
            }
          } catch (err) {
             console.error("Failed to fetch invites");
          }
        }

        if (combined.length > 0) {
          setUsers(combined);
        } else {
          // Fallback if completely empty
          setUsers([
            { id: "1", email: user.email, role: user.role, is_verified: true, created_at: new Date().toISOString() }
          ]);
        }
      } catch (e) {
        console.error(e);
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
    const target = users.find(u => u.id === userId);
    if (!target) return;
    
    if (target.is_invite) {
      // For invites, we can't change role easily right now, they should be revoked and recreated.
      alert("Please revoke the invite and create a new one to change the role.");
      return;
    }

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
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsInviting(true);
    setInviteError("");
    
    try {
      const { data, error } = await apiClient.POST("/api/v1/invites", {
        body: {
          email: inviteEmail,
          role: inviteRole
        }
      });
      
      if (error) {
        setInviteError((error as any).detail || "Failed to send invite.");
      } else if (data) {
        setIsInviteOpen(false);
        setInviteEmail("");
        setInviteRole("recruiter");
        fetchUsers();
      }
    } catch (err) {
      setInviteError("Network error. Please try again.");
    } finally {
      setIsInviting(false);
    }
  };
  
  const handleRevoke = async (inviteId: string) => {
    if (!confirm("Are you sure you want to revoke this invite?")) return;
    try {
      await apiClient.POST("/api/v1/invites/{id}/revoke", {
        params: { path: { id: inviteId } }
      });
      fetchUsers();
    } catch (err) {
      console.error("Failed to revoke invite", err);
    }
  };

  const copyToClipboard = (link: string) => {
    navigator.clipboard.writeText(link);
    setCopiedLink(link);
    setTimeout(() => setCopiedLink(null), 2000);
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
                  {inviteError && (
                    <div className="text-sm text-red-500 bg-red-50 p-2 rounded">
                      {inviteError}
                    </div>
                  )}
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
                      <option value="hr_manager">HR Manager</option>
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
              <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100 sm:pl-6">Member</th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Status</th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Role</th>
              <th scope="col" className="px-3 py-3.5 text-right text-sm font-semibold text-gray-900 dark:text-gray-100">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-zinc-700 bg-white dark:bg-zinc-900">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-gray-100 sm:pl-6">
                  <div>{u.full_name || (u.email ? u.email.split("@")[0] : "Member")}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 font-normal">{u.email}</div>
                  {u.is_invite && u.link && (
                    <div className="text-xs text-gray-400 mt-1 flex items-center gap-2">
                      <span>Invite Link:</span>
                      <code className="bg-gray-100 px-1 rounded truncate max-w-[200px] inline-block">{u.link}</code>
                      <button 
                        onClick={() => copyToClipboard(u.link!)}
                        className="text-indigo-600 hover:text-indigo-800 p-1"
                        title="Copy Link"
                      >
                        {copiedLink === u.link ? <CheckCircle2 className="h-3 w-3 text-green-600" /> : <Copy className="h-3 w-3" />}
                      </button>
                    </div>
                  )}
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400">
                  {!u.is_invite ? (
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-200">Active</span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">Invited (Pending)</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400">
                  {canManageRoles && !u.is_invite ? (
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      disabled={u.id === user?.id && u.role === "hr_manager"} // Prevent self-demotion roughly
                      className="mt-1 block w-full rounded-md border-gray-300 py-1 pl-3 pr-8 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 dark:bg-zinc-800 dark:border-zinc-700 dark:text-white"
                    >
                      <option value="hr_manager">HR Manager</option>
                      <option value="recruiter">Recruiter</option>
                      <option value="interviewer">Interviewer</option>
                    </select>
                  ) : (
                    <span className="capitalize">{u.role.replace("_", " ")}</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-right">
                   {u.is_invite && (
                     <Button 
                       variant="ghost" 
                       size="sm" 
                       onClick={() => handleRevoke(u.id)}
                       className="text-red-600 hover:text-red-800 hover:bg-red-50"
                       title="Revoke Invite"
                     >
                       <Trash2 className="h-4 w-4" />
                     </Button>
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
