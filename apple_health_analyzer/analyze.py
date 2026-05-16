#!/usr/bin/env python3
"""
Apple Health Data Analyzer

Usage:
    python analyze.py <export.zip or export.xml> [days] [--output FILE]

Examples:
    python analyze.py export.zip            # last 1 day (default)
    python analyze.py export.zip 7          # last 7 days
    python analyze.py export.zip 30 -o report.txt
"""

import xml.etree.ElementTree as ET
import zipfile
import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional, TextIO


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
}

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

_ASLEEP_VALUES = {
    "HKCategoryValueSleepAnalysisAsleep",
    "HKCategoryValueSleepAnalysisAsleepCore",
    "HKCategoryValueSleepAnalysisAsleepDeep",
    "HKCategoryValueSleepAnalysisAsleepREM",
}


def load_health_xml(path: str) -> ET.Element:
    if path.lower().endswith(".zip"):
        with zipfile.ZipFile(path, "r") as z:
            xml_name = next(
                (n for n in z.namelist() if n.endswith("export.xml")), None
            )
            if not xml_name:
                raise FileNotFoundError(
                    "export.xml not found inside the zip. "
                    "Make sure you are using a direct Apple Health export."
                )
            with z.open(xml_name) as f:
                return ET.parse(f).getroot()
    return ET.parse(path).getroot()


def _parse_dt(date_str: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def analyze(root: ET.Element, days: int, out: TextIO = sys.stdout) -> None:
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(days=days)

    daily_data: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    sleep_hours: dict[str, float] = defaultdict(float)
    workouts: dict[str, list[dict]] = defaultdict(list)

    for rec in root.iter("Record"):
        rtype = rec.get("type", "")
        start_dt = _parse_dt(rec.get("startDate", ""))
        if start_dt is None or start_dt < cutoff:
            continue
        date_key = start_dt.strftime("%Y-%m-%d")

        if rtype == "HKCategoryTypeIdentifierSleepAnalysis":
            if rec.get("value", "") in _ASLEEP_VALUES:
                end_dt = _parse_dt(rec.get("endDate", ""))
                if end_dt:
                    sleep_hours[date_key] += (end_dt - start_dt).total_seconds() / 3600
            continue

        if rtype not in METRIC_LABELS:
            continue
        try:
            daily_data[date_key][rtype].append(float(rec.get("value", "")))
        except (ValueError, TypeError):
            continue

    for w in root.iter("Workout"):
        start_dt = _parse_dt(w.get("startDate", ""))
        if start_dt is None or start_dt < cutoff:
            continue
        date_key = start_dt.strftime("%Y-%m-%d")
        workouts[date_key].append({
            "type": w.get("workoutActivityType", "").replace("HKWorkoutActivityType", ""),
            "duration": float(w.get("duration") or 0),
            "energy": float(w.get("totalEnergyBurned") or 0),
            "distance": float(w.get("totalDistance") or 0),
        })

    all_dates = sorted(
        set(daily_data) | set(sleep_hours) | set(workouts),
        reverse=True,
    )

    def p(line: str = "") -> None:
        print(line, file=out)

    W = 62
    if not all_dates:
        p(f"No Apple Health data found in the last {days} day(s).")
        return

    p("=" * W)
    p(f"  Apple Health Summary  ·  Last {days} day(s)")
    p(f"  {cutoff.strftime('%Y-%m-%d')}  →  {now.strftime('%Y-%m-%d')}")
    p("=" * W)

    for date_key in all_dates:
        p(f"\n{'─' * W}")
        p(f"  {date_key}")
        p(f"{'─' * W}")

        metrics = daily_data.get(date_key, {})
        for rtype, (label, unit) in METRIC_LABELS.items():
            if rtype not in metrics:
                continue
            values = metrics[rtype]
            if rtype in AVERAGE_METRICS:
                val = f"{sum(values)/len(values):.1f}"
                suffix = f"{unit} (avg of {len(values)} readings)"
            else:
                val = f"{sum(values):,.0f}"
                suffix = unit
            p(f"  {label:<36} {val} {suffix}")

        if date_key in sleep_hours:
            h = sleep_hours[date_key]
            p(f"  {'Sleep':<36} {int(h)}h {int((h % 1) * 60)}m")

        if date_key in workouts:
            p()
            p("  Workouts:")
            for w in workouts[date_key]:
                dur = f"{w['duration']:.0f} min"
                parts = [
                    f"{w['energy']:.0f} kcal" if w["energy"] else "",
                    f"{w['distance']:.2f} km" if w["distance"] else "",
                ]
                extras = "  ".join(x for x in parts if x)
                p(f"    • {w['type']:<28} {dur}  {extras}")

    p(f"\n{'=' * W}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze Apple Health export data for the last X days.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python analyze.py export.zip           # last 1 day\n"
            "  python analyze.py export.zip 7         # last 7 days\n"
            "  python analyze.py export.zip 30 -o report.txt"
        ),
    )
    parser.add_argument("export", help="Path to export.zip or export.xml")
    parser.add_argument(
        "days",
        nargs="?",
        type=int,
        default=1,
        help="Number of past days to include (default: 1)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Save output to this file (in addition to stdout)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.export):
        print(f"Error: file not found — {args.export}", file=sys.stderr)
        sys.exit(1)
    if args.days < 1:
        print("Error: days must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {args.export}  (last {args.days} day(s))\n")
    root = load_health_xml(args.export)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w") as f:
            analyze(root, args.days, out=sys.stdout)
            # re-run to write to file (fast — XML already parsed)
            f.seek(0)
            analyze(root, args.days, out=f)
        print(f"Report saved to: {args.output}")
    else:
        analyze(root, args.days)


if __name__ == "__main__":
    main()
