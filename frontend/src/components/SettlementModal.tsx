import { useState } from 'react';
import { settlementsApi } from '../api';
import { X, HandCoins } from 'lucide-react';

interface Props {
  groupId: string;
  members: any[];
  onClose: () => void;
  onCreated: () => void;
}

export default function SettlementModal({ groupId, members, onClose, onCreated }: Props) {
  const [fromUserId, setFromUserId] = useState(members[0]?.user_id || '');
  const [toUserId, setToUserId] = useState(members.length > 1 ? members[1]?.user_id : '');
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (fromUserId === toUserId) {
      setError('Payer and payee cannot be the same person');
      return;
    }

    setLoading(true);

    try {
      await settlementsApi.create(groupId, {
        from_user_id: fromUserId,
        to_user_id: toUserId,
        amount_inr: parseFloat(amount),
        note: note || undefined,
      });
      onCreated();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to record settlement');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <HandCoins className="w-6 h-6 text-primary-400" />
            Record Settlement
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X className="w-5 h-5 text-white/50" />
          </button>
        </div>

        <form id="settlement-form" onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Who Paid?</label>
            <select
              value={fromUserId}
              onChange={(e) => setFromUserId(e.target.value)}
              className="input-field bg-surface-900"
              required
            >
              <option value="" disabled>Select payer</option>
              {members.map(m => (
                <option key={m.user_id} value={m.user_id} className="bg-surface-800">
                  {m.user_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Who Received?</label>
            <select
              value={toUserId}
              onChange={(e) => setToUserId(e.target.value)}
              className="input-field bg-surface-900"
              required
            >
              <option value="" disabled>Select payee</option>
              {members.map(m => (
                <option key={m.user_id} value={m.user_id} className="bg-surface-800">
                  {m.user_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Amount (₹ INR)</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="input-field"
              placeholder="0.00"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-white/70 mb-2">Note (Optional)</label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="input-field"
              placeholder="e.g. Bank transfer"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
              {error}
            </div>
          )}
        </form>

        <div className="mt-8 pt-4 border-t border-white/10 flex justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" form="settlement-form" disabled={loading} className="btn-primary min-w-[120px]">
            {loading ? 'Saving...' : 'Record'}
          </button>
        </div>
      </div>
    </div>
  );
}
