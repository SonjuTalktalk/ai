"""
OpenAI API 클라이언트
손주톡톡 AI 모듈의 OpenAI API 통신 담당
"""
import os
import logging
from typing import Optional, List, Dict
from openai import OpenAI, APIConnectionError, AuthenticationError, RateLimitError
from dotenv import load_dotenv

# 환경 변수 로드 (프로그램 전체에서 한 번만)
load_dotenv()

# 로깅 설정 (다른 모듈에서도 일관되게 사용 가능)
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class OpenAIClient:
    """손주톡톡용 OpenAI API 클라이언트"""
    
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(self, model: Optional[str] = None):
        """OpenAI 클라이언트 초기화"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model or self.DEFAULT_MODEL
        logger.info(f"OpenAI 클라이언트 초기화 완료 (모델: {self.model})")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 300,
        temperature: float = 0.7
    ) -> str:
        """
        채팅 완성 API 호출
        
        Args:
            messages: [{"role": "user", "content": "..."}]
            max_tokens: 최대 토큰 수
            temperature: 응답 창의성 (0.0~1.0)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            result = response.choices[0].message.content.strip()
            logger.debug(f"API 호출 성공 (토큰: {response.usage.total_tokens})")
            return result
            
        except AuthenticationError:
            logger.error("OpenAI API 키 인증 오류")
            return "API 키가 올바르지 않습니다. 설정을 확인해주세요."
        except RateLimitError:
            logger.warning("API 요청 한도 초과")
            return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
        except APIConnectionError:
            logger.error("OpenAI API 연결 오류")
            return "인터넷 연결을 확인해주세요."
        except Exception as e:
            logger.exception(f"OpenAI API 처리 중 예상치 못한 오류: {e}")
            return "죄송해요, 잠시 생각이 안 나네요. 다시 한 번 말씀해 주시겠어요?"
    
    def simple_chat(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """간단한 1회 채팅"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})
        return self.chat_completion(messages)
    
    def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            response = self.simple_chat("테스트", "OK라고 답해주세요.")
            success = bool(response) and "오류" not in response
            logger.info(f"연결 테스트: {'성공' if success else '실패'}")
            return success
        except Exception as e:
            logger.error(f"연결 테스트 중 오류: {e}")
            return False

        
# 파일 실행 테스트
if __name__ == "__main__":
    client = OpenAIClient()
    print(client.simple_chat("안녕!"))