"""Quick test script for Day 5 Checkpoint 1."""

import logging

from app.vector_db import (
    CollectionSchema,
    get_qdrant_client,
    initialize_vector_db,
    verify_collection_schema,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Run checkpoint 1 tests."""
    print("\n" + "=" * 60)
    print("Day 5 Checkpoint 1: Qdrant Client & Collection Setup")
    print("=" * 60 + "\n")

    # Test 1: Client initialization and health check
    print("Test 1: Client Initialization & Health Check")
    print("-" * 60)
    client = get_qdrant_client()
    health = client.health_check()

    print(f"Status: {health['status']}")
    print(f"Connected: {health['connected']}")
    print(f"Host: {health['host']}:{health['port']}")
    print(f"Collections: {health.get('collections', [])}")

    if health["status"] != "healthy":
        print("❌ Qdrant health check failed!")
        return False

    print("✅ Test 1 passed\n")

    # Test 2: Collection schema information
    print("Test 2: Collection Schema Information")
    print("-" * 60)
    schema_info = CollectionSchema.get_schema_info()
    print(f"Collection Name: {schema_info['collection_name']}")
    print(f"Vector Size: {schema_info['vector_size']}")
    print(f"Distance Metric: {schema_info['distance_metric']}")
    print(f"Payload Fields: {len(schema_info['payload_schema'])} fields")
    print(f"Indexes: {len(schema_info['payload_indexes'])} indexes")
    print("✅ Test 2 passed\n")

    # Test 3: Full initialization
    print("Test 3: Full Vector DB Initialization")
    print("-" * 60)
    success = initialize_vector_db(recreate=True)

    if not success:
        print("❌ Vector DB initialization failed!")
        return False

    print("✅ Test 3 passed\n")

    # Test 4: Verify collection
    print("Test 4: Collection Verification")
    print("-" * 60)
    verification = verify_collection_schema(client)
    print(f"Collection Exists: {verification['exists']}")
    print(f"Schema Valid: {verification['schema_valid']}")

    if verification["info"]:
        info = verification["info"]
        print(f"Vector Size: {info['vector_size']}")
        print(f"Points Count: {info['points_count']}")
        print(f"Status: {info['status']}")

    if verification["errors"]:
        print(f"Errors: {verification['errors']}")
        print("❌ Schema validation failed!")
        return False

    print("✅ Test 4 passed\n")

    # Final summary
    print("=" * 60)
    print("🎉 ALL TESTS PASSED! 🎉")
    print("=" * 60)
    print("\n✅ Qdrant client wrapper implemented")
    print("✅ Collection schema defined")
    print("✅ Collection created with proper indexes")
    print("✅ Health checks working")
    print("✅ Schema verification working")
    print("\n🚀 Ready for Checkpoint 2: Embedding Pipeline\n")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
