from __future__ import annotations

from datetime import datetime, timedelta

import pymysql
from pymysql.cursors import DictCursor

from .config import Settings
from .models import Availability, Driver, Guide, MatchingCandidate, Reservation, TourRequest, Vehicle


class MatchingStore:
    """DB에서 매칭에 필요한 데이터를 읽고 계산 결과를 저장한다.

    입력: Settings의 DB 접속 정보
    출력: dataclass 객체 목록 또는 DB 저장 결과
    remark: SQL과 DB 연결 처리는 이 클래스에 모아서 서비스/계산 코드와 분리한다.
    """

    def __init__(self, settings: Settings):
        """DB 연결을 생성한다.

        입력: DB 접속 설정
        출력: 없음
        """
        self.settings = settings
        self.connection = pymysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )

    def close(self):
        """DB 연결을 닫는다.

        입력: 없음
        출력: 없음
        """
        self.connection.close()

    def list_tour_requests(self) -> list[TourRequest]:
        """최근 투어 요청 목록을 조회한다.

        입력: 없음
        출력: TourRequest 목록, 최대 20건
        """
        sql = """
            SELECT *
            FROM tour_requests
            ORDER BY id DESC
            LIMIT 20
        """
        return [to_tour_request(row) for row in self._fetch_all(sql)]

    def get_tour_request(self, tour_request_id: int) -> TourRequest:
        """계산 대상 투어 요청 1건을 조회한다.

        입력: tour_requests.id
        출력: TourRequest
        """
        row = self._fetch_one("SELECT * FROM tour_requests WHERE id = %s", (tour_request_id,))
        if not row:
            raise ValueError(f"tour_request not found: {tour_request_id}")
        return to_tour_request(row)

    def get_guides(self) -> list[Guide]:
        """활성 상태 가이드 목록을 조회한다.

        입력: 없음
        출력: Guide 목록
        """
        rows = self._fetch_all("SELECT * FROM guides WHERE status = 'ACTIVE'")
        return [to_guide(row) for row in rows]

    def get_drivers(self) -> list[Driver]:
        """승인되고 운영 중인 드라이버 목록을 조회한다.

        입력: 없음
        출력: Driver 목록
        """
        rows = self._fetch_all(
            """
            SELECT *
            FROM drivers
            WHERE approval_status = 'APPROVED'
              AND operation_status = 'ACTIVE'
            """
        )
        return [to_driver(row) for row in rows]

    def get_vehicles(self) -> list[Vehicle]:
        """승인되고 운영 중인 차량 목록을 조회한다.

        입력: 없음
        출력: Vehicle 목록
        """
        rows = self._fetch_all(
            """
            SELECT *
            FROM vehicles
            WHERE approval_status = 'APPROVED'
              AND operation_status = 'ACTIVE'
            """
        )
        return [to_vehicle(row) for row in rows]

    def get_availabilities(self, request: TourRequest) -> list[Availability]:
        """요청 날짜에 사용 가능한 리소스 가용성 목록을 조회한다.

        입력: TourRequest
        출력: Availability 목록
        remark: GUIDE/DRIVER 가용성은 partner.partner_type까지 확인해 잘못 입력된 테스트 데이터를 걸러낸다.
        """
        rows = self._fetch_all(
            """
            SELECT ra.*
            FROM resource_availability ra
            LEFT JOIN partner p
              ON p.partner_id = ra.partner_id
             AND p.user_no = ra.partner_no
            WHERE ra.available_date = %s
              AND ra.status = 'ACTIVE'
              AND (
                    ra.resource_type = 'VEHICLE'
                    OR (ra.resource_type = 'GUIDE' AND p.partner_type = 'GUIDE')
                    OR (ra.resource_type = 'DRIVER' AND p.partner_type = 'DRIVER')
                  )
            """,
            (request.tour_date,),
        )
        return [to_availability(row) for row in rows]

    def get_reservations(self, request: TourRequest) -> list[Reservation]:
        """요청 시간과 겹치는 확정 예약을 조회한다.

        입력: TourRequest
        출력: Reservation 목록
        remark: 여기서 조회된 예약은 같은 가이드/차량/드라이버 중복 배정을 막는 데 사용한다.
        """
        rows = self._fetch_all(
            """
            SELECT *
            FROM reservations
            WHERE status IN ('CONFIRMED')
              AND start_at < %s
              AND end_at > %s
            """,
            (request.end_at, request.start_at),
        )
        return [to_reservation(row) for row in rows]

    def save_candidates(self, candidates: list[MatchingCandidate]) -> list[MatchingCandidate]:
        """계산된 후보 목록을 matching_candidates에 저장한다.

        입력: MatchingCandidate 목록
        출력: DB id가 채워진 MatchingCandidate 목록
        """
        sql = """
            INSERT INTO matching_candidates (
                reserve_id, user_no,
                guide_id, guide_no, vehicle_id, driver_id, driver_no,
                guide_score, vehicle_score, driver_score, price_score, stability_score, total_score,
                guide_price, vehicle_price, driver_price, total_price,
                rank_no, candidate_status, is_recommended, is_selected, expires_at, created_at
            )
            VALUES (
                %(reserve_id)s, %(user_no)s,
                %(guide_id)s, %(guide_no)s, %(vehicle_id)s, %(driver_id)s, %(driver_no)s,
                %(guide_score)s, %(vehicle_score)s, %(driver_score)s, %(price_score)s, %(stability_score)s, %(total_score)s,
                %(guide_price)s, %(vehicle_price)s, %(driver_price)s, %(total_price)s,
                %(rank_no)s, %(candidate_status)s, %(is_recommended)s, %(is_selected)s, %(expires_at)s, NOW()
            )
        """
        expires_at = datetime.now() + timedelta(days=1)
        with self.connection.cursor() as cursor:
            for candidate in candidates:
                data = candidate.__dict__.copy()
                data["expires_at"] = expires_at
                cursor.execute(sql, data)
                candidate.id = cursor.lastrowid
        self.connection.commit()
        return candidates

    def get_candidates(self, reserve_id: str, user_no: int) -> list[MatchingCandidate]:
        """기존 예약 식별값으로 저장된 후보 목록을 조회한다.

        입력: reserve_id, user_no
        출력: MatchingCandidate 목록
        """
        rows = self._fetch_all(
            """
            SELECT *
            FROM matching_candidates
            WHERE reserve_id = %s
              AND user_no = %s
            ORDER BY rank_no ASC
            """,
            (reserve_id, user_no),
        )
        return [to_candidate(row) for row in rows]

    def mark_candidate_selected(self, candidate_id: int):
        """후보 1건을 선택 완료 상태로 변경한다.

        입력: matching_candidates.id
        출력: 없음
        """
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE matching_candidates
                SET candidate_status = 'SELECTED',
                    is_selected = 1
                WHERE id = %s
                """,
                (candidate_id,),
            )
        self.connection.commit()

    def create_reservation_from_candidate(self, candidate_id: int):
        """선택된 후보를 기준으로 reservations에 확정 예약을 생성한다.

        입력: matching_candidates.id
        출력: 없음
        remark: matching_candidates에 tour_request_id를 저장하지 않으므로 reserve_id/user_no로 tour_request를 역추적한다.
        """
        candidate = self._fetch_one("SELECT * FROM matching_candidates WHERE id = %s", (candidate_id,))
        if not candidate:
            raise ValueError(f"candidate not found: {candidate_id}")

        request = self._fetch_one(
            """
            SELECT tr.*
            FROM tour_requests tr
            JOIN resv_info ri
              ON ri.user_no = tr.customer_id
             AND ri.region_code = tr.region_code
            WHERE ri.reserve_id = %s
              AND ri.user_no = %s
            ORDER BY tr.id DESC
            LIMIT 1
            """,
            (candidate["reserve_id"], candidate["user_no"]),
        )
        if not request:
            raise ValueError("tour_request could not be inferred from reserve_id/user_no")

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO reservations (
                    requested_id, guide_id, vehicle_id, driver_id,
                    start_at, end_at,
                    guide_price, vehicle_price, driver_price, total_price,
                    status, matching_candidate_id, create_dt
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'CONFIRMED', %s, NOW())
                """,
                (
                    request["id"],
                    to_int_or_none(candidate["guide_id"]),
                    candidate["vehicle_id"],
                    to_int_or_none(candidate["driver_id"]),
                    request["start_at"],
                    request["end_at"],
                    candidate["guide_price"],
                    candidate["vehicle_price"],
                    candidate["driver_price"],
                    candidate["total_price"],
                    candidate_id,
                ),
            )
        self.connection.commit()

    def _fetch_one(self, sql: str, params=None):
        """단일 행을 dict 형태로 조회한다."""
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def _fetch_all(self, sql: str, params=None):
        """여러 행을 dict 목록 형태로 조회한다."""
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def to_tour_request(row) -> TourRequest:
    """tour_requests 조회 행을 TourRequest 객체로 변환한다."""
    return TourRequest(
        id=row["id"],
        customer_id=row["customer_id"],
        status=row["status"],
        tour_date=row["tour_date"],
        start_at=row["start_at"],
        end_at=row["end_at"],
        region_code=row["region_code"],
        group_size=row["group_size"],
        luggage_count=row["luggage_count"],
        guide_required=bool(row["guide_required"]),
        requested_language=row["requested_language"],
        vehicle_required=bool(row["vehicle_required"]),
        requested_vehicle_type=row["requested_vehicle_type"],
        driver_required=bool(row["driver_required"]),
        requested_theme=row["requested_theme"],
        budget_max=row["budget_max"],
    )


def to_guide(row) -> Guide:
    """guides 조회 행을 Guide 객체로 변환한다."""
    return Guide(
        id=row["id"],
        name=row["name"],
        status=row["status"],
        base_region_code=row["base_region_code"],
        languages=row["languages"] or "",
        themes=row["themes"] or "",
        region_level=row["region_level"] or 0,
        price_per_day=row["price_per_day"] or 0,
        price_per_hour=row["price_per_hour"] or 0,
        rating_avg=row["rating_avg"] or 0,
        review_count=row["review_count"] or 0,
        response_rate=row["response_rate"] or 0,
        avg_response_minutes=row["avg_response_minutes"] or 0,
        cancel_count=row["cancel_count"] or 0,
        no_show_count=row["no_show_count"] or 0,
        complaint_count=row["complaint_count"] or 0,
    )


def to_driver(row) -> Driver:
    """drivers 조회 행을 Driver 객체로 변환한다."""
    return Driver(
        id=row["id"],
        name=row["name"],
        approval_status=row["approval_status"],
        operation_status=row["operation_status"],
        base_region_code=row["base_region_code"],
        vehicle_types=row["vehicle_types"] or "",
        languages=row["languages"] or "",
        regions=row["regions"] or "",
        price_per_day=row["price_per_day"] or 0,
        price_per_hour=row["price_per_hour"] or 0,
        rating_avg=row["rating_avg"] or 0,
        review_count=row["review_count"] or 0,
        response_rate=row["response_rate"] or 0,
        avg_response_minutes=row["avg_response_minutes"] or 0,
        cancel_count=row["cancel_count"] or 0,
        no_show_count=row["no_show_count"] or 0,
        complaint_count=row["complaint_count"] or 0,
    )


def to_vehicle(row) -> Vehicle:
    """vehicles 조회 행을 Vehicle 객체로 변환한다."""
    return Vehicle(
        id=row["id"],
        vehicle_name=row["vehicle_name"],
        vehicle_type=row["vehicle_type"],
        approval_status=row["approval_status"],
        operation_status=row["operation_status"],
        base_region_code=row["base_region_code"],
        seat_count=row["seat_count"] or 0,
        luggage_capacity=row["luggage_capacity"] or 0,
        model_name=row["model_name"],
        model_year=row["model_year"],
        is_premium=bool(row["is_premium"]),
        has_child_seat=bool(row["has_child_seat"]),
        price_per_day=row["price_per_day"] or 0,
        price_per_hour=row["price_per_hour"] or 0,
        rating_avg=row["rating_avg"] or 0,
        review_count=row["review_count"] or 0,
        avg_response_minutes=row["avg_response_minutes"] or 0,
        cancel_count=row["cancel_count"] or 0,
        no_show_count=row["no_show_count"] or 0,
        complaint_count=row["complaint_count"] or 0,
    )


def to_availability(row) -> Availability:
    """resource_availability 조회 행을 Availability 객체로 변환한다."""
    return Availability(
        id=row["id"],
        resource_type=row["resource_type"],
        vehicle_id=row["vehicle_id"],
        partner_id=row["partner_id"],
        partner_no=row["partner_no"],
        available_date=row["available_date"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        status=row["status"],
    )


def to_reservation(row) -> Reservation:
    """reservations 조회 행을 Reservation 객체로 변환한다."""
    return Reservation(
        id=row["id"],
        requested_id=row["requested_id"],
        guide_id=row["guide_id"],
        vehicle_id=row["vehicle_id"],
        driver_id=row["driver_id"],
        start_at=row["start_at"],
        end_at=row["end_at"],
        status=row["status"],
        matching_candidate_id=row["matching_candidate_id"],
    )


def to_candidate(row) -> MatchingCandidate:
    """matching_candidates 조회 행을 MatchingCandidate 객체로 변환한다."""
    return MatchingCandidate(
        id=row["id"],
        reserve_id=row["reserve_id"],
        user_no=row["user_no"],
        guide_id=row["guide_id"],
        guide_no=row["guide_no"],
        vehicle_id=row["vehicle_id"],
        driver_id=row["driver_id"],
        driver_no=row["driver_no"],
        guide_score=float(row["guide_score"] or 0),
        vehicle_score=float(row["vehicle_score"] or 0),
        driver_score=float(row["driver_score"] or 0),
        price_score=float(row["price_score"] or 0),
        stability_score=float(row.get("stability_score") or 0),
        total_score=float(row["total_score"] or 0),
        guide_price=row["guide_price"] or 0,
        vehicle_price=row["vehicle_price"] or 0,
        driver_price=row["driver_price"] or 0,
        total_price=row["total_price"] or 0,
        rank_no=row["rank_no"] or 0,
        candidate_status=row["candidate_status"],
        is_recommended=bool(row["is_recommended"]),
        is_selected=bool(row["is_selected"]),
    )


def to_int_or_none(value):
    """문자열/숫자 값을 int로 바꾸고, 실패하면 None을 반환한다."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
