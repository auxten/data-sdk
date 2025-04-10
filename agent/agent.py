from typing import Callable, Optional, Dict, List
import anthropic
from .prompt import build_sql_prompt
from config import ANTHROPIC_API_KEY


class Agent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    @classmethod
    def claude(cls, token: Optional[str] = None) -> "Agent":
        """Create an Agent instance with Claude client."""
        # Use provided token or fallback to config
        api_key = token or ANTHROPIC_API_KEY
        client = anthropic.Anthropic(api_key=api_key)
        return cls(client)

    def question_wrapper(
        self,
        query_builder: "QueryBuilder",
        question: str,
        cache: bool = True,
    ) -> "QueryBuilder":
        """Wrapper function that generates SQL from a question."""

        # Get the existing SQL and schema from the query builder
        existing_sql = str(query_builder)
        schema = query_builder.get_schema()

        # Build the prompt for Claude
        full_prompt = build_sql_prompt(
            question=question,
            schema=schema,
            existing_sql=existing_sql,
        )

        # Call Claude API to generate SQL
        response = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=64000,
            temperature=0.0 if cache else 0.7,
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
        )

        # Extract the SQL from Claude's response, remove the ```sql and ``` tags
        sql = (
            response.content[0]
            .text.strip()
            .replace("```sql", "")
            .replace("```", "")
            .strip()
        )
        # Create a new QueryBuilder with the generated SQL
        return query_builder.__class__(sql=sql)
