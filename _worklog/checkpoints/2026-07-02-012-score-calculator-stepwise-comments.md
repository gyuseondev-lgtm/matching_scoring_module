# 2026-07-02 체크포인트 012: 함수 호출 단계 분리 및 중간 변수 주석 보강

## 목적

`score_calculator.py`에서 함수 인자 안에 다른 함수 호출을 넣는 방식을 제거하고, 주니어 개발자가 계산 흐름을 단계별로 따라갈 수 있도록 중간 변수와 주석을 보강했다.

사용자 요청:

- 함수 파라미터 안에 다른 함수를 넣어 처리하지 않는다.
- 먼저 함수 반환값을 변수로 받는다.
- 그 변수를 다음 함수의 파라미터로 전달한다.
- 함수 반환값이 변수에 설정되는 부분은 변수 위에 설명 주석을 단다.

## 변경 파일

- `prototype/matching_scoring/score_calculator.py`

## 주요 변경 내용

### 1. 중첩 함수 호출 제거

예전 형태:

```python
language_match_score = binary_score(contains_code(guide.languages, request.requested_language))
```

현재 형태:

```python
# 가이드 언어 목록에 요청 언어가 포함되어 있는지 확인한 값이다.
can_speak_requested_language = contains_code(guide.languages, request.requested_language)

# 언어 지원 여부를 100점 또는 0점으로 변환한 원점수다.
language_match_score = binary_score(can_speak_requested_language)
```

### 2. 함수 반환값 변수 주석 추가

다음처럼 함수 반환값을 받는 주요 변수 위에 설명 주석을 추가했다.

- `language`
- `region`
- `theme`
- `rating`
- `price`
- `reliability`
- `guide_total_score`
- `vehicle_total_score`
- `driver_total_score`
- `normalized_rating`
- `quality_score`

### 3. contains_code 내부 메서드 체인 분리

예전 형태:

```python
for item in raw.replace("|", ",").split(","):
    normalized_item = item.strip().lower()
```

현재는 구분자 정규화, split, strip, lower를 각각 변수로 나눴다.

## 검증

다음 명령으로 파이썬 문법 검사를 통과했다.

```text
C:\Users\shy18\AppData\Local\Python\pythoncore-3.11-64\python.exe -m compileall prototype
```

추가로 다음 패턴 검색에서 실제 코드의 중첩 함수 호출 패턴이 남지 않는 것을 확인했다.

```text
rg -n "\w+\([^\n]*\w+\(|\.\w+\([^\n]*\.\w+\(" prototype\matching_scoring\score_calculator.py -S
```

검색 결과는 docstring의 `점수(float)` 설명만 잡혔다.

## 다음 작업

1. 같은 코드 스타일 기준을 `matching_service.py`, `store.py`에도 적용할지 검토한다.
2. 산식 결과가 기존 값과 동일한지 샘플 데이터 기반으로 비교한다.
3. 점수 기준 확정 후 설계 문서의 의사코드도 같은 단계형 스타일로 정리한다.
