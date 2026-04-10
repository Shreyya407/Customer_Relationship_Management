from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .data import build_customer_table
from .schemas import CustomerSummary, DashboardSummary


app = FastAPI(title="CRM Retail Intelligence API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_data():
    try:
        return build_customer_table()
    except Exception as exc:  # pragma: no cover - startup/runtime error surface
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/summary", response_model=DashboardSummary)
def summary() -> DashboardSummary:
    data = _load_data()
    customers = data.segments
    segment_counts = customers["segment"].value_counts().sort_index().to_dict()
    top_customers = customers.sort_values("revenue", ascending=False).head(10)
    return DashboardSummary(
        total_customers=int(customers["customer_id"].nunique()),
        total_orders=int(data.raw["Invoice"].nunique()),
        total_revenue=float(data.raw["revenue"].sum()),
        average_order_value=float(data.raw.groupby("Invoice")["revenue"].sum().mean()),
        segment_counts={str(key): int(value) for key, value in segment_counts.items()},
        top_customers=[CustomerSummary(**row.to_dict()) for _, row in top_customers.iterrows()],
    )


@app.get("/api/customers", response_model=list[CustomerSummary])
def customers() -> list[CustomerSummary]:
    data = _load_data()
    frame = data.segments.sort_values(["revenue", "orders"], ascending=False)
    return [CustomerSummary(**row.to_dict()) for _, row in frame.iterrows()]


@app.get("/api/customers/{customer_id}", response_model=CustomerSummary)
def customer_detail(customer_id: int) -> CustomerSummary:
    data = _load_data()
    match = data.segments[data.segments["customer_id"] == customer_id]
    if match.empty:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerSummary(**match.iloc[0].to_dict())
