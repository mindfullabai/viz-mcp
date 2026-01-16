# viz-mcp

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)

**Data visualization MCP server with auto-chart generation and multi-chart dashboards.**

Automatically generate interactive charts, heatmaps, and comprehensive dashboards from any data structure. Auto-detects optimal chart type, generates insights, and outputs self-contained HTML or PNG files.

## Features

- **Auto-Detection**: Automatically selects optimal chart type from data structure
- **Multiple Chart Types**: Line, bar, pie, table, metric displays
- **Interactive Visualizations**: Self-contained HTML with Plotly (no internet required)
- **Static Charts**: High-quality PNG exports with Matplotlib
- **Multi-Chart Dashboards**: Combine multiple charts in single HTML file
- **AI-Generated Insights**: Automatic data analysis and observations
- **Chart Management**: List and delete generated charts
- **Flexible Input**: Accepts dict, list, nested structures
- **Zero Configuration**: Works out of the box with sensible defaults

## Installation

### From PyPI (when published)

```bash
pip install viz-mcp
```

### From Source

```bash
git clone https://github.com/mariomosca/viz-mcp.git
cd viz-mcp
pip install -e .
```

## Quick Start

### Claude Desktop Configuration

Add to your Claude Desktop MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "viz": {
      "command": "viz-mcp",
      "env": {
        "EXPORT_DIR": "/path/to/export/directory"
      }
    }
  }
}
```

### Basic Usage

From Claude Desktop:

```
Visualize this data: {"Jan": 100, "Feb": 150, "Mar": 200}
```

```
Create a dashboard with my sales and revenue data
```

```
Show me a list of all generated charts
```

## MCP Server Specification

### Tools (4)

#### 1. `visualize`
Generic visualization tool with auto-detection.

**Parameters**:
- `data` (object|array, required): Data to visualize (dict, list of dicts, or nested structure)
- `chart_type` (string, optional): Chart type - 'auto' (default), 'line', 'bar', 'pie', 'table', 'metric'
- `title` (string, optional): Chart title (auto-generated if omitted)
- `description` (string, optional): Chart description
- `insights` (string, optional): Data insights (auto-generated if omitted)

**Returns**: Interactive HTML chart with auto-generated insights

**Examples**:
```python
# Auto-detect chart type
visualize(
    data={"Q1": 10000, "Q2": 15000, "Q3": 12000, "Q4": 18000}
)

# Force specific chart type
visualize(
    data=[{"month": "Jan", "sales": 100}, {"month": "Feb", "sales": 150}],
    chart_type="line",
    title="Monthly Sales Trend"
)

# Metric display
visualize(
    data={"total_revenue": 50000, "growth": "+15%"},
    chart_type="metric"
)
```

#### 2. `visualize_multi`
Create multi-chart dashboard in single HTML.

**Parameters**:
- `charts` (array, required): Array of chart configurations (max 6 charts)
  - Each chart has: `data`, `chart_type` (optional), `title` (optional), `description` (optional), `insights` (optional)
- `dashboard_title` (string, optional): Dashboard title (default: "Multi-Chart Dashboard")
- `dashboard_description` (string, optional): Dashboard description

**Returns**: Self-contained HTML dashboard with multiple charts

**Example**:
```python
visualize_multi(
    charts=[
        {
            "data": {"Q1": 10000, "Q2": 15000, "Q3": 12000, "Q4": 18000},
            "title": "Quarterly Revenue"
        },
        {
            "data": [{"month": "Jan", "users": 500}, {"month": "Feb", "users": 650}],
            "chart_type": "line",
            "title": "User Growth"
        },
        {
            "data": {"Active": 1200, "Inactive": 300},
            "chart_type": "pie",
            "title": "User Status"
        }
    ],
    dashboard_title="Q4 2025 Business Metrics"
)
```

#### 3. `list_charts`
List all generated charts with metadata.

**Parameters**: None

**Returns**: JSON array of charts with:
- `chart_id`: Unique identifier
- `chart_type`: Type of chart
- `title`: Chart title
- `created_at`: Creation timestamp
- `file_size`: File size in bytes
- `file_path`: Path to chart file

#### 4. `delete_chart`
Delete a chart by its ID.

**Parameters**:
- `chart_id` (string, required): Chart ID to delete (from list_charts)

**Returns**: Success/failure message

## Chart Type Auto-Detection

viz-mcp automatically selects the optimal chart type based on your data structure:

| Data Structure | Auto-Selected Chart | Use Case |
|----------------|---------------------|----------|
| `{"A": 10, "B": 20}` | Bar chart | Compare categories |
| `[{"x": 1, "y": 10}, {"x": 2, "y": 20}]` | Line chart | Show trends over time |
| `{"Category A": 30, "Category B": 70}` | Pie chart | Show proportions (if 2-5 items) |
| `[{"name": "Alice", "score": 95}, ...]` | Table | Detailed data display |
| `{"metric": 1500, "change": "+10%"}` | Metric | Single value display |

You can always override auto-detection by specifying `chart_type`.

## Output Formats

### Interactive HTML (Default)
- **Self-contained**: No internet connection required
- **Interactive**: Zoom, pan, hover tooltips
- **Responsive**: Adapts to screen size
- **Shareable**: Send as single file
- **Technology**: Plotly.js

### Static PNG
- **High Quality**: 150 DPI, publication-ready
- **Technology**: Matplotlib
- **File Size**: Typically 50-200 KB
- **Use Case**: Reports, presentations

## Advanced Usage

### Dashboard with Mixed Chart Types

```python
visualize_multi(
    charts=[
        {
            "data": {"Revenue": 50000, "Costs": 35000, "Profit": 15000},
            "chart_type": "bar",
            "title": "Financial Overview"
        },
        {
            "data": [
                {"date": "2026-01-01", "users": 1000},
                {"date": "2026-01-08", "users": 1200},
                {"date": "2026-01-15", "users": 1350}
            ],
            "chart_type": "line",
            "title": "Weekly User Growth"
        },
        {
            "data": {"Plan A": 450, "Plan B": 320, "Plan C": 230},
            "chart_type": "pie",
            "title": "Subscription Distribution"
        }
    ],
    dashboard_title="Weekly Business Dashboard",
    dashboard_description": "Key metrics for Week 2, Jan 2026"
)
```

### Custom Insights

```python
visualize(
    data={"Q1": 10000, "Q2": 15000, "Q3": 12000, "Q4": 18000},
    title="Quarterly Revenue 2025",
    description="Revenue performance by quarter",
    insights="Q2 showed strongest growth (+50%). Q3 dip attributed to seasonal factors. Q4 recovery exceeded projections."
)
```

### Integration with tracking-mcp

```python
# Query data from tracking-mcp
events = query_events(
    entity_type="weight",
    start_date="2026-01-01",
    end_date="2026-01-15"
)

# Transform and visualize
weight_data = [
    {"date": e["date"], "weight": e["data"]["weight_kg"]}
    for e in events
]

visualize(
    data=weight_data,
    chart_type="line",
    title="Weight Progress - January 2026"
)
```

## Project Structure

```
viz-mcp/
├── viz_mcp/
│   ├── viz_server.py          # MCP server implementation
│   ├── auto_detect.py          # Auto-detection logic
│   ├── chart_generator.py     # Chart generation
│   ├── insights_generator.py  # AI insights
│   └── __init__.py
├── exports/                    # Generated charts (HTML/PNG)
├── tests/
│   └── test_basic.py
├── pyproject.toml
├── LICENSE
├── CHANGELOG.md
└── README.md
```

## Dependencies

- **mcp** (>=1.7.1): MCP SDK
- **matplotlib** (>=3.8.0): Static charts
- **plotly** (>=5.18.0): Interactive visualizations
- **pandas** (>=2.1.0): Data manipulation
- **numpy** (>=1.26.0): Numerical operations
- **seaborn** (>=0.13.0): Enhanced styling
- **kaleido** (>=0.2.1): Static image export

## Architecture

### Auto-Detection Algorithm

1. **Analyze data structure**: dict, list, nested
2. **Count data points**: Single value vs multiple
3. **Detect patterns**: Time series, categories, proportions
4. **Select chart type**: Line, bar, pie, table, metric
5. **Generate chart**: Plotly (HTML) or Matplotlib (PNG)
6. **Add insights**: AI-generated observations

### Chart Generation Pipeline

```
Input Data → Auto-Detect → Generate Chart → Add Insights → Export (HTML/PNG)
```

### Insights Generation

- **Automatic Analysis**: Trends, outliers, patterns
- **Statistical Metrics**: Mean, median, min, max, variance
- **Observations**: Growth rates, comparisons, highlights
- **Natural Language**: Human-readable insights

## Chart Management

### List All Charts

```python
list_charts()
```

**Returns**:
```json
[
  {
    "chart_id": "abc123...",
    "chart_type": "line",
    "title": "Monthly Revenue",
    "created_at": "2026-01-16T10:30:00",
    "file_size": 125000,
    "file_path": "/path/to/exports/chart_abc123.html"
  }
]
```

### Delete Chart

```python
delete_chart(chart_id="abc123...")
```

## Development

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black viz_mcp/

# Lint
ruff check viz_mcp/
```

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version history.

**Current version**: 1.0.0 (Initial public release)

## Related Projects

- **[tracking-mcp](https://github.com/mariomosca/tracking-mcp)**: Companion MCP server for entity tracking (provides data source for visualizations)

## Use Cases

### Personal Productivity
- Daily scorecard heatmaps
- Habit tracking visualizations
- Weight loss progress charts
- Fitness metrics dashboards

### Business Analytics
- Sales trend analysis
- Revenue vs costs comparison
- User growth tracking
- Subscription distribution

### Data Science
- Exploratory data analysis
- Quick data visualization
- Dashboard prototyping
- Report generation

## Troubleshooting

### Charts not generating

Check export directory exists and is writable:
```bash
ls -la ~/path/to/exports/
```

### "No data to visualize" error

Ensure data is not empty:
```python
# Bad
data = {}

# Good
data = {"A": 10, "B": 20}
```

### Interactive charts won't open

HTML files are self-contained. Open manually:
```bash
open ~/path/to/exports/chart_*.html
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

**Mario Mosca** - [GitHub](https://github.com/mariomosca)

## Contributing

Contributions welcome! Please open an issue or pull request.

## Support

For issues, questions, or feature requests, please open an issue on GitHub:
https://github.com/mariomosca/viz-mcp/issues
