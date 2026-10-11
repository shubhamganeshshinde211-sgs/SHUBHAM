"""
API Endpoint Integration Tests using FastAPI TestClient.
"""
import pytest
from starlette.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"

def test_data_quality_endpoint(client):
    res = client.get("/api/data-quality")
    assert res.status_code == 200
    data = res.json()
    assert "active_data_mode" in data
    assert "metrics" in data
    assert "provenance" in data

def test_forecast_evaluation_endpoint(client):
    res = client.get("/api/forecasts/evaluation")
    assert res.status_code == 200
    data = res.json()
    assert "total_evaluated_samples" in data
    assert "commodities" in data

def test_forecast_by_crop_endpoint(client):
    res = client.get("/api/forecasts/tomato?horizon=3")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    item = data[0]
    assert "predicted_modal_price" in item
    assert "forecast_status" in item
    assert "model_name" in item

def test_routes_optimizer_endpoint(client):
    payload = {
        "crop_id": "tomato",
        "quantity_kg": 5000,
        "vehicle_type": "covered_truck",
        "decision_policy": "forecast_aware",
        "forecast_horizon_days": 3
    }
    res = client.post("/api/routes/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "ranked_routes" in data
    assert len(data["ranked_routes"]) > 0
    route0 = data["ranked_routes"][0]
    assert "breakdown" in route0
    assert "timing_recommendation" in route0
    assert "net_realization" in route0["breakdown"]

def test_realization_backward_compatibility(client):
    payload = {
        "quantity_kg": 1000,
        "price_per_kg": 30,
        "loss_fraction": 0.05,
        "transport_cost": 2000,
        "handling_cost": 500,
        "holding_cost": 100,
        "market_cost": 200
    }
    res = client.post("/realization", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "net_realization" in data
    assert "net_per_kg" in data
    # Revenue = 1000 * 0.95 * 30 = 28500
    # Costs = 2000 + 500 + 100 + 200 = 2800
    # Net = 28500 - 2800 = 25700
    assert data["net_realization"] == 25700.0
    assert data["net_per_kg"] == 25.7
