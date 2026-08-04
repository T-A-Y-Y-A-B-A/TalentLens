'use client';

import { useEffect, useState } from 'react';
import { getMe, getOrganization, listOrganizationUsers, updateOrganization, updateUserRole, User, Organization } from '@/lib/api/organization';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, ShieldCheck, Settings, Users } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function OrganizationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [currentUser, setCurrentUser] = useState<(User & { org_id: string }) | null>(null);
  const [org, setOrg] = useState<Organization | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  
  // Org Editing state
  const [isEditingOrg, setIsEditingOrg] = useState(false);
  const [orgName, setOrgName] = useState('');
  const [savingOrg, setSavingOrg] = useState(false);

  // Role Change state
  const [roleChangeTarget, setRoleChangeTarget] = useState<{ user: User, newRole: string } | null>(null);
  const [savingRole, setSavingRole] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const me = await getMe();
        setCurrentUser(me);
        
        const [orgData, usersData] = await Promise.all([
          getOrganization(me.org_id),
          listOrganizationUsers(me.org_id)
        ]);
        
        setOrg(orgData);
        setOrgName(orgData.name);
        setUsers(usersData);
      } catch (err: any) {
        if (err.message === 'Not authenticated') {
          router.push('/login');
        } else {
          setError(err.message || 'Failed to load organization data.');
        }
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [router]);

  const canEdit = currentUser?.role === 'hr_manager' || currentUser?.role === 'super_admin';

  const handleOrgSave = async () => {
    if (!org || !currentUser) return;
    setSavingOrg(true);
    try {
      const updated = await updateOrganization(currentUser.org_id, { name: orgName });
      setOrg(updated);
      setIsEditingOrg(false);
    } catch (err: any) {
      setError(err.message || 'Failed to update organization.');
    } finally {
      setSavingOrg(false);
    }
  };

  const confirmRoleChange = async () => {
    if (!roleChangeTarget || !currentUser) return;
    setSavingRole(true);
    try {
      await updateUserRole(currentUser.org_id, roleChangeTarget.user.id, roleChangeTarget.newRole);
      setUsers(users.map(u => 
        u.id === roleChangeTarget.user.id ? { ...u, role: roleChangeTarget.newRole as any } : u
      ));
    } catch (err: any) {
      setError(err.message || 'Failed to update role.');
    } finally {
      setSavingRole(false);
      setRoleChangeTarget(null);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error || !org) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error || 'An unknown error occurred.'}</AlertDescription>
      </Alert>
    );
  }

  const roleColors: Record<string, string> = {
    super_admin: 'bg-purple-100 text-purple-700 border-purple-200',
    hr_manager: 'bg-indigo-100 text-indigo-700 border-indigo-200',
    recruiter: 'bg-blue-100 text-blue-700 border-blue-200',
    interviewer: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  };

  const formatRole = (role: string) => role.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-zinc-900">Organization Settings</h1>
        <p className="text-zinc-500 mt-2">Manage your organization details and team members.</p>
      </div>

      <Card className="border-zinc-200 shadow-sm rounded-xl overflow-hidden">
        <CardHeader className="bg-zinc-50/50 border-b border-zinc-100 pb-4">
          <div className="flex items-center space-x-2">
            <Settings className="w-5 h-5 text-indigo-500" />
            <CardTitle>Organization Details</CardTitle>
          </div>
          <CardDescription>View and update core organization information.</CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div className="flex items-center justify-between max-w-xl">
            <div className="space-y-1 w-full mr-4">
              <label className="text-sm font-medium text-zinc-500">Organization Name</label>
              {isEditingOrg ? (
                <Input 
                  value={orgName} 
                  onChange={(e) => setOrgName(e.target.value)} 
                  disabled={savingOrg}
                  className="max-w-md font-medium text-lg"
                />
              ) : (
                <p className="text-xl font-semibold text-zinc-900">{org.name}</p>
              )}
            </div>
            
            {canEdit && (
              <div>
                {isEditingOrg ? (
                  <div className="flex space-x-2 mt-4">
                    <Button variant="outline" onClick={() => { setIsEditingOrg(false); setOrgName(org.name); }} disabled={savingOrg}>Cancel</Button>
                    <Button onClick={handleOrgSave} disabled={savingOrg || !orgName.trim() || orgName === org.name} className="bg-indigo-600 hover:bg-indigo-700">
                      {savingOrg && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Save
                    </Button>
                  </div>
                ) : (
                  <Button variant="outline" onClick={() => setIsEditingOrg(true)} className="mt-4 shadow-sm">
                    Edit Details
                  </Button>
                )}
              </div>
            )}
          </div>
          
          <div className="mt-6 pt-6 border-t border-zinc-100">
            <p className="text-sm text-zinc-500">
              <span className="font-medium mr-2">Current Plan:</span> 
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-zinc-100 text-zinc-800 uppercase tracking-wider">
                {org.plan}
              </span>
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="border-zinc-200 shadow-sm rounded-xl overflow-hidden">
        <CardHeader className="bg-zinc-50/50 border-b border-zinc-100 pb-4">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-indigo-500" />
            <CardTitle>Team Members</CardTitle>
          </div>
          <CardDescription>Manage who has access to your organization.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-zinc-50/50">
              <TableRow className="hover:bg-transparent">
                <TableHead className="font-semibold">User</TableHead>
                <TableHead className="font-semibold">Status</TableHead>
                <TableHead className="font-semibold">Joined</TableHead>
                <TableHead className="font-semibold">Role</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id} className="group">
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium text-zinc-900">{user.email}</span>
                      {user.id === currentUser?.id && <span className="text-xs text-indigo-500 font-medium">You</span>}
                    </div>
                  </TableCell>
                  <TableCell>
                    {user.is_verified ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                        <ShieldCheck className="w-3 h-3 mr-1" /> Verified
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100">
                        Pending
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-zinc-500 text-sm">
                    {new Date(user.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {canEdit ? (
                      <Select 
                        value={user.role} 
                        onValueChange={(val) => {
                          if (val !== user.role) {
                            setRoleChangeTarget({ user, newRole: val });
                          }
                        }}
                      >
                        <SelectTrigger className="w-[160px] h-8 text-sm">
                          <SelectValue placeholder="Select role" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="super_admin">Super Admin</SelectItem>
                          <SelectItem value="hr_manager">HR Manager</SelectItem>
                          <SelectItem value="recruiter">Recruiter</SelectItem>
                          <SelectItem value="interviewer">Interviewer</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${roleColors[user.role] || 'bg-zinc-100 text-zinc-800'}`}>
                        {formatRole(user.role)}
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <AlertDialog open={!!roleChangeTarget} onOpenChange={(open) => !open && setRoleChangeTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Change User Role</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to change the role for <span className="font-semibold text-zinc-900">{roleChangeTarget?.user.email}</span> to <span className="font-semibold text-zinc-900">{roleChangeTarget && formatRole(roleChangeTarget.newRole)}</span>?
              {roleChangeTarget?.user.id === currentUser?.id && roleChangeTarget?.newRole !== 'hr_manager' && roleChangeTarget?.newRole !== 'super_admin' && (
                <div className="mt-4 p-3 bg-red-50 text-red-800 rounded-md border border-red-200 text-sm font-medium">
                  Warning: You are demoting yourself. You will lose access to manage the organization.
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={savingRole}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmRoleChange} disabled={savingRole} className="bg-indigo-600 hover:bg-indigo-700">
              {savingRole && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
