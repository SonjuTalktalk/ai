"""
손주톡톡 분석 생성 서비스
사용자의 활동/학습/사용 로그를 분석해서 칭찬/격려/분석 리포트 생성
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from sonju_ai.utils.openai_client import OpenAIClient
from sonju_ai.config.prompts import get_prompt

logger = logging.getLogger(__name__)

class AnalysisGenerator:
    """사용자 활동 분석 및 리포트 생성 서비스"""
    
    def __init__(self):
        """분석 생성 서비스 초기화"""
        self.openai_client = OpenAIClient()
        logger.info("분석 생성 서비스 초기화 완료")
    
    def generate_learning_analysis(
        self, 
        user_id: str, 
        learning_data: Dict,
        period: str = "week"
    ) -> Dict[str, str]:
        """
        학습 분석 리포트 생성
        
        Args:
            user_id: 사용자 ID
            learning_data: 학습 데이터 {
                "total_study_time": 180,  # 분
                "completed_lessons": 5,
                "accuracy_rate": 0.85,
                "app_usage": {"카카오톡": 20, "사진": 15},
                "weak_areas": ["사진 전송", "설정 변경"],
                "strong_areas": ["전화 걸기", "메시지 보내기"]
            }
            period: 분석 기간 ("day", "week", "month")
            
        Returns:
            dict: {
                "analysis_text": "분석 내용",
                "encouragement": "격려 메시지",
                "recommendations": ["추천1", "추천2"],
                "score": 85
            }
        """
        try:
            # 학습 데이터 요약
            data_summary = self._summarize_learning_data(learning_data, period)
            
            # 분석 프롬프트 생성
            analysis_prompt = get_prompt("analysis")
            
            # AI에게 분석 요청
            user_message = f"""
학습 데이터 요약: {data_summary}

위 데이터를 바탕으로 다음을 생성해주세요:
1. 따뜻하고 구체적인 칭찬과 분석 (2-3문장)
2. 격려 메시지 (1-2문장)
3. 개선 추천사항 3개 (각각 한 문장)

어르신이 기뻐하실 만한 톤으로 작성해주세요.
"""
            
            response = self.openai_client.simple_chat(user_message, analysis_prompt)
            
            # 응답 파싱
            analysis_result = self._parse_analysis_response(response, learning_data)
            
            logger.info(f"학습 분석 생성 완료 - 사용자: {user_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"학습 분석 생성 중 오류 - 사용자: {user_id}, 오류: {e}")
            return self._get_default_analysis(learning_data)
    
    def _summarize_learning_data(self, learning_data: Dict, period: str) -> str:
        """학습 데이터를 자연어로 요약"""
        summary_parts = []
        
        # 기간 설정
        period_text = {"day": "오늘", "week": "이번주", "month": "이번달"}
        period_str = period_text.get(period, "이번주")
        
        # 학습 시간
        if "total_study_time" in learning_data:
            minutes = learning_data["total_study_time"]
            if minutes >= 60:
                hours = minutes // 60
                mins = minutes % 60
                if mins > 0:
                    time_str = f"{hours}시간 {mins}분"
                else:
                    time_str = f"{hours}시간"
            else:
                time_str = f"{minutes}분"
            summary_parts.append(f"{period_str} 학습 시간: {time_str}")
        
        # 완료한 학습
        if "completed_lessons" in learning_data:
            count = learning_data["completed_lessons"]
            summary_parts.append(f"완료한 학습: {count}개")
        
        # 정확도
        if "accuracy_rate" in learning_data:
            rate = int(learning_data["accuracy_rate"] * 100)
            summary_parts.append(f"정확도: {rate}%")
        
        # 자주 사용한 앱
        if "app_usage" in learning_data:
            apps = learning_data["app_usage"]
            if apps:
                top_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)[:3]
                app_names = [f"{name}({count}회)" for name, count in top_apps]
                summary_parts.append(f"자주 사용한 앱: {', '.join(app_names)}")
        
        # 어려워하는 영역
        if "weak_areas" in learning_data:
            weak = learning_data["weak_areas"]
            if weak:
                summary_parts.append(f"연습이 필요한 영역: {', '.join(weak[:2])}")
        
        # 잘하는 영역
        if "strong_areas" in learning_data:
            strong = learning_data["strong_areas"]
            if strong:
                summary_parts.append(f"잘하시는 영역: {', '.join(strong[:2])}")
        
        return ". ".join(summary_parts) if summary_parts else "기본 학습 데이터"
    
    def _parse_analysis_response(self, response: str, learning_data: Dict) -> Dict[str, str]:
        """AI 응답을 파싱해서 구조화된 분석 결과 생성"""
        try:
            # 응답을 섹션별로 나누기 시도
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            analysis_text = ""
            encouragement = ""
            recommendations = []
            
            current_section = "analysis"
            
            for line in lines:
                # 키워드로 섹션 구분
                if any(keyword in line.lower() for keyword in ['격려', '응원', '칭찬']):
                    current_section = "encouragement"
                elif any(keyword in line.lower() for keyword in ['추천', '제안', '개선']):
                    current_section = "recommendations"
                elif line.startswith(('1.', '2.', '3.', '-', '•')):
                    if current_section == "recommendations":
                        # 번호나 기호 제거 후 추가
                        clean_line = line.lstrip('123456789.-•').strip()
                        if clean_line:
                            recommendations.append(clean_line)
                else:
                    if current_section == "analysis":
                        analysis_text += line + " "
                    elif current_section == "encouragement":
                        encouragement += line + " "
            
            # 기본값 설정
            if not analysis_text:
                analysis_text = response[:200] + "..." if len(response) > 200 else response
            
            if not encouragement:
                encouragement = "꾸준히 노력하고 계시는 모습이 정말 보기 좋아요!"
            
            if not recommendations:
                recommendations = ["조금씩 꾸준히 연습해보세요", "어려운 부분은 천천히 반복해보세요", "가족과 함께 연습하면 더 재미있을 거예요"]
            
            # 점수 계산
            score = self._calculate_score(learning_data)
            
            return {
                "analysis_text": analysis_text.strip(),
                "encouragement": encouragement.strip(),
                "recommendations": recommendations[:3],  # 최대 3개
                "score": score
            }
            
        except Exception as e:
            logger.warning(f"분석 응답 파싱 실패: {e}")
            return self._get_default_analysis(learning_data)
    
    def _calculate_score(self, learning_data: Dict) -> int:
        """학습 데이터를 바탕으로 점수 계산"""
        try:
            score = 70  # 기본 점수
            
            # 학습 시간 (최대 15점)
            if "total_study_time" in learning_data:
                minutes = learning_data["total_study_time"]
                if minutes >= 120:  # 2시간 이상
                    score += 15
                elif minutes >= 60:  # 1시간 이상
                    score += 10
                elif minutes >= 30:  # 30분 이상
                    score += 5
            
            # 정확도 (최대 15점)
            if "accuracy_rate" in learning_data:
                rate = learning_data["accuracy_rate"]
                score += int(rate * 15)
            
            # 완료한 학습 수 (최대 10점)
            if "completed_lessons" in learning_data:
                lessons = learning_data["completed_lessons"]
                score += min(lessons * 2, 10)
            
            return min(score, 100)  # 최대 100점
            
        except Exception:
            return 75  # 기본 점수
    
    def _get_default_analysis(self, learning_data: Dict) -> Dict[str, str]:
        """기본 분석 결과 (fallback)"""
        return {
            "analysis_text": "꾸준히 학습하고 계시는 모습이 정말 보기 좋습니다. 작은 발걸음이지만 분명히 발전하고 계세요.",
            "encouragement": "오늘도 새로운 것을 배우려는 의지가 훌륭합니다. 계속 화이팅하세요!",
            "recommendations": [
                "매일 조금씩이라도 꾸준히 연습해보세요",
                "어려운 부분은 가족에게 도움을 요청해보세요",
                "성공한 부분은 스스로 칭찬해주세요"
            ],
            "score": self._calculate_score(learning_data)
        }
    
    def generate_weekly_summary(self, user_id: str, week_data: List[Dict]) -> str:
        """
        주간 요약 리포트 생성
        
        Args:
            user_id: 사용자 ID
            week_data: 일별 데이터 리스트 [{"date": "2025-10-21", "study_time": 30, ...}, ...]
            
        Returns:
            str: 주간 요약 텍스트
        """
        try:
            if not week_data:
                return "이번주는 충분한 휴식을 취하셨네요!"
            
            # 주간 통계 계산
            total_days = len(week_data)
            total_study_time = sum(day.get("study_time", 0) for day in week_data)
            total_lessons = sum(day.get("completed_lessons", 0) for day in week_data)
            avg_accuracy = sum(day.get("accuracy_rate", 0) for day in week_data) / total_days if total_days > 0 else 0
            
            # 요약 텍스트 생성
            summary_parts = [
                f"이번주 {total_days}일 동안 활동하셨습니다.",
                f"총 학습 시간은 {total_study_time}분이고, {total_lessons}개의 학습을 완료하셨습니다."
            ]
            
            if avg_accuracy > 0:
                accuracy_percent = int(avg_accuracy * 100)
                summary_parts.append(f"평균 정확도는 {accuracy_percent}%입니다.")
            
            # 격려 메시지 추가
            if total_study_time >= 300:  # 5시간 이상
                summary_parts.append("정말 열심히 하셨네요! 대단합니다.")
            elif total_study_time >= 120:  # 2시간 이상
                summary_parts.append("꾸준히 노력하고 계시는 모습이 보기 좋습니다.")
            else:
                summary_parts.append("조금씩이라도 꾸준히 하고 계시니 훌륭합니다.")
            
            logger.info(f"주간 요약 생성 완료 - 사용자: {user_id}")
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"주간 요약 생성 중 오류 - 사용자: {user_id}, 오류: {e}")
            return "이번주도 고생 많으셨어요. 다음주도 함께 화이팅해요!"


# 간단한 테스트 실행
if __name__ == "__main__":
    try:
        analysis_generator = AnalysisGenerator()
        
        # 테스트 학습 데이터
        test_learning_data = {
            "total_study_time": 150,  # 2시간 30분
            "completed_lessons": 8,
            "accuracy_rate": 0.78,
            "app_usage": {"카카오톡": 25, "사진": 18, "전화": 12},
            "weak_areas": ["사진 전송", "설정 변경"],
            "strong_areas": ["전화 걸기", "메시지 보내기", "앱 찾기"]
        }
        
        # 분석 생성 테스트
        analysis = analysis_generator.generate_learning_analysis("test_user", test_learning_data)
        
        # 결과 출력
        print("=== 학습 분석 결과 ===")
        print(f"점수: {analysis['score']}점")
        print(f"분석: {analysis['analysis_text']}")
        print(f"격려: {analysis['encouragement']}")
        print("추천사항:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        # 주간 요약 테스트
        test_week_data = [
            {"date": "2025-10-21", "study_time": 30, "completed_lessons": 2, "accuracy_rate": 0.8},
            {"date": "2025-10-22", "study_time": 45, "completed_lessons": 3, "accuracy_rate": 0.75},
            {"date": "2025-10-23", "study_time": 60, "completed_lessons": 4, "accuracy_rate": 0.85}
        ]
        
        weekly_summary = analysis_generator.generate_weekly_summary("test_user", test_week_data)
        print(f"\n=== 주간 요약 ===\n{weekly_summary}")
        
    except Exception as e:
        print(f"테스트 중 오류: {e}")