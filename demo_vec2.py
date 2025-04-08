def demo_advanced_index_features():
    # Connect to ClickHouse
    db = connect(
        host="localhost",
        port=8123,
        username="default",
        password="",
        database="vector_search_db",
    )

    # Get index reference
    comment_index = db.get_index(Comments, "comment_vector")

    # Rebuild index if needed
    comment_index.rebuild()

    # Index stats
    stats = comment_index.stats()
    print(f"Index has {stats['vector_count']} vectors")
    print(f"Average query time: {stats['avg_query_time_ms']}ms")

    # Hybrid search - combine text search and vector similarity
    hybrid_results = (
        db.table(Comments)
        .hybrid_search(
            query_text="interface issues",
            text_fields=["comment_text"],
            vector_index="comment_vector",
            text_weight=0.3,  # 30% weight for text match
            vector_weight=0.7,  # 70% weight for semantic similarity
        )
        .limit(5)
        .execute()
    )

    # Search with multiple vectors (combining queries)
    multi_query_results = (
        db.table(Comments)
        .using_index("comment_vector")
        .multi_search(
            queries=["interface design", "performance issues"],
            weights=[0.7, 0.3],  # Weight importance of each query
        )
        .limit(5)
        .execute()
    )

    # Print multi-query results
    print("\nMulti-query search results:")
    for item in multi_query_results:
        print(f"- {item.comment_text} (score: {item.similarity_score:.3f})")
