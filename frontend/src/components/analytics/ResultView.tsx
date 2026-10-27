'use client';

import React from 'react';
import {
  FileText,
  TrendingUp,
  AlertTriangle,
  Download,
  Info,
  CheckCircle2,
  Table as TableIcon,
  BarChart3,
} from 'lucide-react';
import { SynthesizedResponse } from '../../services/api/types';
import { PlotlyChart } from '../visualizations/PlotlyChart';
import { getResultDownloadUrl } from '../../services/api/results.api';

interface ResultViewProps {
  response: SynthesizedResponse;
}

export const ResultView: React.FC<ResultViewProps> = ({ response }) => {
  return (
    <div className="space-y-6 text-slate-200">
      {/* 1. Answer & Summary Card */}
      <div className="rounded-2xl bg-gradient-to-br from-slate-900/90 to-slate-950/90 border border-slate-800 p-6 shadow-2xl backdrop-blur-xl">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-white tracking-tight">Executive Summary</h3>
          </div>
          {response.metrics?.export_file_url && (
            <a
              href={getResultDownloadUrl(response.metrics.export_file_url.split('/download/')[1])}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white transition-all shadow-md hover:shadow-blue-500/20"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Full Results</span>
            </a>
          )}
        </div>
        <p className="text-slate-300 leading-relaxed font-normal mb-4 text-sm sm:text-base">
          {response.answer}
        </p>
        {response.summary && (
          <div className="p-3.5 rounded-xl bg-blue-950/30 border border-blue-900/40 text-blue-200 text-xs sm:text-sm">
            <span className="font-semibold text-blue-400 mr-2">Key Takeaway:</span>
            {response.summary}
          </div>
        )}
      </div>

      {/* 2. Key Metrics Grid */}
      {response.metrics && Object.keys(response.metrics).length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
          {Object.entries(response.metrics)
            .filter(([k]) => !['export_file_url'].includes(k))
            .slice(0, 8)
            .map(([key, val]) => (
              <div
                key={key}
                className="rounded-xl bg-slate-900/80 border border-slate-800 p-3.5 shadow-lg flex flex-col justify-between"
              >
                <span className="text-xs uppercase tracking-wider text-slate-400 font-medium truncate">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="text-lg sm:text-xl font-bold text-white mt-1">
                  {typeof val === 'number' ? (val % 1 !== 0 ? val.toFixed(2) : val.toLocaleString()) : String(val)}
                </span>
              </div>
            ))}
        </div>
      )}

      {/* 3. Key Findings Bullets */}
      {response.key_findings && response.key_findings.length > 0 && (
        <div className="rounded-xl bg-slate-900/60 border border-slate-800/80 p-5 shadow-lg">
          <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Key Insights & Supporting Findings
          </h4>
          <ul className="space-y-2">
            {response.key_findings.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-sm text-slate-300">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 shrink-0"></span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. Interactive Plotly Charts */}
      {response.charts && response.charts.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <span>Interactive Data Visualizations</span>
          </div>
          <div className="grid grid-cols-1 gap-6">
            {response.charts.map((chart, idx) => (
              <PlotlyChart
                key={chart.chart_id || idx}
                figure={chart.figure}
                title={chart.title}
              />
            ))}
          </div>
        </div>
      )}

      {/* 5. Tabular Data Presentation */}
      {response.tables && response.tables.length > 0 && (
        <div className="space-y-4">
          {response.tables.map((table, tIdx) => {
            const rows = table.rows || [];
            if (rows.length === 0) return null;
            const columns = table.columns || Object.keys(rows[0]);

            return (
              <div
                key={tIdx}
                className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 shadow-xl overflow-hidden"
              >
                <div className="flex items-center gap-2 mb-3">
                  <TableIcon className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-sm font-semibold text-slate-200">{table.title}</h4>
                </div>
                <div className="overflow-x-auto max-h-72 border border-slate-800 rounded-lg">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/80 sticky top-0 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                      <tr>
                        {columns.map((col) => (
                          <th key={col} className="px-3.5 py-2.5 whitespace-nowrap">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                      {rows.map((r, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-800/40 transition-colors">
                          {columns.map((c) => (
                            <td key={c} className="px-3.5 py-2 whitespace-nowrap">
                              {r[c] !== null && r[c] !== undefined ? String(r[c]) : '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 6. Evidence & Limitations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {response.evidence && response.evidence.length > 0 && (
          <div className="rounded-xl bg-slate-950/40 border border-slate-800/70 p-4">
            <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-blue-400" />
              Calculations & Methodology Evidence
            </h5>
            <ul className="space-y-1.5 text-xs text-slate-400">
              {response.evidence.map((ev, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-slate-600">•</span>
                  <span>{ev}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {response.limitations && response.limitations.length > 0 && (
          <div className="rounded-xl bg-slate-950/40 border border-slate-800/70 p-4">
            <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Model Boundaries & Limitations
            </h5>
            <ul className="space-y-1.5 text-xs text-slate-400">
              {response.limitations.map((lim, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-slate-600">•</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* 7. Warnings */}
      {response.warnings && response.warnings.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-900/40 text-amber-300 text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="space-y-1">
            {response.warnings.map((w, idx) => (
              <p key={idx}>{w}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
