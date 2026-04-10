from pathlib import Path
import sys

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "model_loaded" in payload


def test_customer_listing_returns_records():
    response = client.get("/api/customers", params={"limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] > 0
    assert len(payload["customers"]) > 0
    assert "customer_id" in payload["customers"][0]


def test_customer_detail_and_prediction_route():
    listing = client.get("/api/customers", params={"limit": 1})
    customer_id = listing.json()["customers"][0]["customer_id"]

    detail_response = client.get(f"/api/customers/{customer_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["customer_id"] == customer_id

    prediction_response = client.post(f"/api/customers/{customer_id}/prediction")
    assert prediction_response.status_code == 200
    prediction_payload = prediction_response.json()
    assert prediction_payload["customer_id"] == customer_id
    assert 0 <= prediction_payload["probability_high_value"] <= 1
