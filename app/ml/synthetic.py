"""Seeded synthetic measurements, for TESTING the calibration pipeline only.

The truth below is deliberately different from Ember's assumed defaults, so a test can prove the
calibrator recovers unknown values from noisy data. Never use synthetic data to claim real-world
accuracy: it only shows that the fitting code is correct.
"""

import random

from app.ml.observations import Observation
from app.services.cooling import CoolingParameters, cooled_temperature_c

TRUE_PARAMETERS = CoolingParameters(
    packaging_half_life_min={
        "insulated": 95.0,
        "foil": 62.0,
        "standard": 52.0,
        "unknown": 52.0,
        "paper": 24.0,
        "open_box": 17.0,
    },
    category_factor={"biryani": 1.1, "curry": 1.2, "soup": 1.4, "fries": 0.6, "pizza": 0.7},
)
PACKAGING_CHOICES = ("insulated", "foil", "standard", "paper", "open_box")
CATEGORY_CHOICES = ("biryani", "curry", "soup", "fries", "pizza")


def generate_observations(
    count: int,
    *,
    seed: int,
    truth: CoolingParameters = TRUE_PARAMETERS,
    noise_sd_c: float = 2.0,
) -> list[Observation]:
    """Probe-style rows: initial and ambient temps vary; measurement noise is Gaussian."""
    if count <= 0:
        raise ValueError("count must be positive")
    if noise_sd_c < 0:
        raise ValueError("noise_sd_c must be non-negative")
    rng = random.Random(seed)
    rows: list[Observation] = []
    for _ in range(count):
        packaging = rng.choice(PACKAGING_CHOICES)
        category = rng.choice(CATEGORY_CHOICES)
        ambient = rng.uniform(8.0, 42.0)
        initial = min(max(rng.gauss(72.0, 4.0), 62.0), 85.0)
        minutes = rng.uniform(5.0, 70.0)
        true_temp = cooled_temperature_c(
            initial_c=initial,
            ambient_c=ambient,
            minutes=minutes,
            half_life_min=truth.half_life_min(packaging, category),
        )
        rows.append(
            Observation(
                packaging,
                category,
                ambient,
                initial,
                minutes,
                true_temp + rng.gauss(0.0, noise_sd_c),
            )
        )
    return rows
