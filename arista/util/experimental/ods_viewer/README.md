# ODS Viewer Tool

Web-based visualization tool for ODS (Operational Data Store) time-series data. Upload multiple CSV files and visualize sensor data with interactive charts.

## Quick Start

1. Open `index.html` in a web browser
2. Click "Add CSV File" to upload ODS CSV data
3. Select sensors and click "Add Sensor" to plot
4. Use chart controls to zoom and navigate

## Visualization Modes

- **Multi-axis** (default): Clean dual Y-axis display with actual values
- **Normalize (0-1)**: Scale all sensors to 0-1 range for comparison
- **Zoom**: Focus on actual data range with padding
- **Noresize**: Show full scale from zero to maximum

## Data Format

CSV format (no headers):
```
sensor_name::sensor_id, value, timestamp, other_id
```

Example:
```csv
host123::qsfp_service.qsfp.interface.fab1/1/1.temp,56,"Thu, 08 May 25 00:00:00 -0700",1746687600
host123::sensor_service.sensor_read.FAN1_RPM.value,5600,"Thu, 08 May 25 00:00:00 -0700",1746687600
```

## Development

```bash
make test    # Run tests
make deploy  # Deploy to web server
```

## Features

- Multi-file CSV upload
- Interactive Plotly.js charts
- Web worker processing for large files
- Sensor search and filtering
- Time range selection
- Responsive design
