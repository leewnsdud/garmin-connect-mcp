# Garmin Running MCP Server

MCP (Model Context Protocol) server that provides Garmin Connect running data.
Use this server for running training analysis, planning, and workout creation.

All API responses are automatically filtered to remove personally identifiable information (PII) such as owner names, profile IDs, and GPS coordinates via the `sanitize.strip_pii()` module.

---

## Project structure

```
src/garmin_mcp/
  __init__.py          # FastMCP server entrypoint, stdio transport
  auth.py              # OAuth authentication (token -> credentials fallback)
  client.py            # Garmin API wrapper (429 retry, date validation)
  sanitize.py          # PII filtering (strips owner info, GPS coordinates)
  tools/
    __init__.py        # Tool module registration
    activities.py      # Activity query/detail (4 tools)
    summary.py         # Weekly/monthly summary (2 tools)
    training.py        # Training metrics (5 tools)
    heart_rate.py      # Heart rate/HRV (3 tools)
    wellness.py        # Sleep/stress/body battery (3 tools)
    records.py         # PR/goals (2 tools)
    workout.py         # Workout creation/listing (2 tools)
    gear.py            # Running shoe management (1 tool)
scripts/
  auth.py              # Pre-auth CLI (run once for initial setup)
```

## Setup

```sh
uv sync                            # Install dependencies
uv run python scripts/auth.py      # Garmin auth (run once)
uv run garmin-mcp                  # Start MCP server
```

## Build & reinstall

After code changes, you must reinstall for them to take effect:

```sh
uv sync --reinstall-package garmin-mcp
```

MCP clients (e.g. Claude Desktop) must restart the server process to pick up new code.

---

## MCP tools reference

22 tools total. All date parameters use `YYYY-MM-DD` format, defaulting to today.

---

### Activities (4 tools)

#### `get_recent_activities`

Returns recent running activities with key metrics. Non-running activities are filtered out.

**Parameters:** `count: int = 20` (max 100)
**Returns:** `list[dict]`

**Example request:**
```
Get my last 2 running activities
```

**Example response:**
```json
[
  {
    "activity_id": 21892408004,
    "name": "Running",
    "date": "2026-02-17 14:29:01",
    "type": "running",
    "distance_km": 5.76,
    "duration_seconds": 1948.8,
    "moving_duration_seconds": 1945.7,
    "avg_pace": "5:38",
    "max_pace": "5:12",
    "avg_heart_rate": 158,
    "max_heart_rate": 170,
    "avg_cadence": 175.5,
    "max_cadence": 184,
    "avg_stride_length_cm": 100.5,
    "avg_ground_contact_time_ms": 254.5,
    "avg_vertical_oscillation_cm": 8.4,
    "avg_vertical_ratio": 8.3,
    "calories": 426,
    "elevation_gain": 14,
    "elevation_loss": 10,
    "max_elevation": 11.8,
    "min_elevation": 3.8,
    "avg_power": 308,
    "max_power": 456,
    "normalized_power": 309,
    "training_effect_aerobic": 3.6,
    "training_effect_anaerobic": 0,
    "training_load": 112.0,
    "training_effect_label": "TEMPO",
    "vo2max": 51,
    "fastest_split_1km": "5:21",
    "fastest_split_1mile": "8:42",
    "fastest_split_5km": "28:03",
    "hr_zone_1_seconds": 34.0,
    "hr_zone_2_seconds": 164.0,
    "hr_zone_3_seconds": 1384.9,
    "hr_zone_4_seconds": 328.7,
    "hr_zone_5_seconds": 0,
    "steps": 5692,
    "lap_count": 6,
    "is_pr": false,
    "max_temperature": 30,
    "min_temperature": 17
  }
]
```

#### `get_activities_by_date`

Returns running activities within a date range.

**Parameters:** `start_date: str`, `end_date: str`
**Returns:** `list[dict]` (same structure as `get_recent_activities`)

**Example request:**
```
Get running activities from Feb 10-17, 2026
```

#### `get_activity_detail`

Returns full details of a single activity. Uses the detail API which provides additional fields like min heart rate, stride length, and description.

**Parameters:** `activity_id: int`
**Returns:** `dict`

**Example request:**
```
Get details for activity 21892408004
```

**Example response:**
```json
{
  "activity_id": 21892408004,
  "name": "Running",
  "date": "2026-02-17 14:29:01",
  "type": "running",
  "distance_km": 5.76,
  "duration_seconds": 1948.8,
  "avg_pace": "5:38",
  "avg_heart_rate": 158,
  "max_heart_rate": 170,
  "min_heart_rate": 105,
  "avg_cadence": 175,
  "max_cadence": 184,
  "calories": 426,
  "elevation_gain": 14,
  "elevation_loss": 10,
  "min_elevation": 3.8,
  "max_elevation": 11.8,
  "avg_power": 308,
  "max_power": 456,
  "normalized_power": 309,
  "training_effect_aerobic": 3.6,
  "training_effect_anaerobic": 0,
  "training_load": 112.0,
  "training_label": "TEMPO",
  "avg_stride_length": 100.5,
  "avg_vertical_oscillation": 8.4,
  "avg_ground_contact_time": 254.5,
  "avg_vertical_ratio": 8.3,
  "avg_temperature": 22,
  "max_temperature": 30,
  "min_temperature": 17,
  "steps": 5692,
  "description": null
}
```

#### `get_activity_splits`

Returns per-km split data for pacing strategy analysis (positive/negative splits).

**Parameters:** `activity_id: int`
**Returns:** `dict` with `lapDTOs` array

**Example request:**
```
Get splits for activity 21892408004
```

**Example response (abbreviated):**
```json
{
  "activityId": 21892408004,
  "lapDTOs": [
    {
      "lapIndex": 1,
      "distance": 1000,
      "duration": 349.8,
      "averageSpeed": 2.86,
      "averageHR": 144,
      "maxHR": 156,
      "averageRunCadence": 175.3,
      "averagePower": 302,
      "elevationGain": 7,
      "groundContactTime": 254.6,
      "strideLength": 97.3,
      "verticalOscillation": 8.1
    },
    {
      "lapIndex": 2,
      "distance": 1000,
      "duration": 350.6,
      "averageSpeed": 2.85,
      "averageHR": 156,
      "maxHR": 159,
      "averageRunCadence": 175.3,
      "averagePower": 301
    }
  ]
}
```

> Note: Speed is in m/s. To convert to pace (min:sec/km), use `1000 / speed / 60` for minutes.

---

### Summary (2 tools)

#### `get_weekly_running_summary`

Returns weekly running summary with aggregated metrics.

**Parameters:** `end_date: str = ""` (defaults to today), `weeks: int = 1` (max 12)
**Returns:** `list[dict]`

**Example request:**
```
Show my weekly running summary for the last 4 weeks
```

**Example response:**
```json
[
  {
    "week_start": "2026-02-16",
    "week_end": "2026-02-22",
    "total_runs": 1,
    "total_distance_km": 5.76,
    "total_duration_seconds": 1948.8,
    "avg_pace": "5:38",
    "avg_heart_rate": 158,
    "total_elevation_gain": 14,
    "longest_run_km": 5.76,
    "longest_run_pace": "5:38"
  }
]
```

#### `get_monthly_running_summary`

Returns monthly summary with weekly breakdown and month-over-month comparison.

**Parameters:** `year: int = 0`, `month: int = 0` (defaults to current month)
**Returns:** `dict`

**Example request:**
```
Show my February 2026 running summary
```

**Example response:**
```json
{
  "year": 2026,
  "month": 2,
  "total_runs": 4,
  "total_distance_km": 31.33,
  "total_duration_seconds": 11100.8,
  "avg_pace": "5:54",
  "avg_heart_rate": 157.2,
  "total_elevation_gain": 73,
  "longest_run_km": 10.27,
  "longest_run_pace": "6:01",
  "weekly_breakdown": [
    {
      "week_number": 1,
      "week_start": "2026-02-01",
      "week_end": "2026-02-07",
      "total_runs": 1,
      "total_distance_km": 10.27,
      "avg_pace": "6:01"
    }
  ],
  "vs_previous_month": {
    "distance_change_pct": -69.2,
    "runs_change": -5,
    "previous_month_distance_km": 101.78,
    "previous_month_runs": 9
  }
}
```

---

### Training (5 tools)

#### `get_training_status`

Returns current training status classification.

**Parameters:** `date: str = ""`
**Returns:** `dict`

**Example request:**
```
What is my current training status?
```

> Possible values: Productive, Maintaining, Overreaching, Detraining, Recovery, Peaking, Unproductive.

#### `get_training_readiness`

Returns training readiness score based on sleep, recovery, training load, and HRV.

**Parameters:** `date: str = ""`
**Returns:** `list[dict]`

**Example request:**
```
Am I ready to train today?
```

**Example response:**
```json
[
  {
    "calendarDate": "2026-02-19",
    "level": "HIGH",
    "feedbackShort": "WELL_RECOVERED",
    "score": 78,
    "recoveryTime": 1,
    "recoveryTimeFactorPercent": 99,
    "recoveryTimeFactorFeedback": "GOOD",
    "acwrFactorPercent": 90,
    "acwrFactorFeedback": "GOOD",
    "acuteLoad": 221,
    "hrvWeeklyAverage": 51
  }
]
```

> `score` ranges from 0-100. `level` can be LOW, MODERATE, HIGH, PRIME.

#### `get_vo2max_and_fitness`

Returns VO2max estimate and fitness age data. Essential for Jack Daniels VDOT calculation.

**Parameters:** `date: str = ""`
**Returns:** `dict`

**Example request:**
```
What is my current VO2max and fitness age?
```

**Example response:**
```json
{
  "max_metrics": [],
  "fitness_age": {
    "chronologicalAge": 30,
    "fitnessAge": 26.6,
    "achievableFitnessAge": 22.7,
    "components": {
      "vigorousDaysAvg": { "value": 1.5, "targetValue": 3 },
      "rhr": { "value": 59 },
      "bmi": { "value": 24.2, "targetValue": 20.9 }
    }
  }
}
```

#### `get_race_predictions`

Returns predicted race times for 5K, 10K, half marathon, and marathon.

**Parameters:** none
**Returns:** `dict`

**Example request:**
```
What are my predicted race times?
```

**Example response:**
```json
{
  "calendarDate": "2026-02-19",
  "time5K": 1267,
  "time10K": 2603,
  "timeHalfMarathon": 5927,
  "timeMarathon": 13087
}
```

> All times are in **seconds**. 1267s = 21:07 (5K), 2603s = 43:23 (10K), 5927s = 1:38:47 (half), 13087s = 3:38:07 (marathon).

#### `get_lactate_threshold`

Returns lactate threshold heart rate and pace. Critical for threshold training design.

**Parameters:** `start_date: str = ""`, `end_date: str = ""`
**Returns:** `dict`

**Example request:**
```
What is my lactate threshold?
```

**Example response:**
```json
{
  "speed_and_heart_rate": {
    "calendarDate": "2026-02-17T15:02:03.422",
    "speed": 0.383,
    "heartRate": 184
  },
  "power": {
    "sport": "RUNNING",
    "functionalThresholdPower": 389,
    "weight": 73,
    "powerToWeight": 5.33
  }
}
```

> `speed` is in km/s. Convert to pace: `1 / speed / 60` = ~43.5 min/km is wrong; the actual unit is different. Use `1000 / (speed * 1000) / 60` or interpret as m/s: 0.383 * 1000 = 383 m/s is also wrong. The actual value 0.383 represents speed in a Garmin-specific unit. Lactate threshold HR (184 bpm) is the primary usable metric.

---

### Heart Rate (3 tools)

#### `get_heart_rate_data`

Returns daily heart rate data including resting HR.

**Parameters:** `date: str = ""`
**Returns:** `dict`

**Example request:**
```
Show my heart rate data for today
```

#### `get_hrv_data`

Returns Heart Rate Variability data. Higher HRV indicates better recovery.

**Parameters:** `date: str = ""`
**Returns:** `dict`

**Example request:**
```
What is my HRV status?
```

#### `get_activity_hr_zones`

Returns heart rate zone distribution for a specific activity with percentages. Essential for 80/20 training intensity analysis.

**Parameters:** `activity_id: int`
**Returns:** `dict`

**Example request:**
```
Show HR zone distribution for activity 21892408004
```

**Example response:**
```json
{
  "activity_id": 21892408004,
  "hr_zones": [
    { "zoneNumber": 1, "secsInZone": 34.0, "zoneLowBoundary": 125, "percentage": 1.8 },
    { "zoneNumber": 2, "secsInZone": 164.0, "zoneLowBoundary": 138, "percentage": 8.6 },
    { "zoneNumber": 3, "secsInZone": 1384.9, "zoneLowBoundary": 152, "percentage": 72.4 },
    { "zoneNumber": 4, "secsInZone": 328.7, "zoneLowBoundary": 165, "percentage": 17.2 },
    { "zoneNumber": 5, "secsInZone": 0, "zoneLowBoundary": 179, "percentage": 0 }
  ]
}
```

> For 80/20 analysis: Zone 1-2 = easy (10.4%), Zone 3-5 = moderate/hard (89.6%). This run was mostly zone 3 (threshold), not following an 80/20 distribution.

---

### Wellness (3 tools)

#### `get_sleep_data`

Returns sleep data including duration, stages (deep/light/REM), and sleep score.

**Parameters:** `date: str = ""`
**Returns:** `dict`

**Example request:**
```
How did I sleep last night?
```

> Response includes `dailySleepDTO` with `deepSleepSeconds`, `lightSleepSeconds`, `remSleepSeconds`, `sleepTimeSeconds`, and `sleepScores`. Sleep need baseline and recommendations are also included.

#### `get_daily_wellness`

Returns comprehensive daily wellness: stress, Body Battery, SpO2, and respiration in a single call.

**Parameters:** `date: str = ""`
**Returns:** `dict`

**Example request:**
```
Show my wellness data for today
```

**Example response (key fields):**
```json
{
  "date": "2026-02-19",
  "stress": {
    "maxStressLevel": 65,
    "avgStressLevel": 48
  },
  "body_battery": [
    {
      "charged": 0,
      "drained": 14
    }
  ],
  "spo2": {
    "lastSevenDaysAvgSpO2": 97.3
  },
  "respiration": {
    "lowestRespirationValue": 13,
    "highestRespirationValue": 20,
    "avgWakingRespirationValue": 17
  }
}
```

> Note: `stress` and `body_battery` contain large time-series arrays (`stressValuesArray`, `bodyBatteryValuesArray`). Use summary fields like `avgStressLevel`, `charged`, `drained` for quick analysis.

#### `get_weekly_wellness_summary`

Returns weekly wellness trends: daily stress, Body Battery, sleep scores, and resting HR.

**Parameters:** `end_date: str = ""`, `weeks: int = 1` (max 4)
**Returns:** `list[dict]`

**Example request:**
```
Show my wellness trends for the past 2 weeks
```

---

### Records & Goals (2 tools)

#### `get_personal_records`

Returns all personal records (PRs) including best times for various distances.

**Parameters:** none
**Returns:** `list[dict]`

**Example request:**
```
Show my personal records
```

**Example response (abbreviated):**
```json
[
  {
    "typeId": 1,
    "activityName": "Track Running",
    "activityType": "track_running",
    "value": 201.0
  },
  {
    "typeId": 3,
    "activityName": "2024 RYW 10K",
    "activityType": "running",
    "value": 1161.3
  },
  {
    "typeId": 5,
    "activityName": "2024 Chicago Marathon",
    "activityType": "running",
    "value": 5301.2
  },
  {
    "typeId": 6,
    "activityName": "2024 JTBC Marathon",
    "activityType": "running",
    "value": 11186.1
  }
]
```

> `typeId` mapping: 1=1K, 2=1 mile, 3=5K, 4=10K, 5=half marathon, 6=marathon, 7=longest run distance.
> `value` is in **seconds** for time records, **meters** for distance records.
> Example: typeId 3 (5K) value 1161.3s = 19:21, typeId 5 (half) value 5301.2s = 1:28:21, typeId 6 (marathon) value 11186.1s = 3:06:26.

#### `get_goals`

Returns fitness goals and progress.

**Parameters:** `status: str = "active"` (options: `active`, `completed`, `all`)
**Returns:** `list[dict]`

**Example request:**
```
Show my active fitness goals
```

---

### Workout (2 tools)

#### `create_running_workout`

Creates a structured running workout and uploads it to Garmin Connect. The workout syncs to the user's Garmin watch.

**Parameters:** `name: str`, `steps: list[dict]`, `description: str = ""`
**Returns:** `dict`

**Example request:**
```
Create a 4x1km interval workout at 4:20-4:40/km pace with 2min recovery
```

**Example call:**
```json
{
  "name": "4x1km @4:30",
  "description": "VO2max interval session",
  "steps": [
    { "type": "warmup", "duration_seconds": 600, "description": "Easy jog" },
    {
      "type": "repeat", "count": 4, "skip_last_rest": true,
      "steps": [
        { "type": "interval", "duration_seconds": 270, "target": { "type": "pace", "min": "4:20", "max": "4:40" } },
        { "type": "recovery", "duration_seconds": 120 }
      ]
    },
    { "type": "cooldown", "duration_seconds": 600 }
  ]
}
```

**Example response:**
```json
{
  "status": "created",
  "workout_name": "4x1km @4:30",
  "estimated_duration_seconds": 2280,
  "result": { "workoutId": 123456789, "workoutName": "4x1km @4:30" }
}
```

#### `get_workouts`

Returns saved workouts from Garmin Connect.

**Parameters:** `count: int = 20` (max 100)
**Returns:** `list[dict]`

**Example request:**
```
Show my saved workouts
```

---

### Gear (1 tool)

#### `get_running_gear`

Returns running shoes with cumulative distance and activity count. Useful for determining when to replace shoes (typically 500-800 km).

**Parameters:** none
**Returns:** `list[dict]`

**Example request:**
```
Which of my shoes need replacement?
```

**Example response (abbreviated):**
```json
[
  {
    "uuid": "868101ee-...",
    "name": "Adidas Boston 13",
    "model": "Unknown Shoes",
    "status": "active",
    "date_begin": "2025-05-12T00:00:00.0",
    "total_distance_km": 854.96,
    "total_activities": 95
  },
  {
    "uuid": "469605dc-...",
    "name": "Asics Superblast",
    "status": "active",
    "total_distance_km": 822.37,
    "total_activities": 83
  },
  {
    "uuid": "56bcedf9-...",
    "name": "Brooks Glycerin GTS 20",
    "status": "retired",
    "total_distance_km": 766.04,
    "total_activities": 84
  }
]
```

> Shoes with `total_distance_km` > 700 should be flagged for replacement. `status` can be `active` or `retired`.

---

## Workout creation guide

Detailed reference for the `create_running_workout` `steps` parameter.

### Step types

- `warmup` - Warm-up phase
- `interval` - High intensity interval
- `recovery` - Recovery jog between intervals
- `cooldown` - Cool-down phase
- `repeat` - Repeat group (requires `count` and nested `steps`)

### Target types (optional)

Add a `target` object to any step to set an intensity target:

```json
{"type": "pace", "min": "4:30", "max": "4:50"}
{"type": "heart_rate", "min": 140, "max": 155}
{"type": "cadence", "min": 170, "max": 185}
```

- `pace`: min/max in `min:sec/km` format (string)
- `heart_rate`: min/max in bpm (integer)
- `cadence`: min/max in steps per minute (integer)

### Options

- **Workout description**: Top-level `description` parameter
- **Step notes**: Add `"description": "note text"` to any step
- **Skip last recovery**: Add `"skip_last_rest": true` to a repeat step to omit the final recovery

### Example: tempo run with HR target

```json
{
  "name": "40min Tempo",
  "description": "Threshold pace session",
  "steps": [
    { "type": "warmup", "duration_seconds": 600 },
    { "type": "interval", "duration_seconds": 2400, "target": { "type": "heart_rate", "min": 165, "max": 175 } },
    { "type": "cooldown", "duration_seconds": 600 }
  ]
}
```

### Example: 6x800m with cadence target

```json
{
  "name": "6x800m Speed",
  "steps": [
    { "type": "warmup", "duration_seconds": 900 },
    {
      "type": "repeat", "count": 6, "skip_last_rest": true,
      "steps": [
        { "type": "interval", "duration_seconds": 180, "target": { "type": "cadence", "min": 180, "max": 190 } },
        { "type": "recovery", "duration_seconds": 180 }
      ]
    },
    { "type": "cooldown", "duration_seconds": 600 }
  ]
}
```

---

## Running training methodologies

This server provides data to support the following training methodologies:

| Methodology | Key tools |
|-------------|-----------|
| **Jack Daniels VDOT** | `get_vo2max_and_fitness`, `get_personal_records`, `get_race_predictions` |
| **Norwegian Double Threshold** | `get_lactate_threshold`, `get_activity_hr_zones`, `create_running_workout` |
| **80/20 Training** | `get_activity_hr_zones`, `get_weekly_running_summary` |
| **Hanson's Method** | `get_weekly_running_summary`, `get_monthly_running_summary`, `get_activity_splits` |
| **Pfitzinger** | `get_weekly_running_summary`, `get_monthly_running_summary`, `get_recent_activities` |

### Methodology usage patterns

**Jack Daniels VDOT workflow:**
1. Call `get_personal_records` to find recent race times (typeId 3=5K, 4=10K, 5=half, 6=marathon)
2. Call `get_vo2max_and_fitness` for current VO2max
3. Calculate VDOT from race times, derive training paces (Easy, Marathon, Threshold, Interval, Repetition)
4. Create workouts with `create_running_workout` using calculated pace targets

**80/20 intensity distribution analysis:**
1. Call `get_recent_activities` for recent runs
2. For each activity, call `get_activity_hr_zones` to get zone distribution
3. Sum zone 1-2 time (easy) vs zone 3-5 time (moderate/hard)
4. Target: 80% easy, 20% hard across total training volume

---

## Development notes

### Authentication flow

1. `scripts/auth.py` - Login with email/password, saves OAuth token to `~/.garminconnect/`
2. On server start, `auth.py` auto-loads saved token
3. On token expiry, attempts re-auth via `GARMIN_EMAIL`/`GARMIN_PASSWORD` env vars
4. If all fail, raises `RuntimeError`

### API response structure differences

Garmin API uses different response structures for list vs detail endpoints:

- **List** (`get_activities`): Flat structure - `activity["distance"]`, `activity["averageHR"]`
- **Detail** (`get_activity`): Nested structure - `activity["summaryDTO"]["distance"]`, `activity["activityTypeDTO"]["typeKey"]`

When adding new tools, always verify actual API response keys.

### Garmin workout target type IDs

The library (`garminconnect.workout`) `TargetType` constants do not match the actual Garmin API:

| Purpose | Correct targetTypeId | targetTypeKey |
|---------|---------------------|---------------|
| No target | 1 | `no.target` |
| Heart rate | 2 | `heart.rate.zone` |
| Cadence | 3 | `cadence` |
| Pace | **6** | `pace.zone` |

> The library defines `TargetType.SPEED = 4`, but actual pace targets require **6**. Using 4 causes Garmin to misinterpret pace values as heart rate values.

### Return type pitfalls

Some Garmin APIs return `list` when you might expect `dict`:

- `get_personal_record()` -> `list[dict]`
- `get_training_readiness()` -> `list[dict]`

Always verify actual return types and match MCP tool type hints accordingly.

### PII filtering

The `sanitize.strip_pii()` function recursively removes the following keys from all API responses:

- Owner info: `ownerId`, `ownerFullName`, `ownerDisplayName`, profile image URLs
- Profile IDs: `userProfilePK`, `userProfilePk`, `userProfileId`, `profileId`, `profileNumber`
- User details: `displayName`, `fullName`, `userPro`, `userRoles`
- GPS coordinates: `startLatitude`, `startLongitude`, `endLatitude`, `endLongitude`
