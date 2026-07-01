# Checkpoint 2026-07-02-007: Stability Score Column Decision

## 목적

`matching_candidates`에 `stability_score` 컬럼을 추가하기로 한 결정을 사유와 함께 기록한다.

## 결정

`matching_candidates` 테이블에 `stability_score` 컬럼을 추가한다.

권장 DDL:

```sql
ALTER TABLE matching_candidates
ADD COLUMN stability_score DECIMAL(5,2) DEFAULT 0.00 COMMENT '안정성스코어'
AFTER price_score;
```

컬럼 위치는 점수 컬럼의 의미 흐름을 고려해 `price_score` 뒤, `total_score` 앞이 적절하다.

```text
guide_score
vehicle_score
driver_score
price_score
stability_score
total_score
```

## 결정 사유

PDF 설계의 최종 점수 산식은 `stability_score`를 10% 반영한다.

```text
total_score =
  guide_score * 0.40
  + vehicle_score * 0.20
  + driver_score * 0.20
  + price_score * 0.10
  + stability_score * 0.10
```

따라서 `stability_score`를 계산하면서 DB에 저장하지 않으면 다음 문제가 생긴다.

| 문제 | 설명 |
| --- | --- |
| 점수 재현 불가 | `total_score`가 어떤 안정성 점수로 계산됐는지 나중에 확인하기 어렵다. |
| 운영 설명 불가 | 운영자가 "왜 이 후보가 추천됐는지" 확인할 때 점수 근거가 일부 사라진다. |
| 설계와 DB 불일치 | PDF 산식에는 있는 점수 항목이 저장 테이블에는 없어 구현/문서/운영이 어긋난다. |
| 테스트 검증 약화 | 저장된 후보의 `total_score`를 DB 값만으로 재계산하기 어렵다. |

따라서 안정성 점수를 최종 점수에 반영할 계획이라면 컬럼 추가가 가장 책임 있는 선택이다.

## 안정성 점수의 의미

`stability_score`는 후보 조합이 취소, 클레임, 노쇼, 차량 문제 없이 안정적으로 수행될 가능성을 평가하는 조합 점수다.

PDF 기준 개념:

```text
기본 점수 80
+ 가이드 취소 이력 없음
+ 드라이버 취소 이력 없음
+ 차량 고장 이력 없음
- 가이드 클레임 과다
- 드라이버 클레임 과다
- 차량 고장 과다
최종 0~100 제한
```

현재 테스트베드 DB에는 `vehicles.breakdown_count`가 없다. 따라서 초기 구현에서는 차량 고장 이력 항목을 제외하거나 별도 컬럼/테이블 추가 여부를 별도 결정해야 한다.

## 구현 영향

### 저장 테이블

`matching_candidates` 저장 시 다음 값을 함께 저장한다.

- `guide_score`
- `vehicle_score`
- `driver_score`
- `price_score`
- `stability_score`
- `total_score`

### 계산 모듈

`StabilityScorer` 또는 동등한 계산 함수를 별도 구성한다.

초기 산식 예:

```text
stability_score = clamp(
  80
  + guide_no_cancel_bonus
  + driver_no_cancel_bonus
  + vehicle_no_breakdown_bonus_or_0
  - guide_complaint_penalty
  - driver_complaint_penalty
  - vehicle_breakdown_penalty_or_0,
  0,
  100
)
```

### 테스트

필수 테스트:

- 안정성 점수가 0 미만으로 내려가지 않는지
- 안정성 점수가 100을 초과하지 않는지
- `total_score` 계산이 저장된 `stability_score`를 사용해 재현되는지
- `stability_score`가 없는 기존 row에 기본값 `0.00`이 들어가도 마이그레이션이 실패하지 않는지

## 남은 결정 사항

`stability_score` 컬럼 추가는 확정했다. 다만 다음은 아직 별도 결정이 필요하다.

1. `vehicles.breakdown_count`를 추가할지
2. 차량 고장 이력을 별도 테이블에서 가져올지
3. 초기 구현에서는 차량 고장 항목을 제외하고 가이드/드라이버 신뢰도만으로 안정성 점수를 계산할지

현 단계에서는 `stability_score` 컬럼을 먼저 추가하고, 차량 고장 이력은 별도 후속 결정으로 분리하는 것이 가장 단순하고 안전하다.

