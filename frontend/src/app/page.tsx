'use client';

import React, { useState } from 'react';
import { Sidebar } from '../components/dashboard/Sidebar';
import { ChatInterface } from '../components/chat/ChatInterface';
import { DatasetUploader } from '../components/datasets/DatasetUploader';
import { DatabaseModal } from '../components/database-connections/DatabaseModal';
import { ModelEvaluationsView } from '../components/analytics/ModelEvaluationsView';
import { useDatasetStore } from '../stores/useDatasetStore';
import { useDataSourceStore } from '../stores/useDataSourceStore';
import {
  MessageSquare,
  FileSpreadsheet,
  Database,
  BarChart2,
  ShieldCheck,
} from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'dataset' | 'database' | 'evaluations'>('chat');
  const { activeDataset } = useDatasetStore();
  const { activeConnection } = useDataSourceStore();

  return (
    <div className="flex w-screen h-screen bg-slate-950 overflow-hidden">
      {/* Collapsible / Responsive Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-800 bg-slate-950/80 px-6 flex items-center justify-between shrink-0 backdrop-blur-md">
          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 sm:gap-2">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'chat'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Chat & Analysis</span>
            </button>

            <button
              onClick={() => setActiveTab('dataset')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'dataset'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Datasets</span>
            </button>

            <button
              onClick={() => setActiveTab('database')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'database'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>SQL Connections</span>
            </button>

            <button
              onClick={() => setActiveTab('evaluations')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'evaluations'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Model Benchmarks</span>
            </button>
          </div>

          {/* Active Context Indicators */}
          <div className="hidden md:flex items-center gap-3 text-xs">
            {activeDataset && (
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-950/60 border border-blue-800 text-blue-300 font-medium truncate max-w-[200px]">
                <FileSpreadsheet className="w-3 h-3 text-blue-400" />
                <span className="truncate">{activeDataset.originalFilename}</span>
              </span>
            )}

            {activeConnection && (
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-950/60 border border-indigo-800 text-indigo-300 font-medium truncate max-w-[180px]">
                <Database className="w-3 h-3 text-indigo-400" />
                <span className="truncate">{activeConnection.name}</span>
              </span>
            )}

            <span className="flex items-center gap-1 text-emerald-400 bg-emerald-950/40 border border-emerald-900/60 px-2.5 py-1 rounded-full text-[11px] font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Read-Only Enforced</span>
            </span>
          </div>
        </header>

        {/* Dynamic Content Views */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'dataset' && <DatasetUploader />}
          {activeTab === 'database' && <DatabaseModal />}
          {activeTab === 'evaluations' && <ModelEvaluationsView />}
        </div>
      </main>
    </div>
  );
}
