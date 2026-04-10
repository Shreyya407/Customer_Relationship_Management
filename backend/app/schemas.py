from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    model_loaded: bool


class CustomerSummary(BaseModel):
    customer_id: str
    country: str
    recency_days: int
    frequency: int
    monetary: float
    average_line_amount: float


class CustomerListResponse(BaseModel):
    total: int
    customers: list[CustomerSummary]


class CustomerDetail(BaseModel):
    customer_id: str
    country: str
    first_purchase_date: str
    last_purchase_date: str
    recency_days: int
    tenure_days: int
    invoices_count: int
    line_items_count: int
    quantity_sum: float
    monetary: float
    average_line_amount: float
    purchase_rate: float


class PredictionResponse(BaseModel):
    customer_id: str
    segment: str = Field(description="Predicted customer value segment.")
    probability_high_value: float
    model_source: str


class CountryListResponse(BaseModel):
    countries: list[str]
