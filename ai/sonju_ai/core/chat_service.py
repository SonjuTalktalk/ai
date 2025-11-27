"""
손주톡톡 채팅 서비스
메인 채팅 기능과 대화 관리 (4개 모델 지원 + 대화형 할일 추출 + TTS)
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from sonju_ai.utils.openai_client import OpenAIClient
from sonju_ai.config.prompts import get_prompt, validate_model_type
from sonju_ai.core.todo_processor import TodoProcessor

logger = logging.getLogger(__name__)

class ChatService:
    """손주톡톡 메인 채팅 서비스 (4개 AI 모델 + 대화형 할일 추출 + TTS)"""
    
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
        self.todo_processor = TodoProcessor()
        
        logger.info(
            f"채팅 서비스 초기화 완료 (AI 이름: {ai_name}, 모델: {self.model_type})"
        )
    
    def update_model_type(self, model_type: str):
        """AI 모델 타입 업데이트"""
        self.model_type = validate_model_type(model_type)
        logger.info(f"AI 모델 업데이트 완료: {self.model_type}")
    
    def update_ai_name(self, ai_name: str):
        """AI 이름 업데이트"""
        self.ai_name = ai_name
        logger.info(f"AI 이름 업데이트 완료: {self.ai_name}")
    
    def chat(
        self, 
        user_id: str, 
        message: str, 
        history: Optional[List[Dict]] = None,
        enable_tts: bool = False
    ) -> Dict:
        """
        사용자와 채팅 (대화형 할일 추출 + TTS 지원)
        
        Args:
            user_id: 사용자 ID
            message: 사용자 메시지
            history: 백엔드에서 전달받은 대화 기록 (선택)
            enable_tts: TTS 활성화 여부
            
        Returns:
            dict: {
                "response": "AI응답",
                "timestamp": "시간",
                "ai_name": "AI이름",
                "model_type": "모델타입",
                "has_todo": True/False,
                "step": "none" | "suggest" | "ask_date" | "saved" | "cancelled",
                "task": "병원 가기" (has_todo=True일 때만),
                "date": "내일" (has_todo=True일 때만),
                "time": "오전 10시" (has_todo=True일 때만),
                "tts_path": "audio.mp3" (enable_tts=True일 때만)
            }
        """
        try:
            # 1. 할일 추출 먼저 확인 (대화형)
            todo_result = self.todo_processor.process_message(message, user_id)
            
            # 2-1. 할일 관련 대화 (확인/날짜 물어보기 또는 저장 완료)
            if todo_result["response"] is not None:
                ai_response = todo_result["response"]
                
                # TTS 생성 (옵션)
                tts_path = None
                if enable_tts:
                    tts_path = self.openai_client.text_to_speech(ai_response)
                
                return {
                    "response": ai_response,
                    "timestamp": datetime.now().isoformat(),
                    "ai_name": self.ai_name,
                    "model_type": self.model_type,
                    "has_todo": todo_result["has_todo"],
                    "step": todo_result["step"],  # ✅ step 필드 추가!
                    "task": todo_result.get("task"),
                    "date": todo_result.get("date"),
                    "time": todo_result.get("time"),
                    "tts_path": tts_path
                }
            
            # 2-2. 일반 채팅
            else:
                # 시스템 프롬프트 설정
                system_prompt = get_prompt(
                    "chat",
                    model_type=self.model_type,
                    ai_name=self.ai_name
                )
                
                # 메시지 구성
                messages = [{"role": "system", "content": system_prompt}]
                
                # 대화 기록 추가
                if history:
                    messages.extend(history)
                
                # 현재 사용자 메시지 추가
                messages.append({"role": "user", "content": message})
                
                # OpenAI API 호출
                ai_response = self.openai_client.chat_completion(messages)
                
                # TTS 생성 (옵션)
                tts_path = None
                if enable_tts:
                    tts_path = self.openai_client.text_to_speech(ai_response)
                
                logger.info(
                    f"채팅 완료 - 사용자: {user_id}, "
                    f"모델: {self.model_type}, 메시지 길이: {len(message)}"
                )
                
                return {
                    "response": ai_response,
                    "timestamp": datetime.now().isoformat(),
                    "ai_name": self.ai_name,
                    "model_type": self.model_type,
                    "has_todo": False,
                    "step": "none",  # ✅ 일반 채팅은 step=none
                    "task": None,
                    "date": None,
                    "time": None,
                    "tts_path": tts_path
                }
            
        except Exception as e:
            logger.error(f"채팅 처리 중 오류 발생 - 사용자: {user_id}, 오류: {e}")
            error_response = "죄송해요, 잠시 문제가 생겼어요. 다시 한 번 말씀해 주시겠어요?"
            
            return {
                "response": error_response,
                "timestamp": datetime.now().isoformat(),
                "ai_name": self.ai_name,
                "model_type": self.model_type,
                "has_todo": False,
                "step": "none",
                "task": None,
                "date": None,
                "time": None,
                "tts_path": None
            }
    
    def generate_encouragement(self, user_id: str, context: str = "") -> str:
        """격려 메시지 생성"""
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
        """사용자 패턴 분석 및 피드백 생성"""
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
    try:
        print("="*50)
        print("손주톡톡 채팅 + 할일 추출 (step 포함) 테스트")
        print("="*50)
        
        chat_service = ChatService("손주", "friendly")
        
        # 테스트 1: 일반 채팅
        print("\n[테스트 1] 일반 채팅")
        r1 = chat_service.chat("user1", "안녕하세요!", enable_tts=False)
        print(f"step={r1['step']}, has_todo={r1['has_todo']}")
        print(f"💬 AI: {r1['response']}\n")
        
        # 테스트 2: 할일 추출 (날짜 있음)
        print("[테스트 2] 할일 추출 - 날짜 있음")
        r2 = chat_service.chat("user2", "내일 오전 10시에 병원 가야 해요", enable_tts=False)
        print(f"step={r2['step']}, has_todo={r2['has_todo']}")
        print(f"💬 AI: {r2['response']}")
        
        r3 = chat_service.chat("user2", "응", enable_tts=False)
        print(f"step={r3['step']}, has_todo={r3['has_todo']}")
        print(f"💬 AI: {r3['response']}")
        if r3['has_todo']:
            print(f"✅ 저장: {r3['task']} | {r3['date']} {r3['time']}\n")
        
        # 테스트 3: 할일 추출 (날짜 없음)
        print("[테스트 3] 할일 추출 - 날짜 없음")
        r4 = chat_service.chat("user3", "손주한테 전화해야 하는데", enable_tts=False)
        print(f"step={r4['step']}, has_todo={r4['has_todo']}")
        print(f"💬 AI: {r4['response']}")
        
        r5 = chat_service.chat("user3", "응", enable_tts=False)
        print(f"step={r5['step']}, has_todo={r5['has_todo']}")
        print(f"💬 AI: {r5['response']}")
        
        r6 = chat_service.chat("user3", "내일 오후 2시", enable_tts=False)
        print(f"step={r6['step']}, has_todo={r6['has_todo']}")
        print(f"💬 AI: {r6['response']}")
        if r6['has_todo']:
            print(f"✅ 저장: {r6['task']} | {r6['date']} {r6['time']}\n")
        
        print("="*50)
        print("테스트 완료!")
        print("="*50)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")