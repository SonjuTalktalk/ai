# 손주톡톡 AI 모듈

손주톡톡 프로젝트의 AI 서비스 모듈입니다. 어르신을 위한 친근한 AI 어시스턴트 기능을 제공합니다.

## 주요 기능

- **친근한 채팅** - 손주처럼 따뜻한 대화
- **할일 추천** - 사용자 맞춤형 데일리 투두 생성
- **학습 분석** - 활동 패턴 분석 및 격려 메시지
- **격려 시스템** - 상황별 맞춤형 응원 메시지

## 프로젝트 구조

```
sonju_ai/
├── utils/openai_client.py     # OpenAI API 클라이언트
├── config/prompts.py          # 프롬프트 설정
├── core/
│   ├── chat_service.py        # 채팅 서비스
│   ├── todo_processor.py      # 할일 생성
│   └── analysis_generator.py  # 학습 분석
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

chat_service = ChatService("손주톡톡")
response = chat_service.chat("user123", "안녕하세요!")
print(response["response"])
```

### 할일 생성
```python
from sonju_ai.core.todo_processor import TodoProcessor

todo_processor = TodoProcessor()
user_profile = {"name": "김할머니", "age": 75, "interests": ["요리", "가족"]}
todos = todo_processor.generate_daily_todos("user123", user_profile)
```

### 학습 분석
```python
from sonju_ai.core.analysis_generator import AnalysisGenerator

analyzer = AnalysisGenerator()
learning_data = {"total_study_time": 120, "completed_lessons": 5, "accuracy_rate": 0.85}
analysis = analyzer.generate_learning_analysis("user123", learning_data)
```

## FastAPI 연동

```python
from fastapi import FastAPI
from pydantic import BaseModel
from sonju_ai.core.chat_service import ChatService
from sonju_ai.core.todo_processor import TodoProcessor
from sonju_ai.core.analysis_generator import AnalysisGenerator

# Request 모델 정의
class ChatRequest(BaseModel):
    user_id: str
    message: str

class TodoRequest(BaseModel):
    user_id: str
    user_profile: dict
    activity_logs: dict | None = None

class AnalysisRequest(BaseModel):
    user_id: str
    learning_data: dict

app = FastAPI()

# AI 서비스 초기화
chat_service = ChatService("손주톡톡")
todo_processor = TodoProcessor()
analysis_generator = AnalysisGenerator()

# 채팅 API
@app.post("/ai/chat")
async def chat(request: ChatRequest):
    response = chat_service.chat(request.user_id, request.message)
    return {"ai_response": response["response"]}

# 할일 생성 API
@app.post("/ai/todos")
async def generate_todos(request: TodoRequest):
    todos = todo_processor.generate_daily_todos(
        request.user_id, request.user_profile, request.activity_logs
    )
    return {"todos": todos}

# 학습 분석 API
@app.post("/ai/analysis")
async def analyze_learning(request: AnalysisRequest):
    analysis = analysis_generator.generate_learning_analysis(
        request.user_id, request.learning_data
    )
    return analysis
```