"""Vector database module for managing embeddings and semantic search."""

from app.vector_db.client import QdrantClientWrapper, get_qdrant_client
from app.vector_db.schema import (
    CollectionSchema,
    initialize_vector_db,
    setup_collection,
    verify_collection_schema,
)

__all__ = [
    "QdrantClientWrapper",
    "get_qdrant_client",
    "CollectionSchema",
    "initialize_vector_db",
    "setup_collection",
    "verify_collection_schema",
]
