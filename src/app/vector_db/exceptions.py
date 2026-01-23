"""벡터 DB 작업용 커스텀 예외."""


class VectorDBError(Exception):
    """벡터 DB 오류의 기본 예외."""


class VectorDBConnectionError(VectorDBError):
    """벡터 DB 연결 실패 시 발생."""


class VectorDBOperationError(VectorDBError):
    """벡터 DB 작업 실패 시 발생."""
