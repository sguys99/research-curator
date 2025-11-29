# Research Curator 작업 일지

## Day 1: 프로젝트 셋업 & LLM 통합 (2025-11-28)

### 작업 계획

1. **핵심 인프라 구축**
   - 프로젝트 초기 구조 설정
   - 데이터베이스 모델 설계
   - 환경 설정 및 보안 모듈 구현
   - Docker 서비스 구성

2. **LLM 통합**
   - LiteLLM 기반 통합 클라이언트 구현
   - FastAPI 엔드포인트 설계
   - Chat Completion, Embedding 기능 구현

---

### 작업 결과

#### 1. Core 설정 모듈

**`src/app/core/config.py`** - 환경 변수 관리
- Pydantic Settings를 사용한 타입 안전한 설정 관리
- 주요 설정 항목:
  - Database (PostgreSQL) 연결 정보
  - Vector DB (Qdrant) 연결 정보
  - LLM 설정 (OpenAI, Anthropic Claude)
  - 검색 API (Serper, Brave)
  - SMTP 이메일 설정
  - JWT 인증 설정
  - 스케줄러 설정
- 개발/프로덕션 환경 분리 지원

**`src/app/core/security.py`** - JWT 기반 인증
- 매직 링크 토큰 생성 및 검증
- 액세스 토큰 생성 및 검증
- 비밀번호 해싱

#### 2. 데이터베이스 모델

**`src/app/db/models.py`** - SQLAlchemy ORM 모델
- **User**: 사용자 계정 관리
  - UUID v7 기반 ID
  - email (unique, indexed), name
  - created_at, last_login 타임스탬프

- **UserPreference**: 사용자 설정
  - 연구 분야 (research_fields)
  - 키워드 (keywords)
  - 소스 설정 (sources)
  - 콘텐츠 비율 (info_types: paper/news/report)
  - 이메일 설정 (email_time, daily_limit, email_enabled)

- **CollectedArticle**: 수집된 아티클
  - 제목, 콘텐츠, 요약
  - source_url (unique), source_type
  - 카테고리, 중요도 점수
  - Vector DB 참조 (vector_id)
  - 메타데이터 (JSON)

- **SentDigest**: 이메일 발송 이력
  - 사용자 ID, 아티클 ID 목록
  - 발송 시간, 오픈 여부 추적

- **Feedback**: 사용자 피드백
  - 평점 (1-5), 코멘트
  - 사용자 및 아티클 참조

**`src/app/db/session.py`** - 데이터베이스 세션 관리
- SQLAlchemy async 엔진 설정
- Connection pooling (pool_size: 20, max_overflow: 10)
- FastAPI 의존성 함수 `get_db()` 제공

#### 3. LLM 통합 (핵심 추가 작업)

**`src/app/llm/client.py`** - LiteLLM 기반 통합 클라이언트
- **LLMClient 클래스**
  - 멀티 프로바이더 지원 (OpenAI, Claude)
  - LiteLLM을 통한 통일된 인터페이스
  - 주요 메서드:
    - `chat_completion()`: 동기 채팅 완성
    - `achat_completion()`: 비동기 채팅 완성
    - `generate_embedding()`: 동기 임베딩 생성
    - `agenerate_embedding()`: 비동기 임베딩 생성
  - JSON 응답 포맷 지원 (OpenAI JSON mode)
  - 자동 JSON 파싱 및 검증

- **설정 가능한 파라미터**
  - provider: "openai" | "claude"
  - model: 모델 명 (선택적, 기본값 설정에서 가져옴)
  - temperature: 0.0 ~ 1.0
  - max_tokens: 응답 최대 토큰 수

- **캐싱**
  - `get_llm_client()`: LRU 캐시를 사용한 클라이언트 인스턴스 재사용

**`src/app/api/routers/llm.py`** - LLM API 엔드포인트
- **POST `/llm/chat/completions`**
  - 범용 채팅 완성 엔드포인트
  - OpenAI/Claude 선택 가능
  - 메시지 기반 대화형 인터페이스

- **POST `/llm/embeddings`**
  - 텍스트 임베딩 생성
  - OpenAI embedding 모델 사용
  - 벡터 차원 정보 반환

- **POST `/llm/summarize`**
  - 아티클 요약 생성
  - 다국어 지원 (한국어/영어)
  - 요약 길이 제어 (문장 수 지정)

- **POST `/llm/analyze`**
  - 연구 아티클 분석
  - 동시 처리 (asyncio.gather):
    - 메타데이터 추출 (카테고리, 중요도, 키워드, 분야)
    - 한국어 요약 생성
  - JSON 응답 자동 파싱

**`src/app/api/schemas/llm.py`** - Pydantic 스키마
- **ChatMessage**: 채팅 메시지 (role, content)
- **ChatCompletionRequest/Response**: 채팅 완성 요청/응답
- **EmbeddingRequest/Response**: 임베딩 요청/응답
- **ArticleSummaryRequest/Response**: 요약 요청/응답
- **ArticleAnalysisRequest/Response**: 분석 요청/응답
- 각 스키마에 예제 포함

#### 4. FastAPI 애플리케이션

**`src/app/api/main.py`** - FastAPI 엔트리포인트
- CORS 미들웨어 설정 (로컬 개발 포트 허용)
- Health check 엔드포인트:
  - `GET /`: 서비스 정보 (name, version, status)
  - `GET /health`: 헬스 체크
- LLM 라우터 등록 (`/llm`)
- 자동 API 문서 생성 (Swagger UI, ReDoc)

#### 5. Docker 서비스

**`docker-compose.yml`**
- **PostgreSQL**
  - 이미지: postgres:17
  - 포트: 5433:5432
  - Volume: `./postgres_data` (영속성 보장)

- **Qdrant Vector DB**
  - 이미지: qdrant/qdrant:latest
  - 포트: 6333 (HTTP), 6334 (gRPC)
  - Volume: `./qdrant_data`

#### 6. 데이터베이스 마이그레이션

**Alembic 설정**
- `alembic/env.py`: 자동으로 `.env`에서 DATABASE_URL 로드
- `alembic.ini`: 마이그레이션 기본 설정
- 환경 변수 기반 동적 설정

#### 7. 환경 변수 설정

**.env.example - 환경 변수 템플릿**
```bash
# Application
APP_NAME="Research Curator"
ENVIRONMENT=development
DEBUG=True

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/research_curator

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# LLM
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Search APIs
SERPER_API_KEY=xxx
BRAVE_API_KEY=xxx

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
```

#### 8. 문서화

- **`docs/LLM_INTEGRATION.md`**: LLM 통합 가이드
- **`examples/llm_usage_example.py`**: LLMClient 사용 예제
- **`notebooks/test_llm_client.ipynb`**: Jupyter 노트북 기반 대화형 테스트

#### 9. 테스트

**`tests/test_llm_client.py`**
- LLMClient 단위 테스트
- pytest 기반 비동기 테스트
- Mock을 사용한 외부 API 격리

---

### 설치된 주요 패키지

```toml
dependencies = [
    "fastapi>=0.121.3",
    "sqlalchemy>=2.0.44",
    "alembic>=1.17.2",
    "asyncpg>=0.31.0",
    "psycopg2-binary>=2.9.11",

    # LLM
    "litellm>=1.80.0",
    "openai>=2.8.1",

    # Security
    "python-jose>=3.5.0",
    "passlib>=1.7.4",

    # Vector DB
    "qdrant-client>=1.16.1",

    # Utils
    "pydantic>=2.12.4",
    "pydantic-settings>=2.12.0",
    "uuid7>=0.1.0",
]
```

---

### 최종 디렉토리 구조

```
research-curator/
├── src/app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # 환경 설정
│   │   └── security.py        # 인증 로직
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py          # SQLAlchemy 모델
│   │   └── session.py         # DB 세션 관리
│   ├── llm/                   # 신규 추가
│   │   ├── __init__.py
│   │   └── client.py          # LLM 통합 클라이언트
│   └── api/
│       ├── __init__.py
│       ├── main.py            # FastAPI 앱
│       ├── schemas/           # 신규 추가
│       │   ├── __init__.py
│       │   └── llm.py         # LLM 스키마
│       └── routers/
│           ├── __init__.py
│           └── llm.py         # LLM 라우터
│
├── docs/
│   └── LLM_INTEGRATION.md     # 신규 추가
│
├── examples/
│   └── llm_usage_example.py   # 신규 추가
│
├── notebooks/
│   └── test_llm_client.ipynb  # 신규 추가
│
├── tests/
│   └── test_llm_client.py     # 신규 추가
│
├── alembic/                   # DB 마이그레이션
├── docker-compose.yml         # Docker 서비스
├── .env                       # 환경 변수 (개발)
├── .env.example              # 환경 변수 템플릿
└── pyproject.toml            # 프로젝트 설정
```

---

### 실행 방법

#### 1. 환경 설정
```bash
# 가상 환경 활성화
source .venv/bin/activate

# 패키지 동기화
uv sync
```

#### 2. Docker 서비스 시작
```bash
# PostgreSQL & Qdrant 시작
docker compose up -d

# 서비스 상태 확인
docker compose ps
```

#### 3. 환경 변수 설정
```bash
# .env 파일 생성 (없는 경우)
cp .env.example .env

# .env 파일 편집 (필수 항목)
# - OPENAI_API_KEY
# - DATABASE_URL
# - JWT_SECRET_KEY
```

#### 4. FastAPI 서버 실행
```bash
# 개발 모드 (자동 재시작)
uvicorn src.app.api.main:app --reload
```

#### 5. API 테스트
```bash
# Health check
curl http://localhost:8000/health

# Swagger 문서
open http://localhost:8000/docs
```

---

### 테스트 결과

#### Health Check
```json
// GET http://localhost:8000/
{
  "name": "Research Curator",
  "version": "1.0.0",
  "status": "running"
}

// GET http://localhost:8000/health
{
  "status": "healthy"
}
```

#### LLM API 예제
```bash
# Chat Completion
curl -X POST http://localhost:8000/llm/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is machine learning?"}
    ],
    "provider": "openai"
  }'

# Embedding
curl -X POST http://localhost:8000/llm/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "text": "AI research trends in 2024"
  }'

# Summarization (Korean)
curl -X POST http://localhost:8000/llm/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "title": "GPT-5 Performance",
    "content": "...",
    "language": "ko"
  }'
```

---

### 주요 성과

1. **완전한 프로젝트 인프라 구축**
   - 데이터베이스, Vector DB, API 서버 모두 정상 작동
   - Docker 기반 재현 가능한 개발 환경

2. **LLM 통합 완료**
   - LiteLLM을 통한 멀티 프로바이더 지원 (OpenAI, Claude)
   - 4개의 REST API 엔드포인트 구현
   - 비동기 처리로 성능 최적화

3. **확장 가능한 아키텍처**
   - 모듈화된 구조 (core, db, llm, api)
   - 의존성 주입 패턴 적용
   - 타입 안전성 (Pydantic, SQLAlchemy 2.0)

4. **문서화 및 테스트**
   - 통합 가이드 작성
   - 실행 가능한 예제 코드 제공
   - 단위 테스트 작성

---

### 다음 단계 (Day 2)

1. **데이터 수집 모듈 구현** (`src/app/collectors/`)
   - arXiv 논문 수집기
   - Google Scholar 수집기
   - 뉴스 수집기

2. **데이터 처리 파이프라인** (`src/app/processors/`)
   - LLM 기반 요약 생성
   - 중요도 평가
   - 카테고리 분류
   - 임베딩 생성 및 Qdrant 저장

3. **API 엔드포인트 확장**
   - 사용자 관리 (CRUD)
   - 매직 링크 인증
   - 아티클 CRUD
   - 검색 API

4. **데이터베이스 마이그레이션**
   - Alembic 마이그레이션 생성
   - 초기 데이터 시딩
