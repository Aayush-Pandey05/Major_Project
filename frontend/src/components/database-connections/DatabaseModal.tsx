'use client';

import React, { useState, useEffect } from 'react';
import {
  Database,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Table as TableIcon,
  ShieldCheck,
  Plus,
} from 'lucide-react';
import { useDataSourceStore } from '../../stores/useDataSourceStore';
import {
  testConnection,
  getSchema,
  saveConnection,
  getConnections,
} from '../../services/api/database-connections.api';
import { TableSchema } from '../../services/api/types';

export const DatabaseModal: React.FC = () => {
  const { activeConnection, setActiveConnection, connections, setConnections } = useDataSourceStore();

  const [name, setName] = useState('');
  const [dbType, setDbType] = useState('postgresql');
  const [connectionUrl, setConnectionUrl] = useState('');
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [schema, setSchema] = useState<{ tables_count: number; tables: TableSchema[] } | null>(null);
  const [isLoadingSchema, setIsLoadingSchema] = useState(false);

  const fetchConnections = async () => {
    try {
      const list = await getConnections();
      setConnections(list);
    } catch (err) {
      console.error('Failed to load connections:', err);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  const handleTest = async () => {
    if (!connectionUrl.trim()) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await testConnection(connectionUrl);
      setTestResult(res);
      if (res.success) {
        setIsLoadingSchema(true);
        const s = await getSchema(connectionUrl);
        setSchema(s);
        setIsLoadingSchema(false);
      }
    } catch (err: any) {
      setTestResult({ success: false, message: err.message || 'Connection test failed.' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!connectionUrl.trim() || !name.trim()) return;

    try {
      const saved = await saveConnection({
        name,
        type: dbType,
        connectionUrl,
      });
      await fetchConnections();
      setActiveConnection(saved);
      setName('');
      setConnectionUrl('');
      setTestResult(null);
      setSchema(null);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    }
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6 text-slate-200">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          External SQL Database Connections (Read-Only)
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Connect your PostgreSQL, MySQL, or SQLite databases. Analytical queries are strictly enforced as read-only.
        </p>
      </div>

      {/* Security Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3 text-xs text-slate-300">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
        <div>
          <span className="font-semibold text-white">Strict Read-Only Guarantee:</span> All mutation statements
          (INSERT, UPDATE, DELETE, DROP, ALTER) are automatically rejected. Database passwords are never exposed
          client-side or sent to OpenAI.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Plus className="w-4 h-4 text-blue-400" />
            Connect New Database
          </h3>

          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Connection Label</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Production Analytics Read-Only"
                required
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Database Dialect</label>
              <select
                value={dbType}
                onChange={(e) => setDbType(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="postgresql">PostgreSQL</option>
                <option value="mysql">MySQL</option>
                <option value="sqlite">SQLite (Local file / read-only)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">
                Connection URI (Read-Only Credentials Recommended)
              </label>
              <input
                type="text"
                value={connectionUrl}
                onChange={(e) => setConnectionUrl(e.target.value)}
                placeholder="postgresql://user:password@hostname:5432/dbname"
                required
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 font-mono"
              />
              <span className="text-[11px] text-slate-500 block mt-1">
                Tip: For SQLite, use <code className="text-slate-400">sqlite:///path/to/data.db</code>
              </span>
            </div>

            {testResult && (
              <div
                className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
                  testResult.success
                    ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                    : 'bg-rose-950/40 border-rose-800 text-rose-300'
                }`}
              >
                {testResult.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                <span>{testResult.message}</span>
              </div>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={handleTest}
                disabled={isTesting || !connectionUrl.trim()}
                className="flex-1 py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-xs font-semibold text-slate-200 transition-all flex items-center justify-center gap-2"
              >
                {isTesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                <span>Test Connection</span>
              </button>

              <button
                type="submit"
                disabled={!name.trim() || !connectionUrl.trim()}
                className="flex-1 py-2 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white transition-all shadow-md"
              >
                Save Connection
              </button>
            </div>
          </form>
        </div>

        {/* Existing Connections & Schema Preview */}
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400" />
              Saved Databases ({connections.length})
            </h3>

            {connections.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No saved connections yet.</p>
            ) : (
              <div className="space-y-2">
                {connections.map((c) => {
                  const isActive = activeConnection?.id === c.id;
                  return (
                    <div
                      key={c.id}
                      onClick={() => setActiveConnection(c)}
                      className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between text-xs ${
                        isActive
                          ? 'bg-indigo-950/50 border-indigo-500 text-white shadow-md'
                          : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:bg-slate-900'
                      }`}
                    >
                      <div>
                        <span className="font-semibold block">{c.name}</span>
                        <code className="text-[11px] text-slate-500 font-mono">{c.sanitizedUrl}</code>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${isActive ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-800 text-slate-400'}`}>
                        {isActive ? 'Active Source' : 'Select'}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Introspected Schema */}
          {schema && schema.tables && schema.tables.length > 0 && (
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <TableIcon className="w-4 h-4 text-blue-400" />
                  Introspected Tables ({schema.tables.length})
                </h4>
                <span className="text-[11px] text-emerald-400 font-mono">Read-Only OK</span>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {schema.tables.map((t) => (
                  <div key={t.table_name} className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                    <span className="font-semibold text-white">{t.table_name}</span>
                    <div className="flex flex-wrap gap-1">
                      {t.columns.slice(0, 6).map((c) => (
                        <span key={c.name} className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 text-[10px] font-mono">
                          {c.name}: <span className="text-blue-400">{c.type}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
