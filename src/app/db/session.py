"""데이터베이스 세션 관리."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLAlchemy 엔진 생성(PostgreSQL 연결 엔진)
engine = create_engine(
    settings.database_url_str,
    echo=False,  # SQL 로그 비활성화(노이즈 감소)
    pool_pre_ping=True,  # 연결 전 유효성 검증
    pool_size=10,
    max_overflow=20,  # 최대 30개 동시 연결 지원
)

# 세션 팩토리 생성(데이터베이스 세션 생성용)
# 팩토리 개념
# # 팩토리 없이(매번 설정을 반복해야 함)
# session1 = Session(bind=engine, autocommit=False, autoflush=False)
# session2 = Session(bind=engine, autocommit=False, autoflush=False)
# session3 = Session(bind=engine, autocommit=False, autoflush=False)

# # 팩토리 사용(한 번 설정하면 계속 재사용): 일관성/재사용성/편리성
# SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# session1 = SessionLocal()  # 동일한 설정으로 생성
# session2 = SessionLocal()  # 동일한 설정으로 생성
# session3 = SessionLocal()  # 동일한 설정으로 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 의존성 함수
# FastAPI 의존성 주입에 사용되는 핵심 함수
# 세션을 생성하고, 요청 완료 후 자동으로 close 처리
# API 라우터에서 db: Session = Depends(get_db) 형태로 사용
def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션을 제공하는 의존성 함수.

    FastAPI 사용 예시:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 모든 테이블 생성(테스트용). 실제로는 Alembic 사용
def create_tables():
    """모든 테이블을 생성한다(테스트 전용, 실제 마이그레이션은 Alembic 사용)."""
    from app.db.models import Base

    Base.metadata.create_all(bind=engine)


# 모든 테이블 삭제(테스트용)
def drop_tables():
    """모든 테이블을 삭제한다(테스트 전용)."""
    from app.db.models import Base

    Base.metadata.drop_all(bind=engine)
