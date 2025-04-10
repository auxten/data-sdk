from typing import Dict, Any, List
import numpy as np


def infer_data_types(data: Dict[str, List[Any]]) -> Dict[str, str]:
    """Infer column types from data.

    Args:
        data: Dictionary of column names to lists of values

    Returns:
        Dictionary mapping column names to ClickHouse types
    """
    type_mapping = {
        int: "Int64",
        float: "Float64",
        str: "String",
        bool: "Bool",
        np.int64: "Int64",
        np.float64: "Float64",
        np.bool_: "Bool",
    }

    schema = {}
    for col_name, values in data.items():
        if not values:
            schema[col_name] = "String"  # Default to String if no values
            continue

        # Get the first non-None value
        first_value = next((v for v in values if v is not None), None)
        if first_value is None:
            schema[col_name] = "String"  # Default to String if all values are None
            continue

        # Get the type of the first non-None value
        value_type = type(first_value)
        if value_type in type_mapping:
            schema[col_name] = type_mapping[value_type]
        else:
            schema[col_name] = "String"  # Default to String for unknown types

    return schema


def convert_to_columnar(data: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """Convert row-based data to columnar format.

    Args:
        data: List of dictionaries representing rows

    Returns:
        Dictionary mapping column names to lists of values
    """
    if not data:
        return {}

    # Get all column names
    columns = set()
    for row in data:
        columns.update(row.keys())

    # Initialize columnar data structure
    columnar_data = {col: [] for col in columns}

    # Fill in values
    for row in data:
        for col in columns:
            columnar_data[col].append(row.get(col))

    return columnar_data
