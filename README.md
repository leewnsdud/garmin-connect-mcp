# Garmin Connect MCP

Garmin Connect의 러닝 데이터를 활용한 개인화된 훈련 분석 및 계획을 제공하는 Model Context Protocol (MCP) 서버입니다.

[English Version](README_EN.md)

## 📚 문서

- [사용자 가이드](README_GUIDE.md) - 시나리오별 활용법과 상세한 사용 방법
- [프롬프트 템플릿](PROMPTS.md) - 효과적인 대화를 위한 프롬프트 예시

## 개요

이 MCP 서버는 Garmin Connect API와 Claude를 연결하여 러너들이 데이터 기반의 훈련 계획을 수립할 수 있도록 지원합니다. 개인 기록, VO2 Max, 훈련 부하, 회복 상태 등을 종합적으로 분석하여 최적화된 훈련 제안을 제공합니다.

### 주요 기능

- 🏃 **퍼포먼스 분석**: 개인 기록, VO2 Max, 젖산 역치 등 종합 분석
- 📊 **훈련 부하 관리**: ATL/CTL 비율을 통한 과훈련 및 부상 위험 관리
- 📅 **맞춤형 훈련 계획**: VDOT 기반 페이스 계산 및 일일 훈련 제안
- 💓 **건강 모니터링**: 심박수, 수면, 스트레스, 회복 지표 추적
- 🎯 **레이스 준비**: 목표 설정, 테이퍼링, 레이스 예측

## 프로젝트 구조

- `main.py`: MCP 서버 엔트리포인트. 서버 설정과 툴 라우팅만 담당합니다.
- `services/garmin_client.py`: Garmin Connect 인증, 토큰 재사용, 공용 API 호출을 담당하는 서비스 레이어.
- `handlers/training.py`: 훈련 계획 탐색/요약/스케줄 관련 핸들러.
- `handlers/analytics.py`: 주간 러닝 리포트, 장비 인사이트 등 분석 기능.
- `utils.py`: 캐싱, 포맷팅, 러닝 계산식 등 공통 유틸리티.

## ✅ 2025-11-13 라이브 검증 요약

- **연결 상태**: VPN 해제 후 GARMIN API 인증과 주요 도구 호출이 정상 수행됨.
- **주요 지표**: 1주 러닝 거리 39.76km, 평균 페이스 `5:32/km`, 가장 긴 러닝 15.17km.
- **훈련 상태**: Training readiness 점수 11(POOR)로 회복 위주의 권장.
- **디바이스**: `fenix 8 - 47mm, AMOLED` + `HRM-Pro Plus` 두 기기 인식, 설정 조회 성공.
- **훈련 계획/기어**: 현재 계정 기준 공개 러닝 훈련 계획과 등록된 러닝화 없음.
- **리소스 URI**: `activity://{id}/full`, `trends://monthly` 등 대용량 리소스 조회 확인.

## ⚠️ Known Issues (2025-11-13)

- 현재 계정에서는 공개 러닝 훈련 계획이 없어 `list_training_plans` 및 후속 도구가 빈 응답을 반환합니다.
- Garmin Connect에 러닝화가 등록되어 있지 않아 `get_gear_insights`가 분석 결과를 제공하지 못합니다.

## 설치 방법

### 사전 요구사항

- Python 3.13 이상
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 패키지 관리자)
- Garmin Connect 계정
- Claude Desktop 앱

### 자동 설치

```bash
# 전체 자동 설치 (권장)
git clone https://github.com/leewnsdud/garmin-connect-mcp.git
cd garmin-connect-mcp
uv run python install.py
```

### 수동 설치

1. 저장소 클론
```bash
git clone https://github.com/leewnsdud/garmin-connect-mcp.git
cd garmin-connect-mcp
```

2. 의존성 설치
```bash
uv sync
```

3. 환경 변수 설정
```bash
cp .env.template .env
# .env 파일을 열어 Garmin Connect 인증 정보 입력
# 필요 시 GARMIN_TIMEZONE=Asia/Seoul 처럼 타임존(IANA ID 또는 UTC±HH:MM) 지정
```

4. Garmin 인증 설정
```bash
uv run python setup_garmin_auth.py
```

5. Claude Desktop 설정
```bash
uv run python setup_claude_desktop.py
```

5-1. Claude Desktop MCP 서버 직접 설정

- claude_desktop_config.json 파일에 직접 설정

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--directory",
        "/[디렉토리 경로]/garmin-connect-mcp",
        "python",
        "main.py"
      ],
      "env": {
        "GARMIN_USERNAME": [Garmin Connect 이메일],
        "GARMIN_PASSWORD": [Garmin Connect 비밀번호],
        "GARMIN_TIMEZONE": "Asia/Seoul"
      }
    }
  }
}
```

### 🕒 타임존 설정

- `GARMIN_TIMEZONE` 환경 변수(또는 MCP 서버 설정의 `env`)를 사용해 날짜 계산 기준을 지정할 수 있습니다.
- IANA 타임존(`Asia/Seoul`, `America/Los_Angeles`)이나 `UTC+09:00`, `GMT-0330` 형태의 오프셋을 지원합니다.
- 미설정 시 기본값은 `UTC`이며, 모든 날짜 기반 도구(`get_activities_for_date`, `get_weekly_running_summary`, `download_activity_file`, 리소스 등)가 해당 타임존을 사용해 한국 시간 대비 하루 밀림 현상을 방지합니다.

## 사용 가능한 도구 (총 43개)

### 🏃 퍼포먼스 분석 (9개)

#### get_personal_records
개인 최고 기록을 조회합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "personal_records": {
    "5K": {
      "time": "19:21",
      "seconds": 1161.27,
      "date": "2024-09-29T08:01:00.0",
      "activity_id": 17154668201
    },
    "10K": {
      "time": "39:03",
      "seconds": 2343.88,
      "date": "2024-09-29T08:01:00.0",
      "activity_id": 17154668201
    },
    "half_marathon": {
      "time": "01:28:21",
      "seconds": 5301.22,
      "date": "2024-10-13T07:39:36.0",
      "activity_id": 17276890811
    },
    "marathon": {
      "time": "03:06:26",
      "seconds": 11186.12,
      "date": "2024-11-03T08:07:11.0",
      "activity_id": 17443738442
    }
  }
}
```
#### get_vo2max
현재 VO2 Max 값과 추이를 조회합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "vo2_max": null,
  "vo2_max_trend": null,
  "race_predictions": {
    "time5K": 1118,
    "time10K": 2398,
    "timeHalfMarathon": 5340,
    "timeMarathon": 11656,
    "calendarDate": "2025-11-13"
  },
  "date": "2025-11-13"
}
```
#### get_training_status
현재 훈련 상태와 회복 시간을 확인합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "training_status": {
    "status": "Unknown",
    "fitness_level": null,
    "load_balance": null,
    "recovery_time": null,
    "training_effect": {
      "aerobic": null,
      "anaerobic": null
    }
  },
  "training_readiness": {
    "score": 11,
    "level": "POOR",
    "feedback": "FOCUS_ON_RECOVERY"
  },
  "date": "2025-11-13"
}
```
#### get_lactate_threshold
젖산 역치 페이스와 심박수 데이터를 조회합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "lactate_threshold": {
    "note": "No lactate threshold data found. This requires a compatible Garmin device and sufficient running data."
  },
  "date": "2025-11-13"
}
```
#### get_race_predictions
현재 체력 기준 예상 레이스 기록을 제공합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "race_predictions": {
    "note": "No race predictions available. This requires recent running activities and a compatible Garmin device."
  },
  "current_vo2_max": null,
  "raw_predictions": {
    "time10K": 2398,
    "timeHalfMarathon": 5340,
    "timeMarathon": 11656,
    "calendarDate": "2025-11-13"
  }
}
```
#### get_training_readiness
훈련 준비도와 권장사항을 제공합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "training_readiness": {
    "score": 11,
    "level": "POOR",
    "message": null,
    "recovery_level": null,
    "training_load_balance": null,
    "sleep_quality": null,
    "hrv_status": null
  },
  "recovery_time_hours": null,
  "date": "2025-11-13"
}
```
#### get_recovery_time
권장 회복 시간을 확인합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "recovery_info": {
    "recovery_time_hours": 0,
    "recovery_time_formatted": "0 hours",
    "fully_recovered_at": "Already recovered"
  },
  "last_activity": {
    "activity_name": "러닝",
    "activity_type": "running",
    "start_time": "2025-11-12 20:16:25",
    "training_effect": {
      "aerobic": null,
      "anaerobic": null
    }
  }
}
```
#### get_endurance_score
유산소 지구력 능력을 나타내는 지구력 점수를 조회합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "endurance_score": null,
  "level": null,
  "description": null,
  "trend": null,
  "date": "2025-11-13"
}
```
#### get_hill_score
언덕 오르기 능력을 나타내는 힐 스코어를 조회합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "hill_score": null,
  "level": null,
  "description": null,
  "trend": null,
  "date": "2025-11-13"
}
```
### 📊 활동 데이터 (4개)

#### get_recent_running_activities
최근 러닝 활동 목록을 조회합니다.

**응답 예시 (2025-11-13 실측):**
```json
[
  {
    "activityId": 20966535017,
    "activityName": "러닝",
    "startTimeLocal": "2025-11-12 20:16:25",
    "distance": 1049.04,
    "duration": 344.49,
    "averageSpeed": 3.05,
    "averageHR": 142,
    "aerobicTrainingEffect": 1.3
  },
  {
    "activityId": 20966534341,
    "activityName": "러닝",
    "startTimeLocal": "2025-11-12 19:55:17",
    "distance": 4146.17,
    "duration": 1184.73,
    "averageSpeed": 3.5,
    "averageHR": 157,
    "aerobicTrainingEffect": 3.0
  }
]
```
#### get_activity_summary
특정 활동의 기본 정보를 조회합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "activity_id": "20966535017",
  "activity_name": "러닝",
  "activity_type": "running",
  "start_time": "2025-11-12T20:16:25.0",
  "distance_km": 1.05,
  "duration_seconds": 344.489,
  "duration_formatted": "05:44",
  "average_pace_per_km": "5:28",
  "average_speed_kmh": 10.96,
  "elevation_gain_m": 1.0,
  "elevation_loss_m": 0.0,
  "calories": 75.0,
  "average_hr": 142.0,
  "max_hr": 153.0,
  "training_effect": {
    "aerobic": 1.3,
    "anaerobic": null
  },
  "resources": {
    "full_details": "activity://20966535017/full",
    "splits": "activity://20966535017/splits",
    "hr_zones": "activity://20966535017/hr-zones",
    "advanced_metrics": "activity://20966535017/metrics"
  }
}
```
#### get_activity_details
활동의 상세 메트릭과 분할 구간을 조회합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "activity_id": 20966535017,
  "splits": {
    "lapDTOs": 2,
    "eventDTOs": 2
  },
  "weather": {
    "issueDate": "2025-11-12T11:00:00.000+00:00",
    "temp": 52,
    "windSpeed": 3,
    "relativeHumidity": 67
  },
  "performance_metrics": {
    "normalized_power": null,
    "training_stress_score": null,
    "intensity_factor": null
  },
  "note": "Use include_raw=true or activity://20966535017/full resource for complete data."
}
```
#### get_weekly_running_summary
주간 러닝 요약 정보와 트렌드를 제공합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "weekly_summaries": [
    {
      "week_start": "2025-11-06",
      "week_end": "2025-11-13",
      "total_runs": 6,
      "total_distance_km": 39.76,
      "total_duration_hours": 3.67,
      "average_pace_per_km": "5:32",
      "longest_run_km": 15.17,
      "total_elevation_gain_m": 86.0
    }
  ],
  "trends": null,
  "analysis_period": "1 week(s)"
}
```
### 💓 건강 지표 (8개)

#### get_heart_rate_metrics
안정시 심박수와 HRV 데이터를 조회합니다.

**응답 예시:**
```json
{
  "date": "2024-12-29",
  "resting_heart_rate": 48,
  "heart_rate_zones": {
    "zone1": {"min": 96, "max": 115},
    "zone2": {"min": 115, "max": 134},
    "zone3": {"min": 134, "max": 153},
    "zone4": {"min": 153, "max": 172},
    "zone5": {"min": 172, "max": 191}
  },
  "hrv": 45
}
```

#### get_sleep_analysis
수면 데이터와 단계별 분석을 제공합니다.

**응답 예시:**
```json
{
  "sleep_summary": {
    "total_sleep_hours": 7.5,
    "sleep_start": "2024-12-28 23:00",
    "sleep_end": "2024-12-29 06:30",
    "sleep_levels": {
      "deep": 5400,
      "light": 14400,
      "rem": 7200,
      "awake": 900
    },
    "sleep_score": 82,
    "sleep_quality": "good"
  }
}
```

#### get_body_battery
바디 배터리 에너지 레벨을 확인합니다.

**응답 예시:**
```json
{
  "body_battery_summary": {
    "current_level": 85,
    "charged_value": 95,
    "drained_value": 10
  },
  "body_battery_timeline": [
    {"timestamp": "06:00", "level": 95},
    {"timestamp": "12:00", "level": 75},
    {"timestamp": "18:00", "level": 85}
  ]
}
```

#### get_stress_levels
스트레스 수준과 추이를 분석합니다.

**응답 예시:**
```json
{
  "stress_summary": {
    "average_stress": 28,
    "max_stress": 65,
    "min_stress": 12,
    "current_stress": 25
  },
  "date": "2024-12-29"
}
```

#### get_daily_activity
일일 활동량과 강도를 추적합니다.

**응답 예시:**
```json
{
  "activity_summary": {
    "steps": 12500,
    "floors_climbed": 15,
    "intensity_minutes": {
      "moderate": 45,
      "vigorous": 20
    },
    "calories_burned": 2850,
    "distance_km": 9.2
  }
}
```

#### get_hrv_data
상세한 심박변이도(HRV) 데이터를 조회하여 회복 및 스트레스 상태를 분석합니다.

**응답 예시:**
```json
{
  "hrv_summary": {
    "daily_rmssd": 45,
    "weekly_avg": 42,
    "status": "balanced",
    "trend": "improving"
  },
  "hrv_readings": [
    {
      "timestamp": "2024-12-29 07:00",
      "value": 45,
      "quality": "good"
    }
  ],
  "date": "2024-12-29"
}
```

#### get_respiration_data
하루 동안의 호흡수 데이터 및 패턴을 조회합니다.

**응답 예시:**
```json
{
  "respiration_summary": {
    "daily_avg_breaths_per_min": 14,
    "sleep_avg_breaths_per_min": 12,
    "awake_avg_breaths_per_min": 15,
    "highest_breaths_per_min": 22,
    "lowest_breaths_per_min": 10
  },
  "date": "2024-12-29"
}
```

#### get_spo2_data
하루 동안의 혈중 산소 포화도(SpO2) 수준을 조회합니다.

**응답 예시:**
```json
{
  "spo2_summary": {
    "daily_avg_spo2": 96,
    "sleep_avg_spo2": 95,
    "lowest_spo2": 92,
    "highest_spo2": 98
  },
  "spo2_readings": [
    {
      "timestamp": "2024-12-29 23:00",
      "value": 95,
      "reading_type": "sleep"
    }
  ],
  "date": "2024-12-29"
}
```

### 🎯 훈련 계획 (8개)

#### calculate_training_paces (구버전)
기본적인 훈련 페이스를 계산합니다.

#### calculate_vdot_zones
VDOT 기반 정확한 훈련 구간을 계산합니다.

**응답 예시:**
```json
{
  "vdot": 55.3,
  "race_input": {
    "distance": "10K",
    "time": "38:45",
    "pace_per_km": "3:52"
  },
  "training_zones": {
    "easy": {
      "pace_per_km": "5:10-5:40",
      "description": "Conversational pace for base building",
      "heart_rate_range": "65-79% of max HR"
    },
    "marathon": {
      "pace_per_km": "4:15",
      "description": "Marathon race pace",
      "heart_rate_range": "80-89% of max HR"
    },
    "threshold": {
      "pace_per_km": "3:55",
      "description": "Comfortably hard, sustainable for ~1 hour",
      "heart_rate_range": "88-92% of max HR"
    },
    "interval": {
      "pace_per_km": "3:35",
      "description": "3-5 minute intervals at 3K-5K pace",
      "heart_rate_range": "95-100% of max HR"
    },
    "repetition": {
      "pace_per_km": "3:20",
      "description": "Short, fast repeats for speed development",
      "heart_rate_range": "Not HR based - focus on pace"
    }
  },
  "equivalent_race_times": {
    "5K": "18:30",
    "10K": "38:45",
    "half_marathon": "1:27:00",
    "marathon": "3:12:00"
  }
}
```

#### analyze_threshold_zones
노르웨이 더블 임계점 훈련을 위한 역치 구간을 분석합니다.

**응답 예시:**
```json
{
  "threshold_zones": {
    "threshold_1": {
      "description": "Lower threshold - Marathon to Half Marathon pace",
      "pace_range": "4:15 - 4:05",
      "heart_rate": "152-158 bpm",
      "duration": "15-30 minutes continuous or 3x10-15min intervals",
      "purpose": "Improve aerobic capacity and fatigue resistance"
    },
    "threshold_2": {
      "description": "Upper threshold - 10K to 15K pace",
      "pace_range": "4:00 - 3:50",
      "heart_rate": "162-168 bpm",
      "duration": "8-15 minutes intervals with short recovery",
      "purpose": "Improve lactate buffering and threshold pace"
    }
  },
  "weekly_workout_plan": {
    "tuesday": "Threshold 1: 2x15min at lower threshold with 3min recovery",
    "thursday": "Threshold 2: 5x8min at upper threshold with 90s recovery",
    "saturday": "Long run with threshold segments: Include 3x10min at Threshold 1"
  }
}
```

#### suggest_daily_workout
현재 컨디션에 맞는 일일 훈련을 제안합니다.

**응답 예시:**
```json
{
  "recommended_workout": {
    "description": "VO2max intervals",
    "warmup": "15 minutes easy + 4x100m strides",
    "main": "6x1000m at 5K pace with 2-3min recovery",
    "cooldown": "10 minutes easy",
    "pace": "5K race pace or slightly faster",
    "heart_rate": "Zone 5 (95-100% max HR) during intervals"
  },
  "current_status": {
    "training_phase": "build",
    "readiness_score": 85,
    "recovery_hours_remaining": 0,
    "training_load_ratio": 1.05
  },
  "rationale": "Based on your build phase and current readiness",
  "alternative_options": ["fartlek", "hill repeats", "track workout"]
}
```

#### analyze_workout_quality
완료된 훈련의 실행 품질을 분석합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "workout_summary": {
    "activity_name": "러닝",
    "date": "2025-11-12T20:16:25.0",
    "type": "easy"
  },
  "execution_analysis": {
    "heart_rate": {
      "distribution": {
        "Zone 1": {"time_minutes": 0.8, "percentage": 13.9},
        "Zone 2": {"time_minutes": 2.6, "percentage": 45.5},
        "Zone 3": {"time_minutes": 2.3, "percentage": 40.7}
      },
      "expected": {"Zone 1": 20, "Zone 2": 70, "Zone 3": 10},
      "zones_analysis": {
        "Zone 1": {"assessment": "On target"},
        "Zone 2": {"assessment": "Off target"},
        "Zone 3": {"assessment": "Off target"}
      }
    },
    "pacing": {
      "variation": "1.3%",
      "assessment": "Excellent - very consistent",
      "splits_analyzed": 2
    }
  },
  "recommendations": [
    "Great pacing control - maintain current approach",
    "Keep effort easier to stay in aerobic zones"
  ]
}
```

#### list_training_plans
러닝 훈련 계획 전체 목록을 필터와 함께 조회합니다. 목적 거리나 경험 수준을 지정하면 해당 조건에 맞는 계획만 반환합니다.

**응답 예시:**
```json
{
  "total_available": 7,
  "returned": 3,
  "plans": [
    {
      "id": 345678,
      "name": "12주 하프마라톤 빌드업",
      "distance_type": "half_marathon",
      "experience_level": "intermediate",
      "intensity": "balanced",
      "duration_weeks": 12,
      "target_event_date": "2025-04-13"
    },
    {
      "id": 456789,
      "name": "16주 마라톤 시니어",
      "distance_type": "marathon",
      "experience_level": "advanced",
      "intensity": "high",
      "duration_weeks": 16,
      "target_event_date": "2025-05-18"
    }
  ],
  "filters": {
    "goal_distance": "half_marathon",
    "experience_level": "intermediate"
  },
  "metadata": {
    "total_plans_in_response": 7,
    "plan_ids": [345678, 456789, 567890]
  },
  "note": "Use get_training_plan_overview to inspect a specific plan. Calendar entries contain personal schedule mappings."
}
```

#### get_training_plan_overview
특정 훈련 계획의 주요 정보, 페이즈 구성, 초기 주차 미리보기를 제공합니다.

**응답 예시:**
```json
{
  "plan": {
    "id": 345678,
    "name": "12주 하프마라톤 빌드업",
    "goal_type": "TIME_GOAL",
    "distance_type": "half_marathon",
    "experience_level": "intermediate",
    "duration_weeks": 12,
    "target_event_date": "2025-04-13"
  },
  "phases": [
    {"name": "Base", "weeks": 4, "focus": "유산소 기반 다지기"},
    {"name": "Build", "weeks": 5, "focus": "지구력 + 스피드 향상"},
    {"name": "Peak", "weeks": 2, "focus": "레이스 페이스 최적화"},
    {"name": "Taper", "weeks": 1, "focus": "피로 회복 및 컨디션 극대화"}
  ],
  "schedule_preview": {
    "weeks": [
      {
        "week": 1,
        "focus": "Base",
        "planned_distance_km": 48.0,
        "key_workouts": [
          {"name": "롱런 16km", "distance_km": 16.0},
          {"name": "템포런 6km", "distance_km": 10.0}
        ]
      },
      {
        "week": 2,
        "focus": "Base",
        "planned_distance_km": 50.0,
        "key_workouts": [
          {"name": "롱런 18km", "distance_km": 18.0},
          {"name": "VO2max 인터벌", "distance_km": 8.0}
        ]
      }
    ],
    "preview_weeks": 4,
    "total_weeks": 12,
    "note": "Preview limited to the first few weeks. Request full plan details for complete schedule."
  },
  "metadata": {
    "plan_id": 345678,
    "plan_name": "12주 하프마라톤 빌드업",
    "plan_category": "TRADITIONAL",
    "schedule_weeks_preview": 4
  }
}
```

#### get_training_plan_schedule
훈련 계획의 주차별 스케줄 스냅샷과 개인 캘린더 매핑 정보를 제공합니다.

**응답 예시:**
```json
{
  "plan_id": 345678,
  "plan_name": "12주 하프마라톤 빌드업",
  "schedule": {
    "weeks": [
      {
        "week": 1,
        "planned_distance_km": 48.0,
        "key_workouts": [
          {"name": "롱런 16km", "distance_km": 16.0},
          {"name": "템포런 6km", "distance_km": 10.0}
        ]
      },
      {
        "week": 2,
        "planned_distance_km": 50.0,
        "key_workouts": [
          {"name": "롱런 18km", "distance_km": 18.0},
          {"name": "VO2max 인터벌", "distance_km": 8.0}
        ]
      }
    ],
    "preview_weeks": 6,
    "total_weeks": 12
  },
  "calendar_alignment": {
    "start_date": "2025-01-20",
    "end_date": "2025-04-13",
    "upcoming_workouts": [
      {"date": "2025-01-20", "workout_name": "이지런 8km"},
      {"date": "2025-01-21", "workout_name": "VO2max 인터벌 6x800m"},
      {"date": "2025-01-23", "workout_name": "롱런 16km"}
    ],
    "note": "Limited to upcoming scheduled workouts."
  },
  "metadata": {
    "weeks_requested": 6,
    "plan_category": "TRADITIONAL"
  }
}
```

### 📈 훈련 부하 관리 (3개)

#### analyze_training_load
훈련 부하와 부상 위험을 분석합니다.

**응답 예시:**
```json
{
  "training_load_metrics": {
    "acute_load_atl": 125.5,
    "chronic_load_ctl": 110.2,
    "training_stress_balance": -15.3,
    "atl_ctl_ratio": 1.14,
    "load_status": "Optimal - Good balance"
  },
  "weekly_progression": [
    {"week": "Week -1", "total_load": 450.2, "daily_average": 64.3},
    {"week": "Week -2", "total_load": 425.8, "daily_average": 60.8}
  ],
  "recommendations": {
    "current_state": "Fatigued",
    "injury_risk": "Low",
    "suggested_action": "Maintain current load"
  }
}
```

#### get_training_effect
유산소/무산소 훈련 효과를 분석합니다.

**응답 예시:**
```json
{
  "summary": {
    "average_aerobic_effect": 3.2,
    "average_anaerobic_effect": 1.8,
    "training_focus": "Aerobic base building",
    "aerobic_benefit": "Improving fitness",
    "anaerobic_benefit": "Maintaining fitness",
    "total_activities": 12
  },
  "recommendations": {
    "aerobic": "Maintain current aerobic training",
    "anaerobic": "Add intervals or tempo runs",
    "recovery": "Training load is appropriate"
  }
}
```

#### get_training_load_balance
급성/만성 훈련 부하 균형을 평가합니다.

**응답 예시:**
```json
{
  "training_load_metrics": {
    "acute_load_atl": 125.5,
    "chronic_load_ctl": 110.2,
    "training_stress_balance": -15.3,
    "atl_ctl_ratio": 1.14,
    "load_status": "Optimal - Good balance"
  },
  "weekly_progression": [
    {"week": "Week -1", "total_load": 450.2, "daily_average": 64.3}
  ],
  "recommendations": {
    "current_state": "Fatigued",
    "injury_risk": "Low",
    "suggested_action": "Maintain current load"
  }
}
```

### 👟 장비 관리 (1개)

#### get_gear_insights
러닝화 누적 거리와 교체 알림을 제공합니다. 사용자별 활동 수량을 참고해 신발 교체 시기를 판단할 수 있습니다.

**응답 예시:**
```json
{
  "total_activities": 1264,
  "threshold_km": 800,
  "gear_items_analyzed": 2,
  "gear_summary": [
    {
      "name": "Endorphin Speed 3",
      "brand": "Saucony",
      "distance_km": 735.4,
      "usage_percent": 91.9,
      "activities": 112,
      "last_used": "2025-01-18",
      "lifecycle_status": "warning",
      "recommendation": "Approaching mileage limit – plan a replacement soon."
    },
    {
      "name": "Invincible Run 2",
      "brand": "Nike",
      "distance_km": 512.7,
      "usage_percent": 64.1,
      "activities": 76,
      "last_used": "2025-01-15",
      "lifecycle_status": "ok",
      "recommendation": "Mileage within acceptable range."
    }
  ],
  "alerts": [
    "Endorphin Speed 3 nearing limit with 735 km."
  ],
  "metadata": {
    "include_retired": false,
    "max_items": 5,
    "user_profile_number": "2591602"
  },
  "note": "Consider rotating shoes before the mileage threshold to reduce injury risk."
}
```

### 📉 추이 분석 (1개)

#### get_running_trends
장기간 러닝 퍼포먼스 추이를 분석합니다.

**응답 예시:**
```json
{
  "analysis_period": "6 months",
  "monthly_trends": [
    {
      "month": "2024-12",
      "activity_count": 18,
      "avg_distance_km": 8.5,
      "total_distance_km": 153
    }
  ],
  "overall_trends": {
    "distance_trend": "increasing",
    "consistency": "regular"
  }
}
```

### 📊 고급 메트릭 분석 (2개)

#### analyze_heart_rate_zones
활동 중 심박수 구간 분포를 분석합니다.

**응답 예시:**
```json
{
  "zone_distribution": {
    "Zone 1": {"time_minutes": 5.2, "percentage": 10.0},
    "Zone 2": {"time_minutes": 20.5, "percentage": 40.0},
    "Zone 3": {"time_minutes": 15.3, "percentage": 30.0},
    "Zone 4": {"time_minutes": 8.0, "percentage": 15.0},
    "Zone 5": {"time_minutes": 2.5, "percentage": 5.0}
  }
}
```

#### get_advanced_running_metrics
러닝 다이나믹스 데이터를 조회합니다. (Running Dynamics를 지원하는 디바이스 필요)

**응답 예시:**
```json
{
  "advanced_running_metrics": {
    "stride_length_m": 1.25,
    "vertical_ratio_percent": 8.5,
    "vertical_amplitude_cm": 10.2,
    "ground_contact_time_ms": 245,
    "cadence_spm": 180,
    "ground_contact_balance_percent": 50.2
  },
  "device_support": {
    "running_dynamics_supported": true,
    "device_name": "Forerunner 965"
  }
}
```

### 📱 디바이스 관리 (3개)

#### get_devices
연결된 모든 Garmin 디바이스 정보를 조회합니다.

**응답 예시:**
```json
{
  "devices": [
    {
      "device_id": "123456789",
      "product_name": "Forerunner 965",
      "device_type": "running_watch",
      "last_sync": "2024-12-29 18:30",
      "battery_status": "good",
      "software_version": "20.26"
    },
    {
      "device_id": "987654321",
      "product_name": "HRM-Pro",
      "device_type": "heart_rate_monitor",
      "last_sync": "2024-12-29 07:00"
    }
  ],
  "total_devices": 2
}
```

#### get_primary_training_device
러닝 활동에 사용되는 주요 디바이스 정보를 조회합니다.

**응답 예시:**
```json
{
  "primary_device": {
    "device_id": "123456789",
    "product_name": "Forerunner 965",
    "model": "fenix7",
    "capabilities": {
      "running_dynamics": true,
      "vo2_max": true,
      "training_status": true,
      "race_predictor": true
    },
    "last_used": "2024-12-29 07:00"
  }
}
```

#### get_device_settings
디바이스 설정 및 구성 정보를 조회합니다.

**응답 예시:**
```json
{
  "device_settings": {
    "heart_rate_zones": {
      "zone1_max": 135,
      "zone2_max": 152,
      "zone3_max": 169,
      "zone4_max": 186,
      "zone5_max": 202
    },
    "user_profile": {
      "max_hr": 190,
      "resting_hr": 48,
      "lactate_threshold_hr": 165
    },
    "data_recording": {
      "gps_mode": "smart",
      "recording_interval": "every_second"
    }
  }
}
```

### 💾 데이터 관리 (4개)

#### get_paginated_activities
페이지네이션을 지원하여 대량의 활동 데이터를 조회합니다.

**응답 예시:**
```json
{
  "activities": [
    {
      "activity_id": "12345678",
      "activity_name": "Morning Run",
      "start_time": "2024-12-29 07:00",
      "distance_km": 10.5,
      "duration_seconds": 3150
    }
  ],
  "pagination": {
    "total_count": 150,
    "current_page": 1,
    "total_pages": 8,
    "has_more": true
  }
}
```

#### get_activities_for_date
특정 날짜의 모든 활동을 조회합니다.

**응답 예시:**
```json
{
  "date": "2024-12-29",
  "activities": [
    {
      "activity_id": "12345678",
      "activity_type": "running",
      "start_time": "07:00",
      "distance_km": 10.5,
      "duration": "52:30"
    },
    {
      "activity_id": "12345679",
      "activity_type": "strength_training",
      "start_time": "18:00",
      "duration": "45:00"
    }
  ],
  "total_activities": 2
}
```

#### download_activity_file
활동 데이터를 다양한 파일 형식(TCX, GPX, FIT)으로 다운로드합니다.

**응답 예시 (2025-11-13 실측):**
```json
{
  "activity_id": "20966535017",
  "format": "tcx",
  "data_type": "text",
  "size_bytes": 261042,
  "data": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<TrainingCenterDatabase ...",
  "note": null
}
```

```json
{
  "activity_id": "20966535017",
  "format": "fit",
  "data_type": "binary",
  "size_bytes": 19929,
  "note": "Binary FIT/Original data retrieved successfully. Decode externally if needed."
}
```

**참고:** FIT/Original 형식은 바이너리 데이터를 그대로 반환하며, 필요 시 외부 도구로 디코딩해야 합니다.

대용량 텍스트 파일(TCX/GPX/CSV)은 MCP 응답 한도를 초과하면 자동으로 `overflow://...` 리소스로 오프로드되어 반환됩니다. 이 경우 응답에 포함된 리소스 URI를 사용해 전체 데이터를 스트리밍 방식으로 가져오면 됩니다.

### 🎯 목표 설정 (1개)

#### set_race_goal
레이스 목표를 설정하고 훈련 계획을 수립합니다.

**응답 예시:**
```json
{
  "race_goal": {
    "distance": "half_marathon",
    "target_time": "1:35:00",
    "target_pace_per_km": "4:30",
    "race_date": "2025-03-15",
    "days_until_race": 75
  },
  "training_recommendation": {
    "phase": "build",
    "weeks_until_race": 10,
    "recommended_weekly_volume": "50-60 km",
    "key_workouts": ["Long run", "Tempo run", "Interval training"]
  }
}
```

## 테스트

- 표준 라이브러리 `unittest`를 사용해 핵심 유틸리티에 대한 회귀 테스트를 제공합니다.
- 실행 방법:
  ```bash
  uv run python -m unittest
  ```
- 검증 항목:
  - 거리 단위 변환(`normalize_distance_to_km`)
  - 훈련 계획 목록/요약 전처리 로직
  - 주차별 스케줄 프리뷰 그룹화

## 개발자 정보

### 시스템 요구사항

- Python 3.13+
- macOS, Windows, Linux 지원
- Garmin Connect 계정 (2FA 비활성화 권장)

### 의존성

- `garminconnect>=0.2.34`
- `garth>=0.5.17,<0.6.0`
- `mcp[cli]>=1.7.0`
- `python-dotenv>=1.0.0`

### 문제 해결

자세한 문제 해결 방법은 [사용자 가이드](README_GUIDE.md#문제-해결)를 참조하세요.

## 라이선스

MIT License

## 기여하기

프로젝트에 기여하고 싶으시다면 Pull Request를 보내주세요. 모든 기여를 환영합니다!

---

💡 **도움이 필요하신가요?** [사용자 가이드](README_GUIDE.md)와 [프롬프트 템플릿](PROMPTS.md)을 확인해보세요!
