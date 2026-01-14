# viz-mcp

**Data Visualization MCP Server for tracking-mcp**

Generate interactive charts, heatmaps, and dashboards from tracking data.

## Features

### Tools

**1. generate_scorecard_heatmap**
- Calendar heatmap of daily scorecard scores
- Output: PNG image (matplotlib + seaborn)
- Highlights patterns: weekdays vs weekends, high/low score days

**2. generate_fitness_trend**
- Interactive chart: workout strain + recovery %
- Output: HTML (plotly interactive)
- Dual-axis: strain (bars) + recovery (line)

**3. generate_weight_progress**
- Weight loss progress vs target line
- Output: HTML (plotly interactive)
- Shows: actual weight, target trajectory (-0.5kg/week)

**4. generate_correlation_plot**
- Scatter plot + trend line for any two metrics
- Output: PNG (matplotlib)
- Examples: recovery vs strain, sleep vs score, HRV vs performance

### Resources

**viz://dashboard/weekly**
- Weekly summary dashboard (markdown)
- Auto-calculates current week
- Summary: scorecard avg, total workouts, weight measurements

**viz://stats/summary**
- Visualization stats (JSON)
- Total events by entity_type
- Export directory, database path

## Installation

```bash
cd ~/Desktop/Projects/04-Personal-Tools/viz-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Configuration

Add to `work-hub/.mcp.json`:

```json
{
  "viz-mcp": {
    "type": "stdio",
    "command": "/path/to/viz-mcp/.venv/bin/python3",
    "args": ["/path/to/viz-mcp/mcp_server/viz_server.py"],
    "env": {
      "TRACKING_DB_PATH": "/path/to/tracking-mcp/data/tracking.db",
      "EXPORT_DIR": "/path/to/viz-mcp/exports"
    }
  }
}
```

Add permissions to `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__viz-mcp__*"
    ]
  }
}
```

## Usage Examples

### Generate Scorecard Heatmap

```python
mcp__viz-mcp__generate_scorecard_heatmap(
  start_date="2026-01-01",
  end_date="2026-01-14"
)
# Output: exports/scorecard_heatmap_YYYYMMDD_HHMMSS.png
```

### Generate Fitness Trend

```python
mcp__viz-mcp__generate_fitness_trend(
  start_date="2026-01-01",
  end_date="2026-01-14"
)
# Output: exports/fitness_trend_YYYYMMDD_HHMMSS.html
# Open in browser for interactive chart
```

### Generate Weight Progress

```python
mcp__viz-mcp__generate_weight_progress(
  start_date="2026-01-04",
  end_date="2026-01-14"
)
# Output: exports/weight_progress_YYYYMMDD_HHMMSS.html
```

### Generate Correlation Plot

```python
# Recovery vs Strain
mcp__viz-mcp__generate_correlation_plot(
  entity_type="workout",
  x_field="recovery_pre",
  y_field="strain",
  start_date="2026-01-01",
  end_date="2026-01-14"
)

# Sleep vs Score (nested field access)
mcp__viz-mcp__generate_correlation_plot(
  entity_type="scorecard",
  x_field="whoop.hrv",
  y_field="score",
  start_date="2026-01-01",
  end_date="2026-01-14"
)
# Output: exports/correlation_ENTITY_YYYYMMDD_HHMMSS.png
```

### Read Weekly Dashboard

```python
mcp__viz-mcp__read_resource(uri="viz://dashboard/weekly")
# Returns: Markdown summary of current week
```

## Architecture

```
viz-mcp/
├── mcp_server/
│   ├── __init__.py
│   └── viz_server.py          # MCP server + visualization functions
├── exports/                    # Generated charts (PNG/HTML)
├── tests/
│   └── test_basic.py
├── pyproject.toml
└── README.md

Connects to:
  tracking-mcp/data/tracking.db  (SQLite database)
```

## Chart Types

### 1. Heatmap (matplotlib + seaborn)
- **Use case**: Patterns over time (weekly/monthly view)
- **Best for**: Scorecard scores, habit tracking
- **Format**: Static PNG
- **Size**: ~150 DPI, optimized for viewing

### 2. Interactive Line/Bar (plotly)
- **Use case**: Trends, dual-metric comparison
- **Best for**: Fitness metrics, weight progress
- **Format**: HTML (self-contained, no internet required)
- **Interactive**: Zoom, pan, hover tooltips

### 3. Scatter + Regression (matplotlib)
- **Use case**: Correlation analysis
- **Best for**: Finding relationships between metrics
- **Format**: Static PNG
- **Features**: Trend line, correlation coefficient

## Data Access

viz-mcp connects to tracking-mcp database in **read-only** mode:
- No writes to database
- Safe to run in parallel with tracking-mcp
- Exports stored in viz-mcp/exports/ directory

## Nested Field Access

Supports dot notation for nested JSON fields:

```python
# Access nested whoop.recovery
x_field="whoop.recovery"

# Access nested diet.protein_g
y_field="diet.protein_g"
```

## Dependencies

- **mcp**: MCP SDK
- **matplotlib**: Static charts (PNG)
- **plotly**: Interactive charts (HTML)
- **pandas**: Data manipulation
- **seaborn**: Enhanced heatmaps
- **kaleido**: Plotly PNG export (optional)

## Roadmap

**Phase 2: Advanced Charts** (planned)
- Multi-metric dashboard (single HTML with tabs)
- Moving average + trend analysis
- Week-over-week comparison
- Streak visualization

**Phase 3: Pre-built Templates** (planned)
- Monthly report (PDF export)
- Q1 progress dashboard
- Correlation matrix (all metrics)

## Troubleshooting

### Charts not generating

1. Check tracking-mcp database path:
   ```bash
   ls -la ~/Desktop/Projects/04-Personal-Tools/tracking-mcp/data/tracking.db
   ```

2. Verify data exists for date range:
   ```python
   mcp__tracking-mcp__query_events(
     entity_type="scorecard",
     start_date="2026-01-01"
   )
   ```

### Interactive charts won't open

HTML files are self-contained. Open manually:
```bash
open ~/Desktop/Projects/04-Personal-Tools/viz-mcp/exports/fitness_trend_*.html
```

### Permission errors

Ensure viz-mcp permissions in `.claude/settings.local.json`:
```json
"mcp__viz-mcp__*"
```

Restart Claude Code session after adding permissions.

## Current Status (2026-01-14)

**Phase 1: Core Setup** ✅
- [x] Directory structure
- [x] Python venv + dependencies
- [x] MCP server skeleton
- [x] 4 chart tools implemented
- [x] 2 resources (dashboard, stats)
- [x] work-hub integration

**Next**: Phase 2 - Advanced Charts

**Total effort**: ~4h

## Examples Output

See `exports/` directory for generated charts:
- `scorecard_heatmap_*.png` - Calendar view of scores
- `fitness_trend_*.html` - Interactive strain/recovery
- `weight_progress_*.html` - Weight loss trajectory
- `correlation_*.png` - Scatter plots with trend lines
