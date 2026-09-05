from app.models.schemas import HeatRiskRequest, HeatRiskResponse


def predict_heat_risk(request: HeatRiskRequest) -> HeatRiskResponse:
    """Simple interpretable baseline; replace with a trained model later."""
    risk = 0.05
    risk += min(request.estimated_delivery_minutes / 90, 0.35)
    risk += min(request.pickup_delay_minutes / 20, 0.30)
    risk += min(request.distance_km / 20, 0.15)

    if request.ambient_temperature_c < 15:
        risk += 0.10
    elif request.ambient_temperature_c > 35:
        risk += 0.03

    if request.packaging_type.lower() in {"standard", "paper"}:
        risk += 0.05

    risk = min(max(risk, 0.0), 1.0)

    if risk >= 0.70:
        level = "high"
        state = "lukewarm_or_cold"
        action = "priority_pickup"
    elif risk >= 0.40:
        level = "medium"
        state = "warm"
        action = "nudge"
    else:
        level = "low"
        state = "hot"
        action = "none"

    return HeatRiskResponse(
        heat_risk=round(risk, 3),
        risk_level=level,
        expected_state=state,
        recommended_action=action,
    )
