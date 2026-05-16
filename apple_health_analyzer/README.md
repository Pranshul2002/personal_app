# Apple Health Analyzer

Analyze your Apple Health export and print a daily summary for any number of past days. The full pipeline runs automatically: an iOS Shortcut exports data to iCloud, and a Mac background watcher processes it the moment the file arrives.

## Quick start (manual)

```bash
# last 1 day (default)
python analyze.py export.zip

# last 7 days, save report to file
python analyze.py export.zip 7 -o report.txt

# last 30 days
python analyze.py export.zip 30
```

No third-party packages needed — pure Python 3.10+ standard library.

---

## Automated pipeline

```
iPhone Health app
      │  (iOS Shortcut runs on schedule)
      ▼
iCloud Drive  ~/HealthExports/export.zip
      │  (Mac launchd detects new file)
      ▼
run.sh → analyze.py
      │
      ▼
~/HealthData/YYYY-MM-DD.txt
```

### Step 1 — iOS Shortcut (on your iPhone)

1. Open the **Shortcuts** app.
2. Tap **+** to create a new shortcut.
3. Add these actions in order:

   | # | Action | Setting |
   |---|--------|---------|
   | 1 | **Export Health Data** | (built-in action — search "Export Health") |
   | 2 | **Save File** | Location: **iCloud Drive → HealthExports** · filename: `export.zip` · overwrite: on |

4. Tap the shortcut name → **Add to Home Screen** (optional).
5. To schedule it, go to the **Automation** tab → **+** → **Time of Day** (e.g. every morning at 07:00) → select your shortcut → turn off "Ask Before Running".

> The first run will ask for permission to access Health data — tap **Allow All**.

### Step 2 — Mac watcher (one-time setup)

```bash
cd apple_health_analyzer
bash install_watcher.sh          # default: 1 day
# or
bash install_watcher.sh 7        # analyse last 7 days
```

This:
- Creates `~/Library/Mobile Documents/com~apple~CloudDocs/HealthExports/` (the iCloud folder your Shortcut saves to)
- Installs a **launchd** agent that watches that folder
- Runs `run.sh` automatically whenever iCloud delivers a new `export.zip`
- Saves each report to `~/HealthData/YYYY-MM-DD.txt`

### Checking logs

```bash
tail -f /tmp/healthanalyzer.log   # stdout
tail -f /tmp/healthanalyzer.err   # errors
```

### Uninstalling the watcher

```bash
launchctl unload ~/Library/LaunchAgents/com.healthanalyzer.watcher.plist
rm ~/Library/LaunchAgents/com.healthanalyzer.watcher.plist
```

---

## Metrics tracked

| Category    | Metrics |
|-------------|---------|
| Activity    | Steps, Distance (Walk/Run/Cycling/Swimming), Flights Climbed, Exercise Time, Stand Time |
| Energy      | Active & Basal Energy Burned |
| Heart       | Heart Rate, Resting HR, Walking HR Avg, HRV (SDNN) |
| Vitals      | Respiratory Rate, Blood Oxygen (SpO2), Blood Pressure |
| Body        | Weight, BMI, Body Fat %, Lean Body Mass, VO2 Max |
| Nutrition   | Energy, Protein, Carbs, Fat, Water, Alcoholic Beverages |
| Sleep       | Total asleep time per night (Core + Deep + REM) |
| Mindfulness | Mindful Session minutes |
| Workouts    | All workout types with duration, energy burned, distance |
