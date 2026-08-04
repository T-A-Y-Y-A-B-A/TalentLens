"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";

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
        }
      } catch (e) {
        console.error("Failed to fetch users");
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
        alert("Role updated successfully!");
        fetchUsers();
      } else if (error) {
        alert("Error updating role");
      }
    } catch (e) {
      alert("Error updating role");
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-white">Users & Roles</h2>
      
      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
        <table className="min-w-full divide-y divide-gray-300 dark:divide-zinc-700">
          <thead className="bg-gray-50 dark:bg-zinc-800">
            <tr>
              <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-gray-100 sm:pl-6">Email</th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Status</th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">Role</th>
              {canManageRoles && (
                <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                  <span className="sr-only">Actions</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-zinc-700 bg-white dark:bg-zinc-900">
            {users.map((u) => (
              <tr key={u.id}>
                <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-gray-100 sm:pl-6">{u.email}</td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-400">
                  {u.is_verified ? (
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-200">Verified</span>
                  ) : (
                    <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">Pending</span>
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
                {canManageRoles && (
                  <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                    {/* Add any other actions here */}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
