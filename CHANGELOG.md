# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-16

### Added
- Initial public release
- Companion MCP server for tracking-mcp data visualization
- Auto-chart generation with multiple output formats (PNG, HTML)
- MCP Tools for visualization:
  - `visualize`: Generic auto-detection tool (accepts any data structure)
  - `visualize_multi`: Multi-chart dashboard generator
  - `list_charts`: List all generated charts
  - `delete_chart`: Delete chart by ID
- Auto-chart type detection based on data structure
- Support for line charts, bar charts, pie charts, tables, metrics
- Interactive HTML output with Plotly
- Static PNG output with Matplotlib
- Multi-chart dashboards in single HTML file
- AI-generated insights for each chart
- Chart metadata storage and retrieval

### Technical Stack
- Python 3.10+
- MCP SDK (mcp >= 1.7.1)
- Matplotlib for static charts
- Plotly for interactive visualizations
- Pandas for data manipulation
- NumPy for numerical operations
- Seaborn for enhanced styling
- Kaleido for static image export from Plotly

### Features
- **Auto-Detection**: Automatically selects optimal chart type from data structure
- **Multiple Formats**: PNG (static) and HTML (interactive) outputs
- **Dashboard Support**: Combine multiple charts in single HTML
- **Insights Generation**: AI-generated data insights for each visualization
- **Chart Management**: List and delete generated charts
- **Flexible Input**: Accepts dict, list, nested structures
- **Extensible**: Easy to add new chart types

[1.0.0]: https://github.com/mariomosca/viz-mcp/releases/tag/v1.0.0
