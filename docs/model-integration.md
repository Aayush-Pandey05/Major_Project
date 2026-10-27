# Model Integration & Artifact Verification Guide

## 1. Overview

The Multi-Agent AI Data Analyst integrates two pre-trained machine learning models migrated into `backend2/app/models/`:
1. **Isolation Forest Retail Anomaly Detector** (`app/models/anomaly_detection/`)
2. **XGBoost Time-Series Sales Forecaster** (`app/models/forecasting/`)

Neither model requires retraining on startup. Both models are served deterministically by Python services without calling external LLM APIs for inference or calculations.

---

## 2. Model 1: Isolation Forest Anomaly Detector

### 2.1 Artifact Details
- **Artifact File**: `backend2/app/models/artifacts/isolation_forest_retail_model.joblib`
- **Metadata File**: `backend2/app/models/artifacts/isolation_forest_metadata.json`
- **Algorithm**: `sklearn.ensemble.IsolationForest`
- **Estimators**: 300 trees, `max_samples=4096`, `contamination=0.01`
- **Model Threshold**: `0.558716583436735`
- **Intended Scope**: Retail transaction data (Online Retail II schema). Flagged records indicate unusual transaction behavior requiring audit review; flags do not constitute a legal or fraud determination.

### 2.2 Feature Pipeline
Transforms raw transaction lines into 8 invoice-level features:
1. `total_invoice_value`: Sum of (Quantity × Price) across merchandise purchase lines.
2. `total_quantity`: Sum of units.
3. `unique_product_count`: Number of distinct StockCodes.
4. `average_unit_price`: Mean of merchandise unit prices.
5. `max_line_value`: Maximum single-line transaction value.
6. `price_std`: Population standard deviation of line unit prices.
7. `hour_of_day`: Hour (0-23) of earliest invoice scan timestamp.
8. `day_of_week`: Weekday of transaction (Monday=0 ... Sunday=6).

### 2.3 Counterfactual Explanations
For every flagged anomaly, the system computes counterfactual feature contributions by substituting each feature with its training-set median and observing the score reduction:
$$\Delta \text{score}_f = \text{score}(\mathbf{x}) - \text{score}(\mathbf{x}_{f \leftarrow \text{median}})$$
Features with high positive contributions are highlighted as key drivers in the diagnostic findings.

### 2.4 Genuine Evaluation Metrics (Ground Truth Reference)
From `model_metadata.json`:
- **Flag Rate on Test Set**: 1.38%
- **Synthetic Injection ROC-AUC**: 0.8874 (±0.0138)
- **Synthetic Injection PR-AUC**: 0.3344 (±0.0370)
- **Precision**: 36.66%
- **Recall**: 25.51%
- **F1 Score**: 30.07%
- **Seed Stability Spearman Correlation**: 0.9876

---

## 3. Model 2: XGBoost Time-Series Forecaster

### 3.1 Artifact Details
- **Artifact File**: `backend2/app/models/artifacts/xgboost_sales_forecasting_model.joblib`
- **Metadata File**: `backend2/app/models/artifacts/xgboost_metadata.json`
- **Algorithm**: `xgboost.XGBRegressor` (`hist` tree method)
- **Hyperparameters**: `n_estimators=350`, `max_depth=7`, `learning_rate=0.06`, `subsample=0.8`, `colsample_bytree=0.75`, `reg_alpha=0.5`, `reg_lambda=2.0`
- **Target Transform**: $\log(1 + \text{sales})$ during training with $\text{expm1}$ and zero-clipping at inference.
- **Support Data**: Compact reference history (`reference_history.parquet`), store metadata (`stores.csv`), crude oil prices (`oil.csv`), and holiday events (`holidays_events.csv`) in `app/models/forecasting/reference_data/`.

### 3.2 Feature Pipeline
- **Store & Product Categoricals**: `store_nbr`, `family`, `type`, `cluster`, `city`, `state`.
- **Temporal & Calendar Features**: `year`, `month`, `day`, `dayofweek`, `dayofyear`, `weekofyear`, `is_weekend`.
- **Recursive Sales Lags**: `sales_lag_1`, `sales_lag_7`, `sales_lag_14`, `sales_lag_28`.
- **Shifted Rolling Statistics**: 7, 14, 28-day rolling means; 7, 28-day rolling standard deviations (computed on $t-1$ values to prevent target leakage).
- **External Covariates**: Daily WTI oil price (`dcoilwtico`), 1-day lag, 7-day rolling mean, national holiday flag, workday flag, promotion count.

### 3.3 Genuine Benchmark Performance
From `model_metadata.json`:
| Metric | Baseline (Lag-7) | XGBoost 1-Step | XGBoost 16-Day Recursive |
|---|---|---|---|
| **RMSLE** | 0.5694 | 0.3834 | **0.4088** |
| **MAE** | 100.23 | 66.78 | **79.74** |
| **RMSE** | 350.06 | 232.37 | **284.55** |
| **WAPE (%)** | 21.46% | 14.29% | **17.07%** |

---

## 4. Generic Dataset Adaptation Strategy

When a user uploads a dataset that does not match the pre-trained retail schemas:
1. **Anomaly Detection**:
   - The dataset is profiled for numeric columns.
   - A dedicated unsupervised Isolation Forest is fitted in-memory on standardized numeric features.
   - Anomalies, ranks, and score distributions are returned.
2. **Time-Series Forecasting**:
   - The user selects or the system detects the date column and target numerical column.
   - A lightweight lag-regression XGBoost forecaster generates multi-step recursive projections.
