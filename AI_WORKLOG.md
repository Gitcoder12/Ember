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

## 2026-11-13 — Portfolio audit of current main and CI repair PR

### Audit record
- Audited main HEAD: `563a16718ce66d70250c6ed5ff6065b22677c0dc`.
- Main recursive tree: 41 tracked files, root-level source and tests, one nested `tests/test_api.py`, package metadata, and no GitHub Actions workflow under `.github/workflows/`.
- Recommendation: IMPROVE / strong applied-science candidate after package and measurement reproducibility are stabilized.

### Confirmed main-branch findings
- `pyproject.toml` declares `ember-calibrate = "app.ml.calibrate:main"`, but main contains `calibrate.py` at repository root and does not contain `app/ml/calibrate.py` or `app/ml/observations.py`. The root calibration module imports those missing package paths. The installed calibration command is therefore inconsistent with the committed package layout.
- The README links to `docs/measurement-protocol.md` and `docs/NEXT.md`, while the tree contains `measurement-protocol.md` and `NEXT.md` at repository root.
- A generated-looking path `mnt/user-data/outputs/Ember/app/ml/__init__.py` is tracked. Preserve it until its origin and contents are reviewed; do not delete it as cleanup without provenance and Git-history checks.
- Main has a root `ci.yml`, not a workflow under `.github/workflows/`; GitHub Actions will not discover that file as a workflow.
- Pytest is configured with `testpaths = ["tests"]`, while most test files are at repository root. The configured discovery path therefore excludes the root-level tests.
- The README correctly distinguishes synthetic calibration verification from real-world food-temperature accuracy. Real probe data is still required before field-accuracy claims.

### Existing repair work
- [PR #2](https://github.com/Gitcoder12/Ember/pull/2) moves calibration/observation modules into the canonical `app/ml` package, adds strict CI, corrects test discovery, and adds AI_WORKLOG.
- GitHub Actions run [43414162445](https://github.com/Gitcoder12/Ember/actions/runs/43414162445) associated with the current PR #2 head completed successfully.
- The worklog contains earlier validated SHAs; re-check the exact current PR head before merge and ensure the final run is attached to that head.
- PR #8 is documentation-focused. Avoid duplicating work already present in PR #2.

### Verification
- Inspected main README, pyproject, calibration module, app entry point, recursive tree, and open issues/PR metadata.
- No local tests were run in this audit.
- Main CI: NOT CONFIGURED at the expected GitHub Actions path.
- PR #2 CI: completed successfully on the current PR head; this does not repair main until merge.
- Independent final-head review: NOT COMPLETE.
- Real probe calibration and field accuracy: NOT VERIFIED.

### Next actions
1. Review the exact current PR #2 diff and ensure all legacy test files are either included in discovery or intentionally retired with evidence.
2. Remove or relocate the tracked generated-output artifact only after confirming it has no unique user data and preserving history.
3. Resolve README links and align every command with the installed package.
4. Obtain real, independently collected probe measurements and report held-out residuals; do not use synthetic tests as field validation.
5. Keep ratings non-persistent and refund actions advisory until storage, authorization, and product policy are defined.
