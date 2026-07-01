# Matching Scoring Prototype

관광 리소스 매칭 스코어링 프로토타입입니다.

이 코드는 테스트베드 DB의 신규 테이블을 기준으로 동작합니다.

## 실행 흐름

```text
tour_requests 1건 선택
-> 가이드/차량/드라이버/가용성/예약 데이터 조회
-> 필수조건 필터링
-> 가능한 조합 생성
-> 점수 계산
-> matching_candidates 저장
-> 추천 후보 TOP 3 출력
-> 콘솔에서 후보 선택
```

## 설치

```bash
pip install -r requirements.txt
```

`.env.example`을 참고해 `.env`를 작성합니다.

## 실행

```bash
python prototype/run_console.py
```

## 현재 전제

- `matching_candidates.tour_request_id` 컬럼은 추가하지 않습니다.
- `matching_candidates.stability_score` 컬럼은 추가하는 전제입니다.
- 후보 저장은 `reserve_id`, `user_no` 기준으로 합니다.
- 가이드 가용성은 `resource_availability.resource_type='GUIDE'`와 `partner.partner_type='GUIDE'`가 모두 맞는 경우만 사용합니다.

