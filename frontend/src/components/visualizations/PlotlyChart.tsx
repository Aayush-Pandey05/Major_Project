'use client';

import React from 'react';
import dynamic from 'next/dynamic';

// Dynamically import Plotly with SSR disabled to prevent server-side DOM errors
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => (
    <div className="h-80 w-full flex items-center justify-center bg-slate-900/40 rounded-xl border border-slate-800 text-slate-400">
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <span>Rendering interactive chart...</span>
      </div>
    </div>
  ),
});

interface PlotlyChartProps {
  figure: {
    data: any[];
    layout: Record<string, any>;
  };
  title?: string;
  className?: string;
}

export const PlotlyChart: React.FC<PlotlyChartProps> = ({ figure, title, className = '' }) => {
  if (!figure || !figure.data) {
    return null;
  }

  const enhancedLayout = {
    autosize: true,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: {
      color: '#cbd5e1', // Slate-300
      family: 'Inter, system-ui, sans-serif',
      size: 12,
    },
    margin: { t: 40, r: 20, l: 50, b: 40 },
    xaxis: {
      gridcolor: '#334155', // Slate-700
      zerolinecolor: '#475569',
      ...figure.layout?.xaxis,
    },
    yaxis: {
      gridcolor: '#334155',
      zerolinecolor: '#475569',
      ...figure.layout?.yaxis,
    },
    ...figure.layout,
  };

  return (
    <div className={`w-full overflow-hidden rounded-xl bg-slate-900/60 border border-slate-800/80 p-4 shadow-xl backdrop-blur-md ${className}`}>
      {title && <h4 className="text-sm font-semibold text-slate-200 mb-2">{title}</h4>}
      <div className="w-full h-80">
        <Plot
          data={figure.data}
          layout={enhancedLayout}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
};
