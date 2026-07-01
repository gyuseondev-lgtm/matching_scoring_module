from __future__ import annotations

from .config import Settings
from .models import Availability, Driver, Guide, MatchingCandidate, Reservation, TourRequest, Vehicle
from .score_calculator import ScoreCalculator, contains_code
from .store import MatchingStore


class MatchingService:
    """매칭 후보 생성, 점수 계산, 저장, 선택 처리를 묶어서 실행한다.

    입력: MatchingStore, ScoreCalculator, Settings
    출력: public 메서드를 통해 후보 목록을 저장하거나 선택 상태를 변경한다.
    remark: 리소스 수가 작다는 전제로 DB에서 목록을 한 번에 읽고 메모리에서 조합한다.
    """

    def __init__(self, store: MatchingStore, calculator: ScoreCalculator, settings: Settings):
        """서비스 실행에 필요한 저장소, 계산기, 설정을 보관한다.

        입력: DB 저장소, 점수 계산기, 실행 설정
        출력: 없음
        """
        self.store = store
        self.calculator = calculator
        self.settings = settings

    def generate_candidates(self, tour_request_id: int, reserve_id: str, user_no: int) -> list[MatchingCandidate]:
        """투어 요청 1건에 대해 가능한 후보 조합을 생성하고 저장한다.

        입력: tour_requests.id, 기존 예약 reserve_id, 사용자 user_no
        출력: 저장된 MatchingCandidate 목록
        remark: matching_candidates에는 tour_request_id를 저장하지 않기로 했기 때문에 reserve_id/user_no를 함께 받는다.
        """
        request = self.store.get_tour_request(tour_request_id)
        guides = self.store.get_guides()
        drivers = self.store.get_drivers()
        vehicles = self.store.get_vehicles()
        availabilities = self.store.get_availabilities(request)
        reservations = self.store.get_reservations(request)

        guides = [guide for guide in guides if self._guide_passes(request, guide, availabilities, reservations)]
        vehicles = [vehicle for vehicle in vehicles if self._vehicle_passes(request, vehicle, availabilities, reservations)]

        candidates = []
        for guide in guides:
            for vehicle in vehicles:
                eligible_drivers = [
                    driver
                    for driver in drivers
                    if self._driver_passes(request, driver, vehicle, availabilities, reservations)
                ]
                for driver in eligible_drivers:
                    candidates.append(self._build_candidate(request, reserve_id, user_no, guide, vehicle, driver))

        ranked = self._rank_candidates(candidates)
        return self.store.save_candidates(ranked[: self.settings.max_saved_candidates])

    def select_candidate(self, candidate_id: int, create_reservation: bool = False):
        """후보 1건을 최종 선택 상태로 변경한다.

        입력: matching_candidates.id, reservations 확정 저장 여부
        출력: 없음
        remark: create_reservation=True일 때만 reservations에 확정 예약을 만든다.
        """
        self.store.mark_candidate_selected(candidate_id)
        if create_reservation:
            self.store.create_reservation_from_candidate(candidate_id)

    def _build_candidate(
        self,
        request: TourRequest,
        reserve_id: str,
        user_no: int,
        guide: Guide,
        vehicle: Vehicle,
        driver: Driver,
    ) -> MatchingCandidate:
        """가이드/차량/드라이버 1개 조합을 MatchingCandidate 객체로 만든다.

        입력: 투어 요청, 예약 식별값, 사용자 식별값, 리소스 조합
        출력: 아직 DB에 저장되지 않은 MatchingCandidate
        """
        guide_score = self.calculator.guide_score(request, guide)
        vehicle_score = self.calculator.vehicle_score(request, vehicle)
        driver_score = self.calculator.driver_score(request, driver, vehicle)

        guide_price = guide.price_per_day
        vehicle_price = vehicle.price_per_day
        driver_price = driver.price_per_day
        total_price = guide_price + vehicle_price + driver_price

        price_score = self.calculator.price_score(total_price, request.budget_max)
        stability_score = self.calculator.stability_score(guide, driver, vehicle)
        total_score = self.calculator.total_score(
            guide_score,
            vehicle_score,
            driver_score,
            price_score,
            stability_score,
        )

        return MatchingCandidate(
            reserve_id=reserve_id,
            user_no=user_no,
            guide_id=str(guide.id),
            guide_no=None,
            vehicle_id=vehicle.id,
            driver_id=str(driver.id),
            driver_no=None,
            guide_score=round(guide_score, 2),
            vehicle_score=round(vehicle_score, 2),
            driver_score=round(driver_score, 2),
            price_score=round(price_score, 2),
            stability_score=round(stability_score, 2),
            total_score=total_score,
            guide_price=guide_price,
            vehicle_price=vehicle_price,
            driver_price=driver_price,
            total_price=total_price,
        )

    def _rank_candidates(self, candidates: list[MatchingCandidate]) -> list[MatchingCandidate]:
        """후보를 최종 점수 기준으로 정렬하고 추천 표시를 붙인다.

        입력: 저장 전 후보 목록
        출력: rank_no와 is_recommended가 채워진 후보 목록
        """
        candidates.sort(key=lambda c: (-c.total_score, -c.price_score, c.total_price))
        for index, candidate in enumerate(candidates, start=1):
            candidate.rank_no = index
            candidate.is_recommended = index <= self.settings.recommend_count
        return candidates

    def _guide_passes(
        self,
        request: TourRequest,
        guide: Guide,
        availabilities: list[Availability],
        reservations: list[Reservation],
    ) -> bool:
        """가이드가 필수 조건, 가용 시간, 예약 충돌 조건을 통과하는지 확인한다."""
        if request.guide_required and not contains_code(guide.languages, request.requested_language):
            return False
        if not self._has_partner_availability("GUIDE", guide.id, request, availabilities):
            return False
        return not self._has_reservation_conflict(guide_id=guide.id, reservations=reservations)

    def _vehicle_passes(
        self,
        request: TourRequest,
        vehicle: Vehicle,
        availabilities: list[Availability],
        reservations: list[Reservation],
    ) -> bool:
        """차량이 인원, 수하물, 차종, 가용 시간, 예약 충돌 조건을 통과하는지 확인한다."""
        if vehicle.seat_count < request.group_size:
            return False
        if vehicle.luggage_capacity < request.luggage_count:
            return False
        if request.requested_vehicle_type and vehicle.vehicle_type != request.requested_vehicle_type:
            return False
        if not self._has_vehicle_availability(vehicle.id, request, availabilities):
            return False
        return not self._has_reservation_conflict(vehicle_id=vehicle.id, reservations=reservations)

    def _driver_passes(
        self,
        request: TourRequest,
        driver: Driver,
        vehicle: Vehicle,
        availabilities: list[Availability],
        reservations: list[Reservation],
    ) -> bool:
        """드라이버가 차량 운전 가능 여부, 가용 시간, 예약 충돌 조건을 통과하는지 확인한다."""
        if not contains_code(driver.vehicle_types, vehicle.vehicle_type):
            return False
        if not self._has_partner_availability("DRIVER", driver.id, request, availabilities):
            return False
        return not self._has_reservation_conflict(driver_id=driver.id, reservations=reservations)

    def _has_vehicle_availability(
        self,
        vehicle_id: int,
        request: TourRequest,
        availabilities: list[Availability],
    ) -> bool:
        """차량 ID에 맞는 가용성 행이 요청 시간을 포함하는지 확인한다."""
        for availability in availabilities:
            if availability.resource_type != "VEHICLE" or availability.vehicle_id != vehicle_id:
                continue
            if self._covers_request_time(availability, request):
                return True
        return False

    def _has_partner_availability(
        self,
        resource_type: str,
        resource_id: int,
        request: TourRequest,
        availabilities: list[Availability],
    ) -> bool:
        """가이드/드라이버 ID에 맞는 가용성 행이 요청 시간을 포함하는지 확인한다.

        remark: 현재 테스트베드는 guides/drivers.id와 resource_availability.partner_no가 연결된다는 전제로 동작한다.
        """
        for availability in availabilities:
            if availability.resource_type != resource_type:
                continue
            # 테스트베드의 가이드/드라이버 테이블은 bigint id이고, 가용성은 partner_no를 쓴다.
            if availability.partner_no != resource_id:
                continue
            if self._covers_request_time(availability, request):
                return True
        return False

    def _covers_request_time(self, availability: Availability, request: TourRequest) -> bool:
        """가용 시작/종료 시간이 요청 시작/종료 시간을 모두 포함하는지 확인한다."""
        return availability.start_time <= request.start_at.time() and availability.end_time >= request.end_at.time()

    def _has_reservation_conflict(
        self,
        reservations: list[Reservation],
        guide_id: int | None = None,
        vehicle_id: int | None = None,
        driver_id: int | None = None,
    ) -> bool:
        """이미 확정된 예약과 같은 가이드/차량/드라이버가 겹치는지 확인한다.

        입력: 시간대가 겹치는 예약 목록과 확인할 리소스 ID
        출력: 충돌 여부(bool)
        """
        for reservation in reservations:
            if guide_id is not None and reservation.guide_id == guide_id:
                return True
            if vehicle_id is not None and reservation.vehicle_id == vehicle_id:
                return True
            if driver_id is not None and reservation.driver_id == driver_id:
                return True
        return False
