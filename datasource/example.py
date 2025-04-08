from datasource.data_source import DataSource


def example_postgres():
    # Connect to PostgreSQL
    db = DataSource.connect(
        "postgres",
        host="localhost",
        port=5432,
        database="mydb",
        user="user",
        password="password",
        schema="public",
    )

    # Create a query using the table function
    query = (
        db.table("users")
        .select("id, name, email")
        .filter("age", ">", 18)
        .join("orders", on={"users.id": "orders.user_id"})
        .limit(10)
    )

    print("PostgreSQL Query:")
    print(query.__str__())
    print()


def example_api():
    # Connect to an API
    api = DataSource.connect(
        "API",
        url="https://api.example.com/v1",
        api_key="your_api_key",
        headers={"Accept": "application/json"},
    )

    # Query the API using collection
    query = (
        api.collection("users")
        .select("id, name, subscription_status")
        .filter("subscription_status", "=", "active")
        .limit(100)
    )

    print("API Query:")
    print(query.__str__())
    print()


def example_file():
    # Connect to a CSV file
    csv_source = DataSource.connect("file", path="data/users.csv", format="CSV")

    # Query the CSV file
    query = csv_source.table("users_csv").select("*").filter("age", ">", 21)

    print("CSV File Query:")
    print(query.__str__())
    print()

    # Connect to a Parquet file
    parquet_source = DataSource.connect(
        "file", path="data/orders.parquet", format="Parquet"
    )

    # Query the Parquet file
    query = (
        parquet_source.table("orders_parquet")
        .select("order_id, customer_id, total")
        .filter("total", ">", 100)
        .limit(5)
    )

    print("Parquet File Query:")
    print(query.__str__())


if __name__ == "__main__":
    example_postgres()
    example_api()
    example_file()
