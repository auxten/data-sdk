from datasource import DataSource

# Use a Pandas-style connection configuration approach with unified interface
# chDB can use any Python function or API as a table
revenuecat = DataSource.connect(
    "API",
    url="http://localhost:8000/v1",
    api_key="xxx",
    headers={"Accept": "application/json"},
)

# select() method to specify fields
# Allows more granular control over returned data
users = revenuecat.collection("users").select("id, name, subscription_status")

# filter method with multiple operator support
# More expressive filtering operations with SQL-like clarity
active_users = users.filter("subscription_status", "=", "active")

# Database connections use the same unified interface
# Consistency across different data sources reduces cognitive load
# db = DataSource.connect(
#     "postgres", host="localhost", database="mydb", user="user", password="xxx"
# )

# File source connection (CSV)
db = DataSource.connect("file", path="data/comments.csv", format="CSV")

# SQL syntax sugar while maintaining DataFrame-style interface
# Familiar SQL concepts merged with modern object chaining
comments = db.table("comments").select("*")

# Add Pandas-style relational queries
# Enhanced join operations with clear relation definition
subscribed_user_comments = active_users.join(
    comments, on={"users.id": "comments.user_id"}
)

# Pandas-style pagination and limitations
# Efficient data handling without loading unnecessary records
sample = subscribed_user_comments.limit(1000)

# Show the query plan
print("Query Plan:")
print(sample)

# Execute the query and show results
print("\nResults:")
print(sample.execute())

# Execute with different output formats
print("\nResults as JSON:")
print(sample.execute(output_format="JSON"))

# # Define the LLM vendor for text-to-SQL
# question = LLM(LLM.claude(token="xxx")).question_func(prompt="")

# # Add async support for better performance
# # Non-blocking operations for heavy data processing
# # - `question` could be used as text-to-sql short hand, cache=True will
# # make sure the LLM generated SQL is determinstic unless question changed.
# # - `explain` will show the underlying function calling to get the result.
# analysis = (
#     sample.question("what's the top 10 mentioned words", cache=True).explain().execute()
# )

# # Rich output format options
# # Multiple export formats for different downstream needs
# result = analysis.to_dataframe()  # Return pandas DataFrame
# result = analysis.to_dict()  # Return dictionary structure
# result = analysis.to_chart("bar")  # Generate visualization directly in Notebook
