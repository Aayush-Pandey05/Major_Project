"""
agent.py
========
Visualization Agent: Generates renderable Plotly chart specifications
(data traces and layout configurations) directly from structured analytical results.
STRICTLY NEVER CALLS OPENAI.
Outputs are directly consumable by frontend Plotly.js / react-plotly.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pydantic import BaseModel, Field

class ChartSpecification(BaseModel):
    chart_id: str
    chart_type: str # 'line' | 'bar' | 'scatter' | 'heatmap' | 'histogram'
    title: str
    figure: Dict[str, Any] # Plotly figure dictionary containing 'data' and 'layout'
    description: Optional[str] = None

class VisualizationAgentResult(BaseModel):
    charts: List[ChartSpecification] = Field(default_factory=list)

class VisualizationAgent:
    def create_forecast_chart(
        self,
        forecast_records: List[Dict[str, Any]],
        title: str = "Sales Forecast (Next Horizon Days)"
    ) -> ChartSpecification:
        dates = [r["date"] for r in forecast_records]
        values = [r["predicted_sales"] for r in forecast_records]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='Predicted Sales',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=7, color='#1d4ed8')
        ))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Sales (Units)",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=40, r=40, t=50, b=40)
        )

        return ChartSpecification(
            chart_id="forecast_series_plot",
            chart_type="line",
            title=title,
            figure=json.loads(fig.to_json()),
            description="Interactive time-series forecast plot showing predicted daily sales."
        )

    def create_anomaly_scatter_chart(
        self,
        scored_records: List[Dict[str, Any]],
        threshold: float,
        title: str = "Anomaly Score Distribution & Outliers"
    ) -> ChartSpecification:
        invoices = [r.get("Invoice", r.get("invoice", str(i))) for i, r in enumerate(scored_records)]
        scores = [float(r.get("anomaly_score", 0.0)) for r in scored_records]
        is_anom = [s >= threshold for s in scores]

        colors = ['#ef4444' if a else '#64748b' for a in is_anom]
        sizes = [10 if a else 5 for a in is_anom]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(scores))),
            y=scores,
            mode='markers',
            marker=dict(color=colors, size=sizes, opacity=0.8),
            text=[f"Invoice: {inv}<br>Score: {sc:.3f}" for inv, sc in zip(invoices, scores)],
            hoverinfo='text',
            name='Invoices'
        ))

        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="#dc2626",
            annotation_text=f"Model Threshold ({threshold:.3f})",
            annotation_position="bottom right"
        )

        fig.update_layout(
            title=title,
            xaxis_title="Transaction Index",
            yaxis_title="Anomaly Score (-score_samples)",
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40)
        )

        return ChartSpecification(
            chart_id="anomaly_scatter_plot",
            chart_type="scatter",
            title=title,
            figure=json.loads(fig.to_json()),
            description="Scatter plot showing transaction anomaly scores relative to the decision threshold."
        )

    def create_correlation_heatmap(
        self,
        corr_matrix: Dict[str, Dict[str, float]],
        title: str = "Feature Correlation Matrix"
    ) -> ChartSpecification:
        cols = list(corr_matrix.keys())
        z_vals = [[corr_matrix[r][c] for c in cols] for r in cols]

        fig = go.Figure(data=go.Heatmap(
            z=z_vals,
            x=cols,
            y=cols,
            colorscale='Blues',
            zmin=-1,
            zmax=1,
            text=z_vals,
            texttemplate="%{text:.2f}"
        ))

        fig.update_layout(
            title=title,
            template="plotly_white",
            margin=dict(l=60, r=40, t=50, b=60)
        )

        return ChartSpecification(
            chart_id="correlation_heatmap",
            chart_type="heatmap",
            title=title,
            figure=json.loads(fig.to_json()),
            description="Heatmap visualizing Pearson correlations between numerical attributes."
        )

    def create_bar_chart(
        self,
        categories: List[str],
        values: List[float],
        title: str = "Comparison Overview",
        x_label: str = "Category",
        y_label: str = "Value"
    ) -> ChartSpecification:
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color='#3b82f6'
            )
        ])

        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40)
        )

        return ChartSpecification(
            chart_id="bar_chart",
            chart_type="bar",
            title=title,
            figure=json.loads(fig.to_json()),
            description="Bar chart displaying aggregate comparisons."
        )

    def create_distribution_chart(
        self,
        values: List[float],
        column_name: str,
        title: Optional[str] = None
    ) -> ChartSpecification:
        fig = go.Figure(data=[
            go.Histogram(
                x=values,
                marker_color='#6366f1',
                opacity=0.85,
                nbinsx=25
            )
        ])
        fig.update_layout(
            title=title or f"Distribution of {column_name}",
            xaxis_title=column_name,
            yaxis_title="Frequency",
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        return ChartSpecification(
            chart_id=f"dist_{column_name.lower().replace(' ', '_')}",
            chart_type="histogram",
            title=title or f"Distribution of {column_name}",
            figure=json.loads(fig.to_json()),
            description=f"Histogram visualizing the value distribution of {column_name}."
        )

    def create_metrics_summary_chart(
        self,
        metrics: Dict[str, Any],
        title: str = "Key Numerical Metrics Overview"
    ) -> ChartSpecification:
        numeric_items = {
            k: float(v)
            for k, v in metrics.items()
            if isinstance(v, (int, float)) and not any(ign in k.lower() for ign in ["export", "id", "version", "year", "code"])
        }
        cats = [k.replace("_", " ").title() for k in numeric_items.keys()][:8]
        vals = [numeric_items[k] for k in numeric_items.keys()][:8]
        return self.create_bar_chart(cats, vals, title=title, x_label="Analytical Metric", y_label="Calculated Value")
