from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.config import settings

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


@lru_cache(maxsize=1)
def load_transactions() -> pd.DataFrame:
    if not settings.dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {settings.dataset_path}")

    try:
        frame = pd.read_csv(settings.dataset_path, sep=";", decimal=",", encoding="utf-8")
    except UnicodeDecodeError:
        frame = pd.read_csv(settings.dataset_path, sep=";", decimal=",", encoding="latin1")
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_label = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset is missing required columns: {missing_label}")

    frame["InvoiceDate"] = pd.to_datetime(frame["InvoiceDate"], dayfirst=True, errors="coerce")
    frame["Quantity"] = pd.to_numeric(frame["Quantity"], errors="coerce")
    frame["Price"] = pd.to_numeric(frame["Price"], errors="coerce")
    frame["CustomerID"] = pd.to_numeric(frame["Customer ID"], errors="coerce")

    frame = frame.dropna(subset=["InvoiceDate", "Quantity", "Price", "CustomerID"])
    frame = frame[(frame["Quantity"] > 0) & (frame["Price"] > 0)]
    frame["CustomerID"] = frame["CustomerID"].astype(int).astype(str)
    frame["Country"] = frame["Country"].fillna("Unknown")
    frame["TotalAmount"] = frame["Quantity"] * frame["Price"]

    return frame[
        [
            "Invoice",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "Price",
            "CustomerID",
            "Country",
            "TotalAmount",
        ]
    ].copy()


@lru_cache(maxsize=1)
def build_customer_features() -> pd.DataFrame:
    frame = load_transactions()
    reference_date = frame["InvoiceDate"].max() + pd.Timedelta(days=1)

    aggregated = frame.groupby("CustomerID").agg(
        first_invoice=("InvoiceDate", "min"),
        last_invoice=("InvoiceDate", "max"),
        invoices_count=("Invoice", "nunique"),
        line_items_count=("Invoice", "count"),
        quantity_sum=("Quantity", "sum"),
        monetary=("TotalAmount", "sum"),
        average_line_amount=("TotalAmount", "mean"),
        country=("Country", lambda values: values.mode().iat[0] if not values.mode().empty else "Unknown"),
    )

    aggregated["recency_days"] = (reference_date - aggregated["last_invoice"]).dt.days
    aggregated["tenure_days"] = (reference_date - aggregated["first_invoice"]).dt.days.clip(lower=1)
    aggregated["purchase_rate"] = aggregated["invoices_count"] / aggregated["tenure_days"]

    ordered = aggregated.reset_index().sort_values(
        by=["monetary", "invoices_count"],
        ascending=[False, False],
    )
    return ordered


def _apply_customer_filters(frame: pd.DataFrame, search: str | None, country: str | None) -> pd.DataFrame:
    filtered = frame

    if search:
        search_value = search.strip()
        if search_value:
            filtered = filtered[
                filtered["CustomerID"].str.contains(search_value, case=False, na=False)
                | filtered["country"].str.contains(search_value, case=False, na=False)
            ]

    if country:
        filtered = filtered[filtered["country"].str.lower() == country.strip().lower()]

    return filtered


def list_customers(search: str | None, country: str | None, limit: int, offset: int) -> tuple[list[dict], int]:
    customers = build_customer_features()
    filtered = _apply_customer_filters(customers, search=search, country=country)
    total = int(filtered.shape[0])

    paginated = filtered.iloc[offset : offset + limit]
    records: list[dict] = []
    for _, row in paginated.iterrows():
        records.append(
            {
                "customer_id": row["CustomerID"],
                "country": str(row["country"]),
                "recency_days": int(row["recency_days"]),
                "frequency": int(row["invoices_count"]),
                "monetary": round(float(row["monetary"]), 2),
                "average_line_amount": round(float(row["average_line_amount"]), 2),
            }
        )
    return records, total


def get_customer_detail(customer_id: str) -> dict | None:
    customers = build_customer_features()
    matches = customers[customers["CustomerID"] == str(customer_id)]
    if matches.empty:
        return None

    row = matches.iloc[0]
    return {
        "customer_id": row["CustomerID"],
        "country": str(row["country"]),
        "first_purchase_date": row["first_invoice"].date().isoformat(),
        "last_purchase_date": row["last_invoice"].date().isoformat(),
        "recency_days": int(row["recency_days"]),
        "tenure_days": int(row["tenure_days"]),
        "invoices_count": int(row["invoices_count"]),
        "line_items_count": int(row["line_items_count"]),
        "quantity_sum": round(float(row["quantity_sum"]), 2),
        "monetary": round(float(row["monetary"]), 2),
        "average_line_amount": round(float(row["average_line_amount"]), 2),
        "purchase_rate": round(float(row["purchase_rate"]), 4),
    }


def get_customer_feature_vector(customer_id: str) -> dict | None:
    customers = build_customer_features()
    matches = customers[customers["CustomerID"] == str(customer_id)]
    if matches.empty:
        return None

    row = matches.iloc[0]
    return {
        "recency_days": float(row["recency_days"]),
        "invoices_count": float(row["invoices_count"]),
        "line_items_count": float(row["line_items_count"]),
        "quantity_sum": float(row["quantity_sum"]),
        "monetary": float(row["monetary"]),
        "average_line_amount": float(row["average_line_amount"]),
        "tenure_days": float(row["tenure_days"]),
        "purchase_rate": float(row["purchase_rate"]),
    }


def list_countries() -> list[str]:
    customers = build_customer_features()
    countries = customers["country"].dropna().astype(str).unique().tolist()
    return sorted(countries)
