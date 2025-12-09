"""Database session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine, PostgreSQL DB 연결 엔진 생성
engine = create_engine(
    settings.database_url_str,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # 연결전 유효성 검증
    pool_size=10,
    max_overflow=20,  # 최대 30개 동시연결 지원
)

# Create session factory, 데이터베이스 세션을 생성하는 팩토리?
# 팩토리 개념
# # 팩토리 없이 (매번 설정을 반복해야 함)
# session1 = Session(bind=engine, autocommit=False, autoflush=False)
# session2 = Session(bind=engine, autocommit=False, autoflush=False)
# session3 = Session(bind=engine, autocommit=False, autoflush=False)

# # 팩토리 사용 (한 번 설정하면 계속 재사용): 일관성/ 재사용성/ 편리성
# SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# session1 = SessionLocal()  # 동일한 설정으로 생성
# session2 = SessionLocal()  # 동일한 설정으로 생성
# session3 = SessionLocal()  # 동일한 설정으로 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 의존성 함수
# FastAPI 의존성 주입(Dependency Injection)에 사용되는 핵심 함수
# 세션을 생성하고, 요청 완료 후 자동으로 close 처리
# API 라우터에서 db: Session = Depends(get_db) 형태로 사용
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 모든 테이블 생성(테스트용) 실제로는 Alembic 사용
def create_tables():
    """Create all database tables. Use only for testing; prefer Alembic for migrations."""
    from app.db.models import Base

    Base.metadata.create_all(bind=engine)


# 모든 테이블 삭제(테스트용)
def drop_tables():
    """Drop all database tables. Use only for testing."""
    from app.db.models import Base

    Base.metadata.drop_all(bind=engine)
