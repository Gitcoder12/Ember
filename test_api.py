import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "restaurant_id": "rest_123",
    "food_category": "biryani",
    "distance_km": 7.2,
    "estimated_delivery_minutes": 36,
    "pickup_delay_minutes": 8,
    "packaging_type": "standard",
    "ambient_temperature_c": 31,
}
HEAT_RISK_URL = "/api/v1/predictions/heat-risk"


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ember"}


def test_heat_risk_prediction_contract() -> None:
    response = client.post(HEAT_RISK_URL, json=VALID_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["heat_risk"] <= 1
    assert body["risk_level"] in {"low", "medium", "high"}
    assert body["recommended_action"] in {"none", "nudge", "priority_pickup"}
    assert isinstance(body["risk_factors"], list)


@pytest.mark.parametrize(
    "overrides",
    [
        {"distance_km": -1},
        {"packaging_type": "wooden"},
        {"unexpected_field": 1},
        {"restaurant_id": "../etc/passwd"},
        {"distance_km": 40, "estimated_delivery_minutes": 5},
    ],
)
def test_invalid_payload_returns_422(overrides: dict[str, object]) -> None:
    response = client.post(HEAT_RISK_URL, json={**VALID_PAYLOAD, **overrides})
    assert response.status_code == 422


def test_missing_body_returns_422() -> None:
    assert client.post(HEAT_RISK_URL, json={}).status_code == 422


def test_unknown_route_returns_404() -> None:
    assert client.get("/nope").status_code == 404


def test_wrong_method_returns_405() -> None:
    assert client.get(HEAT_RISK_URL).status_code == 405


def test_request_id_is_generated_and_safe_ids_are_echoed() -> None:
    generated = client.get("/health").headers["X-Request-ID"]
    assert len(generated) == 32
    echoed = client.get("/health", headers={"X-Request-ID": "trace-abc.123"})
    assert echoed.headers["X-Request-ID"] == "trace-abc.123"


def test_unsafe_request_id_is_replaced() -> None:
    response = client.get("/health", headers={"X-Request-ID": "bad id\twith spaces"})
    assert response.headers["X-Request-ID"] != "bad id\twith spaces"


def test_cold_rating_goes_to_refund_review() -> None:
    response = client.post(
        "/api/v1/ratings",
        json={
            "order_id": "ord_123",
            "temperature_rating": "cold",
            "packaging_rating": 2,
            "predicted_heat_risk": 0.82,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "order_id": "ord_123",
        "temperature_rating": "cold",
        "refund_decision": "refund_review",
        "model_corroborated": True,
    }


def test_invalid_rating_returns_422() -> None:
    response = client.post(
        "/api/v1/ratings",
        json={"order_id": "ord_1", "temperature_rating": "frozen", "packaging_rating": 9},
    )
    assert response.status_code == 422


def test_unhandled_error_returns_generic_500(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr("app.api.routes.predict_heat_risk", explode)
    safe_client = TestClient(app, raise_server_exceptions=False)
    response = safe_client.post(HEAT_RISK_URL, json=VALID_PAYLOAD)
    assert response.status_code == 500
    assert "secret" not in response.text
    assert response.json()["detail"] == "Internal server error"
