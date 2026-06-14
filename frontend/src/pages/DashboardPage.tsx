import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { groupsApi } from '../api';
import { useAuth } from '../contexts/AuthContext';
import { Users, ArrowRight, Plus, TrendingUp, TrendingDown } from 'lucide-react';

interface GroupSummary {
  id: string;
  name: string;
  base_currency: string;
  created_at: string;
  member_count: number;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    try {
      const res = await groupsApi.list();
      setGroups(res.data);
    } catch (err) {
      console.error('Failed to load groups:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-white/40 mt-1">Welcome back, {user?.name} 👋</p>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="stat-card animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center">
              <Users className="w-6 h-6 text-primary-400" />
            </div>
            <div>
              <p className="stat-value">{groups.length}</p>
              <p className="stat-label">Groups</p>
            </div>
          </div>
        </div>
        <div className="stat-card animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <p className="stat-value">{groups.reduce((sum, g) => sum + g.member_count, 0)}</p>
              <p className="stat-label">Active Members</p>
            </div>
          </div>
        </div>
        <div className="stat-card animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
              <TrendingDown className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <p className="stat-value">₹ —</p>
              <p className="stat-label">Net Balance</p>
            </div>
          </div>
        </div>
      </div>

      {/* Groups List */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Your Groups</h2>
        {groups.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <Users className="w-12 h-12 mx-auto text-white/20 mb-4" />
            <h3 className="text-lg font-medium text-white/60 mb-2">No groups yet</h3>
            <p className="text-white/30 mb-6">Create a group or ask a flatmate to add you.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {groups.map((group, index) => (
              <Link
                key={group.id}
                to={`/groups/${group.id}`}
                className="glass-card-hover p-6 group animate-slide-up"
                style={{ animationDelay: `${0.1 * index}s` }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/30 to-primary-700/30 
                                  flex items-center justify-center border border-primary-500/20">
                    <Users className="w-6 h-6 text-primary-400" />
                  </div>
                  <ArrowRight className="w-5 h-5 text-white/20 group-hover:text-primary-400 
                                         transition-all group-hover:translate-x-1" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-1">{group.name}</h3>
                <p className="text-sm text-white/40">
                  {group.member_count} member{group.member_count !== 1 ? 's' : ''} • {group.base_currency}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
