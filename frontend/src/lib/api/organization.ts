export interface Organization {
  id: string;
  name: string;
  plan: string;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  role: 'super_admin' | 'hr_manager' | 'recruiter' | 'interviewer';
  is_verified: boolean;
  created_at: string;
}

const getHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

export async function getMe(): Promise<User & { org_id: string }> {
  const res = await fetch(`/api/v1/auth/me`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Not authenticated');
  return res.json();
}

export async function getOrganization(id: string): Promise<Organization> {
  const res = await fetch(`/api/v1/organizations/${id}`, {
    headers: getHeaders(),
  });
  if (!res.ok) {
    if (res.status === 404) throw new Error('Organization not found');
    throw new Error('Failed to fetch organization');
  }
  return res.json();
}

export async function updateOrganization(id: string, data: { name?: string; plan?: string }): Promise<Organization> {
  const res = await fetch(`/api/v1/organizations/${id}`, {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    if (res.status === 403) throw new Error('Not authorized to update organization');
    throw new Error('Failed to update organization');
  }
  return res.json();
}

export async function listOrganizationUsers(id: string): Promise<User[]> {
  const res = await fetch(`/api/v1/organizations/${id}/users`, {
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json();
}

export async function updateUserRole(orgId: string, userId: string, role: string): Promise<User> {
  const res = await fetch(`/api/v1/organizations/${orgId}/users/${userId}/role`, {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify({ role }),
  });
  if (!res.ok) {
    if (res.status === 400) throw new Error('Invalid role change requested');
    if (res.status === 403) throw new Error('Not authorized to change user roles');
    throw new Error('Failed to update user role');
  }
  return res.json();
}
