"""
손주톡톡 채팅 서비스
메인 채팅 기능과 대화 관리 (4개 모델 지원)
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from sonju_ai.utils.openai_client import OpenAIClient
from sonju_ai.config.prompts import get_prompt, validate_model_type

logger = logging.getLogger(__name__)

class ChatService:
    """손주톡톡 메인 채팅 서비스 (4개 AI 모델 지원)"""
    
    def __init__(
        self, 
        ai_name: str = "손주",
        model_type: str = "friendly"
    ):
        """
        채팅 서비스 초기화
        
        Args:
            ai_name: AI 어시스턴트 이름
            model_type: AI 모델 타입
                - "friendly": 다정한 (따뜻하고 자상하게)
                - "active": 활발한 (에너지 넘치고 적극적으로)
                - "pleasant": 유쾌한 (재치있고 유머러스하게)
                - "reliable": 듬직한 (침착하고 체계적으로)
        """
        self.ai_name = ai_name
        self.model_type = validate_model_type(model_type)
        
        self.openai_client = OpenAIClient()
        self.conversation_history: Dict[str, List[Dict]] = {}
        
        logger.info(
            f"채팅 서비스 초기화 완료 (AI 이름: {ai_name}, 모델: {self.model_type})"
        )
    
    def update_model_type(self, model_type: str):
        """
        AI 모델 타입 업데이트
        
        Args:
            model_type: 새로운 모델 타입 ("friendly", "active", "pleasant", "reliable")
        """
        self.model_type = validate_model_type(model_type)
        logger.info(f"AI 모델 업데이트 완료: {self.model_type}")
    
    def update_ai_name(self, ai_name: str):
        """
        AI 이름 업데이트
        
        Args:
            ai_name: 새로운 AI 이름
        """
        self.ai_name = ai_name
        logger.info(f"AI 이름 업데이트 완료: {self.ai_name}")
    
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
            dict: {
                "response": "AI응답",
                "timestamp": "시간",
                "ai_name": "AI이름",
                "model_type": "모델타입"
            }
        """
        try:
            # 사용자별 대화 기록 가져오기
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            history = self.conversation_history[user_id]
            
            # 시스템 프롬프트 설정 (모델 타입에 따라)
            system_prompt = get_prompt(
                "chat",
                model_type=self.model_type,
                ai_name=self.ai_name
            )
            
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
                "timestamp": datetime.now().isoformat(),
                "model_type": self.model_type
            }
            history.append(conversation_record)
            
            # 대화 기록 길이 제한
            if len(history) > max_history * 2:
                self.conversation_history[user_id] = history[-max_history:]
            
            logger.info(
                f"채팅 완료 - 사용자: {user_id}, "
                f"모델: {self.model_type}, 메시지 길이: {len(message)}"
            )
            
            return {
                "response": ai_response,
                "timestamp": conversation_record["timestamp"],
                "ai_name": self.ai_name,
                "model_type": self.model_type
            }
            
        except Exception as e:
            logger.error(f"채팅 처리 중 오류 발생 - 사용자: {user_id}, 오류: {e}")
            error_response = "죄송해요, 잠시 문제가 생겼어요. 다시 한 번 말씀해 주시겠어요?"
            
            return {
                "response": error_response,
                "timestamp": datetime.now().isoformat(),
                "ai_name": self.ai_name,
                "model_type": self.model_type
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
    # 4개 모델 테스트
    try:
        print("="*50)
        print("손주톡톡 4개 AI 모델 테스트")
        print("="*50)
        
        # 1. 다정한(friendly) 모델
        print("\n[1] 다정한(friendly) 모델")
        chat_friendly = ChatService("손주", "friendly")
        response1 = chat_friendly.chat("test_user", "문자 보내는 법 알려주세요")
        print(f"응답: {response1['response']}\n")
        
        # 2. 활발한(active) 모델
        print("[2] 활발한(active) 모델")
        chat_active = ChatService("손주", "active")
        response2 = chat_active.chat("test_user", "문자 보내는 법 알려주세요")
        print(f"응답: {response2['response']}\n")
        
        # 3. 유쾌한(pleasant) 모델
        print("[3] 유쾌한(pleasant) 모델")
        chat_pleasant = ChatService("손주", "pleasant")
        response3 = chat_pleasant.chat("test_user", "문자 보내는 법 알려주세요")
        print(f"응답: {response3['response']}\n")
        
        # 4. 듬직한(reliable) 모델
        print("[4] 듬직한(reliable) 모델")
        chat_reliable = ChatService("손주", "reliable")
        response4 = chat_reliable.chat("test_user", "문자 보내는 법 알려주세요")
        print(f"응답: {response4['response']}\n")
        
        # 모델 변경 테스트
        print("[5] 모델 변경 테스트")
        chat_service = ChatService("손주", "friendly")
        print("초기: friendly 모델")
        
        chat_service.update_model_type("active")
        print("변경: active 모델")
        response5 = chat_service.chat("test_user", "오늘 기분이 좋아요!")
        print(f"응답: {response5['response']}\n")
        
        print("="*50)
        print("테스트 완료!")
        print("="*50)
        
    except Exception as e:
        print(f"테스트 중 오류: {e}")