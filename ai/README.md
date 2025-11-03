# 손주톡톡 AI 모듈

손주톡톡 프로젝트의 AI 서비스 모듈입니다. 어르신을 위한 친근한 AI 어시스턴트 기능을 제공합니다.

## 주요 기능

- **AI 챗봇** - 4가지 성격 모델 선택 가능 (friendly(다정한) / active(활발한) / pleasant(유쾌한) / reliable(듬직한))
- **할일 추출** - 대화에서 자동으로 할일과 루틴 추출
- **건강 메모 분석** - 건강 상태 4단계 판정 (healthy/normal/warning/danger) + 처방전 OCR + 음성 메모 STT

## 프로젝트 구조

```
sonju_ai/
├── utils/openai_client.py     # OpenAI API 클라이언트
├── config/prompts.py          # 프롬프트 설정
├── core/
│   ├── chat_service.py        # 챗봇
│   ├── todo_processor.py      # 할일 추출
│   └── health_service.py      # 건강 메모 분석
└── tests/test_core.py         # 통합 테스트
```

## 설치 및 실행

### 의존성 설치
```bash
pip install -r requirements.txt
```

### 환경변수 설정
```bash
# .env.template 파일을 복사해 .env 파일 생성
cp .env.template .env

# .env 파일에 실제 API 키 입력
OPENAI_API_KEY=your_openai_api_key_here
```

### 테스트 실행
```bash
cd ai
python -m sonju_ai.tests.test_core
```

## 사용 예시

### 기본 채팅
```python
from sonju_ai.core.chat_service import ChatService

# 기본 초기화 (다정한 모델)
chat_service = ChatService("손주톡톡")

# 특정 모델로 초기화 (friendly, active, pleasant, reliable 중 선택)
chat_service = ChatService("손주톡톡", model_type="friendly")

response = chat_service.chat("user123", "안녕하세요!")
print(response["response"])
```

### 할일 추출
```python
from sonju_ai.core.todo_processor import TodoProcessor

todo_processor = TodoProcessor()

# 대화에서 할일 추출
user_input = "내일 오전 10시에 병원 가야 해요. 그리고 손주한테 전화도 해야겠어요."
result = todo_processor.extract_todos_from_conversation(user_input, "user123")

# 추출된 할일 확인
tasks = todo_processor.get_tasks_list(result)
for task in tasks:
    print(f"할일: {task['task']}, 시간: {task['time']}, 카테고리: {task['category']}")

# 사용자용 포맷
formatted_text = todo_processor.format_extracted_todos(result)
print(formatted_text)
```

### 건강 메모 분석
```python
from sonju_ai.core.health_service import HealthService

health_service = HealthService()

# 건강 메모 분석
result = health_service.analyze_health_memo("오늘 머리가 좀 아파요")
print(f"상태: {result['status']}")  # healthy, normal, warning, danger 중 하나
print(f"색상: {health_service.get_status_color(result['status'])}")  # 캘린더 색상 매핑

# 처방전 이미지에서 정보 추출
prescription_info = health_service.extract_prescription_info("prescription.jpg")
for medicine in prescription_info['medicines']:
    print(f"약: {medicine['name']}, 복용: {medicine['frequency']}")

# 음성 메모 텍스트 변환 + 건강 분석
voice_result = health_service.analyze_voice_memo("voice_memo.mp3")
print(f"텍스트: {voice_result['text']}, 상태: {voice_result['status']}")
```

## FastAPI 연동

```python
from fastapi import FastAPI
from pydantic import BaseModel
from sonju_ai.core.chat_service import ChatService
from sonju_ai.core.todo_processor import TodoProcessor
from sonju_ai.core.health_service import HealthService

# Request 모델 정의
class ChatRequest(BaseModel):
    user_id: str
    message: str

class TodoExtractionRequest(BaseModel):
    user_id: str
    message: str

class HealthMemoRequest(BaseModel):
    memo_text: str

app = FastAPI()

# AI 서비스 초기화
chat_service = ChatService("손주톡톡")
todo_processor = TodoProcessor()
health_service = HealthService()

# 지원 모델 조회 API
@app.get("/ai/models")
async def get_available_models():
    """사용 가능한 AI 모델 목록 반환"""
    from sonju_ai.config.prompts import get_available_models
    models = get_available_models()
    return {
        "models": [
            {"id": "friendly", "name": "다정한"},
            {"id": "active", "name": "활발한"},
            {"id": "pleasant", "name": "유쾌한"},
            {"id": "reliable", "name": "듬직한"}
        ]
    }

# 채팅 API
@app.post("/ai/chat")
async def chat(request: ChatRequest):
    response = chat_service.chat(request.user_id, request.message)
    return {"ai_response": response["response"]}

# 할일 추출 API
@app.post("/ai/todos/extract")
async def extract_todos(request: TodoExtractionRequest):
    result = todo_processor.extract_todos_from_conversation(
        request.message, request.user_id
    )
    return {
        "extracted_tasks": todo_processor.get_tasks_list(result),
        "formatted_text": todo_processor.format_extracted_todos(result)
    }

# 건강 메모 분석 API
@app.post("/ai/health/analyze")
async def analyze_health(request: HealthMemoRequest):
    result = health_service.analyze_health_memo(request.memo_text)
    return {
        "status": result["status"],
        "color": health_service.get_status_color(result["status"]),
        "timestamp": result["timestamp"]
    }
```