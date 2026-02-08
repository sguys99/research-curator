"""FastAPI 애플리케이션 진입점."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    articles,
    auth,
    collectors,
    feedback,
    llm,
    pipeline,
    processors,
    scheduler,
    users,
)
from app.core.config import settings
from app.vector_db.client import get_qdrant_client
from app.vector_db.schema import initialize_vector_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """시작/종료 이벤트를 처리하는 lifespan 컨텍스트 매니저."""
    # 시작
    logger.info("Starting up application...")

    # 벡터 DB 초기화
    logger.info("Initializing vector database...")
    try:
        success = initialize_vector_db(recreate=False)
        if not success:
            logger.error("Failed to initialize vector database")
            logger.warning("Vector search features may not work correctly")
        else:
            logger.info("Vector database initialized successfully")
    except Exception as e:
        logger.error(f"Error during vector database initialization: {e}")
        logger.warning("Vector search features may not work correctly")

    logger.info("Application startup complete")

    yield

    # 종료
    logger.info("Shutting down application...")

    # Qdrant 클라이언트 연결 종료
    try:
        client = get_qdrant_client()
        client.close()
        logger.info("Qdrant client connection closed")
    except Exception as e:
        logger.error(f"Error closing Qdrant client: {e}")

    logger.info("Application shutdown complete")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered research curation service for researchers",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """헬스 체크 엔드포인트."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """모니터링용 헬스 체크."""
    return {"status": "healthy"}


# 라우터 등록
app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")
app.include_router(articles.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
app.include_router(collectors.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(processors.router, prefix="/api")
app.include_router(scheduler.router, prefix="/api")
