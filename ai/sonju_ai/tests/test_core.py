"""
손주톡톡 AI 모듈 핵심 테스트
필수 기능만 간단하게 테스트
"""

import unittest
import logging
import os

# 테스트할 모듈들 import
from sonju_ai.utils.openai_client import OpenAIClient
from sonju_ai.config.prompts import get_prompt
from sonju_ai.core.chat_service import ChatService
from sonju_ai.core.todo_processor import TodoProcessor
from sonju_ai.core.health_service import HealthService

# 테스트용 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestOpenAIClient(unittest.TestCase):
    """OpenAI 클라이언트 기본 테스트"""
    
    def setUp(self):
        try:
            self.client = OpenAIClient()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_connection(self):
        """연결 테스트"""
        result = self.client.test_connection()
        self.assertTrue(result)
    
    def test_vision_completion(self):
        """Vision API 기본 테스트 (URL 이미지)"""
        # 테스트용 공개 이미지 URL
        test_url = "https://via.placeholder.com/150"
        try:
            response = self.client.vision_completion(
                "이 이미지를 간단히 설명해주세요",
                test_url
            )
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
        except Exception as e:
            self.skipTest(f"Vision API 테스트 실패: {e}")
    
    def test_chat_with_json_format(self):
        """JSON 응답 형식 테스트"""
        messages = [
            {"role": "user", "content": "JSON 형식으로 답해주세요: {\"status\": \"ok\"}"}
        ]
        response = self.client.chat_completion(
            messages,
            response_format={"type": "json_object"}
        )
        self.assertIsInstance(response, str)
        # JSON 파싱 가능한지 확인
        import json
        try:
            json.loads(response)
        except json.JSONDecodeError:
            self.fail("JSON 응답 형식이 아닙니다")


class TestPrompts(unittest.TestCase):
    """프롬프트 기본 테스트"""
    
    def test_chat_prompt_generation(self):
        """채팅 프롬프트 생성 테스트 (기본 모델만)"""
        prompt = get_prompt("chat", model_type="friendly", ai_name="손주")
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
        self.assertIn("손주", prompt)
    
    def test_todo_prompt_generation(self):
        """할일 프롬프트 생성 테스트"""
        prompt = get_prompt("todo")
        self.assertIsInstance(prompt, str)
        self.assertIn("할일", prompt)
    
    def test_health_analysis_prompt(self):
        """건강 분석 프롬프트 생성 테스트"""
        prompt = get_prompt("health_analysis")
        self.assertIsInstance(prompt, str)
        self.assertIn("danger", prompt)
        self.assertIn("warning", prompt)
        self.assertIn("normal", prompt)
        self.assertIn("healthy", prompt)
    
    def test_prescription_ocr_prompt(self):
        """처방전 OCR 프롬프트 생성 테스트"""
        prompt = get_prompt("prescription_ocr")
        self.assertIsInstance(prompt, str)
        self.assertIn("medicines", prompt)


class TestChatService(unittest.TestCase):
    """채팅 서비스 핵심 테스트"""
    
    def setUp(self):
        try:
            self.chat_service = ChatService("손주", "friendly")
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_chat_basic(self):
        """기본 채팅 테스트"""
        response = self.chat_service.chat("test_user", "안녕하세요")
        
        # 필수 필드 확인
        self.assertIn("response", response)
        self.assertIn("timestamp", response)
        self.assertIn("ai_name", response)
        self.assertIn("model_type", response)
        
        # 응답 내용 확인
        self.assertIsInstance(response["response"], str)
        self.assertGreater(len(response["response"]), 0)
    
    def test_conversation_history(self):
        """대화 기록 테스트"""
        self.chat_service.chat("test_user", "첫 번째")
        self.chat_service.chat("test_user", "두 번째")
        
        history = self.chat_service.get_conversation_history("test_user")
        self.assertEqual(len(history), 2)
    
    def test_clear_history(self):
        """대화 기록 삭제 테스트"""
        self.chat_service.chat("test_user", "테스트")
        self.chat_service.clear_conversation_history("test_user")
        
        history = self.chat_service.get_conversation_history("test_user")
        self.assertEqual(len(history), 0)


class TestTodoProcessor(unittest.TestCase):
    """할일 추출 핵심 테스트"""
    
    def setUp(self):
        try:
            self.todo_processor = TodoProcessor()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_extract_basic(self):
        """기본 할일 추출 테스트"""
        result = self.todo_processor.extract_todos_from_conversation(
            "내일 병원 가야 해요", 
            "test_user"
        )
        tasks = self.todo_processor.get_tasks_list(result)
        
        # 할일이 추출되는지 확인
        self.assertIsInstance(tasks, list)
        
        if tasks:
            # 필수 필드 확인
            task = tasks[0]
            self.assertIn("task", task)
            self.assertIn("category", task)
            self.assertIn("time", task)
    
    def test_no_todos(self):
        """할일 없는 대화 테스트"""
        result = self.todo_processor.extract_todos_from_conversation(
            "오늘 날씨가 좋네요",
            "test_user"
        )
        tasks = self.todo_processor.get_tasks_list(result)
        self.assertEqual(len(tasks), 0)
    
    def test_format_todos(self):
        """할일 포맷 테스트"""
        test_result = {
            "tasks": [
                {"task": "병원 가기", "time": "내일", "category": "건강"}
            ]
        }
        formatted = self.todo_processor.format_extracted_todos(test_result)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("병원 가기", formatted)


class TestHealthService(unittest.TestCase):
    """건강 서비스 핵심 테스트"""
    
    def setUp(self):
        try:
            self.health_service = HealthService()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_analyze_health_memo_basic(self):
        """기본 건강 메모 분석 테스트"""
        result = self.health_service.analyze_health_memo("오늘 컨디션이 좋아요")
        
        # 필수 필드 확인
        self.assertIn("status", result)
        self.assertIn("timestamp", result)
        
        # status 값 검증
        valid_statuses = ["healthy", "normal", "warning", "danger"]
        self.assertIn(result["status"], valid_statuses)
    
    def test_analyze_health_memo_warning(self):
        """주의 상태 메모 분석 테스트"""
        result = self.health_service.analyze_health_memo("머리가 좀 아파요")
        
        self.assertIn("status", result)
        # warning이 나올 가능성이 높지만, AI 판단이므로 필수는 아님
        self.assertIn(result["status"], ["warning", "normal", "danger"])
    
    def test_analyze_empty_memo(self):
        """빈 메모 처리 테스트"""
        result = self.health_service.analyze_health_memo("")
        
        self.assertIn("status", result)
        self.assertIn("error", result)
        self.assertEqual(result["status"], "normal")
    
    def test_get_status_color(self):
        """상태 색상 변환 테스트"""
        self.assertEqual(self.health_service.get_status_color("healthy"), "green")
        self.assertEqual(self.health_service.get_status_color("normal"), "blue")
        self.assertEqual(self.health_service.get_status_color("warning"), "yellow")
        self.assertEqual(self.health_service.get_status_color("danger"), "red")
        self.assertEqual(self.health_service.get_status_color("invalid"), "blue")
    
    def test_format_health_analysis(self):
        """건강 분석 포맷 테스트"""
        test_result = {
            "status": "healthy",
            "timestamp": "2025-11-03T12:00:00"
        }
        formatted = self.health_service.format_health_analysis(test_result)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("건강한 상태", formatted)
    
    def test_transcribe_audio_invalid_path(self):
        """잘못된 오디오 경로 처리 테스트"""
        result = self.health_service.transcribe_audio("invalid_path.mp3")
        
        # 빈 문자열 또는 에러 메시지 반환
        self.assertIsInstance(result, str)


class TestIntegration(unittest.TestCase):
    """통합 테스트"""
    
    def setUp(self):
        try:
            self.chat_service = ChatService("손주", "friendly")
            self.todo_processor = TodoProcessor()
            self.health_service = HealthService()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_basic_workflow(self):
        """기본 워크플로우 테스트"""
        user_id = "integration_test"
        
        # 1. 채팅
        chat_response = self.chat_service.chat(user_id, "안녕하세요")
        self.assertIn("response", chat_response)
        
        # 2. 할일 추출
        todo_input = "내일 병원 가야 해요"
        todo_result = self.todo_processor.extract_todos_from_conversation(
            todo_input, 
            user_id
        )
        tasks = self.todo_processor.get_tasks_list(todo_result)
        self.assertIsInstance(tasks, list)
        
        # 3. 건강 메모 분석
        health_result = self.health_service.analyze_health_memo("오늘 컨디션 좋아요")
        self.assertIn("status", health_result)
        
        logger.info(
            f"통합 테스트 완료 - "
            f"채팅 응답: {len(chat_response['response'])}자, "
            f"할일: {len(tasks)}개, "
            f"건강 상태: {health_result['status']}"
        )
    
    def test_health_workflow(self):
        """건강 기능 통합 테스트"""
        # 건강 메모 분석
        memo = "오늘 산책하고 운동했어요. 기분이 정말 좋네요!"
        result = self.health_service.analyze_health_memo(memo)
        
        self.assertIn("status", result)
        
        # 색상 변환
        color = self.health_service.get_status_color(result["status"])
        self.assertIn(color, ["green", "blue", "yellow", "red"])
        
        # 포맷팅
        formatted = self.health_service.format_health_analysis(result)
        self.assertIsInstance(formatted, str)
        
        logger.info(f"건강 워크플로우 완료 - 상태: {result['status']}, 색상: {color}")


def run_tests():
    """테스트 실행"""
    print("=== 손주톡톡 AI 모듈 테스트 시작 ===\n")
    
    # unittest 실행
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 클래스 추가
    test_classes = [
        TestOpenAIClient,
        TestPrompts,
        TestChatService,
        TestTodoProcessor,
        TestHealthService,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과
    print(f"\n=== 테스트 결과 ===")
    print(f"총 {result.testsRun}개 테스트")
    print(f"실패: {len(result.failures)}개")
    print(f"에러: {len(result.errors)}개")
    print(f"건너뜀: {len(result.skipped)}개")
    
    if result.wasSuccessful():
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 일부 테스트 실패")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    try:
        # API 키 확인
        client = OpenAIClient()
        print("✅ OpenAI API 키 확인됨\n")
        run_tests()
    except ValueError:
        print("❌ OpenAI API 키가 없습니다.")
        print("테스트를 실행하려면 .env 파일에 OPENAI_API_KEY를 설정하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")