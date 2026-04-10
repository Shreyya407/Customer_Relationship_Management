from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import settings


REQUIRED_COLUMNS = {
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
}


@dataclass
class RetailData:
    raw: pd.DataFrame
    customers: pd.DataFrame
    segments: pd.DataFrame


def _read_dataset(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=";", dtype={"Customer ID": "Int64"}, encoding="utf-8")
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    return frame


def _parse_frame(frame: pd.DataFrame) -> pd.DataFrame:
    parsed = frame.copy()
    parsed["InvoiceDate"] = pd.to_datetime(parsed["InvoiceDate"], dayfirst=True, errors="coerce")
    parsed["Quantity"] = pd.to_numeric(parsed["Quantity"], errors="coerce")
    parsed["Price"] = pd.to_numeric(parsed["Price"].astype(str).str.replace(",", "."), errors="coerce")
    parsed = parsed.dropna(subset=["Customer ID", "InvoiceDate", "Quantity", "Price"])
    parsed = parsed[parsed["Quantity"] > 0]
    parsed["revenue"] = parsed["Quantity"] * parsed["Price"]
    return parsed


def _score(series: pd.Series, reverse: bool = False) -> pd.Series:
    if series.nunique() < 4:
        return pd.Series([3] * len(series), index=series.index)
    ranked = pd.qcut(series.rank(method="first"), 4, labels=[1, 2, 3, 4])
    scores = ranked.astype(int)
    return 5 - scores if reverse else scores


def build_customer_table(path: str | None = None) -> RetailData:
    dataset_path = Path(path or settings.dataset_path)
    frame = _parse_frame(_read_dataset(str(dataset_path)))

    snapshot = frame["InvoiceDate"].max()
    customers = (
        frame.groupby(["Customer ID", "Country"], as_index=False)
        .agg(
            orders=("Invoice", "nunique"),
            items=("Quantity", "sum"),
            revenue=("revenue", "sum"),
            last_purchase=("InvoiceDate", "max"),
        )
        .rename(columns={"Customer ID": "customer_id", "Country": "country"})
    )
    customers["last_purchase_days"] = (snapshot - customers["last_purchase"]).dt.days
    customers["recency_score"] = _score(customers["last_purchase_days"], reverse=True)
    customers["frequency_score"] = _score(customers["orders"])
    customers["monetary_score"] = _score(customers["revenue"])
    customers["rfm_cluster"] = (
        customers["recency_score"].astype(str)
        + customers["frequency_score"].astype(str)
        + customers["monetary_score"].astype(str)
    )
    return RetailData(raw=frame, customers=customers, segments=_segment_customers(customers))


def _segment_customers(customers: pd.DataFrame) -> pd.DataFrame:
    frame = customers.copy()
    high_value = frame["monetary_score"] >= 4
    loyal = (frame["frequency_score"] >= 3) & (frame["recency_score"] >= 3)
    at_risk = frame["recency_score"] <= 2

    frame["segment"] = "Occasional"
    frame.loc[high_value & loyal, "segment"] = "Champions"
    frame.loc[high_value & ~loyal, "segment"] = "High Value"
    frame.loc[~high_value & loyal, "segment"] = "Loyal"
    frame.loc[at_risk & ~high_value, "segment"] = "At Risk"
    return frame
