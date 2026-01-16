"""Automatic insights generation from chart data."""

import pandas as pd
from .auto_detect import normalize_input, ChartType, get_column_by_type


def generate_insights(data, chart_type: ChartType) -> str:
    """
    Generate automatic insights based on data and chart type.

    Args:
        data: Input data (dict/list/DataFrame)
        chart_type: ChartType enum value

    Returns:
        Insights string with emoji bullets
    """
    df = normalize_input(data)

    if df.empty:
        return "⚠️ No data available for insights"

    if chart_type == ChartType.LINE_CHART:
        return generate_line_insights(df)
    elif chart_type == ChartType.BAR_CHART:
        return generate_bar_insights(df)
    elif chart_type == ChartType.PIE_CHART:
        return generate_pie_insights(df)
    elif chart_type == ChartType.TABLE:
        return generate_table_insights(df)
    elif chart_type == ChartType.METRIC_CARD:
        return generate_metric_insights(df)
    else:
        return "📊 Chart generated successfully"


def generate_line_insights(df: pd.DataFrame) -> str:
    """Generate insights for line charts (trend analysis)."""
    insights = []

    # Find numeric column
    numeric_col = get_column_by_type(df, 'numeric')
    if numeric_col is None:
        numeric_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    values = df[numeric_col].dropna()

    if len(values) < 2:
        return "📊 Insufficient data for trend analysis"

    # Calculate trend
    first_val = values.iloc[0]
    last_val = values.iloc[-1]
    change = last_val - first_val
    pct_change = (change / first_val * 100) if first_val != 0 else 0

    if change > 0:
        insights.append(f"📈 Upward trend: +{pct_change:.1f}% ({first_val:.1f} → {last_val:.1f})")
    elif change < 0:
        insights.append(f"📉 Downward trend: {pct_change:.1f}% ({first_val:.1f} → {last_val:.1f})")
    else:
        insights.append(f"➡️ Stable: no change from {first_val:.1f}")

    # Find peak and valley
    max_val = values.max()
    min_val = values.min()
    avg_val = values.mean()

    insights.append(f"📊 Range: {min_val:.1f} - {max_val:.1f} (avg: {avg_val:.1f})")

    # Volatility check
    std_dev = values.std()
    if std_dev / avg_val > 0.2:  # High volatility
        insights.append(f"⚠️ High volatility detected (σ={std_dev:.1f})")

    return " | ".join(insights)


def generate_bar_insights(df: pd.DataFrame) -> str:
    """Generate insights for bar charts (categorical comparison)."""
    insights = []

    categorical_col = get_column_by_type(df, 'categorical')
    numeric_col = get_column_by_type(df, 'numeric')

    if categorical_col is None:
        categorical_col = df.columns[0]
    if numeric_col is None:
        numeric_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    # Sort by value and find top 3
    sorted_df = df.sort_values(numeric_col, ascending=False)
    top_3 = sorted_df.head(3)

    top_names = top_3[categorical_col].tolist()
    top_values = top_3[numeric_col].tolist()

    insights.append(f"🥇 Top: {top_names[0]} ({top_values[0]:.1f})")

    if len(top_names) > 1:
        insights.append(f"🥈 2nd: {top_names[1]} ({top_values[1]:.1f})")

    # Total if numeric
    total = df[numeric_col].sum()
    insights.append(f"📊 Total: {total:.1f}")

    return " | ".join(insights)


def generate_pie_insights(df: pd.DataFrame) -> str:
    """Generate insights for pie charts (proportions)."""
    insights = []

    categorical_col = get_column_by_type(df, 'categorical')
    numeric_col = get_column_by_type(df, 'numeric')

    if categorical_col is None:
        categorical_col = df.columns[0]
    if numeric_col is None:
        numeric_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    total = df[numeric_col].sum()

    # Find dominant category
    max_row = df.loc[df[numeric_col].idxmax()]
    max_name = max_row[categorical_col]
    max_val = max_row[numeric_col]
    max_pct = (max_val / total * 100) if total > 0 else 0

    insights.append(f"🎯 Dominant: {max_name} ({max_pct:.1f}%)")

    # Check if balanced
    avg_pct = 100 / len(df)
    if max_pct > avg_pct * 1.5:
        insights.append(f"⚖️ Imbalanced distribution")
    else:
        insights.append(f"⚖️ Relatively balanced")

    insights.append(f"📊 {len(df)} categories")

    return " | ".join(insights)


def generate_table_insights(df: pd.DataFrame) -> str:
    """Generate insights for tables (data summary)."""
    insights = []

    insights.append(f"📋 {len(df)} rows × {len(df.columns)} columns")

    # Count column types
    numeric_cols = sum(1 for col in df.columns if get_column_by_type(df[[col]], 'numeric'))
    if numeric_cols > 0:
        insights.append(f"🔢 {numeric_cols} numeric columns")

    return " | ".join(insights)


def generate_metric_insights(df: pd.DataFrame) -> str:
    """Generate insights for single metric cards."""
    value = df.iloc[0, 0]

    if isinstance(value, (int, float)):
        if value > 1000:
            return f"📈 Large value: {value:,.0f}"
        elif value < 0:
            return f"📉 Negative value: {value:.1f}"
        else:
            return f"📊 Value: {value:.1f}"
    else:
        return f"💡 Value: {value}"
