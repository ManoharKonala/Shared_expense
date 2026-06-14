import { useState, useEffect } from 'react';
import { expensesApi } from '../api';
import { X, Plus, Trash2, SplitSquareHorizontal } from 'lucide-react';

interface Props {
  groupId: string;
  members: any[];
  onClose: () => void;
  onCreated: () => void;
}

export default function AddExpenseModal({ groupId, members, onClose, onCreated }: Props) {
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [exchangeRate, setExchangeRate] = useState('1.0');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [paidById, setPaidById] = useState(members[0]?.user_id || '');
  const [splitType, setSplitType] = useState('equal');
  
  // Custom split state
  const [splits, setSplits] = useState<{user_id: string, value: string}[]>(
    members.map(m => ({ user_id: m.user_id, value: '' }))
  );

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const payload: any = {
      description,
      total_amount: parseFloat(amount),
      currency,
      exchange_rate_to_inr: parseFloat(exchangeRate),
      date,
      paid_by_user_id: paidById,
      split_type: splitType,
    };

    if (splitType !== 'equal') {
      payload.splits = splits
        .filter(s => s.value !== '' && parseFloat(s.value) > 0)
        .map(s => {
          const splitObj: any = { user_id: s.user_id };
          if (splitType === 'exact') splitObj.amount = parseFloat(s.value);
          else if (splitType === 'percentage') splitObj.percentage = parseFloat(s.value);
          else if (splitType === 'shares') splitObj.shares = parseFloat(s.value);
          return splitObj;
        });
      
      if (payload.splits.length === 0) {
        setError('Please provide split values');
        setLoading(false);
        return;
      }
    }

    try {
      await expensesApi.create(groupId, payload);
      onCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create expense');
    } finally {
      setLoading(false);
    }
  };

  const handleSplitChange = (userId: string, value: string) => {
    setSplits(splits.map(s => s.user_id === userId ? { ...s, value } : s));
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <SplitSquareHorizontal className="w-6 h-6 text-primary-400" />
            Add Expense
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X className="w-5 h-5 text-white/50" />
          </button>
        </div>

        <div className="overflow-y-auto pr-2 flex-1 custom-scrollbar">
          <form id="expense-form" onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Description</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="input-field"
                  placeholder="e.g. Dinner at Dishoom"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Date</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="input-field"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-white/70 mb-2">Amount</label>
                <div className="relative">
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="absolute left-0 top-0 bottom-0 bg-transparent border-r border-white/10 text-white px-3 focus:outline-none rounded-l-xl"
                  >
                    <option className="bg-surface-800" value="INR">₹ INR</option>
                    <option className="bg-surface-800" value="USD">$ USD</option>
                    <option className="bg-surface-800" value="EUR">€ EUR</option>
                    <option className="bg-surface-800" value="GBP">£ GBP</option>
                  </select>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="input-field pl-24"
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>
              {currency !== 'INR' && (
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Exchange Rate (to INR)</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0.01"
                    value={exchangeRate}
                    onChange={(e) => setExchangeRate(e.target.value)}
                    className="input-field"
                    required
                  />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">Paid By</label>
              <select
                value={paidById}
                onChange={(e) => setPaidById(e.target.value)}
                className="input-field bg-surface-900"
                required
              >
                {members.map(m => (
                  <option key={m.user_id} value={m.user_id} className="bg-surface-800">
                    {m.user_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">Split Type</label>
              <div className="flex gap-2 p-1 bg-white/5 rounded-xl">
                {(['equal', 'exact', 'percentage', 'shares'] as const).map(type => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setSplitType(type)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all capitalize
                      ${splitType === type 
                        ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30' 
                        : 'text-white/40 hover:text-white'
                      }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {splitType !== 'equal' && (
              <div className="bg-white/5 p-4 rounded-xl border border-white/10">
                <h4 className="text-sm font-medium text-white/70 mb-3 capitalize">
                  Enter {splitType} for each member
                </h4>
                <div className="space-y-3">
                  {members.map(m => (
                    <div key={m.user_id} className="flex items-center gap-4">
                      <span className="flex-1 text-sm text-white">{m.user_name}</span>
                      <div className="w-32 relative">
                        <input
                          type="number"
                          step={splitType === 'exact' ? '0.01' : '1'}
                          min="0"
                          value={splits.find(s => s.user_id === m.user_id)?.value || ''}
                          onChange={(e) => handleSplitChange(m.user_id, e.target.value)}
                          className="input-field py-2 pr-8 text-right"
                          placeholder="0"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 text-sm">
                          {splitType === 'exact' ? currency : splitType === 'percentage' ? '%' : ''}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                {error}
              </div>
            )}
          </form>
        </div>

        <div className="mt-6 pt-4 border-t border-white/10 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" form="expense-form" disabled={loading} className="btn-primary min-w-[120px]">
            {loading ? 'Saving...' : 'Save Expense'}
          </button>
        </div>
      </div>
    </div>
  );
}
