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

---

## Day 3: 데이터 수집 파이프라인 구현 (2025-12-01)

### 작업 계획

Day 3의 목표는 다양한 소스(arXiv, 뉴스 등)에서 AI 관련 콘텐츠를 자동으로 수집하는 파이프라인을 구축하는 것입니다.

**핵심 작업:**
1. Base Collector 인터페이스 설계
2. 재시도 로직 및 에러 핸들링 구현
3. Serper/Brave Search API 통합
4. arXiv 논문 수집기 구현
5. 뉴스 수집기 구현
6. 데이터 수집 API 엔드포인트 구현
7. 통합 테스트 및 검증

---

### 작업 결과

#### 1. Base Collector 인터페이스

**`src/app/collectors/base.py`** - 추상 베이스 클래스

**주요 구성 요소:**

- **SourceType Enum**: 콘텐츠 유형 정의
  - `PAPER`: 학술 논문
  - `NEWS`: 뉴스 기사
  - `REPORT`: 리서치 리포트
  - `BLOG`: 블로그 포스트
  - `OTHER`: 기타

- **CollectedData 데이터클래스**: 표준화된 수집 데이터 구조
  ```python
  @dataclass
  class CollectedData:
      title: str                    # 제목
      content: str                  # 본문 또는 요약
      url: str                      # 원문 URL
      source_type: SourceType       # 콘텐츠 유형
      source_name: str              # 소스 이름 (예: "arXiv", "TechCrunch")
      metadata: Dict[str, Any]      # 추가 메타데이터
      collected_at: datetime        # 수집 시간
  ```

- **BaseCollector 추상 클래스**: 모든 수집기의 기본 인터페이스
  - `collect()`: 추상 메서드, 각 수집기가 구현
  - `_create_collected_data()`: 헬퍼 메서드, 데이터 생성 표준화

- **커스텀 예외 클래스**:
  - `CollectorError`: 베이스 예외
  - `RateLimitError`: Rate limiting 예외
  - `APIError`: API 호출 실패 예외

**설계 철학:**
- 모든 수집기가 동일한 데이터 형식 반환
- 확장 가능한 구조 (새 소스 추가 용이)
- 타입 안전성 (Enum, dataclass 활용)

---

#### 2. 재시도 로직 및 에러 핸들링

**`src/app/core/retry.py`** - 재시도 유틸리티

**retry_with_backoff 데코레이터:**
```python
@retry_with_backoff(
    max_retries=3,           # 최대 재시도 횟수
    initial_delay=1.0,       # 초기 지연 시간 (초)
    max_delay=60.0,          # 최대 지연 시간
    backoff_factor=2.0,      # 지연 시간 증가 배수
    exceptions=(Exception,)  # 재시도할 예외 타입
)
async def fetch_data():
    # API 호출
    pass
```

**특징:**
- **Exponential Backoff**: 재시도 간격이 지수적으로 증가
  - 1차 실패: 1초 대기
  - 2차 실패: 2초 대기
  - 3차 실패: 4초 대기
- **동기/비동기 함수 모두 지원**: 자동 감지
- **상세한 로깅**: 각 재시도 시 로그 기록
- **설정 가능한 예외 타입**: 특정 예외만 재시도

**RateLimiter 클래스:**
```python
rate_limiter = RateLimiter(max_calls=10, time_window=60.0)
await rate_limiter.acquire()  # 호출 전 대기
```

**특징:**
- 시간 윈도우 내 최대 호출 횟수 제한
- 자동 대기 (rate limit 초과 시)
- API 서비스 보호

---

#### 3. Search API 통합

**`src/app/collectors/search_client.py`** - Serper/Brave Search 클라이언트

**SearchClient 클래스:**

**Serper API 지원:**
```python
results = await search_client.serper_search(
    query="transformer optimization",
    num_results=10,
    search_type="search",  # search, news, scholar
    date_filter="w"        # d(day), w(week), m(month)
)
```

**Brave Search API 지원:**
```python
results = await search_client.brave_search(
    query="GPT-4 news",
    num_results=10,
    search_type="web",     # web, news
    freshness="pw"         # pd, pw, pm
)
```

**주요 기능:**
- **멀티 프로바이더**: Serper와 Brave를 통일된 인터페이스로 제공
- **자동 재시도**: `@retry_with_backoff` 데코레이터 적용
- **Rate Limiting**: API 호출 빈도 자동 제어
- **에러 처리**:
  - 429: Rate limit 예외
  - 401: 인증 실패 예외
  - 기타: 일반 API 에러
- **결과 파싱**: 각 API의 응답을 표준 형식으로 변환

**파싱된 결과 형식:**
```python
{
    "title": "...",
    "snippet": "...",
    "link": "...",
    "date": "...",
    "source": "..."
}
```

---

#### 4. arXiv Collector

**`src/app/collectors/arxiv.py`** - arXiv 논문 수집기

**ArxivCollector 클래스:**

**사용 예시:**
```python
collector = ArxivCollector()
papers = await collector.collect(
    query="large language model",
    limit=10,
    filters={
        "categories": ["cs.AI", "cs.LG"],
        "sort_by": "relevance",       # relevance, last_updated, submitted
        "sort_order": "descending"    # ascending, descending
    }
)
```

**지원 기능:**
- **arXiv 공식 API 사용**: 무료, 안정적
- **카테고리 필터링**: AI, ML, NLP 등 세부 분야 선택
- **정렬 옵션**: 관련도, 최신순, 제출일순
- **풍부한 메타데이터 수집**:
  - arXiv ID
  - 저자 목록
  - 주요 카테고리 및 전체 카테고리
  - 발행일, 업데이트일
  - PDF URL
  - DOI, Journal Reference

**수집 데이터 구조:**
```python
CollectedData(
    title="Attention Is All You Need",
    content="초록 전문...",
    url="http://arxiv.org/abs/1706.03762",
    source_type=SourceType.PAPER,
    source_name="arXiv",
    metadata={
        "arxiv_id": "1706.03762",
        "authors": ["Ashish Vaswani", ...],
        "primary_category": "cs.CL",
        "categories": ["cs.CL", "cs.AI"],
        "published": "2017-06-12T17:57:34+00:00",
        "pdf_url": "https://arxiv.org/pdf/1706.03762"
    }
)
```

**인기 AI 카테고리 목록:**
```python
["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE", "cs.RO", "stat.ML"]
```

---

#### 5. News Collector

**`src/app/collectors/news.py`** - 뉴스 수집기

**NewsCollector 클래스:**

**사용 예시:**
```python
collector = NewsCollector(search_provider="serper")
articles = await collector.collect(
    query="artificial intelligence",
    limit=10,
    filters={
        "domains": ["techcrunch.com", "venturebeat.com"],
        "date_filter": "w"  # 최근 1주일
    }
)
```

**기본 뉴스 도메인:**
- `techcrunch.com` - 스타트업/기술 뉴스
- `venturebeat.com` - AI/테크 뉴스
- `technologyreview.com` - MIT Technology Review
- `theverge.com` - 테크 뉴스
- `wired.com` - 테크/문화
- `arstechnica.com` - 기술 분석
- `zdnet.com` - 엔터프라이즈 기술

**주요 기능:**
- **도메인 필터링**: 신뢰할 수 있는 소스만 선택
- **검색 쿼리 자동 구성**: `site:` 연산자 활용
- **Search API 통합**: Serper 또는 Brave 선택 가능
- **날짜 필터**: 최근 뉴스만 수집

**도메인 쿼리 생성 예시:**
```python
# 입력
query = "GPT-4"
domains = ["techcrunch.com", "venturebeat.com"]

# 생성된 쿼리
"GPT-4 (site:techcrunch.com OR site:venturebeat.com)"
```

---

#### 6. 데이터 수집 API 엔드포인트

**`src/app/api/schemas/collectors.py`** - Pydantic 스키마

**주요 스키마:**

1. **CollectionRequest**: 수집 요청
```python
{
    "query": "transformer optimization",
    "sources": ["arxiv", "news"],  # Optional
    "limit": 10,
    "filters": {
        "categories": ["cs.AI"],
        "domains": ["techcrunch.com"]
    }
}
```

2. **CollectionResponse**: 수집 결과
```python
{
    "total": 15,
    "results": [...],
    "errors": []
}
```

3. **CollectedItemResponse**: 개별 아이템
```python
{
    "title": "...",
    "content": "...",
    "url": "...",
    "source_type": "paper",
    "source_name": "arXiv",
    "metadata": {...},
    "collected_at": "2024-12-01T10:00:00"
}
```

**`src/app/api/routers/collectors.py`** - API 라우터

**API 엔드포인트:**

**1. POST `/api/collectors/search`** - 통합 검색
- 여러 소스를 동시에 검색
- 소스 지정 가능 (미지정 시 전체 검색)
- 각 소스별 에러 개별 처리
- 부분 성공 지원 (일부 소스 실패해도 성공한 결과 반환)

**2. POST `/api/collectors/arxiv`** - arXiv 전용
- arXiv 논문만 검색
- 카테고리, 정렬 필터 지원

**3. POST `/api/collectors/news`** - 뉴스 전용
- 뉴스 기사만 검색
- 도메인, 날짜 필터 지원

**4. GET `/api/collectors/sources`** - 소스 목록
- 지원되는 모든 소스 정보
- 각 소스별 필터 옵션 정보

**CollectorRegistry:**
- 모든 수집기를 중앙 집중식으로 관리
- 동적으로 수집기 추가/제거 가능
- 소스 정보 제공

---

#### 7. 통합 테스트

**테스트 결과:**

**1. Health Check**
```bash
$ curl http://localhost:8000/health
{"status": "healthy"}
```

**2. 소스 목록 조회**
```bash
$ curl http://localhost:8000/api/collectors/sources
{
  "sources": [
    {
      "name": "arxiv",
      "type": "paper",
      "description": "Academic papers from arXiv.org",
      "supported_filters": ["categories", "sort_by", "sort_order"]
    },
    {
      "name": "news",
      "type": "news",
      "description": "Tech and AI news articles",
      "supported_filters": ["domains", "date_filter", "freshness"]
    }
  ]
}
```

**3. arXiv 논문 수집**
```bash
$ curl -X POST http://localhost:8000/api/collectors/arxiv \
  -H "Content-Type: application/json" \
  -d '{
    "query": "large language model",
    "limit": 3,
    "filters": {
      "categories": ["cs.AI", "cs.LG"]
    }
  }'

# 결과: 3개의 관련 논문 성공적으로 수집
# - "Demystifying Instruction Mixing for Fine-tuning Large Language Models"
# - "WizardLM: Empowering large pre-trained language models..."
# - "PB-LLM: Partially Binarized Large Language Models"
```

**4. 통합 검색**
```bash
$ curl -X POST http://localhost:8000/api/collectors/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "GPT-4",
    "sources": ["arxiv"],
    "limit": 2
  }'

# 결과: 2개의 GPT-4 관련 논문 수집 성공
```

**5. Swagger UI**
- URL: `http://localhost:8000/docs`
- 모든 엔드포인트 정상 작동
- 대화형 API 테스트 가능

---

### 최종 디렉토리 구조

```
research-curator/
├── src/app/
│   ├── collectors/              # 신규 추가
│   │   ├── __init__.py
│   │   ├── base.py             # BaseCollector 인터페이스
│   │   ├── search_client.py    # Serper/Brave API 클라이언트
│   │   ├── arxiv.py            # arXiv 수집기
│   │   └── news.py             # 뉴스 수집기
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── retry.py            # 신규 추가: 재시도 로직
│   │
│   └── api/
│       ├── schemas/
│       │   ├── llm.py
│       │   └── collectors.py   # 신규 추가
│       │
│       └── routers/
│           ├── llm.py
│           └── collectors.py   # 신규 추가
│
└── pyproject.toml              # arxiv 패키지 추가
```

---

### 설치된 패키지

```toml
dependencies = [
    # 기존 패키지...
    "arxiv>=2.3.1",              # 신규 추가
    "feedparser>=6.0.12",        # arxiv 의존성
    "sgmllib3k==1.0.0",          # feedparser 의존성
]
```

---

### 주요 성과

#### 1. 완전한 데이터 수집 파이프라인 구축
- **모듈화된 구조**: 각 소스별 독립적인 Collector
- **표준화된 인터페이스**: BaseCollector 추상 클래스
- **확장 가능성**: 새 소스 추가 용이 (Google Scholar, Reports 등)

#### 2. 견고한 에러 핸들링
- **자동 재시도**: Exponential backoff 전략
- **Rate Limiting**: API 호출 빈도 자동 제어
- **부분 실패 허용**: 일부 소스 실패해도 다른 소스는 정상 수집

#### 3. RESTful API 제공
- **4개의 엔드포인트**: 통합 검색, arXiv, 뉴스, 소스 목록
- **OpenAPI 문서 자동 생성**: Swagger UI
- **타입 안전성**: Pydantic 스키마

#### 4. 실전 테스트 완료
- arXiv에서 실제 논문 수집 성공
- 모든 API 엔드포인트 정상 작동 확인
- Swagger UI를 통한 대화형 테스트 가능

---

### 다음 단계 (Day 4)

**Day 4 목표: LLM 통합 및 데이터 처리**

1. **데이터 처리 모듈** (`src/app/processors/`)
   - `summarizer.py`: LLM 기반 한국어 요약 생성
   - `evaluator.py`: 중요도 평가 (LLM + 메타데이터)
   - `classifier.py`: 카테고리 분류
   - `embedder.py`: 임베딩 생성

2. **프롬프트 설계**
   - 요약 생성 프롬프트 (한국어)
   - 중요도 평가 프롬프트
   - 카테고리 분류 프롬프트

3. **배치 처리 최적화**
   - 여러 아티클 동시 처리
   - 비용 최적화

4. **테스트**
   - 수집된 데이터로 LLM 처리 테스트
   - 품질 검증

---

### 참고 사항

**API 키 설정:**
```bash
# .env 파일에 추가 필요
SERPER_API_KEY=your-serper-api-key-here
BRAVE_API_KEY=your-brave-api-key-here
```

**실행 방법:**
```bash
# 서버 시작
uvicorn app.api.main:app --reload

# API 문서 확인
open http://localhost:8000/docs

# 테스트 요청
curl -X POST http://localhost:8000/api/collectors/arxiv \
  -H "Content-Type: application/json" \
  -d '{"query": "GPT", "limit": 5}'
```

**로깅:**
- 모든 수집 작업은 로그 기록
- 재시도 시도 및 실패 정보 포함
- 디버깅 및 모니터링 용이

---

## Day 4: LLM 통합 및 데이터 처리 파이프라인 구축 (2025-12-03)

### 작업 계획

Day 4의 목표는 수집된 아티클을 LLM으로 자동 처리하는 완전한 파이프라인을 구축하는 것입니다.

**핵심 작업:**
1. 프롬프트 관리 시스템 구현
2. 4개 프로세서 모듈 구현
   - ArticleSummarizer (요약 생성)
   - ImportanceEvaluator (중요도 평가)
   - ContentClassifier (카테고리 분류)
   - TextEmbedder (임베딩 생성)
3. 통합 파이프라인 구현
4. API 엔드포인트 구현
5. 통합 테스트 작성
6. 문서화 및 검증

---

### 작업 결과

#### 1. 프롬프트 관리 시스템

**`configs/prompts.yaml`** - 중앙 집중식 프롬프트 관리

**프롬프트 카테고리 (6개):**

1. **summarize**: 요약 생성 프롬프트
   - 언어별 (korean, english)
   - 길이별 (short, medium, long)
   ```yaml
   summarize:
     korean:
       medium:
         system: "당신은 AI 연구 분야의 전문 리서처입니다..."
         user_template: "다음 내용을 3-5문장으로 요약해주세요..."
   ```

2. **evaluate_importance**: 중요도 평가
   - 4가지 기준 평가 (혁신성, 관련성, 영향력, 시의성)
   - JSON 응답 형식

3. **classify_category**: 카테고리 분류
   - 5개 카테고리 (paper, news, report, blog, other)
   - 키워드 및 연구 분야 추출

4. **extract_metadata**: 메타데이터 추출
   - 저자, 출판일, 기관 등

5. **onboarding**: 온보딩 챗봇
   - 사용자 설정 수집

6. **common**: 공통 지시사항
   - 응답 형식 가이드라인

**`src/app/core/prompts.py`** - PromptManager 클래스

**주요 기능:**
- YAML 파일에서 프롬프트 로드
- 템플릿 변수 치환
- 메시지 빌드 (system + user)
- 싱글톤 패턴 (`get_prompt_manager()`)

**사용 예시:**
```python
pm = get_prompt_manager()
messages = pm.build_messages(
    "summarize",
    "korean.medium",
    title="GPT-4",
    content="..."
)
```

---

#### 2. 프로세서 모듈 구현

**`src/app/processors/`** - 데이터 처리 모듈

##### 2.1 ArticleSummarizer

**`src/app/processors/summarizer.py`**

**주요 기능:**
- 한국어/영어 요약 생성
- 3가지 길이 옵션 (short: 2-3문장, medium: 3-5문장, long: 6-8문장)
- 배치 처리 지원

**API:**
```python
summarizer = ArticleSummarizer(provider="openai")
summary = await summarizer.summarize(
    title="Attention Is All You Need",
    content="We propose the Transformer...",
    language="ko",
    length="medium"
)
```

**특징:**
- LiteLLM 통합 (OpenAI, Claude 선택 가능)
- 비동기 처리
- 배치 처리로 성능 최적화

---

##### 2.2 ImportanceEvaluator

**`src/app/processors/evaluator.py`**

**평가 방식:**
- **LLM 평가 (70%)**: 4가지 기준
  - Innovation (혁신성): 0.0-1.0
  - Relevance (관련성): 0.0-1.0
  - Impact (영향력): 0.0-1.0
  - Timeliness (시의성): 0.0-1.0

- **메타데이터 평가 (30%)**: 인용수, 연도 등
  - 인용수 점수: log scale
  - 시간 점수: 최근일수록 높음

**최종 점수:**
```
final_score = 0.7 × llm_score + 0.3 × metadata_score
```

**API:**
```python
evaluator = ImportanceEvaluator()
result = await evaluator.evaluate(
    title="GPT-4 Technical Report",
    content="...",
    metadata={"year": 2023, "citations": 5000}
)
# {
#   "innovation": 0.9,
#   "relevance": 0.85,
#   "impact": 0.9,
#   "timeliness": 0.8,
#   "final_score": 0.86,
#   "llm_score": 0.88,
#   "metadata_score": 0.8,
#   "reasoning": "..."
# }
```

---

##### 2.3 ContentClassifier

**`src/app/processors/classifier.py`**

**분류 기능:**
- **카테고리 분류**: paper, news, report, blog, other
- **키워드 추출**: 핵심 키워드 5-10개
- **연구 분야 식별**: Machine Learning, NLP, Computer Vision 등
- **세부 분야 추출**: Deep Learning, Transformer 등

**폴백 로직:**
- LLM 실패 시 URL/소스 기반 분류
- arXiv → paper
- 뉴스 도메인 → news

**API:**
```python
classifier = ContentClassifier()
result = await classifier.classify(
    title="Attention Is All You Need",
    content="We propose the Transformer...",
    source_name="arXiv",
    url="https://arxiv.org/abs/1706.03762"
)
# {
#   "category": "paper",
#   "confidence": 1.0,
#   "keywords": ["Transformer", "Attention", "NLP"],
#   "research_field": "Machine Learning",
#   "sub_fields": ["Deep Learning", "NLP"]
# }
```

---

##### 2.4 TextEmbedder

**`src/app/processors/embedder.py`**

**임베딩 생성:**
- OpenAI text-embedding-3-small (1536 차원)
- SHA-256 기반 캐싱
- 배치 처리 지원

**아티클 임베딩 최적화:**
```python
text = f"""
제목: {title}
요약: {summary}
내용: {content[:1000]}
"""
```

**API:**
```python
embedder = TextEmbedder(use_cache=True)

# 단일 텍스트
embedding = await embedder.embed("Attention Is All You Need")
# [0.01, -0.02, ...] (1536 dims)

# 아티클 전용
embedding = await embedder.embed_article_async(
    title="GPT-4",
    content="...",
    summary="..."
)
```

**캐시 관리:**
- `clear_cache()`: 캐시 초기화
- `get_cache_size()`: 캐시 크기 확인

---

#### 3. 통합 처리 파이프라인

**`src/app/processors/pipeline.py`** - ProcessingPipeline

**ProcessedArticle 데이터클래스:**
```python
@dataclass
class ProcessedArticle:
    # 원본
    title: str
    content: str
    url: str
    source_name: str
    source_type: str

    # 처리 결과
    summary: str                    # 요약
    importance_score: float         # 최종 중요도 (0.0-1.0)
    category: str                   # 카테고리
    keywords: list[str]             # 키워드
    research_field: str             # 연구 분야
    embedding: list[float]          # 1536차원 벡터

    # 상세 평가
    innovation_score: float
    relevance_score: float
    impact_score: float
    timeliness_score: float

    # 메타데이터
    metadata: dict
    processed_at: datetime
```

**처리 순서 (최적화):**
1. **병렬 실행** (asyncio.gather):
   - 요약 생성
   - 중요도 평가
   - 카테고리 분류
2. **순차 실행**:
   - 임베딩 생성 (요약 사용)

**API:**
```python
pipeline = ProcessingPipeline(
    provider="openai",
    summary_language="ko",
    summary_length="medium"
)

# 단일 아티클 처리
result = await pipeline.process_article(
    title="Attention Is All You Need",
    content="...",
    url="https://arxiv.org/abs/1706.03762",
    metadata={"year": 2017, "citations": 50000}
)

# 배치 처리 (병렬)
results = await pipeline.process_batch(
    articles=[
        {"title": "Paper 1", "content": "..."},
        {"title": "Paper 2", "content": "..."}
    ],
    max_concurrent=5
)
```

**성능:**
- 단일 아티클: ~3.7초
- 배치 5개: ~8.6초 (평균 1.7초/개, 53% 성능 향상)

**유틸리티 함수:**
- `get_top_articles()`: 중요도 순 정렬
- `filter_by_category()`: 카테고리 필터링
- `filter_by_score()`: 점수 기준 필터링
- `get_statistics()`: 통계 정보

---

#### 4. API 엔드포인트 구현

**`src/app/api/schemas/processors.py`** - Pydantic 스키마

**10개 스키마 정의:**
1. `SummarizeRequest/Response` - 요약 생성
2. `EvaluateRequest/Response` - 중요도 평가
3. `ClassifyRequest/Response` - 카테고리 분류
4. `ProcessArticleRequest/Response` - 단일 처리
5. `BatchProcessRequest/Response` - 배치 처리
6. `StatisticsResponse` - 통계

**모든 스키마에 포함:**
- Field 설명 (description)
- 예제 데이터 (json_schema_extra)
- 타입 검증

**`src/app/api/routers/processors.py`** - API 라우터

**6개 엔드포인트:**

1. **POST `/api/processors/summarize`**
   - 요약 생성
   - 한국어/영어, short/medium/long

2. **POST `/api/processors/evaluate`**
   - 중요도 평가
   - 4가지 점수 + 최종 점수 반환

3. **POST `/api/processors/classify`**
   - 카테고리 분류
   - 키워드, 연구 분야 추출

4. **POST `/api/processors/process`**
   - 전체 파이프라인 처리
   - 요약+평가+분류+임베딩 한 번에

5. **POST `/api/processors/batch-process`**
   - 배치 처리 (최대 10개 동시)
   - 처리 시간, 성공/실패 개수 반환

6. **POST `/api/processors/statistics`**
   - 처리 결과 통계
   - 카테고리 분포, 평균 점수 등

**에러 핸들링:**
- HTTPException 사용
- 상세한 에러 메시지
- 500 에러 자동 처리

---

#### 5. 통합 테스트

**`tests/test_processors.py`** - 프로세서 단위 테스트 (5개)
- `test_summarizer`: 요약 생성 테스트
- `test_evaluator`: 중요도 평가 테스트
- `test_classifier`: 카테고리 분류 테스트
- `test_embedder`: 임베딩 생성 테스트
- `test_all_processors_integration`: 통합 테스트

**`tests/test_pipeline.py`** - 파이프라인 테스트 (4개)
- `test_single_article_processing`: 단일 처리
- `test_batch_processing`: 배치 처리
- `test_pipeline_utilities`: 유틸리티 함수
- `test_processed_article_to_dict`: 데이터 변환

**`tests/test_api_processors.py`** - API 통합 테스트 (21개)

**8개 테스트 클래스:**
1. `TestSummarizeEndpoint` (3개)
2. `TestEvaluateEndpoint` (2개)
3. `TestClassifyEndpoint` (2개)
4. `TestProcessEndpoint` (2개)
5. `TestBatchProcessEndpoint` (3개)
6. `TestStatisticsEndpoint` (2개)
7. `TestEndToEndWorkflow` (1개)
8. `TestErrorHandling` (4개)
9. `TestHealthCheck` (2개)

**테스트 커버리지:**
- 정상 케이스 (Happy Path)
- 에러 케이스 (Error Handling)
- 엣지 케이스 (Edge Cases)
- End-to-End 워크플로우
- 입력 검증 (Pydantic)

**테스트 결과:**
```
================== 30 passed in 61.92s ==================
```
- ✅ 30개 테스트 모두 통과 (100%)
- ✅ 프로세서, 파이프라인, API 모두 검증
- ✅ 에러 핸들링 정상 작동

---

#### 6. 문서화

**`docs/PROMPTS.md`** - 프롬프트 시스템 가이드
- 프롬프트 구조 설명
- 사용 예제
- 커스터마이징 방법

**`docs/PROCESSORS.md`** - 프로세서 사용 가이드
- 5개 프로세서 상세 설명
- API 레퍼런스
- 성능 최적화 팁
- 파이프라인 사용법

**`docs/reports/`** - 검증 리포트
- `day4_checkpoint4.md`: API 엔드포인트 검증
- `day4_checkpoint5.md`: 통합 테스트 검증
- `README.md`: 리포트 디렉토리 안내

**`notebooks/03.test_day4.ipynb`** - 대화형 테스트 노트북
- 모든 Checkpoint 검증 (1-5)
- 프로세서 개별 테스트
- 파이프라인 테스트
- API 엔드포인트 테스트

---

### 최종 디렉토리 구조

```
research-curator/
├── src/app/
│   ├── processors/              # 신규 추가 ⭐
│   │   ├── __init__.py
│   │   ├── summarizer.py       # 요약 생성
│   │   ├── evaluator.py        # 중요도 평가
│   │   ├── classifier.py       # 카테고리 분류
│   │   ├── embedder.py         # 임베딩 생성
│   │   └── pipeline.py         # 통합 파이프라인
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── retry.py
│   │   └── prompts.py          # 신규 추가 ⭐
│   │
│   └── api/
│       ├── schemas/
│       │   ├── llm.py
│       │   ├── collectors.py
│       │   └── processors.py   # 신규 추가 ⭐
│       │
│       └── routers/
│           ├── llm.py
│           ├── collectors.py
│           └── processors.py   # 신규 추가 ⭐
│
├── configs/
│   └── prompts.yaml            # 신규 추가 ⭐
│
├── docs/
│   ├── PROMPTS.md              # 신규 추가 ⭐
│   ├── PROCESSORS.md           # 신규 추가 ⭐
│   ├── LLM_INTEGRATION.md
│   └── reports/                # 신규 추가 ⭐
│       ├── README.md
│       ├── day4_checkpoint4.md
│       └── day4_checkpoint5.md
│
├── notebooks/
│   ├── 01.test_llm_client.ipynb
│   ├── 02.test_day3_collectors.ipynb
│   ├── 03.test_day4.ipynb      # 신규 추가 ⭐
│   └── test_prompts.ipynb
│
└── tests/
    ├── test_llm_client.py
    ├── test_processors.py      # 신규 추가 ⭐
    ├── test_pipeline.py        # 신규 추가 ⭐
    └── test_api_processors.py  # 신규 추가 ⭐
```

---

### 설치된 패키지

```bash
# 기존 패키지 유지
# 추가 패키지 없음 (기존 litellm, openai 사용)
```

---

### 주요 성과

#### 1. 완전한 LLM 처리 파이프라인 구축 ✅
- **4개 프로세서**: 요약, 평가, 분류, 임베딩
- **통합 파이프라인**: 병렬 처리로 성능 최적화 (53% 향상)
- **배치 처리**: 여러 아티클 동시 처리

#### 2. 프롬프트 관리 시스템 ✅
- **중앙 집중식 관리**: YAML 기반
- **다국어/다양한 길이 지원**: 한국어/영어, short/medium/long
- **재사용 가능**: 템플릿 변수 치환

#### 3. RESTful API 구현 ✅
- **6개 엔드포인트**: 모든 처리 기능 API화
- **Pydantic 스키마**: 타입 안전성
- **OpenAPI 문서**: Swagger UI 자동 생성

#### 4. 완전한 테스트 커버리지 ✅
- **30개 테스트**: 100% 통과
- **3가지 레벨**: 단위, 통합, API
- **End-to-End**: 전체 워크플로우 검증

#### 5. 상세한 문서화 ✅
- **사용 가이드**: PROMPTS.md, PROCESSORS.md
- **검증 리포트**: Checkpoint 4, 5
- **대화형 테스트**: Jupyter 노트북

---

### 성능 벤치마크

| 작업 | 시간 | 비고 |
|-----|------|------|
| 단일 아티클 처리 | 3.7초 | 요약+평가+분류+임베딩 |
| 배치 5개 처리 | 8.6초 | 병렬 처리 (평균 1.7초/개) |
| 프로세서 테스트 | ~5초 | pytest 5개 테스트 |
| 파이프라인 테스트 | ~15초 | pytest 4개 테스트 |
| API 통합 테스트 | 36초 | pytest 21개 테스트 |
| **전체 테스트** | **62초** | **30개 테스트 모두 통과** |

---

### Checkpoint 검증 결과

**✅ Checkpoint 1**: 프롬프트 시스템 정상 작동
- 6개 카테고리 로드 성공
- 메시지 빌드 정상 작동

**✅ Checkpoint 2**: 4개 프로세서 정상 작동
- ArticleSummarizer: 한국어/영어 요약 생성
- ImportanceEvaluator: 점수 0.0-1.0 범위 내
- ContentClassifier: 카테고리 정확히 분류
- TextEmbedder: 1536차원 임베딩 생성

**✅ Checkpoint 3**: 파이프라인 정상 작동
- 단일 아티클 처리: 3.7초
- 배치 5개 처리: 8.6초 (53% 성능 향상)
- 유틸리티 함수 모두 작동

**✅ Checkpoint 4**: API 엔드포인트 정상 작동
- 6개 엔드포인트 모두 200 OK
- Swagger UI 정상 접근
- 요청/응답 스키마 검증 통과

**✅ Checkpoint 5**: 통합 테스트 완료
- 30개 테스트 모두 통과 (100%)
- 에러 핸들링 검증
- End-to-End 워크플로우 검증

---

### API 엔드포인트 예시

#### 1. 요약 생성
```bash
curl -X POST http://localhost:8000/api/processors/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Attention Is All You Need",
    "content": "We propose the Transformer...",
    "language": "ko",
    "length": "medium"
  }'

# 응답
{
  "summary": "트랜스포머 아키텍처를 제안하는 논문...",
  "language": "ko",
  "length": "medium"
}
```

#### 2. 전체 처리
```bash
curl -X POST http://localhost:8000/api/processors/process \
  -H "Content-Type: application/json" \
  -d '{
    "title": "GPT-4 Technical Report",
    "content": "GPT-4 is a large multimodal model...",
    "url": "https://openai.com/research/gpt-4",
    "metadata": {"year": 2023, "citations": 5000}
  }'

# 응답
{
  "summary": "GPT-4는 대규모 멀티모달 모델...",
  "importance_score": 0.92,
  "category": "paper",
  "keywords": ["GPT-4", "multimodal", "AI"],
  "embedding": [0.01, -0.02, ...],  // 1536 dims
  "innovation_score": 0.95,
  ...
}
```

---

### 다음 단계 (Day 5)

**Day 5 목표: Vector DB 통합 및 검색 기능**

1. **Qdrant 통합**
   - Collection 생성 및 관리
   - 벡터 저장 및 검색
   - 메타데이터 필터링

2. **검색 API**
   - 시맨틱 검색 엔드포인트
   - 하이브리드 검색 (벡터 + 키워드)
   - 유사 논문 추천

3. **데이터베이스 연동**
   - PostgreSQL에 처리 결과 저장
   - Qdrant와 PostgreSQL 동기화
   - CRUD API 구현

4. **스케줄러**
   - 자동 수집 및 처리
   - 배치 작업 관리

---

### 참고 사항

**실행 방법:**
```bash
# FastAPI 서버 시작
uvicorn src.app.api.main:app --reload

# API 문서
open http://localhost:8000/docs

# 테스트 실행
pytest tests/ -v
```

**환경 변수:**
```bash
# .env 파일
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx  # Optional
```

**Jupyter 노트북 테스트:**
```bash
jupyter notebook notebooks/03.test_day4.ipynb
```
