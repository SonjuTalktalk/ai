"""
손주톡톡 처방전 OCR 테스트 (GPT-4o-mini Vision)
"""

import os
from pprint import pprint
from sonju_ai.core.health_service import HealthService


def main():
    print("\n=== 손주톡톡 처방전 OCR 테스트 시작 ===")

    # 1) 현재 파일 기준 절대경로 계산
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # 2) 테스트 이미지 경로 설정 (파일명만 바꾸면 됨)
    IMAGE_PATH = os.path.join(BASE_DIR, "samples", "prescriptions", "pre3.jpg")

    print(f"- 이미지 파일 경로: {IMAGE_PATH}\n")

    # 3) HealthService 초기화
    service = HealthService()

    # 4) OCR 실행
    result = service.extract_prescription_info(IMAGE_PATH)

    # 5) 원본 결과 출력
    print("👉 OCR 원본 분석 결과(raw):")
    pprint(result, width=80, sort_dicts=False)
    print("\n")

    # 6) 약 정보만 보기
    medicines = result.get("medicines", [])

    if not medicines:
        print("△ 추출된 약 정보가 없습니다.\n")
        return

    print("=== 추출된 약 정보 ===")
    for i, med in enumerate(medicines, start=1):
        print(f"\n[{i}] ------------------")
        print(f"약 이름: {med.get('name')}")
        print(f"처방 날짜: {med.get('prescription_date')}")
        print(f"투약 일수: {med.get('duration_days')}")
        print(f"복용 횟수: {med.get('frequency')}")
        print(f"시간대: {med.get('times')}")
    print("\n")


if __name__ == "__main__":
    main()
