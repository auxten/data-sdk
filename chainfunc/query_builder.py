from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import chdb
from chdbpyreader.data_reader import DataReader
from agent import Agent
import re


@dataclass
class JoinInfo:
    table_func: str
    conditions: Dict[str, str]
    alias: str


@dataclass
class QueryState:
    table: str
    select_fields: List[str] = None
    where_conditions: List[str] = None
    joins: List[JoinInfo] = None
    limit_value: Optional[int] = None
    explain: bool = False
    table_alias: str = None
    schema: Optional[Dict[str, str]] = None  # Store column name -> type mapping


class QueryBuilder:
    def __init__(
        self,
        table_func: str = None,
        reader: Optional[DataReader] = None,
        alias: Optional[str] = None,
        sql: Optional[str] = None,
    ):
        """Initialize QueryBuilder.

        Args:
            table_func: The table function string (e.g., "Python(reader)")
            reader: Optional DataReader instance
            alias: Optional table alias
            sql: Optional existing SQL query string
        """
        if sql:
            # If SQL is provided, use it directly
            self._sql = sql
            self.state = None
        else:
            # Otherwise initialize normally
            self.state = QueryState(table=table_func)
            self._sql = None
            self._reader = reader
            # Generate table alias if not provided
            if not alias:
                alias = self._generate_alias(table_func)
            self.state.table_alias = alias

    def _generate_alias(self, table_func: str) -> str:
        """Generate table alias from table function"""
        if table_func.startswith("Python("):
            # For Python(reader), use the table name from DataReader
            return self._reader.table_name if self._reader else "python"
        elif table_func.startswith("postgresql("):
            # Extract database and table name from postgresql function
            match = re.search(
                r"postgresql\([^,]+,\s*'([^']+)',\s*'([^']+)'", table_func
            )
            if match:
                return f"{match.group(1)}_{match.group(2)}"
            return "pg"
        elif table_func.startswith("file("):
            # Extract filename from file function
            match = re.search(r"file\('([^']+)',\s*'[^']+'", table_func)
            if match:
                # Get the last part of the path and remove extension
                filename = match.group(1).split("/")[-1].split(".")[0]
                # Use the table name from the file path
                return filename
            return "file"
        else:
            return "table"

    def select(self, fields: Union[str, List[str]]) -> "QueryBuilder":
        """Select specific fields from the table"""
        if isinstance(fields, str):
            fields = [field.strip() for field in fields.split(",")]
        self.state.select_fields = fields
        return self

    def filter(self, field: str, operator: str, value: Any) -> "QueryBuilder":
        """Add a WHERE condition to the query"""
        if self.state.where_conditions is None:
            self.state.where_conditions = []
        # Add table alias to field if it exists
        field_with_alias = (
            f"{self.state.table_alias}.{field}" if self.state.table_alias else field
        )
        condition = f"{field_with_alias} {operator} {self._format_value(value)}"
        self.state.where_conditions.append(condition)
        return self

    def join(
        self,
        other: Union[str, "QueryBuilder"],
        on: Dict[str, str],
        alias: Optional[str] = None,
    ) -> "QueryBuilder":
        """Add a JOIN condition to the query"""
        if self.state.joins is None:
            self.state.joins = []

        # Get the table function string and generate alias if needed
        if isinstance(other, QueryBuilder):
            table_func = other.state.table
            alias = other.state.table_alias  # Use the original QueryBuilder's alias
        else:
            table_func = other
            # Only generate alias if not provided
            if not alias:
                temp_builder = QueryBuilder(table_func)
                alias = temp_builder.state.table_alias

        self.state.joins.append(
            JoinInfo(table_func=table_func, conditions=on, alias=alias)
        )
        return self

    def limit(self, n: int) -> "QueryBuilder":
        """Limit the number of results"""
        self.state.limit_value = n
        return self

    def explain(self) -> "QueryBuilder":
        """Add EXPLAIN to the query"""
        self.state.explain = True
        return self

    def _format_value(self, value: Any) -> str:
        """Format values for SQL query"""
        if isinstance(value, str):
            return f"'{value}'"
        return str(value)

    def _build_sql(self) -> str:
        """Build the SQL query from the current state"""
        # If we have existing SQL, return it directly
        if self._sql:
            return self._sql

        parts = []

        # Add EXPLAIN if requested
        if self.state.explain:
            parts.append("EXPLAIN")

        # Add SELECT clause with table aliases
        if self.state.select_fields:
            fields = []
            for field in self.state.select_fields:
                if "." not in field:  # Add table alias if field doesn't have one
                    field = (
                        f"{self.state.table_alias}.{field}"
                        if self.state.table_alias
                        else field
                    )
                fields.append(field)

            # If we have joins, we need to include all fields from the joined table
            if self.state.joins:
                for join in self.state.joins:
                    if join.alias:
                        fields.append(f"{join.alias}.*")
                    else:
                        fields.append("*")

            select_fields = ", ".join(fields)
        else:
            # If no specific fields selected, select all fields from all tables
            select_fields = []
            # Add all fields from the main table
            if self.state.table_alias:
                select_fields.append(f"{self.state.table_alias}.*")
            else:
                select_fields.append("*")

            # Add all fields from joined tables
            if self.state.joins:
                for join in self.state.joins:
                    if join.alias:
                        select_fields.append(f"{join.alias}.*")
                    else:
                        select_fields.append("*")

            select_fields = ", ".join(select_fields)

        parts.append(f"SELECT {select_fields}")

        # Add FROM clause with table alias
        from_clause = self.state.table
        if self.state.table_alias:
            from_clause = f"{from_clause} AS {self.state.table_alias}"
        parts.append(f"FROM {from_clause}")

        # Add JOIN clauses with aliases
        if self.state.joins:
            for join in self.state.joins:
                join_clause = f"JOIN {join.table_func}"
                if join.alias:
                    join_clause += f" AS {join.alias}"
                conditions = []
                for k, v in join.conditions.items():
                    # Add table aliases to join conditions
                    left_table = (
                        self.state.table_alias if "." not in k else k.split(".")[0]
                    )
                    right_table = join.alias if "." not in v else v.split(".")[0]
                    left_field = k.split(".")[-1] if "." in k else k
                    right_field = v.split(".")[-1] if "." in v else v
                    conditions.append(
                        f"{left_table}.{left_field}={right_table}.{right_field}"
                    )
                join_clause += f" ON {' AND '.join(conditions)}"
                parts.append(join_clause)

        # Add WHERE clause
        if self.state.where_conditions:
            parts.append(f"WHERE {' AND '.join(self.state.where_conditions)}")

        # Add LIMIT clause
        if self.state.limit_value is not None:
            parts.append(f"LIMIT {self.state.limit_value}")

        return " ".join(parts)

    def execute(self, output_format: str = "PrettyCompact") -> str:
        """Execute the query using chdb and return the results"""
        # If SQL was already built (e.g., from a question), use it directly
        if self._sql:
            sql = self._sql
        else:
            sql = self._build_sql()
            self._sql = sql

        # If the query uses Python(reader) and we have a reader instance,
        # declare it globally for ClickHouse to use
        if "Python(reader)" in sql and hasattr(self, "_reader") and self._reader:
            global reader
            reader = self._reader

        # print(sql)
        return chdb.query(sql, output_format)

    def explain(self) -> str:
        """Show the query execution plan"""
        self.state.explain = True
        return self.execute()

    def __str__(self) -> str:
        """Return the current SQL query"""
        return self._build_sql()

    def get_schema(self) -> Dict[str, Union[List[str], Dict[str, str]]]:
        """Extract schema information from the query builder."""
        schema = {}

        # Get schema from the main table
        if self.state.table_alias:
            if self.state.schema:  # If we have column types
                schema[self.state.table_alias] = self.state.schema
            else:
                schema[self.state.table_alias] = self.state.select_fields or ["*"]

        # Get schema from joined tables
        if self.state.joins:
            for join in self.state.joins:
                if join.alias:
                    # For file sources, we can't know the exact columns
                    # For API sources, we can get columns from DataReader
                    if join.table_func.startswith("file("):
                        schema[join.alias] = ["*"]  # All columns from file
                    elif join.table_func.startswith("Python("):
                        # Try to get columns from DataReader if available
                        if hasattr(self, "_reader") and self._reader:
                            schema[join.alias] = self._reader.get_schema() or ["*"]
                        else:
                            schema[join.alias] = ["*"]
                    else:
                        schema[join.alias] = ["*"]  # Default to all columns

        return schema

    def question(self, question: str) -> "QueryBuilder":
        """Generate SQL from a natural language question using Agent."""
        agent = Agent()
        return agent.question_wrapper(self, question)

    def table(self, name: str) -> "QueryBuilder":
        """Create a QueryBuilder for the specified table"""
        self._table_name = name
        table_func = self._get_clickhouse_table_function()
        builder = QueryBuilder(table_func, self._reader)

        # Get schema information if available
        if self._reader:
            schema = self._reader.get_schema()
            builder.state.schema = schema

        return builder
