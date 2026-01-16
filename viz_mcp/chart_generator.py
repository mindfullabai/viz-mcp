"""Generic chart generation with Plotly."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from .auto_detect import ChartType, normalize_input, infer_type, get_column_by_type


def generate_chart(data, chart_type: ChartType, title: str = "") -> go.Figure:
    """
    Generate Plotly figure from data.

    Args:
        data: Input data (dict, list, DataFrame)
        chart_type: ChartType enum value
        title: Chart title (auto-generated if empty)

    Returns:
        Plotly Figure object
    """
    df = normalize_input(data)

    if df.empty:
        return create_empty_chart("No data to visualize")

    if chart_type == ChartType.LINE_CHART:
        return generate_line_chart(df, title)

    elif chart_type == ChartType.BAR_CHART:
        return generate_bar_chart(df, title)

    elif chart_type == ChartType.PIE_CHART:
        return generate_pie_chart(df, title)

    elif chart_type == ChartType.METRIC_CARD:
        return generate_metric_card(df, title)

    else:  # TABLE fallback
        return generate_table(df, title)


def generate_line_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Generate line chart (time series or sequential data)."""
    # Auto-detect x/y columns
    temporal_col = get_column_by_type(df, 'temporal')
    numeric_col = get_column_by_type(df, 'numeric')

    if temporal_col is None:
        # Fallback: use first column as x
        temporal_col = df.columns[0]

    if numeric_col is None:
        # Fallback: use second column or first if only one col
        numeric_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    fig = px.line(
        df,
        x=temporal_col,
        y=numeric_col,
        title=title or f"{numeric_col} over time",
        markers=True
    )

    fig.update_layout(
        template='plotly_white',
        hovermode='x unified',
        font=dict(family='Arial', size=12)
    )

    return fig


def generate_bar_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Generate bar chart (categorical comparison)."""
    categorical_col = get_column_by_type(df, 'categorical')
    numeric_col = get_column_by_type(df, 'numeric')

    if categorical_col is None:
        categorical_col = df.columns[0]

    if numeric_col is None:
        numeric_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    fig = px.bar(
        df,
        x=categorical_col,
        y=numeric_col,
        title=title or f"{numeric_col} by {categorical_col}"
    )

    fig.update_layout(
        template='plotly_white',
        font=dict(family='Arial', size=12)
    )

    return fig


def generate_pie_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Generate pie chart (proportions, max 5 categories recommended)."""
    names_col = get_column_by_type(df, 'categorical')
    values_col = get_column_by_type(df, 'numeric')

    if names_col is None:
        names_col = df.columns[0]

    if values_col is None:
        values_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

    fig = px.pie(
        df,
        names=names_col,
        values=values_col,
        title=title or f"{values_col} distribution"
    )

    fig.update_layout(
        template='plotly_white',
        font=dict(family='Arial', size=12)
    )

    return fig


def generate_metric_card(df: pd.DataFrame, title: str) -> go.Figure:
    """Generate single metric card display."""
    value = df.iloc[0, 0]

    # Create indicator chart (gauge-like)
    fig = go.Figure(go.Indicator(
        mode="number",
        value=float(value) if isinstance(value, (int, float)) else 0,
        title={'text': title or str(df.columns[0])},
    ))

    fig.update_layout(
        template='plotly_white',
        font=dict(family='Arial', size=24),
        height=300
    )

    return fig


def generate_table(df: pd.DataFrame, title: str) -> go.Figure:
    """Generate interactive table display."""
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(df.columns),
            fill_color='paleturquoise',
            align='left',
            font=dict(size=14, color='black')
        ),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color='lavender',
            align='left',
            font=dict(size=12)
        )
    )])

    fig.update_layout(
        title=title or "Data Table",
        template='plotly_white'
    )

    return fig


def create_empty_chart(message: str) -> go.Figure:
    """Create placeholder chart for empty data."""
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=20, color="gray")
    )

    fig.update_layout(
        template='plotly_white',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig
