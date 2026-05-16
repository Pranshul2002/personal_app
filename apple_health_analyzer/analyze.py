#!/usr/bin/env python3
"""
Apple Health Data Analyzer

Usage:
    python analyze.py <export.zip or export.xml> <days>

Example:
    python analyze.py export.zip 7
    python analyze.py export.xml 30
"""

import xml.etree.ElementTree as ET
import zipfile
import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional


# ─── Label + unit for every recognised metric ───────────────────────────────
METRIC_LABELS: dict[str, tuple[str, str]] = {
    "HKQuantityTypeIdentifierStepCount":                     ("Steps",                    "steps"),
    "HKQuantityTypeIdentifierDistanceWalkingRunning":        ("Distance Walk/Run",        "km"),
    "HKQuantityTypeIdentifierDistanceCycling":               ("Distance Cycling",         "km"),
    "HKQuantityTypeIdentifierDistanceSwimming":              ("Distance Swimming",        "m"),
    "HKQuantityTypeIdentifierActiveEnergyBurned":            ("Active Energy Burned",     "kcal"),
    "HKQuantityTypeIdentifierBasalEnergyBurned":             ("Basal Energy Burned",      "kcal"),
    "HKQuantityTypeIdentifierHeartRate":                     ("Heart Rate",               "bpm"),
    "HKQuantityTypeIdentifierRestingHeartRate":              ("Resting Heart Rate",       "bpm"),
    "HKQuantityTypeIdentifierWalkingHeartRateAverage":       ("Walking Heart Rate Avg",   "bpm"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN":      ("HRV (SDNN)",               "ms"),
    "HKQuantityTypeIdentifierRespiratoryRate":               ("Respiratory Rate",         "breaths/min"),
    "HKQuantityTypeIdentifierOxygenSaturation":              ("Blood Oxygen (SpO2)",      "%"),
    "HKQuantityTypeIdentifierBloodPressureSystolic":         ("Blood Pressure Systolic",  "mmHg"),
    "HKQuantityTypeIdentifierBloodPressureDiastolic":        ("Blood Pressure Diastolic", "mmHg"),
    "HKQuantityTypeIdentifierBodyMass":                      ("Body Mass",                "kg"),
    "HKQuantityTypeIdentifierBodyFatPercentage":             ("Body Fat",                 "%"),
    "HKQuantityTypeIdentifierBodyMassIndex":                 ("BMI",                      ""),
    "HKQuantityTypeIdentifierLeanBodyMass":                  ("Lean Body Mass",           "kg"),
    "HKQuantityTypeIdentifierFlightsClimbed":                ("Flights Climbed",          "flights"),
    "HKQuantityTypeIdentifierAppleExerciseTime":             ("Exercise Time",            "min"),
    "HKQuantityTypeIdentifierAppleStandTime":                ("Stand Time",               "min"),
    "HKQuantityTypeIdentifierVO2Max":                        ("VO2 Max",                  "mL/kg/min"),
    "HKQuantityTypeIdentifierDietaryEnergyConsumed":         ("Dietary Energy",           "kcal"),
    "HKQuantityTypeIdentifierDietaryProtein":                ("Dietary Protein",          "g"),
    "HKQuantityTypeIdentifierDietaryCarbohydrates":          ("Dietary Carbs",            "g"),
    "HKQuantityTypeIdentifierDietaryFatTotal":               ("Dietary Fat",              "g"),
    "HKQuantityTypeIdentifierDietaryWater":                  ("Water Intake",             "mL"),
    "HKQuantityTypeIdentifierNumberOfAlcoholicBeverages":    ("Alcoholic Beverages",      "drinks"),
    "HKQuantityTypeIdentifierMindfulSession":                ("Mindful Session",          "min"),
    "HKQuantityTypeIdentifierNikeFuel":                      ("Nike Fuel",                "NikeFuel"),
}

# Metrics that are averaged per day (not summed)
AVERAGE_METRICS: set[str] = {
    "HKQuantityTypeIdentifierHeartRate",
    "HKQuantityTypeIdentifierRestingHeartRate",
    "HKQuantityTypeIdentifierWalkingHeartRateAverage",
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
    "HKQuantityTypeIdentifierRespiratoryRate",
    "HKQuantityTypeIdentifierOxygenSaturation",
    "HKQuantityTypeIdentifierBloodPressureSystolic",
    "HKQuantityTypeIdentifierBloodPressureDiastolic",
    "HKQuantityTypeIdentifierBodyMass",
    "HKQuantityTypeIdentifierBodyFatPercentage",
    "HKQuantityTypeIdentifierBodyMassIndex",
    "HKQuantityTypeIdentifierLeanBodyMass",
    "HKQuantityTypeIdentifierVO2Max",
}


def load_health_xml(path: str) -> ET.Element:
    """Load Apple Health XML from a .zip export or a raw export.xml file."""
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path, "r") as z:
            xml_name = next(
                (n for n in z.namelist() if n.endswith("export.xml")), None
            )
            if not xml_name:
                raise FileNotFoundError(
                    "export.xml not found inside the zip archive. "
                    "Make sure you are using a direct Apple Health export."
                )
            with z.open(xml_name) as f:
                return ET.parse(f).getroot()
    else:
        return ET.parse(path).getroot()


def _parse_dt(date_str: str) -> Optional[datetime]:
    """Parse the Apple Health date format into a timezone-aware datetime."""
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


# Sleep category values that count as "asleep"
_ASLEEP_VALUES = {
    "HKCategoryValueSleepAnalysisAsleep",
    "HKCategoryValueSleepAnalysisAsleepCore",
    "HKCategoryValueSleepAnalysisAsleepDeep",
    "HKCategoryValueSleepAnalysisAsleepREM",
}


def analyze(root: ET.Element, days: int) -> None:
    """Parse the XML tree and print a daily health summary."""
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(days=days)

    # daily_data[date][metric] = list of float values
    daily_data: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    sleep_hours: dict[str, float] = defaultdict(float)
    workouts: dict[str, list[dict]] = defaultdict(list)

    # ── Records ──────────────────────────────────────────────────────────────
    for rec in root.iter("Record"):
        rtype = rec.get("type", "")
        start_dt = _parse_dt(rec.get("startDate", ""))
        if start_dt is None or start_dt < cutoff:
            continue

        date_key = start_dt.strftime("%Y-%m-%d")

        # Sleep is a category with non-numeric values
        if rtype == "HKCategoryTypeIdentifierSleepAnalysis":
            if rec.get("value", "") in _ASLEEP_VALUES:
                end_dt = _parse_dt(rec.get("endDate", ""))
                if end_dt:
                    sleep_hours[date_key] += (
                        end_dt - start_dt
                    ).total_seconds() / 3600
            continue

        if rtype not in METRIC_LABELS:
            continue

        try:
            daily_data[date_key][rtype].append(float(rec.get("value", "")))
        except (ValueError, TypeError):
            continue

    # ── Workouts ─────────────────────────────────────────────────────────────
    for w in root.iter("Workout"):
        start_dt = _parse_dt(w.get("startDate", ""))
        if start_dt is None or start_dt < cutoff:
            continue
        date_key = start_dt.strftime("%Y-%m-%d")
        workouts[date_key].append(
            {
                "type": w.get("workoutActivityType", "").replace(
                    "HKWorkoutActivityType", ""
                ),
                "duration": float(w.get("duration") or 0),
                "energy": float(w.get("totalEnergyBurned") or 0),
                "distance": float(w.get("totalDistance") or 0),
            }
        )

    # ── Output ───────────────────────────────────────────────────────────────
    all_dates = sorted(
        set(daily_data) | set(sleep_hours) | set(workouts),
        reverse=True,
    )

    if not all_dates:
        print(f"No Apple Health data found in the last {days} day(s).")
        return

    W = 62
    print("=" * W)
    print(f"  Apple Health Summary  ·  Last {days} day(s)")
    print(
        f"  {cutoff.strftime('%Y-%m-%d')}  →  {now.strftime('%Y-%m-%d')}"
    )
    print("=" * W)

    for date_key in all_dates:
        print(f"\n{'─' * W}")
        print(f"  {date_key}")
        print(f"{'─' * W}")

        metrics = daily_data.get(date_key, {})

        for rtype, (label, unit) in METRIC_LABELS.items():
            if rtype not in metrics:
                continue
            values = metrics[rtype]
            if rtype in AVERAGE_METRICS:
                val = f"{sum(values) / len(values):.1f}"
                suffix = f"{unit} (avg of {len(values)} readings)"
            else:
                val = f"{sum(values):,.0f}"
                suffix = unit
            print(f"  {label:<36} {val} {suffix}")

        if date_key in sleep_hours:
            h = sleep_hours[date_key]
            print(
                f"  {'Sleep':<36} {int(h)}h {int((h % 1) * 60)}m"
            )

        if date_key in workouts:
            print()
            print("  Workouts:")
            for w in workouts[date_key]:
                dur = f"{w['duration']:.0f} min"
                parts = [f"{w['energy']:.0f} kcal" if w["energy"] else "",
                         f"{w['distance']:.2f} km" if w["distance"] else ""]
                extras = "  ".join(p for p in parts if p)
                print(f"    • {w['type']:<28} {dur}  {extras}")

    print(f"\n{'=' * W}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze Apple Health export data for the last X days.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python analyze.py export.zip 7\n"
            "  python analyze.py apple_health_export/export.xml 30"
        ),
    )
    parser.add_argument(
        "export",
        help="Path to Apple Health export.zip or export.xml",
    )
    parser.add_argument(
        "days",
        type=int,
        help="Number of past days to include (e.g. 7, 30, 90)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.export):
        print(f"Error: file not found — {args.export}", file=sys.stderr)
        sys.exit(1)

    if args.days < 1:
        print("Error: days must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {args.export}  (analysing last {args.days} day(s))\n")
    root = load_health_xml(args.export)
    analyze(root, args.days)


if __name__ == "__main__":
    main()
