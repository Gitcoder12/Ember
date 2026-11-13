# AI Engineering Worklog

## 2026-11-13 — Strict CI and cooling-model hardening

### Completed
- Addressed all three fresh Codex review findings: reject positive-distance zero-minute ETAs, allow digit-led normalized food-category labels that the measurement parser already emits, and preserve X-Request-ID on generic 500 responses.
- Replaced the accidental root package marker with the intended `app` package structure; removed the root `__init__.py` that caused mypy to identify `app.models.schemas` twice.
- Restored canonical modules under `app/core`, `app/ml`, `app/services`, `app/api`, and `app/models`, including the measured-data calibration pipeline, cooling physics, request middleware, API routes, and refund assessment.
- Corrected pytest discovery to include both the root regression suite and nested tests. Enabled pytest's `importlib` mode to avoid collisions between duplicate legacy test module names.
- Corrected Ruff's first-party import classification and scoped `S101` to test files and `S311` to seeded synthetic/bootstrap PRNG code. Production security checks remain enabled.
- Added finite-value validation for cooling temperatures, elapsed time, half-life, and probability uncertainty inputs.
- Added regression coverage for near-zero exposure, extreme supported ambient temperatures, non-finite numeric values, monotonic cooling, and schema rejection outside the supported ambient range.
- Expanded the model card with accepted input boundaries, uncertainty caveats, and explicit food-safety limitations.

### Validation
- Exact validated PR head: `3a346d0fcc43855c14bd98f81d111318c250a746`.
- GitHub Actions run: [43411528899](https://github.com/Gitcoder12/Ember/actions/runs/43411528899).
- Fresh Codex review completed on the earlier validated implementation with three P2 findings; all three are fixed and the threads resolved.
- Python 3.11: editable install, Ruff, Ruff format check, strict mypy, pytest all passed.
- Python 3.12: editable install, Ruff, Ruff format check, strict mypy, pytest all passed.
- Pytest: 108 tests collected and passed on each version.
- Coverage: 99.44% on each version (required minimum 90%).
- One Starlette/httpx deprecation warning remains; it does not fail the checks.

### Remaining
- The CI workflow and quality baseline are validated; the PR is not merged.
- Review the full diff before merge and obtain the required repository review/approval.
- Separate or remove legacy root-level duplicate source modules in a dedicated follow-up only after confirming no external scripts depend on them.
- Real-world temperature calibration still requires independently collected probe data; synthetic tests do not establish field accuracy.
- Rating persistence and a real-probe calibration workflow remain separate product issues.


## 2026-11-13 — Calibration/API contract review fixes

- Reject CSV packaging labels not supported by the prediction API; unsupported labels such as `vacuum bag` no longer produce unusable calibration parameters.
- Validate normalized food-category labels against the same character/length contract used by the API.
- Apply a 0.01 °C minimum numerical floor to calibrated temperature uncertainty, including serialized JSON and the human-readable report. This prevents a near-perfect fit from rounding uncertainty to zero and being rejected by the parameter loader.
- Document supported packaging/category labels and clarify that the uncertainty floor is not a probe-accuracy guarantee.
- Added regression tests for unsupported packaging/category labels and near-zero calibration uncertainty round-tripping through the parameter loader.
