# Ember 🔥

**Stop eating cold delivery food.**

Ember is a heat-aware food-delivery intelligence layer designed to predict whether a meal will arrive hot, identify where heat is being lost, and help customers, restaurants, and delivery partners act before the experience goes bad.

> **Core idea:** Don't measure food temperature after the problem happens. Predict the risk of a cold meal before it reaches the customer.

## Why Ember?

Food can leave a restaurant hot and still arrive cold because of preparation time, pickup delays, rider travel time, traffic, weather, packaging, restaurant-to-customer distance, and batching.

Today's delivery experience mostly optimizes for **time and logistics**. Ember adds another objective: **food heat retention**.

## What Ember Does

- 🌡️ **Heat Risk Prediction** — estimates the probability that an order will arrive below an acceptable serving temperature.
- ⏱️ **Delay Detection** — identifies orders spending too long between preparation, pickup, and delivery.
- 📦 **Packaging Intelligence** — learns which restaurant/package combinations retain heat better.
- 🛵 **Rider Delay Signals** — detects unusually slow delivery segments and surfaces actionable nudges.
- 💸 **Cold-Meal Refund Automation** — supports rule-based or model-assisted refund decisions.
- ⭐ **Crowdsourced Heat Ratings** — lets customers report whether food arrived hot, warm, lukewarm, or cold.
- 📊 **Restaurant Heat Analytics** — shows restaurants where heat loss is occurring and which interventions help.
- 🔌 **Delivery Platform Integration** — designed as an API/service that could sit alongside existing delivery platforms rather than replacing them.

## MVP

The first version should stay brutally simple:

1. Customer/order data enters Ember.
2. Ember calculates a **Cold Food Risk Score**.
3. The system identifies the main risk factors.
4. A recommendation is generated: `none`, `nudge`, `priority`, or `refund review`.
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
│  Heat Risk: 82% 🔥          │
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
│   ├── models/              # Domain and API schemas
│   ├── services/            # Business logic
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
  "heat_risk": 0.82,
  "risk_level": "high",
  "expected_state": "lukewarm_or_cold",
  "recommended_action": "priority_pickup"
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
  "packaging_rating": 2
}
```

## Development Roadmap

### Phase 1 — Foundation

- [x] Repository created
- [ ] Project structure
- [ ] FastAPI service
- [ ] Health endpoint
- [ ] Order schema
- [ ] Heat-risk API

### Phase 2 — Prediction MVP

- [ ] Synthetic order dataset
- [ ] Baseline cooling model
- [ ] Feature engineering
- [ ] Baseline ML model
- [ ] Evaluation pipeline
- [ ] Explainable risk factors

### Phase 3 — Product Layer

- [ ] Customer heat rating
- [ ] Restaurant dashboard
- [ ] Refund rules engine
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

MIT © 2026 DHARAVATH SATVIK
