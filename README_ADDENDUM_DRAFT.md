# Ember — README Explanation Draft

> This draft must be checked against the code before replacing or merging into README.md.

## In plain language

An early food-delivery intelligence service that aims to estimate whether a meal may arrive warm and identify where heat is lost during delivery.

## What the current project contains

FastAPI-oriented Python application with a calibration workflow planned around probe measurements and thermal observations. The current audit identified missing app.ml calibration modules and stale docs paths; the calibration command should not be advertised as usable until the package paths and tests work.

## Technical explanation

Document the actual architecture, module boundaries, input formats, transformations, outputs, dependencies and failure behavior. Do not describe proposed components as implemented.

## Running the project

Use the tested commands in the main README. Include prerequisites, expected terminal output and one minimal example. State which inputs are synthetic, sample or real measurement data.

## Research and engineering limits

Explain unsupported inputs, known inaccuracies, uncertainty, data provenance and the evidence needed before making stronger claims.

## Contribution path

Read FEATURE_UPGRADE_PLAN.md and CONTRIBUTING.md. The activity log records what has actually been tested.
