# Checkpoint 2026-07-02-006: Production DB Structure Gap

## 목적

운영 DB에서 가이드/드라이버 겸임 가능성과 테스트베드에서 확인한 신규 테이블 존재 여부를 확인한 결과를 기록한다.

## 사용자 확인 결과

운영 DB에서 다음 쿼리 계열을 실행했다.

1. `partner`에서 같은 `user_no`가 여러 `partner_type`을 가지는지 확인
2. `partner`에서 같은 `partner_id`가 여러 `partner_type`을 가지는지 확인
3. DRIVER와 GUIDE를 동시에 가진 사용자 상세 확인
4. `guides` / `drivers`와 `partner` 연결 확인
5. `resource_availability`와 `partner` 연결 확인

결과:

| 확인 항목 | 운영 DB 결과 | 판단 |
| --- | --- | --- |
| 같은 `user_no`가 여러 `partner_type` 보유 | 레코드 없음 | 한 사용자가 복수 역할을 갖는 구조는 확인되지 않음 |
| 같은 `partner_id`가 여러 `partner_type` 보유 | 레코드 없음 | 한 파트너 ID가 복수 역할을 갖는 구조는 확인되지 않음 |
| DRIVER와 GUIDE를 동시에 가진 사용자 | 레코드 없음 | 운영 DB 기준 겸임 구조 없음 |
| `blackbird.guides` | SQL 1146, table does not exist | 운영 DB에는 테스트베드 `guides` 테이블 없음 |
| `blackbird.resource_availability` | SQL 1146, table does not exist | 운영 DB에는 테스트베드 `resource_availability` 테이블 없음 |

## 핵심 결론

운영 DB는 테스트베드에서 확인한 스코어링 신규 스키마와 구조가 다르다.

따라서 테스트베드에서 확인한 다음 테이블을 운영 DB 기준으로 바로 전제하면 안 된다.

- `guides`
- `resource_availability`
- 추가로 `drivers`, `vehicles`, `tour_requests`, `reservations`, `matching_candidates`도 운영 DB 존재 여부를 별도로 확인해야 한다.

운영 DB의 `partner`만 기준으로 보면 DRIVER/GUIDE 겸임은 확인되지 않았다. 따라서 테스트베드의 `resource_availability.resource_type='GUIDE'`가 `partner_type='DRIVER'`로 연결된 건 겸임 가능성보다는 테스트베드 데이터 오류 또는 테스트베드 스키마/데이터 혼재로 보는 편이 타당하다.

## 설계 영향

현재는 두 가지 설계 기준 중 하나를 선택해야 한다.

### 선택지 A: 테스트베드 신규 스키마 기준 구현

전제:

- `tour_requests`
- `guides`
- `drivers`
- `vehicles`
- `resource_availability`
- `reservations`
- `matching_candidates`

장점:

- PDF 설계와 가장 잘 맞는다.
- 스코어링에 필요한 필드가 명확하다.

단점:

- 운영 DB에는 일부 테이블이 없으므로 운영 적용 전 마이그레이션/DDL 반영이 필요하다.

### 선택지 B: 운영 DB 현재 스키마 기준 구현

전제:

- `partner`
- `resv_info`
- 기존 운영 테이블

장점:

- 운영 DB에 바로 붙일 가능성이 높다.

단점:

- PDF의 `tour_requests/guides/drivers/resource_availability` 기준 설계를 그대로 쓸 수 없다.
- 가이드/드라이버 점수에 필요한 필드가 운영 DB 어디에 있는지 재조사해야 한다.

## 다음 확인 쿼리

운영 DB에서 테스트베드 신규 테이블 존재 여부를 한 번에 확인한다.

```sql
SELECT
    x.expected_table,
    CASE
        WHEN t.table_name IS NOT NULL THEN 'EXISTS'
        ELSE 'MISSING'
    END AS status
FROM (
    SELECT 'tour_requests' AS expected_table
    UNION ALL SELECT 'guides'
    UNION ALL SELECT 'drivers'
    UNION ALL SELECT 'vehicles'
    UNION ALL SELECT 'resource_availability'
    UNION ALL SELECT 'matching_candidates'
    UNION ALL SELECT 'reservations'
    UNION ALL SELECT 'resv_info'
    UNION ALL SELECT 'partner'
    UNION ALL SELECT 'syscode'
    UNION ALL SELECT 'platform_region'
) x
LEFT JOIN information_schema.tables t
    ON t.table_schema = 'blackbird'
   AND t.table_name = x.expected_table
ORDER BY x.expected_table;
```

운영 DB의 가이드/드라이버 관련 컬럼을 `partner`에서 먼저 확인한다.

```sql
SELECT
    column_name,
    column_type,
    is_nullable,
    column_comment
FROM information_schema.columns
WHERE table_schema = 'blackbird'
  AND table_name = 'partner'
  AND (
      column_name LIKE '%guide%'
      OR column_name LIKE '%driver%'
      OR column_name LIKE '%license%'
      OR column_name LIKE '%region%'
      OR column_name LIKE '%lang%'
      OR column_name LIKE '%review%'
      OR column_name LIKE '%score%'
      OR column_name LIKE '%offer%'
  )
ORDER BY ordinal_position;
```

## 현재 결론

운영 DB 기준으로는 가이드와 드라이버를 동시에 수행하는 파트너 구조가 확인되지 않았다. 또한 테스트베드의 핵심 신규 테이블 일부가 운영 DB에 없다.

따라서 다음 단계는 점수 산식 구현이 아니라, "운영 DB 현재 스키마에 맞춰 구현할 것인지" 또는 "테스트베드 신규 스키마를 운영에 반영한 뒤 구현할 것인지"를 결정하는 것이다.

