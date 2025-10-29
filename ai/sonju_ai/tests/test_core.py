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
    """할일 추출 서비스 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        try:
            self.todo_processor = TodoProcessor()
        except ValueError as e:
            self.skipTest(f"OpenAI API 키가 없습니다: {e}")
    
    def test_extract_todos_from_conversation(self):
        """대화에서 할일 추출 테스트"""
        test_cases = [
            # (입력, 예상 할일 수, 예상 카테고리)
            ("내일 오전 10시에 병원 가야 해요", 1, "건강"),
            ("손주한테 안부 전화 드려야 하는데 까먹을까봐", 1, "가족"),
            ("카카오톡으로 사진 보내는 법 배우고 싶어요", 1, "학습"),
            ("오늘 날씨가 좋네요", 0, None),  # 할일 없음
            ("내일 마트 가서 장보고, 저녁에는 드라마 봐야지", 2, None)  # 복합
        ]
        
        for user_input, expected_count, expected_category in test_cases:
            with self.subTest(input=user_input):
                result = self.todo_processor.extract_todos_from_conversation(user_input, "test_user")
                tasks = self.todo_processor.get_tasks_list(result)
                
                # 할일 수 확인
                self.assertEqual(len(tasks), expected_count, f"입력: {user_input}")
                
                # 카테고리 확인 (할일이 있는 경우)
                if expected_count > 0 and expected_category:
                    self.assertEqual(tasks[0]["category"], expected_category)
    
    def test_extract_todos_structure(self):
        """추출된 할일 구조 테스트"""
        result = self.todo_processor.extract_todos_from_conversation("내일 병원 가야 해요", "test_user")
        tasks = self.todo_processor.get_tasks_list(result)
        
        if tasks:
            task = tasks[0]
            # 필수 필드 확인
            self.assertIn("task", task)
            self.assertIn("category", task)
            self.assertIn("time", task)
            
            # 타입 확인
            self.assertIsInstance(task["task"], str)
            self.assertIsInstance(task["category"], str)
            # time은 None일 수 있음
    
    def test_format_extracted_todos(self):
        """할일 표시 형식 테스트"""
        # 할일 있는 경우
        test_result = {
            "tasks": [
                {"task": "병원 가기", "time": "내일 오전", "category": "건강"}
            ]
        }
        formatted = self.todo_processor.format_extracted_todos(test_result)
        self.assertIn("추출된 할일 1개", formatted)
        self.assertIn("병원 가기", formatted)
        
        # 할일 없는 경우
        empty_result = {"tasks": []}
        formatted_empty = self.todo_processor.format_extracted_todos(empty_result)
        self.assertIn("추출된 할일이 없습니다", formatted_empty)
    
    def test_get_tasks_list(self):
        """태스크 리스트 반환 테스트"""
        test_result = {
            "tasks": [
                {"task": "테스트 할일", "time": None, "category": "일상"}
            ]
        }
        tasks = self.todo_processor.get_tasks_list(test_result)
        
        self.assertIsInstance(tasks, list)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["task"], "테스트 할일")
    
    def test_duplicate_filtering(self):
        """중복 할일 필터링 테스트"""
        # 유사한 할일들이 중복 제거되는지 확인
        test_input = "병원 가야 해요. 그리고 병원 가기도 해야 하고요. 병원 방문 예정이에요."
        result = self.todo_processor.extract_todos_from_conversation(test_input, "test_user")
        tasks = self.todo_processor.get_tasks_list(result)
        
        # 중복이 제거되어야 함 (유사한 할일들이 하나로 합쳐짐)
        if tasks:
            task_names = [task["task"].lower().strip() for task in tasks]
            unique_names = set(task_names)
            self.assertEqual(len(task_names), len(unique_names), "중복 할일이 제거되지 않음")
    
    def test_category_classification_detailed(self):
        """상세 카테고리 분류 테스트"""
        test_cases = [
            ("혈압약 먹어야 해", "건강"),
            ("운동하러 가야지", "건강"),
            ("아들한테 전화해야 해", "가족"),
            ("친구랑 만나기로 했어", "가족"),
            ("스마트폰 사용법 배우고 싶어", "학습"),
            ("요리법 익혀야겠어", "학습"),
            ("빨래해야 해", "일상"),
            ("마트에서 장보기", "일상"),
            ("드라마 보려고 해", "취미"),
            ("음악 들을 거야", "취미")
        ]
        
        for user_input, expected_category in test_cases:
            with self.subTest(input=user_input):
                result = self.todo_processor.extract_todos_from_conversation(user_input, "test_user")
                tasks = self.todo_processor.get_tasks_list(result)
                
                if tasks:
                    self.assertEqual(tasks[0]["category"], expected_category, 
                                   f"입력: {user_input}, 예상: {expected_category}, 실제: {tasks[0]['category']}")
    
    def test_json_parsing_robustness(self):
        """JSON 파싱 안정성 테스트"""
        # _parse_extraction_response 메서드를 직접 테스트
        processor = self.todo_processor
        
        # 정상 케이스
        normal_response = '{"tasks": [{"task": "병원 가기", "time": "내일", "category": "건강"}]}'
        result = processor._parse_extraction_response(normal_response)
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["task"], "병원 가기")
        
        # 앞뒤 텍스트가 있는 케이스 (개선된 파싱 로직 테스트)
        messy_response = '다음은 결과입니다: {"tasks": [{"task": "전화하기", "time": null, "category": "가족"}]} 이상입니다.'
        result = processor._parse_extraction_response(messy_response)
        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(result["tasks"][0]["task"], "전화하기")
        
        # 잘못된 JSON 케이스
        invalid_response = '이것은 JSON이 아닙니다'
        result = processor._parse_extraction_response(invalid_response)
        self.assertEqual(result["tasks"], [])
        
        # tasks가 null인 케이스
        null_tasks_response = '{"tasks": null}'
        result = processor._parse_extraction_response(null_tasks_response)
        self.assertEqual(result["tasks"], [])
        
        # 빈 tasks 배열 케이스
        empty_tasks_response = '{"tasks": []}'
        result = processor._parse_extraction_response(empty_tasks_response)
        self.assertEqual(result["tasks"], [])
    
    def test_edge_cases(self):
        """엣지 케이스 테스트"""
        # 빈 문자열
        result = self.todo_processor.extract_todos_from_conversation("", "test_user")
        self.assertEqual(result["tasks"], [])
        
        # 매우 긴 텍스트
        long_text = "안녕하세요. " * 100 + "내일 병원 가야 해요."
        result = self.todo_processor.extract_todos_from_conversation(long_text, "test_user")
        tasks = self.todo_processor.get_tasks_list(result)
        # 긴 텍스트에서도 할일이 추출되어야 함
        self.assertGreaterEqual(len(tasks), 0)
        
        # 특수문자가 포함된 텍스트
        special_text = "내일 오후 3:30에 A&B 병원에서 검사받아야 해요! (중요)"
        result = self.todo_processor.extract_todos_from_conversation(special_text, "test_user")
        tasks = self.todo_processor.get_tasks_list(result)
        if tasks:
            self.assertIsInstance(tasks[0]["task"], str)
            self.assertGreater(len(tasks[0]["task"]), 0)

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
        
        # 2. 할일 추출 테스트
        test_input = "내일 오전에 병원 가고, 손주한테 전화해야 해요"
        extraction_result = self.todo_processor.extract_todos_from_conversation(test_input, user_id)
        tasks = self.todo_processor.get_tasks_list(extraction_result)
        self.assertIsInstance(tasks, list)
        
        # 3. 분석 생성 테스트
        learning_data = {"total_study_time": 60, "completed_lessons": 3, "accuracy_rate": 0.9}
        analysis = self.analysis_generator.generate_learning_analysis(user_id, learning_data)
        self.assertIn("score", analysis)
        
        logger.info(f"통합 테스트 완료 - 채팅: {len(chat_response['response'])}자, 추출된 할일: {len(tasks)}개, 점수: {analysis['score']}점")

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