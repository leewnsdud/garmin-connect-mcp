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
        "GARMIN_PASSWORD": [Garmin Connect 비밀번호]
      }
    }
  }
}
```

## 사용 가능한 도구 (총 39개)

### 🏃 퍼포먼스 분석 (9개)

#### get_personal_records
개인 최고 기록을 조회합니다.

**응답 예시:**
```json
{
  "personal_records": {
    "5K": {
      "time": "18:45",
      "seconds": 1125,
      "date": "2024-03-15",
      "activity_id": "12345678"
    },
    "10K": {
      "time": "39:30",
      "seconds": 2370,
      "date": "2024-02-10",
      "activity_id": "12345679"
    },
    "half_marathon": {
      "time": "1:28:15",
      "seconds": 5295,
      "date": "2023-11-20",
      "activity_id": "12345680"
    },
    "marathon": {
      "time": "3:15:42",
      "seconds": 11742,
      "date": "2023-10-15",
      "activity_id": "12345681"
    }
  }
}
```

#### get_vo2max
현재 VO2 Max 값과 추이를 조회합니다.

**응답 예시:**
```json
{
  "vo2_max": 55.3,
  "vo2_max_trend": {
    "current": 55.3,
    "week_ago": 54.8,
    "month_ago": 53.9,
    "trend": "improving"
  },
  "race_predictions": {
    "5K": "18:30",
    "10K": "38:45",
    "half_marathon": "1:27:00",
    "marathon": "3:12:00"
  },
  "date": "2024-12-29"
}
```

#### get_training_status
현재 훈련 상태와 회복 시간을 확인합니다.

**응답 예시:**
```json
{
  "training_status": {
    "status": "productive",
    "fitness_level": "5",
    "load_balance": "optimal",
    "recovery_time": 18,
    "training_effect": {
      "aerobic": 3.2,
      "anaerobic": 1.8
    }
  },
  "training_readiness": {
    "score": 85,
    "level": "high",
    "message": "Great day for hard training"
  }
}
```

#### get_lactate_threshold
젖산 역치 페이스와 심박수 데이터를 조회합니다.

**응답 예시:**
```json
{
  "lactate_threshold": {
    "pace_per_km": "4:05",
    "heart_rate_bpm": 165,
    "speed_kmh": 14.6
  },
  "date": "2024-12-29"
}
```

#### get_race_predictions
현재 체력 기준 예상 레이스 기록을 제공합니다.

**응답 예시:**
```json
{
  "race_predictions": {
    "5K": {
      "predicted_time": "18:30",
      "race_readiness_level": "peak",
      "race_readiness_state": "ready"
    },
    "10K": {
      "predicted_time": "38:45",
      "race_readiness_level": "good",
      "race_readiness_state": "ready"
    }
  },
  "current_vo2_max": 55.3
}
```

#### get_training_readiness
훈련 준비도와 권장사항을 제공합니다.

**응답 예시:**
```json
{
  "training_readiness": {
    "score": 82,
    "level": "high",
    "message": "Good day for quality workout",
    "recovery_level": "adequate",
    "training_load_balance": "optimal",
    "sleep_quality": "good",
    "hrv_status": "balanced"
  },
  "recovery_time_hours": 12
}
```

#### get_recovery_time
권장 회복 시간을 확인합니다.

**응답 예시:**
```json
{
  "recovery_info": {
    "recovery_time_hours": 24,
    "recovery_time_formatted": "24 hours",
    "fully_recovered_at": "2024-12-30 18:30"
  },
  "last_activity": {
    "activity_name": "Evening Run",
    "activity_type": "running",
    "start_time": "2024-12-29 18:00",
    "training_effect": {
      "aerobic": 3.5,
      "anaerobic": 2.1
    }
  }
}
```

#### get_endurance_score
유산소 지구력 능력을 나타내는 지구력 점수를 조회합니다.

**응답 예시:**
```json
{
  "endurance_score": {
    "score": 68,
    "level": "good",
    "percentile": 75,
    "description": "Your endurance capability for sustained aerobic efforts"
  },
  "date": "2024-12-29"
}
```

#### get_hill_score
언덕 오르기 능력을 나타내는 힐 스코어를 조회합니다.

**응답 예시:**
```json
{
  "hill_score": {
    "score": 72,
    "level": "very_good",
    "percentile": 80,
    "description": "Your uphill running capability and power"
  },
  "date": "2024-12-29"
}
```

### 📊 활동 데이터 (4개)

#### get_recent_running_activities
최근 러닝 활동 목록을 조회합니다.

**응답 예시:**
```json
[
  {
    "activityId": 12345678,
    "activityName": "Morning Run",
    "startTimeLocal": "2024-12-29 07:30",
    "distance": 10000,
    "duration": 2700,
    "averageSpeed": 3.7,
    "averageHR": 145,
    "aerobicTrainingEffect": 3.2
  }
]
```

#### get_activity_summary
특정 활동의 기본 정보를 조회합니다.

**응답 예시:**
```json
{
  "activity_id": "12345678",
  "activity_name": "Morning Run",
  "activity_type": "running",
  "distance_km": 10.5,
  "duration_formatted": "52:30",
  "average_pace_per_km": "5:00",
  "average_speed_kmh": 12.0,
  "elevation_gain_m": 125,
  "calories": 650,
  "average_hr": 145,
  "max_hr": 172
}
```

#### get_activity_details
활동의 상세 메트릭과 분할 구간을 조회합니다.

**응답 예시:**
```json
{
  "activity_id": "12345678",
  "splits": [
    {
      "distance": 1000,
      "time": 300,
      "pace": "5:00",
      "averageHR": 140
    }
  ],
  "weather": {
    "temperature": 18,
    "humidity": 65,
    "wind_speed": 10
  },
  "performance_metrics": {
    "normalized_power": 245,
    "training_stress_score": 85,
    "intensity_factor": 0.82
  }
}
```

#### get_weekly_running_summary
주간 러닝 요약 정보와 트렌드를 제공합니다.

**응답 예시:**
```json
{
  "week_summary": {
    "total_distance_km": 45.5,
    "total_time_hours": 4.2,
    "total_elevation_gain_m": 380,
    "average_pace_per_km": "5:30",
    "activity_count": 5
  },
  "weekly_trend": {
    "distance_change_percent": 8.5,
    "pace_improvement": true,
    "consistency_score": 85
  },
  "week_period": "2024-12-23 to 2024-12-29"
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

### 🎯 훈련 계획 (5개)

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

**응답 예시:**
```json
{
  "workout_summary": {
    "activity_name": "Track Intervals",
    "date": "2024-12-29",
    "type": "interval"
  },
  "execution_analysis": {
    "distance": {
      "planned": "10 km",
      "actual": "10.2 km",
      "accuracy": "98.0%",
      "assessment": "Good"
    },
    "pace": {
      "planned": "3:35",
      "actual": "3:37",
      "accuracy": "99.1%",
      "assessment": "Excellent"
    },
    "pacing": {
      "variation": "2.5%",
      "assessment": "Excellent - very consistent"
    }
  },
  "quality_score": {
    "overall_score": 95.5,
    "grade": "A+"
  },
  "recommendations": ["Good workout execution - maintain this consistency"],
  "key_takeaways": ["Excellent workout execution!", "Pace control was on point"]
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

**응답 예시:**
```json
{
  "activity_id": "12345678",
  "file_format": "tcx",
  "file_size_bytes": 125000,
  "download_url": "file://activities/12345678.tcx",
  "downloaded": true,
  "message": "Activity file downloaded successfully"
}
```

**참고:** 이 tool은 파일을 로컬에 저장하고 경로를 반환합니다.

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

## 개발자 정보

### 시스템 요구사항

- Python 3.13+
- macOS, Windows, Linux 지원
- Garmin Connect 계정 (2FA 비활성화 권장)

### 의존성

- `garminconnect>=0.2.26`
- `garth>=0.5.3`
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
