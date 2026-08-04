"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/providers/AuthProvider";
import { apiClient } from "@/lib/api/client";

export default function OrganizationSettingsPage() {
  const { user } = useAuth();
  const [org, setOrg] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [plan, setPlan] = useState("");

  useEffect(() => {
    if (user && (user as any).org_id) {
      apiClient.GET("/api/v1/organizations/{id}", {
        params: { path: { id: (user as any).org_id } }
      }).then(({ data, error }) => {
        if (data) {
          setOrg(data);
          setName(data.name);
          setPlan(data.plan);
        }
        setLoading(false);
      });
    }
  }, [user]);

  const handleSave = async () => {
    if (!user || !(user as any).org_id) return;
    try {
      const { data, error } = await apiClient.PATCH("/api/v1/organizations/{id}", {
        params: { path: { id: (user as any).org_id } },
        body: { name, plan }
      });
      if (data) {
        setOrg(data);
        alert("Saved successfully!");
      } else if (error) {
        alert("Error saving");
      }
    } catch (e) {
      alert("Error saving");
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-semibold mb-6 text-gray-900 dark:text-white">Organization Profile</h2>
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 sm:text-sm dark:bg-zinc-800 dark:border-zinc-700 dark:text-white"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Plan</label>
          <input
            type="text"
            value={plan}
            onChange={(e) => setPlan(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 sm:text-sm dark:bg-zinc-800 dark:border-zinc-700 dark:text-white"
          />
        </div>
        <button
          onClick={handleSave}
          className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Save Changes
        </button>
      </div>
    </div>
  );
}
