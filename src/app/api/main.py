"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import articles, auth, collectors, feedback, llm, processors, scheduler, users
from app.core.config import settings
from app.vector_db.client import get_qdrant_client
from app.vector_db.schema import initialize_vector_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up application...")

    # Initialize vector database
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

    # Shutdown
    logger.info("Shutting down application...")

    # Close Qdrant client connection
    try:
        client = get_qdrant_client()
        client.close()
        logger.info("Qdrant client connection closed")
    except Exception as e:
        logger.error(f"Error closing Qdrant client: {e}")

    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered research curation service for researchers",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check for monitoring."""
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")
app.include_router(articles.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
app.include_router(collectors.router, prefix="/api")
app.include_router(processors.router, prefix="/api")
app.include_router(scheduler.router, prefix="/api")
