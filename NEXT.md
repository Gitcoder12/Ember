# Status and next steps

Single source of truth for continuing work. Update it at the end of every session.

## Done
- API: `/health`, `POST /api/v1/predictions/heat-risk`, `POST /api/v1/ratings` (evaluates, does not store)
- Physics model (Newton's law), explainable risk factors, 57 C FDA-anchored threshold
- Refund triage, strict validation, request IDs, safe 500 handler
- Calibration pipeline: probe-data CSV -> fitted half-lives, bootstrap CIs, held-out error, JSON
- Tooling: ruff, strict mypy, pytest (coverage gate), Dockerfile, CI workflow

## Known gaps (be honest about these)
- Cooling constants are assumed until calibrated with REAL measurements
- Calibration is validated on synthetic data only (proves code, not real accuracy)
- Category factors are assumed during packaging fitting; CIs reflect sampling noise, not that assumption
- Single-lump cooling model: no portion size, batching, or reheating effects
- Ratings are not persisted; Docker image and CI were not run in the authoring sandbox

## Next, in priority order
1. **Collect real data** (human task): follow `docs/measurement-protocol.md`, aim for 30+ rows per
   packaging type, run `ember-calibrate`. Done when held-out error on real data is reported in
   `docs/model-card.md`.
2. **Persistence:** SQLAlchemy + SQLite (Postgres via docker-compose). Tables: ratings, prediction
   log. Done when ratings survive a restart and tests cover the repository layer.
3. **`services/rating_engine.py`:** Bayesian-smoothed restaurant heat score so one bad review does not
   sink a restaurant with few ratings. Done when unit tests cover small-sample behaviour.
4. **Residual ML (only with >= 500 real rows):** gradient boosting on the physics residual. Ship only if it
   beats calibrated physics on a held-out set; otherwise do not ship it.
5. **`services/delay_analysis.py`:** detect slow pickup and delivery segments.
