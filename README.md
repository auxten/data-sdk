# data-sdk
High level data sdk of chDB and ClickHouse

## Overview
The data-sdk provides a high-level interface for working with chDB and ClickHouse databases, offering powerful features for data manipulation, vector search, and ETL operations.

## Advanced API Usage

### 1. Data Source Connections
```python
from datasource import DataSource

# Connect to various data sources using a unified interface
revenuecat = DataSource.connect(
    "API",
    url="http://localhost:8000/v1",
    api_key="",
)

# File source connection (CSV)
db = DataSource.connect("file", path="data/comments.csv", format="CSV")
```

### 2. Query Building
```python
# Select specific fields
users = revenuecat.collection("users").select("id, name, subscription_status")

# Apply filters
active_users = users.filter("subscription_status", "=", "active")

# Join operations
subscribed_user_comments = active_users.join(
    comments, on={"users.id": "comments.user_id"}
)

# Pagination and limits
sample = subscribed_user_comments.limit(1000)
```

### 3. Vector Search
```python
from clickhouse_sdk import ClickHouseDB, Field, VectorIndex, Table, Query, connect

# Define a table with vector index
@dataclass
class Comments(Table):
    id: str = Field(primary_key=True, auto_uuid=True)
    user_id: str
    comment_text: str
    created_at: datetime.datetime = Field(default_now=True)

    class Meta:
        engine = "MergeTree"
        order_by = ("user_id", "created_at")
        indexes = [
            VectorIndex(
                name="comment_vector",
                source_field="comment_text",
                model="multilingual-e5-large",
                dim=1024,
                distance_function="cosineDistance",
            )
        ]

# Perform vector search
results = (
    db.table(Comments)
    .using_index("comment_vector")
    .search(query_text)
    .filter(created_at__gte=datetime.datetime.now() - datetime.timedelta(days=7))
    .limit(10)
    .execute()
)
```

### 4. Natural Language Queries
```python
# Generate SQL from natural language
analysis = sample.question("accumulate the total comments count for each user")
print(analysis.execute())
```

### 5. Data Export
```python
# Export to different formats
result = analysis.to_dataframe()  # Return pandas DataFrame
result = analysis.to_dict()  # Return dictionary structure
```

### 6. Visualization
```python
# Plot results
analysis.plot(x="name", y="total_comments", kind="bar")
```

## Key Features

1. **Unified Data Source Interface**: Connect to various data sources (APIs, files, databases) using a consistent interface.

2. **Advanced Query Building**: Build complex queries with a fluent interface supporting joins, filters, and aggregations.

3. **Vector Search**: Perform semantic search using vector embeddings with support for multiple models and distance functions.

4. **Natural Language Processing**: Convert natural language questions into SQL queries.

5. **Data Export**: Export results in multiple formats including pandas DataFrames and dictionaries.

6. **Visualization**: Built-in support for data visualization using matplotlib.

## Requirements

- Python 3.8+
- chDB
- pandas
- matplotlib

## Installation

```bash
pip install -r requirements.txt
```

## Examples

See the `demo_etl.ipynb` and `demo_vec1.py` files for complete examples of the SDK's capabilities.
