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
