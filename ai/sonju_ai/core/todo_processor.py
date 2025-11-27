"""
손주톡톡 할일 추출 서비스
대화에서 자동으로 할일을 추출하는 AI 서비스 (대화형 상태 머신)
"""

import logging
import json
import re
from typing import Dict, Optional

from sonju_ai.utils.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class TodoProcessor:
    """
    할일 추출 전용 서비스 (대화형 상태 머신)
    
    백엔드 연동을 위한 step 필드:
    - "none": 할일 없음 (일반 대화)
    - "suggest": 할일 발견, 사용자에게 등록 여부 확인 중
    - "ask_date": 날짜 입력 대기 중
    - "saved": 할일 최종 저장 완료 (has_todo=True)
    - "cancelled": 사용자가 등록 거부함
    """

    def __init__(self) -> None:
        self.openai_client = OpenAIClient()
        # {user_id: {"state": "ask_confirm"|"ask_date", "task": str, "date": Optional[str], "time": Optional[str]}}
        self.pending_todos: Dict[str, Dict] = {}
        logger.info("할일 추출 서비스 초기화 완료 (대화형)")

    def process_message(self, user_input: str, user_id: str) -> Dict:
        """
        사용자 메시지를 처리하여 할일 추출 진행
        
        Args:
            user_input: 사용자 입력 텍스트
            user_id: 사용자 ID
            
        Returns:
            dict: {
                "has_todo": bool,           # 최종 저장(saved) 시에만 True
                "response": Optional[str],   # AI가 할일 관련 말할 내용
                "task": Optional[str],
                "date": Optional[str],       # 자연어 (예: "내일")
                "time": Optional[str],       # 자연어 (예: "오전 10시")
                "step": str,                 # "none" | "suggest" | "ask_date" | "saved" | "cancelled"
            }
        """
        try:
            # 1. 이미 진행 중인 할일이 있는지 확인
            if user_id in self.pending_todos:
                return self._handle_pending_todo(user_input, user_id)
            
            # 2. 새로운 할일 감지 (GPT 호출)
            detection_result = self._detect_new_todo(user_input)
            
            has_todo = bool(detection_result.get("has_todo"))
            task = detection_result.get("task")
            date = detection_result.get("date")
            time = detection_result.get("time")
            
            # 할일이 없거나 task가 명확하지 않으면 일반 대화
            if not (has_todo and task):
                if has_todo and not task:
                    logger.warning(
                        f"[TodoProcessor] has_todo=True인데 task 없음. "
                        f"입력: {user_input!r}"
                    )
                return {
                    "has_todo": False,
                    "response": None,
                    "task": None,
                    "date": None,
                    "time": None,
                    "step": "none",
                }
            
            # 할일 발견 → 확인 요청 단계
            self.pending_todos[user_id] = {
                "state": "ask_confirm",
                "task": task,
                "date": date,  # None 가능
                "time": time,  # None 가능
            }
            
            return {
                "has_todo": False,  # 아직 확정 전
                "response": f"지금 말씀하신 '{task}'를 할일로 등록해 둘까요?",
                "task": task,
                "date": date,
                "time": time,
                "step": "suggest",
            }
            
        except Exception as e:
            logger.error(f"[TodoProcessor] process_message 오류 - user_id={user_id}, err={e}")
            return {
                "has_todo": False,
                "response": None,
                "task": None,
                "date": None,
                "time": None,
                "step": "none",
            }
    
    def _handle_pending_todo(self, user_input: str, user_id: str) -> Dict:
        """대기 중인 할일 처리"""
        pending = self.pending_todos[user_id]
        state = pending["state"]
        
        # 1. 확인 단계 (등록 여부)
        if state == "ask_confirm":
            confirmation = self._parse_confirmation(user_input)
            
            if confirmation == "yes":
                task = pending["task"]
                date = pending["date"]
                time = pending["time"]
                
                # 날짜가 이미 있으면 바로 저장
                if date:
                    del self.pending_todos[user_id]
                    
                    msg = (
                        f"네, {date}"
                        + (f" {time}" if time else "")
                        + f"에 '{task}' 일정으로 등록해 둘게요."
                    )
                    return {
                        "has_todo": True,
                        "response": msg,
                        "task": task,
                        "date": date,
                        "time": time,
                        "step": "saved",
                    }
                
                # 날짜 없음 → 날짜 입력 단계로
                self.pending_todos[user_id]["state"] = "ask_date"
                return {
                    "has_todo": False,
                    "response": (
                        "할일을 등록하려면 날짜가 필요해요.\n"
                        "날짜를 알려주시면 추가해 드릴게요.\n"
                        "예: 내일, 내일 오전 10시, 11월 25일"
                    ),
                    "task": task,
                    "date": None,
                    "time": None,
                    "step": "ask_date",
                }
            
            elif confirmation == "no":
                # 거부
                del self.pending_todos[user_id]
                return {
                    "has_todo": False,
                    "response": "알겠어요, 일정으로는 따로 남기지 않을게요.",
                    "task": None,
                    "date": None,
                    "time": None,
                    "step": "cancelled",
                }
            
            else:
                # 불명확 → pending 제거, 일반 대화로
                del self.pending_todos[user_id]
                return {
                    "has_todo": False,
                    "response": None,
                    "task": None,
                    "date": None,
                    "time": None,
                    "step": "none",
                }
        
        # 2. 날짜 입력 단계
        elif state == "ask_date":
            datetime_result = self._parse_datetime(user_input)
            date = datetime_result.get("date")
            time = datetime_result.get("time")
            
            if date:
                task = pending["task"]
                del self.pending_todos[user_id]
                
                msg = (
                    f"네, {date}"
                    + (f" {time}" if time else "")
                    + f"에 '{task}' 일정으로 등록해 둘게요."
                )
                return {
                    "has_todo": True,
                    "response": msg,
                    "task": task,
                    "date": date,
                    "time": time,
                    "step": "saved",
                }
            
            # 날짜 파싱 실패 → pending 제거, 일반 대화로
            del self.pending_todos[user_id]
            return {
                "has_todo": False,
                "response": None,
                "task": None,
                "date": None,
                "time": None,
                "step": "none",
            }
        
        # 알 수 없는 상태
        else:
            del self.pending_todos[user_id]
            return {
                "has_todo": False,
                "response": None,
                "task": None,
                "date": None,
                "time": None,
                "step": "none",
            }
    
    def _detect_new_todo(self, user_input: str) -> Dict:
        """새로운 할일 감지 (GPT 호출)"""
        try:
            detection_prompt = """사용자 메시지에서 구체적인 일정이나 할일을 찾아주세요.

[추출 기준]
- 구체적인 "행동 + 대상"이 분명한 경우만 추출
  예: "병원 가야 해" → task: "병원 가기"
  예: "손주한테 전화해야 해" → task: "손주에게 전화하기"
  예: "도서관 가야 해" → task: "도서관 가기"

- 단순 시간 언급만 있고 무엇을 할지 불명확하면 제외
  예: "내일 9시에 가야 해" → 어디? 무엇? 불명확 → has_todo: false

[중요 규칙]
- task는 짧은 한국어로만 (예: "병원 가기", "손주에게 전화하기")
- task를 명확히 정할 수 없으면 has_todo: false

[응답 형식]
반드시 JSON만 출력. 설명 없이 JSON만.

{
  "has_todo": true,
  "task": "병원 가기",
  "date": "내일",
  "time": "오전 10시"
}

날짜/시간 없으면 해당 필드는 null.
할일 없으면 {"has_todo": false, "task": null, "date": null, "time": null}"""

            user_message = f'사용자 메시지: "{user_input}"\n\n위 메시지에서 할일을 찾아 JSON으로만 답변하세요.'
            response = self.openai_client.simple_chat(user_message, detection_prompt)
            result = self._parse_json_response(response)
            
            has_todo = bool(result.get("has_todo"))
            task = result.get("task") if has_todo else None
            date = result.get("date") if has_todo else None
            time = result.get("time") if has_todo else None
            
            return {
                "has_todo": has_todo,
                "task": task,
                "date": date,
                "time": time,
            }
            
        except Exception as e:
            logger.error(f"[TodoProcessor] 할일 감지 오류: {e}")
            return {"has_todo": False, "task": None, "date": None, "time": None}
    
    def _parse_confirmation(self, user_input: str) -> str:
        """확인 응답 파싱 (예/아니오)"""
        text = user_input.strip().lower()
        
        yes_keywords = [
            "응", "예", "네", "좋아", "그래", "맞아",
            "ok", "okay", "ㅇㅋ", "ㅇㅇ",
            "추가", "등록", "넣어", "해줘", "해 주세요",
            "기억해", "기억해줘",
        ]
        no_keywords = [
            "아니", "아냐", "안", "싫어", "그만",
            "no", "ㄴㄴ", "거절", "말아", "필요없", "괜찮아",
        ]
        
        if any(word in text for word in yes_keywords):
            return "yes"
        
        if any(word in text for word in no_keywords):
            return "no"
        
        return "unknown"
    
    def _parse_datetime(self, user_input: str) -> Dict:
        """날짜/시간 파싱 (GPT 호출)"""
        try:
            parse_prompt = """사용자가 입력한 날짜/시간을 추출해주세요.

[응답 형식]
JSON만 출력. 설명 없이 JSON만.

{
  "date": "내일",
  "time": "오전 10시"
}

시간 없으면 time은 null.
날짜 없으면 date와 time 모두 null."""

            user_message = f'사용자 입력: "{user_input}"\n\n날짜와 시간을 JSON으로만 답변하세요.'
            response = self.openai_client.simple_chat(user_message, parse_prompt)
            result = self._parse_json_response(response)
            
            date = result.get("date")
            time = result.get("time")
            return {"date": date, "time": time}
            
        except Exception as e:
            logger.error(f"[TodoProcessor] 날짜/시간 파싱 오류: {e}")
            return {"date": None, "time": None}
    
    def _parse_json_response(self, response: str) -> Dict:
        """GPT 응답에서 JSON 추출 및 파싱"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
            json_match = re.search(json_pattern, response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group().strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.error(f"[TodoProcessor] JSON 파싱 실패: {json_str[:150]}")
            
            logger.error(f"[TodoProcessor] JSON 파싱 실패: {response[:150]}")
            return {}


# 간단한 테스트 실행
if __name__ == "__main__":
    try:
        processor = TodoProcessor()
        
        print("=== 손주톡톡 할일 추출 테스트 (대화형) ===\n")
        
        # 테스트 시나리오 1: 날짜 있는 할일
        print("[시나리오 1] 날짜 있는 할일")
        r1 = processor.process_message("내일 오전 10시에 병원 가야 해요", "user1")
        print(f"step={r1['step']}, 💬 {r1['response']}")
        
        r2 = processor.process_message("응", "user1")
        print(f"step={r2['step']}, 💬 {r2['response']}")
        if r2['has_todo']:
            print(f"✅ 저장: {r2['task']} | {r2['date']} {r2['time']}\n")
        
        # 테스트 시나리오 2: 날짜 없는 할일
        print("[시나리오 2] 날짜 없는 할일")
        r3 = processor.process_message("손주한테 전화해야 하는데", "user2")
        print(f"step={r3['step']}, 💬 {r3['response']}")
        
        r4 = processor.process_message("응", "user2")
        print(f"step={r4['step']}, 💬 {r4['response']}")
        
        r5 = processor.process_message("내일 오후 2시", "user2")
        print(f"step={r5['step']}, 💬 {r5['response']}")
        if r5['has_todo']:
            print(f"✅ 저장: {r5['task']} | {r5['date']} {r5['time']}\n")
        
        # 테스트 시나리오 3: 거절
        print("[시나리오 3] 거절")
        r6 = processor.process_message("내일 운동 가야 해", "user3")
        print(f"step={r6['step']}, 💬 {r6['response']}")
        
        r7 = processor.process_message("아니", "user3")
        print(f"step={r7['step']}, 💬 {r7['response']}\n")
        
        print("="*50)
        print("테스트 완료!")
        print("="*50)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")