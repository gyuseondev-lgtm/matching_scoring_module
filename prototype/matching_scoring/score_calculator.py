from __future__ import annotations

from enum import Enum, IntEnum

from .config import Settings
from .models import Driver, Guide, TourRequest, Vehicle


class ScoreRange(IntEnum):
    """공통 점수 범위."""

    MIN = 0
    MAX = 100


class BinaryScore(IntEnum):
    """가능/불가능처럼 단순 판정하는 항목의 원점수."""

    MATCH = 100
    NO_MATCH = 0


class GuideScore(IntEnum):
    """가이드 점수 항목별 배점."""

    LANGUAGE = 25
    REGION = 20
    THEME = 15
    RATING_REVIEW = 15
    ASSIGNMENT_BALANCE = 10
    PRICE = 10
    RELIABILITY = 5


class VehicleScore(IntEnum):
    """차량 점수 항목별 배점."""

    TYPE_MATCH = 20
    TYPE_MISMATCH = 5
    SEAT_ENOUGH_3_OR_MORE = 25
    SEAT_ENOUGH_2 = 20
    SEAT_ENOUGH_1 = 15
    SEAT_EXACT = 10
    LUGGAGE_ENOUGH_3_OR_MORE = 20
    LUGGAGE_ENOUGH_2 = 16
    LUGGAGE_ENOUGH_1 = 12
    LUGGAGE_EXACT = 8
    REGION_MATCH = 10
    REGION_MISMATCH = 3
    QUALITY = 15
    QUALITY_RATING = 8
    QUALITY_REVIEW = 4
    QUALITY_PREMIUM = 2
    QUALITY_BASE = 1


class DriverScore(IntEnum):
    """드라이버 점수 항목별 배점."""

    CAN_DRIVE = 20
    CANNOT_DRIVE = 0
    REGION_MATCH = 25
    REGION_MISMATCH = 10
    LANGUAGE = 10
    RATING_REVIEW = 15
    RELIABILITY = 15
    PRICE_MULTIPLIER = 15


class PriceScore(IntEnum):
    """가격 적합도 점수."""

    NO_BUDGET = 70
    VERY_GOOD = 100
    GOOD = 80
    OVER_10_PERCENT = 50
    OVER_20_PERCENT = 30
    TOO_EXPENSIVE = 0


class SmallPriceScore(IntEnum):
    """개별 리소스 가격 보조 점수."""

    NO_BUDGET = 7
    VERY_GOOD = 10
    GOOD = 8
    OVER_10_PERCENT = 5
    OVER_20_PERCENT = 2
    TOO_EXPENSIVE = 0


class StabilityScore(IntEnum):
    """안정성 점수 계산에 사용하는 값."""

    BASE = 80
    NO_CANCEL_BONUS = 5
    COMPLAINT_LIMIT = 3
    COMPLAINT_PENALTY = 10


class ReviewScore(IntEnum):
    """평점/리뷰 계산에 사용하는 값."""

    MAX_RATING = 5
    REVIEW_BONUS = 5
    FULL_REVIEW_COUNT = 30


class CountValue(IntEnum):
    """개수 비교에 사용하는 기준값."""

    ZERO = 0
    FOUR = 4


class PenaltyValue(IntEnum):
    """감점 계산에 사용하는 정수값."""

    NO_SHOW = 2


class CapacityRemaining(IntEnum):
    """좌석/수하물 여유 개수 기준."""

    THREE_OR_MORE = 3
    TWO = 2
    ONE = 1
    EXACT = 0


class ScoreRatio(Enum):
    """비율 계산에 사용하는 값."""

    BUDGET_GOOD = 0.8
    BUDGET_OVER_10_PERCENT = 1.1
    BUDGET_OVER_20_PERCENT = 1.2
    COMPLAINT_PENALTY_UNIT = 0.5


DRIVER_PRICE_SCORE_RATIO = DriverScore.PRICE_MULTIPLIER / GuideScore.PRICE


class ScoreCalculator:
    """매칭 후보의 세부 점수와 최종 점수를 계산한다.

    입력: DB에서 읽어 온 TourRequest, Guide, Vehicle, Driver 객체
    출력: 각 항목별 점수(float)와 가중 합산된 최종 점수(float)
    remark: 이 클래스는 DB를 읽거나 저장하지 않고, 전달받은 값만 계산한다.
    """

    def __init__(self, settings: Settings):
        """점수 가중치 설정을 보관한다.

        입력: Settings
        출력: 없음
        """
        self.settings = settings

    def guide_score(self, request: TourRequest, guide: Guide) -> float:
        """요청 조건에 대한 가이드 적합도를 계산한다.

        입력: 투어 요청 1건, 가이드 1명
        출력: 0~100 사이의 가이드 점수
        remark: 최근 배정 횟수 데이터가 붙기 전까지는 배정 균형 점수를 기본값으로 둔다.
        """
        # 요청 언어와 가이드 보유 언어를 비교한 언어 점수다.
        language = self._guide_language_score(request, guide)

        # 가이드 지역 숙련도를 가이드 지역 배점으로 환산한 점수다.
        region = self._level_score(guide.region_level, GuideScore.REGION)

        # 요청 테마를 가이드가 지원하는지 확인한 테마 점수다.
        theme = self._guide_theme_score(request, guide)

        # 가이드 평점과 리뷰 수를 함께 반영한 점수다.
        rating = self._rating_review_score(guide.rating_avg, guide.review_count, GuideScore.RATING_REVIEW)

        assignment_balance = GuideScore.ASSIGNMENT_BALANCE

        # 가이드 가격이 요청 예산에 얼마나 맞는지 계산한 점수다.
        price = self.small_price_score(guide.price_per_day, request.budget_max)

        # 가이드 취소, 노쇼, 컴플레인 이력을 반영한 신뢰도 점수다.
        reliability = self._small_reliability_score(
            guide.cancel_count,
            guide.no_show_count,
            guide.complaint_count,
            max_score=GuideScore.RELIABILITY,
        )

        total = language + region + theme + rating + assignment_balance + price + reliability

        # 가이드 총점을 0~100 범위 안으로 제한한 값이다.
        guide_total_score = clamp(total, ScoreRange.MIN, ScoreRange.MAX)
        return guide_total_score

    def vehicle_score(self, request: TourRequest, vehicle: Vehicle) -> float:
        """요청 조건에 대한 차량 적합도를 계산한다.

        입력: 투어 요청 1건, 차량 1대
        출력: 0~100 사이의 차량 점수
        """
        # 요청 차종과 차량 차종의 일치 여부 점수다.
        type_score = self._vehicle_type_score(request.requested_vehicle_type, vehicle.vehicle_type)

        # 요청 인원을 태운 뒤 남는 좌석 여유 점수다.
        seat_score = self._vehicle_seat_score(vehicle.seat_count, request.group_size)

        # 요청 수하물을 실은 뒤 남는 적재 여유 점수다.
        luggage_score = self._vehicle_luggage_score(vehicle.luggage_capacity, request.luggage_count)

        # 요청 지역과 차량 주 활동 지역의 일치 점수다.
        region_score = self._vehicle_region_score(request, vehicle)

        # 차량 평점, 리뷰, 프리미엄 여부를 반영한 품질 점수다.
        quality = self._vehicle_quality_score(vehicle)

        # 차량 가격이 요청 예산에 얼마나 맞는지 계산한 점수다.
        price = self.small_price_score(vehicle.price_per_day, request.budget_max)

        total = type_score + seat_score + luggage_score + region_score + quality + price

        # 차량 총점을 0~100 범위 안으로 제한한 값이다.
        vehicle_total_score = clamp(total, ScoreRange.MIN, ScoreRange.MAX)
        return vehicle_total_score

    def driver_score(self, request: TourRequest, driver: Driver, vehicle: Vehicle) -> float:
        """요청 및 차량에 대한 드라이버 적합도를 계산한다.

        입력: 투어 요청 1건, 드라이버 1명, 함께 배정할 차량 1대
        출력: 0~100 사이의 드라이버 점수
        """
        # 드라이버가 후보 차량 타입을 운전할 수 있는지 계산한 점수다.
        can_drive = self._driver_vehicle_score(driver, vehicle)

        # 요청 지역과 드라이버 운행 가능 지역의 적합도 점수다.
        region = self._driver_region_score(request, driver)

        # 요청 언어와 드라이버 보유 언어를 비교한 언어 점수다.
        language = self._driver_language_score(request, driver)

        # 드라이버 평점과 리뷰 수를 함께 반영한 점수다.
        rating = self._rating_review_score(driver.rating_avg, driver.review_count, DriverScore.RATING_REVIEW)

        # 드라이버 취소, 노쇼, 컴플레인 이력을 반영한 신뢰도 점수다.
        reliability = self._small_reliability_score(
            driver.cancel_count,
            driver.no_show_count,
            driver.complaint_count,
            max_score=DriverScore.RELIABILITY,
        )

        # 드라이버 가격이 요청 예산에 얼마나 맞는지 계산한 점수다.
        price = self.driver_price_score(driver.price_per_day, request.budget_max)

        total = can_drive + region + language + rating + reliability + price

        # 드라이버 총점을 0~100 범위 안으로 제한한 값이다.
        driver_total_score = clamp(total, ScoreRange.MIN, ScoreRange.MAX)
        return driver_total_score

    def price_score(self, total_price: int, budget_max: int) -> float:
        """총 견적이 예산에 얼마나 맞는지 계산한다.

        입력: 가이드/차량/드라이버 총 가격, 요청 예산 상한
        출력: 0~100 사이의 가격 점수
        """
        if not budget_max:
            return PriceScore.NO_BUDGET

        if total_price <= budget_max * ScoreRatio.BUDGET_GOOD.value:
            return PriceScore.VERY_GOOD

        if total_price <= budget_max:
            return PriceScore.GOOD

        if total_price <= budget_max * ScoreRatio.BUDGET_OVER_10_PERCENT.value:
            return PriceScore.OVER_10_PERCENT

        if total_price <= budget_max * ScoreRatio.BUDGET_OVER_20_PERCENT.value:
            return PriceScore.OVER_20_PERCENT

        return PriceScore.TOO_EXPENSIVE

    def stability_score(self, guide: Guide, driver: Driver, vehicle: Vehicle) -> float:
        """선택 후 취소/문제 발생 가능성을 낮추기 위한 안정성 점수를 계산한다.

        입력: 후보 조합에 포함된 가이드, 드라이버, 차량
        출력: 0~100 사이의 안정성 점수
        remark: 차량 고장 이력 컬럼은 아직 없어서 차량은 컴플레인 수만 반영한다.
        """
        score = StabilityScore.BASE

        if guide.cancel_count == CountValue.ZERO:
            score += StabilityScore.NO_CANCEL_BONUS

        if driver.cancel_count == CountValue.ZERO:
            score += StabilityScore.NO_CANCEL_BONUS

        if guide.complaint_count > StabilityScore.COMPLAINT_LIMIT:
            score -= StabilityScore.COMPLAINT_PENALTY

        if driver.complaint_count > StabilityScore.COMPLAINT_LIMIT:
            score -= StabilityScore.COMPLAINT_PENALTY

        # 차량 고장 이력 컬럼이 아직 없어서 차량은 클레임만 반영한다.
        if vehicle.complaint_count > StabilityScore.COMPLAINT_LIMIT:
            score -= StabilityScore.COMPLAINT_PENALTY

        # 안정성 점수를 0~100 범위 안으로 제한한 값이다.
        stability_total_score = clamp(score, ScoreRange.MIN, ScoreRange.MAX)
        return stability_total_score

    def total_score(
        self,
        guide_score: float,
        vehicle_score: float,
        driver_score: float,
        price_score: float,
        stability_score: float,
    ) -> float:
        """항목별 점수에 설정 가중치를 적용해 최종 점수를 계산한다.

        입력: 가이드, 차량, 드라이버, 가격, 안정성 점수
        출력: 소수점 2자리로 반올림한 최종 점수
        """
        weighted_score = (
            guide_score * self.settings.guide_weight
            + vehicle_score * self.settings.vehicle_weight
            + driver_score * self.settings.driver_weight
            + price_score * self.settings.price_weight
            + stability_score * self.settings.stability_weight
        )

        # 최종 가중 점수를 소수점 2자리로 반올림한 값이다.
        rounded_total_score = round(weighted_score, 2)
        return rounded_total_score

    def small_price_score(self, price: int, budget_max: int) -> float:
        """개별 리소스 가격에 대한 보조 점수를 계산한다.

        입력: 개별 리소스 가격, 요청 예산 상한
        출력: 0~10 사이의 가격 보조 점수
        """
        if not budget_max:
            return SmallPriceScore.NO_BUDGET

        if price <= budget_max * ScoreRatio.BUDGET_GOOD.value:
            return SmallPriceScore.VERY_GOOD

        if price <= budget_max:
            return SmallPriceScore.GOOD

        if price <= budget_max * ScoreRatio.BUDGET_OVER_10_PERCENT.value:
            return SmallPriceScore.OVER_10_PERCENT

        if price <= budget_max * ScoreRatio.BUDGET_OVER_20_PERCENT.value:
            return SmallPriceScore.OVER_20_PERCENT

        return SmallPriceScore.TOO_EXPENSIVE

    def driver_price_score(self, price: int, budget_max: int) -> float:
        """드라이버 가격 보조 점수를 계산한다.

        입력: 드라이버 가격, 요청 예산 상한
        출력: 0~15 사이의 가격 보조 점수
        """
        # 드라이버 기본 가격 점수다.
        base_price_score = self.small_price_score(price, budget_max)
        return base_price_score * DRIVER_PRICE_SCORE_RATIO

    def _guide_language_score(self, request: TourRequest, guide: Guide) -> float:
        """가이드 언어 가능 여부를 100/0으로 판단하고 가이드 언어 배점으로 환산한다."""
        # 가이드 언어 목록에 요청 언어가 포함되어 있는지 확인한 값이다.
        can_speak_requested_language = contains_code(guide.languages, request.requested_language)

        # 언어 지원 여부를 100점 또는 0점으로 변환한 원점수다.
        language_match_score = binary_score(can_speak_requested_language)

        language_score = language_match_score * GuideScore.LANGUAGE / BinaryScore.MATCH
        return language_score

    def _guide_theme_score(self, request: TourRequest, guide: Guide) -> float:
        """가이드가 요청 테마를 지원하는지 확인해 테마 점수를 계산한다."""
        # 가이드 테마 목록에 요청 테마가 포함되어 있는지 확인한 값이다.
        can_support_requested_theme = contains_code(guide.themes, request.requested_theme)

        if can_support_requested_theme:
            return GuideScore.THEME

        return ScoreRange.MIN

    def _driver_vehicle_score(self, driver: Driver, vehicle: Vehicle) -> float:
        """드라이버가 후보 차량 타입을 운전할 수 있는지 계산한다."""
        # 드라이버가 후보 차량 타입을 운전할 수 있는지 확인한 값이다.
        can_drive_vehicle_type = contains_code(driver.vehicle_types, vehicle.vehicle_type)

        if can_drive_vehicle_type:
            return DriverScore.CAN_DRIVE

        return DriverScore.CANNOT_DRIVE

    def _driver_region_score(self, request: TourRequest, driver: Driver) -> float:
        """드라이버의 운행 가능 지역과 요청 지역의 적합도를 계산한다."""
        # 드라이버 운행 가능 지역 목록에 요청 지역이 포함되어 있는지 확인한 값이다.
        can_drive_region = contains_code(driver.regions, request.region_code)
        is_base_region = driver.base_region_code == request.region_code

        if can_drive_region or is_base_region:
            return DriverScore.REGION_MATCH

        return DriverScore.REGION_MISMATCH

    def _driver_language_score(self, request: TourRequest, driver: Driver) -> float:
        """드라이버 언어 가능 여부를 100/0으로 판단하고 드라이버 언어 배점으로 환산한다."""
        # 드라이버 언어 목록에 요청 언어가 포함되어 있는지 확인한 값이다.
        can_speak_requested_language = contains_code(driver.languages, request.requested_language)

        # 언어 지원 여부를 100점 또는 0점으로 변환한 원점수다.
        language_match_score = binary_score(can_speak_requested_language)

        language_score = language_match_score * DriverScore.LANGUAGE / BinaryScore.MATCH
        return language_score

    def _vehicle_region_score(self, request: TourRequest, vehicle: Vehicle) -> float:
        """차량의 주 활동 지역과 요청 지역의 일치 점수를 계산한다."""
        if vehicle.base_region_code == request.region_code:
            return VehicleScore.REGION_MATCH

        return VehicleScore.REGION_MISMATCH

    def _vehicle_seat_score(self, seat_count: int, group_size: int) -> float:
        """요청 인원을 태운 뒤 남는 좌석 여유 점수를 계산한다."""
        remaining = seat_count - group_size
        scores = [
            VehicleScore.SEAT_ENOUGH_3_OR_MORE,
            VehicleScore.SEAT_ENOUGH_2,
            VehicleScore.SEAT_ENOUGH_1,
            VehicleScore.SEAT_EXACT,
        ]

        # 남은 좌석 수를 점수 구간에 맞춰 변환한 값이다.
        seat_score = self._remaining_capacity_score(remaining, scores)
        return seat_score

    def _vehicle_luggage_score(self, luggage_capacity: int, luggage_count: int) -> float:
        """요청 수하물을 실은 뒤 남는 적재 여유 점수를 계산한다."""
        remaining = luggage_capacity - luggage_count
        scores = [
            VehicleScore.LUGGAGE_ENOUGH_3_OR_MORE,
            VehicleScore.LUGGAGE_ENOUGH_2,
            VehicleScore.LUGGAGE_ENOUGH_1,
            VehicleScore.LUGGAGE_EXACT,
        ]

        # 남은 수하물 적재 가능 수량을 점수 구간에 맞춰 변환한 값이다.
        luggage_score = self._remaining_capacity_score(remaining, scores)
        return luggage_score

    def _level_score(self, level: int, max_score: int) -> float:
        """1~5 단계 숙련도를 지정된 만점 기준 점수로 변환한다."""
        # 숙련도 값을 허용 범위 안으로 제한한 값이다.
        normalized_level = clamp(level, ScoreRange.MIN, ReviewScore.MAX_RATING)

        level_score = normalized_level / ReviewScore.MAX_RATING * max_score
        return level_score

    def _rating_review_score(self, rating_avg: int, review_count: int, max_score: int) -> float:
        """평점과 리뷰 수를 함께 반영한 신뢰 점수를 계산한다."""
        rating_score_limit = max_score - ReviewScore.REVIEW_BONUS

        # 평점 값을 0~5 범위 안으로 제한한 값이다.
        normalized_rating = clamp(rating_avg, ScoreRange.MIN, ReviewScore.MAX_RATING)

        rating_part = normalized_rating / ReviewScore.MAX_RATING
        rating_score = rating_part * rating_score_limit
        review_ratio = review_count / ReviewScore.FULL_REVIEW_COUNT
        limited_review_ratio = min(review_ratio, 1)
        review_score = limited_review_ratio * ReviewScore.REVIEW_BONUS
        return rating_score + review_score

    def _small_reliability_score(self, cancel_count: int, no_show_count: int, complaint_count: int, max_score: int) -> float:
        """취소, 노쇼, 컴플레인을 감점으로 반영한다."""
        no_show_penalty = no_show_count * PenaltyValue.NO_SHOW
        complaint_penalty = complaint_count * ScoreRatio.COMPLAINT_PENALTY_UNIT.value
        score = max_score - cancel_count - no_show_penalty - complaint_penalty

        # 신뢰도 점수를 0점과 항목 만점 사이로 제한한 값이다.
        reliability_score = clamp(score, ScoreRange.MIN, max_score)
        return reliability_score

    def _vehicle_type_score(self, requested: str, actual: str) -> float:
        """요청 차종과 실제 차종의 일치 점수를 계산한다."""
        if requested == actual:
            return VehicleScore.TYPE_MATCH

        return VehicleScore.TYPE_MISMATCH

    def _remaining_capacity_score(self, remaining: int, scores: list[int]) -> float:
        """요청 수량을 채운 뒤 남는 좌석/수하물 여유 점수를 계산한다."""
        if len(scores) != CountValue.FOUR:
            raise ValueError("capacity score list must contain 4 values")

        if remaining >= CapacityRemaining.THREE_OR_MORE:
            return scores[0]

        if remaining == CapacityRemaining.TWO:
            return scores[1]

        if remaining == CapacityRemaining.ONE:
            return scores[2]

        if remaining == CapacityRemaining.EXACT:
            return scores[3]

        return ScoreRange.MIN

    def _vehicle_quality_score(self, vehicle: Vehicle) -> float:
        """차량 평점, 리뷰 수, 프리미엄 여부를 품질 점수로 계산한다."""
        # 차량 평점 값을 0~5 범위 안으로 제한한 값이다.
        normalized_rating = clamp(vehicle.rating_avg, ScoreRange.MIN, ReviewScore.MAX_RATING)

        rating_part = normalized_rating / ReviewScore.MAX_RATING
        rating = rating_part * VehicleScore.QUALITY_RATING
        review_ratio = vehicle.review_count / ReviewScore.FULL_REVIEW_COUNT
        limited_review_ratio = min(review_ratio, 1)
        reviews = limited_review_ratio * VehicleScore.QUALITY_REVIEW

        # 프리미엄 차량 여부를 품질 보너스로 변환한 값이다.
        premium = self._vehicle_premium_score(vehicle)

        total = rating + reviews + premium + VehicleScore.QUALITY_BASE

        # 차량 품질 점수를 품질 항목 만점 안으로 제한한 값이다.
        quality_score = clamp(total, ScoreRange.MIN, VehicleScore.QUALITY)
        return quality_score

    def _vehicle_premium_score(self, vehicle: Vehicle) -> float:
        """프리미엄 차량 여부를 차량 품질 보너스로 변환한다."""
        if vehicle.is_premium:
            return VehicleScore.QUALITY_PREMIUM

        return ScoreRange.MIN


def binary_score(is_matched: bool) -> int:
    """가능/불가능 판정을 100점 또는 0점으로 변환한다.

    입력: 조건 만족 여부
    출력: 100 또는 0
    """
    if is_matched:
        return BinaryScore.MATCH

    return BinaryScore.NO_MATCH


def contains_code(raw: str, code: str) -> bool:
    """쉼표 또는 파이프로 저장된 코드 목록에 특정 코드가 있는지 확인한다.

    입력: 원본 코드 문자열, 찾을 코드
    출력: 포함 여부(bool)
    """
    if not raw or not code:
        return False

    # 파이프 구분자를 쉼표 구분자로 통일한 문자열이다.
    normalized_separator_text = raw.replace("|", ",")

    # 구분자로 나눈 원본 코드 목록이다.
    raw_values = normalized_separator_text.split(",")

    values = []
    for item in raw_values:
        # 코드 앞뒤 공백을 제거한 값이다.
        stripped_item = item.strip()

        # 대소문자 차이로 인한 오매칭을 막기 위해 소문자로 바꾼 코드값이다.
        normalized_item = stripped_item.lower()
        values.append(normalized_item)

    # 비교 대상 코드의 앞뒤 공백을 제거한 값이다.
    stripped_code = code.strip()

    # 비교 대상 코드를 소문자로 바꾼 값이다.
    normalized_code = stripped_code.lower()
    return normalized_code in values


def clamp(value: float, min_value: float, max_value: float) -> float:
    """숫자를 최소값과 최대값 사이로 제한한다.

    입력: 원본 값, 최소값, 최대값
    출력: 제한된 값
    """
    if value < min_value:
        return min_value

    if value > max_value:
        return max_value

    return value

