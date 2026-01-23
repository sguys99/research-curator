"""Qdrant 컬렉션 스키마 정의 및 설정 유틸리티."""

import logging
from typing import Any

from qdrant_client.http import models

from app.core.config import settings
from app.vector_db.client import QdrantClientWrapper, get_qdrant_client

logger = logging.getLogger(__name__)


class CollectionSchema:
    """research_articles 컬렉션 스키마 정의."""

    # 컬렉션 메타데이터
    COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME
    VECTOR_SIZE = settings.QDRANT_VECTOR_SIZE
    DISTANCE_METRIC = models.Distance.COSINE

    # 페이로드 스키마(참조/검증용)
    PAYLOAD_SCHEMA = {
        "article_id": "string (UUID)",  # PostgreSQL CollectedArticle.id 참조
        "title": "string",  # 아티클 제목
        "summary": "string",  # 한국어 요약
        "source_type": "string",  # paper/news/report
        "category": "string",  # AI, ML, NLP 등
        "importance_score": "float",  # 0.0 - 1.0
        "collected_at": "string (ISO timestamp)",  # 수집 시각
        "metadata": "object",  # 추가 메타데이터(저자, 인용 등)
    }

    # 필터링 최적화를 위한 인덱스 설정
    PAYLOAD_INDEXES = [
        # source_type 필터링용 인덱스
        {
            "field_name": "source_type",
            "field_schema": models.PayloadSchemaType.KEYWORD,
        },
        # category 필터링용 인덱스
        {
            "field_name": "category",
            "field_schema": models.PayloadSchemaType.KEYWORD,
        },
        # importance_score 임계값 필터링용 인덱스
        {
            "field_name": "importance_score",
            "field_schema": models.PayloadSchemaType.FLOAT,
        },
        # collected_at 기간 필터링용 인덱스
        {
            "field_name": "collected_at",
            "field_schema": models.PayloadSchemaType.KEYWORD,
        },
    ]

    @classmethod
    def get_schema_info(cls) -> dict[str, Any]:  # 스키마 정보를 딕셔너리로 반환
        """전체 스키마 정보를 반환한다.

        Returns:
            dict: 컬렉션 이름, 벡터 크기, 페이로드 스키마 등
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


# 컬렉션 생성 및 인덱스 설정
def setup_collection(
    client: QdrantClientWrapper | None = None,
    recreate: bool = False,
) -> bool:
    """research_articles 컬렉션을 스키마/인덱스와 함께 설정한다.

    Args:
        client: Qdrant 클라이언트(기본값: 전역 클라이언트)
        recreate: True면 기존 컬렉션 삭제 후 재생성(기본값: False)

    Returns:
        bool: 설정 성공 여부

    Raises:
        VectorDBConnectionError: Qdrant 서버 연결 실패 시
    """
    if client is None:
        client = get_qdrant_client()  # 전역 싱글턴 클라이언트

    collection_name = CollectionSchema.COLLECTION_NAME

    try:
        # 컬렉션 존재 여부 확인
        exists = client.collection_exists(collection_name)

        if exists and not recreate:
            logger.info(f"Collection '{collection_name}' already exists. Skipping creation.")
            info = client.get_collection_info(collection_name)
            if info:
                logger.info(f"Collection info: {info}")
            return True

        # 컬렉션 재생성 또는 생성
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

        # 페이로드 인덱스 생성(필터링 최적화)
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
                # 하나 실패해도 다른 인덱스는 계속 생성

        # 컬렉션 설정 검증
        info = client.get_collection_info(collection_name)
        if info:
            logger.info(f"Collection '{collection_name}' setup complete: {info}")
        else:
            logger.warning("Collection created but unable to retrieve info")

        return True

    except Exception as e:
        logger.error(f"Error during collection setup: {e}")
        return False


# 컬렉션 생성/스키마 검증
def verify_collection_schema(client: QdrantClientWrapper | None = None) -> dict[str, Any]:
    """컬렉션 존재 여부와 스키마 일치 여부를 검증한다.

    Args:
        client: Qdrant 클라이언트(기본값: 전역 클라이언트)

    Returns:
        dict: 검증 결과
            - exists: 컬렉션 존재 여부
            - schema_valid: 스키마 일치 여부
            - info: 컬렉션 정보(존재 시)
            - errors: 검증 오류 목록(있는 경우)
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

    # 컬렉션 존재 여부 확인
    if not client.collection_exists(collection_name):
        result["errors"].append(f"Collection '{collection_name}' does not exist")
        return result

    result["exists"] = True

    # 컬렉션 정보 조회
    info = client.get_collection_info(collection_name)
    if info is None:
        result["errors"].append("Unable to retrieve collection information")
        return result

    result["info"] = info

    # 벡터 크기 검증
    if info["vector_size"] != CollectionSchema.VECTOR_SIZE:
        result["errors"].append(
            f"Vector size mismatch: expected {CollectionSchema.VECTOR_SIZE}, got {info['vector_size']}",
        )
    else:
        result["schema_valid"] = True

    return result


# 애플리케이션 시작 시 호출하는 메인 진입점
# src/app/api/main.py의 @app.on_event("startup")에서 호출
def initialize_vector_db(recreate: bool = False) -> bool:
    """벡터 DB를 초기화한다(메인 진입점).

    애플리케이션 시작 시 호출해 Qdrant 컬렉션 설정을 보장한다.

    Args:
        recreate: True면 기존 컬렉션이 있어도 재생성(기본값: False)

    Returns:
        bool: 초기화 성공 여부
    """
    logger.info("Initializing vector database...")

    try:
        # Qdrant 클라이언트 확보
        client = get_qdrant_client()

        # 헬스 체크
        health = client.health_check()
        if health["status"] != "healthy":
            logger.error(f"Qdrant health check failed: {health.get('error')}")
            return False

        logger.info(f"Qdrant server is healthy at {health['host']}:{health['port']}")
        logger.info(f"Available collections: {health.get('collections', [])}")

        # 컬렉션 설정
        success = setup_collection(client, recreate=recreate)
        if not success:
            logger.error("Failed to setup collection")
            return False

        # 스키마 검증
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
