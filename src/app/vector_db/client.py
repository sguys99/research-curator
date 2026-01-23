"""벡터 DB 연결/작업을 위한 Qdrant 클라이언트 래퍼."""

import logging
import threading
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings
from app.vector_db.exceptions import VectorDBConnectionError

logger = logging.getLogger(__name__)


# DB 연결 및 컬렉션(RDB 테이블과 유사) 관리를 담당
class QdrantClientWrapper:
    """Qdrant 연결 관리 및 유틸리티를 포함한 클라이언트 래퍼."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        collection_name: str | None = None,
    ) -> None:
        """Qdrant 클라이언트를 초기화한다.

        Args:
            host: Qdrant 서버 호스트(기본값: settings.QDRANT_HOST)
            port: Qdrant 서버 포트(기본값: settings.QDRANT_PORT)
            collection_name: 기본 컬렉션 이름(기본값: settings.QDRANT_COLLECTION_NAME)
        """
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME  # research_articles
        self._client: QdrantClient | None = None
        self._client_lock = threading.Lock()

    @property  # 메서드를 속성처럼 접근(예: .client), Lazy initialization(지연 초기화, 사용할 때 연결)
    def client(self) -> QdrantClient:
        """Qdrant 클라이언트를 생성하거나 반환한다.

        Returns:
            QdrantClient: 활성 Qdrant 클라이언트

        Raises:
            VectorDBConnectionError: Qdrant 서버 연결 실패 시
        """
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    try:
                        self._client = QdrantClient(host=self.host, port=self.port)
                        logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
                    except Exception as e:
                        logger.error(f"Failed to connect to Qdrant: {e}")
                        raise VectorDBConnectionError(
                            f"Unable to connect to Qdrant at {self.host}:{self.port}",
                        ) from e
        return self._client

    def health_check(self) -> dict[str, Any]:
        """Qdrant 서버 상태와 연결 여부를 확인한다.

        Returns:
            dict: 상태 정보
                - status: "healthy" 또는 "unhealthy"
                - connected: 연결 여부
                - host: Qdrant 서버 호스트
                - port: Qdrant 서버 포트
                - collections: 컬렉션 이름 목록(연결 시)
                - error: 오류 메시지(비정상 시)
        """
        try:
            # 컬렉션 목록을 조회해 연결 확인
            collections = self.client.get_collections()  # QdrantClient의 메서드
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
        """Qdrant에 컬렉션이 존재하는지 확인한다.

        Args:
            collection_name: 확인할 컬렉션 이름(기본값: self.collection_name)

        Returns:
            bool: 존재 여부
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
        """Qdrant에 새 컬렉션을 생성한다.

        Args:
            collection_name: 컬렉션 이름(기본값: self.collection_name)
            vector_size: 임베딩 벡터 크기(기본값: settings.QDRANT_VECTOR_SIZE)
            distance: 유사도 거리 척도(기본값: COSINE)
            on_disk_payload: 페이로드 디스크 저장 여부(기본값: True)

        Returns:
            bool: 생성 성공 여부

        Raises:
            ValueError: 이미 컬렉션이 존재하는 경우
        """
        name = collection_name or self.collection_name
        size = vector_size or settings.QDRANT_VECTOR_SIZE

        # 컬렉션 존재 여부 확인
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
        """Qdrant에서 컬렉션을 삭제한다.

        Args:
            collection_name: 삭제할 컬렉션 이름(기본값: self.collection_name)

        Returns:
            bool: 삭제 성공 여부
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
        """컬렉션 정보를 조회한다.

        Args:
            collection_name: 조회할 컬렉션 이름(기본값: self.collection_name)

        Returns:
            dict: 컬렉션 정보
                - name: 컬렉션 이름
                - vector_size: 임베딩 벡터 크기
                - points_count: 포인트 개수
                - status: 컬렉션 상태
            컬렉션이 없으면 None 반환
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
        """컬렉션을 재생성한다(존재 시 삭제 후 재생성).

        Args:
            collection_name: 컬렉션 이름(기본값: self.collection_name)
            vector_size: 임베딩 벡터 크기(기본값: settings.QDRANT_VECTOR_SIZE)
            distance: 유사도 거리 척도(기본값: COSINE)

        Returns:
            bool: 재생성 성공 여부
        """
        name = collection_name or self.collection_name

        # 존재하면 삭제
        if self.collection_exists(name):
            if not self.delete_collection(name):
                logger.error(f"Failed to delete existing collection '{name}'")
                return False

        # 새 컬렉션 생성
        try:
            return self.create_collection(name, vector_size, distance)
        except ValueError:
            # 방금 삭제했으므로 발생하면 안 됨
            logger.error(f"Unexpected error: collection '{name}' exists after deletion")
            return False

    def close(self) -> None:
        """Qdrant 클라이언트 연결을 종료한다."""
        if self._client is not None:
            with self._client_lock:
                if self._client is not None:
                    self._client.close()
                    self._client = None
                    logger.info("Qdrant client connection closed")

    def __enter__(self) -> "QdrantClientWrapper":
        """컨텍스트 매니저 진입."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """컨텍스트 매니저 종료."""
        self.close()

    def __repr__(self) -> str:
        """클라이언트 문자열 표현."""
        return (
            f"QdrantClientWrapper(host={self.host}, port={self.port}, collection={self.collection_name})"
        )


# 전역 클라이언트 인스턴스(싱글턴, 앱 전역 동일 연결 재사용)
_qdrant_client: QdrantClientWrapper | None = None
_qdrant_client_lock = threading.Lock()


def get_qdrant_client() -> QdrantClientWrapper:
    """전역 Qdrant 클라이언트 인스턴스를 반환한다.

    Returns:
        QdrantClientWrapper: 싱글턴 Qdrant 클라이언트
    """
    global _qdrant_client
    if _qdrant_client is None:
        with _qdrant_client_lock:
            if _qdrant_client is None:
                _qdrant_client = QdrantClientWrapper()
    return _qdrant_client
