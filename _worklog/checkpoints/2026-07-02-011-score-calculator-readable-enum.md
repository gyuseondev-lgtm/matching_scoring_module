# 2026-07-02 체크포인트 011: 점수 계산 코드 가독성 및 Enum 정리

## 목적

`score_calculator.py`의 산식을 주니어 개발자가 읽기 쉽도록 정리했다.

사용자 요청:

- 한 줄 삼항식으로 처리한 계산을 풀어서 작성한다.
- 필요하면 함수로 분리한다.
- 산식 숫자를 코드 본문에 직접 쓰지 말고 Enum으로 관리한다.

## 변경 파일

- `prototype/matching_scoring/score_calculator.py`

## 주요 변경 내용

### 1. 점수 숫자 Enum 분리

다음 값을 `IntEnum` 또는 `Enum`으로 분리했다.

- 공통 점수 범위: `ScoreRange`
- 가능/불가능 원점수: `BinaryScore`
- 가이드 항목 배점: `GuideScore`
- 차량 항목 배점: `VehicleScore`
- 드라이버 항목 배점: `DriverScore`
- 가격 점수: `PriceScore`, `SmallPriceScore`
- 안정성 점수: `StabilityScore`
- 평점/리뷰 기준: `ReviewScore`
- 개수/용량 기준: `CountValue`, `CapacityRemaining`
- 예산 비율과 소수 감점 단위: `ScoreRatio`

### 2. 한 줄 조건식 제거

예전 형태:

```python
language = 25 if contains_code(guide.languages, request.requested_language) else 0
```

현재 형태:

```python
language = self._guide_language_score(request, guide)
```

내부에서는 언어 가능 여부를 먼저 `100/0`으로 판단한 뒤, 가이드 언어 배점으로 환산한다.

### 3. 계산 함수 분리

다음 계산을 별도 함수로 분리했다.

- `_guide_language_score`
- `_guide_theme_score`
- `_driver_vehicle_score`
- `_driver_region_score`
- `_driver_language_score`
- `_vehicle_region_score`
- `_vehicle_seat_score`
- `_vehicle_luggage_score`
- `_vehicle_premium_score`
- `binary_score`

## 검증

다음 명령으로 파이썬 문법 검사를 통과했다.

```text
C:\Users\shy18\AppData\Local\Python\pythoncore-3.11-64\python.exe -m compileall prototype
```

검사 후 생성된 `__pycache__`는 정리했다.

## 다음 작업

1. 다른 산식 파일이 추가되면 같은 방식으로 배점은 Enum, 계산 흐름은 함수로 분리한다.
2. 실제 테스트 데이터로 점수가 의도한 범위 안에서 나오는지 확인한다.
3. PDF 설계 문서의 항목별 배점과 `ScoreCalculator` Enum 값이 일치하는지 한 번 더 대조한다.
