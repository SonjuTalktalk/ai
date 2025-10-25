"""
손주톡톡 AI 모듈 통합 테스트
모든 core 모듈들의 기능을 테스트
"""

import unittest
import logging
from typing import Dict, List

# 테스트할 모듈들 import
from sonju_ai.utils.openai_client import OpenAIClient
from sonju_ai.config.prompts import get_prompt
from sonju_ai.core.chat_service import ChatService
from sonju_ai.core.todo_processor import TodoProcessor
from sonju_ai.core.analysis_generator import AnalysisGenerator

# 테스트용 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestOpenAIClient(unittest.TestCase):
    """OpenAI 클라이언트 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        try:
            self.client = OpenAIClient()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_client_initialization(self):
        """클라이언트 초기화 테스트"""
        self.assertIsNotNone(self.client)
        self.assertEqual(self.client.model, "gpt-4o-mini")
    
    def test_simple_chat(self):
        """간단한 채팅 테스트"""
        response = self.client.simple_chat("안녕", "간단히 인사해주세요")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
    
    def test_connection(self):
        """연결 테스트"""
        result = self.client.test_connection()
        self.assertTrue(result)

class TestPrompts(unittest.TestCase):
    """프롬프트 설정 테스트"""
    
    def test_chat_prompt(self):
        """채팅 프롬프트 테스트"""
        prompt = get_prompt("chat", ai_name="테스트AI")
        self.assertIn("테스트AI", prompt)
        self.assertIn("어르신", prompt)
    
    def test_analysis_prompt(self):
        """분석 프롬프트 테스트"""
        prompt = get_prompt("analysis")
        self.assertIn("학습 데이터", prompt)
        self.assertIn("격려", prompt)
    
    def test_todo_prompt(self):
        """할일 프롬프트 테스트"""
        prompt = get_prompt("todo")
        self.assertIn("할일", prompt)
        self.assertIn("어르신", prompt)
    
    def test_invalid_prompt_type(self):
        """잘못된 프롬프트 타입 테스트"""
        with self.assertRaises(ValueError):
            get_prompt("invalid_type")

class TestChatService(unittest.TestCase):
    """채팅 서비스 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        try:
            self.chat_service = ChatService("테스트AI")
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_service_initialization(self):
        """서비스 초기화 테스트"""
        self.assertEqual(self.chat_service.ai_name, "테스트AI")
        self.assertIsInstance(self.chat_service.conversation_history, dict)
    
    def test_chat_basic(self):
        """기본 채팅 테스트"""
        response = self.chat_service.chat("test_user", "안녕하세요")
        
        self.assertIn("response", response)
        self.assertIn("timestamp", response)
        self.assertIn("ai_name", response)
        self.assertEqual(response["ai_name"], "테스트AI")
        self.assertIsInstance(response["response"], str)
        self.assertGreater(len(response["response"]), 0)
    
    def test_conversation_history(self):
        """대화 기록 테스트"""
        # 여러 번 대화
        self.chat_service.chat("test_user", "첫 번째 메시지")
        self.chat_service.chat("test_user", "두 번째 메시지")
        
        # 기록 확인
        history = self.chat_service.get_conversation_history("test_user")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["user_message"], "첫 번째 메시지")
        self.assertEqual(history[1]["user_message"], "두 번째 메시지")
    
    def test_clear_history(self):
        """기록 삭제 테스트"""
        self.chat_service.chat("test_user", "테스트 메시지")
        self.assertTrue(self.chat_service.clear_conversation_history("test_user"))
        
        history = self.chat_service.get_conversation_history("test_user")
        self.assertEqual(len(history), 0)
    
    def test_encouragement_generation(self):
        """격려 메시지 생성 테스트"""
        encouragement = self.chat_service.generate_encouragement("test_user", "새 기능 학습중")
        self.assertIsInstance(encouragement, str)
        self.assertGreater(len(encouragement), 0)

class TestTodoProcessor(unittest.TestCase):
    """할일 처리 서비스 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        try:
            self.todo_processor = TodoProcessor()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
        
        # 테스트 데이터
        self.test_profile = {
            "name": "김할머니",
            "age": 75,
            "interests": ["요리", "가족", "건강"]
        }
        
        self.test_activity = {
            "recent_apps": ["카카오톡", "사진"],
            "learning_progress": {
                "completed_lessons": 5,
                "weak_areas": ["사진 전송"]
            }
        }
    
    def test_generate_daily_todos(self):
        """할일 생성 테스트"""
        todos = self.todo_processor.generate_daily_todos("test_user", self.test_profile, self.test_activity)
        
        self.assertIsInstance(todos, list)
        self.assertGreater(len(todos), 0)
        
        # 첫 번째 할일 구조 확인
        if todos:
            todo = todos[0]
            self.assertIn("task", todo)
            self.assertIn("category", todo)
            self.assertIn("time", todo)
            self.assertIn("priority", todo)
    
    def test_prioritize_todos(self):
        """할일 우선순위 조정 테스트"""
        test_todos = [
            {"task": "스트레칭", "category": "건강", "time": "오전", "priority": "보통"},
            {"task": "전화하기", "category": "가족", "time": "오후", "priority": "높음"}
        ]
        
        preferences = {"health_focus": True, "morning_person": True}
        prioritized = self.todo_processor.prioritize_todos(test_todos, preferences)
        
        self.assertEqual(len(prioritized), 2)
        self.assertIsInstance(prioritized, list)
    
    def test_format_todos_display(self):
        """할일 표시 형식 테스트"""
        test_todos = [
            {"task": "테스트 할일", "category": "일상", "time": "오전", "priority": "보통"}
        ]
        
        formatted = self.todo_processor.format_todos_for_display(test_todos)
        self.assertIsInstance(formatted, str)
        self.assertIn("오늘의 할일", formatted)
        self.assertIn("테스트 할일", formatted)

class TestAnalysisGenerator(unittest.TestCase):
    """분석 생성 서비스 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        try:
            self.analysis_generator = AnalysisGenerator()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
        
        # 테스트 데이터
        self.test_learning_data = {
            "total_study_time": 120,
            "completed_lessons": 5,
            "accuracy_rate": 0.85,
            "app_usage": {"카카오톡": 20, "사진": 15},
            "weak_areas": ["사진 전송"],
            "strong_areas": ["전화 걸기"]
        }
    
    def test_generate_learning_analysis(self):
        """학습 분석 생성 테스트"""
        analysis = self.analysis_generator.generate_learning_analysis("test_user", self.test_learning_data)
        
        self.assertIn("analysis_text", analysis)
        self.assertIn("encouragement", analysis)
        self.assertIn("recommendations", analysis)
        self.assertIn("score", analysis)
        
        # 타입 확인
        self.assertIsInstance(analysis["analysis_text"], str)
        self.assertIsInstance(analysis["encouragement"], str)
        self.assertIsInstance(analysis["recommendations"], list)
        self.assertIsInstance(analysis["score"], int)
        
        # 점수 범위 확인
        self.assertGreaterEqual(analysis["score"], 0)
        self.assertLessEqual(analysis["score"], 100)
    
    def test_weekly_summary(self):
        """주간 요약 테스트"""
        week_data = [
            {"date": "2025-10-21", "study_time": 30, "completed_lessons": 2, "accuracy_rate": 0.8},
            {"date": "2025-10-22", "study_time": 45, "completed_lessons": 3, "accuracy_rate": 0.75}
        ]
        
        summary = self.analysis_generator.generate_weekly_summary("test_user", week_data)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)

class TestIntegration(unittest.TestCase):
    """통합 테스트 - 모듈들이 함께 작동하는지 확인"""
    
    def setUp(self):
        """테스트 준비"""
        try:
            self.chat_service = ChatService("통합테스트AI")
            self.todo_processor = TodoProcessor()
            self.analysis_generator = AnalysisGenerator()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_full_workflow(self):
        """전체 워크플로우 테스트"""
        user_id = "integration_test_user"
        
        # 1. 채팅 테스트
        chat_response = self.chat_service.chat(user_id, "안녕하세요!")
        self.assertIn("response", chat_response)
        
        # 2. 할일 생성 테스트
        user_profile = {"name": "테스트사용자", "age": 70, "interests": ["가족"]}
        todos = self.todo_processor.generate_daily_todos(user_id, user_profile)
        self.assertIsInstance(todos, list)
        
        # 3. 분석 생성 테스트
        learning_data = {"total_study_time": 60, "completed_lessons": 3, "accuracy_rate": 0.9}
        analysis = self.analysis_generator.generate_learning_analysis(user_id, learning_data)
        self.assertIn("score", analysis)
        
        logger.info(f"통합 테스트 완료 - 채팅: {len(chat_response['response'])}자, 할일: {len(todos)}개, 점수: {analysis['score']}점")

def run_basic_test():
    """기본 테스트 실행 (API 키 없이도 가능한 테스트들)"""
    print("=== 기본 기능 테스트 ===")
    
    # 프롬프트 테스트
    try:
        chat_prompt = get_prompt("chat", ai_name="테스트")
        print(f"✅ 프롬프트 생성 성공: {len(chat_prompt)}자")
    except Exception as e:
        print(f"❌ 프롬프트 테스트 실패: {e}")
    
    # 기본 클래스 초기화 테스트 (API 키 없이)
    try:
        # 환경변수 없어도 클래스 구조는 확인 가능
        print("✅ 모듈 import 성공")
    except Exception as e:
        print(f"❌ 모듈 import 실패: {e}")

def run_full_test():
    """전체 테스트 실행"""
    print("=== 전체 기능 테스트 ===")
    
    # unittest 실행
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 클래스들 추가
    test_classes = [
        TestOpenAIClient,
        TestPrompts,
        TestChatService,
        TestTodoProcessor,
        TestAnalysisGenerator,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 요약
    print(f"\n=== 테스트 결과 요약 ===")
    print(f"실행된 테스트: {result.testsRun}개")
    print(f"실패: {len(result.failures)}개")
    print(f"에러: {len(result.errors)}개")
    print(f"건너뛴 테스트: {len(result.skipped)}개")
    
    if result.wasSuccessful():
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️ 일부 테스트 실패")

if __name__ == "__main__":
    print("손주톡톡 AI 모듈 테스트 시작\n")
    
    # 기본 테스트 먼저 실행
    run_basic_test()
    print()
    
    # 사용자에게 전체 테스트 실행 여부 확인
    try:
        # API 키 확인
        client = OpenAIClient()
        print("OpenAI API 키 확인됨. 전체 테스트를 실행합니다.\n")
        run_full_test()
    except ValueError:
        print("OpenAI API 키가 없습니다. 기본 테스트만 실행됩니다.")
    except Exception as e:
        print(f"테스트 실행 중 오류: {e}")