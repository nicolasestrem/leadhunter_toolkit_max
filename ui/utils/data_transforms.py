"""
Data transformation utilities for UI layer
Handles conversion of pandas/numpy types to JSON-serializable formats
"""

import pandas as pd


def dict_to_json_safe(data):
    """
    Convert a dict with pandas/numpy types to JSON-serializable dict.

    Args:
        data: dict potentially containing Timestamp or numpy types

    Returns:
        Dict with JSON-serializable values
    """
    result = {}
    for key, value in data.items():
        # Handle lists and arrays
        if isinstance(value, (list, tuple)):
            result[key] = [dict_to_json_safe_value(v) for v in value]
        else:
            result[key] = dict_to_json_safe_value(value)
    return result


def dict_to_json_safe_value(value):
    """
    Convert a single value to JSON-safe type.

    Args:
        value: Any value potentially containing pandas/numpy types

    Returns:
        JSON-serializable value
    """
    # Check for None/NaN (use try/except to avoid array ambiguity)
    try:
        if pd.isna(value):
            return None
    except (ValueError, TypeError):
        # Value is an array or non-scalar, continue processing
        pass

    # Handle specific types
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    elif isinstance(value, (list, tuple)):
        return [dict_to_json_safe_value(v) for v in value]
    elif hasattr(value, 'item'):  # numpy scalar types
        return value.item()
    elif isinstance(value, dict):
        return dict_to_json_safe(value)
    else:
        return value


def dataframe_to_json_safe(df):
    """
    Convert DataFrame to JSON-serializable dict, handling Timestamps and other pandas types.

    Args:
        df: pandas DataFrame

    Returns:
        List of dicts with JSON-serializable values
    """
    # Convert to dict with default date format
    records = df.to_dict(orient="records")

    # Convert any remaining Timestamp objects to ISO strings
    return [dict_to_json_safe(record) for record in records]
