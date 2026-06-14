import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { groupsApi, expensesApi, balancesApi, settlementsApi } from '../api';
import { useAuth } from '../contexts/AuthContext';
import AddExpenseModal from '../components/AddExpenseModal';
import SettlementModal from '../components/SettlementModal';
import {
  Users, Plus, ArrowRight, Calendar, TrendingUp, TrendingDown,
  Receipt, Upload, HandCoins, ChevronDown, ChevronUp, Search
} from 'lucide-react';

export default function GroupPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [group, setGroup] = useState<any>(null);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [balances, setBalances] = useState<any[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [showSettlementModal, setShowSettlementModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'expenses' | 'members' | 'settlements'>('expenses');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (groupId) loadAll();
  }, [groupId]);

  const loadAll = async () => {
    try {
      const [gRes, eRes, bRes, sRes] = await Promise.all([
        groupsApi.get(groupId!),
        expensesApi.list(groupId!),
        balancesApi.get(groupId!),
        balancesApi.getSuggested(groupId!),
      ]);
      setGroup(gRes.data);
      setExpenses(eRes.data);
      setBalances(bRes.data);
      setSuggestions(sRes.data);
    } catch (err) {
      console.error('Failed to load group data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExpenseCreated = () => {
    setShowExpenseModal(false);
    loadAll();
  };

  const handleSettlementCreated = () => {
    setShowSettlementModal(false);
    loadAll();
  };

  const filteredExpenses = expenses.filter(e => 
    e.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.paid_by_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!group) return <div className="text-white/40">Group not found</div>;

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
            {group.name}
          </h1>
          <p className="text-white/40 mt-1">
            {group.members.filter((m: any) => !m.left_at).length} active members • {group.base_currency}
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate(`/groups/${groupId}/import`)} className="btn-secondary flex items-center gap-2">
            <Upload className="w-4 h-4" /> Import CSV
          </button>
          <button onClick={() => setShowSettlementModal(true)} className="btn-secondary flex items-center gap-2">
            <HandCoins className="w-4 h-4" /> Record Settlement
          </button>
          <button onClick={() => setShowExpenseModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Expense
          </button>
        </div>
      </div>

      {/* Balance Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {balances.map((b: any, i: number) => (
          <Link
            key={b.user_id}
            to={`/expenses/breakdown?userId=${b.user_id}&groupId=${groupId}`}
            onClick={(e) => {
              e.preventDefault();
              // Navigate to a drilldown view later — for now show via API
            }}
            className="glass-card-hover p-4 text-center animate-slide-up"
            style={{ animationDelay: `${0.05 * i}s` }}
          >
            <div className={`w-10 h-10 mx-auto rounded-full flex items-center justify-center text-sm font-bold mb-2
              ${parseFloat(b.balance_inr) > 0 
                ? 'bg-emerald-500/20 text-emerald-400' 
                : parseFloat(b.balance_inr) < 0 
                  ? 'bg-red-500/20 text-red-400' 
                  : 'bg-white/10 text-white/40'
              }`}
            >
              {b.user_name.charAt(0)}
            </div>
            <p className="text-sm font-medium text-white truncate">{b.user_name}</p>
            <p className={`text-lg font-bold mt-1 ${
              parseFloat(b.balance_inr) > 0 ? 'text-emerald-400' : 
              parseFloat(b.balance_inr) < 0 ? 'text-red-400' : 'text-white/40'
            }`}>
              ₹{Math.abs(parseFloat(b.balance_inr)).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </p>
            <p className="text-xs text-white/30 mt-0.5">
              {b.status === 'owed' ? 'is owed' : b.status === 'owes' ? 'owes' : 'settled'}
            </p>
          </Link>
        ))}
      </div>

      {/* Suggested Settlements */}
      {suggestions.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <HandCoins className="w-5 h-5 text-primary-400" />
            Suggested Settlements
            <span className="badge-info ml-2">{suggestions.length} transfer{suggestions.length > 1 ? 's' : ''}</span>
          </h3>
          <div className="space-y-3">
            {suggestions.map((s: any, i: number) => (
              <div key={i} className="flex items-center gap-4 p-3 bg-white/5 rounded-xl">
                <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 text-sm font-bold">
                  {s.from_user_name.charAt(0)}
                </div>
                <div className="flex-1">
                  <span className="text-white font-medium">{s.from_user_name}</span>
                  <span className="text-white/30 mx-2">pays</span>
                  <span className="text-white font-medium">{s.to_user_name}</span>
                </div>
                <span className="text-lg font-bold text-primary-400">
                  ₹{parseFloat(s.amount_inr).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 p-1 rounded-xl w-fit">
        {(['expenses', 'members', 'settlements'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all capitalize
              ${activeTab === tab 
                ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30' 
                : 'text-white/40 hover:text-white'
              }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Expenses Tab */}
      {activeTab === 'expenses' && (
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              type="text"
              placeholder="Search expenses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field pl-11"
            />
          </div>

          {/* Expense List */}
          <div className="glass-card overflow-hidden">
            {filteredExpenses.length === 0 ? (
              <div className="p-12 text-center">
                <Receipt className="w-12 h-12 mx-auto text-white/20 mb-4" />
                <p className="text-white/40">No expenses yet</p>
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {filteredExpenses.map((expense) => (
                  <Link
                    key={expense.id}
                    to={`/expenses/${expense.id}`}
                    className="flex items-center gap-4 p-4 hover:bg-white/5 transition-colors group"
                  >
                    <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center">
                      <Receipt className="w-5 h-5 text-primary-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-white truncate">{expense.description}</p>
                      <p className="text-sm text-white/30">
                        Paid by {expense.paid_by_name} • {new Date(expense.date).toLocaleDateString('en-IN')}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-white">
                        {expense.currency === 'INR' ? '₹' : '$'}
                        {parseFloat(expense.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </p>
                      {expense.currency !== 'INR' && (
                        <p className="text-xs text-white/30">
                          ₹{parseFloat(expense.amount_in_inr).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </p>
                      )}
                      <span className="badge-info text-[10px] mt-1 inline-block">{expense.split_type}</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-white/10 group-hover:text-primary-400 transition-all" />
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Members Tab */}
      {activeTab === 'members' && (
        <div className="glass-card overflow-hidden">
          <div className="divide-y divide-white/5">
            {group.members.map((member: any) => (
              <div key={member.id} className="flex items-center gap-4 p-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold
                  ${member.left_at 
                    ? 'bg-white/10 text-white/30' 
                    : 'bg-gradient-to-br from-primary-400 to-primary-600 text-white'
                  }`}
                >
                  {member.user_name.charAt(0)}
                </div>
                <div className="flex-1">
                  <p className={`font-medium ${member.left_at ? 'text-white/40' : 'text-white'}`}>
                    {member.user_name}
                    {member.left_at && <span className="ml-2 badge-danger text-[10px]">Left</span>}
                  </p>
                  <p className="text-sm text-white/30">{member.user_email}</p>
                </div>
                <div className="text-right text-sm">
                  <p className="text-white/40">
                    <Calendar className="w-3 h-3 inline mr-1" />
                    Joined {new Date(member.joined_at).toLocaleDateString('en-IN')}
                  </p>
                  {member.left_at && (
                    <p className="text-red-400/60">
                      Left {new Date(member.left_at).toLocaleDateString('en-IN')}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Settlements Tab */}
      {activeTab === 'settlements' && (
        <div className="glass-card p-6">
          <p className="text-white/40 text-center">Settlements will appear here after recording.</p>
        </div>
      )}

      {/* Modals */}
      {showExpenseModal && (
        <AddExpenseModal
          groupId={groupId!}
          members={group.members.filter((m: any) => !m.left_at)}
          onClose={() => setShowExpenseModal(false)}
          onCreated={handleExpenseCreated}
        />
      )}
      {showSettlementModal && (
        <SettlementModal
          groupId={groupId!}
          members={group.members}
          onClose={() => setShowSettlementModal(false)}
          onCreated={handleSettlementCreated}
        />
      )}
    </div>
  );
}
