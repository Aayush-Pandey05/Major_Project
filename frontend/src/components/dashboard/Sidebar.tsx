'use client';

import React, { useEffect, useState } from 'react';
import {
  MessageSquarePlus,
  MessageSquare,
  Database,
  FileSpreadsheet,
  Activity,
  Trash2,
  Cpu,
  BarChart2,
  CheckCircle,
  XCircle,
  HelpCircle,
} from 'lucide-react';
import { useSessionStore } from '../../stores/useSessionStore';
import { useDatasetStore } from '../../stores/useDatasetStore';
import { useDataSourceStore } from '../../stores/useDataSourceStore';
import { getRecentSessions, deleteSession, createSession } from '../../services/api/chat.api';
import { checkSystemHealth } from '../../services/api/health.api';
import { SystemHealth } from '../../services/api/types';

interface SidebarProps {
  activeTab: 'chat' | 'dataset' | 'database' | 'evaluations';
  setActiveTab: (tab: 'chat' | 'dataset' | 'database' | 'evaluations') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const { activeSessionId, sessions, setSessions, setActiveSessionId, resetSession } = useSessionStore();
  const { activeDataset } = useDatasetStore();
  const { activeConnection } = useDataSourceStore();

  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  const fetchSessions = async () => {
    try {
      const data = await getRecentSessions();
      setSessions(data);
      if (!activeSessionId && data.length > 0) {
        setActiveSessionId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    }
  };

  const fetchHealth = async () => {
    try {
      const h = await checkSystemHealth();
      setHealth(h);
    } catch {
      // offline
    }
  };

  useEffect(() => {
    fetchSessions();
    fetchHealth();
    const interval = setInterval(fetchHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  const handleNewChat = async () => {
    try {
      const newSession = await createSession('default_session', 'New Analytical Query');
      setActiveSessionId(newSession.id);
      await fetchSessions();
      setActiveTab('chat');
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('Delete this conversation?')) {
      setIsDeleting(id);
      try {
        await deleteSession(id);
        if (activeSessionId === id) {
          resetSession();
        }
        await fetchSessions();
      } catch (err) {
        console.error('Failed to delete session:', err);
      } finally {
        setIsDeleting(null);
      }
    }
  };

  return (
    <aside className="w-72 sm:w-80 h-screen bg-slate-950 border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
      {/* Top Section */}
      <div className="flex flex-col h-full overflow-hidden">
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Cpu className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-tight flex items-center gap-1.5">
                Multi-Agent AI
              </h1>
              <span className="text-[10px] text-blue-400 font-medium">Data Analyst Platform</span>
            </div>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            v1.0
          </span>
        </div>

        {/* Action Controls & Navigation Tabs */}
        <div className="p-3 space-y-2 border-b border-slate-800/80">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs sm:text-sm shadow-lg shadow-blue-600/20 transition-all hover:scale-[1.01]"
          >
            <MessageSquarePlus className="w-4 h-4" />
            <span>New Chat Analysis</span>
          </button>

          <div className="grid grid-cols-2 gap-1.5 pt-1">
            <button
              onClick={() => setActiveTab('dataset')}
              className={`flex items-center gap-2 p-2 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'dataset'
                  ? 'bg-blue-950/60 text-blue-400 border border-blue-800'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">Datasets</span>
            </button>

            <button
              onClick={() => setActiveTab('database')}
              className={`flex items-center gap-2 p-2 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'database'
                  ? 'bg-blue-950/60 text-blue-400 border border-blue-800'
                  : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <Database className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">SQL Databases</span>
            </button>
          </div>

          <button
            onClick={() => setActiveTab('evaluations')}
            className={`w-full flex items-center gap-2 p-2 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'evaluations'
                ? 'bg-blue-950/60 text-blue-400 border border-blue-800'
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5 shrink-0 text-emerald-400" />
            <span>Model Benchmark Reports</span>
          </button>
        </div>

        {/* 10 Most Recent Conversations */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
          <div className="flex items-center justify-between px-2 mb-2">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Recent Conversations (10 Max)
            </span>
            <span className="text-[10px] text-slate-500 font-mono">{sessions.length}/10</span>
          </div>

          {sessions.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500 italic">
              No recent conversations yet. Start a new analysis above!
            </div>
          ) : (
            sessions.map((sess) => {
              const isActive = activeSessionId === sess.id && activeTab === 'chat';
              return (
                <div
                  key={sess.id}
                  onClick={() => {
                    setActiveSessionId(sess.id);
                    setActiveTab('chat');
                  }}
                  className={`group relative flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all text-xs ${
                    isActive
                      ? 'bg-slate-800/90 text-white font-medium border border-slate-700 shadow-md'
                      : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2 overflow-hidden pr-2">
                    <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                    <span className="truncate">{sess.title || 'Untitled Session'}</span>
                  </div>

                  <button
                    onClick={(e) => handleDeleteSession(e, sess.id)}
                    disabled={isDeleting === sess.id}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
                    title="Delete conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Bottom Status Section */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/80 space-y-2">
        {/* Active Context Badges */}
        {(activeDataset || activeConnection) && (
          <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-[11px] space-y-1">
            <span className="text-slate-400 font-semibold block">Active Source:</span>
            {activeDataset && (
              <div className="flex items-center gap-1.5 text-blue-400 truncate">
                <FileSpreadsheet className="w-3 h-3 shrink-0" />
                <span className="truncate">{activeDataset.originalFilename}</span>
              </div>
            )}
            {activeConnection && (
              <div className="flex items-center gap-1.5 text-indigo-400 truncate">
                <Database className="w-3 h-3 shrink-0" />
                <span className="truncate">{activeConnection.name}</span>
              </div>
            )}
          </div>
        )}

        {/* Backend Health Pill */}
        <div className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs space-y-1.5">
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
            <span className="flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-blue-400" />
              System Status
            </span>
            <span className="text-[10px] text-slate-500">Live</span>
          </div>

          <div className="grid grid-cols-2 gap-1 text-[11px]">
            <div className="flex items-center gap-1 text-slate-400">
              {health?.status === 'healthy' ? (
                <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
              ) : (
                <XCircle className="w-3 h-3 text-amber-400 shrink-0" />
              )}
              <span className="truncate">Backend 1</span>
            </div>

            <div className="flex items-center gap-1 text-slate-400">
              {health?.backend2?.status === 'healthy' ? (
                <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
              ) : (
                <HelpCircle className="w-3 h-3 text-slate-500 shrink-0" />
              )}
              <span className="truncate">FastAPI ML</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
