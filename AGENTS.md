# Garmin Running MCP Server

Garmin Connect 러닝 데이터를 제공하는 MCP(Model Context Protocol) 서버.
러닝 훈련 분석, 계획 수립, 워크아웃 생성에 활용한다.

---

## Project structure

```
src/garmin_mcp/
  __init__.py          # FastMCP 서버 엔트리포인트, stdio transport
  auth.py              # OAuth 인증 (토큰 → 자격증명 순서)
  client.py            # Garmin API 래퍼 (429 재시도, 날짜 검증)
  tools/
    __init__.py        # 전체 도구 모듈 등록
    activities.py      # 활동 조회/상세 (4 tools)
    summary.py         # 주간/월간 요약 (2 tools)
    training.py        # 훈련 지표 (5 tools)
    heart_rate.py      # 심박/HRV (3 tools)
    wellness.py        # 수면/스트레스/바디배터리 (3 tools)
    records.py         # PR/목표 (2 tools)
    workout.py         # 워크아웃 생성/조회 (2 tools)
    gear.py            # 러닝화 관리 (1 tool)
scripts/
  auth.py              # 사전 인증 CLI (최초 1회 실행)
```

## Setup

```sh
uv sync                            # 의존성 설치
uv run python scripts/auth.py      # Garmin 인증 (최초 1회)
uv run garmin-mcp                  # MCP 서버 실행
```

## Build & reinstall

코드 변경 후 반드시 재설치해야 반영된다:

```sh
uv sync --reinstall-package garmin-mcp
```

Claude Desktop 등 MCP 클라이언트는 서버 프로세스를 재시작해야 새 코드가 적용된다.

---

## MCP tools reference

총 22개 도구. 모든 날짜 파라미터는 `YYYY-MM-DD` 형식. 기본값은 오늘.

### Activities

| Tool | Parameters | Returns | Description |
|------|-----------|---------|-------------|
| `get_recent_activities` | `count: int = 20` (max 100) | `list[dict]` | 최근 러닝 활동. 러닝만 필터링하여 반환. |
| `get_activities_by_date` | `start_date: str`, `end_date: str` | `list[dict]` | 날짜 범위 러닝 활동 조회. |
| `get_activity_detail` | `activity_id: int` | `dict` | 단일 활동 상세. 페이스, 심박, 케이던스, 파워, 고도, 보폭, 지면접촉시간, 온도, GPS 좌표 포함. |
| `get_activity_splits` | `activity_id: int` | `dict` | km별 스플릿 데이터. 네거티브/포지티브 스플릿 분석용. |

### Summary

| Tool | Parameters | Returns | Description |
|------|-----------|---------|-------------|
| `get_weekly_running_summary` | `end_date: str = ""`, `weeks: int = 1` (max 12) | `list[dict]` | 주간 러닝 요약. 거리, 횟수, 평균페이스, 고도, 최장거리 런 포함. |
| `get_monthly_running_summary` | `year: int = 0`, `month: int = 0` | `dict` | 월간 요약 + 주별 breakdown + 전월 대비 변화율. |

### Training

| Tool | Parameters | Returns | Description |
|------|-----------|---------|-------------|
| `get_training_status` | `date: str = ""` | `dict` | 훈련 상태: Productive, Maintaining, Overreaching, Detraining, Recovery, Peaking, Unproductive. |
| `get_training_readiness` | `date: str = ""` | `list[dict]` | 훈련 준비도. 수면, 회복, 훈련부하, HRV 기반 점수. |
| `get_vo2max_and_fitness` | `date: str = ""` | `dict` | VO2max 추정치 + 피트니스 나이. Jack Daniels VDOT 계산에 활용. |
| `get_race_predictions` | 없음 | `dict` | 5K, 10K, 하프마라톤, 풀마라톤 예상 기록. |
| `get_lactate_threshold` | `start_date: str = ""`, `end_date: str = ""` | `dict` | 젖산역치 심박수/페이스. 역치 훈련 설계에 활용. |

### Heart Rate

| Tool | Parameters | Returns | Description |
|------|-----------|---------|-------------|
| `get_heart_rate_data` | `date: str = ""` | `dict` | 일간 심박 + 안정시 심박(RHR). |
| `get_hrv_data` | `date: str = ""` | `dict` | 심박변이도(HRV). 높을수록 회복 양호. |
| `get_activity_hr_zones` | `activity_id: int` | `dict` | 활동별 심박존 분포(%). 80/20 강도 분석에 필수. |

### Wellness

| Tool | Parameters | Returns | Description |
|------|-----------|---------|-------------|
| `get_sleep_data` | `date: str = ""` | `dict` | 수면 시간, 단계(deep/light/REM), 수면 점수. |
| `get_daily_wellness` | `date: str = ""` | `dict` | 스트레스, 바디배터리, SpO2, 호흡수를 한번에 조회. |
| `get_weekly_wellness_summary` | `end_date: str = ""`, `weeks: int = 1` (max 4) | `list[dict]` | 주간 웰니스 트렌드. 일별 스트레스/바디배터리/수면점수/안정시심박 포함. |

### Records & Goals

| Tool | Parameters | Returns | Description |
|------|-----------|---------|-------------|
| `get_personal_records` | 없음 | `list[dict]` | 개인 기록(PR). 1K, 1마일, 5K, 10K, 하프, 풀 등 거리별 최고기록. |
| `get_goals` | `status: str = "active"` | `list[dict]` | 피트니스 목표. `active`, `completed`, `all` 필터. |

### Workout

| Tool | Parameters | Returns | Description |
|------|-----------|---------|-------------|
| `create_running_workout` | `name: str`, `steps: list[dict]`, `description: str = ""` | `dict` | 워크아웃 생성 후 Garmin Connect 업로드. Garmin 워치에 동기화됨. |
| `get_workouts` | `count: int = 20` (max 100) | `list[dict]` | 저장된 워크아웃 목록 조회. |

### Gear

| Tool | Parameters | Returns | Description |
|------|-----------|---------|-------------|
| `get_running_gear` | 없음 | `list[dict]` | 러닝화 목록. 신발별 누적 거리/활동 수 포함. 교체시기 판단용(보통 500-800km). |

---

## Workout creation guide

`create_running_workout`의 `steps` 파라미터 구조.

### Step types

- `warmup` — 워밍업
- `interval` — 인터벌 (고강도)
- `recovery` — 회복 조깅
- `cooldown` — 쿨다운
- `repeat` — 반복 그룹 (`count` + 중첩 `steps` 필요)

### Target types (선택)

각 step에 `target` 객체를 추가하여 목표 설정:

```json
{"type": "pace", "min": "4:30", "max": "4:50"}
{"type": "heart_rate", "min": 140, "max": 155}
{"type": "cadence", "min": 170, "max": 185}
```

- pace의 min/max는 `분:초/km` 형식 문자열
- heart_rate는 bpm 정수
- cadence는 spm 정수

### Options

- **워크아웃 설명**: 최상위 `description` 파라미터
- **step별 메모**: 각 step에 `"description": "메모 내용"`
- **마지막 회복 건너뛰기**: repeat step에 `"skip_last_rest": true`

### Example: 4x1km interval

```json
{
  "name": "4x1km @4:30",
  "description": "VO2max 인터벌 훈련",
  "steps": [
    {"type": "warmup", "duration_seconds": 600, "description": "가볍게 조깅"},
    {
      "type": "repeat", "count": 4, "skip_last_rest": true,
      "steps": [
        {"type": "interval", "duration_seconds": 270, "target": {"type": "pace", "min": "4:20", "max": "4:40"}},
        {"type": "recovery", "duration_seconds": 120}
      ]
    },
    {"type": "cooldown", "duration_seconds": 600}
  ]
}
```

---

## Running training methodologies

이 서버의 데이터로 분석 가능한 러닝 훈련 방법론:

| 방법론 | 핵심 활용 도구 |
|--------|--------------|
| **Jack Daniels VDOT** | `get_vo2max_and_fitness`, `get_personal_records`, `get_race_predictions` |
| **Norwegian Double Threshold** | `get_lactate_threshold`, `get_activity_hr_zones`, `create_running_workout` |
| **80/20 Training** | `get_activity_hr_zones`, `get_weekly_running_summary` |
| **Hanson's Method** | `get_weekly_running_summary`, `get_monthly_running_summary`, `get_activity_splits` |
| **Pfitzinger** | `get_weekly_running_summary`, `get_monthly_running_summary`, `get_recent_activities` |

---

## Development notes

### Authentication flow

1. `scripts/auth.py` — 이메일/비밀번호로 로그인, `~/.garminconnect/`에 OAuth 토큰 저장
2. 서버 시작 시 `auth.py`가 저장된 토큰으로 자동 로그인
3. 토큰 만료 시 `GARMIN_EMAIL`/`GARMIN_PASSWORD` 환경변수로 재인증 시도
4. 모두 실패 시 `RuntimeError` 발생

### API response structure differences

Garmin API는 목록 조회와 상세 조회의 응답 구조가 다르다:

- **목록** (`get_activities`): 플랫 구조 — `activity["distance"]`, `activity["averageHR"]`
- **상세** (`get_activity`): 중첩 구조 — `activity["summaryDTO"]["distance"]`, `activity["activityTypeDTO"]["typeKey"]`

새 도구 추가 시 반드시 실제 API 응답을 확인하여 올바른 키 경로를 사용할 것.

### Garmin workout target type IDs

라이브러리(`garminconnect.workout`)의 `TargetType` 상수와 실제 Garmin API가 불일치한다:

| 용도 | 올바른 targetTypeId | targetTypeKey |
|------|-------------------|---------------|
| 타겟 없음 | 1 | `no.target` |
| 심박수 | 2 | `heart.rate.zone` |
| 케이던스 | 3 | `cadence` |
| 페이스 | **6** | `pace.zone` |

> 라이브러리는 `TargetType.SPEED = 4`로 정의하지만 실제 페이스 타겟은 **6**이다. 4를 사용하면 심박수로 잘못 매핑됨.

### Return type pitfalls

일부 Garmin API는 `dict`를 반환할 것 같지만 실제로는 `list`를 반환한다:

- `get_personal_record()` → `list[dict]`
- `get_training_readiness()` → `list[dict]`

새 도구 추가 시 실제 반환 타입을 확인하고 MCP 도구의 타입 힌트와 일치시킬 것.
