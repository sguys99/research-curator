"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import collectors, llm, processors
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered research curation service for researchers",
    debug=settings.DEBUG,
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
app.include_router(llm.router, prefix="/api")
app.include_router(collectors.router, prefix="/api")
app.include_router(processors.router, prefix="/api")

# TODO: Add more routers
# from app.api.routers import auth, users, articles, search, feedback
# app.include_router(auth.router, prefix="/auth", tags=["auth"])
# app.include_router(users.router, prefix="/users", tags=["users"])
# app.include_router(articles.router, prefix="/articles", tags=["articles"])
# app.include_router(search.router, prefix="/search", tags=["search"])
# app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
