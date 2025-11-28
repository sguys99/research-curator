# AI Research Curator

AI 연구자를 위한 맞춤형 리서치 큐레이션 서비스입니다. LLM과 웹 검색 기술을 활용하여 특정 연구 분야의 트렌드 정보를 주기적으로 수집하고, 한국어로 요약하여 이메일로 전송합니다.

## 주요 기능

- 🤖 **자동 데이터 수집**: arXiv, Google Scholar, TechCrunch 등에서 논문/뉴스/리포트 자동 수집
- 🧠 **LLM 기반 처리**: GPT-4를 활용한 한국어 요약, 중요도 평가, 카테고리 분류
- 🔍 **Vector DB 검색**: Qdrant를 사용한 시맨틱 검색 및 과거 자료 재검색
- 📧 **이메일 큐레이션**: 매일 상위 N개 자료를 HTML 이메일로 전송
- 🎨 **웹 대시보드**: Streamlit 기반 설정 관리 및 검색 인터페이스
- 🔐 **매직 링크 인증**: 비밀번호 없는 간편한 이메일 인증

## 기술 스택

- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Vector DB**: Qdrant
- **LLM**: OpenAI GPT-4o via LiteLLM
- **Frontend**: Streamlit
- **Scheduler**: APScheduler
- **Package Manager**: uv

---

## 📅 개발 일지

### Day 1: 프로젝트 셋업 & 데이터베이스 (2025-11-28)

#### ✅ 완료 작업

**1. Core 설정 모듈**
- `src/app/core/config.py`: Pydantic Settings로 환경 변수 관리
  - Database, Qdrant, OpenAI, SMTP, JWT 설정
  - 개발/프로덕션 환경 분리
- `src/app/core/security.py`: JWT 기반 인증
  - 매직 링크 토큰 생성/검증
  - 액세스 토큰 생성/검증

**2. 데이터베이스 모델**
- `src/app/db/models.py`: SQLAlchemy ORM 모델 5개 정의
  - `User`: 사용자 계정 (id, email, name)
  - `UserPreference`: 사용자 설정 (연구 분야, 키워드, 소스, 이메일 시간)
  - `CollectedArticle`: 수집된 아티클 (제목, 요약, 중요도, 벡터 ID)
  - `SentDigest`: 이메일 발송 이력
  - `Feedback`: 사용자 피드백 (평점, 코멘트)

**3. 데이터베이스 세션 관리**
- `src/app/db/session.py`: SQLAlchemy 세션 팩토리
  - FastAPI 의존성 함수 `get_db()`
  - Connection pooling 설정

**4. Docker 서비스**
- `docker-compose.yml`: PostgreSQL, Qdrant 컨테이너 설정
  - PostgreSQL: 포트 5433
  - Qdrant: 포트 6333 (HTTP), 6334 (gRPC)
  - Volume 마운트로 데이터 영속성 보장

**5. FastAPI 애플리케이션**
- `src/app/api/main.py`: FastAPI 앱 엔트리포인트
  - CORS 미들웨어 설정
  - Health check 엔드포인트 (`/`, `/health`)

**6. Alembic 마이그레이션**
- `alembic/env.py`: 자동으로 .env에서 DB URL 로드
- `alembic.ini`: 마이그레이션 설정

**7. 환경 변수 설정**
- `.env`: 개발용 환경 변수 (OpenAI API 키 포함)
- `.env.example`: 환경 변수 템플릿

#### 📦 설치된 패키지
```bash
# 핵심 패키지
- sqlalchemy
- alembic
- asyncpg
- psycopg2-binary
- python-jose
- passlib
- qdrant-client
- pydantic-settings
```

#### 🚀 실행 방법

**1. 의존성 설치**
```bash
# 가상 환경 활성화
source .venv/bin/activate

# 패키지 동기화
uv sync
```

**2. Docker 서비스 시작**
```bash
# PostgreSQL & Qdrant 시작
docker compose up -d

# 서비스 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f
```

**3. 환경 변수 설정**
```bash
# .env 파일이 없다면 생성
cp .env.example .env

# .env 파일 편집 (필수 항목)
# - OPENAI_API_KEY
# - DATABASE_URL
# - JWT_SECRET_KEY
```

**4. FastAPI 서버 실행**
```bash
# 개발 모드 (자동 재시작)
uvicorn app.api.main:app --reload

# 또는 호스트/포트 지정
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**5. API 테스트**
```bash
# Health check
curl http://localhost:8000/health

# 서비스 정보
curl http://localhost:8000/

# Swagger 문서 (브라우저)
open http://localhost:8000/docs
```

#### 📊 테스트 결과
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

#### 🗂️ 디렉토리 구조
```
src/app/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py          # 환경 설정
│   └── security.py        # 인증 로직
├── db/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy 모델
│   └── session.py         # DB 세션 관리
└── api/
    ├── __init__.py
    ├── main.py            # FastAPI 앱
    └── routers/
        └── __init__.py

alembic/                   # DB 마이그레이션
docker-compose.yml         # Docker 서비스
.env                       # 환경 변수 (개발)
.env.example              # 환경 변수 템플릿
```

#### 🔜 다음 단계 (Day 2)
1. ✅ 기본 인프라 셋업 완료
2. 🔲 매직 링크 인증 API 구현
3. 🔲 사용자 관리 API (CRUD)
4. 🔲 DB 마이그레이션 생성 및 실행
5. 🔲 Pydantic 스키마 정의

---

## 사전 요구사항

- Python 3.12.9 (고정 버전)
- `uv` 패키지 매니저
- Docker & Docker Compose
- PostgreSQL 클라이언트 (선택)

## 빠른 시작

### 1. 환경 설정

**개발 환경** (pre-commit hooks 포함):
```bash
make init-dev
# 또는
bash install.sh --dev
```

**프로덕션 환경**:
```bash
make init
# 또는
bash install.sh
```

### 2. Docker 서비스 시작
```bash
docker compose up -d
```

### 3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 편집 (API 키 입력)
```

### 4. FastAPI 서버 실행
```bash
source .venv/bin/activate
uvicorn app.api.main:app --reload
```

### 5. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 유용한 명령어

### Docker 관리
```bash
# 서비스 시작
docker compose up -d

# 서비스 중지
docker compose down

# 로그 확인
docker compose logs -f

# PostgreSQL 접속
docker exec -it research-curator-postgres psql -U postgres -d research_curator

# Qdrant 헬스체크
curl http://localhost:6333/healthz
```

### 데이터베이스 마이그레이션
```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1

# 현재 상태 확인
alembic current
```

### 코드 포맷팅
```bash
# Ruff 포맷팅
make format

# 또는
ruff format .
```

---

## 프로젝트 설정

### 환경 변수 (.env)
```bash
# Application
APP_NAME="Research Curator"
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/research_curator

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# OpenAI
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Authentication
JWT_SECRET_KEY=your-secret-key-here
```

전체 환경 변수 목록은 [.env.example](.env.example)을 참고하세요.

---

## 트러블슈팅

### PostgreSQL 포트 충돌
```bash
# 기본 PostgreSQL 서비스 확인
lsof -i :5432

# docker-compose.yml에서 포트 변경 (예: 5433:5432)
# .env의 DATABASE_URL도 변경
```

### Alembic 실행 오류
```bash
# Python path 확인
python -c "from app.core.config import settings; print('OK')"

# 가상환경이 활성화되었는지 확인
which python  # .venv/bin/python이어야 함
```

---

## 작성자

- KMYU (sguys99@gmail.com)

## 라이선스

This project is for educational and research purposes.
