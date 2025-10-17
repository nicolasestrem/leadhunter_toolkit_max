"""
Data transformation utilities for UI layer
Handles conversion of pandas/numpy types to JSON-serializable formats
"""

import pandas as pd


def dict_to_json_safe(data):
    """Convert a dictionary with pandas/numpy types to a JSON-serializable dictionary.

    This function iterates through a dictionary and converts any non-serializable
    types, such as pandas Timestamps or numpy data types, into formats that can be
    safely encoded as JSON.

    Args:
        data (dict): A dictionary that may contain non-serializable types.

    Returns:
        dict: A dictionary with all values converted to JSON-serializable types.
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
    """Convert a single value to a JSON-safe type.

    This helper function handles the conversion of individual values, such as pandas
    Timestamps, numpy types, and NaNs, to their JSON-serializable equivalents.

    Args:
        value: The value to convert.

    Returns:
        The JSON-serializable value.
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
    """Convert a pandas DataFrame to a JSON-serializable list of dictionaries.

    This function first converts the DataFrame to a list of records and then ensures
    that each record is JSON-serializable by processing it with 'dict_to_json_safe'.

    Args:
        df (pd.DataFrame): The pandas DataFrame to convert.

    Returns:
        list: A list of JSON-serializable dictionaries.
    """
    # Convert to dict with default date format
    records = df.to_dict(orient="records")

    # Convert any remaining Timestamp objects to ISO strings
    return [dict_to_json_safe(record) for record in records]
