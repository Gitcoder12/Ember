# Ember — Activity Log

**Snapshot:** 2026-11-13

## Verified history

Issue #7 records missing calibration modules, stale documentation paths and an unexpected generated artifact path. No files were changed as part of that issue: https://github.com/Gitcoder12/Ember/issues/7

## Current scope and caveats

FastAPI-oriented Python application with a calibration workflow planned around probe measurements and thermal observations. The current audit identified missing app.ml calibration modules and stale docs paths; the calibration command should not be advertised as usable until the package paths and tests work.

## Append-only work record

| Date | Human / agent | Issue or PR | Files / task | Validation command and environment | Result | Evidence / limitations |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | name | link | paths | exact command | pass / fail / not run | link and caveats |

Record failures, regressions, reversions and checks not run. Never rewrite prior history to imply success. A green CI run is not proof of production readiness.

## Portfolio documentation rollout — 2026-11-13

- Documentation PR: https://github.com/Gitcoder12/Ember/pull/8
- Added project-specific feature plan, company-fit mapping, two-level README guide and quality checklist.
- Existing agent/contributor instructions were preserved or extended without replacing the repository's established policies.
- README now includes a beginner explanation and a technical/research view tied to current scope and limitations.
- Validation: documentation/source review only; no application runtime test or deployment is claimed by this docs PR.
- Status: draft PR, not merged.
