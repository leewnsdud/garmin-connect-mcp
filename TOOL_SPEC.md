# Garmin Running MCP - Tool Specification

Full request/response specification for all 24 MCP tools.

All date parameters use `YYYY-MM-DD` format and default to today when empty.
All pace values are in `min:sec/km` format (e.g. `"5:38"`).
All distance values are in kilometers unless otherwise noted.

---

## Table of Contents

- [Activities](#activities-6-tools)
- [Summary](#summary-2-tools)
- [Training](#training-5-tools)
- [Heart Rate](#heart-rate-3-tools)
- [Wellness](#wellness-3-tools)
- [Records & Goals](#records--goals-2-tools)
- [Workout](#workout-2-tools)
- [Gear](#gear-1-tool)

---

## Activities (6 tools)

### `get_recent_activities`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `count` | int | 20 | Number of activities (max 100) |

**Response:** `list[dict]` — each dict contains:

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | int | Garmin activity ID |
| `name` | str | Activity name |
| `date` | str | `"YYYY-MM-DD HH:MM:SS"` |
| `type` | str | `"running"`, `"trail_running"`, `"track_running"`, etc. |
| `distance_km` | float | Total distance |
| `duration_seconds` | float | Total elapsed time |
| `moving_duration_seconds` | float | Moving time |
| `avg_pace` | str | Average pace `"mm:ss"` |
| `max_pace` | str | Fastest pace `"mm:ss"` |
| `avg_heart_rate` | int\|null | Average heart rate (bpm) |
| `max_heart_rate` | int\|null | Maximum heart rate (bpm) |
| `avg_cadence` | float\|null | Average running cadence (spm) |
| `max_cadence` | float\|null | Maximum cadence (spm) |
| `avg_stride_length_cm` | float\|null | Average stride length |
| `avg_ground_contact_time_ms` | float\|null | Average ground contact time |
| `avg_vertical_oscillation_cm` | float\|null | Average vertical oscillation |
| `avg_vertical_ratio` | float\|null | Average vertical ratio (%) |
| `calories` | int\|null | Calories burned |
| `elevation_gain` | float\|null | Total ascent (m) |
| `elevation_loss` | float\|null | Total descent (m) |
| `max_elevation` | float\|null | Maximum altitude (m) |
| `min_elevation` | float\|null | Minimum altitude (m) |
| `avg_power` | int\|null | Average running power (W) |
| `max_power` | int\|null | Maximum running power (W) |
| `normalized_power` | int\|null | Normalized power (W) |
| `training_effect_aerobic` | float\|null | Aerobic training effect (0-5) |
| `training_effect_anaerobic` | float\|null | Anaerobic training effect (0-5) |
| `training_load` | float\|null | Training load score |
| `training_effect_label` | str\|null | `"RECOVERY"`, `"BASE"`, `"TEMPO"`, `"THRESHOLD"`, `"VO2MAX"` etc. |
| `vo2max` | int\|null | VO2max during this activity |
| `fastest_split_1km` | str\|null | Fastest 1km split pace |
| `fastest_split_1mile` | str\|null | Fastest 1 mile split pace |
| `fastest_split_5km` | str\|null | Fastest 5km split pace |
| `hr_zone_1_seconds` | float\|null | Time in HR zone 1 |
| `hr_zone_2_seconds` | float\|null | Time in HR zone 2 |
| `hr_zone_3_seconds` | float\|null | Time in HR zone 3 |
| `hr_zone_4_seconds` | float\|null | Time in HR zone 4 |
| `hr_zone_5_seconds` | float\|null | Time in HR zone 5 |
| `steps` | int\|null | Total steps |
| `lap_count` | int\|null | Number of laps |
| `is_pr` | bool | Whether activity contains a personal record |
| `max_temperature` | int\|null | Max temperature (°C) |
| `min_temperature` | int\|null | Min temperature (°C) |
| `avg_grade_adjusted_pace` | str\|null | Grade Adjusted Pace (GAP) `"mm:ss"` |
| `max_vertical_speed` | float\|null | Max vertical speed (m/s) — climbing rate |
| `water_estimated_ml` | float\|null | Estimated water consumption (ml) |
| `split_summary` | dict\|null | RWD breakdown (see below) |

**`split_summary` structure** (when available):

```json
{
  "run": { "distance_km": 5.76, "duration_seconds": 1948.7, "avg_pace": "5:38", "elevation_gain": 14.0, "elevation_loss": 10.0 },
  "walk": { "distance_km": 1.2, "duration_seconds": 720.0, "avg_pace": "10:00", "elevation_gain": 50.0, "elevation_loss": 5.0 },
  "stand": { "distance_km": 0.0, "duration_seconds": 30.0, "avg_pace": null, "elevation_gain": 0.0, "elevation_loss": 0.0 }
}
```

---

### `get_activities_by_date`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | str | (required) | Start date `YYYY-MM-DD` |
| `end_date` | str | (required) | End date `YYYY-MM-DD` |

**Response:** `list[dict]` — same structure as `get_recent_activities`

---

### `get_activity_detail`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `activity_id` | int | (required) | Garmin activity ID |

**Response:** `dict` — extracted from Garmin detail API (`summaryDTO`). Shares most field names with the list tool but uses the detail API's nested structure. Key differences from list tool noted below.

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | int | Garmin activity ID |
| `name` | str | Activity name |
| `date` | str | `"YYYY-MM-DD HH:MM:SS"` |
| `type` | str | Activity type key |
| `distance_km` | float | Total distance |
| `duration_seconds` | float | Total elapsed time |
| `avg_pace` | str | Average pace `"mm:ss"` |
| `avg_heart_rate` | int\|null | Average heart rate |
| `max_heart_rate` | int\|null | Maximum heart rate |
| `min_heart_rate` | int\|null | Minimum heart rate (detail only) |
| `avg_cadence` | float\|null | Average cadence |
| `max_cadence` | float\|null | Maximum cadence |
| `calories` | int\|null | Calories burned |
| `elevation_gain` | float\|null | Total ascent (m) |
| `elevation_loss` | float\|null | Total descent (m) |
| `min_elevation` | float\|null | Minimum altitude |
| `max_elevation` | float\|null | Maximum altitude |
| `avg_power` | int\|null | Average running power (W) |
| `max_power` | int\|null | Maximum running power (W) |
| `normalized_power` | int\|null | Normalized power (W) |
| `training_effect_aerobic` | float\|null | Aerobic training effect |
| `training_effect_anaerobic` | float\|null | Anaerobic training effect |
| `training_load` | float\|null | Training load score |
| `training_label` | str\|null | Training effect label (note: `training_label` not `training_effect_label`) |
| `avg_stride_length` | float\|null | Stride length (note: no `_cm` suffix) |
| `avg_vertical_oscillation` | float\|null | Vertical oscillation (note: no `_cm` suffix) |
| `avg_ground_contact_time` | float\|null | Ground contact time (note: no `_ms` suffix) |
| `avg_vertical_ratio` | float\|null | Vertical ratio (%) |
| `avg_temperature` | int\|null | Average temperature (°C, detail only) |
| `max_temperature` | int\|null | Max temperature (°C) |
| `min_temperature` | int\|null | Min temperature (°C) |
| `steps` | int\|null | Total steps |
| `description` | str\|null | User-entered activity notes (detail only) |
| `avg_grade_adjusted_pace` | str\|null | Grade Adjusted Pace `"mm:ss"` |
| `max_vertical_speed` | float\|null | Max vertical speed (m/s) |
| `water_estimated_ml` | float\|null | Estimated water (ml) |
| `impact_load` | float\|null | Cumulative impact stress (detail only) |
| `begin_potential_stamina` | float\|null | Stamina at start 0-100% (detail only) |
| `end_potential_stamina` | float\|null | Stamina at end 0-100% (detail only) |
| `min_available_stamina` | float\|null | Lowest stamina 0-100% (detail only) |
| `split_summary` | dict\|null | RWD breakdown |

> **Note:** The detail tool uses slightly different field names than the list tool for running dynamics: `avg_stride_length` (vs `avg_stride_length_cm`), `avg_ground_contact_time` (vs `avg_ground_contact_time_ms`), `avg_vertical_oscillation` (vs `avg_vertical_oscillation_cm`), and `training_label` (vs `training_effect_label`). The detail tool also lacks some list-only fields: `moving_duration_seconds`, `max_pace`, `fastest_split_*`, `hr_zone_*_seconds`, `lap_count`, `is_pr`.

---

### `get_activity_splits`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `activity_id` | int | (required) | Garmin activity ID |

**Response:** `dict` with:

| Field | Type | Description |
|-------|------|-------------|
| `activityId` | int | Activity ID |
| `lapDTOs` | list[dict] | Per-km/mile lap data |

**Each `lapDTOs` entry:**

| Field | Type | Description |
|-------|------|-------------|
| `lapIndex` | int | Lap number (1-based) |
| `distance` | float | Lap distance (m) |
| `duration` | float | Lap duration (sec) |
| `avg_pace` | str\|null | Average pace `"mm:ss"` |
| `avg_moving_pace` | str\|null | Average moving pace |
| `max_pace` | str\|null | Fastest pace in lap |
| `grade_adjusted_pace` | str\|null | Grade adjusted pace |
| `averageHR` | int\|null | Average heart rate |
| `maxHR` | int\|null | Max heart rate |
| `averageRunCadence` | float\|null | Average cadence |
| `averagePower` | int\|null | Average power (W) |
| `elevationGain` | float\|null | Elevation gain (m) |
| `groundContactTime` | float\|null | Ground contact time (ms) |
| `strideLength` | float\|null | Stride length (cm) |
| `verticalOscillation` | float\|null | Vertical oscillation (cm) |

> Speed fields (`averageSpeed`, `averageMovingSpeed`, `maxSpeed`, `avgGradeAdjustedSpeed`) are replaced by pace fields. `maxVerticalSpeed` (m/s) is preserved as climbing rate.

---

### `get_activity_weather`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `activity_id` | int | (required) | Garmin activity ID |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `issueDate` | str | Weather report time (ISO 8601) |
| `temp` | int | Temperature (°F) |
| `apparentTemp` | int | Feels-like temperature (°F) |
| `dewPoint` | int | Dew point (°F) |
| `relativeHumidity` | int | Relative humidity (%) |
| `windDirection` | int | Wind direction (degrees) |
| `windDirectionCompassPoint` | str | Wind direction (compass) |
| `windSpeed` | int | Wind speed (mph) |
| `windGust` | int\|null | Wind gust (mph) |
| `weatherStationDTO` | dict | Weather station info |
| `weatherTypeDTO` | dict | Weather description (`desc` field) |

> Latitude/longitude fields are stripped for privacy. Temperatures in **Fahrenheit**, wind in **mph**.

---

### `get_activity_typed_splits`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `activity_id` | int | (required) | Garmin activity ID |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | int | Activity ID |
| `total_climb_splits` | int | Number of climb segments |
| `splits` | list[dict] | Climb segment data |

**Each `splits` entry:**

| Field | Type | Description |
|-------|------|-------------|
| `type` | str | `"CLIMB_PRO_CYCLING_CLIMB"` or `"CLIMB_PRO_CYCLING_CLIMB_SECTION"` |
| `difficulty` | str | `"DESCENT"`, `"LOW"`, `"MODERATE"`, `"STEEP"`, `"STEEPER"`, `"STEEPEST"`, `"FOURTH_CATEGORY"` to `"HC"` |
| `distance_km` | float | Segment distance |
| `duration_seconds` | float | Segment duration |
| `elevation_gain` | float\|null | Elevation gain (m) |
| `elevation_loss` | float\|null | Elevation loss (m) |
| `start_elevation` | float\|null | Starting elevation (m) |
| `avg_grade` | float\|null | Average gradient (%) |
| `max_grade` | float\|null | Maximum gradient (%) |
| `actual_pace` | str\|null | Actual pace `"mm:ss"` |
| `grade_adjusted_pace` | str\|null | Grade adjusted pace `"mm:ss"` |
| `avg_heart_rate` | int\|null | Average heart rate |
| `max_heart_rate` | int\|null | Max heart rate |
| `avg_power` | int\|null | Average power (W) |
| `avg_cadence` | float\|null | Average cadence (spm) |

---

## Summary (2 tools)

### `get_weekly_running_summary`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `end_date` | str | today | End date `YYYY-MM-DD` |
| `weeks` | int | 1 | Number of weeks (max 12) |

**Response:** `list[dict]` — one dict per week:

| Field | Type | Description |
|-------|------|-------------|
| `week_start` | str | ISO date |
| `week_end` | str | ISO date |
| `total_runs` | int | Number of runs |
| `total_distance_km` | float | Total distance |
| `total_duration_seconds` | float | Total duration |
| `avg_pace` | str\|null | Average pace `"mm:ss"` |
| `avg_heart_rate` | float\|null | Average heart rate |
| `total_elevation_gain` | float | Total elevation gain (m) |
| `longest_run_km` | float | Longest run distance |
| `longest_run_pace` | str\|null | Longest run pace |

---

### `get_monthly_running_summary`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `year` | int | current | Year (e.g. 2026) |
| `month` | int | current | Month (1-12) |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `year` | int | Year |
| `month` | int | Month |
| `total_runs` | int | Total runs in month |
| `total_distance_km` | float | Total distance |
| `total_duration_seconds` | float | Total duration |
| `avg_pace` | str\|null | Average pace |
| `avg_heart_rate` | float\|null | Average heart rate |
| `total_elevation_gain` | float | Total elevation gain |
| `longest_run_km` | float | Longest run distance |
| `longest_run_pace` | str\|null | Longest run pace |
| `weekly_breakdown` | list[dict] | Per-week breakdown |
| `vs_previous_month` | dict | Month-over-month comparison |

**`weekly_breakdown` entry:**

| Field | Type | Description |
|-------|------|-------------|
| `week_number` | int | Week ordinal in month |
| `week_start` | str | ISO date |
| `week_end` | str | ISO date |
| `total_runs` | int | Runs in this week |
| `total_distance_km` | float | Distance in this week |
| `avg_pace` | str\|null | Average pace |

**`vs_previous_month`:**

| Field | Type | Description |
|-------|------|-------------|
| `distance_change_pct` | float\|null | Distance change % |
| `runs_change` | int | Runs count difference |
| `previous_month_distance_km` | float | Previous month distance |
| `previous_month_runs` | int | Previous month run count |

---

## Training (5 tools)

### `get_training_status`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | str | today | Date `YYYY-MM-DD` |

**Response:** `dict` — Raw Garmin training status data.

Key values: `Productive`, `Maintaining`, `Overreaching`, `Detraining`, `Recovery`, `Peaking`, `Unproductive`.

---

### `get_training_readiness`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | str | today | Date `YYYY-MM-DD` |

**Response:** `list[dict]`

| Field | Type | Description |
|-------|------|-------------|
| `calendarDate` | str | Date |
| `level` | str | `"LOW"`, `"MODERATE"`, `"HIGH"`, `"PRIME"` |
| `feedbackShort` | str | Summary (e.g. `"WELL_RECOVERED"`) |
| `score` | int | Readiness score (0-100) |
| `recoveryTime` | int | Recovery time (hours) |
| `recoveryTimeFactorPercent` | int | Recovery factor (%) |
| `recoveryTimeFactorFeedback` | str | Recovery feedback |
| `acwrFactorPercent` | int | Acute:Chronic workload ratio (%) |
| `acwrFactorFeedback` | str | Workload feedback |
| `acuteLoad` | int | Acute training load |
| `hrvWeeklyAverage` | int | Weekly HRV average |

---

### `get_vo2max_and_fitness`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | str | today | Date `YYYY-MM-DD` |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `max_metrics` | dict\|list | VO2max metrics from Garmin |
| `fitness_age` | dict\|null | Fitness age data |

**`fitness_age` structure (when available):**

| Field | Type | Description |
|-------|------|-------------|
| `chronologicalAge` | int | Actual age |
| `fitnessAge` | float | Calculated fitness age |
| `achievableFitnessAge` | float | Best achievable fitness age |
| `components` | dict | Contributing factors (vigorous days, rhr, bmi) |

---

### `get_race_predictions`

No parameters.

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `calendarDate` | str | Prediction date |
| `time5K` | int | 5K time (seconds) |
| `time10K` | int | 10K time (seconds) |
| `timeHalfMarathon` | int | Half marathon time (seconds) |
| `timeMarathon` | int | Marathon time (seconds) |

---

### `get_lactate_threshold`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | str | "" | Start date (optional) |
| `end_date` | str | "" | End date (optional) |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `speed_and_heart_rate` | dict | Lactate threshold speed and HR |
| `power` | dict | Functional threshold power |

**`speed_and_heart_rate`:**

| Field | Type | Description |
|-------|------|-------------|
| `calendarDate` | str | Date of measurement |
| `speed` | float | Speed (Garmin-specific unit) |
| `heartRate` | int | Lactate threshold HR (bpm) |

**`power`:**

| Field | Type | Description |
|-------|------|-------------|
| `sport` | str | `"RUNNING"` |
| `functionalThresholdPower` | int | FTP (watts) |
| `weight` | float | Body weight (kg) |
| `powerToWeight` | float | Power-to-weight ratio (W/kg) |

---

## Heart Rate (3 tools)

### `get_heart_rate_data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | str | today | Date `YYYY-MM-DD` |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `heart_rates` | dict | Hourly/granular HR data |
| `resting_heart_rate` | dict\|null | Resting HR data (nested structure with `allMetrics.metricsMap`) |

---

### `get_hrv_data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | str | today | Date `YYYY-MM-DD` |

**Response:** `dict` — Raw HRV metrics. Higher values = better recovery.

---

### `get_activity_hr_zones`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `activity_id` | int | (required) | Garmin activity ID |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | int | Activity ID |
| `hr_zones` | list[dict] | HR zone distribution |

**Each `hr_zones` entry:**

| Field | Type | Description |
|-------|------|-------------|
| `zoneNumber` | int | Zone number (1-5) |
| `secsInZone` | float | Seconds in zone |
| `zoneLowBoundary` | int | Zone lower bound (bpm) |
| `percentage` | float | % of total activity time |

---

## Wellness (3 tools)

### `get_sleep_data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | str | today | Date `YYYY-MM-DD` |

**Response:** `dict` — Garmin sleep data including:
- `dailySleepDTO`: sleep stages (`deepSleepSeconds`, `lightSleepSeconds`, `remSleepSeconds`), `sleepTimeSeconds`, `sleepScores`
- Sleep need baseline and recommendations

---

### `get_daily_wellness`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | str | today | Date `YYYY-MM-DD` |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `date` | str | ISO date |
| `stress` | dict\|null | Stress data (`maxStressLevel`, `avgStressLevel`) |
| `body_battery` | list[dict]\|null | Body Battery (list with `charged`, `drained` fields) |
| `spo2` | dict\|null | Blood oxygen (`lastSevenDaysAvgSpO2`) |
| `respiration` | dict\|null | Respiration rate (`lowestRespirationValue`, `highestRespirationValue`, `avgWakingRespirationValue`) |

---

### `get_weekly_wellness_summary`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `end_date` | str | today | End date `YYYY-MM-DD` |
| `weeks` | int | 1 | Number of weeks (max 4) |

**Response:** `list[dict]` — one per week:

| Field | Type | Description |
|-------|------|-------------|
| `week_start` | str | ISO date |
| `week_end` | str | ISO date |
| `avg_stress` | float\|null | Average stress level |
| `avg_sleep_score` | float\|null | Average sleep score |
| `avg_resting_hr` | float\|null | Average resting HR |
| `daily_data` | list[dict] | Daily breakdown |

**`daily_data` entry:**

| Field | Type | Description |
|-------|------|-------------|
| `date` | str | ISO date |
| `stress_avg` | int\|null | Average stress |
| `body_battery_high` | int\|null | Body battery high |
| `body_battery_low` | int\|null | Body battery low |
| `resting_hr` | int\|null | Resting heart rate |
| `steps` | int\|null | Total steps |
| `sleep_score` | int\|null | Sleep score |
| `sleep_duration_seconds` | int\|null | Sleep duration |

---

## Records & Goals (2 tools)

### `get_personal_records`

No parameters.

**Response:** `list[dict]`

| Field | Type | Description |
|-------|------|-------------|
| `typeId` | int | Record type (see below) |
| `activityName` | str | Activity where PR was set |
| `activityType` | str | Activity type key |
| `value` | float | Time (seconds) or distance (meters) |

**`typeId` mapping:**

| typeId | Distance |
|--------|----------|
| 1 | 1K |
| 2 | 1 Mile |
| 3 | 5K |
| 4 | 10K |
| 5 | Half Marathon |
| 6 | Marathon |
| 7 | Longest Run (distance in meters) |

---

### `get_goals`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | str | `"active"` | `"active"`, `"completed"`, `"all"` |

**Response:** `list[dict]` — Fitness goals with progress data.

---

## Workout (2 tools)

### `create_running_workout`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | (required) | Workout name |
| `steps` | list[dict] | (required) | Step definitions (see below) |
| `description` | str | `""` | Workout notes |

**Step definition:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | str | yes | `"warmup"`, `"cooldown"`, `"interval"`, `"recovery"`, `"rest"`, `"repeat"` |
| `duration_seconds` | int | no | Time-based end condition |
| `distance_meters` | int | no | Distance-based end condition (priority over duration) |
| `target` | dict | no | Intensity target (see below) |
| `description` | str | no | Step notes |

**For `repeat` steps:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | str | yes | Must be `"repeat"` |
| `count` | int | yes | Number of repetitions |
| `steps` | list[dict] | yes | Nested step definitions |
| `skip_last_rest` | bool | no | Skip final recovery step |

**Target definition:**

| Target type | min | max | Unit |
|-------------|-----|-----|------|
| `pace` | str `"4:30"` | str `"4:50"` | min:sec per km |
| `heart_rate` | int `140` | int `155` | bpm |
| `cadence` | int `170` | int `185` | steps per minute |
| `power` | int `280` | int `320` | watts |

**Response:** `dict`

| Field | Type | Description |
|-------|------|-------------|
| `status` | str | `"created"` |
| `workout_name` | str | Workout name |
| `estimated_duration_seconds` | int | Estimated total duration |
| `result` | dict | Garmin API response (`workoutId`, `workoutName`) |

> For distance-based steps, estimated duration uses ~5:00/km.
> If both `distance_meters` and `duration_seconds` are provided, distance takes priority.

---

### `get_workouts`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `count` | int | 20 | Number of workouts (max 100) |

**Response:** `list[dict]` — Saved workout definitions from Garmin Connect.

---

## Gear (1 tool)

### `get_running_gear`

No parameters.

**Response:** `list[dict]` — all running shoes (active + retired):

| Field | Type | Description |
|-------|------|-------------|
| `uuid` | str | Gear UUID |
| `name` | str | Shoe name |
| `model` | str | Shoe model |
| `status` | str | `"active"` or `"retired"` |
| `date_begin` | str\|null | Start date |
| `date_end` | str\|null | Retirement date |
| `max_distance_km` | float\|null | User-set lifespan limit |
| `total_distance_km` | float | Cumulative distance |
| `total_activities` | int | Number of activities |
| `wear_percentage` | float\|null | Wear % (>100% = exceeded lifespan) |

---

## Data Processing Notes

### Speed → Pace Conversion

All running speed fields (m/s) are converted to pace (min:sec/km):
```
pace_total_seconds = 1000 / speed_ms
minutes = pace_total_seconds // 60
seconds = pace_total_seconds % 60
formatted = f"{minutes}:{seconds:02.0f}"
```

Exception: `maxVerticalSpeed` is kept as m/s since it represents climbing rate, not running pace.

### PII Filtering

The `sanitize.strip_pii()` function recursively removes from all API responses:
- Owner info: `ownerId`, `ownerFullName`, `ownerDisplayName`, `userId`, profile image URLs
- Profile IDs: `userProfilePK`, `userProfilePk`, `userProfileId`, `profileId`, `profileNumber`
- User details: `displayName`, `fullName`, `userPro`, `userRoles`
- GPS coordinates: `startLatitude`, `startLongitude`, `endLatitude`, `endLongitude`

### Unit Reference

| Metric | Unit |
|--------|------|
| Distance | km (converted from meters) |
| Pace | min:sec/km |
| Duration | seconds |
| Heart rate | bpm |
| Cadence | steps per minute (spm) |
| Power | watts (W) |
| Elevation | meters (m) |
| Temperature | °C (activities), °F (weather) |
| Wind speed | mph (weather) |
| Stride length | cm |
| Ground contact time | ms |
| Vertical oscillation | cm |
| Vertical speed | m/s |
| Weight | kg |
| Water | ml |
| Stamina | % (0-100) |
