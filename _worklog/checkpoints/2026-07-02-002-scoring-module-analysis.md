# Checkpoint 2026-07-02-002: Scoring Module Analysis

## 목적

`reference/스코어링 로직작성.md`를 기준으로 관련 문서와 파일을 확인하고, 리소스 자동 매칭을 위해 어떤 모듈을 만들어야 하는지, 각 모듈이 어떤 기능을 가져야 하는지 상세히 기록한다.

이번 기록은 구현 지시가 아니라 구현 전 분석 산출물이다. 구현은 아직 시작하지 않았다.

## 분석 모드

Primary Mode: Analysis / Research Mode

사용한 관점:

- 요구사항 해석: 업무지시사항이 실제로 요구하는 범위와 제외 범위를 식별
- 관련 자료 추적: 지시문이 지정한 PDF, ERD, 수정 DB 파일의 관계 확인
- 데이터 계약: 실제 사용할 테이블, 컬럼, 저장 가능한 점수 필드 확인
- 모듈 경계: 후보 생성, 필터링, 점수 계산, 랭킹, 저장의 책임 분리
- 검증 가능성: 테스트 가능한 입력/출력, 확정 필요 사항, 스키마 불일치 식별

## 확인한 관련 파일

| 파일 | 관련성 | 확인 내용 |
| --- | --- | --- |
| `reference/스코어링 로직작성.md` | 최상위 업무지시 | AI Agent 개발이 아니라 스코어링 로직 모듈 작성이 목표라고 명시한다. PDF 6장 스코어계산을 반드시 참고하라고 지시한다. ERD 누락 필드는 현실적으로 간소화한 것이므로 언어 가능 여부처럼 단순 판정 가능한 필드는 가능이면 만점, 불가능이면 최소 점수로 구현하라고 지시한다. |
| `reference/관광리소스 매칭 AI Agent.pdf` | 최초 설계 문서 | `6. 스코어계산`에 필수조건, 가이드/차량/드라이버 점수, 조합 점수, 후보 저장 규칙이 정의되어 있다. |
| `reference/블랙버드TB_DB_수정본_20260624.txt` | 최신 DB 수정 기준 | `vehicles`, `resource_availability`, `matching_candidates` 신규/수정 정의가 있다. `tour_requests`, `reservations`는 실제로 `resv_info` 참조로 바뀐 것으로 보인다. |
| `reference/erd_수정본_20260624.mdj` | ERD 수정본 | StarUML JSON 형태다. `RESV_INFO`, `GUIDES`, `VEHICLES`, `PARTNER`, `RESOURCE_AVAILABILITIES`, `RESERVATIONS`, `MATCHING_CANDIDATES`, `SYSCODE` 계열 엔티티가 있다. |

## 요구사항 해석

### 해야 하는 것

- 투어 예약 또는 요청 1건에 대해 배치 가능한 가이드, 차량, 드라이버 후보를 조회한다.
- 각 후보가 필수조건을 만족하는지 먼저 검증한다.
- 필수조건을 통과한 후보만 점수 계산 대상으로 삼는다.
- 가능한 조합을 생성한다.
- 가이드 점수, 차량 점수, 드라이버 점수, 조합 가격 점수, 조합 안정성 점수를 계산한다.
- 최종 점수 기준으로 순위를 부여한다.
- 상위 후보를 `matching_candidates`에 저장한다.
- 개발 후 설계문서를 업데이트할 수 있도록 산식과 데이터 출처를 명확히 남긴다.

### 하지 말아야 하는 것

- 이번 목표는 AI Agent 개발이 아니다.
- LLM이 투어를 해석하거나 후보를 판단하는 구조를 만들 필요는 없다.
- 관리자 confirm UI나 최종 선택 화면은 현재 모듈의 직접 범위가 아니다.
- ERD에 없는 세분화 필드를 억지로 새 가정하지 않는다. 예를 들어 언어 skill_level이 없으면 가능 여부를 기준으로 만점 또는 최소 점수를 주는 방식으로 단순화한다.

## 관련 데이터 모델 요약

### 예약/요청

수정 DB 기준으로 `tour_requests`, `reservations`보다 `resv_info`가 실제 참조 테이블이다.

`matching_candidates`의 FK는 다음과 같다.

```text
FOREIGN KEY (reserve_id, user_no) REFERENCES resv_info(reserve_id, user_no)
```

따라서 스코어링 모듈의 주 입력키는 최소한 다음이어야 한다.

- `reserve_id`
- `user_no`

PDF는 `tour_requests.group_size`, `tour_requests.luggage_count`, `requested_language`, `requested_vehicle_type`, `guide_required`, `budget_max`, `region_code`, `start_at`, `end_at` 같은 요청 필드를 전제로 한다. 하지만 수정 DB 파일에는 이 필드들이 `resv_info`에서 어떻게 표현되는지 정의되어 있지 않다. 구현 전 `resv_info` 실제 컬럼 확인이 필요하다.

### 차량

수정 DB 기준 `blackbird.vehicles`가 신규 추가 대상이다.

주요 필드:

- 식별: `id`
- 필터: `approval_status`, `operation_status`, `base_region_code`
- 적합성: `vehicle_type`, `seat_count`, `luggage_capacity`, `is_premium`, `has_child_seat`
- 가격: `price_per_day`, `price_per_hour`
- 품질/신뢰: `rating_avg`, `review_count`, `avg_response_minutes`, `cancel_count`, `no_show_count`, `complaint_count`

주의:

- PDF의 안정성 점수는 `vehicle.breakdown_count`를 사용하지만 수정 DB의 `vehicles`에는 `breakdown_count`가 없다.
- ERD 수정본에는 `vehicle_type`이 `vechcle_type`으로 오타 표기되어 있으나, 수정 DB SQL에는 `vehicle_type`이 맞다. 구현 기준은 수정 DB SQL이어야 한다.

### 가용 시간

수정 DB 기준 테이블명은 `resource_availability`이다. PDF/ERD에는 `resource_availabilities` 또는 `RESOURCE_AVAILABILITIES`로 표기되어 있으나 수정 DB SQL 기준은 단수형이다.

주요 필드:

- `resource_type`: `VEHICLE`, `DRIVER`, `GUIDE`
- `vehicle_id`
- `partner_id`
- `partner_no`
- `available_date`
- `start_time`
- `end_time`
- `status`

주의:

- ERD에는 `avaliable_date` 오타가 있으나 수정 DB SQL에는 `available_date`가 맞다.
- 차량은 `vehicle_id`로, 가이드/드라이버는 `partner_id`, `partner_no`로 가용성을 연결한다.

### 가이드/드라이버

PDF는 별도 `GUIDES`, `DRIVERS` 테이블을 전제하지만 수정 DB 파일은 `partner` 테이블을 실제 출처로 언급한다.

```sql
select * from partner where partner_type = 'DRIVER'
select * from partner where partner_type = 'PRIVATE'
select * from partner where partner_type = 'GUIDE'
```

ERD 수정본에는 `GUIDES` 엔티티가 있지만 수정 DB SQL에는 `GUIDES` 생성문이 없다. 따라서 구현 전 실제 운영 DB에서 가이드와 드라이버 속성의 출처를 확인해야 한다.

필요한 속성:

- 가이드: 지원 언어, 담당 지역, 투어 테마, 가격, 평점, 리뷰 수, 응답 속도, 취소/노쇼/클레임 수
- 드라이버: 운전 가능 차종, 운행 지역, 언어 가능 여부, 가격, 평점, 리뷰 수, 응답 속도, 취소/노쇼/클레임 수

현재 문서만으로 확정 가능한 최소 식별자는 다음이다.

- `partner.partner_id`
- `partner.user_no`
- `partner.partner_type`

### 후보 저장

수정 DB 기준 `matching_candidates`가 결과 저장 테이블이다.

저장 필드:

- 예약키: `reserve_id`, `user_no`
- 리소스: `guide_id`, `guide_no`, `vehicle_id`, `driver_id`, `driver_no`
- 점수: `guide_score`, `vehicle_score`, `driver_score`, `price_score`, `total_score`
- 가격: `guide_price`, `vehicle_price`, `driver_price`, `total_price`
- 순위/상태: `rank_no`, `candidate_status`, `is_recommended`, `is_selected`, `expires_at`, `created_at`

중요한 불일치:

- PDF의 최종 산식은 `stability_score`를 저장 컬럼으로 전제한다.
- 수정 DB의 `matching_candidates`에는 `stability_score` 컬럼이 없다.
- 따라서 구현 전 선택지가 필요하다.
  - 선택지 A: `matching_candidates.stability_score decimal(5,2)` 컬럼을 추가한다.
  - 선택지 B: 안정성 점수는 내부 계산에만 사용하고 저장하지 않는다.
  - 선택지 C: 안정성 점수를 `total_score`에 반영하지 않고 문서/산식을 수정한다.

책임 있는 결과물 관점에서는 A가 가장 추적 가능하다. B는 운영자가 후보 점수 원인을 재현하기 어렵고, C는 PDF 설계와 달라지므로 별도 합의가 필요하다.

## 만들어야 할 모듈

### 1. Request Loader 모듈

역할:

- `reserve_id`, `user_no`로 예약/요청 정보를 읽는다.
- 스코어링에 필요한 표준 입력 DTO로 변환한다.

입력:

- `reserve_id`
- `user_no`

출력 예시:

```text
ScoringRequest
- reserve_id
- user_no
- start_at
- end_at
- date
- region_code
- group_size
- luggage_count
- requested_language
- guide_required
- requested_vehicle_type
- vehicle_type_required
- budget_max
- tour_theme
- requires_driver
- requires_vehicle
```

기능:

- DB의 `resv_info` 필드를 스코어링 표준 필드로 매핑한다.
- 누락 필드를 `null`로 넘길지, 기본값을 둘지 명확히 한다.
- 날짜/시간 범위를 `available_date`, `start_time`, `end_time` 비교가 가능한 형태로 정규화한다.

구현 전 확인 필요:

- `resv_info` 실제 컬럼명
- 요청 인원, 짐 개수, 예산, 언어, 지역, 테마, 차량 타입이 어느 컬럼 또는 JSON에 저장되는지

### 2. Resource Repository 모듈

역할:

- 차량, 가이드, 드라이버 후보 원천 데이터를 조회한다.
- 스코어러가 DB 스키마에 직접 의존하지 않도록 도메인 모델로 변환한다.

필요 Repository:

- `VehicleRepository`
- `GuideRepository`
- `DriverRepository`
- `AvailabilityRepository`
- `ReservationConflictRepository`
- `MatchingCandidateRepository`

기능:

- 승인/운영 상태가 맞는 리소스 후보 조회
- 가용 시간 조회
- 기존 예약 충돌 조회
- 가격, 평점, 이력 카운트 조회
- 계산된 후보 저장

주의:

- 차량은 `vehicles` 기준으로 구현 가능하다.
- 가이드/드라이버는 `partner`만으로 점수 계산에 필요한 속성이 부족하다. 실제 프로필/메타 테이블 확인이 필요하다.
- `PRIVATE` 파트너를 드라이버/차량 공급업체로 볼지, 드라이버 후보에 포함할지 정책 결정이 필요하다.

### 3. Eligibility Filter 모듈

역할:

- 점수 계산 전에 필수조건을 검증하고 불합격 후보를 제외한다.

필수 필터:

| 필터 | 대상 | 기준 | 불합격 처리 |
| --- | --- | --- | --- |
| 운영 상태 | 공통 | 차량은 `approval_status=APPROVED` 및 `operation_status=ACTIVE`, 파트너/가용성은 `status=ACTIVE` 계열 | 후보 제외 |
| 가용 시간 | 공통 | `resource_availability`가 요청 시작~종료 시간을 전체 포함 | 후보 제외 |
| 예약 충돌 | 공통 | 동일 리소스의 확정/진행 예약과 시간이 겹치지 않음 | 후보 제외 |
| 필수 언어 | 가이드 | `guide_required=true`이고 요청 언어가 있으면 해당 언어 지원 필요 | 후보 제외 |
| 좌석 수 | 차량 | `seat_count >= group_size` | 후보 제외 |
| 짐 적재 | 차량 | `luggage_capacity >= luggage_count` | 후보 제외 |
| 필수 차종 | 차량 | 필수 차종 지정 시 일치 또는 허용 대체 차종 | 후보 제외 |
| 차종 운전 가능 | 드라이버 | 배정 차량의 `vehicle_type`이 드라이버 운전 가능 차종에 포함 | 후보 제외 |

설계 원칙:

- 필터는 점수 0점 처리와 구분해야 한다.
- 필수조건 실패는 후보 제외다.
- 선호조건 미충족은 후보 유지 후 점수 감점 또는 0점이다.
- 제외 사유는 테스트와 운영 분석을 위해 내부 로그 또는 디버그 결과에 남길 수 있어야 한다.

### 4. Guide Scorer 모듈

역할:

- 가이드 1명에 대해 0~100점의 `guide_score`를 계산한다.

PDF 기준 배점:

| 항목 | 배점 |
| --- | ---: |
| 언어 적합도 | 25 |
| 지역 숙련도 | 20 |
| 투어 테마 적합도 | 15 |
| 평점/후기 | 15 |
| 최근 배정 균형 | 10 |
| 가격 적합도 | 10 |
| 응답속도/신뢰도 | 5 |

현재 업무지시 반영:

- 언어 skill_level이 실제 데이터에 없다면 언어 가능 여부만 사용한다.
- 해당 언어 가능이면 언어 적합도 25점.
- 해당 언어 불가능이고 필수 언어이면 후보 제외.
- 해당 언어 불가능이고 선호 언어이면 0점.

지역/테마 skill_level이 없을 경우의 보수적 대체안:

- 지역 지원 여부만 있으면 지원 20점, 미지원 0점 또는 필수 지역이면 후보 제외.
- 테마 지원 여부만 있으면 지원 15점, 미지원 0점.
- 지역/테마 데이터가 전혀 없으면 해당 항목은 0점 처리하거나, 운영 합의 하에 중립점으로 둘 수 있다.
- 추천 품질을 책임 있게 운영하려면 중립점보다 0점이 더 보수적이다. 단, 데이터 미비로 전체 후보 점수가 과도하게 낮아질 수 있다.

산식:

```text
guide_score =
  language_score
  + region_score
  + theme_score
  + rating_review_score
  + recent_assignment_balance_score
  + guide_price_score
  + guide_reliability_score
```

평점/후기:

```text
rating_score = (rating_avg / 5) * 10
review_score = min(review_count / 30, 1) * 5
rating_review_score = rating_score + review_score
```

신뢰도:

```text
guide_reliability_score = clamp(
  5 - cancel_count * 1 - no_show_count * 2 - complaint_count * 0.5,
  0,
  5
)
```

최근 배정 균형:

| 최근 7일 확정/완료 예약 수 | 점수 |
| ---: | ---: |
| 0 | 10 |
| 1 | 8 |
| 2 | 6 |
| 3 | 4 |
| 4 이상 | 2 |

### 5. Vehicle Scorer 모듈

역할:

- 차량 1대에 대해 0~100점의 `vehicle_score`를 계산한다.

PDF 기준 배점:

| 항목 | 배점 |
| --- | ---: |
| 차종 적합도 | 20 |
| 좌석 여유 | 25 |
| 짐 적재 가능성 | 20 |
| 지역 적합도 | 10 |
| 차량 품질/평점 | 15 |
| 가격 적합도 | 10 |

세부 기준:

| 항목 | 조건 | 점수 |
| --- | --- | ---: |
| 차종 적합도 | 요청 차종과 정확히 일치 | 20 |
| 차종 적합도 | 상위 차종 또는 운영상 허용 가능한 대체 차종 | 15 |
| 차종 적합도 | 차종 미일치이나 운행 가능 | 5 |
| 좌석 여유 | 요청 인원 대비 3석 이상 여유 | 25 |
| 좌석 여유 | 2석 여유 | 20 |
| 좌석 여유 | 1석 여유 | 15 |
| 좌석 여유 | 정확히 일치 | 10 |
| 짐 적재 | 요청 짐 개수 대비 3개 이상 여유 | 20 |
| 짐 적재 | 2개 여유 | 16 |
| 짐 적재 | 1개 여유 | 12 |
| 짐 적재 | 정확히 일치 | 8 |
| 지역 적합도 | 기본 운행 지역과 요청 지역 일치 | 10 |
| 지역 적합도 | 동일 권역 운행 가능 | 7 |
| 지역 적합도 | 지역 불일치이나 배차 가능 | 3 |

차량 품질/평점 15점은 PDF에 세부 산식이 없다. 구현안:

```text
vehicle_quality_score =
  rating_component up to 8
  + review_component up to 4
  + premium_component up to 2
  + model_year_component up to 1
```

단, 이 세부 배분은 설계문서에 없는 보완안이므로 사용자 확인이 필요하다.

차량 가격 적합도:

- 가이드 가격 적합도와 동일한 10점 구간을 사용한다.
- 기준값은 요청 예산의 차량 몫 또는 차량 기준가가 필요하다.
- 기준값이 없으면 중립점 정책이 필요하다.

### 6. Driver Scorer 모듈

역할:

- 드라이버 1명에 대해 0~100점의 `driver_score`를 계산한다.

PDF 기준 배점:

| 항목 | 배점 |
| --- | ---: |
| 차량 운전 가능 적합도 | 20 |
| 지역 운행 숙련도 | 25 |
| 언어 가능성 | 10 |
| 평점/후기 | 15 |
| 신뢰도 | 15 |
| 가격 적합도 | 15 |

세부 기준:

| 항목 | 조건 | 점수 |
| --- | --- | ---: |
| 차량 운전 가능 | 배정 차량 타입 운전 가능 | 20 |
| 차량 운전 가능 | 운전 가능 차량 타입 미포함 | 후보 제외 |
| 지역 운행 숙련도 | skill_level 5 | 25 |
| 지역 운행 숙련도 | skill_level 4 | 20 |
| 지역 운행 숙련도 | skill_level 3 | 15 |
| 지역 운행 숙련도 | skill_level 2 | 10 |
| 지역 운행 숙련도 | skill_level 1 | 5 |
| 언어 가능성 | 가이드 없음 또는 드라이버 고객 응대 필요 + 요청 언어 가능 | 10 |
| 언어 가능성 | 가이드 동행 + 드라이버 언어 불필요 | 6 |
| 언어 가능성 | 요청 언어 미지원 | 0 |

현재 데이터 리스크:

- 수정 DB 파일에는 별도 `drivers` 테이블 정의가 없다.
- 드라이버의 운전 가능 차종, 지역 숙련도, 언어, 가격, 평점/후기, 신뢰도 필드 출처가 불명확하다.
- `partner`에 일부 속성이 있거나 별도 프로필 테이블이 있을 가능성이 높다. 실제 DB 확인 전에는 구현을 확정할 수 없다.

### 7. Combination Builder 모듈

역할:

- 필수조건을 통과한 리소스 후보를 조합한다.

기본 조합:

```text
eligible_guides x eligible_vehicles x eligible_drivers
```

예외:

- `guide_required=false`이면 가이드 없는 조합을 허용한다.
- 차량이 필요 없는 요청이면 차량 점수를 제외한다.
- 드라이버가 필요 없는 요청이면 드라이버 점수를 제외한다.

주의:

- 단순 Cartesian Product는 후보 수가 급증할 수 있다.
- 운영 초기에는 전체 조합 생성이 가능하더라도, 리소스가 늘어나면 사전 필터와 상위 N개 컷이 필요할 수 있다.
- 하지만 현재 요구사항은 "가능한 후보들의 Cartesian Product"를 명시하므로, 초기 구현은 필수조건 통과 후보 전체 조합을 기준으로 한다.

### 8. Price Scorer 모듈

역할:

- 조합 전체 가격에 대한 `price_score`를 0~100점으로 계산한다.

PDF 기준:

| 조건 | 점수 |
| --- | ---: |
| `total_price <= budget_max * 0.80` | 100 |
| `total_price <= budget_max` | 80 |
| `total_price <= budget_max * 1.10` | 50 |
| `total_price <= budget_max * 1.20` | 30 |
| `total_price > budget_max * 1.20` | 0 |
| `budget_max` 미입력 | 70 |

가격 구성:

```text
total_price = guide_price + vehicle_price + driver_price
```

가이드가 없으면 `guide_price=0`, 차량이 없으면 `vehicle_price=0`, 드라이버가 없으면 `driver_price=0`으로 계산한다.

### 9. Stability Scorer 모듈

역할:

- 조합 전체 안정성 점수 `stability_score`를 0~100점으로 계산한다.

PDF 기준:

```text
base = 80
+5 if guide.cancel_count == 0
+5 if driver.cancel_count == 0
+5 if vehicle.breakdown_count == 0
-10 if guide.complaint_count > 3
-10 if driver.complaint_count > 3
-10 if vehicle.breakdown_count > 2
clamp 0..100
```

스키마 문제:

- 수정 DB `vehicles`에는 `breakdown_count`가 없다.
- 수정 DB `matching_candidates`에는 `stability_score`가 없다.

구현 보완안:

- `breakdown_count`가 없으면 차량 안정성 보너스/패널티는 계산하지 않거나 0건으로 간주한다.
- 0건으로 간주하면 차량 안정성이 과대평가될 수 있다.
- 계산하지 않으면 PDF의 안정성 점수와 달라진다.
- 운영 신뢰성을 위해서는 `vehicles.breakdown_count` 또는 차량 장애 이력 테이블 출처를 확인해야 한다.

### 10. Total Score Calculator 모듈

역할:

- 리소스별 점수와 조합 점수를 가중합해 `total_score`를 계산한다.

기본 산식:

```text
total_score =
  guide_score * 0.40
  + vehicle_score * 0.20
  + driver_score * 0.20
  + price_score * 0.10
  + stability_score * 0.10
```

리소스가 필요 없는 경우:

- 해당 점수 항목을 제외한다.
- 남은 항목의 가중치를 100%로 재분배한다.

예: `guide_required=false`

```text
원래 남는 가중치 = vehicle 0.20 + driver 0.20 + price 0.10 + stability 0.10 = 0.60
재분배:
vehicle = 0.20 / 0.60 = 0.3333
driver = 0.20 / 0.60 = 0.3333
price = 0.10 / 0.60 = 0.1667
stability = 0.10 / 0.60 = 0.1667
```

주의:

- 가이드가 선택 사항이지만 후보에 가이드가 포함된 조합과 미포함 조합을 동시에 비교할지 정책이 필요하다.
- `guide_required=false`를 "가이드는 절대 불필요"로 볼지, "가이드 없어도 가능"으로 볼지에 따라 조합 생성 방식이 달라진다.

### 11. Ranking 모듈

역할:

- 계산된 후보 조합을 `total_score` 내림차순으로 정렬한다.
- 동일 점수일 때 결정적 순서를 보장한다.
- `rank_no`를 부여한다.
- 상위 3개 후보에 `is_recommended=true`를 부여한다.

동점 처리 제안:

1. `total_score` 높은 순
2. `price_score` 높은 순
3. `total_price` 낮은 순
4. `stability_score` 높은 순
5. `guide_score`, `vehicle_score`, `driver_score` 순
6. 리소스 ID 오름차순

동점 처리 규칙은 운영 결과에 직접 영향을 주므로 설계문서에 반드시 남겨야 한다.

### 12. Persistence 모듈

역할:

- 계산된 후보를 `matching_candidates`에 저장한다.

저장 정책:

- 기존 후보를 삭제 후 재생성할지, 새 버전으로 추가할지 결정해야 한다.
- 같은 `reserve_id`, `user_no`에 대해 중복 실행될 수 있으므로 idempotency 정책이 필요하다.

권장 초기 정책:

- 같은 예약의 기존 `OFFERED` 또는 추천 전 상태 후보를 만료/삭제하고 재생성한다.
- 이미 `SELECTED`인 후보가 있으면 자동 재계산을 막거나 별도 강제 옵션이 필요하다.

저장값:

- `candidate_status`: 초기값 `OFFERED` 또는 `CANDIDATE`
- `is_recommended`: 상위 3개 true
- `is_selected`: 초기값 false
- `expires_at`: 운영 정책에 따라 생성 후 N시간 또는 N일
- `created_at`: 현재 시각

주의:

- 수정 DB 예시는 `candidate_status`에 `SELECTED`, `OFFERED`, `CANCELLED`가 섞여 있다.
- 정확한 상태 enum은 운영 코드 또는 DB 코드값 확인이 필요하다.

### 13. Rule Configuration 모듈

역할:

- 점수 배점과 구간을 코드에 하드코딩하지 않고 한곳에서 관리한다.

초기에는 별도 관리자 UI 없이 코드/설정 파일로 충분하다.

관리할 값:

- 가이드 항목별 배점
- 차량 항목별 배점
- 드라이버 항목별 배점
- 최종 조합 가중치
- 가격 구간
- 최근 배정 균형 구간
- 추천 후보 개수
- 후보 만료 시간

주의:

- DB 기반 가중치 관리 테이블은 현재 요구사항에 없다.
- 먼저 코드 설정 또는 YAML/JSON 설정으로 시작하고, 운영 조정 요구가 생기면 DB화하는 편이 단순하다.

### 14. Debug/Explanation 모듈

역할:

- 후보별 점수 산출 근거를 내부적으로 설명 가능한 형태로 만든다.

필요 이유:

- `matching_candidates`에는 최종 점수 필드만 있고 세부 항목 점수 저장 컬럼이 없다.
- 운영자가 왜 특정 후보가 1위인지 확인하려면 설명 데이터가 필요하다.

초기 구현안:

- API 응답 또는 로그에만 `score_breakdown`을 포함한다.
- DB 저장은 하지 않는다.

향후 개선안:

- `matching_candidate_score_details` 같은 별도 상세 테이블을 추가한다.

## 권장 패키지/파일 구조

언어와 프레임워크가 아직 확정되지 않았으므로 개념 구조로 기록한다.

```text
matching_scoring/
  models/
    request
    resource
    candidate
    score_breakdown
  repositories/
    request_repository
    vehicle_repository
    partner_repository
    availability_repository
    reservation_repository
    candidate_repository
  eligibility/
    common_filters
    guide_filters
    vehicle_filters
    driver_filters
  scoring/
    guide_scorer
    vehicle_scorer
    driver_scorer
    price_scorer
    stability_scorer
    total_score_calculator
  matching/
    combination_builder
    ranker
    matching_service
  config/
    scoring_rules
  tests/
    test_eligibility
    test_guide_scorer
    test_vehicle_scorer
    test_driver_scorer
    test_total_score
    test_matching_service
```

핵심 진입점은 `MatchingService.generate_candidates(reserve_id, user_no)` 형태가 적절하다.

## 처리 흐름

```text
1. Request Loader가 reserve_id, user_no로 ScoringRequest를 구성한다.
2. Repository가 운영 가능한 차량, 가이드, 드라이버 후보를 조회한다.
3. Eligibility Filter가 가용 시간, 예약 충돌, 필수조건을 검증한다.
4. Combination Builder가 가능한 guide x vehicle x driver 조합을 만든다.
5. Guide/Vehicle/Driver Scorer가 개별 점수를 계산한다.
6. Price Scorer가 total_price와 price_score를 계산한다.
7. Stability Scorer가 stability_score를 계산한다.
8. Total Score Calculator가 가중치 재분배를 반영해 total_score를 계산한다.
9. Ranking 모듈이 rank_no와 is_recommended를 부여한다.
10. Persistence 모듈이 matching_candidates에 저장한다.
11. 결과와 score_breakdown을 반환하거나 로그로 남긴다.
```

## 구현 전 확정 필요 사항

다음은 구현을 시작하기 전에 반드시 확인해야 한다. 확인 없이 진행하면 잘못된 DB 매핑이나 재현 불가능한 점수 산식이 될 위험이 크다.

1. 실제 개발 언어와 실행 형태
   - Python 모듈인지, Node/Java/Spring 서비스인지, 기존 서버에 붙는 배치/서비스인지 확인 필요.

2. `resv_info` 실제 컬럼
   - `start_at`, `end_at`, `group_size`, `luggage_count`, `requested_language`, `requested_vehicle_type`, `budget_max`, `region_code`, `tour_theme`, `guide_required` 매핑이 필요.

3. 가이드 속성 출처
   - 언어 가능 여부, 지역, 테마, 가격, 평점, 리뷰, 응답, 취소/노쇼/클레임 데이터가 어느 테이블에 있는지 필요.

4. 드라이버 속성 출처
   - 운전 가능 차종, 운행 지역, 언어 가능 여부, 가격, 평점, 리뷰, 응답, 취소/노쇼/클레임 데이터가 어느 테이블에 있는지 필요.

5. `stability_score` 저장 여부
   - PDF는 저장 컬럼을 전제하지만 수정 DB에는 없다.

6. 차량 장애 이력 출처
   - PDF는 `vehicle.breakdown_count`를 사용하지만 수정 DB에는 없다.

7. 차종 상위 호환 규칙
   - `requested_vehicle_type`과 `vehicle_type`이 불일치할 때 어떤 차종을 상위/대체 가능으로 볼지 코드표가 필요.

8. 동일 권역 지역 규칙
   - `base_region_code`와 요청 `region_code`가 정확히 같지 않을 때 동일 권역 판단 기준이 필요.

9. 후보 재생성 정책
   - 같은 예약에 기존 후보가 있을 때 삭제, 만료, 버전 추가 중 어떤 정책을 사용할지 필요.

10. 상태값 enum
    - `candidate_status`, 예약 확정/진행 상태, 가용성 상태의 정확한 코드값이 필요.

## 테스트 전략

### 단위 테스트

- 언어 가능 여부가 true이면 가이드 언어 점수 25점인지 확인
- 언어 필수인데 미지원이면 후보 제외되는지 확인
- 좌석 수가 부족하면 차량 후보 제외되는지 확인
- 짐 적재량이 부족하면 차량 후보 제외되는지 확인
- 가격 구간별 `price_score`가 100/80/50/30/0/70으로 나오는지 확인
- `rating_avg`, `review_count` 보정 산식 확인
- 취소/노쇼/클레임 감점이 0점 미만으로 내려가지 않는지 확인
- 리소스가 빠진 경우 가중치 재분배가 맞는지 확인

### 통합 테스트

- 샘플 예약 1건에 대해 후보 생성부터 `matching_candidates` 저장까지 검증
- 가이드 없는 요청에서 `guide_score=0` 또는 null 처리 정책 확인
- 상위 3개 후보에만 `is_recommended=true`가 들어가는지 확인
- 동일 예약 재실행 시 중복 후보가 생기지 않는지 확인

### 회귀 테스트

- PDF의 예시 산식과 동일한 입력을 넣었을 때 예상 점수가 재현되는지 확인
- DB 컬럼명이 바뀌었을 때 Repository 테스트에서 실패하도록 구성

## 현재 결론

이 저장소에서 만들어야 할 핵심은 "AI Agent"가 아니라 deterministic scoring engine이다. 가장 책임 있는 구조는 `Request Loader -> Repository -> Eligibility Filter -> Resource Scorers -> Combination Scorers -> Ranker -> Persistence`로 나누는 것이다.

단, 현재 문서만으로 바로 구현하면 위험한 지점이 있다. 특히 `resv_info` 실제 컬럼, 가이드/드라이버 상세 속성 출처, `stability_score` 컬럼 부재, `vehicle.breakdown_count` 부재는 구현 전 확정해야 한다.

따라서 다음 단계는 코딩이 아니라 설계문서 작성과 데이터 계약 확정이다. 그 뒤 최소 구현으로 차량/가용성/후보 저장부터 시작하고, 가이드/드라이버 상세 점수는 실제 데이터 출처가 확인된 뒤 붙이는 것이 맞다.

## 검증 결과

- `reference/스코어링 로직작성.md`를 읽었다.
- `reference/관광리소스 매칭 AI Agent.pdf`에서 `6. 스코어계산` 텍스트를 추출해 확인했다.
- `reference/블랙버드TB_DB_수정본_20260624.txt`에서 수정 DB 정의를 확인했다.
- `reference/erd_수정본_20260624.mdj`를 구조적으로 파싱해 ERD 엔티티/컬럼 목록을 확인했다.
- 구현은 수행하지 않았다.

## 다음 에이전트가 먼저 볼 것

1. `AGENT.md`
2. `_worklog/INDEX.md`
3. `_worklog/HANDOFF.md`
4. 이 파일
5. `reference/스코어링 로직작성.md`
6. `reference/블랙버드TB_DB_수정본_20260624.txt`
7. `reference/관광리소스 매칭 AI Agent.pdf`

