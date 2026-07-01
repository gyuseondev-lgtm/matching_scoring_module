from matching_scoring.config import load_settings
from matching_scoring.matching_service import MatchingService
from matching_scoring.score_calculator import ScoreCalculator
from matching_scoring.store import MatchingStore


def main():
    """콘솔에서 테스트 시나리오를 실행한다.

    입력: 사용자가 입력한 메뉴, tour_request_id, reserve_id, user_no, candidate_id
    출력: 후보 생성 결과, 추천 후보 목록, 선택 처리 결과를 콘솔에 출력한다.
    remark: 운영 UI가 붙기 전까지 수동 테스트용으로만 사용한다.
    """
    settings = load_settings()
    store = MatchingStore(settings)
    calculator = ScoreCalculator(settings)
    service = MatchingService(store, calculator, settings)

    print("=== Matching Scoring Prototype ===")

    while True:
        print("\n1. tour_request 목록 보기")
        print("2. 후보 생성")
        print("3. 추천 후보 보기")
        print("4. 후보 선택")
        print("0. 종료")

        choice = input("선택: ").strip()

        if choice == "1":
            for request in store.list_tour_requests():
                print(
                    f"{request.id}: {request.start_at} ~ {request.end_at}, "
                    f"region={request.region_code}, language={request.requested_language}, "
                    f"vehicle={request.requested_vehicle_type}, budget={request.budget_max}"
                )

        elif choice == "2":
            tour_request_id = int(input("tour_request_id: ").strip())
            reserve_id = input("reserve_id: ").strip()
            user_no = int(input("user_no: ").strip())

            candidates = service.generate_candidates(tour_request_id, reserve_id, user_no)
            print(f"{len(candidates)}개 후보를 저장했습니다.")
            print_top_candidates(candidates)

        elif choice == "3":
            reserve_id = input("reserve_id: ").strip()
            user_no = int(input("user_no: ").strip())
            candidates = store.get_candidates(reserve_id, user_no)
            print_top_candidates(candidates)

        elif choice == "4":
            candidate_id = int(input("선택할 candidate_id: ").strip())
            create_reservation = input("reservations 확정 저장도 할까요? (y/N): ").strip().lower() == "y"
            service.select_candidate(candidate_id, create_reservation=create_reservation)
            print("선택 처리가 완료되었습니다.")

        elif choice == "0":
            break

        else:
            print("잘못된 선택입니다.")

    store.close()


def print_top_candidates(candidates):
    """상위 추천 후보를 콘솔에 출력한다.

    입력: MatchingCandidate 목록
    출력: 없음
    """
    if not candidates:
        print("후보가 없습니다.")
        return

    print("\n[추천 후보]")
    for candidate in candidates[:3]:
        print(
            f"#{candidate.rank_no} candidate_id={candidate.id or '-'} "
            f"guide={candidate.guide_id or '-'} vehicle={candidate.vehicle_id or '-'} "
            f"driver={candidate.driver_id or '-'} total={candidate.total_score:.2f} "
            f"(guide={candidate.guide_score:.2f}, vehicle={candidate.vehicle_score:.2f}, "
            f"driver={candidate.driver_score:.2f}, price={candidate.price_score:.2f}, "
            f"stability={candidate.stability_score:.2f})"
        )


if __name__ == "__main__":
    main()
