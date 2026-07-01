# Checkpoint 2026-07-02-005: DB Linkage Follow-up

## 목적

이전 체크포인트에서 남긴 두 가지 핵심 확인 사항을 추가 쿼리 결과로 판정한다.

1. `resource_availability`의 `GUIDE` 행이 실제 가이드와 연결되는지
2. `matching_candidates`가 `resv_info`와 실제로 연결되는지

## 확인 결과 요약

| 확인 항목 | 결과 | 판단 |
| --- | --- | --- |
| `resource_availability`의 `GUIDE` 행 | `partner_id='dodo122'`, `partner_no=841`가 `partner_type='DRIVER'`로 조인됨 | 데이터 오류 또는 설계 불일치 |
| `matching_candidates` 12건과 `resv_info` 연결 | 12건 모두 `reserve_id`, `user_no`로 매칭됨 | 정상 |

## `GUIDE` 가용성 확인 결과

쿼리 결과:

| id | resource_type | partner_id | partner_no | available_date | start_time | end_time | status | partner_type |
| ---: | --- | --- | ---: | --- | --- | --- | --- | --- |
| 10 | `GUIDE` | `dodo122` | 841 | 2026-07-10 | 07:00:00 | 23:00:00 | `ACTIVE` | `DRIVER` |

판단:

- `resource_availability.resource_type='GUIDE'`인데 실제 연결된 `partner.partner_type`은 `DRIVER`다.
- 이 데이터는 현재 상태로 가이드 가용성 필터에 사용하면 안 된다.
- 원인은 셋 중 하나로 봐야 한다.
  - `resource_availability.resource_type` 값이 잘못 입력됐다.
  - `partner`의 `partner_type`이 잘못 입력됐다.
  - 가이드 가용성은 `partner`가 아니라 `guides`에 직접 연결해야 하는데 현재 테이블 설계가 혼재되어 있다.

구현 영향:

- 차량 가용성은 `vehicle_id`로 확인 가능하다.
- 드라이버 가용성은 `partner_id/partner_no`로 확인 가능하다.
- 가이드 가용성은 현재 샘플 데이터 기준으로 신뢰할 수 없다.
- 따라서 구현 시 가이드 가용성 필터는 데이터 정정 후 적용하거나, `guides`와의 별도 연결 정책을 확정해야 한다.

## `matching_candidates`와 `resv_info` 연결 확인 결과

`matching_candidates` 12건은 모두 `resv_info.reserve_id`, `resv_info.user_no`와 매칭된다.

확인된 상태값:

| candidate_id | reserve_status |
| ---: | --- |
| 1 | `DW` |
| 2 | `DW` |
| 3 | `DW` |
| 4 | `DW` |
| 5 | `DP` |
| 6 | `DW` |
| 7 | `DP` |
| 8 | `DP` |
| 9 | `DP` |
| 10 | `DW` |
| 11 | `DW` |
| 12 | `DW` |

판단:

- 결과 저장 테이블 `matching_candidates`의 예약 FK는 실제 데이터 기준 정상이다.
- 이전 샘플 left join에서 매칭이 안 보였던 것은 `resv_info` 앞 50건 샘플에 해당 후보 예약이 없었기 때문이다.
- `matching_candidates` 저장은 `reserve_id`, `user_no` 기준으로 진행해도 된다.

## 현재 결론

스코어링 구현에서 결과 저장 경로는 어느 정도 확정할 수 있다.

```text
matching_candidates.reserve_id + matching_candidates.user_no
-> resv_info.reserve_id + resv_info.user_no
```

반면 리소스 가용성 경로는 아직 불완전하다.

```text
resource_availability(resource_type='GUIDE')
-> partner(partner_type='DRIVER')
```

이 불일치 때문에 가이드 가용성 필터를 그대로 구현하면 잘못된 후보 제외/포함이 발생한다.

## 다음 확인/결정 사항

### 1. 가이드 가용성 데이터 정정 여부

다음 중 하나를 결정해야 한다.

- `resource_availability`의 `GUIDE` 행을 실제 `GUIDE` 파트너로 수정한다.
- `partner.dodo122`가 실제로 가이드도 겸하는지 확인하고, 다중 역할 표현 방식을 정한다.
- 가이드 가용성은 `partner`가 아니라 `guides.id` 기준으로 별도 관리하도록 설계를 바꾼다.

### 2. `guides/drivers`와 `partner` 연결키

아직 다음 관계는 확정되지 않았다.

```text
guides.id -> partner.partner_id/user_no ?
drivers.id -> partner.partner_id/user_no ?
```

이 관계가 확정되어야 `resource_availability`와 `guides/drivers` 점수 테이블을 안전하게 연결할 수 있다.

### 3. 요청 원천 선택

현재 판단:

- 스코어링 입력은 `tour_requests`가 가장 적합하다.
- 결과 저장은 `matching_candidates -> resv_info` 경로가 정상이다.
- 따라서 구현 설계에는 `tour_requests`와 `resv_info`를 연결하는 정책이 반드시 필요하다.

## 다음 추천 쿼리

### `dodo122/841`의 실제 역할 확인

```sql
SELECT
    partner_id,
    user_no,
    partner_type,
    partner_name,
    guide_support_lang,
    guide_tour_region_code,
    driver_license_type,
    offer_region_code
FROM partner
WHERE partner_id = 'dodo122'
   OR user_no = 841;
```

### 가이드/드라이버와 partner의 이름/ID 연결 가능성 확인

```sql
SELECT
    g.id AS guide_id,
    g.name AS guide_name,
    p.partner_id,
    p.user_no,
    p.partner_type,
    p.partner_name
FROM guides g
LEFT JOIN partner p
    ON p.partner_type = 'GUIDE'
   AND (
        p.user_no = g.id
        OR p.partner_id = CAST(g.id AS CHAR)
        OR p.partner_name = g.name
   )
ORDER BY g.id;
```

```sql
SELECT
    d.id AS driver_id,
    d.name AS driver_name,
    p.partner_id,
    p.user_no,
    p.partner_type,
    p.partner_name
FROM drivers d
LEFT JOIN partner p
    ON p.partner_type = 'DRIVER'
   AND (
        p.user_no = d.id
        OR p.partner_id = CAST(d.id AS CHAR)
        OR p.partner_name = d.name
   )
ORDER BY d.id;
```

### `tour_requests`와 `resv_info` 연결 후보 확인

```sql
SELECT
    tr.id AS tour_request_id,
    tr.customer_id,
    tr.start_at,
    tr.end_at,
    tr.region_code,
    ri.reserve_id,
    ri.user_no,
    ri.region_code AS resv_region_code,
    ri.reserve_dt,
    ri.reserve_status
FROM tour_requests tr
LEFT JOIN resv_info ri
    ON ri.user_no = tr.customer_id
   AND ri.region_code = tr.region_code
ORDER BY tr.id, ri.reserve_dt DESC
LIMIT 50;
```

