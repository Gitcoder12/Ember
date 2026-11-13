"""Post-delivery refund triage.

Policy: a customer's "cold" report always goes to refund review. The model only annotates whether
it agrees, because an unvalidated model must never overrule a customer.
"""

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.models.schemas import RefundDecision, TemperatureRating


@dataclass(frozen=True)
class RefundAssessment:
    decision: RefundDecision
    model_corroborated: bool | None


def assess_refund(
    rating: TemperatureRating,
    predicted_heat_risk: float | None,
    settings: Settings | None = None,
) -> RefundAssessment:
    config = settings or get_settings()
    if rating != "cold":
        return RefundAssessment(decision="no_action", model_corroborated=None)
    corroborated = (
        None
        if predicted_heat_risk is None
        else predicted_heat_risk >= config.refund_corroboration_threshold
    )
    return RefundAssessment(decision="refund_review", model_corroborated=corroborated)
