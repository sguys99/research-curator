"""Qdrant collection schema definitions and setup utilities."""

import logging
from typing import Any

from qdrant_client.http import models

from app.core.config import settings
from app.vector_db.client import QdrantClientWrapper, get_qdrant_client

logger = logging.getLogger(__name__)


class CollectionSchema:
    """Schema definition for research_articles collection."""

    # Collection metadata
    COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME
    VECTOR_SIZE = settings.QDRANT_VECTOR_SIZE
    DISTANCE_METRIC = models.Distance.COSINE

    # Payload schema (for reference and validation)
    PAYLOAD_SCHEMA = {
        "article_id": "string (UUID)",  # Reference to PostgreSQL CollectedArticle.id
        "title": "string",  # Article title
        "summary": "string",  # Korean summary
        "source_type": "string",  # paper/news/report
        "category": "string",  # AI, ML, NLP, etc.
        "importance_score": "float",  # 0.0 - 1.0
        "collected_at": "string (ISO timestamp)",  # When article was collected
        "metadata": "object",  # Additional metadata (authors, citations, etc.)
    }

    # Index configuration for optimized filtering
    PAYLOAD_INDEXES = [
        # Create index on source_type for filtering by paper/news/report
        {
            "field_name": "source_type",
            "field_schema": models.PayloadSchemaType.KEYWORD,
        },
        # Create index on category for filtering by research category
        {
            "field_name": "category",
            "field_schema": models.PayloadSchemaType.KEYWORD,
        },
        # Create index on importance_score for filtering by score threshold
        {
            "field_name": "importance_score",
            "field_schema": models.PayloadSchemaType.FLOAT,
        },
        # Create index on collected_at for date range filtering
        {
            "field_name": "collected_at",
            "field_schema": models.PayloadSchemaType.KEYWORD,
        },
    ]

    @classmethod
    def get_schema_info(cls) -> dict[str, Any]:
        """Get complete schema information.

        Returns:
            dict: Schema information including collection name, vector size, and payload schema
        """
        return {
            "collection_name": cls.COLLECTION_NAME,
            "vector_size": cls.VECTOR_SIZE,
            "distance_metric": cls.DISTANCE_METRIC.value,
            "payload_schema": cls.PAYLOAD_SCHEMA,
            "payload_indexes": [
                {"field": idx["field_name"], "type": idx["field_schema"].value}
                for idx in cls.PAYLOAD_INDEXES
            ],
        }


def setup_collection(
    client: QdrantClientWrapper | None = None,
    recreate: bool = False,
) -> bool:
    """Setup the research_articles collection with proper schema and indexes.

    Args:
        client: Qdrant client instance (defaults to global client)
        recreate: If True, delete existing collection and create new one (default: False)

    Returns:
        bool: True if setup was successful, False otherwise

    Raises:
        ConnectionError: If unable to connect to Qdrant server
    """
    if client is None:
        client = get_qdrant_client()

    collection_name = CollectionSchema.COLLECTION_NAME

    try:
        # Check if collection exists
        exists = client.collection_exists(collection_name)

        if exists and not recreate:
            logger.info(f"Collection '{collection_name}' already exists. Skipping creation.")
            info = client.get_collection_info(collection_name)
            if info:
                logger.info(f"Collection info: {info}")
            return True

        # Recreate or create collection
        if recreate:
            logger.info(f"Recreating collection '{collection_name}'...")
            success = client.recreate_collection(
                collection_name=collection_name,
                vector_size=CollectionSchema.VECTOR_SIZE,
                distance=CollectionSchema.DISTANCE_METRIC,
            )
        else:
            logger.info(f"Creating collection '{collection_name}'...")
            success = client.create_collection(
                collection_name=collection_name,
                vector_size=CollectionSchema.VECTOR_SIZE,
                distance=CollectionSchema.DISTANCE_METRIC,
            )

        if not success:
            logger.error(f"Failed to create collection '{collection_name}'")
            return False

        # Create payload indexes for optimized filtering
        logger.info("Creating payload indexes...")
        for index_config in CollectionSchema.PAYLOAD_INDEXES:
            try:
                client.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=index_config["field_name"],
                    field_schema=index_config["field_schema"],
                )
                logger.info(f"Created index on '{index_config['field_name']}'")
            except Exception as e:
                logger.warning(f"Failed to create index on '{index_config['field_name']}': {e}")
                # Continue with other indexes even if one fails

        # Verify collection setup
        info = client.get_collection_info(collection_name)
        if info:
            logger.info(f"Collection '{collection_name}' setup complete: {info}")
        else:
            logger.warning("Collection created but unable to retrieve info")

        return True

    except Exception as e:
        logger.error(f"Error during collection setup: {e}")
        return False


def verify_collection_schema(client: QdrantClientWrapper | None = None) -> dict[str, Any]:
    """Verify that the collection exists and has the correct schema.

    Args:
        client: Qdrant client instance (defaults to global client)

    Returns:
        dict: Verification results including:
            - exists: boolean indicating if collection exists
            - schema_valid: boolean indicating if schema matches expected
            - info: collection information (if exists)
            - errors: list of validation errors (if any)
    """
    if client is None:
        client = get_qdrant_client()

    collection_name = CollectionSchema.COLLECTION_NAME
    result = {
        "exists": False,
        "schema_valid": False,
        "info": None,
        "errors": [],
    }

    # Check if collection exists
    if not client.collection_exists(collection_name):
        result["errors"].append(f"Collection '{collection_name}' does not exist")
        return result

    result["exists"] = True

    # Get collection info
    info = client.get_collection_info(collection_name)
    if info is None:
        result["errors"].append("Unable to retrieve collection information")
        return result

    result["info"] = info

    # Validate vector size
    if info["vector_size"] != CollectionSchema.VECTOR_SIZE:
        result["errors"].append(
            f"Vector size mismatch: expected {CollectionSchema.VECTOR_SIZE}, "
            f"got {info['vector_size']}",
        )
    else:
        result["schema_valid"] = True

    return result


def initialize_vector_db(recreate: bool = False) -> bool:
    """Initialize the vector database (main entry point).

    This function should be called during application startup to ensure
    the Qdrant collection is properly configured.

    Args:
        recreate: If True, recreate the collection even if it exists (default: False)

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    logger.info("Initializing vector database...")

    try:
        # Get Qdrant client
        client = get_qdrant_client()

        # Check health
        health = client.health_check()
        if health["status"] != "healthy":
            logger.error(f"Qdrant health check failed: {health.get('error')}")
            return False

        logger.info(f"Qdrant server is healthy at {health['host']}:{health['port']}")
        logger.info(f"Available collections: {health.get('collections', [])}")

        # Setup collection
        success = setup_collection(client, recreate=recreate)
        if not success:
            logger.error("Failed to setup collection")
            return False

        # Verify schema
        verification = verify_collection_schema(client)
        if not verification["exists"]:
            logger.error("Collection verification failed: collection does not exist")
            return False

        if not verification["schema_valid"]:
            logger.error(f"Schema validation failed: {verification['errors']}")
            return False

        logger.info("Vector database initialization complete!")
        return True

    except Exception as e:
        logger.error(f"Vector database initialization error: {e}")
        return False
