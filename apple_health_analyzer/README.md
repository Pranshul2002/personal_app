# Apple Health Analyzer

Analyze your Apple Health export and print a daily summary for any number of past days.

## How to export your Apple Health data

1. Open the **Health** app on your iPhone.
2. Tap your profile picture (top-right).
3. Scroll down and tap **Export All Health Data**.
4. Tap **Export** and share/save the resulting `export.zip`.

## Requirements

Python 3.10+ only. No third-party packages needed — the script uses the standard library.

## Usage

```bash
python analyze.py <export.zip or export.xml> <days>
```

### Examples

```bash
# Last 7 days from a zip export
python analyze.py export.zip 7

# Last 30 days from an unpacked XML file
python analyze.py apple_health_export/export.xml 30

# Last 90 days
python analyze.py export.zip 90
```

## Sample output

```
Loading: export.zip  (analysing last 7 day(s))

==============================================================
  Apple Health Summary  ·  Last 7 day(s)
  2026-05-09  →  2026-05-16
==============================================================

──────────────────────────────────────────────────────────────
  2026-05-15
──────────────────────────────────────────────────────────────
  Steps                                9,843 steps
  Distance Walk/Run                    7.21 km
  Active Energy Burned                 512 kcal
  Basal Energy Burned                  1,823 kcal
  Heart Rate                           72.4 bpm (avg of 48 readings)
  Resting Heart Rate                   58.0 bpm (avg of 1 readings)
  HRV (SDNN)                           42.3 ms (avg of 1 readings)
  Blood Oxygen (SpO2)                  98.2 % (avg of 6 readings)
  Flights Climbed                      8 flights
  Exercise Time                        35 min
  Stand Time                           10 min
  Sleep                                7h 23m

  Workouts:
    • Running                          32 min  420 kcal  5.10 km
```

## Metrics tracked

| Category       | Metrics |
|----------------|---------|
| Activity       | Steps, Distance (Walk/Run/Cycling/Swimming), Flights Climbed, Exercise Time, Stand Time |
| Energy         | Active & Basal Energy Burned |
| Heart          | Heart Rate, Resting HR, Walking HR Avg, HRV (SDNN) |
| Vitals         | Respiratory Rate, Blood Oxygen (SpO2), Blood Pressure |
| Body           | Weight, BMI, Body Fat %, Lean Body Mass, VO2 Max |
| Nutrition      | Energy, Protein, Carbs, Fat, Water, Alcoholic Beverages |
| Sleep          | Total asleep time per night (Core + Deep + REM) |
| Mindfulness    | Mindful Session minutes |
| Workouts       | All workout types with duration, energy, distance |
