# Health Check Dashboard

A Python-based health check dashboard that monitors the status of API endpoints and displays the results in an interactive web interface.

## Features

- Real-time monitoring of multiple API endpoints
- Visual indicators for service status (UP/DOWN)
- Response time tracking
- Historical status visualization
- Interactive dashboard with auto-refresh capability
- Easy URL management (add/remove endpoints)
- Automatic metric updates when URLs are added/removed
- Proper handling of unchecked URLs in metrics
- Persistent storage of URLs and check history (survives server restarts)
- URL validation with warnings for missing http/https schema
- Automatic clearing of URL input field after successful addition
- Auto-refresh checks also save history to file
- Manual and auto-refresh checks both update persistent history

## Requirements

- Python 3.7+
- Streamlit
- Requests
- Pandas
- Plotly

## Installation

1. Clone or download this repository
2. Install the required packages:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install streamlit requests pandas plotly
```

## Usage

### Running the Dashboard

```bash
streamlit run health_check_dashboard.py
```

### Configuration

The dashboard allows you to:

1. **Add URLs**: Enter new API endpoints in the sidebar
2. **Remove URLs**: Click the ❌ button next to any URL to remove it
3. **Manual Check**: Click "🔄 Check Now" to manually trigger a health check
4. **Auto Refresh**: Enable the checkbox in the sidebar to automatically refresh at specified intervals

### Dashboard Interface

The main dashboard displays:

- **Summary Metrics**: Total services, UP services, DOWN services
- **Status Table**: Detailed view of each endpoint's status, response time, and status code
- **Visualizations**:
  - Pie chart showing status distribution
  - Bar chart showing response times for UP services
  - Line chart showing historical status trends

## How It Works

The application performs GET requests to each configured URL and determines the status based on:

- **UP**: HTTP status code 200-299
- **DOWN**: HTTP status code 300+, connection errors, timeouts, or exceptions

Each check records:
- Status (UP/DOWN)
- Response time in milliseconds
- HTTP status code
- Timestamp of the check
- Error message (if any)

## Testing

Run the unit tests to verify all functionality:

```bash
python -m pytest test_health_check_dashboard.py -v
```

## Customization

You can customize the application by:

- Modifying the default URLs in the `__init__` method
- Adjusting the timeout value in the `check_url_health` method
- Changing the history retention limit (currently 100 entries per URL)
- Modifying the status determination logic

## Persistence

The application automatically saves data to JSON files:
- `urls.json`: Stores the list of URLs being monitored
- `history.json`: Stores the check history for visualization
- Both files are automatically created and updated during runtime
- Data persists across server restarts

## Architecture

- `HealthCheckDashboard` class: Main application logic
- Health checking: Performed using the `requests` library
- Visualization: Created using `Plotly` and displayed in `Streamlit`
- State management: Uses Streamlit's session state for temporary storage
- Persistence: Saves URLs to `urls.json` and history to `history.json` files

## License

Apache-2.0

## Contributing

Please create a pull request if you want to add features or fix bugs.