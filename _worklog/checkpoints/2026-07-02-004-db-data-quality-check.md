# Checkpoint 2026-07-02-004: DB Data Quality Check

## 목적

테이블/컬럼 존재 확인 이후, 실제 데이터가 스코어링 구현에 사용할 수 있는 수준인지 확인한다. 이번 체크포인트는 사용자가 실행한 데이터 건수, 필수 필드 null, 코드값, 상태값, 연결키 확인 쿼리 결과를 분석한 기록이다.

## 입력 자료

- 사용자 첨부 파일: `pasted-text.txt`
- 포함된 쿼리:
  - 테이블별 row count
  - `tour_requests`, `guides`, `drivers` 핵심 필드 누락 여부
  - `syscode` 코드값
  - 주요 상태값 분포
  - `resource_availability` 연결키 분포 및 `partner` 조인
  - `tour_requests`와 `reservations` 연결 확인
  - `resv_info`와 `matching_candidates` 연결 샘플 확인

## 테이블별 데이터 건수

| 테이블 | 건수 | 판단 |
| --- | ---: | --- |
| `resv_info` | 2296 | 기존 운영 예약 데이터는 충분히 많다. 단, 스코어링 필드가 직접적으로 부족하다. |
| `tour_requests` | 7 | 스코어링 설계용 요청 데이터는 적지만 존재한다. 샘플/PoC 테스트 가능. |
| `guides` | 20 | 가이드 후보 데이터 존재. |
| `drivers` | 20 | 드라이버 후보 데이터 존재. |
| `vehicles` | 20 | 차량 후보 데이터 존재. |
| `resource_availability` | 10 | 매우 적다. 실제 후보 생성 결과가 제한될 수 있다. |
| `matching_candidates` | 12 | 기존 후보 결과 샘플 존재. |
| `reservations` | 5 | 예약 충돌 확인 샘플 존재. |
| `partner` | 465 | 기존 파트너 원장 데이터는 충분하다. |
| `syscode` | 572 | 코드 데이터 존재. |
| `platform_region` | 9 | 지역 코드 데이터 존재. |

## 필수값 품질

### `tour_requests`

| 항목 | 결과 |
| --- | ---: |
| 전체 | 7 |
| `region_code` null | 0 |
| `start_at` null | 0 |
| `end_at` null | 0 |
| `group_size` null 또는 0 | 0 |
| `requested_language` 누락 | 0 |
| `requested_vehicle_type` 누락 | 0 |
| `budget_max` null 또는 0 | 0 |

판단:

- `tour_requests`는 스코어링 입력으로 필요한 필수 필드가 모두 채워져 있다.
- PDF 설계 기준 구현/테스트 원천으로 가장 적합하다.
- 단, 건수가 7건이라 다양한 경계조건 테스트에는 부족하다.

### `guides`

| 항목 | 결과 |
| --- | ---: |
| 전체 | 20 |
| `languages` 누락 | 0 |
| `themes` 누락 | 0 |
| `base_region_code` 누락 | 0 |
| `price_per_day` 누락/0 | 0 |
| `rating_avg` null | 0 |

판단:

- 가이드 점수 계산에 필요한 핵심 필드는 샘플 기준 모두 채워져 있다.
- 언어/테마 값의 형식은 아직 별도 확인이 필요하다. 예: 단일 코드인지, comma-separated인지, 레벨 포함 문자열인지.

### `drivers`

| 항목 | 결과 |
| --- | ---: |
| 전체 | 20 |
| `vehicle_types` 누락 | 0 |
| `languages` 누락 | 0 |
| `base_region_code` 누락 | 0 |
| `price_per_day` 누락/0 | 0 |

판단:

- 드라이버 점수 계산에 필요한 핵심 필드는 샘플 기준 모두 채워져 있다.
- `regions`와 `vehicle_types` 값 형식 확인이 필요하다.

## 코드값 확인

### 차종 코드: `CAR_TYPE`

확인된 주요 코드:

| code_id | code_name | code_desc |
| --- | --- | --- |
| `M001` | 승용택시 | null |
| `PA001` | 세단 택시 | 승용차(또는 동급) |
| `PT001` | 세단 | (4인승) |
| `PA002` | 미니밴 택시 | SUV(또는 동급) |
| `PT003` | 미니밴 | (9인승) |
| `PA003` | 라지밴 택시 | 콜밴(또는 동급) |
| `PT005` | 라지밴 | (15인승) |
| `PT002` | 프리미엄 세단 | (4인승) |
| `PT004` | 프리미엄 미니밴 | (7인승) |
| `M002` | 콜밴 | null |
| `M003` | 카니발리무진 | null |
| `M004` | 전세버스 | null |

판단:

- 차종 코드는 존재한다.
- 그러나 "상위 차종 또는 운영상 허용 가능한 대체 차종" 관계를 기계적으로 판단할 컬럼은 아직 없다.
- 코드명/설명으로 추론하면 위험하다. 차종 호환 매트릭스가 별도 필요하다.

### 언어 코드: `LNG`

확인된 코드:

```text
de, en, Es, fr, id, It, ja, ko, Ru, th, vi, zh-CN, zh-TW
```

주의:

- `Es`, `It`, `Ru`처럼 대문자가 섞여 있다.
- 요청 언어와 리소스 언어 비교 시 case-sensitive 비교를 그대로 쓰면 오매칭 위험이 있다.
- 구현에서는 언어 코드를 정규화하거나 DB 코드값과 동일 비교 정책을 확정해야 한다.

### 투어 타입: `TOUR_TYPE`

확인된 코드:

```text
ACTIVE, RELAXATION, FOOD, LOCAL, NATURE, CITY, FAMILY, KIDS, SENIOR, HISTORY, LUXURY
```

판단:

- `tour_requests.requested_theme`과 `guides.themes` 비교에 사용할 수 있다.

## 상태값 확인

| 테이블 | 상태 컬럼 | 값 분포 | 필터 판단 |
| --- | --- | --- | --- |
| `tour_requests` | `status` | `APPROVED` 3, `PENDING` 2, `CANCELLED` 1, `COMPLETED` 1 | 후보 생성 대상은 보통 `APPROVED` 또는 `PENDING` 중 정책 결정 필요 |
| `guides` | `status` | `ACTIVE` 14, `INACTIVE` 2, `SUSPENDED` 4 | `ACTIVE`만 후보 |
| `drivers` | `approval_status`, `operation_status` | `APPROVED/ACTIVE` 14, `APPROVED/SUSPENDED` 4, `REJECTED/''` 2 | `APPROVED` + `ACTIVE`만 후보 |
| `vehicles` | `approval_status`, `operation_status` | `APPROVED/ACTIVE` 18, `APPROVED/INACTIVE` 1, `PENDING/READY` 1 | `APPROVED` + `ACTIVE`만 후보 |
| `resource_availability` | `status` | `ACTIVE` 10 | `ACTIVE`만 후보 |
| `matching_candidates` | `candidate_status` | `OFFERED` 5, `SELECTED` 4, `CANCELLED` 3 | 재생성/충돌 정책에 반영 |
| `reservations` | `status` | `CONFIRMED` 3, `COMPLETED` 1, `CANCELLED` 1 | 충돌 제외는 `CONFIRMED`, 진행/완료 정책 확인 필요 |

## 가용성 연결 확인

### `resource_availability` 분포

| resource_type | total | vehicle_id 있음 | partner_id 있음 | partner_no 있음 |
| --- | ---: | ---: | ---: | ---: |
| `DRIVER` | 1 | 0 | 1 | 1 |
| `GUIDE` | 1 | 0 | 1 | 1 |
| `VEHICLE` | 8 | 8 | 0 | 0 |

판단:

- 차량 가용성은 `vehicle_id`로 연결된다.
- 가이드/드라이버 가용성은 `partner_id`, `partner_no`로 연결된다.
- 가이드/드라이버 가용성 데이터가 각 1건뿐이라 후보 생성 테스트 범위가 매우 좁다.

### `resource_availability`와 `partner` 조인 결과

| resource_type | partner_id | partner_no | matched partner_type | 판단 |
| --- | --- | ---: | --- | --- |
| `DRIVER` | `cjcodriver01` | 315 | `DRIVER` | 정상 |
| `GUIDE` | `dodo122` | 841 | `DRIVER` | 이상 |

중요 문제:

- `resource_availability.resource_type='GUIDE'`인데 조인된 `partner.partner_type`은 `DRIVER`다.
- 이 행은 데이터 입력 오류, resource_type 오류, 또는 `partner`의 역할 정의 오류일 수 있다.
- 이 상태로 구현하면 가이드 가용성 필터가 잘못 동작한다.

구현 전 확인 필요:

```sql
SELECT *
FROM partner
WHERE partner_id = 'dodo122'
   OR user_no = 841;
```

```sql
SELECT *
FROM guides
WHERE id = 841
   OR name LIKE '%dodo%';
```

```sql
SELECT *
FROM resource_availability
WHERE resource_type = 'GUIDE';
```

## 요청-예약 연결 확인

`tour_requests`와 `reservations`는 연결된다.

| tour_request_id | reservation_id | reservation status |
| ---: | ---: | --- |
| 1 | 1 | `CONFIRMED` |
| 2 | 2 | `CANCELLED` |
| 3 | 3 | `CONFIRMED` |
| 4 | 5 | `CONFIRMED` |
| 5 | 7 | `COMPLETED` |
| 6 | null | null |
| 7 | null | null |

판단:

- `reservations.requested_id = tour_requests.id` 연결은 실제로 동작한다.
- `tour_requests` 6, 7은 아직 reservation이 없으므로 신규 후보 생성 테스트 대상으로 적합하다.
- `tour_requests` 1~5는 기존 예약/충돌 테스트 대상으로 쓸 수 있다.

## `resv_info`와 `matching_candidates` 연결 샘플

사용자가 실행한 left join 샘플 50건에서는 `matching_candidates`가 모두 null이었다.

주의:

- 이 결과만으로 `matching_candidates`가 `resv_info`와 연결되지 않는다고 결론내리면 안 된다.
- 쿼리가 `resv_info`의 앞 50건만 가져온 결과일 가능성이 높고, `matching_candidates`의 샘플 reserve_id는 2025년/2026년 일부 특정 예약일 수 있다.

다음 확인 쿼리:

```sql
SELECT
    mc.id AS candidate_id,
    mc.reserve_id,
    mc.user_no,
    ri.reserve_id AS matched_reserve_id,
    ri.user_no AS matched_user_no,
    ri.reserve_status
FROM matching_candidates mc
LEFT JOIN resv_info ri
    ON ri.reserve_id = mc.reserve_id
   AND ri.user_no = mc.user_no
ORDER BY mc.id;
```

이 쿼리에서 `matched_reserve_id`가 null이면 `matching_candidates`의 FK 설계와 실제 `resv_info` 데이터가 불일치하는 것이다.

## 현재 구현 가능성 판단

### 구현 가능한 부분

- `tour_requests` 기반 요청 로딩
- `guides`, `drivers`, `vehicles` 기반 후보 조회
- `guides.status='ACTIVE'` 필터
- `drivers.approval_status='APPROVED' AND operation_status='ACTIVE'` 필터
- `vehicles.approval_status='APPROVED' AND operation_status='ACTIVE'` 필터
- `resource_availability.status='ACTIVE'` 기반 가용성 필터
- `reservations.requested_id = tour_requests.id` 기반 기존 예약 확인
- `matching_candidates` 결과 저장 구조 일부

### 아직 구현하면 위험한 부분

- `GUIDE` 가용성 연결: 현재 샘플에서 파트너 타입 불일치
- `guides/drivers`와 `partner` 정식 연결키
- `matching_candidates.guide_id/driver_id`에 어떤 ID를 저장할지
- `matching_candidates`와 `resv_info` 실제 FK 데이터 정합성
- `stability_score` 저장 여부
- 차량 `breakdown_count` 부재 처리
- 차종 상위 호환 규칙
- 언어 코드 대소문자 정규화 정책

## 다음에 실행할 우선 쿼리

### 1. `matching_candidates`가 실제 `resv_info`와 연결되는지 확인

```sql
SELECT
    mc.id AS candidate_id,
    mc.reserve_id,
    mc.user_no,
    ri.reserve_id AS matched_reserve_id,
    ri.user_no AS matched_user_no,
    ri.reserve_status
FROM matching_candidates mc
LEFT JOIN resv_info ri
    ON ri.reserve_id = mc.reserve_id
   AND ri.user_no = mc.user_no
ORDER BY mc.id;
```

### 2. 가이드 가용성 이상 데이터 확인

```sql
SELECT
    ra.*,
    p.partner_type,
    p.partner_name
FROM resource_availability ra
LEFT JOIN partner p
    ON p.partner_id = ra.partner_id
   AND p.user_no = ra.partner_no
WHERE ra.resource_type = 'GUIDE';
```

### 3. `guides/drivers` 값 형식 확인

```sql
SELECT id, name, languages, themes, base_region_code, region_level
FROM guides
ORDER BY id
LIMIT 20;
```

```sql
SELECT id, name, vehicle_types, languages, regions, base_region_code
FROM drivers
ORDER BY id
LIMIT 20;
```

### 4. `tour_requests` 6, 7 후보 생성 테스트 가능성 확인

```sql
SELECT *
FROM tour_requests
WHERE id IN (6, 7);
```

```sql
SELECT *
FROM reservations
WHERE requested_id IN (6, 7);
```

## 현재 결론

데이터는 존재하고, `tour_requests` 기준으로 스코어링 PoC를 시작할 수 있을 정도의 필수값은 채워져 있다. 하지만 가용성 데이터가 너무 적고, `GUIDE` 가용성 행이 드라이버 파트너로 연결되는 이상 데이터가 있다.

따라서 다음 단계는 "바로 구현"이 아니라, 위 연결 오류와 `matching_candidates`-`resv_info` 정합성을 먼저 확인하는 것이다. 이 두 가지가 확인되면 Repository 설계를 확정할 수 있다.

