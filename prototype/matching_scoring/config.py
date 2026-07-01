import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Settings:
    """프로토타입 실행에 필요한 DB 접속 정보와 점수 가중치 설정이다."""

    db_host: str  # DB 호스트
    db_port: int  # DB 포트
    db_name: str  # DB 이름
    db_user: str  # DB 사용자
    db_password: str  # DB 비밀번호

    recommend_count: int = 3  # 추천 후보 표시 개수
    max_saved_candidates: int = 50  # DB에 저장할 최대 후보 수

    guide_weight: float = 0.40  # 가이드 점수 가중치
    vehicle_weight: float = 0.20  # 차량 점수 가중치
    driver_weight: float = 0.20  # 드라이버 점수 가중치
    price_weight: float = 0.10  # 가격 점수 가중치
    stability_weight: float = 0.10  # 안정성 점수 가중치


def load_settings() -> Settings:
    """환경변수와 .env 파일에서 실행 설정을 읽는다.

    입력: .env 또는 OS 환경변수
    출력: Settings
    """
    load_dotenv()

    return Settings(
        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_name=os.getenv("DB_NAME", "blackbird"),
        db_user=os.getenv("DB_USER", ""),
        db_password=os.getenv("DB_PASSWORD", ""),
    )
