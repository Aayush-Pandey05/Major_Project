'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  ArrowRight,
  Loader2,
  CheckCircle2,
  Clock,
  Database,
  FileSpreadsheet,
} from 'lucide-react';
import { useSessionStore } from '../../stores/useSessionStore';
import { useDatasetStore } from '../../stores/useDatasetStore';
import { useDataSourceStore } from '../../stores/useDataSourceStore';
import { useAgentRunStore } from '../../stores/useAgentRunStore';
import { getSessionById } from '../../services/api/chat.api';
import { streamAgentWorkflow } from '../../services/api/streaming-client';
import { ResultView } from '../analytics/ResultView';
import { ProgressEvent, SynthesizedResponse } from '../../services/api/types';

const EXAMPLE_QUERIES = [
  'Forecast sales for the next 14 days for store 1',
  'Identify unusual transactions and anomalies in this dataset',
  'Summarize this dataset and describe numerical distributions',
  'Find correlations between numerical variables',
  'Show monthly sales trend and plot the forecast',
  'Query the database to summarize order metrics',
];

export const ChatInterface: React.FC = () => {
  const [inputQuery, setInputQuery] = useState('');
  const { activeSessionId, messages, setMessages, addMessage } = useSessionStore();
  const { activeDataset } = useDatasetStore();
  const { activeConnection } = useDataSourceStore();
  const {
    isExecuting,
    setIsExecuting,
    progressEvents,
    addProgressEvent,
    latestResponse,
    setLatestResponse,
    resetRun,
  } = useAgentRunStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load active session messages when switched
  useEffect(() => {
    if (activeSessionId) {
      getSessionById(activeSessionId)
        .then((sess) => {
          if (sess.messages) {
            setMessages(sess.messages);
          }
        })
        .catch(console.error);
    }
  }, [activeSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, progressEvents, latestResponse]);

  const handleSubmit = async (queryText?: string) => {
    const query = (queryText || inputQuery).trim();
    if (!query || isExecuting) return;

    setInputQuery('');
    resetRun();
    setIsExecuting(true);

    // Optimistically add user message
    const tempUserMsg = {
      id: `temp_${Date.now()}`,
      sessionId: activeSessionId || 'default',
      role: 'user' as const,
      content: query,
      createdAt: new Date().toISOString(),
    };
    addMessage(tempUserMsg);

    // Stream through centralized streaming client
    await streamAgentWorkflow({
      query,
      sessionId: activeSessionId || undefined,
      datasetId: activeDataset?.id,
      connectionId: activeConnection?.id,
      onProgress: (event: ProgressEvent) => {
        addProgressEvent(event);
      },
      onFinalResponse: (resp: SynthesizedResponse) => {
        setLatestResponse(resp);
        // Add final assistant message
        addMessage({
          id: `resp_${Date.now()}`,
          sessionId: activeSessionId || 'default',
          role: 'assistant',
          content: resp.answer,
          structuredData: resp,
          createdAt: new Date().toISOString(),
        });
        setIsExecuting(false);
      },
      onError: (err: string) => {
        console.error('Workflow execution error:', err);
        addMessage({
          id: `err_${Date.now()}`,
          sessionId: activeSessionId || 'default',
          role: 'assistant',
          content: `Execution encounter: ${err}`,
          createdAt: new Date().toISOString(),
        });
        setIsExecuting(false);
      },
    });
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/40 overflow-hidden">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.length === 0 ? (
          /* Empty / Welcome State */
          <div className="max-w-2xl mx-auto mt-12 text-center space-y-6">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-500/20">
              <Sparkles className="w-7 h-7 text-white" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                Multi-Agent AI Data Analyst
              </h2>
              <p className="text-sm text-slate-400 max-w-lg mx-auto">
                Ask analytical questions in plain English. Specialized agents perform evidence-based
                statistical profiling, Isolation Forest anomaly detection, XGBoost sales forecasting, and
                read-only SQL queries.
              </p>
            </div>

            {/* Quick Context Indicators */}
            <div className="flex items-center justify-center gap-3 text-xs text-slate-400">
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700">
                <FileSpreadsheet className="w-3.5 h-3.5 text-blue-400" />
                {activeDataset ? activeDataset.originalFilename : 'No dataset selected (using reference)'}
              </span>
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700">
                <Database className="w-3.5 h-3.5 text-indigo-400" />
                {activeConnection ? activeConnection.name : 'No external SQL database'}
              </span>
            </div>

            {/* Selectable Example Queries */}
            <div className="text-left space-y-2 pt-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Suggested Analytical Inquiries:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {EXAMPLE_QUERIES.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSubmit(q)}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-blue-600/50 hover:bg-slate-800/60 text-left text-xs sm:text-sm text-slate-300 transition-all group"
                  >
                    <span>{q}</span>
                    <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 shrink-0 ml-2 transition-colors" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Active Chat Message History */
          messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id || idx}
                className={`flex gap-3 max-w-4xl mx-auto ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4 text-blue-400" />
                  </div>
                )}

                <div className={`max-w-3xl space-y-3 ${isUser ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed ${
                      isUser
                        ? 'bg-blue-600 text-white rounded-br-sm shadow-lg shadow-blue-600/10'
                        : 'bg-slate-900/90 border border-slate-800 text-slate-200 rounded-bl-sm shadow-xl'
                    }`}
                  >
                    {isUser ? (
                      <p className="font-medium">{msg.content}</p>
                    ) : msg.structuredData ? (
                      <ResultView response={msg.structuredData} />
                    ) : (
                      <p>{msg.content}</p>
                    )}
                  </div>
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 mt-1">
                    <User className="w-4 h-4 text-slate-300" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Real-time Streaming Agent Execution Progress */}
        {isExecuting && (
          <div className="max-w-3xl mx-auto p-4 rounded-2xl bg-slate-950/90 border border-blue-500/30 shadow-2xl backdrop-blur-xl space-y-3 animate-pulse">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2 text-xs font-bold text-blue-400 uppercase tracking-wider">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Multi-Agent Workflow In Progress</span>
              </div>
              <span className="text-[11px] text-slate-500">Live SSE Stream</span>
            </div>

            <div className="space-y-2">
              {progressEvents.map((ev, i) => (
                <div key={i} className="flex items-start gap-2.5 text-xs text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-white mr-1.5">{ev.agent}:</span>
                    <span className="text-slate-400">{ev.message}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/90 backdrop-blur-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="max-w-4xl mx-auto flex items-center gap-2 rounded-2xl bg-slate-900 border border-slate-800 px-4 py-2 shadow-2xl focus-within:border-blue-500 transition-colors"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isExecuting}
            placeholder={
              activeDataset
                ? `Ask anything about ${activeDataset.originalFilename}...`
                : 'Ask analytical questions (e.g., "Forecast sales for next 14 days", "Detect anomalies")...'
            }
            className="flex-1 bg-transparent border-0 text-sm text-white placeholder-slate-500 focus:outline-none"
          />

          <button
            type="submit"
            disabled={!inputQuery.trim() || isExecuting}
            className="p-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white transition-all shadow-md"
          >
            {isExecuting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>
      </div>
    </div>
  );
};
