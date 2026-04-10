from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.data import get_customer_detail, get_customer_feature_vector, list_countries, list_customers
from app.model_service import load_model, score_customer
from app.schemas import (
    CountryListResponse,
    CustomerDetail,
    CustomerListResponse,
    HealthResponse,
    PredictionResponse,
)


app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name, model_loaded=load_model() is not None)


@app.get("/api/countries", response_model=CountryListResponse)
def get_countries() -> CountryListResponse:
    return CountryListResponse(countries=list_countries())


@app.get("/api/customers", response_model=CustomerListResponse)
def get_customers(
    search: str | None = Query(default=None, description="Search by customer ID or country."),
    country: str | None = Query(default=None, description="Filter by country."),
    limit: int = Query(default=30, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> CustomerListResponse:
    customers, total = list_customers(search=search, country=country, limit=limit, offset=offset)
    return CustomerListResponse(total=total, customers=customers)


@app.get("/api/customers/{customer_id}", response_model=CustomerDetail)
def get_customer(customer_id: str) -> CustomerDetail:
    detail = get_customer_detail(customer_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerDetail(**detail)


@app.post("/api/customers/{customer_id}/prediction", response_model=PredictionResponse)
def predict_customer_value(customer_id: str) -> PredictionResponse:
    feature_row = get_customer_feature_vector(customer_id)
    if feature_row is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    probability, segment, source = score_customer(feature_row)
    return PredictionResponse(
        customer_id=customer_id,
        segment=segment,
        probability_high_value=round(float(probability), 4),
        model_source=source,
    )
