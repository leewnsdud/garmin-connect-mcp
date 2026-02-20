# garmin-mcp

Garmin Connect 러닝 데이터를 LLM에 제공하는 MCP(Model Context Protocol) 서버입니다.

Claude Desktop 등 MCP 클라이언트와 연동하여 러닝 훈련 분석, 계획 수립, 워크아웃 생성 등을 수행할 수 있습니다.

## 주요 기능

- **러닝 활동 조회** - 최근 활동, 날짜별 조회, 상세 분석, 스플릿 데이터 (47개 필드: 페이스, 심박, 케이던스, 러닝 다이나믹스, 파워, HR존, GAP, 경사도, 스태미나, 온도 등)
- **트레일러닝 분석** - ClimbPro 경사 구간 분석, 등급별 난이도, Grade Adjusted Pace, Run/Walk Detection, 날씨 조건
- **주간/월간 요약** - 볼륨 트렌드, 전월 대비 비교
- **훈련 지표** - VO2max, 훈련 상태, 훈련 준비도, 레이스 예측, 젖산역치
- **심박/HRV** - 일간 심박, 심박변이도, 활동별 심박존 분포
- **웰니스** - 수면, 스트레스, 바디배터리, SpO2
- **개인 기록/목표** - PR, 피트니스 목표
- **워크아웃 생성** - 시간/거리 기반 인터벌, 템포 등 구조화된 워크아웃을 Garmin 워치에 전송 (페이스/심박/케이던스/파워 타겟)
- **러닝화 관리** - 신발별 누적 거리 + 마모율 추적
- **개인정보 보호** - 모든 API 응답에서 PII(소유자 이름, 프로필 ID, GPS 좌표) 자동 필터링

## 요구 사항

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- Garmin Connect 계정

## 설치

```bash
git clone https://github.com/leewnsdud/garmin-connect-mcp.git
cd garmin-connect-mcp
uv sync
```

## 인증

최초 1회 인증이 필요합니다.

```bash
uv run python scripts/auth.py
```

이메일, 비밀번호를 입력하면 OAuth 토큰이 `~/.garminconnect/`에 저장됩니다. MFA 사용 시 코드 입력 프롬프트가 나타납니다.

> 토큰이 만료되면 다시 실행하거나, `.env` 파일에 자격증명을 설정하면 자동 갱신됩니다.

## Claude Desktop 연동

`~/Library/Application Support/Claude/claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "garmin-mcp": {
      "command": "/Users/<username>/.local/bin/uv",
      "args": [
        "--directory",
        "/path/to/garmin-mcp",
        "run",
        "garmin-mcp"
      ]
    }
  }
}
```

> `uv`의 전체 경로를 사용해야 합니다. `which uv`로 확인하세요.

설정 후 Claude Desktop을 재시작하면 도구가 활성화됩니다.

## 환경 변수 (선택)

`.env.example`을 참고하여 `.env` 파일을 생성합니다.

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `GARMIN_EMAIL` | Garmin Connect 이메일 | - |
| `GARMIN_PASSWORD` | Garmin Connect 비밀번호 | - |
| `GARMIN_TOKEN_DIR` | 토큰 저장 경로 | `~/.garminconnect` |
| `GARMINTOKENS` | Base64 인코딩 토큰 (CI/Docker용) | - |

## 제공 도구 (24개)

### Activities

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `get_recent_activities` | 최근 러닝 활동 목록 (GAP, RWD 포함) | `count` (기본 20, 최대 100) |
| `get_activities_by_date` | 날짜 범위로 러닝 활동 조회 | `start_date`, `end_date` |
| `get_activity_detail` | 활동 상세 정보 (스태미나, 임팩트 로드 포함) | `activity_id` |
| `get_activity_splits` | km별 스플릿 데이터 | `activity_id` |
| `get_activity_weather` | 활동 중 날씨 조건 (온도, 습도, 풍속) | `activity_id` |
| `get_activity_typed_splits` | ClimbPro 경사 구간 분석 (등급, GAP) | `activity_id` |

### Summary

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `get_weekly_running_summary` | 주간 러닝 요약 | `end_date`, `weeks` (최대 12) |
| `get_monthly_running_summary` | 월간 러닝 요약 + 전월 비교 | `year`, `month` |

### Training

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `get_training_status` | 훈련 상태 | `date` |
| `get_training_readiness` | 훈련 준비도 점수 | `date` |
| `get_vo2max_and_fitness` | VO2max + 피트니스 나이 | `date` |
| `get_race_predictions` | 5K/10K/하프/풀 예상 기록 | 없음 |
| `get_lactate_threshold` | 젖산역치 심박/페이스 | `start_date`, `end_date` |

### Heart Rate

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `get_heart_rate_data` | 일간 심박 데이터 | `date` |
| `get_hrv_data` | 심박변이도 (HRV) | `date` |
| `get_activity_hr_zones` | 활동별 심박존 분포 | `activity_id` |

### Wellness

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `get_sleep_data` | 수면 데이터 | `date` |
| `get_daily_wellness` | 스트레스/바디배터리/SpO2/호흡수 | `date` |
| `get_weekly_wellness_summary` | 주간 웰니스 트렌드 | `end_date`, `weeks` (최대 4) |

### Records & Goals

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `get_personal_records` | 개인 기록 (1K~마라톤) | 없음 |
| `get_goals` | 피트니스 목표 | `status` (active/completed/all) |

### Workout

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `create_running_workout` | 워크아웃 생성 및 Garmin에 업로드 (시간/거리 기반, 페이스/심박/케이던스/파워 타겟) | `name`, `steps`, `description` |
| `get_workouts` | 저장된 워크아웃 목록 | `count` (기본 20, 최대 100) |

### Gear

| 도구 | 설명 | 주요 파라미터 |
|------|------|--------------|
| `get_running_gear` | 러닝화 목록 + 누적 거리 + 마모율 | 없음 |

## 워크아웃 생성 가이드

`create_running_workout`으로 구조화된 러닝 워크아웃을 생성하고 Garmin 워치에 동기화할 수 있습니다.

### Step 타입

| 타입 | 설명 |
|------|------|
| `warmup` | 워밍업 |
| `interval` | 인터벌 (고강도) |
| `recovery` | 회복 조깅 |
| `rest` | 완전 휴식 (서서 쉬기) |
| `cooldown` | 쿨다운 |
| `repeat` | 반복 그룹 |

### 종료 조건 (Step 기간)

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `duration_seconds` | int | 시간 기반 | `"duration_seconds": 300` (5분) |
| `distance_meters` | int | 거리 기반 | `"distance_meters": 1000` (1km) |

하나의 워크아웃에서 시간/거리 기반 step을 혼합 사용할 수 있습니다.

### Target 타입

| 타입 | 값 형식 | 예시 |
|------|---------|------|
| `pace` | min:sec/km | `"min": "4:30", "max": "4:50"` |
| `heart_rate` | bpm | `"min": 140, "max": 155` |
| `cadence` | spm | `"min": 170, "max": 185` |
| `power` | watts | `"min": 280, "max": 320` |

### 옵션

- **워크아웃 메모**: `description` 파라미터로 전체 설명 추가
- **Step 메모**: 각 step에 `"description": "메모"` 추가
- **마지막 회복 건너뛰기**: repeat step에 `"skip_last_rest": true` 추가

### 예시: 4x1km 거리 기반 인터벌

```json
{
  "name": "4x1km Intervals @4:30",
  "description": "10K 레이스 대비 VO2max 인터벌",
  "steps": [
    {
      "type": "warmup",
      "duration_seconds": 600,
      "description": "가볍게 조깅"
    },
    {
      "type": "repeat",
      "count": 4,
      "skip_last_rest": true,
      "steps": [
        {
          "type": "interval",
          "distance_meters": 1000,
          "target": { "type": "pace", "min": "4:20", "max": "4:40" },
          "description": "목표 페이스 유지"
        },
        {
          "type": "recovery",
          "duration_seconds": 120,
          "description": "천천히 조깅으로 회복"
        }
      ]
    },
    {
      "type": "cooldown",
      "duration_seconds": 600,
      "description": "마무리 조깅"
    }
  ]
}
```

> 상세 워크아웃 생성 가이드는 [AGENTS.md](./AGENTS.md#workout-creation-guide)를, 전체 도구 요청/응답 규격은 [TOOL_SPEC.md](./TOOL_SPEC.md)를 참조하세요.

## 활용 예시

Claude Desktop에서 다음과 같이 활용할 수 있습니다:

- "이번 주 러닝 요약해줘"
- "최근 3개월 주간 볼륨 트렌드 분석해줘"
- "내 VO2max 기준으로 Jack Daniels VDOT 훈련 페이스 계산해줘"
- "최근 활동들의 심박존 분포를 보고 80/20 비율을 지키고 있는지 확인해줘"
- "내일 4x1km 인터벌 워크아웃 만들어줘"
- "내 러닝화 중 교체 시기가 된 것이 있는지 확인해줘"
- "수면과 훈련 준비도의 상관관계를 분석해줘"
- "최근 트레일러닝의 경사 구간별 성과를 분석해줘"
- "트레일러닝에서 걷기/달리기 비율을 확인해줘"

## 지원하는 러닝 훈련 방법론

| 방법론 | 활용 데이터 |
|--------|------------|
| Jack Daniels VDOT | VO2max, PR, 레이스 예측 |
| Norwegian Double Threshold | 젖산역치, 심박존 |
| 80/20 Training | 심박존 분포 |
| Hanson's Method | 주간/월간 볼륨, 페이스 트렌드 |
| Pfitzinger | 주간 볼륨, 장거리 런 분석 |
| 트레일/울트라 분석 | ClimbPro 경사 구간, 날씨, RWD, GAP |

## 개발

```bash
# 코드 수정 후 패키지 재설치
uv sync --reinstall-package garmin-mcp

# Claude Desktop 재시작으로 MCP 서버 반영
```

## 개인정보 보호

모든 Garmin API 응답에서 다음 개인정보 필드가 자동으로 제거됩니다:

- **소유자 정보**: `ownerId`, `ownerFullName`, `ownerDisplayName`, `userId`, 프로필 이미지 URL
- **프로필 ID**: `userProfilePK`, `userProfileId`, `profileId`, `profileNumber`
- **사용자 정보**: `displayName`, `fullName`, `userPro`, `userRoles`
- **GPS 좌표**: `startLatitude`, `startLongitude`, `endLatitude`, `endLongitude`

이 필터링은 `src/garmin_mcp/sanitize.py`의 `strip_pii()` 함수를 통해 재귀적으로 처리됩니다.

## 기술 스택

- [python-garminconnect](https://github.com/cyberjunky/python-garminconnect) - Garmin Connect API 클라이언트
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 서버 프레임워크
- [uv](https://docs.astral.sh/uv/) - Python 패키지 매니저
- [garth](https://github.com/matin/garth) - OAuth 토큰 관리

## 라이선스

MIT
