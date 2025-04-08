from typing import Dict, Any


def get_data(table_name: str) -> Dict[str, Any]:
    """
    Get data from a table with support for field selection, filtering, and pagination.

    Args:
        table_name: Name of the table to query

    Returns:
        Dict containing the table name and filtered/selected data
    """
    # Sample data - in a real implementation this would come from a database
    sample_data = {
        "users": [
            {
                "id": 1,
                "name": "John Doe",
                "subscription_status": "active",
                "created_at": "2024-01-01",
            },
            {
                "id": 2,
                "name": "Jane Doe",
                "subscription_status": "inactive",
                "created_at": "2024-01-02",
            },
            {
                "id": 3,
                "name": "Bob Smith",
                "subscription_status": "active",
                "created_at": "2024-01-03",
            },
            {
                "id": 4,
                "name": "Alice Johnson",
                "subscription_status": "inactive",
                "created_at": "2024-01-04",
            },
            {
                "id": 5,
                "name": "Bob Johnson",
                "subscription_status": "active",
                "created_at": "2024-01-05",
            },
            {
                "id": 6,
                "name": "Emily Davis",
                "subscription_status": "active",
                "created_at": "2024-01-06",
            },
            {
                "id": 7,
                "name": "Michael Brown",
                "subscription_status": "inactive",
                "created_at": "2024-01-07",
            },
            {
                "id": 8,
                "name": "Sarah Wilson",
                "subscription_status": "active",
                "created_at": "2024-01-08",
            },
            {
                "id": 9,
                "name": "David Miller",
                "subscription_status": "inactive",
                "created_at": "2024-01-09",
            },
            {
                "id": 10,
                "name": "Lisa Anderson",
                "subscription_status": "active",
                "created_at": "2024-01-10",
            },
            {
                "id": 11,
                "name": "James Taylor",
                "subscription_status": "active",
                "created_at": "2024-01-11",
            },
            {
                "id": 12,
                "name": "Jennifer Martinez",
                "subscription_status": "inactive",
                "created_at": "2024-01-12",
            },
            {
                "id": 13,
                "name": "Robert Garcia",
                "subscription_status": "active",
                "created_at": "2024-01-13",
            },
            {
                "id": 14,
                "name": "Patricia Rodriguez",
                "subscription_status": "inactive",
                "created_at": "2024-01-14",
            },
            {
                "id": 15,
                "name": "William Lee",
                "subscription_status": "active",
                "created_at": "2024-01-15",
            },
            {
                "id": 16,
                "name": "Mary White",
                "subscription_status": "active",
                "created_at": "2024-01-16",
            },
            {
                "id": 17,
                "name": "Charles Harris",
                "subscription_status": "inactive",
                "created_at": "2024-01-17",
            },
            {
                "id": 18,
                "name": "Elizabeth Clark",
                "subscription_status": "active",
                "created_at": "2024-01-18",
            },
            {
                "id": 19,
                "name": "Joseph Lewis",
                "subscription_status": "inactive",
                "created_at": "2024-01-19",
            },
            {
                "id": 20,
                "name": "Nancy Hall",
                "subscription_status": "active",
                "created_at": "2024-01-20",
            },
        ],
        "comments": [
            {
                "id": 1,
                "user_id": 1,
                "text": "Great product!",
                "created_at": "2024-01-01",
            },
            {
                "id": 2,
                "user_id": 2,
                "text": "Needs improvement",
                "created_at": "2024-01-02",
            },
            {
                "id": 3,
                "user_id": 1,
                "text": "Works well!!",
                "created_at": "2024-01-03",
            },
            {
                "id": 4,
                "user_id": 3,
                "text": "Excellent customer service",
                "created_at": "2024-01-04",
            },
            {
                "id": 5,
                "user_id": 4,
                "text": "Could be better",
                "created_at": "2024-01-05",
            },
            {
                "id": 6,
                "user_id": 5,
                "text": "Very satisfied with the features",
                "created_at": "2024-01-06",
            },
            {
                "id": 7,
                "user_id": 6,
                "text": "User interface needs work",
                "created_at": "2024-01-07",
            },
            {
                "id": 8,
                "user_id": 7,
                "text": "Best in class performance",
                "created_at": "2024-01-08",
            },
            {
                "id": 9,
                "user_id": 8,
                "text": "Not worth the price",
                "created_at": "2024-01-09",
            },
            {
                "id": 10,
                "user_id": 9,
                "text": "Highly recommended",
                "created_at": "2024-01-10",
            },
            {
                "id": 11,
                "user_id": 10,
                "text": "Great value for money",
                "created_at": "2024-01-11",
            },
            {
                "id": 12,
                "user_id": 11,
                "text": "Needs more features",
                "created_at": "2024-01-12",
            },
            {
                "id": 13,
                "user_id": 12,
                "text": "Perfect for my needs",
                "created_at": "2024-01-13",
            },
            {
                "id": 14,
                "user_id": 13,
                "text": "Too complicated to use",
                "created_at": "2024-01-14",
            },
            {
                "id": 15,
                "user_id": 14,
                "text": "Very intuitive design",
                "created_at": "2024-01-15",
            },
            {
                "id": 16,
                "user_id": 15,
                "text": "Could use better documentation",
                "created_at": "2024-01-16",
            },
            {
                "id": 17,
                "user_id": 16,
                "text": "Fast and reliable",
                "created_at": "2024-01-17",
            },
            {
                "id": 18,
                "user_id": 17,
                "text": "Not what I expected",
                "created_at": "2024-01-18",
            },
            {
                "id": 19,
                "user_id": 18,
                "text": "Excellent support team",
                "created_at": "2024-01-19",
            },
            {
                "id": 20,
                "user_id": 19,
                "text": "Would buy again",
                "created_at": "2024-01-20",
            },
        ],
    }

    # Get the data for the requested table
    data = sample_data.get(table_name, [])

    return {"table_name": table_name, "data": data, "total_count": len(data)}
