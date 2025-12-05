# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI 연구자를 위한 맞춤형 리서치 큐레이션 서비스입니다. LLM과 웹 검색 기술을 활용하여 특정 연구 분야의 트렌드 정보를 주기적으로 수집하고, 한국어로 요약하여 이메일로 전송합니다.

### 핵심 기능
- **자동 데이터 수집**: arXiv, Google Scholar, TechCrunch 등에서 논문/뉴스/리포트 수집
- **LLM 기반 처리**: GPT-4를 활용한 한국어 요약, 중요도 평가, 카테고리 분류
- **Vector DB 검색**: Qdrant를 사용한 시맨틱 검색 및 과거 자료 재검색
- **이메일 큐레이션**: 매일 상위 N개 자료를 HTML 이메일로 전송
- **웹 대시보드**: Streamlit 기반 설정 관리 및 검색 인터페이스

### 기술 스택
- **Backend**: Python, FastAPI
- **Database**: PostgreSQL
- **Vector DB**: Qdrant (Docker)
- **LLM**: GPT-4 via LiteLLM
- **Embedding**: OpenAI
- **Frontend**: Streamlit
- **Scheduler**: APScheduler / Celery Beat
- **Data Collection**: Serper API, Brave Search API

## Environment Setup

### Initial Development Setup
```bash
# Development environment (includes pre-commit hooks)
make init-dev
# OR
bash install.sh --dev

# Production environment
make init
# OR
bash install.sh

# View all available make commands
make help
```

The project uses:
- Python 3.12.9 (pinned version)
- uv for dependency management
- Virtual environment in `.venv/`
- Always activate the virtual environment: `source .venv/bin/activate`

### Environment Variables
```bash
cp .env.example .env
cp .env.dev.example .env.dev
```

Required environment variables:
- `OPENAI_API_KEY`: OpenAI API key for GPT-4 and embeddings
- `SERPER_API_KEY` or `BRAVE_API_KEY`: Search API key
- `DATABASE_URL`: PostgreSQL connection string
- `QDRANT_HOST`, `QDRANT_PORT`: Qdrant Vector DB connection
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`: Email configuration
- `JWT_SECRET_KEY`: Secret key for JWT token generation

### Docker Services
```bash
# Start PostgreSQL and Qdrant
docker-compose up -d

# Or run Qdrant separately
docker run -p 6333:6333 qdrant/qdrant
```

### Running the Application
```bash
# Start FastAPI backend
uvicorn src.app.api.main:app --reload

# Start Streamlit frontend
streamlit run src/app/frontend/main.py

# Run scheduler (for automated data collection and email sending)
python -m src.app.scheduler.main
```

## Code Quality & Formatting

### Pre-commit Hooks
Pre-commit is configured with:
- Ruff (formatting and linting, line-length: 105)
- trailing-whitespace, end-of-file-fixer, mixed-line-ending
- check-added-large-files (max 30MB)
- requirements-txt-fixer
- add-trailing-comma

### Manual Formatting
```bash
make format  # Runs ruff format
```

**Important**: Always maintain line-length of 105 characters for Ruff formatting.

## Architecture

### Directory Structure
```
src/app/                  # Main package (통합 관리)
  api/                    # FastAPI backend
    main.py               # FastAPI app entry point
    routers/              # API route handlers
      auth.py             # Magic link authentication
      users.py            # User management
      preferences.py      # User preferences
      articles.py         # Article CRUD
      search.py           # Semantic search
      feedback.py         # User feedback
    dependencies.py       # Dependency injection
    schemas.py            # Pydantic models

  collectors/             # Data collection modules
    base.py               # Base collector interface
    arxiv.py              # arXiv paper collector
    scholar.py            # Google Scholar collector
    news.py               # News collector (TechCrunch, etc.)
    reports.py            # Research report collector

  processors/             # LLM processing modules
    summarizer.py         # Article summarization
    evaluator.py          # Importance scoring
    classifier.py         # Category classification
    embedder.py           # Embedding generation

  db/                     # Database modules
    models.py             # SQLAlchemy models
    crud.py               # CRUD operations
    session.py            # Database session management

  vector_db/              # Qdrant integration
    client.py             # Qdrant client wrapper
    operations.py         # Vector CRUD operations

  email/                  # Email service
    templates/            # HTML email templates
    sender.py             # SMTP email sender
    builder.py            # Email content builder

  scheduler/              # Task scheduling
    main.py               # Scheduler entry point
    tasks.py              # Scheduled task definitions

  frontend/               # Streamlit application
    main.py               # Streamlit entry point
    pages/                # Streamlit pages
      onboarding.py       # AI chatbot onboarding
      dashboard.py        # Main dashboard
      settings.py         # User settings
      search.py           # Semantic search UI
      feedback.py         # Feedback submission

configs/                  # Configuration files
  settings.yaml           # Application settings
  prompts.yaml            # LLM prompt templates
  sources.yaml            # Default data sources

data/                     # Data directory (git-ignored)
  raw/                    # Raw collected data
  processed/              # Processed articles

notebooks/                # Jupyter notebooks for experiments
tests/                    # Test files
```

### Database Schema

**PostgreSQL Tables:**
- `users`: User accounts (id, email, name, created_at)
- `user_preferences`: User settings (research_fields, keywords, sources, email_time)
- `collected_articles`: Collected articles (title, content, summary, source_url, importance_score)
- `sent_digests`: Email sending history
- `feedback`: User feedback on articles

**Qdrant Collection:**
- `research_articles`: Article embeddings with metadata

### System Workflow

**Daily Automation Pipeline:**
1. **01:00** - Data collection from configured sources
2. **01:30** - LLM processing (summarization, scoring, classification)
3. **06:00** - Content curation and email template generation
4. **08:00** - Email delivery to users

### API Endpoints

```
POST   /auth/magic-link      # Request magic link
GET    /auth/verify          # Verify magic link token
GET    /users/me             # Get current user
PUT    /users/preferences    # Update user preferences
GET    /articles             # List articles
GET    /articles/search      # Semantic search
POST   /feedback             # Submit feedback
```

## Dependencies

Key dependencies for this project:
- **API Framework**: fastapi, uvicorn, pydantic
- **Database**: sqlalchemy, asyncpg, alembic
- **Vector DB**: qdrant-client
- **LLM**: litellm, openai, langchain
- **Web Scraping**: httpx, beautifulsoup4, serper
- **Email**: aiosmtplib, jinja2
- **Scheduler**: apscheduler
- **Frontend**: streamlit
- **Auth**: python-jose, passlib

When adding new dependencies:
```bash
uv add <package>  # Adds to pyproject.toml and syncs
```

## Development Workflow

1. Activate the virtual environment: `source .venv/bin/activate`
2. Start Docker services: `docker-compose up -d`
3. Run database migrations: `alembic upgrade head`
4. Start the backend: `uvicorn src.app.api.main:app --reload`
5. Start the frontend: `streamlit run src/app/frontend/main.py`

### Git Commit Policy

**CRITICAL**: NEVER create git commits automatically without explicit user request.

- Only run `git commit` when the user explicitly asks to commit
- Do NOT commit after completing tasks
- Do NOT commit when finishing checkpoints
- Do NOT commit when writing documentation
- Always wait for user's explicit instruction to commit

Examples of when NOT to commit:
- ❌ "작업 완료했습니다" → DO NOT commit
- ❌ "Checkpoint 완료" → DO NOT commit
- ❌ "문서 작성 완료" → DO NOT commit

Only commit when user says:
- ✅ "커밋해줘"
- ✅ "commit"
- ✅ "git commit 해줘"

### Testing
```bash
pytest tests/                    # Run all tests
pytest tests/test_collectors.py  # Run specific test file
pytest -v --cov=src/app          # Run with coverage
```

### Database Migrations
```bash
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head                               # Apply migrations
alembic downgrade -1                               # Rollback one migration
```

## LLM Prompt Guidelines

All LLM prompts are stored in `configs/prompts.yaml`. When modifying prompts:
1. Use clear, specific instructions
2. Include few-shot examples for complex tasks
3. Specify output format explicitly (JSON schema preferred)
4. Test with various input types before deploying

### Key Prompts
- `summarize_article`: Generate Korean summary of article
- `evaluate_importance`: Score article importance (0-1)
- `classify_category`: Classify as paper/news/report
- `onboarding_chat`: AI chatbot for user onboarding

## Error Handling

- All API endpoints should return appropriate HTTP status codes
- Use structured error responses with error codes
- Log errors with sufficient context for debugging
- Implement retry logic for external API calls (LLM, search APIs)

## Security Considerations

- Store API keys in environment variables, never in code
- Use parameterized queries for all database operations
- Validate and sanitize all user inputs
- Implement rate limiting for API endpoints
- Use HTTPS in production
- JWT tokens should have appropriate expiration times
