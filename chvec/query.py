from typing import Type, List, Dict, Any, Optional, Union
import numpy as np
from .models import Table, VectorIndex, Field
import datetime


class Query:
    def __init__(self, db, table_class: Type[Table]):
        self.db = db
        self.table_class = table_class
        self.table_name = table_class.__name__.lower()
        self._filters = []
        self._limit = None
        self._index_name = None
        self._search_text = None

    def using_index(self, index_name: str) -> "Query":
        """Specify which vector index to use for search"""
        self._index_name = index_name
        return self

    def search(self, text: str) -> "Query":
        """Set the search text for vector similarity search"""
        self._search_text = text
        return self

    def filter(self, **kwargs) -> "Query":
        """Add WHERE conditions to the query"""
        for field, value in kwargs.items():
            if "__" in field:
                field, op = field.split("__")
                if op == "gte":
                    self._filters.append(f"{field} >= {self._format_value(value)}")
                elif op == "lte":
                    self._filters.append(f"{field} <= {self._format_value(value)}")
                elif op == "eq":
                    self._filters.append(f"{field} = {self._format_value(value)}")
            else:
                self._filters.append(f"{field} = {self._format_value(value)}")
        return self

    def limit(self, n: int) -> "Query":
        """Set the maximum number of results to return"""
        self._limit = n
        return self

    def _format_value(self, value: Any) -> str:
        """Format a value for SQL insertion"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif isinstance(value, datetime.datetime):
            # Format datetime in ClickHouse's expected format: 'YYYY-MM-DD HH:MM:SS'
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        elif isinstance(value, np.ndarray):
            return f"[{','.join(map(str, value))}]"
        elif isinstance(value, list):
            return f"[{','.join(map(self._format_value, value))}]"
        elif isinstance(value, Field):
            if value.auto_uuid:
                return "generateUUIDv4()"
            elif value.default_now:
                return "now()"
            elif value.default is not None:
                return self._format_value(value.default)
            else:
                return "NULL"
        else:
            return f"'{str(value)}'"

    def insert(self, data: Union[Dict[str, Any], Table]) -> None:
        """Insert a single record"""
        if isinstance(data, Table):
            data = data.to_dict()

        # Get vector indexes
        indexes = self.table_class.get_indexes()

        # Generate embeddings for vector fields
        for index in indexes:
            if index.source_field in data:
                embedding = self._generate_embedding(data[index.source_field])
                data[index.embedding_column] = embedding

        # Build insert query
        columns = ", ".join(data.keys())
        values = ", ".join(self._format_value(v) for v in data.values())

        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({values})"

        cur = self.db.conn.cursor()
        cur.execute(query)
        cur.close()

    def insert_many(self, data_list: List[Union[Dict[str, Any], Table]]) -> None:
        """Insert multiple records"""
        if not data_list:
            return

        # Convert Table instances to dicts
        records = []
        for data in data_list:
            if isinstance(data, Table):
                records.append(data.to_dict())
            else:
                records.append(data)

        # Get vector indexes
        indexes = self.table_class.get_indexes()

        # Generate embeddings for vector fields
        for record in records:
            for index in indexes:
                if index.source_field in record:
                    embedding = self._generate_embedding(record[index.source_field])
                    record[index.embedding_column] = embedding

        # Build insert query
        columns = ", ".join(records[0].keys())
        values_list = []
        for record in records:
            values = ", ".join(self._format_value(v) for v in record.values())
            values_list.append(f"({values})")

        query = (
            f"INSERT INTO {self.table_name} ({columns}) VALUES {', '.join(values_list)}"
        )

        cur = self.db.conn.cursor()
        cur.execute(query)
        cur.close()

    def _generate_embedding(self, text: str) -> List[float]:
        """Mock embedding generation function"""
        # This is a placeholder - in real implementation, use a proper embedding model
        return list(np.random.rand(1024).astype(np.float32))

    def execute(self) -> List[Dict[str, Any]]:
        """Execute the query and return results"""
        if not self._index_name or not self._search_text:
            raise ValueError("Must specify index and search text for vector search")

        # Get the vector index configuration
        index = next(
            (
                idx
                for idx in self.table_class.get_indexes()
                if idx.name == self._index_name
            ),
            None,
        )
        if not index:
            raise ValueError(f"Vector index {self._index_name} not found")

        # Generate embedding for search text
        search_embedding = self._generate_embedding(self._search_text)
        embedding_str = "[" + ",".join(map(str, search_embedding)) + "]"

        # Build the query
        where_clause = " AND ".join(self._filters) if self._filters else "1=1"
        limit_clause = f"LIMIT {self._limit}" if self._limit else ""

        query = f"""
        SELECT 
            *,
            {index.distance_function}({index.embedding_column}, {embedding_str}) as similarity_score
        FROM {self.table_name}
        WHERE {where_clause}
        ORDER BY similarity_score ASC
        {limit_clause}
        """

        # Execute query
        cur = self.db.conn.cursor()
        print(query)
        cur.execute(query)
        results = []
        for row in cur:
            result = {}
            for i, col_name in enumerate(cur.column_names()):
                result[col_name] = row[i]
            results.append(result)
        cur.close()

        return results
