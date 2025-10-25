"""
손주톡톡 채팅 서비스
메인 채팅 기능과 대화 관리
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from sonju_ai.utils.openai_client import OpenAIClient
from sonju_ai.config.prompts import get_prompt

logger = logging.getLogger(__name__)

class ChatService:
    """손주톡톡 메인 채팅 서비스"""
    
    def __init__(self, ai_name: str = "손주"):
        """
        채팅 서비스 초기화
        
        Args:
            ai_name: AI 어시스턴트 이름
        """
        self.ai_name = ai_name
        self.openai_client = OpenAIClient()
        self.conversation_history: Dict[str, List[Dict]] = {}
        logger.info(f"채팅 서비스 초기화 완료 (AI 이름: {ai_name})")
    
    def chat(
        self, 
        user_id: str, 
        message: str, 
        max_history: int = 10
    ) -> Dict[str, str]:
        """
        사용자와 채팅
        
        Args:
            user_id: 사용자 ID
            message: 사용자 메시지
            max_history: 유지할 대화 기록 수
            
        Returns:
            dict: {"response": "AI응답", "timestamp": "시간", "ai_name": "AI이름"}
        """
        try:
            # 사용자별 대화 기록 가져오기
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            history = self.conversation_history[user_id]
            
            # 시스템 프롬프트 설정
            system_prompt = get_prompt("chat", ai_name=self.ai_name)
            
            # 메시지 구성
            messages = [{"role": "system", "content": system_prompt}]
            
            # 기존 대화 기록 추가 (최근 max_history개만)
            recent_history = history[-max_history:] if len(history) > max_history else history
            for conv in recent_history:
                messages.append({"role": "user", "content": conv["user_message"]})
                messages.append({"role": "assistant", "content": conv["ai_response"]})
            
            # 현재 사용자 메시지 추가
            messages.append({"role": "user", "content": message})
            
            # OpenAI API 호출
            ai_response = self.openai_client.chat_completion(messages)
            
            # 대화 기록 저장
            conversation_record = {
                "user_message": message,
                "ai_response": ai_response,
                "timestamp": datetime.now().isoformat()
            }
            history.append(conversation_record)
            
            # 대화 기록 길이 제한
            if len(history) > max_history * 2:
                self.conversation_history[user_id] = history[-max_history:]
            
            logger.info(f"채팅 완료 - 사용자: {user_id}, 메시지 길이: {len(message)}")
            
            return {
                "response": ai_response,
                "timestamp": conversation_record["timestamp"],
                "ai_name": self.ai_name
            }
            
        except Exception as e:
            logger.error(f"채팅 처리 중 오류 발생 - 사용자: {user_id}, 오류: {e}")
            error_response = "죄송해요, 잠시 문제가 생겼어요. 다시 한 번 말씀해 주시겠어요?"
            
            return {
                "response": error_response,
                "timestamp": datetime.now().isoformat(),
                "ai_name": self.ai_name
            }
    
    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """
        사용자의 대화 기록 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            list: 대화 기록 리스트
        """
        return self.conversation_history.get(user_id, [])
    
    def clear_conversation_history(self, user_id: str) -> bool:
        """
        사용자의 대화 기록 삭제
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if user_id in self.conversation_history:
                del self.conversation_history[user_id]
                logger.info(f"대화 기록 삭제 완료 - 사용자: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"대화 기록 삭제 중 오류 - 사용자: {user_id}, 오류: {e}")
            return False
    
    def generate_encouragement(self, user_id: str, context: str = "") -> str:
        """
        격려 메시지 생성
        
        Args:
            user_id: 사용자 ID
            context: 격려 상황 설명
            
        Returns:
            str: 격려 메시지
        """
        try:
            encouragement_prompt = get_prompt("encouragement")
            
            if context:
                user_message = f"상황: {context}. 이런 상황에서 어르신을 격려해주세요."
            else:
                user_message = "어르신을 격려하는 따뜻한 메시지를 만들어주세요."
            
            encouragement = self.openai_client.simple_chat(user_message, encouragement_prompt)
            
            logger.info(f"격려 메시지 생성 완료 - 사용자: {user_id}")
            return encouragement
            
        except Exception as e:
            logger.error(f"격려 메시지 생성 중 오류 - 사용자: {user_id}, 오류: {e}")
            return "오늘도 수고 많으셨어요! 천천히 하시면 돼요."
    
    def analyze_user_pattern(self, user_id: str, activity_data: Dict) -> str:
        """
        사용자 패턴 분석 및 피드백 생성
        
        Args:
            user_id: 사용자 ID
            activity_data: 활동 데이터 {"study_time": 120, "completed_tasks": 5, ...}
            
        Returns:
            str: 분석 결과 메시지
        """
        try:
            analysis_prompt = get_prompt("analysis")
            
            # 활동 데이터를 자연어로 변환
            data_summary = []
            if "study_time" in activity_data:
                minutes = activity_data["study_time"]
                hours = minutes // 60
                mins = minutes % 60
                if hours > 0:
                    data_summary.append(f"학습 시간: {hours}시간 {mins}분")
                else:
                    data_summary.append(f"학습 시간: {mins}분")
            
            if "completed_tasks" in activity_data:
                data_summary.append(f"완료한 미션: {activity_data['completed_tasks']}개")
            
            if "accuracy_rate" in activity_data:
                rate = int(activity_data['accuracy_rate'] * 100)
                data_summary.append(f"정확도: {rate}%")
            
            data_text = ", ".join(data_summary)
            user_message = f"사용자 활동 데이터: {data_text}. 이 데이터를 바탕으로 따뜻한 분석과 격려를 해주세요."
            
            analysis = self.openai_client.simple_chat(user_message, analysis_prompt)
            
            logger.info(f"사용자 패턴 분석 완료 - 사용자: {user_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"사용자 패턴 분석 중 오류 - 사용자: {user_id}, 오류: {e}")
            return "꾸준히 노력하고 계시는 모습이 보기 좋아요! 계속 화이팅하세요!"


# 간단한 테스트 실행
if __name__ == "__main__":
    # 기본 테스트
    try:
        chat_service = ChatService("손주톡톡")
        
        # 테스트 채팅
        response = chat_service.chat("test_user", "안녕하세요!")
        print(f"응답: {response['response']}")
        
        # 격려 메시지 테스트
        encouragement = chat_service.generate_encouragement("test_user", "새로운 기능을 배우려고 시도중")
        print(f"격려: {encouragement}")
        
    except Exception as e:
        print(f"테스트 중 오류: {e}")