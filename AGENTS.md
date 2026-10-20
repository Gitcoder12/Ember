# AGENTS.md

Context for any AI coding agent or human contributor. Read this first, then `docs/NEXT.md`.

## What Ember is
A heat-aware food-delivery risk service (FastAPI, Python 3.11+). It predicts the probability that an
order arrives below a serving temperature, explains why, recommends an action, and triages
"cold" customer reports for refund review.

## Commands
```bash
pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy app && pytest     # quality gate, must pass
uvicorn app.main:app --reload                                  # API + /docs
python -m app.ml.calibrate measurements.csv -o calibration.json # fit physics to real probe data
EMBER_CALIBRATION_PATH=calibration.json uvicorn app.main:app    # serve with calibrated constants
```

## Layout
```
app/api/        thin HTTP routes (no business logic)
app/core/       settings (EMBER_* env), request-ID middleware
app/models/     pydantic schemas = the trust boundary
app/services/   cooling.py (physics), heat_prediction.py, refund_engine.py
app/ml/         observations.py (CSV + validation), calibrate.py (fitter + CLI), synthetic.py (tests only)
tests/          pytest, coverage gate 90%
docs/           NEXT.md (status + plan), model-card.md, measurement-protocol.md
```

## Rules
- **Honesty first.** Never claim accuracy that was not measured. Synthetic data proves the code is
  correct; it never proves real-world accuracy. State assumptions in code and docs.
- The quality gate (ruff, strict mypy, pytest with coverage >= 90%) must pass before every commit.
- Validate at the boundary (`app/models/schemas.py`). New endpoint = validation + tests.
- Routes stay thin; logic lives in pure, testable services. Config only through `core/config.py`.
- Never commit secrets, tokens, raw data, or trained artifacts. Never log personal data.
- Small commits with prefixes: `feat:`, `fix:`, `test:`, `docs:`, `build:`, `ci:`.
- Git identity comes from existing history (`git log -1`); never invent an email.
- After finishing work, update `docs/NEXT.md` so the next agent can continue from the repo alone.

## Key decisions (and why)
- **Physics first, calibrate before ML.** Newton's law has the right shape; only a few constants
  are unknown. Fitting them needs little data and stays explainable. ML on synthetic labels would
  only relearn the physics that generated them.
- **57 C threshold** = FDA Food Code hot-holding minimum (BfR recommends 60 C). It is a safety
  anchor, not a measure of perceived hotness.
- **A customer's "cold" report always goes to refund review.** The model only annotates agreement;
  an unvalidated model must never overrule a customer.
- **Calibrated error replaces assumed error.** `temp_uncertainty_c` comes from held-out data.
- **Fail fast** if `EMBER_CALIBRATION_PATH` points to a missing or invalid file.
