"""
손주톡톡 할일 처리 서비스
사용자 상태와 활동 기록을 바탕으로 하루 할일을 자동 생성
"""

import logging
import re
import json
from typing import List, Dict, Optional
from datetime import datetime, time

from sonju_ai.utils.openai_client import OpenAIClient
from sonju_ai.config.prompts import get_prompt

logger = logging.getLogger(__name__)

class TodoProcessor:
    """할일 생성 및 관리 서비스"""
    
    def __init__(self):
        """할일 처리 서비스 초기화"""
        self.openai_client = OpenAIClient()
        logger.info("할일 처리 서비스 초기화 완료")
    
    def generate_daily_todos(
        self, 
        user_id: str, 
        user_profile: Dict,
        activity_logs: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """
        하루 할일 목록 생성
        
        Args:
            user_id: 사용자 ID
            user_profile: 사용자 프로필 {"name": "김할머니", "age": 75, "interests": [...]}
            activity_logs: 활동 기록 {"recent_apps": [...], "learning_progress": {...}}
            
        Returns:
            list: [{"task": "할일내용", "category": "건강", "time": "오전", "priority": "보통"}]
        """
        try:
            # 사용자 정보 요약
            user_summary = self._create_user_summary(user_profile, activity_logs)
            
            # 할일 생성 프롬프트
            todo_prompt = get_prompt("todo")
            
            # AI에게 할일 생성 요청
            user_message = f"""
사용자 정보: {user_summary}

위 정보를 바탕으로 어르신에게 적합한 오늘의 할일 3-5개를 생성해주세요.

응답 형식 (JSON):
[
  {{"task": "할일 설명", "category": "건강|가족|학습|취미|일상", "time": "오전|오후|저녁", "priority": "높음|보통|낮음"}},
  ...
]
"""
            
            response = self.openai_client.simple_chat(user_message, todo_prompt)
            
            # JSON 파싱 시도
            todos = self._parse_todos_from_response(response)
            
            logger.info(f"할일 생성 완료 - 사용자: {user_id}, 생성된 할일: {len(todos)}개")
            return todos
            
        except Exception as e:
            logger.error(f"할일 생성 중 오류 - 사용자: {user_id}, 오류: {e}")
            return self._get_default_todos()
    
    def _create_user_summary(self, user_profile: Dict, activity_logs: Optional[Dict]) -> str:
        """사용자 정보를 요약문으로 변환"""
        summary_parts = []
        
        # 기본 프로필 정보
        if "name" in user_profile:
            summary_parts.append(f"이름: {user_profile['name']}")
        if "age" in user_profile:
            summary_parts.append(f"나이: {user_profile['age']}세")
        if "interests" in user_profile:
            interests = ", ".join(user_profile['interests'])
            summary_parts.append(f"관심사: {interests}")
        
        # 활동 기록 정보
        if activity_logs:
            if "recent_apps" in activity_logs:
                recent_apps = ", ".join(activity_logs['recent_apps'])
                summary_parts.append(f"최근 사용 앱: {recent_apps}")
            
            if "learning_progress" in activity_logs:
                progress = activity_logs['learning_progress']
                if "completed_lessons" in progress:
                    summary_parts.append(f"완료한 학습: {progress['completed_lessons']}개")
                if "weak_areas" in progress:
                    weak_areas = ", ".join(progress['weak_areas'])
                    summary_parts.append(f"연습이 필요한 영역: {weak_areas}")
        
        return ". ".join(summary_parts) if summary_parts else "기본 사용자"
    
    def _parse_todos_from_response(self, response: str) -> List[Dict[str, str]]:
        """AI 응답에서 할일 목록 파싱"""
        try:
            # JSON 부분 추출 시도
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                todos = json.loads(json_str)
                
                # 유효성 검증
                valid_todos = []
                for todo in todos:
                    if isinstance(todo, dict) and "task" in todo:
                        # 기본값 설정
                        valid_todo = {
                            "task": todo.get("task", ""),
                            "category": todo.get("category", "일상"),
                            "time": todo.get("time", "오후"),
                            "priority": todo.get("priority", "보통")
                        }
                        valid_todos.append(valid_todo)
                
                return valid_todos if valid_todos else self._get_default_todos()
            
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"할일 파싱 실패, 기본 할일 사용: {e}")
        
        # 파싱 실패시 텍스트에서 할일 추출
        return self._extract_todos_from_text(response)
    
    def _extract_todos_from_text(self, response: str) -> List[Dict[str, str]]:
        """텍스트에서 할일 추출 (fallback)"""
        todos = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            # 번호나 불릿 포인트로 시작하는 라인 찾기
            if any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '•', '*']):
                # 번호나 기호 제거
                task_text = re.sub(r'^[\d\.\-\•\*\s]+', '', line).strip()
                if task_text:
                    todos.append({
                        "task": task_text,
                        "category": "일상",
                        "time": "오후",
                        "priority": "보통"
                    })
        
        return todos if todos else self._get_default_todos()
    
    def _get_default_todos(self) -> List[Dict[str, str]]:
        """기본 할일 목록 (fallback)"""
        return [
            {
                "task": "오늘 하루 건강한 식사 챙기기",
                "category": "건강",
                "time": "오전",
                "priority": "높음"
            },
            {
                "task": "가족이나 친구에게 안부 전화드리기",
                "category": "가족",
                "time": "오후",
                "priority": "보통"
            },
            {
                "task": "스마트폰 새로운 기능 하나 배워보기",
                "category": "학습",
                "time": "오후",
                "priority": "보통"
            },
            {
                "task": "좋아하는 음악 들으며 휴식하기",
                "category": "취미",
                "time": "저녁",
                "priority": "낮음"
            }
        ]
    
    def prioritize_todos(self, todos: List[Dict], user_preferences: Dict) -> List[Dict]:
        """
        사용자 선호도에 따라 할일 우선순위 조정
        
        Args:
            todos: 할일 목록
            user_preferences: 선호도 {"morning_person": True, "health_focus": True}
            
        Returns:
            list: 우선순위가 조정된 할일 목록
        """
        try:
            # 우선순위 점수 계산
            for todo in todos:
                score = 50  # 기본 점수
                
                # 건강 관련 우선순위 증가
                if user_preferences.get("health_focus") and todo["category"] == "건강":
                    score += 30
                
                # 아침형 인간이면 오전 할일 우선순위 증가
                if user_preferences.get("morning_person") and todo["time"] == "오전":
                    score += 20
                
                # 기존 우선순위 반영
                priority_scores = {"높음": 30, "보통": 0, "낮음": -20}
                score += priority_scores.get(todo["priority"], 0)
                
                todo["_score"] = score
            
            # 점수순으로 정렬
            sorted_todos = sorted(todos, key=lambda x: x.get("_score", 0), reverse=True)
            
            # 점수 필드 제거
            for todo in sorted_todos:
                todo.pop("_score", None)
            
            logger.info(f"할일 우선순위 조정 완료: {len(sorted_todos)}개")
            return sorted_todos
            
        except Exception as e:
            logger.error(f"할일 우선순위 조정 중 오류: {e}")
            return todos
    
    def format_todos_for_display(self, todos: List[Dict]) -> str:
        """
        할일 목록을 사용자 친화적 텍스트로 변환
        
        Args:
            todos: 할일 목록
            
        Returns:
            str: 표시용 텍스트
        """
        if not todos:
            return "오늘은 충분히 휴식하세요!"
        
        formatted_lines = ["오늘의 할일"]
        
        time_groups = {"오전": [], "오후": [], "저녁": []}
        for todo in todos:
            time_groups[todo.get("time", "오후")].append(todo)
        
        for time_period, time_todos in time_groups.items():
            if time_todos:
                formatted_lines.append(f"\n{time_period}")
                for i, todo in enumerate(time_todos, 1):
                    priority_text = todo.get("priority", "보통")
                    formatted_lines.append(f"  {i}. [{priority_text}] {todo['task']}")
        
        return "\n".join(formatted_lines)


# 간단한 테스트 실행
if __name__ == "__main__":
    try:
        todo_processor = TodoProcessor()
        
        # 테스트 사용자 프로필
        test_profile = {
            "name": "할머니",
            "age": 75,
            "interests": ["요리", "가족", "건강"]
        }
        
        test_activity = {
            "recent_apps": ["카카오톡", "사진"],
            "learning_progress": {
                "completed_lessons": 3,
                "weak_areas": ["사진 전송"]
            }
        }
        
        # 할일 생성 테스트
        todos = todo_processor.generate_daily_todos("test_user", test_profile, test_activity)
        
        # 결과 출력
        formatted = todo_processor.format_todos_for_display(todos)
        print(formatted)
        
    except Exception as e:
        print(f"테스트 중 오류: {e}")