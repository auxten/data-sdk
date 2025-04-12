import chdb
from typing import Type, Optional, Dict, Any
from .models import Table, VectorIndex
from .query import Query


class ClickHouseDB:
    def __init__(self, database: str = "default"):
        self.conn = chdb.connect(database)
        self.database = database
        self._tables: Dict[str, Type[Table]] = {}

    def create_table(self, table_class: Type[Table]):
        """Create a table with vector index support"""
        table_name = table_class.__name__.lower()
        self._tables[table_name] = table_class

        # Get table schema and indexes
        schema = table_class.get_schema()
        indexes = table_class.get_indexes()

        # Create the table with vector column
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
            {schema}
        )
        ENGINE = {table_class.Meta.engine}
        ORDER BY {table_class.Meta.order_by[0]}
        """

        cur = self.conn.cursor()
        print(create_table_sql)
        cur.execute(create_table_sql)

        # Create vector indexes if any
        for index in indexes:
            if isinstance(index, VectorIndex):
                # Create the vector column if it doesn't exist
                alter_sql = f"""
                ALTER TABLE {table_name} 
                ADD COLUMN IF NOT EXISTS {index.embedding_column} Array(Float32)
                """
                cur.execute(alter_sql)

        cur.close()

    def table(self, table_class: Type[Table]) -> Query:
        """Get a query builder for the specified table"""
        table_name = table_class.__name__.lower()
        if table_name not in self._tables:
            raise ValueError(f"Table {table_name} not found")
        return Query(self, table_class)

    def close(self):
        """Close the database connection"""
        self.conn.close()


def connect(backend: str = "chdb", database: str = "default") -> ClickHouseDB:
    """Create a new database connection"""
    if backend != "chdb":
        raise ValueError("Only chdb backend is supported")
    return ClickHouseDB(database)
