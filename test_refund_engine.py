import pytest

from app.core.config import Settings
from app.services.refund_engine import assess_refund

SETTINGS = Settings()


@pytest.mark.parametrize("rating", ["hot", "warm", "lukewarm"])
def test_non_cold_ratings_need_no_refund_action(rating: str) -> None:
    result = assess_refund(rating, 0.9, SETTINGS)  # type: ignore[arg-type]
    assert result.decision == "no_action"
    assert result.model_corroborated is None


@pytest.mark.parametrize(
    ("predicted_risk", "expected"), [(0.9, True), (0.5, True), (0.1, False), (None, None)]
)
def test_cold_rating_always_goes_to_review(
    predicted_risk: float | None, expected: bool | None
) -> None:
    result = assess_refund("cold", predicted_risk, SETTINGS)
    assert result.decision == "refund_review"
    assert result.model_corroborated is expected
