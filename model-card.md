# Model card: Ember heat-risk model

## Summary
Predicts the probability that food arrives below a serving temperature, using Newton's law of
cooling and a Normal error band. It is a physics model with a calibration step, not a black-box ML model.

    T(t) = T_ambient + (T_initial - T_ambient) * 2^(-t / half_life)
    heat_risk = P(T_arrival < min_serving_temp) with T_arrival ~ Normal(T(t), sigma)

`t` = pickup delay + delivery minutes. `half_life` = packaging half-life x food-category factor.

## Threshold
Default `min_serving_temp_c = 57`. The FDA Food Code sets hot holding at 135 F (57 C) or above, and
Germany's BfR recommends at least 60 C. This is a food-safety anchor. What customers perceive as
"hot" is unmeasured; heat ratings should refine it. Short delivery times are within the Food Code's
4-hour window, so a risk score is a quality signal, not a safety verdict.

## Assumptions (defaults, NOT measured)
- Packaging half-lives: insulated 70, foil 50, standard 40, paper 30, open box 25 minutes
- Category factors: 0.6 (fries) to 1.3 (soup); unknown categories use 1.0
- Initial food temperature 75 C; error band sigma 5 C

## Calibration
`python -m app.ml.calibrate data.csv` fits half-lives and category factors by least squares in
temperature space, reports 95% bootstrap CIs, scores on a held-out 20% against the assumed defaults,
and writes `temp_uncertainty_c = max(in-sample, held-out error)` so the stated error is never optimistic.

## Evidence so far
Synthetic data only (seeded, 400 rows, 2 C noise): error fell from 4.5 C (assumed constants) to 2.0 C,
equal to the injected noise. This verifies the fitting code. **It says nothing about real accuracy.**
Real-data results go here once collected.

## Limits and failure modes
- One-lump model: ignores portion size, container shape, batching, reheating, and humidity
- Packaging half-life CIs are conditional on the assumed category factors
- Probabilities are only as good as the error band; recalibrate when packaging or seasons change
- Never use the score to deny a refund. Customer reports go to review regardless
