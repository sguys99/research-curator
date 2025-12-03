"""Qdrant client wrapper for managing vector database connections and operations."""

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings

logger = logging.getLogger(__name__)


class QdrantClientWrapper:
    """Wrapper for Qdrant client with connection management and utility methods."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        collection_name: str | None = None,
    ) -> None:
        """Initialize Qdrant client.

        Args:
            host: Qdrant server host (defaults to settings.QDRANT_HOST)
            port: Qdrant server port (defaults to settings.QDRANT_PORT)
            collection_name: Default collection name (defaults to settings.QDRANT_COLLECTION_NAME)
        """
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self._client: QdrantClient | None = None

    @property
    def client(self) -> QdrantClient:
        """Get or create Qdrant client instance.

        Returns:
            QdrantClient: Active Qdrant client instance

        Raises:
            ConnectionError: If unable to connect to Qdrant server
        """
        if self._client is None:
            try:
                self._client = QdrantClient(host=self.host, port=self.port)
                logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                raise ConnectionError(f"Unable to connect to Qdrant at {self.host}:{self.port}") from e
        return self._client

    def health_check(self) -> dict[str, Any]:
        """Check Qdrant server health and connection status.

        Returns:
            dict: Health status information including:
                - status: "healthy" or "unhealthy"
                - connected: boolean indicating connection status
                - host: Qdrant server host
                - port: Qdrant server port
                - collections: list of available collection names (if connected)
                - error: error message (if unhealthy)
        """
        try:
            # Try to get collections list to verify connection
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            return {
                "status": "healthy",
                "connected": True,
                "host": self.host,
                "port": self.port,
                "collections": collection_names,
            }
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "host": self.host,
                "port": self.port,
                "error": str(e),
            }

    def collection_exists(self, collection_name: str | None = None) -> bool:
        """Check if a collection exists in Qdrant.

        Args:
            collection_name: Collection name to check (defaults to self.collection_name)

        Returns:
            bool: True if collection exists, False otherwise
        """
        name = collection_name or self.collection_name
        try:
            collections = self.client.get_collections()
            return name in [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False

    def create_collection(
        self,
        collection_name: str | None = None,
        vector_size: int | None = None,
        distance: models.Distance = models.Distance.COSINE,
        on_disk_payload: bool = True,
    ) -> bool:
        """Create a new collection in Qdrant.

        Args:
            collection_name: Name of the collection (defaults to self.collection_name)
            vector_size: Size of the embedding vectors (defaults to settings.QDRANT_VECTOR_SIZE)
            distance: Distance metric for similarity (default: COSINE)
            on_disk_payload: Store payload on disk to save memory (default: True)

        Returns:
            bool: True if collection was created successfully, False otherwise

        Raises:
            ValueError: If collection already exists
        """
        name = collection_name or self.collection_name
        size = vector_size or settings.QDRANT_VECTOR_SIZE

        # Check if collection already exists
        if self.collection_exists(name):
            logger.warning(f"Collection '{name}' already exists")
            raise ValueError(f"Collection '{name}' already exists")

        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=size,
                    distance=distance,
                ),
                on_disk_payload=on_disk_payload,
            )
            logger.info(f"Successfully created collection '{name}' with vector size {size}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection '{name}': {e}")
            return False

    def delete_collection(self, collection_name: str | None = None) -> bool:
        """Delete a collection from Qdrant.

        Args:
            collection_name: Name of the collection to delete (defaults to self.collection_name)

        Returns:
            bool: True if collection was deleted successfully, False otherwise
        """
        name = collection_name or self.collection_name

        if not self.collection_exists(name):
            logger.warning(f"Collection '{name}' does not exist")
            return False

        try:
            self.client.delete_collection(collection_name=name)
            logger.info(f"Successfully deleted collection '{name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{name}': {e}")
            return False

    def get_collection_info(self, collection_name: str | None = None) -> dict[str, Any] | None:
        """Get information about a collection.

        Args:
            collection_name: Name of the collection (defaults to self.collection_name)

        Returns:
            dict: Collection information including:
                - name: collection name
                - vector_size: size of embedding vectors
                - points_count: number of points in collection
                - status: collection status
            Returns None if collection doesn't exist
        """
        name = collection_name or self.collection_name

        if not self.collection_exists(name):
            logger.warning(f"Collection '{name}' does not exist")
            return None

        try:
            info = self.client.get_collection(collection_name=name)
            return {
                "name": name,
                "vector_size": info.config.params.vectors.size,
                "points_count": info.points_count,
                "status": info.status,
                "optimizer_status": info.optimizer_status,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

    def recreate_collection(
        self,
        collection_name: str | None = None,
        vector_size: int | None = None,
        distance: models.Distance = models.Distance.COSINE,
    ) -> bool:
        """Recreate a collection (delete if exists, then create new).

        Args:
            collection_name: Name of the collection (defaults to self.collection_name)
            vector_size: Size of the embedding vectors (defaults to settings.QDRANT_VECTOR_SIZE)
            distance: Distance metric for similarity (default: COSINE)

        Returns:
            bool: True if collection was recreated successfully, False otherwise
        """
        name = collection_name or self.collection_name

        # Delete if exists
        if self.collection_exists(name):
            if not self.delete_collection(name):
                logger.error(f"Failed to delete existing collection '{name}'")
                return False

        # Create new collection
        try:
            return self.create_collection(name, vector_size, distance)
        except ValueError:
            # Should not happen since we just deleted it
            logger.error(f"Unexpected error: collection '{name}' exists after deletion")
            return False

    def close(self) -> None:
        """Close the Qdrant client connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("Qdrant client connection closed")

    def __enter__(self) -> "QdrantClientWrapper":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return (
            f"QdrantClientWrapper(host={self.host}, port={self.port}, collection={self.collection_name})"
        )


# Global client instance
_qdrant_client: QdrantClientWrapper | None = None


def get_qdrant_client() -> QdrantClientWrapper:
    """Get or create global Qdrant client instance.

    Returns:
        QdrantClientWrapper: Singleton Qdrant client instance
    """
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClientWrapper()
    return _qdrant_client
