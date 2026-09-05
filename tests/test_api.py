from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_heat_risk_prediction() -> None:
    response = client.post(
        "/api/v1/predictions/heat-risk",
        json={
            "restaurant_id": "rest_123",
            "food_category": "biryani",
            "distance_km": 7.2,
            "estimated_delivery_minutes": 36,
            "pickup_delay_minutes": 8,
            "packaging_type": "standard",
            "ambient_temperature_c": 31,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["heat_risk"] <= 1
    assert body["risk_level"] in {"low", "medium", "high"}
