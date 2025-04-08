import clickhouse_connect
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import datetime

# Initialize ClickHouse client
client = clickhouse_connect.get_client(
    host='localhost',
    port=8123,
    username='default',
    password='',
    database='vector_search_db'
)

# Define table name and vector dimension
TABLE_NAME = 'comments'
VECTOR_DIM = 1024

# Load multilingual E5-large model
model = SentenceTransformer('intfloat/multilingual-e5-large')

# Create the table if it doesn't exist
def create_table():
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id UUID DEFAULT generateUUIDv4(),
        user_id String,
        comment_text String,
        created_at DateTime DEFAULT now(),
        embedding Array(Float32),
        CONSTRAINT valid_embedding CHECK length(embedding) = {VECTOR_DIM}
    )
    ENGINE = MergeTree()
    ORDER BY (user_id, created_at)
    """
    client.command(create_table_query)

# Generate text embedding vector
def generate_embedding(text):
    # For multilingual E5 model, query text needs "query:" prefix
    embedding = model.encode(f"query: {text}")
    return embedding.tolist()

# Insert a single comment
def insert_comment(user_id, comment_text):
    embedding = generate_embedding(comment_text)
    
    insert_query = f"""
    INSERT INTO {TABLE_NAME} (user_id, comment_text, embedding)
    VALUES (%(user_id)s, %(comment_text)s, %(embedding)s)
    """
    
    client.command(
        insert_query,
        parameters={
            'user_id': user_id,
            'comment_text': comment_text,
            'embedding': embedding
        }
    )

# Batch insert multiple comments
def batch_insert_comments(comments):
    user_ids = []
    texts = []
    embeddings = []
    
    for comment in comments:
        user_ids.append(comment['user_id'])
        texts.append(comment['comment_text'])
        embeddings.append(generate_embedding(comment['comment_text']))
    
    # Batch insert for better performance
    client.insert(
        TABLE_NAME,
        [user_ids, texts, embeddings],
        column_names=['user_id', 'comment_text', 'embedding']
    )

# Search for similar comments
def search_comments(query_text, time_range_days=None, user_id=None, limit=10):
    # 1. User provides query text
    # 2. Calculate embedding for query text
    query_embedding = generate_embedding(query_text)
    
    # 3. Set WHERE conditions
    conditions = []
    parameters = {'query_embedding': query_embedding}
    
    if time_range_days is not None:
        conditions.append("created_at >= %(start_date)s")
        start_date = datetime.datetime.now() - datetime.timedelta(days=time_range_days)
        parameters['start_date'] = start_date.strftime('%Y-%m-%d %H:%M:%S')
    
    if user_id is not None:
        conditions.append("user_id = %(user_id)s")
        parameters['user_id'] = user_id
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    # 4. Compute cosine distance
    # 5. Sort results by similarity
    search_query = f"""
    SELECT 
        id,
        user_id,
        comment_text,
        created_at,
        cosineDistance(embedding, %(query_embedding)s) AS similarity_distance
    FROM {TABLE_NAME}
    {where_clause}
    ORDER BY similarity_distance ASC
    LIMIT {limit}
    """
    
    # Execute query
    results = client.query(search_query, parameters=parameters)
    
    # Convert to list of dictionaries
    return results.named_results()

# Program entry point
def main():
    # Initialize table
    create_table()
    
    # Sample comment data
    sample_comments = [
        {
            'user_id': 'user1', 
            'comment_text': 'The new product update is amazing! I love the redesigned interface.'
        },
        {
            'user_id': 'user2', 
            'comment_text': 'I experienced some lag when using the app on my old phone.'
        },
        {
            'user_id': 'user3', 
            'comment_text': 'Is there any way to customize the dashboard? I would like to rearrange widgets.'
        },
        {
            'user_id': 'user1', 
            'comment_text': 'The customer support team was very helpful and resolved my issue quickly.'
        },
        {
            'user_id': 'user2', 
            'comment_text': 'I think the new pricing model is too expensive for small businesses.'
        }
    ]
    
    # Batch insert sample comments
    batch_insert_comments(sample_comments)
    
    # Perform vector search
    query = "How is the user interface of the product?"
    results = search_comments(
        query_text=query,
        time_range_days=7,  # Comments from the last 7 days
        limit=10
    )
    
    # Print search results
    print(f"Search results for query: '{query}'")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Comment: {result['comment_text']}")
        print(f"   User: {result['user_id']}")
        print(f"   Created: {result['created_at']}")
        print(f"   Similarity distance: {result['similarity_distance']:.4f}")

# Run the program
if __name__ == "__main__":
    main()


