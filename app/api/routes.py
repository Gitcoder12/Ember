from fastapi import APIRouter

from app.models.schemas import HeatRiskRequest, HeatRiskResponse, RatingRequest
from app.services.heat_prediction import predict_heat_risk

router = APIRouter()


@router.post("/predictions/heat-risk", response_model=HeatRiskResponse)
def heat_risk(request: HeatRiskRequest) -> HeatRiskResponse:
    return predict_heat_risk(request)


@router.post("/ratings", status_code=201)
def create_rating(request: RatingRequest) -> dict[str, str]:
    # Persistence will be added in the database phase.
    return {"status": "accepted", "temperature_rating": request.temperature_rating}
