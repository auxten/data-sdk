from typing import Dict, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass
from chainfunc.query_builder import QueryBuilder
from chdbpyreader.data_reader import DataReader


class SourceType(Enum):
    API = "API"
    POSTGRES = "postgres"
    FILE = "file"


@dataclass
class PostgresConfig:
    host: str
    port: int = 5432
    database: str = ""
    user: str = ""
    password: str = ""
    schema: Optional[str] = None


@dataclass
class APIConfig:
    url: str
    api_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class FileConfig:
    path: str
    format: str = "CSV"  # CSV, Parquet, etc.


class DataSource:
    def __init__(self, source_type: Union[str, SourceType], **kwargs):
        self.source_type = (
            SourceType(source_type) if isinstance(source_type, str) else source_type
        )
        self.config = self._parse_config(kwargs)
        self._table_name = None
        self._reader = None

    @staticmethod
    def connect(source_type: str, **kwargs) -> "DataSource":
        """Create a new DataSource connection"""
        return DataSource(source_type, **kwargs)

    def _parse_config(
        self, kwargs: Dict[str, Any]
    ) -> Union[PostgresConfig, APIConfig, FileConfig]:
        """Parse configuration based on source type"""
        if self.source_type == SourceType.POSTGRES:
            return PostgresConfig(**kwargs)
        elif self.source_type == SourceType.API:
            return APIConfig(**kwargs)
        elif self.source_type == SourceType.FILE:
            return FileConfig(**kwargs)
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")

    def _get_clickhouse_table_function(self) -> str:
        """Generate ClickHouse table function based on source type"""
        if self.source_type == SourceType.POSTGRES:
            config = self.config
            schema_part = f", schema='{config.schema}'" if config.schema else ""
            return (
                f"postgresql('{config.host}:{config.port}', "
                f"'{config.database}', '{self._table_name}', "
                f"'{config.user}', '{config.password}'{schema_part})"
            )
        elif self.source_type == SourceType.FILE:
            config = self.config
            return f"file('{config.path}', '{config.format}')"
        elif self.source_type == SourceType.API:
            # Initialize reader if not already done
            if not self._reader and self._table_name:
                self._reader = DataReader(self._table_name)
            return "Python(reader)"
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")

    def collection(self, name: str) -> QueryBuilder:
        """For API sources - specify the collection/endpoint"""
        if self.source_type != SourceType.API:
            raise ValueError("collection() method is only available for API sources")
        self._table_name = name
        return self.table(name)

    def table(self, name: str) -> QueryBuilder:
        """Create a QueryBuilder for the specified table"""
        self._table_name = name
        table_func = self._get_clickhouse_table_function()
        return QueryBuilder(table_func, self._reader)

    def execute_raw_query(self, query: str) -> str:
        """Execute a raw SQL query"""
        return f"{query} FROM {self._get_clickhouse_table_function()}"

    @staticmethod
    def set_question_func(func: Callable) -> None:
        """Set the question function for all QueryBuilder instances."""
        QueryBuilder._question_func = func

    # Alias for backward compatibility
    question = set_question_func
