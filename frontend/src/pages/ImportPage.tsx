import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { importsApi } from '../api';
import { Upload, AlertTriangle, CheckCircle2, ArrowRight, FileText } from 'lucide-react';

export default function ImportPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [finalizing, setFinalizing] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const res = await importsApi.upload(groupId!, file);
      setSession(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (anomalyId: string, decision: string) => {
    try {
      await importsApi.resolveAnomaly(session.id, anomalyId, decision);
      // Refresh session to get updated status and anomalies
      const res = await importsApi.getSession(session.id);
      setSession(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to resolve anomaly');
    }
  };

  const handleFinalize = async () => {
    setFinalizing(true);
    try {
      await importsApi.finalize(session.id);
      navigate(`/groups/${groupId}`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to finalize import');
      setFinalizing(false);
    }
  };

  if (!session) {
    return (
      <div className="max-w-2xl mx-auto animate-fade-in">
        <h1 className="text-3xl font-bold text-white mb-2">Import Expenses</h1>
        <p className="text-white/40 mb-8">Upload a CSV file to bulk import expenses.</p>

        <div className="glass-card p-12 text-center">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-white/5 border-2 border-dashed border-white/20 
                          flex items-center justify-center mb-6">
            <Upload className="w-8 h-8 text-white/40" />
          </div>
          
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="hidden"
            id="csv-upload"
          />
          
          {file ? (
            <div className="mb-6">
              <p className="text-white font-medium mb-1">{file.name}</p>
              <p className="text-sm text-white/40">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          ) : (
            <div className="mb-6">
              <p className="text-white font-medium mb-1">Select a CSV file</p>
              <p className="text-sm text-white/40">Must include Date, Description, Amount, Paid By</p>
            </div>
          )}

          <div className="flex justify-center gap-4">
            <label htmlFor="csv-upload" className="btn-secondary cursor-pointer">
              {file ? 'Change File' : 'Browse'}
            </label>
            <button 
              onClick={handleUpload} 
              disabled={!file || loading}
              className="btn-primary min-w-[120px]"
            >
              {loading ? 'Uploading...' : 'Upload'}
            </button>
          </div>

          {error && <p className="text-red-400 mt-4 text-sm">{error}</p>}
        </div>
      </div>
    );
  }

  // Session loaded view
  const pendingAnomalies = session.anomalies.filter((a: any) => a.user_decision === 'pending');
  const resolvedAnomalies = session.anomalies.filter((a: any) => a.user_decision !== 'pending');

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Import Review</h1>
          <p className="text-white/40">
            {session.filename} • {session.total_rows} rows parsed
          </p>
        </div>
        <div className="flex items-center gap-3">
          <a
            href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/import/${session.id}/report`}
            download
            target="_blank"
            rel="noreferrer"
            className="btn-secondary flex items-center gap-2"
          >
            <FileText className="w-4 h-4" /> Download Report JSON
          </a>
          {session.status === 'ready' && (
            <button 
              onClick={handleFinalize}
              disabled={finalizing}
              className="btn-success flex items-center gap-2"
            >
              {finalizing ? 'Finalizing...' : 'Finalize Import'} <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {session.status === 'reviewing' && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0" />
          <div>
            <h3 className="text-amber-400 font-semibold text-lg">Action Required</h3>
            <p className="text-amber-400/80 mt-1">
              Found {pendingAnomalies.length} anomalies that need your review before import can continue.
            </p>
          </div>
        </div>
      )}

      {session.status === 'ready' && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-3">
          <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
          <div>
            <h3 className="text-emerald-400 font-semibold text-lg">Ready to Import</h3>
            <p className="text-emerald-400/80 mt-1">
              All anomalies resolved. Click finalize to import the valid rows.
            </p>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-white">Pending Review ({pendingAnomalies.length})</h2>
        {pendingAnomalies.map((anomaly: any) => (
          <div key={anomaly.id} className="glass-card p-6 border-l-4 border-l-amber-500">
            <div className="flex justify-between items-start mb-4">
              <div>
                <span className="badge-warning mb-2 inline-block">{anomaly.anomaly_type.replace(/_/g, ' ')}</span>
                <h3 className="text-lg font-medium text-white">Row {anomaly.row_number}</h3>
                <p className="text-white/60 mt-1">{anomaly.description}</p>
              </div>
            </div>
            
            <div className="bg-white/5 p-3 rounded-lg mb-4 text-sm font-mono text-white/50 overflow-x-auto">
              {JSON.stringify(anomaly.raw_row, null, 2)}
            </div>

            <div className="flex gap-3">
              <button 
                onClick={() => handleResolve(anomaly.id, 'approve_fix')}
                className="px-4 py-2 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 rounded-lg text-sm font-medium transition-colors"
              >
                Approve Fix (Import)
              </button>
              <button 
                onClick={() => handleResolve(anomaly.id, 'approve_delete')}
                className="px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg text-sm font-medium transition-colors"
              >
                Skip Row
              </button>
            </div>
          </div>
        ))}
        {pendingAnomalies.length === 0 && (
          <p className="text-white/40">No pending items.</p>
        )}
      </div>

      {resolvedAnomalies.length > 0 && (
        <div className="space-y-4 pt-8 border-t border-white/10">
          <h2 className="text-xl font-semibold text-white">Resolved ({resolvedAnomalies.length})</h2>
          {resolvedAnomalies.map((anomaly: any) => (
            <div key={anomaly.id} className="glass-card p-4 opacity-60">
              <div className="flex justify-between items-center">
                <div>
                  <span className="text-white font-medium mr-3">Row {anomaly.row_number}</span>
                  <span className="text-white/50 text-sm">{anomaly.anomaly_type.replace(/_/g, ' ')}</span>
                </div>
                <span className={`badge ${
                  anomaly.user_decision === 'approve_fix' ? 'badge-success' : 'badge-danger'
                }`}>
                  {anomaly.user_decision.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
