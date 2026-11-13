# Ember — Feature Upgrade Plan

**Snapshot:** 2026-11-13

## Objective

An early food-delivery intelligence service that aims to estimate whether a meal may arrive warm and identify where heat is lost during delivery.

## P0 — correctness and scope

- [ ] Restore one canonical app/ml package layout and align console command, imports, docs and tests.
- [ ] Define calibration data schema, units, sensor provenance and measurement protocol.

## P1 — complete user workflow

- [ ] Build a reproducible calibration pipeline with held-out evaluation and uncertainty reporting.
- [ ] Add sensor-data validation, missing-value handling and temporal feature tests.

## P2 — research and scale

- [ ] Evaluate heat-retention prediction against simple baselines on documented probe datasets.
- [ ] Add a privacy-conscious API and deployment guide only after the calibration workflow is reproducible.

## Work packages for collaborators

1. Reproduce one defect or define one measurable question.
2. Implement one bounded change with tests.
3. Document exact commands, environment, input data and expected output.
4. Record results and limitations in ACTIVITY_LOG.md.

## Acceptance gate

- [ ] Clean setup works from README.
- [ ] Tests cover normal, boundary and failure paths.
- [ ] Claims match tested implementation.
- [ ] Benchmarks disclose environment, data and methodology.
- [ ] PR links the roadmap item, tests and log entry.
