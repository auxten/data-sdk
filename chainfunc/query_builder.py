from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import chdb
from chdbpyreader.data_reader import DataReader
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


class QueryBuilder:
    def __init__(
        self,
        table_func: str,
        reader: Optional[DataReader] = None,
        alias: Optional[str] = None,
    ):
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
            select_fields = ", ".join(fields)
        else:
            select_fields = "*"
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
        sql = self._build_sql()
        self._sql = sql

        # If the query uses Python(reader) and we have a reader instance,
        # declare it globally for ClickHouse to use
        if "Python(reader)" in sql and self._reader:
            global reader
            reader = self._reader

        return chdb.query(sql, output_format)

    def explain(self) -> str:
        """Show the query execution plan"""
        self.state.explain = True
        return self.execute()

    def __str__(self) -> str:
        """Return the current SQL query"""
        return self._build_sql()
