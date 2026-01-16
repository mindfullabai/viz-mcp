"""Auto-detection algorithm for optimal chart type selection."""

from enum import Enum
from typing import Any, Tuple
import pandas as pd
from datetime import datetime


class ChartType(Enum):
    """Supported chart types."""
    METRIC_CARD = "metric"
    LINE_CHART = "line"
    BAR_CHART = "bar"
    PIE_CHART = "pie"
    TABLE = "table"


def normalize_input(data: Any) -> pd.DataFrame:
    """
    Normalize input to pandas DataFrame.

    Handles:
    - dict: single row
    - list of dicts: multiple rows
    - DataFrame: passthrough
    """
    if isinstance(data, pd.DataFrame):
        return data

    if isinstance(data, dict):
        # Single value dict → single row DataFrame
        return pd.DataFrame([data])

    if isinstance(data, list):
        if not data:
            return pd.DataFrame()

        # List of dicts → DataFrame
        if isinstance(data[0], dict):
            return pd.DataFrame(data)

        # List of primitives → single column
        return pd.DataFrame({'value': data})

    # Single primitive → 1x1 DataFrame
    return pd.DataFrame({'value': [data]})


def infer_type(series: pd.Series) -> str:
    """
    Infer semantic type of a pandas Series.

    Returns: 'numeric', 'temporal', 'categorical'
    """
    # Check temporal
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'temporal'

    # Try parsing as dates
    if series.dtype == 'object':
        try:
            pd.to_datetime(series, errors='raise')
            return 'temporal'
        except:
            pass

    # Check numeric
    if pd.api.types.is_numeric_dtype(series):
        return 'numeric'

    # Default: categorical
    return 'categorical'


def auto_detect_chart_type(data: Any) -> Tuple[ChartType, float]:
    """
    Auto-detect optimal chart type from data structure.

    Args:
        data: JSON-serializable data (dict, list, nested)

    Returns:
        (chart_type, confidence): Chart type and confidence score (0.0-1.0)

    Decision matrix:
    - Single value (1x1) → Metric Card (1.0)
    - Date + Numeric → Line Chart (0.9)
    - Category + Numeric (≤5) → Pie Chart (0.85)
    - Category + Numeric (6-10) → Bar Chart (0.85)
    - Category + Numeric (>10) → Table (0.6)
    - Multi-dimensional (3+ cols) → Table (0.7)
    - Default fallback → Table (0.5)
    """
    # Step 1: Normalize to DataFrame
    df = normalize_input(data)

    if df.empty:
        return ChartType.TABLE, 0.5

    # Step 2: Analyze structure
    shape = df.shape
    n_cols = len(df.columns)

    col_types = {col: infer_type(df[col]) for col in df.columns}

    has_temporal = any(t == 'temporal' for t in col_types.values())
    has_numeric = any(t == 'numeric' for t in col_types.values())
    has_categorical = any(t == 'categorical' for t in col_types.values())

    # Step 3: Decision tree

    # Single value
    if shape == (1, 1):
        return ChartType.METRIC_CARD, 1.0

    # Time series: temporal + numeric
    if has_temporal and has_numeric:
        return ChartType.LINE_CHART, 0.9

    # Categorical + numeric: bar or pie
    if has_categorical and has_numeric:
        # Find categorical column
        categorical_col = next(
            col for col, t in col_types.items() if t == 'categorical'
        )
        n_categories = df[categorical_col].nunique()

        if n_categories <= 5:
            return ChartType.PIE_CHART, 0.85
        elif n_categories <= 10:
            return ChartType.BAR_CHART, 0.85
        else:
            # Too many categories for chart
            return ChartType.TABLE, 0.6

    # Multi-dimensional: table fallback
    if n_cols >= 3:
        return ChartType.TABLE, 0.7

    # Default safe fallback
    return ChartType.TABLE, 0.5


def get_column_by_type(df: pd.DataFrame, target_type: str) -> str:
    """
    Get first column name matching target type.

    Args:
        df: DataFrame
        target_type: 'numeric', 'temporal', 'categorical'

    Returns:
        Column name or None
    """
    for col in df.columns:
        if infer_type(df[col]) == target_type:
            return col
    return None
