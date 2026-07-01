# Checkpoint 2026-07-02-009: Prototype Scaffold

## 목적

주니어 개발자가 이어받기 쉽도록 `prototype/` 아래에 단순한 Python 프로토타입 구조와 기본 코드를 작성한다.

## 구현 기준

- 테스트베드 신규 스키마 기준으로 작성한다.
- `matching_candidates.tour_request_id`는 추가하지 않는다.
- `matching_candidates.stability_score`는 추가하는 전제로 작성한다.
- 리소스 수가 작다는 전제에서 가이드/드라이버/차량/가용성/예약을 리스트로 한 번에 가져와 메모리에서 처리한다.
- 과한 Repository, Strategy, Factory 계층은 만들지 않는다.
- 실행 주체만 클래스로 둔다.

## 생성한 구조

```text
prototype/
  README.md
  requirements.txt
  .env.example
  run_console.py
  matching_scoring/
    __init__.py
    config.py
    models.py
    store.py
    score_calculator.py
    matching_service.py
```

## 주요 역할

| 파일 | 역할 |
| --- | --- |
| `config.py` | DB 접속정보와 기본 점수 가중치 |
| `models.py` | `@dataclass` 기반 데이터 객체 |
| `store.py` | DB에서 목록을 가져오고 후보/선택 결과 저장 |
| `score_calculator.py` | 가이드/차량/드라이버/가격/안정성/최종 점수 계산 |
| `matching_service.py` | 필수조건 필터링, 조합 생성, 랭킹, 저장 흐름 |
| `run_console.py` | 콘솔에서 목록 조회, 후보 생성, 후보 선택 |

## 클래스 기준

실행 주체:

- `MatchingStore`: DB 담당
- `ScoreCalculator`: 점수 계산 담당
- `MatchingService`: 전체 후보 생성 흐름 담당

데이터 객체:

- `TourRequest`
- `Guide`
- `Driver`
- `Vehicle`
- `Availability`
- `Reservation`
- `MatchingCandidate`

## 현재 구현 흐름

```text
run_console.py
-> MatchingStore 생성
-> ScoreCalculator 생성
-> MatchingService 생성
-> tour_request 선택
-> generate_candidates(tour_request_id, reserve_id, user_no)
-> 후보 저장
-> TOP 3 출력
-> 후보 선택 시 SELECTED 처리
```

## 중요한 구현 전제

### 1. 가용성 연결

현재 프로토타입은 가이드/드라이버 가용성을 다음처럼 매칭한다.

```text
resource_availability.partner_no == guides.id
resource_availability.partner_no == drivers.id
```

이 전제는 아직 최종 확정이 아니다. 테스트베드 데이터의 `GUIDE` 가용성 오류가 있었기 때문에 실제 정정 데이터로 검증해야 한다.

### 2. `stability_score`

`store.py`의 후보 저장 SQL은 `stability_score` 컬럼이 존재한다고 가정한다.

따라서 실행 전 테스트베드 DB에 다음 DDL이 필요하다.

```sql
ALTER TABLE matching_candidates
ADD COLUMN stability_score DECIMAL(5,2) DEFAULT 0.00 COMMENT '안정성스코어'
AFTER price_score;
```

### 3. `tour_request_id`

`matching_candidates`에는 `tour_request_id`를 저장하지 않는다. 콘솔 실행 시 `tour_request_id`, `reserve_id`, `user_no`를 함께 받아 계산과 저장을 연결한다.

## 검증

문법 검사를 수행했다.

```text
C:\Users\shy18\AppData\Local\Python\pythoncore-3.11-64\python.exe -m compileall prototype
```

결과:

```text
compileall 성공
```

`py` 런처는 현재 환경에서 PATH에 없어 실패했다.

## 남은 작업

1. `.env` 작성
2. `pip install -r prototype/requirements.txt`
3. 테스트베드 DB에 `stability_score` 컬럼 추가
4. `resource_availability`의 `GUIDE` 테스트 데이터 정정
5. 콘솔 실행으로 후보 생성 검증
6. 실제 결과를 보고 가이드/드라이버 ID 저장 정책과 가용성 연결키 보정

