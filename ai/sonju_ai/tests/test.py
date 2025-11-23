"""
손주톡톡 할일 추출 서비스
대화에서 자동으로 할일을 추출하는 AI 서비스 (대화형)
"""

import logging
import json
import re
from typing import Dict, List, Optional
from datetime import datetime

from sonju_ai.utils.openai_client import OpenAIClient
from sonju_ai.config.prompts import get_prompt

logger = logging.getLogger(__name__)

class TodoProcessor:
    """할일 추출 전용 서비스 (대화형)"""
    
    def __init__(self):
        """할일 추출 서비스 초기화"""
        self.openai_client = OpenAIClient()
        self.pending_todos = {}  # {user_id: {"state": "ask_confirm", "task": "...", "date": None, "time": None}}
        logger.info("할일 추출 서비스 초기화 완료 (대화형)")
    
    def process_message(self, user_input: str, user_id: str) -> Dict:
        """
        사용자 메시지를 처리하여 할일 추출 진행
        
        Args:
            user_input: 사용자 입력 텍스트
            user_id: 사용자 ID
            
        Returns:
            dict: {
                "has_todo": True/False,
                "response": "AI 응답 메시지" (또는 None),
                "task": "병원 가기" (has_todo=True일 때만),
                "date": "내일" (has_todo=True일 때만),
                "time": "오전 10시" 또는 None (has_todo=True일 때만)
            }
        """
        try:
            # 1. 대기 중인 할일이 있는지 확인
            if user_id in self.pending_todos:
                return self._handle_pending_todo(user_input, user_id)
            
            # 2. 새로운 할일 감지
            detection_result = self._detect_new_todo(user_input)
            
            if detection_result["has_todo"]:
                # 할일 발견 → 확인 요청
                task = detection_result["task"]
                date = detection_result.get("date")
                time = detection_result.get("time")
                
                # 날짜가 있으면 바로 저장, 없으면 물어보기
                if date:
                    # 날짜 있음 → 확인만 받기
                    self.pending_todos[user_id] = {
                        "state": "ask_confirm",
                        "task": task,
                        "date": date,
                        "time": time
                    }
                    return {
                        "has_todo": False,
                        "response": f"{task}을(를) 할일에 추가하시겠습니까?",
                        "task": None,
                        "date": None,
                        "time": None
                    }
                else:
                    # 날짜 없음 → 확인 + 날짜 받기
                    self.pending_todos[user_id] = {
                        "state": "ask_confirm",
                        "task": task,
                        "date": None,
                        "time": None
                    }
                    return {
                        "has_todo": False,
                        "response": f"{task}을(를) 할일에 추가하시겠습니까?",
                        "task": None,
                        "date": None,
                        "time": None
                    }
            else:
                # 할일 없음 → 일반 대화
                return {
                    "has_todo": False,
                    "response": None,  # chat_service에서 처리
                    "task": None,
                    "date": None,
                    "time": None
                }
                
        except Exception as e:
            logger.error(f"할일 처리 중 오류 - 사용자: {user_id}, 오류: {e}")
            return {
                "has_todo": False,
                "response": None,
                "task": None,
                "date": None,
                "time": None
            }
    
    def _handle_pending_todo(self, user_input: str, user_id: str) -> Dict:
        """대기 중인 할일 처리"""
        pending = self.pending_todos[user_id]
        state = pending["state"]
        
        # 1. 확인 단계
        if state == "ask_confirm":
            confirmation = self._parse_confirmation(user_input)
            
            if confirmation == "yes":
                # 날짜가 있으면 바로 저장
                if pending["date"]:
                    task = pending["task"]
                    date = pending["date"]
                    time = pending["time"]
                    
                    # 상태 초기화
                    del self.pending_todos[user_id]
                    
                    # 저장 완료 메시지
                    if time:
                        response_msg = f"{date} {time}로 할일에 추가했어요!"
                    else:
                        response_msg = f"{date}로 할일에 추가했어요!"
                    
                    return {
                        "has_todo": True,
                        "response": response_msg,
                        "task": task,
                        "date": date,
                        "time": time
                    }
                else:
                    # 날짜 없음 → 날짜 물어보기
                    self.pending_todos[user_id]["state"] = "ask_date"
                    return {
                        "has_todo": False,
                        "response": "언제 가실 예정인가요? (예: 내일, 11월 25일, 내일 오후 3시)",
                        "task": None,
                        "date": None,
                        "time": None
                    }
            
            elif confirmation == "no":
                # 거절 → 상태 초기화
                del self.pending_todos[user_id]
                return {
                    "has_todo": False,
                    "response": "알겠어요!",
                    "task": None,
                    "date": None,
                    "time": None
                }
            
            else:
                # 불명확 → 다시 물어보기
                return {
                    "has_todo": False,
                    "response": "추가하시겠습니까? (예/아니요)",
                    "task": None,
                    "date": None,
                    "time": None
                }
        
        # 2. 날짜 입력 단계
        elif state == "ask_date":
            datetime_result = self._parse_datetime(user_input)
            
            if datetime_result["date"]:
                task = pending["task"]
                date = datetime_result["date"]
                time = datetime_result["time"]
                
                # 상태 초기화
                del self.pending_todos[user_id]
                
                # 저장 완료 메시지
                if time:
                    response_msg = f"{date} {time}로 할일에 추가했어요!"
                else:
                    response_msg = f"{date}로 할일에 추가했어요!"
                
                return {
                    "has_todo": True,
                    "response": response_msg,
                    "task": task,
                    "date": date,
                    "time": time
                }
            else:
                # 날짜 파싱 실패 → 다시 물어보기
                return {
                    "has_todo": False,
                    "response": "날짜를 다시 말씀해 주시겠어요? (예: 내일, 11월 25일, 내일 오후 3시)",
                    "task": None,
                    "date": None,
                    "time": None
                }
        
        # 알 수 없는 상태
        else:
            del self.pending_todos[user_id]
            return {
                "has_todo": False,
                "response": None,
                "task": None,
                "date": None,
                "time": None
            }
    
    def _detect_new_todo(self, user_input: str) -> Dict:
        """새로운 할일 감지 (GPT 호출)"""
        try:
            detection_prompt = """사용자 메시지에서 구체적인 일정이나 할일을 찾아주세요.

**추출 기준:**
- 구체적인 행동이나 일정이 있는 경우만
- "해야 해", "할 예정", "하려고 해" 등의 표현
- 단순한 과거 이야기는 제외

**JSON 형식으로만 답변:**
{
    "has_todo": true,
    "task": "병원 가기",
    "date": "내일",
    "time": "오전 10시"
}

날짜/시간이 없으면 해당 필드는 null로.
할일이 없으면 has_todo: false로."""

            user_message = f"사용자 메시지: \"{user_input}\"\n\n위 메시지에서 할일을 찾아주세요."
            
            response = self.openai_client.simple_chat(user_message, detection_prompt)
            result = self._parse_json_response(response)
            
            return result
            
        except Exception as e:
            logger.error(f"할일 감지 중 오류: {e}")
            return {"has_todo": False}
    
    def _parse_confirmation(self, user_input: str) -> str:
        """확인 응답 파싱 (예/아니오)"""
        text = user_input.strip().lower()
        
        # 긍정
        if any(word in text for word in ["응", "예", "네", "좋아", "ok", "okay", "ㅇㅋ", "ㅇㅇ", "그래", "추가"]):
            return "yes"
        
        # 부정
        if any(word in text for word in ["아니", "안", "싫어", "no", "ㄴㄴ", "거절", "말아"]):
            return "no"
        
        return "unknown"
    
    def _parse_datetime(self, user_input: str) -> Dict:
        """날짜/시간 파싱 (GPT 호출)"""
        try:
            parse_prompt = """사용자가 입력한 날짜/시간을 추출해주세요.

**JSON 형식으로만 답변:**
{
    "date": "내일",
    "time": "오전 10시"
}

시간이 없으면 time은 null로.
날짜를 찾을 수 없으면 date도 null로."""

            user_message = f"사용자 입력: \"{user_input}\"\n\n날짜와 시간을 추출해주세요."
            
            response = self.openai_client.simple_chat(user_message, parse_prompt)
            result = self._parse_json_response(response)
            
            return result
            
        except Exception as e:
            logger.error(f"날짜/시간 파싱 중 오류: {e}")
            return {"date": None, "time": None}
    
    def _parse_json_response(self, response: str) -> Dict:
        """GPT 응답에서 JSON 추출 및 파싱"""
        try:
            # 직접 파싱 시도
            return json.loads(response)
        except json.JSONDecodeError:
            # JSON 추출 시도
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group().strip()
                return json.loads(json_str)
            
            # 파싱 실패
            logger.error(f"JSON 파싱 실패: {response[:100]}")
            return {"has_todo": False}


# 간단한 테스트 실행
if __name__ == "__main__":
    try:
        processor = TodoProcessor()
        
        # 테스트 케이스들
        test_cases = [
            ("내일 오전 10시에 병원 가야 해요", "test_user_1"),
            ("응", "test_user_1"),
            ("손주한테 전화해야 하는데", "test_user_2"),
            ("응", "test_user_2"),
            ("내일", "test_user_2"),
        ]
        
        print("=== 손주톡톡 할일 추출 테스트 (대화형) ===\n")
        
        for user_input, user_id in test_cases:
            print(f"[{user_id}] 입력: {user_input}")
            
            result = processor.process_message(user_input, user_id)
            
            if result["has_todo"]:
                print(f"✅ 저장됨: {result['task']} ({result['date']}, {result['time']})")
                print(f"   AI 응답: {result['response']}\n")
            elif result["response"]:
                print(f"💬 AI 응답: {result['response']}\n")
            else:
                print(f"❌ 일반 대화 (할일 없음)\n")
        
    except Exception as e:
        print(f"테스트 중 오류: {e}")