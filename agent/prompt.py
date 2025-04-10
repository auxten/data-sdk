from typing import List, Dict, Optional


def build_sql_prompt(
    question: str,
    schema: Optional[Dict[str, List[str]]] = None,
    existing_sql: Optional[str] = None,
) -> str:
    """Build a prompt for Claude to generate SQL from a natural language question."""

    prompt = """You are a SQL expert. Your task is to generate a ClickHouse SQL query based on the user's question.

Follow these rules:
1. DO NOT use CTEs (WITH clauses). Instead, use direct queries with proper JOINs
2. Use proper table aliases
3. Use ClickHouse-specific functions when needed
4. Format the SQL query for readability:
   - Keep opening and closing parentheses ( ) on the same line
   - Use proper indentation for subqueries
   - Align JOIN conditions
5. Add comments to explain complex parts
6. Handle NULL values appropriately
7. Use proper JOIN syntax
8. Use proper GROUP BY and ORDER BY clauses when needed
9. Consider column types when writing conditions and functions

Example of correct formatting:
SELECT t1.*, t2.column 
FROM table1 t1 
JOIN table2 t2 ON (t1.id = t2.id)
WHERE t1.status = 'active'

Example of incorrect formatting (DO NOT DO THIS):
SELECT t1.*, t2.column 
FROM table1 t1 
JOIN table2 t2 ON (
    t1.id = t2.id
)
WHERE t1.status = 'active'

Just return the SQL query, no other text.

"""

    if schema:
        prompt += "\nAvailable tables and columns:\n"
        for table, columns in schema.items():
            if isinstance(columns, dict):  # If columns is a dict of name -> type
                prompt += f"- {table}:\n"
                for col_name, col_type in columns.items():
                    prompt += f"  - {col_name}: {col_type}\n"
            else:  # If columns is just a list of names
                prompt += f"- {table}: {', '.join(columns)}\n"

    if existing_sql:
        prompt += f"\nExisting SQL query to use:\n```sql\n{existing_sql}\n```\n"

    prompt += f"\nUser question: {question}\n\n"
    prompt += "Generate a SQL query that answers the question. Use direct queries with JOINs, not CTEs. Keep parentheses pairs on the same line.\n"

    return prompt
