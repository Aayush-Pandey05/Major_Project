"""
inference.py
============
Inference interface for retail transaction anomaly detection.
Loads the pre-trained Isolation Forest model from app/models/artifacts/
and scores batches of transactions with counterfactual feature explanations.
Also provides a generic tabular anomaly detector for non-retail schemas.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.core.config import settings
from app.core.exceptions import ModelInferenceError, DataValidationError
from app.models.anomaly_detection.feature_engineering import (
    engineer_features, read_transactions_csv, DISCRETE_FEATURES, FeatureResult
)

DEFAULT_RETAIL_ARTIFACT = settings.MODEL_ARTIFACTS_DIR / "isolation_forest_retail_model.joblib"

class RetailAnomalyDetector:
    def __init__(self, artifact_path: Optional[Union[str, Path]] = None):
        path = Path(artifact_path) if artifact_path else DEFAULT_RETAIL_ARTIFACT
        if not path.exists():
            raise ModelInferenceError(f"Isolation Forest model artifact not found at: {path}")
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.artifact = joblib.load(path)
        except Exception as e:
            raise ModelInferenceError(f"Failed to load Isolation Forest artifact: {e}") from e

        self.pipeline = self.artifact["pipeline"]
        self.feature_names = list(self.artifact["feature_names"])
        self.offset = float(self.artifact["offset"])
        self.contamination = float(self.artifact.get("contamination", 0.01))
        self.reference_stats = self.artifact["reference_stats"]
        self.explanation_config = self.artifact.get("explanation_config", {
            "tail_share": 0.01,
            "rare_discrete_share": 0.005,
            "min_contribution_to_report": 0.01,
            "max_reported_features": 4,
        })
        self.training_scores_sorted = np.asarray(self.artifact["training_score_sorted"])

    def score_features(self, X: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in self.feature_names if c not in X.columns]
        if missing:
            raise DataValidationError(f"Missing required features for model: {missing}")
        
        Xf = X[self.feature_names].copy()
        for c in self.feature_names:
            Xf[c] = pd.to_numeric(Xf[c], errors="coerce").fillna(0.0)

        raw_scores = self.pipeline.score_samples(Xf)
        preds = self.pipeline.predict(Xf)
        dec_func = raw_scores - self.offset
        anomaly_scores = -raw_scores

        pct = 100.0 * np.searchsorted(self.training_scores_sorted, anomaly_scores, side="right") / len(self.training_scores_sorted)

        out = pd.DataFrame({
            "prediction": preds.astype(int),
            "is_anomaly": preds == -1,
            "anomaly_score": anomaly_scores,
            "decision_function": dec_func,
            "score_percentile_vs_training": pct,
        }, index=X.index)
        out["anomaly_rank"] = out["anomaly_score"].rank(ascending=False, method="first").astype(int)
        return out

    def _unusual_features(self, row: pd.Series, contrib: Dict[str, float]) -> List[Dict[str, Any]]:
        tail = self.explanation_config["tail_share"]
        out = []
        for f in self.feature_names:
            st = self.reference_stats["features"].get(f)
            if not st:
                continue
            x = float(row[f])
            rec: Dict[str, Any] = {
                "feature": f,
                "value": x,
                "score_contribution": float(contrib.get(f, 0.0)),
                "training_median": st["median"],
            }
            if st["type"] == "continuous":
                ref_sorted = st["sorted_values"]
                n = len(ref_sorted)
                le = np.searchsorted(ref_sorted, x, side="right") / n
                ge = 1.0 - np.searchsorted(ref_sorted, x, side="left") / n
                rec["percentile_of_training"] = round(100.0 * le, 2)
                rec["direction"] = "high" if ge <= tail else "low" if le <= tail else "normal"
                rec["above_training_max"] = bool(x > ref_sorted[-1])
            else:
                share = st["frequencies"].get(str(int(x)), 0.0)
                rec["percentile_of_training"] = round(share * 100.0, 2)
                rec["direction"] = "rare" if share <= self.explanation_config["rare_discrete_share"] else "normal"
                rec["above_training_max"] = False
            out.append(rec)
        return out

    def predict(
        self,
        data: Union[str, Path, pd.DataFrame],
        explain: str = "flagged",
        top_n: int = 50
    ) -> Dict[str, Any]:
        """Runs the complete retail transaction anomaly detection pipeline."""
        if isinstance(data, (str, Path)):
            raw_df = read_transactions_csv(data)
        elif isinstance(data, pd.DataFrame):
            raw_df = data.copy()
        else:
            raise DataValidationError(f"Invalid data type: {type(data)}")

        feat_res = engineer_features(raw_df)
        invoices = feat_res.invoices
        if invoices.empty:
            raise DataValidationError("No valid purchase invoices found to score in the dataset.")

        scored = self.score_features(invoices[self.feature_names])
        merged = pd.concat([invoices.reset_index(drop=True), scored.reset_index(drop=True)], axis=1)

        flagged_df = merged[merged["is_anomaly"]].sort_values("anomaly_score", ascending=False)
        total_invoices = len(merged)
        flagged_count = len(flagged_df)
        pct_flagged = (flagged_count / total_invoices * 100.0) if total_invoices > 0 else 0.0

        # Build explainable findings
        findings: List[Dict[str, Any]] = []
        explain_rows = flagged_df.head(top_n) if explain == "flagged" else merged.head(top_n)

        for _, row in explain_rows.iterrows():
            # Counterfactual feature contribution: replace feature with median
            contrib: Dict[str, float] = {}
            row_base_score = float(row["anomaly_score"])
            for f in self.feature_names:
                row_copy = row[self.feature_names].copy()
                med = self.reference_stats["features"][f]["median"]
                row_copy[f] = med
                single_df = pd.DataFrame([row_copy], columns=self.feature_names)
                new_score = -float(self.pipeline.score_samples(single_df)[0])
                contrib[f] = round(row_base_score - new_score, 4)

            unusual = self._unusual_features(row, contrib)
            top_contributors = sorted(unusual, key=lambda u: abs(u["score_contribution"]), reverse=True)[:3]
            top_feats_desc = ", ".join([f"{u['feature']} ({u['direction']})" for u in top_contributors if u['direction'] != "normal"])

            explanation = (
                f"Invoice {row['Invoice']} scored {row['anomaly_score']:.3f} "
                f"({row['score_percentile_vs_training']:.1f}th percentile vs training). "
                f"{'Key anomalies: ' + top_feats_desc if top_feats_desc else 'Combined multivariate pattern deviations.'}"
            )

            findings.append({
                "invoice": str(row["Invoice"]),
                "is_anomaly": bool(row["is_anomaly"]),
                "prediction": int(row["prediction"]),
                "anomaly_score": round(float(row["anomaly_score"]), 4),
                "decision_function": round(float(row["decision_function"]), 4),
                "anomaly_rank": int(row["anomaly_rank"]),
                "score_percentile_vs_training": round(float(row["score_percentile_vs_training"]), 2),
                "invoice_datetime": str(row.get("invoice_datetime", "")),
                "customer_id": str(row.get("customer_id", "")) if pd.notna(row.get("customer_id")) else None,
                "country": str(row.get("country", "")) if pd.notna(row.get("country")) else None,
                "features": {f: round(float(row[f]), 2) for f in self.feature_names},
                "unusual_features": unusual,
                "all_feature_contributions": contrib,
                "explanation": explanation,
            })

        score_dist = {
            "min": round(float(merged["anomaly_score"].min()), 4),
            "p25": round(float(merged["anomaly_score"].quantile(0.25)), 4),
            "median": round(float(merged["anomaly_score"].median()), 4),
            "p75": round(float(merged["anomaly_score"].quantile(0.75)), 4),
            "p95": round(float(merged["anomaly_score"].quantile(0.95)), 4),
            "p99": round(float(merged["anomaly_score"].quantile(0.99)), 4),
            "max": round(float(merged["anomaly_score"].max()), 4),
        }

        flagged_summary = flagged_df[[
            "Invoice", "total_invoice_value", "total_quantity", "unique_product_count",
            "anomaly_score", "anomaly_rank"
        ]].head(top_n).to_dict(orient="records")

        return {
            "model_name": "isolation_forest_retail_model",
            "model_version": "1.0.0",
            "total_records_analyzed": total_invoices,
            "anomalies_flagged_count": flagged_count,
            "anomaly_percentage": round(pct_flagged, 2),
            "threshold_score": round(float(-self.offset), 4),
            "flagged_records": flagged_summary,
            "findings": findings,
            "score_distribution": score_dist,
            "full_scored_dataframe": merged,
            "warning": None,
        }


class GenericTabularAnomalyDetector:
    """Unsupervised Isolation Forest detector for arbitrary tabular datasets."""
    def __init__(self, contamination: float = 0.02, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state

    def fit_predict(self, df: pd.DataFrame, top_n: int = 50) -> Dict[str, Any]:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not num_cols:
            raise DataValidationError("No numeric columns available in dataset to perform anomaly detection.")

        clean_df = df[num_cols].fillna(df[num_cols].median()).copy()
        model = IsolationForest(
            n_estimators=150,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1
        )
        model.fit(clean_df)
        preds = model.predict(clean_df)
        raw_scores = model.score_samples(clean_df)
        anomaly_scores = -raw_scores

        res_df = df.copy()
        res_df["is_anomaly"] = preds == -1
        res_df["anomaly_score"] = anomaly_scores
        res_df["anomaly_rank"] = res_df["anomaly_score"].rank(ascending=False, method="first").astype(int)

        flagged = res_df[res_df["is_anomaly"]].sort_values("anomaly_score", ascending=False)
        total = len(res_df)
        flagged_count = len(flagged)

        score_dist = {
            "min": round(float(res_df["anomaly_score"].min()), 4),
            "median": round(float(res_df["anomaly_score"].median()), 4),
            "p95": round(float(res_df["anomaly_score"].quantile(0.95)), 4),
            "max": round(float(res_df["anomaly_score"].max()), 4),
        }

        findings = []
        for idx, row in flagged.head(top_n).iterrows():
            findings.append({
                "invoice": str(idx),
                "is_anomaly": True,
                "prediction": -1,
                "anomaly_score": round(float(row["anomaly_score"]), 4),
                "decision_function": round(float(row["anomaly_score"] - float(-model.offset_)), 4),
                "anomaly_rank": int(row["anomaly_rank"]),
                "score_percentile_vs_training": 99.0,
                "features": {c: round(float(row[c]), 2) for c in num_cols[:8]},
                "unusual_features": [],
                "all_feature_contributions": {},
                "explanation": f"Record {idx} flagged with anomaly score {row['anomaly_score']:.3f} across numerical features {num_cols[:4]}."
            })

        return {
            "model_name": "generic_tabular_isolation_forest",
            "model_version": "1.0.0",
            "total_records_analyzed": total,
            "anomalies_flagged_count": flagged_count,
            "anomaly_percentage": round((flagged_count / total * 100.0) if total > 0 else 0.0, 2),
            "threshold_score": round(float(-model.offset_), 4),
            "flagged_records": flagged.head(top_n).to_dict(orient="records"),
            "findings": findings,
            "score_distribution": score_dist,
            "full_scored_dataframe": res_df,
            "warning": "Generic tabular unsupervised detector fitted on numeric columns.",
        }
