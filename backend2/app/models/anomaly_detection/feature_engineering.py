"""
feature_engineering.py
======================
Feature engineering pipeline for retail transaction anomaly detection.
Supports Online Retail II-style schema and compatible retail datasets.
Deterministic, leak-free, in-memory operations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from app.core.exceptions import DataValidationError

FEATURE_PIPELINE_VERSION = "1.0.0"

CANONICAL_COLUMNS = [
    "Invoice", "StockCode", "Description", "Quantity",
    "InvoiceDate", "Price", "Customer ID", "Country"
]
REQUIRED_COLUMNS = ["Invoice", "StockCode", "Quantity", "InvoiceDate", "Price"]
OPTIONAL_COLUMNS = ["Description", "Customer ID", "Country"]

_ALIASES = {
    "invoice": "Invoice", "invoiceno": "Invoice", "invoicenumber": "Invoice",
    "stockcode": "StockCode",
    "description": "Description",
    "quantity": "Quantity", "qty": "Quantity",
    "invoicedate": "InvoiceDate",
    "price": "Price", "unitprice": "Price",
    "customerid": "Customer ID",
    "country": "Country",
}

NON_PRODUCT_STOCK_CODES = frozenset({
    "POST", "DOT", "M", "C2", "C3", "D", "S", "BANK CHARGES", "ADJUST", "ADJUST2",
    "AMAZONFEE", "CRUK", "TEST001", "TEST002", "B", "GIFT",
})
NON_PRODUCT_PREFIXES = ("GIFT_",)

CANDIDATE_FEATURES = [
    "total_invoice_value", "total_quantity", "unique_product_count", "line_item_count",
    "average_unit_price", "max_line_value", "price_std", "hour_of_day", "day_of_week",
]
DISCRETE_FEATURES = ("hour_of_day", "day_of_week")


def read_transactions_csv(path: Union[str, Path]) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise DataValidationError(f"Input file not found: {p}")
    if p.stat().st_size == 0:
        raise DataValidationError(f"Input file is empty (0 bytes): {p}")
    last_err: Optional[Exception] = None
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            df = pd.read_csv(p, dtype=str, encoding=enc, keep_default_na=False, na_values=[""])
            break
        except UnicodeDecodeError as e:
            last_err = e
        except pd.errors.EmptyDataError:
            raise DataValidationError(f"Input file has no header or data: {p}")
        except pd.errors.ParserError as e:
            raise DataValidationError(f"Input file is not a parseable CSV ({p}): {e}")
    else:
        raise DataValidationError(f"Could not decode {p} as UTF-8 or cp1252: {last_err}")
    if len(df) == 0:
        raise DataValidationError(f"Input file contains a header but no rows: {p}")
    df["source_file"] = p.name
    df["source_row"] = np.arange(len(df))
    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise DataValidationError(f"Expected a pandas DataFrame, got {type(df).__name__}.")
    if df.shape[1] == 0:
        raise DataValidationError("Input has no columns.")
    rename, seen = {}, set()
    for col in df.columns:
        key = re.sub(r"[^a-z]", "", str(col).lower())
        canon = _ALIASES.get(key)
        if canon and canon not in seen:
            rename[col] = canon
            seen.add(canon)
    out = df.rename(columns=rename)
    missing = [c for c in REQUIRED_COLUMNS if c not in out.columns]
    if missing:
        raise DataValidationError(
            f"Missing required column(s): {missing}. Found columns: {list(df.columns)}. "
            f"Required: {REQUIRED_COLUMNS}; optional: {OPTIONAL_COLUMNS}."
        )
    if len(out) == 0:
        raise DataValidationError("Input has columns but zero rows.")
    return out


def _clean_id(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        num = pd.to_numeric(s, errors="coerce")
        notna = num.notna()
        if notna.any() and bool((num[notna] % 1 == 0).all()):
            out = num.astype("Int64").astype("string")
        else:
            out = num.astype("string")
    else:
        out = s.astype("string")
    out = out.str.strip()
    return out.mask(out == "", pd.NA)


def _parse_dates(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        dt = pd.to_datetime(s)
        if getattr(dt.dt, "tz", None) is not None:
            dt = dt.dt.tz_localize(None)
        return dt
    st = s.astype("string").str.strip()
    dt = pd.to_datetime(st, format="%m/%d/%Y %H:%M", errors="coerce")
    todo = dt.isna() & st.notna() & (st != "")
    if todo.any():
        alt = pd.to_datetime(st[todo], format="ISO8601", errors="coerce")
        dt = dt.where(~todo, alt.reindex(dt.index))
        todo = dt.isna() & st.notna() & (st != "")
    if todo.any():
        alt = pd.to_datetime(st[todo], format="mixed", errors="coerce")
        dt = dt.where(~todo, alt.reindex(dt.index))
    return dt


@dataclass
class PreparedLines:
    lines: pd.DataFrame
    rejected: pd.DataFrame
    summary: Dict[str, Any]


def prepare_lines(
    raw: Union[pd.DataFrame, str, Path],
    *,
    max_invalid_fraction: float = 0.05
) -> PreparedLines:
    if isinstance(raw, (str, Path)):
        raw = read_transactions_csv(raw)
    df = standardize_columns(raw).copy()
    n_in = len(df)
    if "source_row" not in df.columns:
        df["source_row"] = np.arange(n_in)
    if "source_file" not in df.columns:
        df["source_file"] = "<in_memory_dataframe>"

    df["Invoice"] = _clean_id(df["Invoice"])
    df["StockCode"] = _clean_id(df["StockCode"])
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["InvoiceDate"] = _parse_dates(df["InvoiceDate"])
    for opt in OPTIONAL_COLUMNS:
        if opt not in df.columns:
            df[opt] = pd.NA
    df["Customer ID"] = _clean_id(df["Customer ID"])
    df["Country"] = df["Country"].astype("string")
    df["Description"] = df["Description"].astype("string")

    bad_cols = {}
    for col in REQUIRED_COLUMNS:
        s = df[col]
        bad = s.isna()
        if col in ("Quantity", "Price"):
            bad = bad | ~np.isfinite(s.astype("float64").fillna(0.0))
        bad_cols[col] = bad
    invalid = np.zeros(n_in, dtype=bool)
    per_col = {}
    for col, bad in bad_cols.items():
        per_col[col] = int(bad.sum())
        invalid |= bad.to_numpy()
        if bad.mean() > max_invalid_fraction:
            raise DataValidationError(
                f"Column '{col}' has {int(bad.sum())} of {n_in} values "
                f"({bad.mean():.1%}) that are missing or invalid."
            )
    rejected = df.loc[invalid].copy()
    df = df.loc[~invalid].copy()
    if len(df) == 0:
        raise DataValidationError("No valid rows remain after type validation.")

    df["Invoice"] = df["Invoice"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    df["stock_norm"] = df["StockCode"].str.strip().str.upper()
    df["Quantity"] = df["Quantity"].astype("float64")
    df["Price"] = df["Price"].astype("float64")
    df["line_value"] = df["Quantity"] * df["Price"]

    first = df["Invoice"].str[0].str.upper()
    df["invoice_type"] = np.select(
        [first == "C", first == "A", first.str.isdigit()],
        ["cancellation", "adjustment", "sale"],
        default="other"
    )

    is_service = df["stock_norm"].isin(NON_PRODUCT_STOCK_CODES) | df["stock_norm"].str.startswith(NON_PRODUCT_PREFIXES)
    sale = df["invoice_type"] == "sale"

    df["line_class"] = np.select(
        [
            df["invoice_type"] == "cancellation",
            df["invoice_type"] == "adjustment",
            df["invoice_type"] == "other",
            sale & (df["Price"] < 0),
            sale & (df["Price"] == 0),
            sale & (df["Quantity"] <= 0),
            sale & is_service,
        ],
        [
            "return", "adjustment", "other_invoice_type", "negative_price", "zero_price",
            "non_positive_quantity", "purchase_service"
        ],
        default="purchase_product"
    )

    summary = {
        "rows_in": int(n_in),
        "rows_rejected_unparseable": int(len(rejected)),
        "rejected_by_column": per_col,
        "rows_valid": int(len(df)),
        "line_class_counts": {k: int(v) for k, v in df["line_class"].value_counts().items()},
        "invoice_type_line_counts": {k: int(v) for k, v in df["invoice_type"].value_counts().items()},
    }
    return PreparedLines(lines=df.reset_index(drop=True), rejected=rejected, summary=summary)


@dataclass
class FeatureResult:
    invoices: pd.DataFrame
    returns: pd.DataFrame
    excluded: pd.DataFrame
    lines: pd.DataFrame
    rejected: pd.DataFrame
    summary: Dict[str, Any] = field(default_factory=dict)


def build_invoice_table(lines: pd.DataFrame) -> pd.DataFrame:
    prod = lines[lines["line_class"] == "purchase_product"]
    if prod.empty:
        return pd.DataFrame(columns=["Invoice"] + CANDIDATE_FEATURES)
    g = prod.groupby("Invoice", sort=False)
    feats = pd.DataFrame({
        "total_invoice_value": g["line_value"].sum(),
        "total_quantity": g["Quantity"].sum(),
        "unique_product_count": g["stock_norm"].nunique(),
        "line_item_count": g.size(),
        "average_unit_price": g["Price"].mean(),
        "max_line_value": prod.assign(_abs=prod["line_value"].abs()).groupby("Invoice", sort=False)["_abs"].max(),
        "price_std": g["Price"].std(ddof=0),
        "invoice_datetime": g["InvoiceDate"].min(),
    })
    feats["hour_of_day"] = feats["invoice_datetime"].dt.hour.astype("int64")
    feats["day_of_week"] = feats["invoice_datetime"].dt.dayofweek.astype("int64")

    allg = lines[lines["invoice_type"] == "sale"].groupby("Invoice", sort=False)
    info = pd.DataFrame({
        "n_lines_in_source": allg.size(),
    })
    svc = lines[lines["line_class"] == "purchase_service"].groupby("Invoice")
    info["n_service_lines"] = svc.size()
    info["service_value"] = svc["line_value"].sum()
    excl = lines[lines["line_class"].isin(["zero_price", "non_positive_quantity", "negative_price"])]
    info["n_excluded_nonpurchase_lines"] = excl.groupby("Invoice").size()

    dup_cols = ["Invoice", "stock_norm", "Quantity", "Price", "InvoiceDate"]
    dup = prod[prod.duplicated(subset=dup_cols, keep="first")].groupby("Invoice").size()
    info["duplicate_line_count"] = dup
    cust = prod.dropna(subset=["Customer ID"]).groupby("Invoice")["Customer ID"].first()
    info["customer_id"] = cust
    info["country"] = g["Country"].first()
    info["source_file"] = g["source_file"].first()
    info["first_source_row"] = g["source_row"].min()
    out = feats.join(info, how="left")
    for c in ["n_service_lines", "service_value", "n_excluded_nonpurchase_lines", "duplicate_line_count"]:
        out[c] = out[c].fillna(0)
    for c in ["n_service_lines", "n_excluded_nonpurchase_lines", "duplicate_line_count"]:
        out[c] = out[c].astype("int64")
    out["has_customer_id"] = out["customer_id"].notna()
    out["first_source_row"] = out["first_source_row"].astype("int64")
    out = out.reset_index().rename(columns={"index": "Invoice"})
    out = out.sort_values(["invoice_datetime", "Invoice"], kind="mergesort").reset_index(drop=True)
    return out


def engineer_features(
    raw: Union[pd.DataFrame, str, Path],
    *,
    max_invalid_fraction: float = 0.05
) -> FeatureResult:
    prep = prepare_lines(raw, max_invalid_fraction=max_invalid_fraction)
    inv = build_invoice_table(prep.lines)
    r = prep.lines[prep.lines["invoice_type"] == "cancellation"]
    ret = pd.DataFrame() if r.empty else r.groupby("Invoice", sort=False).size().reset_index(name="n_lines")
    scored = set(inv["Invoice"])
    rest = prep.lines[~prep.lines["Invoice"].isin(scored)]
    exc = pd.DataFrame() if rest.empty else rest.groupby("Invoice", sort=False).size().reset_index(name="n_lines")
    
    summary = dict(prep.summary)
    summary.update({
        "invoices_scored": int(len(inv)),
        "return_invoices": int(len(ret)),
    })
    return FeatureResult(inv, ret, exc, prep.lines, prep.rejected, summary)


def build_reference_stats(X: pd.DataFrame, feature_names: Sequence[str]) -> Dict[str, Any]:
    stats: Dict[str, Any] = {"n": int(len(X)), "features": {}}
    for f in feature_names:
        v = X[f].to_numpy(dtype="float64")
        if f in DISCRETE_FEATURES:
            vals, cnt = np.unique(v, return_counts=True)
            stats["features"][f] = {
                "type": "discrete",
                "median": float(np.median(v)),
                "frequencies": {str(int(a)): float(b) / len(v) for a, b in zip(vals, cnt)}
            }
        else:
            stats["features"][f] = {
                "type": "continuous",
                "median": float(np.median(v)),
                "p01": float(np.quantile(v, 0.01)),
                "p99": float(np.quantile(v, 0.99)),
                "sorted_values": np.sort(v)
            }
    return stats
