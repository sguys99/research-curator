# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI 연구자를 위한 맞춤형 리서치 큐레이션 서비스. LLM과 웹 검색 기술을 활용하여 특정 연구 분야의 트렌드 정보를 주기적으로 수집하고, 한국어로 요약하여 이메일로 전송합니다.

### 기술 스택
- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Alembic
- **Frontend**: Next.js 16 (App Router), TypeScript, shadcn/ui, Tailwind CSS, Zustand
- **Database**: PostgreSQL, Qdrant (Vector DB)
- **LLM**: OpenAI GPT-4o via LiteLLM
- **Package Manager**: uv (Backend), pnpm (Frontend)

## Development Commands

### Environment Setup
```bash
# 개발 환경 초기화 (pre-commit 포함)
make init-dev

# 가상환경 활성화
source .venv/bin/activate

# 환경 변수 설정
cp .env.example .env
```

### Docker Services
```bash
docker compose up -d          # PostgreSQL & Qdrant 시작
docker compose down           # 서비스 중지
```

### Backend
```bash
uvicorn src.app.api.main:app --reload    # API 서버 (http://localhost:8000)
python -m src.app.scheduler.main          # 스케줄러
alembic upgrade head                      # 마이그레이션 적용
alembic revision --autogenerate -m "msg"  # 마이그레이션 생성
```

### Frontend (Next.js)
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
pytest tests/                 # 전체 테스트
pytest tests/test_*.py -v     # 특정 테스트 파일
```

## Architecture

### Directory Structure
```
src/app/                      # Python 백엔드
  api/                        # FastAPI (routers/, schemas/, dependencies.py)
  db/                         # SQLAlchemy 모델, CRUD, 세션
  collectors/                 # 데이터 수집 (arXiv, Scholar, News)
  processors/                 # LLM 처리 (요약, 평가, 분류, 임베딩)
  vector_db/                  # Qdrant 통합
  scheduler/                  # APScheduler 작업
  llm/                        # LLM 클라이언트
  frontend-poc/               # Streamlit POC (보존용)

frontend/                     # Next.js 프론트엔드 (프로덕션)
  app/                        # App Router 페이지
    (auth)/                   # 인증 (login, verify, onboarding)
    (dashboard)/              # 대시보드, 검색, 설정, 피드백
  components/                 # React 컴포넌트 (ui/, layout/)
  hooks/                      # Custom Hooks
  lib/                        # API 클라이언트, 유틸리티
  stores/                     # Zustand 상태 관리
  types/                      # TypeScript 타입
  providers/                  # Context Providers

alembic/                      # DB 마이그레이션
configs/                      # 설정 파일 (settings.yaml, prompts.yaml)
tests/                        # pytest 테스트
```

### Database Schema
**PostgreSQL**: users, user_preferences, collected_articles, sent_digests, feedback
**Qdrant**: research_articles (임베딩 + 메타데이터)

### API Endpoints
- `POST /auth/magic-link`, `GET /auth/verify` - 매직 링크 인증
- `GET /users/me`, `PUT /users/{id}/preferences` - 사용자 관리
- `GET /api/articles`, `POST /api/articles/search` - 아티클 CRUD/검색
- `POST /api/feedback`, `GET /api/feedback/user/{id}` - 피드백

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

## Git Commit Policy

**CRITICAL**: 사용자가 명시적으로 요청할 때만 커밋 생성

- ❌ 작업 완료 후 자동 커밋 금지
- ✅ "커밋해줘", "commit" 요청 시에만 커밋

커밋 메시지 형식: 이모지 접두사 + 요약 (예: `:bug: Fix scheduler status`)

## LLM Prompts

모든 LLM 프롬프트는 `configs/prompts.yaml`에 저장:
- `summarize_article`: 한국어 요약 생성
- `evaluate_importance`: 중요도 점수 (0-1)
- `classify_category`: paper/news/report 분류
- `onboarding_chat`: AI 챗봇 온보딩
