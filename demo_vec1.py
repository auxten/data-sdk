from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from clickhouse_sdk import ClickHouseDB, Field, VectorIndex, Table, Query, connect
import datetime


# Define the Comments model with vector index
@dataclass
class Comments(Table):
    id: str = Field(primary_key=True, auto_uuid=True)
    user_id: str
    comment_text: str
    created_at: datetime.datetime = Field(default_now=True)

    class Meta:
        engine = "MergeTree"
        order_by = ("user_id", "created_at")
        # Define vector index on the comment_text field
        indexes = [
            VectorIndex(
                name="comment_vector",
                source_field="comment_text",
                model="multilingual-e5-large",
                dim=1024,
                distance_function="cosineDistance",
            )
        ]


# Main function demonstrating SDK usage
def main():
    # Connect to ClickHouse
    db = connect(
        host="localhost",
        port=8123,
        username="default",
        password="",
        database="vector_search_db",
    )

    # Create table with vector index (automatically handles the internal embedding field)
    db.create_table(Comments)

    # Sample comment data - no need to handle embeddings explicitly
    sample_comments = [
        {
            "user_id": "user1",
            "comment_text": "The new product update is amazing! I love the redesigned interface.",
        },
        {
            "user_id": "user2",
            "comment_text": "I experienced some lag when using the app on my old phone.",
        },
        {
            "user_id": "user3",
            "comment_text": "Is there any way to customize the dashboard? I would like to rearrange widgets.",
        },
        {
            "user_id": "user1",
            "comment_text": "The customer support team was very helpful and resolved my issue quickly.",
        },
        {
            "user_id": "user2",
            "comment_text": "I think the new pricing model is too expensive for small businesses.",
        },
    ]

    # Insert comments (SDK handles embedding generation via the index)
    db.table(Comments).insert_many(sample_comments)

    # Perform vector search with index-based API
    query_text = "How is the user interface of the product?"

    # Query using the vector index
    results = (
        db.table(Comments)
        .using_index("comment_vector")
        .search(query_text)
        .filter(created_at__gte=datetime.datetime.now() - datetime.timedelta(days=7))
        .limit(10)
        .execute()
    )

    # Print search results
    print(f"Search results for query: '{query_text}'")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Comment: {result.comment_text}")
        print(f"   User: {result.user_id}")
        print(f"   Created: {result.created_at}")
        print(f"   Similarity score: {result.similarity_score:.4f}")


# Run the demos
if __name__ == "__main__":
    main()
