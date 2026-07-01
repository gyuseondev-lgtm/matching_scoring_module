# Worklog Index

이 파일은 저장소 작업기록의 진입점이다. Codex 또는 개발자가 작업을 재개할 때는 `AGENT.md`를 먼저 읽고, 그 다음 이 파일과 `HANDOFF.md`를 확인한다.

## 운영 규칙

- 체크포인트 상세 기록은 `_worklog/checkpoints/`에 작성한다.
- 새 체크포인트를 만들면 이 인덱스에 링크, 날짜, 목적, 현재 상태를 추가한다.
- 다른 PC로 넘기기 전에는 `HANDOFF.md`를 최신 상태로 갱신한다.
- 작업기록은 GitHub push/pull로 이동 가능한 정보만 담는다. 로컬 절대경로, 개인 IDE 상태, 대화창 기억에만 의존하지 않는다.

## 현재 체크포인트

| 날짜 | 체크포인트 | 목적 | 상태 |
| --- | --- | --- | --- |
| 2026-07-02 | [2026-07-02-001-worklog-environment-setup.md](checkpoints/2026-07-02-001-worklog-environment-setup.md) | 작업기록 및 handoff 환경 구성 | 완료 |
| 2026-07-02 | [2026-07-02-002-scoring-module-analysis.md](checkpoints/2026-07-02-002-scoring-module-analysis.md) | 스코어링 로직 관련 자료 분석 및 모듈 설계 방향 기록 | 완료 |
| 2026-07-02 | [2026-07-02-003-db-table-verification.md](checkpoints/2026-07-02-003-db-table-verification.md) | 실제 DB 컬럼 조회 결과 기반 테이블 존재 및 스코어링 데이터 매핑 확인 | 완료 |
| 2026-07-02 | [2026-07-02-004-db-data-quality-check.md](checkpoints/2026-07-02-004-db-data-quality-check.md) | 실제 데이터 건수, 필수값 품질, 상태값, 연결키 검증 결과 기록 | 완료 |
| 2026-07-02 | [2026-07-02-005-db-linkage-followup.md](checkpoints/2026-07-02-005-db-linkage-followup.md) | 가이드 가용성 이상 데이터와 matching_candidates-resv_info 연결 재확인 | 완료 |
| 2026-07-02 | [2026-07-02-006-prod-db-structure-gap.md](checkpoints/2026-07-02-006-prod-db-structure-gap.md) | 운영 DB와 테스트베드 DB 구조 차이 및 겸임 가능성 확인 결과 기록 | 완료 |
| 2026-07-02 | [2026-07-02-007-stability-score-column-decision.md](checkpoints/2026-07-02-007-stability-score-column-decision.md) | `matching_candidates.stability_score` 컬럼 추가 결정과 사유 기록 | 완료 |
| 2026-07-02 | [2026-07-02-008-no-tour-request-id-column.md](checkpoints/2026-07-02-008-no-tour-request-id-column.md) | `matching_candidates.tour_request_id` 컬럼은 추가하지 않기로 결정 | 완료 |
| 2026-07-02 | [2026-07-02-009-prototype-scaffold.md](checkpoints/2026-07-02-009-prototype-scaffold.md) | 단순 Python 프로토타입 구조와 기본 코드 작성 | 완료 |
| 2026-07-02 | [2026-07-02-010-code-comment-pass.md](checkpoints/2026-07-02-010-code-comment-pass.md) | 프로토타입 코드 클래스/함수 주석 보강 | 완료 |
| 2026-07-02 | [2026-07-02-011-score-calculator-readable-enum.md](checkpoints/2026-07-02-011-score-calculator-readable-enum.md) | 점수 계산 코드 가독성 개선 및 Enum 정리 | 완료 |
| 2026-07-02 | [2026-07-02-012-score-calculator-stepwise-comments.md](checkpoints/2026-07-02-012-score-calculator-stepwise-comments.md) | 함수 호출 단계 분리 및 중간 변수 주석 보강 | 완료 |

## 저장소 주요 문서

| 경로 | 역할 |
| --- | --- |
| `AGENT.md` | 저장소 작업 원칙과 worklog 운영 규칙 |
| `_worklog/HANDOFF.md` | 다른 PC 또는 다음 세션으로 넘길 현재 작업 상태 |
| `reference/스코어링 로직작성.md` | 스코어링 로직 작성 관련 현재 활성 참고 문서 |
| `reference/erd_수정본_20260624.mdj` | ERD 수정본 참고 파일 |
| `reference/블랙버드TB_DB_수정본_20260624.txt` | DB 구조 참고 파일 |
| `reference/관광리소스 매칭 AI Agent.pdf` | 관광리소스 매칭 AI Agent 참고 자료 |

## 다음에 먼저 볼 파일

1. `AGENT.md`
2. `_worklog/INDEX.md`
3. `_worklog/HANDOFF.md`
4. 최신 체크포인트: `_worklog/checkpoints/2026-07-02-012-score-calculator-stepwise-comments.md`


