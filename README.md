# Ember 

**Stop eating cold delivery food.**

Ember is a heat-aware food-delivery intelligence layer designed to predict whether a meal will arrive hot, identify where heat is being lost, and help customers, restaurants, and delivery partners act before the experience goes bad.

> **Core idea:** Don't measure food temperature after the problem happens. Predict the risk of a cold meal before it reaches the customer.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload   # interactive docs: http://localhost:8000/docs
```

Docker: `docker build -t ember . && docker run -p 8000:8000 ember`
Quality gate: `ruff check . && ruff format --check . && mypy app && pytest`
Calibrate with real probe data: `python -m app.ml.calibrate measurements.csv` (see `docs/measurement-protocol.md`)
Context for AI agents and contributors: `AGENTS.md`, `docs/NEXT.md`

## Status and honesty

Ember v0.1 predicts with **Newton's law of cooling** (`app/services/cooling.py`), not machine learning.

- Cooling constants (packaging half-lives, food factors) are **assumed until you calibrate them** with real probe measurements (`app/ml/calibrate.py`). The calibration code is verified on synthetic data only, which proves the code, not real-world accuracy.
- The 57 C threshold is the FDA Food Code hot-holding minimum, a safety anchor rather than a measure of what customers call hot. See `docs/model-card.md`.
- `heat_risk` is P(arrival temperature < serving minimum) under a Normal uncertainty band. It expresses model uncertainty, not measured accuracy.
- `risk_factors` use leave-one-out attribution (re-run the model with one factor fixed). Contributions overlap, so they do not sum to the risk.
- A customer's `cold` rating always goes to `refund_review`. The model only reports whether it agrees. Ratings are **not persisted yet**.
- Persistence and any ML on top of physics come next (see `docs/NEXT.md`). ML ships only if it beats calibrated physics on held-out real data.

## Why Ember?

Food can leave a restaurant hot and still arrive cold because of preparation time, pickup delays, rider travel time, traffic, weather, packaging, restaurant-to-customer distance, and batching.

Today's delivery experience mostly optimizes for **time and logistics**. Ember adds another objective: **food heat retention**.

## What Ember Does

-  **Heat Risk Prediction** — estimates the probability that an order will arrive below an acceptable serving temperature.
-  **Delay Detection** — identifies orders spending too long between preparation, pickup, and delivery.
-  **Packaging Intelligence** — learns which restaurant/package combinations retain heat better.
-  **Rider Delay Signals** — detects unusually slow delivery segments and surfaces actionable nudges.
-  **Cold-Meal Refund Automation** — supports rule-based or model-assisted refund decisions.
-  **Crowdsourced Heat Ratings** — lets customers report whether food arrived hot, warm, lukewarm, or cold.
-  **Restaurant Heat Analytics** — shows restaurants where heat loss is occurring and which interventions help.
-  **Delivery Platform Integration** — designed as an API/service that could sit alongside existing delivery platforms rather than replacing them.

## MVP

The first version should stay brutally simple:

1. Customer/order data enters Ember.
2. Ember calculates a **Cold Food Risk Score**.
3. The system identifies the main risk factors.
4. A recommendation is generated: `none`, `nudge`, or `priority_pickup`. A customer `cold` rating is routed to `refund_review`.
5. The customer can submit a post-delivery heat rating.
6. Ratings feed the prediction model and restaurant analytics.

### Example

```text
Order placed
    ↓
Restaurant prep estimate
    ↓
Pickup ETA + route + distance + weather
    ↓
┌─────────────────────────────┐
│     Ember Heat Engine        │
│                             │
│  Heat Risk: 82%           │
│  Main risk: pickup delay    │
│  Expected arrival: 38 min  │
└─────────────────────────────┘
    ↓
Action: prioritize pickup / notify rider
    ↓
Delivery
    ↓
Customer heat rating
    ↓
Feedback → model improvement
```

## Architecture

Ember is initially designed as a modular Python service so the prediction logic can evolve independently from APIs, integrations, and the user interface.

```text
                    ┌────────────────────┐
                    │ Delivery Platform  │
                    │ / Restaurant Data  │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │    Ember API       │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   Heat Prediction       Delay Analysis      Rating System
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌────────────────────┐
                    │ Decision / Actions │
                    │ nudge • priority   │
                    │ refund • analytics │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │ Database / Events  │
                    └────────────────────┘
```

## Project Structure

```text
Ember/
├── app/
│   ├── api/                 # HTTP/API routes
│   ├── core/                # Configuration and shared infrastructure
│   ├── ml/                  # Calibration from measured data
│   ├── models/              # Domain and API schemas
│   ├── services/            # Business logic
│   │   ├── cooling.py
│   │   ├── heat_prediction.py
│   │   ├── delay_analysis.py
│   │   ├── refund_engine.py
│   │   └── rating_engine.py
│   └── main.py              # Application entry point
├── data/
│   ├── raw/                 # Raw datasets (gitignored)
│   └── processed/           # Processed datasets (gitignored)
├── models/                  # Trained model artifacts (gitignored)
├── tests/                   # Automated tests
├── docs/                    # Architecture and research notes
├── .env.example
├── .gitignore
├── pyproject.toml
├── LICENSE
└── README.md
```

## Heat Risk Model

The initial model does not need expensive deep learning. Start with interpretable features:

| Feature | Why it matters |
|---|---|
| Preparation time | Food cools while waiting to be completed |
| Pickup delay | Hot food sitting idle is a major risk |
| Delivery duration | Longer exposure generally increases cooling |
| Restaurant-customer distance | More travel means more heat loss |
| Weather | Ambient temperature affects cooling |
| Packaging type | Insulation strongly affects retention |
| Food category | Different meals cool at different rates |
| Order batching | Extra stops can increase delivery time |
| Historical restaurant performance | Captures recurring operational problems |
| Historical rider/route delay | Captures predictable logistics risk |

The first prediction target can be:

```text
P(cold_on_arrival | order, restaurant, route, weather, packaging, timing)
```

Later versions can use survival analysis, gradient boosting, time-series features, or physics-informed cooling models.

## Suggested API

### Predict heat risk

```http
POST /api/v1/predictions/heat-risk
```

```json
{
  "restaurant_id": "rest_123",
  "food_category": "biryani",
  "distance_km": 7.2,
  "estimated_delivery_minutes": 36,
  "pickup_delay_minutes": 8,
  "packaging_type": "standard",
  "ambient_temperature_c": 31
}
```

Example response:

```json
{
  "heat_risk": 0.705,
  "risk_level": "high",
  "expected_state": "lukewarm_or_cold",
  "recommended_action": "priority_pickup",
  "predicted_arrival_temp_c": 54.3,
  "primary_risk_factor": "packaging",
  "risk_factors": [
    {"name": "packaging", "contribution": 0.526},
    {"name": "delivery_duration", "contribution": 0.454},
    {"name": "pickup_delay", "contribution": 0.218}
  ]
}
```

### Submit a heat rating

```http
POST /api/v1/ratings
```

```json
{
  "order_id": "ord_123",
  "temperature_rating": "cold",
  "packaging_rating": 2,
  "predicted_heat_risk": 0.82
}
```

`predicted_heat_risk` is optional. Response: `{"order_id": "ord_123", "temperature_rating": "cold", "refund_decision": "refund_review", "model_corroborated": true}`

## Development Roadmap

### Phase 1 — Foundation

- [x] Repository created
- [x] Project structure
- [x] FastAPI service
- [x] Health endpoint
- [x] Order schema
- [x] Heat-risk API

### Phase 2 — Prediction MVP

- [ ] Synthetic order dataset
- [x] Baseline cooling model
- [ ] Feature engineering
- [ ] Baseline ML model
- [ ] Evaluation pipeline
- [x] Explainable risk factors

### Phase 3 — Product Layer

- [ ] Customer heat rating
- [ ] Restaurant dashboard
- [x] Refund rules engine
- [x] Calibration pipeline (probe-data CSV to fitted constants)
- [ ] Rider delay detection
- [ ] Event logging

### Phase 4 — Real-World Validation

- [ ] Collect real delivery data
- [ ] Partner with restaurants
- [ ] Compare predicted vs reported temperature
- [ ] Measure refund reduction
- [ ] Measure customer satisfaction

## Metrics

Ember should optimize for measurable outcomes, not just model accuracy.

**Model metrics**

- ROC-AUC / PR-AUC
- Calibration error
- Brier score
- MAE for temperature prediction

**Product metrics**

- Cold-order rate
- Average delivery heat rating
- False refund rate
- Refund cost per order
- Pickup-delay reduction
- Customer complaint reduction

## Research Direction

A strong research angle is **disruption-aware food temperature prediction for last-mile delivery**: combining delivery events, route characteristics, environmental conditions, packaging, and historical feedback to predict thermal quality at arrival.

This can eventually become both a research project and a deployable product.

## Contributing

Ember is being developed incrementally. Start with the smallest useful component, add tests, and keep the prediction system explainable.

## License

MIT  2026 DHARAVATH SATVIK
