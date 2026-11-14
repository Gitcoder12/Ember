import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.config import Settings, get_settings
from app.models.schemas import (
    HeatRiskRequest,
    HeatRiskResponse,
    RatingRequest,
    RatingResponse,
)
from app.services.heat_prediction import predict_heat_risk
from app.services.refund_engine import assess_refund

logger = logging.getLogger("ember.api")
router = APIRouter()

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/predictions/heat-risk", response_model=HeatRiskResponse)
def heat_risk(
    payload: HeatRiskRequest, request: Request, settings: SettingsDep
) -> HeatRiskResponse:
    result = predict_heat_risk(payload, settings)
    logger.info(
        "heat_risk request_id=%s risk=%.3f action=%s",
        getattr(request.state, "request_id", "-"),
        result.heat_risk,
        result.recommended_action,
    )
    return result


@router.post("/ratings", response_model=RatingResponse)
def evaluate_rating(payload: RatingRequest, settings: SettingsDep) -> RatingResponse:
    """Evaluate a heat rating. Persistence is not implemented yet, so nothing is stored."""
    assessment = assess_refund(payload.temperature_rating, payload.predicted_heat_risk, settings)
    return RatingResponse(
        order_id=payload.order_id,
        temperature_rating=payload.temperature_rating,
        refund_decision=assessment.decision,
        model_corroborated=assessment.model_corroborated,
    )
