# Checkpoint 2026-07-02-003: DB Table Verification

## 목적

사용자가 실행한 `information_schema.columns` 조회 결과를 기준으로, 스코어링 모듈에서 사용할 후보 테이블이 실제 DB에 존재하는지 확인하고, 어떤 테이블의 어떤 값을 사용할지 갱신한다.

## 입력 자료

- 사용자 첨부 파일: `pasted-text.txt`
- 내용: `table_name`, `ordinal_position`, `column_name`, `column_type`, `is_nullable`, `column_key`, `column_default`, `column_comment` 컬럼을 가진 실제 DB 컬럼 조회 결과

## 확인된 테이블 존재 여부

| 테이블 | 존재 여부 | 판단 |
| --- | --- | --- |
| `resv_info` | 존재 | 기존 서비스 예약/배차 요청의 실제 원천 후보 |
| `tour_requests` | 존재 | PDF 설계에 가까운 스코어링 요청 원천 후보 |
| `guides` | 존재 | 가이드 스코어링에 필요한 컬럼 다수 보유 |
| `drivers` | 존재 | 드라이버 스코어링에 필요한 컬럼 다수 보유 |
| `vehicles` | 존재 | 차량 스코어링에 필요한 컬럼 보유 |
| `resource_availability` | 존재 | 리소스 가용 시간 필터에 사용 |
| `matching_candidates` | 존재 | 스코어링 결과 저장 테이블 |
| `reservations` | 존재 | 확정/진행 예약 충돌 확인 후보 |
| `partner` | 존재 | 기존 파트너 원장. 가이드/드라이버 원장 또는 보조 데이터로 사용 가능 |
| `syscode` | 존재 | 언어, 차종, 예약/투어 타입 코드 확인 |
| `platform_region` | 존재 | 지역 코드 및 동일 권역 판단 후보 |

## 중요한 정정 사항

이전 분석에서 `guides`, `drivers`, `tour_requests`, `reservations`의 실제 존재 여부를 확인 필요로 두었다. 첨부된 실제 DB 컬럼 조회 결과 기준으로 이 테이블들은 존재한다.

따라서 가이드/드라이버 점수 계산은 `partner`만으로 억지 매핑할 필요가 없다. 기본 스코어링 속성은 `guides`, `drivers`를 우선 사용하고, `partner`는 실제 서비스 사용자/파트너 계정과 연결이 필요할 때 보조 테이블로 보는 편이 타당하다.

단, 여전히 연결키 문제가 남아 있다.

- `guides.id`는 `bigint`
- `drivers.id`는 `bigint`
- `matching_candidates.guide_id`, `matching_candidates.driver_id`는 `varchar(50)`
- `matching_candidates.guide_no`, `matching_candidates.driver_no`는 `int`
- `partner.partner_id`는 `varchar(50)`
- `partner.user_no`는 `int`

즉, `guides/drivers`와 `partner/matching_candidates` 사이의 식별자 매핑 정책을 확정해야 한다.

## 요청/예약 원천 테이블 판단

### `tour_requests`

스코어링에 필요한 요청 필드가 가장 잘 정리되어 있다.

| 목적 | 컬럼 |
| --- | --- |
| 요청 ID | `id` |
| 고객 ID | `customer_id` |
| 상태 | `status` |
| 투어일 | `tour_date` |
| 시작/종료 | `start_at`, `end_at` |
| 지역 | `region_code` |
| 인원 | `group_size` |
| 짐 | `luggage_count` |
| 가이드 필요 | `guide_required` |
| 요청 언어 | `requested_language` |
| 차량 필요 | `vehicle_required` |
| 요청 차종 | `requested_vehicle_type` |
| 드라이버 필요 | `driver_required` |
| 요청 테마 | `requested_theme` |
| 최대 예산 | `budget_max` |
| 승하차지 | `pickup_location`, `dropoff_location` |
| 원문/구조화 요청 | `raw_requested_text`, `structured_json` |

평가:

- PDF 설계의 스코어링 입력과 가장 잘 맞는다.
- `reservations.requested_id`가 `tour_requests.id`를 참조하는 구조로 보인다.
- 단점은 `matching_candidates`가 `tour_requests.id`가 아니라 `resv_info.reserve_id`, `resv_info.user_no`를 저장한다는 점이다.

### `resv_info`

기존 서비스 예약 데이터가 풍부하다.

스코어링에 직접 매핑 가능한 필드:

| 목적 | 컬럼 |
| --- | --- |
| 예약 ID | `reserve_id` |
| 사용자 번호 | `user_no` |
| 지역 | `region_code` |
| 예약일 | `reserve_dt` |
| 예약 만료 | `reserve_end_dt` |
| 인원 | `boarding_headcount` |
| 짐 | `baggage` |
| 요청 차종 | `car_type_sel`, `car_type` |
| 요금 타입 | `fare_type` |
| 결제 예정 금액 | `payment_amount` |
| 요청사항 | `requirements` |
| 예약 상태 | `reserve_status` |
| 취소 상태 | `reserve_status_cancel`, `cancel_yn` |
| 노쇼 여부 | `noshow_yn` |
| 차량 가격 | `car_price` |
| 상품 가격 | `product_price` |

평가:

- `matching_candidates`의 FK 구조와 맞는다.
- 그러나 PDF의 스코어링 요청 필드와 1:1로 대응하지 않는다.
- 특히 `start_at`, `end_at`, `guide_required`, `requested_language`, `requested_theme`, `budget_max`가 직접 컬럼으로 없다.

### 결론

스코어링 입력 원천은 두 가지 방식 중 하나를 선택해야 한다.

1. `tour_requests`를 입력 원천으로 사용하고, 결과 저장 시 `resv_info.reserve_id/user_no`와 연결하는 매핑을 추가한다.
2. `resv_info`를 입력 원천으로 사용하고, 부족한 스코어링 필드를 `requirements`, `fare_type`, 별도 테이블 또는 기본 정책으로 보완한다.

현재 DB 구조만 보면 `tour_requests`는 스코어링 엔진용 요청 테이블에 가깝고, `resv_info`는 기존 예약 운영 테이블에 가깝다. 책임 있는 구현을 위해서는 두 테이블의 업무 흐름상 연결 관계를 먼저 확인해야 한다.

## 리소스별 데이터 매핑

### 가이드: `guides`

| 점수/필터 목적 | 사용할 컬럼 |
| --- | --- |
| 식별자 | `id` |
| 운영 상태 | `status` |
| 기본 지역 | `base_region_code` |
| 언어 | `languages` |
| 테마 | `themes` |
| 지역 숙련도 | `region_level` |
| 가격 | `price_per_day`, `price_per_hour` |
| 평점/후기 | `rating_avg`, `review_count` |
| 응답 | `response_rate`, `avg_response_minutes` |
| 신뢰도 | `cancel_count`, `no_show_count`, `complaint_count` |

업무지시 반영:

- `languages`가 언어 코드만 담고 언어 레벨이 없으면, 요청 언어 포함 시 언어 점수 만점으로 처리한다.
- 언어 레벨 데이터가 문자열에 같이 들어 있다면 파싱 정책이 필요하다.

### 드라이버: `drivers`

| 점수/필터 목적 | 사용할 컬럼 |
| --- | --- |
| 식별자 | `id` |
| 승인/운영 상태 | `approval_status`, `operation_status` |
| 기본 지역 | `base_region_code` |
| 운전 가능 차종 | `vehicle_types` |
| 언어 | `languages` |
| 지역 | `regions` |
| 가격 | `price_per_day`, `price_per_hour` |
| 평점/후기 | `rating_avg`, `review_count` |
| 응답 | `response_rate`, `avg_response_minutes` |
| 신뢰도 | `cancel_count`, `no_show_count`, `complaint_count` |

주의:

- PDF는 지역 운행 숙련도를 skill_level로 계산하지만 `drivers.regions`에는 숙련도 컬럼이 분리되어 있지 않다.
- `regions` 값 형식 확인이 필요하다. 단순 지역 코드 목록이면 가능 여부 기반 점수로 단순화해야 한다.

### 차량: `vehicles`

| 점수/필터 목적 | 사용할 컬럼 |
| --- | --- |
| 식별자 | `id` |
| 차종 | `vehicle_type` |
| 승인/운영 상태 | `approval_status`, `operation_status` |
| 기본 지역 | `base_region_code` |
| 좌석 | `seat_count` |
| 짐 적재 | `luggage_capacity` |
| 품질 | `model_name`, `model_year`, `is_premium`, `has_child_seat` |
| 가격 | `price_per_day`, `price_per_hour` |
| 평점/후기 | `rating_avg`, `review_count` |
| 응답/신뢰 | `avg_response_minutes`, `cancel_count`, `no_show_count`, `complaint_count` |

주의:

- PDF의 `breakdown_count`는 여전히 없다.
- 안정성 점수에서 차량 고장 이력은 제외하거나 별도 출처 확인이 필요하다.

### 가용성: `resource_availability`

| 목적 | 컬럼 |
| --- | --- |
| 리소스 타입 | `resource_type` |
| 차량 연결 | `vehicle_id` |
| 가이드/드라이버 연결 | `partner_id`, `partner_no` |
| 가용 날짜 | `available_date` |
| 가용 시간 | `start_time`, `end_time` |
| 상태 | `status` |

주의:

- `resource_availability`는 차량은 `vehicle_id`로 연결한다.
- 가이드/드라이버는 `partner_id/partner_no`로 연결하도록 설계되어 있다.
- 그런데 `guides/drivers`는 `id` 기반이다. 이 연결을 바로 할 수 있는지 확인해야 한다.

### 결과 저장: `matching_candidates`

| 목적 | 컬럼 |
| --- | --- |
| 예약 연결 | `reserve_id`, `user_no` |
| 리소스 | `guide_id`, `guide_no`, `vehicle_id`, `driver_id`, `driver_no` |
| 점수 | `guide_score`, `vehicle_score`, `driver_score`, `price_score`, `total_score` |
| 가격 | `guide_price`, `vehicle_price`, `driver_price`, `total_price` |
| 순위/상태 | `rank_no`, `candidate_status`, `is_recommended`, `is_selected`, `expires_at`, `created_at` |

주의:

- `stability_score` 컬럼은 없다.
- PDF 설계와 동일하게 운영하려면 컬럼 추가가 필요하다.

## 새로 해소된 불확실성

| 이전 불확실성 | 현재 판단 |
| --- | --- |
| `guides` 테이블 존재 여부 | 존재함 |
| `drivers` 테이블 존재 여부 | 존재함 |
| `tour_requests` 테이블 존재 여부 | 존재함 |
| `reservations` 테이블 존재 여부 | 존재함 |
| 가이드 기본 점수 데이터 출처 | `guides` 우선 |
| 드라이버 기본 점수 데이터 출처 | `drivers` 우선 |
| 차량 점수 데이터 출처 | `vehicles` |

## 아직 남은 핵심 확인 사항

1. `tour_requests`와 `resv_info`의 연결 관계
   - `tour_requests.id`가 어떤 방식으로 `resv_info.reserve_id/user_no`와 연결되는지 확인 필요.

2. `guides/drivers`와 `partner`의 연결 관계
   - `guides.id`, `drivers.id`가 `partner.partner_id` 또는 `partner.user_no`와 어떻게 매핑되는지 확인 필요.

3. `resource_availability`의 가이드/드라이버 연결 방식
   - `partner_id/partner_no`가 `guides/drivers`에 직접 연결되는지, 아니면 `partner`를 거쳐야 하는지 확인 필요.

4. `matching_candidates`의 `guide_id/driver_id` 저장 정책
   - `guides.id/drivers.id`를 문자열로 저장할지, `partner.partner_id`를 저장할지 결정 필요.

5. `stability_score` 저장 여부
   - 현재 컬럼 없음.

6. 차량 고장 이력 출처
   - `vehicles.breakdown_count` 없음.

## 다음 확인 쿼리

### 1. 테이블별 데이터 건수 확인

```sql
SELECT 'resv_info' AS table_name, COUNT(*) AS row_count FROM resv_info
UNION ALL SELECT 'tour_requests', COUNT(*) FROM tour_requests
UNION ALL SELECT 'guides', COUNT(*) FROM guides
UNION ALL SELECT 'drivers', COUNT(*) FROM drivers
UNION ALL SELECT 'vehicles', COUNT(*) FROM vehicles
UNION ALL SELECT 'resource_availability', COUNT(*) FROM resource_availability
UNION ALL SELECT 'matching_candidates', COUNT(*) FROM matching_candidates
UNION ALL SELECT 'reservations', COUNT(*) FROM reservations
UNION ALL SELECT 'partner', COUNT(*) FROM partner;
```

### 2. 가이드/드라이버와 partner 연결 가능성 확인

```sql
SELECT
    partner_type,
    COUNT(*) AS cnt
FROM partner
WHERE delete_dt IS NULL
GROUP BY partner_type
ORDER BY partner_type;
```

```sql
SELECT
    g.id AS guide_id,
    g.name AS guide_name,
    p.partner_id,
    p.user_no,
    p.partner_name,
    p.partner_type
FROM guides g
LEFT JOIN partner p
    ON p.partner_type = 'GUIDE'
   AND (
        p.partner_id = CAST(g.id AS CHAR)
        OR p.user_no = g.id
        OR p.partner_name = g.name
   )
LIMIT 20;
```

```sql
SELECT
    d.id AS driver_id,
    d.name AS driver_name,
    p.partner_id,
    p.user_no,
    p.partner_name,
    p.partner_type
FROM drivers d
LEFT JOIN partner p
    ON p.partner_type = 'DRIVER'
   AND (
        p.partner_id = CAST(d.id AS CHAR)
        OR p.user_no = d.id
        OR p.partner_name = d.name
   )
LIMIT 20;
```

### 3. resource_availability 연결 확인

```sql
SELECT
    ra.resource_type,
    COUNT(*) AS cnt,
    SUM(CASE WHEN ra.vehicle_id IS NOT NULL THEN 1 ELSE 0 END) AS with_vehicle_id,
    SUM(CASE WHEN ra.partner_id IS NOT NULL THEN 1 ELSE 0 END) AS with_partner_id,
    SUM(CASE WHEN ra.partner_no IS NOT NULL THEN 1 ELSE 0 END) AS with_partner_no
FROM resource_availability ra
GROUP BY ra.resource_type
ORDER BY ra.resource_type;
```

### 4. tour_requests와 reservations 연결 확인

```sql
SELECT
    tr.id AS tour_request_id,
    tr.customer_id,
    tr.start_at,
    tr.end_at,
    r.id AS reservation_id,
    r.requested_id,
    r.status
FROM tour_requests tr
LEFT JOIN reservations r
    ON r.requested_id = tr.id
LIMIT 20;
```

### 5. resv_info와 matching_candidates 연결 확인

```sql
SELECT
    ri.reserve_id,
    ri.user_no,
    ri.reserve_status,
    ri.reserve_dt,
    mc.id AS matching_candidate_id,
    mc.guide_id,
    mc.vehicle_id,
    mc.driver_id,
    mc.total_score,
    mc.candidate_status
FROM resv_info ri
LEFT JOIN matching_candidates mc
    ON mc.reserve_id = ri.reserve_id
   AND mc.user_no = ri.user_no
LIMIT 20;
```

## 현재 결론

스코어링에 필요한 핵심 테이블은 실제 DB에 존재한다. 이전보다 구현 가능성이 높아졌다.

하지만 바로 구현하면 안 되는 이유도 명확해졌다. 데이터는 존재하지만 `tour_requests`, `resv_info`, `guides/drivers`, `partner`, `resource_availability`, `matching_candidates` 사이의 연결키 정책이 아직 확정되지 않았다.

다음 단계는 점수 산식 구현이 아니라 연결 관계 확인이다. 연결 관계가 확정되면 DB 기반 스코어링 모듈의 Repository 설계를 바로 구체화할 수 있다.

