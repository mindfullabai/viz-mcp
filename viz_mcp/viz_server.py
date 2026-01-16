#!/usr/bin/env python3
"""
viz-mcp: MCP server for data visualization from tracking-mcp.

Provides tools and resources for creating charts, heatmaps, and dashboards
from tracking data.
"""

import json
import os
import sqlite3
import uuid
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
from mcp.server import Server
from mcp.types import TextContent, ImageContent, EmbeddedResource, Tool, Resource

# Import auto-detection, chart generation, and insights
from .auto_detect import auto_detect_chart_type, ChartType
from .chart_generator import generate_chart
from .insights_generator import generate_insights

# ============================================================================
# CONFIGURATION
# ============================================================================

TRACKING_DB = Path(os.environ.get(
    "TRACKING_DB_PATH",
    Path.home() / "Desktop/Projects/04-Personal-Tools/tracking-mcp/data/tracking.db"
))

EXPORT_DIR = Path(os.environ.get(
    "EXPORT_DIR",
    Path.home() / "Desktop/Projects/04-Personal-Tools/viz-mcp/exports"
))

EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get SQLite database connection to tracking-mcp."""
    if not TRACKING_DB.exists():
        raise FileNotFoundError(f"Tracking database not found: {TRACKING_DB}")

    conn = sqlite3.connect(str(TRACKING_DB))
    conn.row_factory = sqlite3.Row
    return conn


def query_events(
    entity_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None
) -> list[dict]:
    """Query tracking events from database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT id, entity_type, entity_id, date, data, created_at FROM tracking_events WHERE 1=1"
    params = []

    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date ASC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    events = []
    for row in rows:
        event = dict(row)
        event["data"] = json.loads(event["data"])
        events.append(event)

    conn.close()
    return events


# ============================================================================
# CHART GENERATION HELPERS
# ============================================================================

def save_matplotlib_chart(fig, filename: str) -> Path:
    """Save matplotlib figure to exports directory."""
    output_path = EXPORT_DIR / filename
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return output_path


def save_plotly_chart(fig, filename: str, format: str = "html", metadata: dict = None) -> Path:
    """
    Save plotly figure to exports directory with metadata.

    Args:
        fig: Plotly figure
        filename: Output filename
        format: 'html' or 'png'
        metadata: Optional metadata dict with keys: chart_id, chart_type, title, data_points, description, insights
    """
    output_path = EXPORT_DIR / filename

    if format == "html":
        # Extract metadata
        chart_id = metadata.get('chart_id', str(uuid.uuid4())) if metadata else str(uuid.uuid4())
        chart_type = metadata.get('chart_type', 'unknown') if metadata else 'unknown'
        title = metadata.get('title', 'Untitled') if metadata else 'Untitled'
        data_points = metadata.get('data_points', 0) if metadata else 0
        created_at = metadata.get('created_at', datetime.now().isoformat()) if metadata else datetime.now().isoformat()
        description = metadata.get('description', '') if metadata else ''
        insights = metadata.get('insights', '') if metadata else ''

        # Generate chart div (without full HTML)
        chart_div = fig.to_html(
            include_plotlyjs='cdn',
            full_html=False,
            config={'responsive': True, 'displayModeBar': True}
        )

        # Build complete HTML with template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="chart-id" content="{chart_id}">
    <meta name="chart-type" content="{chart_type}">
    <meta name="chart-title" content="{title}">
    <meta name="created-at" content="{created_at}">
    <meta name="data-points" content="{data_points}">
    <meta name="generator" content="viz-mcp">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px 32px;
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .header .meta {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .description {{
            background: #f8f9fa;
            padding: 20px 32px;
            border-left: 4px solid #667eea;
            margin: 20px 32px;
            border-radius: 4px;
        }}
        .description p {{
            color: #4a5568;
            line-height: 1.6;
            font-size: 15px;
        }}
        .chart-container {{
            padding: 20px 32px;
        }}
        .insights {{
            background: #e6fffa;
            border-left: 4px solid #38b2ac;
            padding: 16px 32px;
            margin: 20px 32px 32px;
            border-radius: 4px;
        }}
        .insights h3 {{
            color: #234e52;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .insights p {{
            color: #2c5282;
            line-height: 1.6;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                <span>{chart_type.upper()} Chart</span> •
                <span>{data_points} data points</span> •
                <span>{created_at[:10]}</span>
            </div>
        </div>

        {f'<div class="description"><p>{description}</p></div>' if description else ''}

        <div class="chart-container">
            {chart_div}
        </div>

        {f'<div class="insights"><h3>💡 Insights</h3><p>{insights}</p></div>' if insights else ''}
    </div>
</body>
</html>"""

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

    elif format == "png":
        fig.write_image(str(output_path))
    else:
        raise ValueError(f"Unsupported format: {format}")

    return output_path


def save_multi_chart_dashboard(charts_data: list, dashboard_title: str, dashboard_description: str = "") -> Path:
    """
    Create multi-chart dashboard HTML.

    Args:
        charts_data: List of dicts with keys: fig, chart_type, title, description, insights, data_points
        dashboard_title: Dashboard title
        dashboard_description: Dashboard description (optional)

    Returns:
        Path to saved HTML file
    """
    # Generate chart divs
    chart_sections = []

    for i, chart_info in enumerate(charts_data, 1):
        fig = chart_info['fig']
        chart_type = chart_info['chart_type']
        title = chart_info['title']
        description = chart_info.get('description', '')
        insights = chart_info.get('insights', '')

        # Generate chart div
        chart_div = fig.to_html(
            include_plotlyjs='cdn' if i == 1 else False,  # Include Plotly.js only once
            full_html=False,
            config={'responsive': True, 'displayModeBar': True}
        )

        # Build section HTML
        section_html = f"""
        <div class="chart-section">
            <div class="chart-header">
                <h2>{title}</h2>
                <span class="chart-badge">{chart_type.upper()}</span>
            </div>
            {f'<div class="description"><p>{description}</p></div>' if description else ''}
            <div class="chart-container">
                {chart_div}
            </div>
            {f'<div class="insights"><h3>💡 Insights</h3><p>{insights}</p></div>' if insights else ''}
        </div>
        """

        chart_sections.append(section_html)

    # Build complete HTML
    dashboard_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    total_charts = len(charts_data)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="dashboard-id" content="{dashboard_id}">
    <meta name="dashboard-title" content="{dashboard_title}">
    <meta name="created-at" content="{created_at}">
    <meta name="total-charts" content="{total_charts}">
    <meta name="generator" content="viz-mcp">
    <title>{dashboard_title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }}
        .dashboard-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 32px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .dashboard-header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .dashboard-header .meta {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .dashboard-description {{
            background: white;
            padding: 20px 32px;
            border-radius: 8px;
            margin-bottom: 24px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .dashboard-description p {{
            color: #4a5568;
            line-height: 1.6;
        }}
        .chart-section {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 24px;
            overflow: hidden;
        }}
        .chart-header {{
            background: #f8f9fa;
            padding: 20px 32px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .chart-header h2 {{
            font-size: 22px;
            font-weight: 600;
            color: #2d3748;
        }}
        .chart-badge {{
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .description {{
            background: #f8f9fa;
            padding: 16px 32px;
            border-left: 4px solid #667eea;
            margin: 20px 32px;
            border-radius: 4px;
        }}
        .description p {{
            color: #4a5568;
            line-height: 1.6;
            font-size: 14px;
        }}
        .chart-container {{
            padding: 20px 32px;
        }}
        .insights {{
            background: #e6fffa;
            border-left: 4px solid #38b2ac;
            padding: 16px 32px;
            margin: 0 32px 32px;
            border-radius: 4px;
        }}
        .insights h3 {{
            color: #234e52;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .insights p {{
            color: #2c5282;
            line-height: 1.6;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>{dashboard_title}</h1>
        <div class="meta">
            <span>{total_charts} charts</span> •
            <span>{created_at[:10]}</span>
        </div>
    </div>

    {f'<div class="dashboard-description"><p>{dashboard_description}</p></div>' if dashboard_description else ''}

    {''.join(chart_sections)}

</body>
</html>"""

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dashboard_{timestamp}.html"
    output_path = EXPORT_DIR / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

    return output_path


def extract_chart_metadata(html_path: Path) -> dict:
    """
    Extract metadata from HTML chart file.

    Returns dict with: chart_id, chart_type, title, created_at, data_points, file_path, file_size
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract meta tags using regex
        metadata = {
            'file_path': str(html_path),
            'file_name': html_path.name,
            'file_size_kb': round(html_path.stat().st_size / 1024, 2)
        }

        # Extract chart-id
        match = re.search(r'<meta name="chart-id" content="([^"]+)"', content)
        if match:
            metadata['chart_id'] = match.group(1)

        # Extract chart-type
        match = re.search(r'<meta name="chart-type" content="([^"]+)"', content)
        if match:
            metadata['chart_type'] = match.group(1)

        # Extract title
        match = re.search(r'<meta name="chart-title" content="([^"]*)"', content)
        if match:
            metadata['title'] = match.group(1)

        # Extract created-at
        match = re.search(r'<meta name="created-at" content="([^"]+)"', content)
        if match:
            metadata['created_at'] = match.group(1)

        # Extract data-points
        match = re.search(r'<meta name="data-points" content="([^"]+)"', content)
        if match:
            metadata['data_points'] = int(match.group(1))

        return metadata

    except Exception as e:
        return {
            'file_path': str(html_path),
            'file_name': html_path.name,
            'error': str(e)
        }


def list_all_charts() -> list[dict]:
    """List all HTML charts in exports directory with metadata."""
    charts = []

    for html_file in sorted(EXPORT_DIR.glob('*.html'), key=lambda p: p.stat().st_mtime, reverse=True):
        metadata = extract_chart_metadata(html_file)
        charts.append(metadata)

    return charts


def delete_chart_by_id(chart_id: str) -> bool:
    """
    Delete chart by chart ID.

    Returns True if deleted, False if not found.
    """
    for html_file in EXPORT_DIR.glob('*.html'):
        metadata = extract_chart_metadata(html_file)
        if metadata.get('chart_id') == chart_id:
            html_file.unlink()
            return True

    return False


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_scorecard_heatmap(start_date: str, end_date: str) -> Path:
    """Create calendar heatmap of daily scores."""
    events = query_events(entity_type="scorecard", start_date=start_date, end_date=end_date)

    if not events:
        raise ValueError("No scorecard data found for date range")

    # Extract scores
    dates = [e["date"] for e in events]
    scores = [e["data"].get("score", 0) for e in events]

    # Create DataFrame
    df = pd.DataFrame({"date": pd.to_datetime(dates), "score": scores})
    df["day_of_week"] = df["date"].dt.dayofweek
    df["week"] = df["date"].dt.isocalendar().week

    # Pivot for heatmap
    pivot = df.pivot(index="day_of_week", columns="week", values="score")

    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".0f",
        cmap="RdYlGn",
        vmin=0,
        vmax=115,
        cbar_kws={"label": "Score"},
        ax=ax
    )

    ax.set_title(f"Daily Scorecard Heatmap ({start_date} to {end_date})", fontsize=14)
    ax.set_xlabel("Week Number")
    ax.set_ylabel("Day of Week")
    ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return save_matplotlib_chart(fig, f"scorecard_heatmap_{timestamp}.png")


def create_fitness_trend(start_date: str, end_date: str) -> Path:
    """Create trend chart for workout strain and recovery."""
    workouts = query_events(entity_type="workout", start_date=start_date, end_date=end_date)

    if not workouts:
        raise ValueError("No workout data found for date range")

    # Extract data
    dates = [w["date"] for w in workouts]
    strains = [w["data"].get("strain", 0) for w in workouts]
    recoveries = [w["data"].get("recovery_pre", None) for w in workouts]

    # Create plotly figure
    fig = go.Figure()

    # Strain bars
    fig.add_trace(go.Bar(
        x=dates,
        y=strains,
        name="Strain",
        marker_color="lightblue"
    ))

    # Recovery line
    fig.add_trace(go.Scatter(
        x=dates,
        y=recoveries,
        name="Recovery %",
        yaxis="y2",
        mode="lines+markers",
        marker=dict(size=8),
        line=dict(color="green", width=2)
    ))

    # Layout
    fig.update_layout(
        title=f"Fitness Trend: Strain & Recovery ({start_date} to {end_date})",
        xaxis_title="Date",
        yaxis_title="Strain",
        yaxis2=dict(
            title="Recovery %",
            overlaying="y",
            side="right",
            range=[0, 100]
        ),
        hovermode="x unified",
        template="plotly_white"
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return save_plotly_chart(fig, f"fitness_trend_{timestamp}.html", format="html")


def create_weight_progress(start_date: str, end_date: str) -> Path:
    """Create weight progress chart with target line."""
    weights = query_events(entity_type="weight", start_date=start_date, end_date=end_date)

    if not weights:
        raise ValueError("No weight data found for date range")

    # Extract data
    dates = [pd.to_datetime(w["date"]) for w in weights]
    weight_values = [w["data"].get("weight_kg", 0) for w in weights]

    # Target line (start: 75kg, end: 67kg over 13 weeks)
    start_weight = 75.0
    target_weight = 67.0
    start_dt = pd.to_datetime("2026-01-04")
    end_dt = pd.to_datetime("2026-03-30")

    target_dates = pd.date_range(start_dt, end_dt, freq="D")
    target_values = np.linspace(start_weight, target_weight, len(target_dates))

    # Create plotly figure
    fig = go.Figure()

    # Actual weight
    fig.add_trace(go.Scatter(
        x=dates,
        y=weight_values,
        name="Actual Weight",
        mode="lines+markers",
        marker=dict(size=10, color="blue"),
        line=dict(width=3)
    ))

    # Target line
    fig.add_trace(go.Scatter(
        x=target_dates,
        y=target_values,
        name="Target (-0.5kg/week)",
        mode="lines",
        line=dict(color="red", width=2, dash="dash")
    ))

    # Layout
    fig.update_layout(
        title=f"Weight Loss Progress Q1 2026 ({start_date} to {end_date})",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        yaxis=dict(range=[66, 76]),
        hovermode="x unified",
        template="plotly_white"
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return save_plotly_chart(fig, f"weight_progress_{timestamp}.html", format="html")


def create_correlation_plot(
    entity_type: str,
    x_field: str,
    y_field: str,
    start_date: str,
    end_date: str
) -> Path:
    """Create scatter plot to show correlation between two metrics."""
    events = query_events(entity_type=entity_type, start_date=start_date, end_date=end_date)

    if not events:
        raise ValueError(f"No {entity_type} data found for date range")

    # Extract data using nested json_extract simulation
    x_values = []
    y_values = []
    dates = []

    for event in events:
        data = event["data"]

        # Support nested field access (e.g., "whoop.recovery")
        x_val = data
        for key in x_field.split("."):
            x_val = x_val.get(key) if isinstance(x_val, dict) else None

        y_val = data
        for key in y_field.split("."):
            y_val = y_val.get(key) if isinstance(y_val, dict) else None

        if x_val is not None and y_val is not None:
            x_values.append(x_val)
            y_values.append(y_val)
            dates.append(event["date"])

    if not x_values:
        raise ValueError(f"No data found for fields {x_field} and {y_field}")

    # Create scatter plot
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(x_values, y_values, alpha=0.6, s=100)

    # Add trend line
    z = np.polyfit(x_values, y_values, 1)
    p = np.poly1d(z)
    ax.plot(x_values, p(x_values), "r--", alpha=0.8, label=f"Trend: y={z[0]:.2f}x+{z[1]:.2f}")

    # Calculate correlation
    correlation = np.corrcoef(x_values, y_values)[0, 1]

    ax.set_title(f"Correlation: {x_field} vs {y_field} (r={correlation:.2f})")
    ax.set_xlabel(x_field)
    ax.set_ylabel(y_field)
    ax.legend()
    ax.grid(True, alpha=0.3)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return save_matplotlib_chart(fig, f"correlation_{entity_type}_{timestamp}.png")


# ============================================================================
# MCP SERVER
# ============================================================================

app = Server("viz-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available visualization tools."""
    return [
        Tool(
            name="visualize",
            description="Generic visualization tool with auto-detection. Accepts any data structure (dict, list, nested) and automatically selects optimal chart type (line, bar, pie, table, metric). Returns interactive HTML chart with insights.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": ["object", "array"],
                        "description": "Data to visualize (dict, list of dicts, or nested structure)",
                    },
                    "chart_type": {
                        "type": "string",
                        "description": "Chart type: 'auto' (default), 'line', 'bar', 'pie', 'table', 'metric'",
                        "enum": ["auto", "line", "bar", "pie", "table", "metric"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Chart title (auto-generated if omitted)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Chart description explaining what it shows (optional, AI can provide)",
                    },
                    "insights": {
                        "type": "string",
                        "description": "Data insights and observations (optional, auto-generated if omitted)",
                    },
                },
                "required": ["data"],
            },
        ),
        Tool(
            name="visualize_multi",
            description="Create multi-chart dashboard in single HTML. Accepts array of chart configs with different data/types. Perfect for comprehensive reports and dashboards.",
            inputSchema={
                "type": "object",
                "properties": {
                    "charts": {
                        "type": "array",
                        "description": "Array of chart configurations (max 6 charts per dashboard)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "data": {
                                    "type": ["object", "array"],
                                    "description": "Data to visualize",
                                },
                                "chart_type": {
                                    "type": "string",
                                    "description": "Chart type: 'auto', 'line', 'bar', 'pie', 'table', 'metric'",
                                    "enum": ["auto", "line", "bar", "pie", "table", "metric"],
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Chart title",
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Chart description (optional)",
                                },
                                "insights": {
                                    "type": "string",
                                    "description": "Chart insights (optional, auto-generated if omitted)",
                                },
                            },
                            "required": ["data"],
                        },
                    },
                    "dashboard_title": {
                        "type": "string",
                        "description": "Dashboard title (default: 'Multi-Chart Dashboard')",
                    },
                    "dashboard_description": {
                        "type": "string",
                        "description": "Dashboard description (optional)",
                    },
                },
                "required": ["charts"],
            },
        ),
        Tool(
            name="list_charts",
            description="List all generated charts with metadata (ID, type, title, created date, size)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="delete_chart",
            description="Delete a chart by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_id": {
                        "type": "string",
                        "description": "Chart ID (UUID) to delete",
                    },
                },
                "required": ["chart_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "visualize":
            # Extract arguments
            data = arguments["data"]
            chart_type_str = arguments.get("chart_type", "auto")
            title = arguments.get("title", "")
            description = arguments.get("description", "")
            insights = arguments.get("insights", "")

            # Auto-detect chart type if needed
            if chart_type_str == "auto":
                detected_type, confidence = auto_detect_chart_type(data)
                chart_type = detected_type
            else:
                # Manual chart type selection
                chart_type = ChartType(chart_type_str)
                confidence = 1.0

            # Generate chart
            fig = generate_chart(data, chart_type, title)

            # Count data points
            data_points = len(data) if isinstance(data, list) else 1

            # Auto-generate insights if not provided
            if not insights:
                insights = generate_insights(data, chart_type)

            # Generate metadata
            chart_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            metadata = {
                'chart_id': chart_id,
                'chart_type': chart_type.value,
                'title': title or f"{chart_type.value} chart",
                'data_points': data_points,
                'created_at': created_at,
                'description': description,
                'insights': insights
            }

            # Save as HTML with metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"viz_{chart_type.value}_{timestamp}.html"
            output_path = save_plotly_chart(fig, filename, format="html", metadata=metadata)

            # Build response message
            message = f"✅ Visualization generated: {output_path}\n"
            message += f"📊 Chart type: {chart_type.value}"
            if chart_type_str == "auto":
                message += f" (auto-detected, confidence: {confidence:.2f})"
            message += f"\n🆔 Chart ID: {chart_id}"
            if insights:
                message += f"\n💡 Insights: {insights}"
            message += f"\n🌐 Open in browser to view interactive chart"

            return [TextContent(
                type="text",
                text=message
            )]

        elif name == "visualize_multi":
            # Extract arguments
            charts_config = arguments["charts"]
            dashboard_title = arguments.get("dashboard_title", "Multi-Chart Dashboard")
            dashboard_description = arguments.get("dashboard_description", "")

            if len(charts_config) > 6:
                return [TextContent(
                    type="text",
                    text="❌ Maximum 6 charts per dashboard. Please reduce the number of charts."
                )]

            # Process each chart
            charts_data = []
            for i, chart_cfg in enumerate(charts_config, 1):
                data = chart_cfg["data"]
                chart_type_str = chart_cfg.get("chart_type", "auto")
                title = chart_cfg.get("title", f"Chart {i}")
                description = chart_cfg.get("description", "")
                insights = chart_cfg.get("insights", "")

                # Auto-detect chart type if needed
                if chart_type_str == "auto":
                    detected_type, confidence = auto_detect_chart_type(data)
                    chart_type = detected_type
                else:
                    chart_type = ChartType(chart_type_str)

                # Generate chart
                fig = generate_chart(data, chart_type, title)

                # Auto-generate insights if not provided
                if not insights:
                    insights = generate_insights(data, chart_type)

                # Count data points
                data_points = len(data) if isinstance(data, list) else 1

                charts_data.append({
                    'fig': fig,
                    'chart_type': chart_type.value,
                    'title': title,
                    'description': description,
                    'insights': insights,
                    'data_points': data_points
                })

            # Save dashboard
            output_path = save_multi_chart_dashboard(charts_data, dashboard_title, dashboard_description)

            # Build response message
            message = f"✅ Dashboard generated: {output_path}\n"
            message += f"📊 {len(charts_data)} charts included\n"
            message += f"📈 Chart types: {', '.join(c['chart_type'] for c in charts_data)}\n"
            message += f"🌐 Open in browser to view interactive dashboard"

            return [TextContent(
                type="text",
                text=message
            )]

        elif name == "list_charts":
            # List all charts with metadata
            charts = list_all_charts()

            if not charts:
                return [TextContent(
                    type="text",
                    text="📊 No charts found in exports directory."
                )]

            # Build response message
            message = f"📊 Found {len(charts)} chart(s):\n\n"
            for i, chart in enumerate(charts, 1):
                chart_id = chart.get('chart_id', 'N/A')
                chart_type = chart.get('chart_type', 'N/A')
                title = chart.get('title', 'Untitled')
                created_at = chart.get('created_at', 'N/A')
                size = chart.get('file_size_kb', 'N/A')

                message += f"{i}. {title}\n"
                message += f"   ID: {chart_id}\n"
                message += f"   Type: {chart_type}\n"
                message += f"   Created: {created_at}\n"
                message += f"   Size: {size} KB\n"
                message += f"   File: {chart.get('file_name', 'N/A')}\n\n"

            return [TextContent(
                type="text",
                text=message
            )]

        elif name == "delete_chart":
            # Delete chart by ID
            chart_id = arguments["chart_id"]
            success = delete_chart_by_id(chart_id)

            if success:
                return [TextContent(
                    type="text",
                    text=f"✅ Chart deleted: {chart_id}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Chart not found: {chart_id}"
                )]

        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error generating chart: {str(e)}"
        )]


# ============================================================================
# RESOURCES
# ============================================================================

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available dashboard resources."""
    return [
        Resource(
            uri="viz://dashboard/weekly",
            name="Weekly Dashboard",
            description="Weekly summary: scorecard, fitness, weight progress",
            mimeType="text/markdown",
        ),
        Resource(
            uri="viz://stats/summary",
            name="Visualization Stats",
            description="Stats on available data for visualization",
            mimeType="application/json",
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == "viz://dashboard/weekly":
        # Calculate current week range
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        start_str = week_start.strftime("%Y-%m-%d")
        end_str = week_end.strftime("%Y-%m-%d")

        # Query data
        scorecards = query_events("scorecard", start_str, end_str)
        workouts = query_events("workout", start_str, end_str)
        weights = query_events("weight", start_str, end_str)

        # Build markdown
        content = f"# Weekly Dashboard ({start_str} to {end_str})\n\n"
        content += f"## Scorecard Summary\n"
        content += f"- Total days tracked: {len(scorecards)}\n"
        if scorecards:
            avg_score = sum(s["data"].get("score", 0) for s in scorecards) / len(scorecards)
            content += f"- Average score: {avg_score:.1f}/115\n"
        content += f"\n## Fitness Summary\n"
        content += f"- Total workouts: {len(workouts)}\n"
        if workouts:
            total_strain = sum(w["data"].get("strain", 0) for w in workouts)
            content += f"- Total strain: {total_strain:.1f}\n"
        content += f"\n## Weight Tracking\n"
        content += f"- Measurements: {len(weights)}\n"
        if weights:
            latest = weights[-1]["data"].get("weight_kg")
            content += f"- Latest: {latest}kg\n"

        return content

    elif uri == "viz://stats/summary":
        # Count available data by entity_type
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT entity_type, COUNT(*) as count FROM tracking_events GROUP BY entity_type")
        stats = {row["entity_type"]: row["count"] for row in cursor.fetchall()}
        conn.close()

        return json.dumps({
            "total_events": sum(stats.values()),
            "by_entity_type": stats,
            "export_dir": str(EXPORT_DIR),
            "database_path": str(TRACKING_DB),
        }, indent=2)

    else:
        raise ValueError(f"Unknown resource URI: {uri}")


# ============================================================================
# MAIN
# ============================================================================

async def async_main():
    """Run MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Entry point for the MCP server."""
    import anyio
    anyio.run(async_main)


if __name__ == "__main__":
    main()
