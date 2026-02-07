# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI 연구자를 위한 맞춤형 리서치 큐레이션 서비스. LLM과 웹 검색 기술을 활용하여 특정 연구 분야의 트렌드 정보를 주기적으로 수집하고, 한국어로 요약하여 이메일로 전송합니다.

### 기술 스택
- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Alembic
- **Frontend**: Next.js 16 (App Router), TypeScript, shadcn/ui, Tailwind CSS, Zustand
- **Database**: PostgreSQL (port 5433), Qdrant (Vector DB, port 6333)
- **LLM**: OpenAI GPT-4o via LiteLLM (provider-agnostic, supports Claude)
- **Package Manager**: uv (Backend), pnpm (Frontend)

## Development Commands

### Environment Setup
```bash
make init-dev                 # 개발 환경 초기화 (pre-commit 포함)
source .venv/bin/activate     # 가상환경 활성화
cp .env.example .env          # 환경 변수 설정
docker compose up -d          # PostgreSQL (5433) & Qdrant (6333) 시작
```

### Backend
```bash
uvicorn src.app.api.main:app --reload    # API 서버 (http://localhost:8000)
python -m src.app.scheduler.main          # 스케줄러
alembic upgrade head                      # 마이그레이션 적용
alembic revision --autogenerate -m "msg"  # 마이그레이션 생성
```

### Frontend
```bash
cd frontend
pnpm install                  # 의존성 설치
pnpm dev                      # 개발 서버 (http://localhost:3000)
pnpm build                    # 프로덕션 빌드
pnpm lint                     # ESLint
pnpm test                     # Vitest 단위 테스트
```

### Code Quality
```bash
make format                   # Ruff 포맷팅 + 린트 (line-length: 105)
pytest tests/                 # 전체 테스트 (기본: unit 마커만 실행)
pytest tests/test_*.py -v     # 특정 테스트 파일
pytest -m integration         # 통합 테스트
```

## Architecture

### Data Pipeline

```
Collectors (arXiv, News, Scholar)
    → Processors (pipeline.py: asyncio.gather로 병렬 처리)
        → Summarizer (한국어 요약)
        → Evaluator (중요도 0-1, 4개 기준)
        → Classifier (paper/news/report + 키워드)
        → Embedder (벡터 임베딩)
    → Dual Storage
        → PostgreSQL: 메타데이터, 요약, 점수
        → Qdrant: 벡터 임베딩 (시맨틱 검색용)
    → Scheduler (06:00 KST 통합 작업)
        → Email (Jinja2 템플릿 + Premailer)
```

### Key Backend Patterns

- **Config**: `src/app/core/config.py` — Pydantic Settings + `@lru_cache` 싱글턴. 환경별 검증 포함
- **Prompts**: `configs/prompts.yaml` — 모든 LLM 프롬프트 중앙 관리. `PromptManager`가 `string.Template`로 치환
- **LLM Client**: `src/app/llm/client.py` — LiteLLM 래퍼. tenacity 기반 재시도, JSON 모드 + 폴백 파싱
- **Auth**: 매직 링크 인증 → JWT (30일). `dependencies.py`의 `get_current_user()` 의존성 주입
- **IDs**: 전체 시스템에서 `uuid7()` 사용 (시간 정렬 가능)
- **Vector ID 분리**: PostgreSQL `article.id` ≠ Qdrant `vector_id`

### Key Frontend Patterns

- **Route Groups**: `(auth)/`, `(dashboard)/` — URL에 영향 없이 레이아웃 분리. AuthGuard로 보호
- **API Client**: `frontend/lib/api/client.ts` — Axios 인터셉터로 Bearer 토큰 자동 주입, 401시 자동 로그아웃
- **State**: Zustand (클라이언트) + TanStack Query (서버 상태). 토큰은 sessionStorage 저장 (XSS 완화)
- **SSE Streaming**: 온보딩 AI 챗봇 (`/api/llm/onboarding/chat`)에서 EventSource 사용
- **Path Alias**: `@` → 프론트엔드 프로젝트 루트

### Directory Structure
```
src/app/                      # Python 백엔드
  core/                       # config, prompts, retry, security
  api/                        # FastAPI (routers/, schemas/, dependencies.py)
  db/                         # SQLAlchemy 모델, CRUD, 세션
  collectors/                 # 데이터 수집 (arXiv, Scholar, News)
  processors/                 # LLM 처리 (pipeline, summarizer, evaluator, classifier, embedder)
  vector_db/                  # Qdrant (client, operations, schema)
  scheduler/                  # APScheduler 작업
  llm/                        # LiteLLM 클라이언트

frontend/                     # Next.js 프론트엔드
  app/                        # App Router 페이지
    (auth)/                   # 인증 (login, verify, onboarding)
    (dashboard)/              # 대시보드, 검색, 설정, 피드백
  components/                 # React 컴포넌트 (ui/, layout/)
  lib/api/                    # API 클라이언트 (도메인별 분리)
  stores/                     # Zustand (auth-store, onboarding-store, toast-store)

configs/                      # settings.yaml, prompts.yaml
alembic/                      # DB 마이그레이션
tests/                        # pytest (markers: unit, integration, e2e)
```

### Database
- **PostgreSQL** (5433): users, user_preferences, collected_articles, sent_digests, feedback
  - `source_url` 유니크 제약 (중복 수집 방지)
  - `ondelete="CASCADE"` — 사용자 삭제시 관련 데이터 자동 삭제
  - JSON 컬럼: research_fields, sources, info_types (유연한 메타데이터)
- **Qdrant**: research_articles (임베딩 + 메타데이터 필터링)

## Environment Variables

필수 환경 변수 (.env):
```bash
OPENAI_API_KEY=sk-xxx
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/research_curator
JWT_SECRET_KEY=your-secret-key
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

Frontend (.env.local):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Code Style

- **Python**: Ruff (line-length: 105, target: py312). `B008` 무시됨 (FastAPI `Depends()` 허용)
- **Frontend**: ESLint + Prettier. Server Components 기본, "use client" 필요시에만
- **Pre-commit**: Ruff check/format, trailing-whitespace, add-trailing-comma

## Git Commit Policy

**CRITICAL**: 사용자가 명시적으로 요청할 때만 커밋 생성

- ❌ 작업 완료 후 자동 커밋 금지
- ✅ "커밋해줘", "commit" 요청 시에만 커밋

커밋 메시지 형식: 이모지 접두사 + 요약 (예: `:bug: Fix scheduler status`)
