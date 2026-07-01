# Handoff

최종 갱신: 2026-07-02

## 현재 상태

- 저장소 루트: `D:\00.git\matching_scroing_module`
- 작업기록 폴더: `_worklog/`
- 작업 원칙 파일: `AGENT.md`
- 현재 구성된 파일:
  - `_worklog/INDEX.md`
  - `_worklog/HANDOFF.md`
  - `_worklog/checkpoints/2026-07-02-001-worklog-environment-setup.md`
  - `_worklog/checkpoints/2026-07-02-002-scoring-module-analysis.md`
  - `_worklog/checkpoints/2026-07-02-003-db-table-verification.md`
  - `_worklog/checkpoints/2026-07-02-004-db-data-quality-check.md`
  - `_worklog/checkpoints/2026-07-02-005-db-linkage-followup.md`
  - `_worklog/checkpoints/2026-07-02-006-prod-db-structure-gap.md`
  - `_worklog/checkpoints/2026-07-02-007-stability-score-column-decision.md`
  - `_worklog/checkpoints/2026-07-02-008-no-tour-request-id-column.md`
  - `_worklog/checkpoints/2026-07-02-009-prototype-scaffold.md`
  - `_worklog/checkpoints/2026-07-02-010-code-comment-pass.md`
- `_worklog/checkpoints/2026-07-02-011-score-calculator-readable-enum.md`
- `_worklog/checkpoints/2026-07-02-012-score-calculator-stepwise-comments.md`
  - `_worklog/checkpoints/2026-07-02-011-score-calculator-readable-enum.md`
- `_worklog/checkpoints/2026-07-02-012-score-calculator-stepwise-comments.md`
  - `_worklog/checkpoints/2026-07-02-012-score-calculator-stepwise-comments.md`

## 최신 체크포인트 요약

`prototype/` 아래에 단순 Python 프로토타입 구조와 기본 코드를 작성했고, 이후 클래스/함수 단위 주석을 보강했다. 구조는 `MatchingStore`, `ScoreCalculator`, `MatchingService`, 콘솔 실행 파일 중심이며, 리소스 목록을 한 번에 가져와 메모리에서 필터링/조합/점수 계산을 수행한다.

상세 기록:

- `_worklog/checkpoints/2026-07-02-009-prototype-scaffold.md`
- `_worklog/checkpoints/2026-07-02-010-code-comment-pass.md`
- `_worklog/checkpoints/2026-07-02-011-score-calculator-readable-enum.md`
- `_worklog/checkpoints/2026-07-02-012-score-calculator-stepwise-comments.md`

## 다음 작업 후보

1. 테스트베드 `matching_candidates` DDL에 `stability_score DECIMAL(5,2) DEFAULT 0.00 COMMENT '안정성스코어'`를 `price_score` 뒤, `total_score` 앞에 추가한다.
2. `.env`를 작성하고 `prototype/requirements.txt` 의존성을 설치한다.
3. `resource_availability`의 `GUIDE` 테스트 데이터 입력 오류를 정정한다.
4. `guides/drivers`와 `partner`의 정식 연결키를 확정한다. 현재 프로토타입은 `partner_no == guides.id/drivers.id` 전제로 가용성을 매칭한다.
5. 콘솔에서 `tour_request_id`, `reserve_id`, `user_no`를 입력해 후보 생성 흐름을 실제 DB로 검증한다.
6. 검증 후 필요한 산식 보정과 설계 문서 업데이트를 진행한다.

## 주의사항

- `reference/` 폴더는 현재 Git 기준 untracked 상태로 관찰되었다. 커밋 전에 포함 여부를 사용자가 확인해야 한다.
- 현재 작업은 분석/기록 단계를 지나 Python 프로토타입 기본 구현과 주석 보강까지 완료했다.
- 실제 DB 조회 결과로 `guides`, `drivers`, `tour_requests`, `reservations`가 존재하는 것으로 확인되어 이전 체크포인트의 일부 "확인 필요" 항목은 해소되었다.
- 실제 데이터 확인 결과 `resource_availability`는 총 10건뿐이며, 그중 가이드/드라이버는 각 1건이다. 후보 생성 테스트에는 데이터가 부족할 수 있다.
- `matching_candidates` 12건은 `resv_info`와 모두 매칭된다. 결과 저장 테이블의 예약 FK는 실제 데이터 기준 정상이다.
- `resource_availability`의 `GUIDE` 행은 드라이버 파트너에 연결되어 있으므로 현재 데이터 그대로는 가이드 가용성 필터에 사용하면 안 된다.
- `tour_requests`는 7건이고 필수 스코어링 필드 누락은 0건이다. PDF 설계 기준 샘플 테스트 원천으로는 `tour_requests`가 더 적합하다.
- 운영 DB에는 테스트베드의 `guides`, `resource_availability` 테이블이 없다. 운영 적용 기준 설계를 하려면 운영 DB에서 다시 컬럼 조사를 해야 한다.
- 운영 DB `partner` 기준으로는 DRIVER/GUIDE 겸임 구조가 확인되지 않았다.
- 사용자가 `matching_candidates.stability_score` 컬럼 추가를 결정했다. 이후 설계/DDL/구현은 이 결정을 전제로 진행한다.
- 사용자가 `matching_candidates.tour_request_id` 컬럼은 추가하지 않기로 결정했다. 이후 설계/구현은 기존 `reserve_id/user_no` 저장 구조를 유지한다.
- 프로토타입 코드는 주니어 인수인계를 고려해 파일 수와 클래스를 줄였다. 계산은 `ScoreCalculator`, DB는 `MatchingStore`, 흐름은 `MatchingService`가 담당하며, 각 클래스/함수에는 입력/출력과 필요한 remark를 주석으로 남겼다. `ScoreCalculator`는 한 줄 삼항 계산을 함수로 풀고, 산식 배점/기준값은 Enum으로 정리했다. 또한 함수 인자 안에 다른 함수 호출을 넣지 않고 중간 변수로 받은 뒤 전달하도록 정리했다.
- `MatchingService`는 가이드/드라이버 가용성 매칭을 `resource_availability.partner_no == guides.id/drivers.id`로 가정한다. 이 연결키는 실제 테스트 후 확정 또는 수정이 필요하다.
- PDF는 분석 중 임시로 `tmp/pdfs/tour_matching_agent.txt`에 텍스트 추출했으나, 작업 산출물이 아니므로 정리했다.
- 다른 PC에서 이어갈 때는 `git pull` 후 `AGENT.md`, `_worklog/INDEX.md`, 이 파일 순서로 읽는다.

## Git handoff 절차

```text
git status --short
git add AGENT.md _worklog prototype reference
git commit -m "Add matching scoring prototype"
git push
```

다른 PC에서는 다음 순서로 이어간다.

```text
git pull
```

그 뒤 `AGENT.md`와 `_worklog/HANDOFF.md`를 읽고 다음 작업을 시작한다.


