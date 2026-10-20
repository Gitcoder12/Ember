"""Runtime configuration, overridable through EMBER_* environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMBER_", env_file=".env", extra="ignore")

    # Physics assumptions. Uncalibrated until real delivery data exists.
    initial_food_temp_c: float = Field(default=75.0, gt=0, le=100)
    # 57 C = FDA Food Code hot-holding minimum (BfR recommends 60 C). A safety anchor, not a
    # measure of what customers perceive as hot; ratings should refine this later.
    min_serving_temp_c: float = Field(default=57.0, gt=0, le=100)
    temp_uncertainty_c: float = Field(default=5.0, gt=0, le=30)

    # Decision thresholds on the heat-risk probability.
    nudge_risk_threshold: float = Field(default=0.35, ge=0, le=1)
    priority_risk_threshold: float = Field(default=0.65, ge=0, le=1)
    refund_corroboration_threshold: float = Field(default=0.5, ge=0, le=1)

    # JSON written by `python -m app.ml.calibrate`; overrides the assumed cooling constants.
    calibration_path: Path | None = None

    log_level: str = "INFO"

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.min_serving_temp_c >= self.initial_food_temp_c:
            raise ValueError("min_serving_temp_c must be below initial_food_temp_c")
        if self.nudge_risk_threshold >= self.priority_risk_threshold:
            raise ValueError("nudge_risk_threshold must be below priority_risk_threshold")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
