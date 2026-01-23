"""임베딩과 시맨틱 검색을 위한 벡터 DB 모듈."""

from app.vector_db.client import QdrantClientWrapper, get_qdrant_client
from app.vector_db.exceptions import VectorDBConnectionError, VectorDBError, VectorDBOperationError
from app.vector_db.operations import VectorOperations, get_vector_operations
from app.vector_db.schema import (
    CollectionSchema,
    initialize_vector_db,
    setup_collection,
    verify_collection_schema,
)

__all__ = [
    "QdrantClientWrapper",
    "get_qdrant_client",
    "VectorDBError",
    "VectorDBConnectionError",
    "VectorDBOperationError",
    "CollectionSchema",
    "initialize_vector_db",
    "setup_collection",
    "verify_collection_schema",
    "VectorOperations",
    "get_vector_operations",
]
