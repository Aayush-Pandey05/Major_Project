'use client';

import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle,
  Database,
  Calendar,
  Target,
  Layers,
  Hash,
  Loader2,
  Table as TableIcon,
} from 'lucide-react';
import { useDatasetStore } from '../../stores/useDatasetStore';
import { uploadDataset, getDatasets } from '../../services/api/datasets.api';
import { Dataset } from '../../services/api/types';

export const DatasetUploader: React.FC = () => {
  const { activeDataset, setActiveDataset, datasets, setDatasets } = useDatasetStore();
  const [isUploading, setIsUploading] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  const fetchList = async () => {
    try {
      const list = await getDatasets();
      setDatasets(list);
      if (list.length > 0 && !selectedDataset) {
        setSelectedDataset(list[0]);
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
    }
  };

  useEffect(() => {
    fetchList();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const newDataset = await uploadDataset(file);
      await fetchList();
      setSelectedDataset(newDataset);
      setActiveDataset(newDataset);
    } catch (err: any) {
      alert(`Upload failed: ${err.message || 'Please check file format.'}`);
    } finally {
      setIsUploading(false);
    }
  };

  const current = selectedDataset || activeDataset || (datasets.length > 0 ? datasets[0] : null);
  const profile = current?.metadataJson;

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6 text-slate-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-blue-400" />
            Dataset Management & Automated Profiling
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload CSV/Excel datasets for analysis. Source files remain strictly immutable and read-only.
          </p>
        </div>

        {/* Upload Button */}
        <label className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold cursor-pointer shadow-lg shadow-blue-500/20 transition-all hover:scale-[1.02]">
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Profiling Dataset...</span>
            </>
          ) : (
            <>
              <UploadCloud className="w-4 h-4" />
              <span>Upload CSV / Excel</span>
            </>
          )}
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.parquet"
            onChange={handleFileUpload}
            disabled={isUploading}
            className="hidden"
          />
        </label>
      </div>

      {/* Dataset Selection Tabs */}
      {datasets.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800/60">
          {datasets.map((d) => {
            const isSelected = current?.id === d.id;
            const isActive = activeDataset?.id === d.id;
            return (
              <div
                key={d.id}
                onClick={() => setSelectedDataset(d)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs cursor-pointer transition-all border shrink-0 ${
                  isSelected
                    ? 'bg-slate-800 text-white border-blue-500 shadow-md'
                    : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-medium max-w-[140px] truncate">{d.originalFilename}</span>
                {isActive && (
                  <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[10px] font-bold">
                    Active
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Dataset Profile Details */}
      {current && profile ? (
        <div className="space-y-6">
          {/* Metadata Cards */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800 gap-4">
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white">{current.originalFilename}</h3>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Hash className="w-3.5 h-3.5 text-slate-500" />
                  SHA-256: <code className="text-slate-300 font-mono text-[11px]">{current.sha256Checksum.slice(0, 16)}...</code>
                </span>
                <span>•</span>
                <span>{profile.row_count.toLocaleString()} rows</span>
                <span>•</span>
                <span>{profile.column_count} columns</span>
                <span>•</span>
                <span>{profile.duplicate_row_count} duplicates</span>
              </div>
            </div>

            <button
              onClick={() => setActiveDataset(current)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeDataset?.id === current.id
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-md'
              }`}
            >
              {activeDataset?.id === current.id ? '✓ Active Analysis Dataset' : 'Set as Active Dataset'}
            </button>
          </div>

          {/* Quick Signal Detection (Dates & Target candidates) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                <Calendar className="w-3.5 h-3.5 text-blue-400" />
                Detected Temporal / Date Columns
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.identified_date_columns?.length > 0 ? (
                  profile.identified_date_columns.map((c) => (
                    <span key={c} className="px-2.5 py-1 rounded-lg bg-blue-950/60 border border-blue-800 text-blue-300 text-xs font-mono">
                      {c}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500 italic">No explicit date columns identified</span>
                )}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
                <Target className="w-3.5 h-3.5 text-emerald-400" />
                Candidate Target Variables
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.candidate_target_columns?.length > 0 ? (
                  profile.candidate_target_columns.map((c) => (
                    <span key={c} className="px-2.5 py-1 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs font-mono">
                      {c}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500 italic">No obvious sales/target metrics identified</span>
                )}
              </div>
            </div>
          </div>

          {/* Column Breakdown Table */}
          <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 shadow-xl overflow-hidden space-y-3">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Column Attributes & Missingness Breakdown
            </h4>

            <div className="overflow-x-auto border border-slate-800 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-3.5 py-2.5">Column</th>
                    <th className="px-3.5 py-2.5">Data Type</th>
                    <th className="px-3.5 py-2.5">Missing</th>
                    <th className="px-3.5 py-2.5">Distinct</th>
                    <th className="px-3.5 py-2.5">Sample Values</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono text-slate-300">
                  {profile.columns.map((col) => (
                    <tr key={col.column_name} className="hover:bg-slate-800/40">
                      <td className="px-3.5 py-2 font-semibold text-white">{col.column_name}</td>
                      <td className="px-3.5 py-2 text-blue-400">{col.data_type}</td>
                      <td className="px-3.5 py-2">
                        {col.missing_count > 0 ? (
                          <span className="text-amber-400 font-bold">{col.missing_percentage}%</span>
                        ) : (
                          <span className="text-slate-500">0%</span>
                        )}
                      </td>
                      <td className="px-3.5 py-2">{col.unique_count.toLocaleString()}</td>
                      <td className="px-3.5 py-2 text-slate-400 truncate max-w-xs">
                        {col.sample_values?.filter(Boolean).join(', ') || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Preview Rows Table */}
          {profile.preview_rows?.length > 0 && (
            <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 shadow-xl overflow-hidden space-y-3">
              <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                <TableIcon className="w-4 h-4 text-blue-400" />
                Raw Data Preview (First 10 Rows)
              </h4>

              <div className="overflow-x-auto border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                    <tr>
                      {Object.keys(profile.preview_rows[0]).map((h) => (
                        <th key={h} className="px-3.5 py-2.5 whitespace-nowrap">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono text-slate-300">
                    {profile.preview_rows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-800/40">
                        {Object.keys(profile.preview_rows[0]).map((h) => (
                          <td key={h} className="px-3.5 py-2 whitespace-nowrap">
                            {row[h] !== null && row[h] !== undefined ? String(row[h]) : '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-12 text-center border-2 border-dashed border-slate-800 rounded-2xl space-y-3">
          <FileSpreadsheet className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">No Dataset Uploaded Yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Upload your CSV or Excel files above to inspect schema metadata, statistical distributions, and run
            automated multi-agent analysis.
          </p>
        </div>
      )}
    </div>
  );
};
