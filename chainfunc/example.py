from query_builder import QueryBuilder


def main():
    # Basic select
    query = QueryBuilder("users").select("id, name, email")
    print("Basic select:")
    print(query.execute())
    print()

    # Select with filter
    query = QueryBuilder("users").select("*").filter("age", ">", 18)
    print("Select with filter:")
    print(query.execute())
    print()

    # Join example
    query = (
        QueryBuilder("users")
        .select("*")
        .join("orders", on={"users.id": "orders.user_id"})
        .filter("orders.total", ">", 100)
    )
    print("Join example:")
    print(query.execute())
    print()

    # Complex query with all features
    query = (
        QueryBuilder("users")
        .select("users.id, users.name, orders.total")
        .join("orders", on={"users.id": "orders.user_id"})
        .filter("users.age", ">", 18)
        .filter("orders.status", "=", "completed")
        .limit(10)
        .explain()
    )
    print("Complex query:")
    print(query.execute())


if __name__ == "__main__":
    main()
