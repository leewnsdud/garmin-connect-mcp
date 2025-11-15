# Garmin Connect MCP 프롬프트 템플릿 (훈련 계획 특화 개정판)

이 문서는 본 MCP 서버가 제공하는 도구들을 활용해 마라톤(및 러닝 전반) 훈련 계획을 수립·운영·점검하는 데 바로 사용할 수 있는 프롬프트 템플릿을 모아 둔 것입니다.

핵심 원칙:
- 데이터 기반: 최근 활동, 주간/월간 추이, VO2 Max, 젖산 역치, 훈련 상태/부하/회복, 장치 지원, 러닝화 사용 데이터 등 MCP 도구를 통해 직접 확인 후 처방합니다.
- 프레임워크 기반: 널리 쓰이는 훈련 체계(잭 다니엘스, 피츠징어, 한슨스, 80/20, 노르웨이식 더블 임계점, 카노바, 해럴드 히그돈)를 상황에 맞게 적용합니다.
- 적응형 운영: 일/주 단위로 준비도(Training Readiness), ATL/CTL, 수면/HRV/스트레스 등을 반영해 가감합니다.

---

## 1) 사전 진단 프롬프트 (Baseline)
훈련 설계 전에 현재 상태를 파악합니다.

```text
내 최근 상태 기반으로 훈련 처방에 필요한 핵심 지표를 정리해줘.
- 다음 MCP 도구들을 호출해 데이터를 요약해: 
  - get_personal_records, get_running_trends, get_weekly_running_summary
  - get_training_status, get_training_readiness, get_recovery_time, get_training_load_balance, get_training_effect
  - get_vo2max, get_race_predictions, get_lactate_threshold (없으면 calculate_vdot_zones로 근사)
  - get_primary_training_device (러닝 다이내믹스 지원 여부), get_advanced_running_metrics (있으면 요약)
  - get_gear_insights (러닝화 누적 거리/교체 경고)
- 핵심만 표로 요약하고, 결론/리스크/권장사항 5줄 이하로 정리해줘.
```

권장 도구 매핑
- 퍼포먼스/역치: `get_vo2max`, `get_race_predictions`, `get_lactate_threshold`, `calculate_vdot_zones`, `calculate_training_paces`
- 부하/준비/회복: `get_training_status`, `get_training_readiness`, `get_recovery_time`, `get_training_load_balance`, `get_training_effect`, `get_weekly_running_summary`
- 활동/세부: `get_recent_running_activities`, `get_paginated_activities`, `get_activity_details`, `analyze_heart_rate_zones`, `analyze_workout_quality`
- 장치/기어: `get_primary_training_device`, `get_devices`, `get_advanced_running_metrics`, `get_gear_insights`

---

## 2) 마라톤 훈련 프레임워크 요약
- 잭 다니엘스(Jack Daniels): VDOT 기반 페이스/존. Q-세션(템포/인터벌/반복) + 기본 주행. 페이즈(기초→구축→피킹→테이퍼).
- 피츠징어(Pfitzinger): 중상급용. 메조사이클 운영, 주중 미들롱런, 롱런 30~35km, MP(마라톤 페이스) 주행, 튠업 레이스.
- 한슨스(Hansons): 누적 피로 개념. 롱런 길이 제한(~26km) 대신 평일 품질 세션(스피드/스트렝스/MP 템포)과 주당 빈도.
- 80/20(Seiler 계열): 80% 저강도(Easy/Recovery), 20% 고강도(Threshold/VO2). 부상 위험 낮추고 지속성 확보.
- 노르웨이 더블 임계점: T1/T2 이중 임계 강도(낮은 LT, 높은 LT) 이틀 반복 또는 하루 2회. 정밀 페이스·젖산 관리.
- 카노바(Canova): 마라톤 특이적 지구력. 롱런에서 MP 유지, 페이스 변형(스테디/진자/대체), 장거리 MP 템포 비중↑.
- 해럴드 히그돈(Hal Higdon): 입문/초중급 친화. 간단한 주간 구성, 안전한 볼륨 상승, 롱런 점진 증가.
- 테이퍼링: 보통 2~3주. 볼륨↓, 빈도 유지, 강도 소폭 유지. 개인 반응에 따라 조정.

---

## 3) 데이터 요구사항 → MCP 도구 연결 예시
- 최근 성능/기록: `get_personal_records`, `get_running_trends`, `get_recent_running_activities`
- 역치/VDOT/페이스: `get_lactate_threshold`(없으면 `calculate_vdot_zones`), `calculate_training_paces`
- 부하/준비/회복: `get_training_status`, `get_training_readiness`, `get_recovery_time`, `get_training_load_balance`, `get_training_effect`
- 주간/월간 요약: `get_weekly_running_summary`, `get_running_trends`
- 장치/메트릭: `get_primary_training_device`, `get_advanced_running_metrics`
- 러닝화/교체: `get_gear_insights`
- 활동 분석/검증: `get_activity_details`, `analyze_heart_rate_zones`, `analyze_workout_quality`
- 자료 추출/내보내기: `download_activity_file`(tcx/gpx/fit)

---

## 4) 계획 생성 프롬프트 (프레임워크 선택)
```text
내 목표와 제약을 반영해 가장 적합한 마라톤 훈련 프레임워크를 선정해줘.
- 입력: 목표 거리/기록, 남은 주수, 주당 가능 일수, 주당 시간/거리 상한, 부상 이력, 선호도(롱런/템포/인터벌)
- 호출: 사전 진단 프롬프트로 데이터 확보 후, 
  (잭 다니엘스 / 피츠징어 / 한슨스 / 80/20 / 노르웨이 더블 임계점 / 카노바 / 히그돈) 중 1~2개 추천
- 선정 근거를 5줄 내외로 요약해줘.
```

---

## 5) 거시계획(매크로사이클) 생성 프롬프트
```text
[남은 N주] 동안의 거시 계획을 만들어줘.
- 페이즈: Base→Build→Peak→Taper 구조(또는 선택 프레임워크의 페이즈)
- 각 페이즈별: 주차 범위, 주당 목표 거리와 시간, 핵심 세션(예: MP, T1/T2, VO2, 롱런 변형), 적응 목표
- MCP 도구로 산출 근거 표시: calculate_vdot_zones, get_training_load_balance, get_weekly_running_summary 등
```

---

## 6) 주간 계획(미시계획) 생성 프롬프트
```text
다음 주 구체 훈련 계획을 만들어줘.
- 입력: VDOT 또는 목표 레이스 기록, 주간 거리 상한, 주당 빈도, 일정 제약(요일/시간)
- 실행: calculate_vdot_zones / calculate_training_paces로 페이스 산정
- 일자별 처방: 세션명, 거리/시간, 페이스 범위, HR/RPE 보완, 휴식/크로스트레이닝 포함
- 안전장치: get_training_readiness, get_recovery_time, get_training_load_balance 반영해 과부하 Guardrail 제시
```

---

## 7) 세부 세션 템플릿 프롬프트
- 임계(Threshold, T1/T2):
```text
내 임계 기준으로 T1/T2 세션을 2안 제안해줘.
- 데이터: get_lactate_threshold(없으면 calculate_vdot_zones), calculate_training_paces
- 형식: (예) T1 3×15' @ LT-2% / T2 5×8' @ LT±0% / 회복 90초
- 대안: HR·RPE 기준도 함께 표기
```

- 마라톤 페이스(MP) 롱런/변형:
```text
마라톤 페이스 주행과 변형 세션(Alternations, Progressive, Fast Finish) 2~3안을 제안해줘.
- 근거: 목표 페이스, 최근 롱런 내성, get_training_effect(에어로빅/무산소), get_weekly_running_summary
```

- VO2max 인터벌:
```text
현재 VDOT 기준 3~5분 인터벌 세션 2안 구성해줘.
- 예: 5×1000m @ I-페이스, 4×1200m @ I-페이스 등 / 회복 2~3분 조절
```

---

## 8) 적응형 조정 프롬프트 (일일/주간)
- 일일(세션 전):
```text
오늘 세션 수행 전 컨디션 점검해줘.
- 호출: get_training_readiness, get_recovery_time
- 정책: 준비도 낮음(예: <25) → 회복/이지로 대체, 중간(25~60) → 볼륨/강도 10~20% 감산, 높음(>60) → 계획 유지
- 조정 결과를 표로 보여줘.
```

- 주간(리뷰 후 다음 주 계획):
```text
이번 주 결과를 반영해 다음 주 계획을 조정해줘.
- 입력: 이번 주 수행 요약(get_weekly_running_summary), 부하/균형(get_training_load_balance), 효과(get_training_effect)
- 정책: ATL/CTL, 거리 증감률(≤10%), 품질 세션 2~3개 한도, 롱런 점진 증가
```

---

## 9) 장치·기어 기반 프롬프트
- 장치 지원/설정:
```text
내 주요 기기의 러닝 다이내믹스 지원 여부와 설정을 확인하고, 측정 가능한 지표와 활용법을 알려줘.
- 호출: get_primary_training_device, get_devices, get_advanced_running_metrics
```

- 러닝화 교체/로테이션:
```text
러닝화 누적 거리 기반 교체 경고/로테이션 전략을 제안해줘.
- 호출: get_gear_insights(distance_threshold_km=800, include_retired=false)
- 출력: 위험/주의/정상 분류, 교체/보수 권장, 주간 로테이션 플랜
```

---

## 10) 활동 분석/리뷰 프롬프트
- 세션 리뷰(간단):
```text
방금 활동 품질을 간단히 평가해줘.
- 호출: analyze_workout_quality(activity_id=..)
- 항목: 페이스 오차, HR 존 분포 vs 의도, Pacing variation, 종합 점수
```

- 상세 분석:
```text
해당 활동의 자세한 메트릭/스플릿/HR존/날씨를 분석해 인사이트를 정리해줘.
- 호출: get_activity_details, analyze_heart_rate_zones
- 필요한 경우 리소스 URI 사용: activity://{id}/full
```

---

## 11) 자료 추출/기록 프롬프트
```text
[Activity ID]의 데이터를 [tcx|gpx|fit] 형식으로 내보내줘.
- 호출: download_activity_file(activity_id=.., format="tcx")
- FIT/Original은 바이너리이니 외부 도구로 디코딩 필요함도 안내해줘.
```

---

## 12) 예시 워크플로우
- 12주 하프 마라톤 준비(중급):
```text
1) 사전 진단 실행 → 2) 프레임워크 선택(잭 다니엘스 or 80/20) → 
3) 12주 거시계획 생성 → 4) 1주차 미시계획 생성(페이스는 calculate_vdot_zones) → 
5) 일일 적응형 조정(준비도/회복 반영) → 6) 활동 리뷰(analyze_workout_quality) → 7) 주간 조정 반복
```

- 16주 풀 마라톤 서브3:10(상급):
```text
1) 사전 진단 → 2) 프레임워크 선택(피츠징어/카노바) → 
3) 거시계획(롱런 MP 비중 점진 증가, 튠업 레이스 포함) → 4) 주간 계획(VO2·T1/T2·MP 배치) →
5) 적응형 조정 → 6) 레이스 3주 전 테이퍼링 계획 적용 → 7) 활동 리뷰 및 최종 조정
```

---

## 13) 빠른 요청 스니펫 모음
```text
- "내 VDOT과 구간 페이스를 계산해줘" → calculate_vdot_zones, calculate_training_paces
- "지난 3개월 러닝 트렌드 요약" → get_running_trends
- "이번 주 요약과 다음 주 추천" → get_weekly_running_summary + 정책 제안
- "내 훈련 부하/균형이 적절한지" → get_training_load_balance
- "오늘 훈련해도 될까?" → get_training_readiness + get_recovery_time
- "어제 활동 상세 분석해줘" → get_activity_details + analyze_heart_rate_zones
- "마라톤 페이스 롱런 2안 제시해줘" → calculate_vdot_zones 기반 세션 템플릿
- "러닝화 교체 시기 점검해줘" → get_gear_insights
- "주요 기기 러닝 다이내믹스 지원/활용법" → get_primary_training_device + get_advanced_running_metrics
```

---

## 14) 안전·가드레일
- 거리/강도 증가는 주당 10% 내 관리, 고강도는 주 2~3회 이하 권장.
- 컨디션 저하(수면/HRV/스트레스 악화, readiness 저점) 시 품질세션 축소·대체.
- 부상 이력/통증 시 전문가 상담 및 훈련 강도 즉시 조정.
- 테이퍼링은 개인 반응에 맞춰 2~3주 범위에서 볼륨 우선 축소.

---

이 템플릿을 상황에 맞게 조합/수정하면, MCP 서버의 데이터와 러닝 이론을 결합한 실전형 훈련 계획을 빠르게 만들고 운영할 수 있습니다.