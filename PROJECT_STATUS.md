# Project Status — Ember

**Snapshot date:** 2026-11-16  
**Status type:** Initial documentation and repository-tree assessment  
**Default branch:** main  
**Review completeness:** Partial — not a code audit or release certification

## Project purpose
Heat-aware food-delivery intelligence service intended to estimate whether meals may arrive below a serving-temperature threshold and identify contributing delay/packaging factors.

## Current maturity (README-declared; not independently verified)
Root includes a Python package/app, API routes, schemas, calibration/cooling/heat-prediction modules, Dockerfile, model/measurement documentation and multiple test files. README states v0.1 uses Newton cooling, not ML; constants are assumed until real-probe calibration, and calibration code has only been checked on synthetic data.

## Observed repository structure
app/, main.py, config.py, cooling.py, heat_prediction.py, observations.py, refund_engine.py, schemas.py, routes.py, middleware.py, calibrate.py, Dockerfile, pyproject.toml, tests and measurement/model docs.

## Known issues and risks to investigate
Food-temperature safety threshold and the FDA reference need exact source/version verification. The model risk is probabilistic under assumed parameters, not validated real-world predictive accuracy. Ratings are not persisted according to README. Refund decisions could affect consumers/merchants; keep human review and clear separation from actual food-safety certification.

## Recommended next actions
Run full Ruff/mypy/pytest and Docker smoke tests; audit calibration data schema and held-out real probe measurements; benchmark physics baseline before any ML; validate uncertainty intervals and edge cases; ensure refund_review never executes a payment automatically; add data retention/privacy controls.

## Verification record
| Check | Result |
|---|---|
| Default-branch top-level tree | Inspected |
| README | Inspected |
| Deep source review | Not performed |
| Tests / build / runtime | Not run |
| Security / dependency audit | Not run |
| Live deployment / API checks | Not run |
| Independent review | Not performed |

## Change log
- 2026-11-16: Added this initial status snapshot on a review branch. No application code or existing data changed.

> Update this file only after the corresponding inspection or verification has actually been performed. Distinguish observed facts, README claims, hypotheses and unrun checks.