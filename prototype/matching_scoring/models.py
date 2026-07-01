from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional


# 투어 요청 1건을 표현한다. tour_requests 테이블의 스코어링 입력값이다.
@dataclass
class TourRequest:
    id: int  # 투어요청 ID
    customer_id: int  # 요청 고객 ID
    status: str  # 요청 상태
    tour_date: date  # 투어 일자
    start_at: datetime  # 투어 시작 일시
    end_at: datetime  # 투어 종료 일시
    region_code: str  # 요청 지역 코드
    group_size: int  # 탑승/투어 인원 수
    luggage_count: int  # 수하물 수
    guide_required: bool  # 가이드 필요 여부
    requested_language: str  # 요청 언어 코드
    vehicle_required: bool  # 차량 필요 여부
    requested_vehicle_type: str  # 요청 차종 코드
    driver_required: bool  # 드라이버 필요 여부
    requested_theme: str  # 요청 투어 테마 코드
    budget_max: int  # 최대 예산


# 가이드 후보 1명을 표현한다. guides 테이블의 점수 계산 대상이다.
@dataclass
class Guide:
    id: int  # 가이드 ID
    name: str  # 가이드 이름
    status: str  # 가이드 운영 상태
    base_region_code: str  # 주 활동 지역 코드
    languages: str  # 지원 언어 코드 목록
    themes: str  # 지원 투어 테마 코드 목록
    region_level: int  # 지역 숙련도
    price_per_day: int  # 1일 가격
    price_per_hour: int  # 시간당 가격
    rating_avg: int  # 평균 평점
    review_count: int  # 리뷰 수
    response_rate: int  # 응답률
    avg_response_minutes: int  # 평균 응답 시간(분)
    cancel_count: int  # 취소 횟수
    no_show_count: int  # 노쇼 횟수
    complaint_count: int  # 컴플레인 횟수


# 드라이버 후보 1명을 표현한다. drivers 테이블의 점수 계산 대상이다.
@dataclass
class Driver:
    id: int  # 드라이버 ID
    name: str  # 드라이버 이름
    approval_status: str  # 승인 상태
    operation_status: str  # 운영 상태
    base_region_code: str  # 주 활동 지역 코드
    vehicle_types: str  # 운전 가능 차종 코드 목록
    languages: str  # 지원 언어 코드 목록
    regions: str  # 운행 가능 지역 코드 목록
    price_per_day: int  # 1일 가격
    price_per_hour: int  # 시간당 가격
    rating_avg: int  # 평균 평점
    review_count: int  # 리뷰 수
    response_rate: int  # 응답률
    avg_response_minutes: int  # 평균 응답 시간(분)
    cancel_count: int  # 취소 횟수
    no_show_count: int  # 노쇼 횟수
    complaint_count: int  # 컴플레인 횟수


# 차량 후보 1대를 표현한다. vehicles 테이블의 점수 계산 대상이다.
@dataclass
class Vehicle:
    id: int  # 차량 ID
    vehicle_name: str  # 차량명
    vehicle_type: str  # 차종 타입 코드
    approval_status: str  # 승인 상태
    operation_status: str  # 운영 상태
    base_region_code: str  # 주 활동 지역 코드
    seat_count: int  # 좌석 수
    luggage_capacity: int  # 수하물 적재 가능 수량
    model_name: str  # 차량 모델명
    model_year: str  # 차량 연식
    is_premium: bool  # 프리미엄 차량 여부
    has_child_seat: bool  # 카시트 보유 여부
    price_per_day: int  # 1일 가격
    price_per_hour: int  # 시간당 가격
    rating_avg: int  # 평균 평점
    review_count: int  # 리뷰 수
    avg_response_minutes: int  # 평균 응답 시간(분)
    cancel_count: int  # 취소 횟수
    no_show_count: int  # 노쇼 횟수
    complaint_count: int  # 컴플레인 횟수


# 리소스의 특정 날짜/시간 가용성을 표현한다. resource_availability 테이블의 행이다.
@dataclass
class Availability:
    id: int  # 가용성 ID
    resource_type: str  # VEHICLE/GUIDE/DRIVER
    vehicle_id: Optional[int]  # 차량 가용성일 때 차량 ID
    partner_id: Optional[str]  # 가이드/드라이버 파트너 ID
    partner_no: Optional[int]  # 가이드/드라이버 사용자 키
    available_date: date  # 가용 날짜
    start_time: time  # 가용 시작 시간
    end_time: time  # 가용 종료 시간
    status: str  # 가용성 상태


# 확정 또는 진행 예약을 표현한다. reservations 테이블의 시간 충돌 확인 대상이다.
@dataclass
class Reservation:
    id: int  # 예약 ID
    requested_id: int  # tour_requests.id
    guide_id: Optional[int]  # 확정 가이드 ID
    vehicle_id: Optional[int]  # 확정 차량 ID
    driver_id: Optional[int]  # 확정 드라이버 ID
    start_at: datetime  # 예약 시작 일시
    end_at: datetime  # 예약 종료 일시
    status: str  # 예약 상태
    matching_candidate_id: int  # 선택 후보 ID


# 계산된 후보 조합 1건을 표현한다. matching_candidates 테이블에 저장된다.
@dataclass
class MatchingCandidate:
    reserve_id: str  # 기존 예약 ID
    user_no: int  # 사용자 키
    guide_id: Optional[str]  # 가이드 ID
    guide_no: Optional[int]  # 가이드 사용자 키
    vehicle_id: Optional[int]  # 차량 ID
    driver_id: Optional[str]  # 드라이버 ID
    driver_no: Optional[int]  # 드라이버 사용자 키
    guide_score: float  # 가이드 점수
    vehicle_score: float  # 차량 점수
    driver_score: float  # 드라이버 점수
    price_score: float  # 가격 점수
    stability_score: float  # 안정성 점수
    total_score: float  # 최종 점수
    guide_price: int  # 가이드 비용
    vehicle_price: int  # 차량 비용
    driver_price: int  # 드라이버 비용
    total_price: int  # 총 비용
    rank_no: int = 0  # 후보 순위
    candidate_status: str = "OFFERED"  # 후보 상태
    is_recommended: bool = False  # 추천 후보 여부
    is_selected: bool = False  # 최종 선택 여부
    id: Optional[int] = None  # 저장 후 생성되는 매칭 ID

