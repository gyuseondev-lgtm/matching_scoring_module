# Checkpoint 2026-07-02-008: No tour_request_id Column Decision

## 목적

`matching_candidates.tour_request_id` 컬럼을 추가하지 않기로 한 결정을 기록한다.

## 결정

`matching_candidates` 테이블에는 `tour_request_id` 컬럼을 추가하지 않는다.

기존 저장 구조를 유지한다.

```text
matching_candidates.reserve_id
matching_candidates.user_no
```

이 두 컬럼으로 기존 예약 테이블과 연결한다.

```text
matching_candidates.reserve_id + matching_candidates.user_no
-> resv_info.reserve_id + resv_info.user_no
```

## 배경

이전 논의에서는 `tour_requests`를 스코어링 입력 원천으로 사용할 경우, 후보 결과가 어떤 `tour_requests.id`에서 계산되었는지 직접 추적하기 위해 다음 컬럼 추가를 제안했다.

```sql
ALTER TABLE matching_candidates
ADD COLUMN tour_request_id BIGINT NULL COMMENT '투어요청ID'
AFTER user_no;
```

사용자는 이 컬럼을 추가하지 않기로 결정했다.

## 설계 영향

### 유지되는 것

- `matching_candidates`는 기존처럼 `reserve_id`, `user_no` 중심으로 저장한다.
- `resv_info`와의 연결은 이미 실제 데이터 12건에서 정상 확인되었다.
- `reservations`에는 여전히 `requested_id`와 `matching_candidate_id`가 존재한다.

### 주의할 것

`matching_candidates`에 `tour_request_id`를 저장하지 않으면, 후보 row만 보고 어떤 `tour_requests.id`에서 계산된 결과인지 직접 알 수 없다.

따라서 구현/설계에서 다음 중 하나를 명확히 해야 한다.

1. 모듈 실행 입력으로 `tour_request_id`, `reserve_id`, `user_no`를 함께 받고, 결과 저장은 `reserve_id`, `user_no`만 사용한다.
2. `tour_requests`는 내부 계산용 임시/신규 요청 테이블로만 사용하고, 운영 추적은 `resv_info` 기준으로 한다.
3. 최종 확정 단계에서 `reservations.requested_id`와 `reservations.matching_candidate_id`를 통해 선택 후보와 요청을 연결한다.

## 권장 구현 전제

`tour_request_id`를 컬럼으로 저장하지 않기로 했으므로, 스코어링 모듈의 실행 입력은 다음 형태가 되어야 한다.

```text
generate_candidates(
  tour_request_id,
  reserve_id,
  user_no
)
```

역할:

- `tour_request_id`: 스코어링 입력값 조회
- `reserve_id`, `user_no`: `matching_candidates` 저장 키

이렇게 하면 DB 컬럼을 추가하지 않으면서도 모듈 실행 시점에는 어떤 요청을 계산하는지 명확히 알 수 있다.

## 위험

`tour_request_id`를 저장하지 않는 결정은 DB 스키마 변경을 줄인다는 장점이 있지만, 다음 위험이 있다.

| 위험 | 설명 |
| --- | --- |
| 후보 row 단독 추적 어려움 | `matching_candidates`만 보면 어떤 `tour_requests.id` 입력인지 바로 알 수 없다. |
| 재계산 추적 어려움 | 같은 `reserve_id/user_no`에 여러 `tour_requests`가 연결될 수 있는 구조라면 구분이 어렵다. |
| 디버깅 비용 증가 | 후보 생성 원천 요청을 찾으려면 실행 로그나 `reservations` 연결을 함께 봐야 한다. |

이 위험은 현재 결정 사항으로 수용한다. 대신 설계문서에는 `reserve_id/user_no` 중심 추적 방식을 명확히 적어야 한다.

## 유지되는 별도 결정

`matching_candidates.stability_score` 컬럼 추가 결정은 유지한다.

```sql
ALTER TABLE matching_candidates
ADD COLUMN stability_score DECIMAL(5,2) DEFAULT 0.00 COMMENT '안정성스코어'
AFTER price_score;
```

