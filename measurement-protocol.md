# Measurement protocol (collecting real calibration data)

Goal: rows of real cooling that `app.ml.calibrate` can fit. No restaurant partnership is needed:
use takeaway you collect yourself.

## Equipment
- Digital probe thermometer (about +/-1 C), alcohol wipes, phone clock, ambient temperature from a weather app or a thermometer

## Per observation
1. **At pickup**, right after the food is packed: probe the centre of the food, record `initial_temp_c`, note the time.
2. Keep the container closed and travel normally.
3. **On arrival**: probe the same spot and depth, record `measured_temp_c`, note the time.
4. `exposure_minutes` = minutes between the two probes. Record `ambient_c`, `packaging_type`, `food_category`.
5. Wipe the probe with alcohol between uses. Do not serve probed portions to others.

## CSV format (header required)
```
packaging_type,food_category,ambient_c,initial_temp_c,exposure_minutes,measured_temp_c
standard,biryani,31,74,38,56
```
Packaging: insulated, foil, standard, paper, open_box, unknown. Categories are free text (lower-cased).

## How much data
- At least 8 rows per packaging type is the minimum to fit it; **30+ is recommended**
- Vary distance, time of day, and weather. Do not collect everything on one route or day
- Rows with gross errors (impossible temperatures, no cooling signal) are rejected and counted

## Run
```bash
python -m app.ml.calibrate measurements.csv -o calibration.json
EMBER_CALIBRATION_PATH=calibration.json uvicorn app.main:app
```
Read the held-out error line. If it is not clearly below the assumed-defaults error, collect more data before trusting the output.
