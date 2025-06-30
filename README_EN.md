# Garmin Connect MCP Server

A Model Context Protocol (MCP) server that provides comprehensive running data and training analytics from Garmin Connect, designed to help create evidence-based running training plans.

## 🚀 Quick Start

### One-Click Installation (Recommended)

```bash
git clone https://github.com/leewnsdud/garmin-connect-mcp.git
cd garmin-connect-mcp
uv run python install.py
```

This command will automatically:
- Install all dependencies
- Set up Garmin authentication
- Run verification tests

### Prerequisites

- **Garmin Connect account** with running data
- **[uv](https://docs.astral.sh/uv/)** package manager installed

## 📋 Features

### Core Running Data
- **Personal Records**: Track your PRs for 5K, 10K, half marathon, and full marathon
- **Activity Metrics**: Access distance, pace, heart rate, altitude, and cadence data
- **Health Insights**: Monitor resting heart rate, stress levels, sleep quality, and body battery
- **VO2 Max & Training Status**: Get your current fitness level, trends, and training readiness

### Advanced Training Analysis
- **Jack Daniels Training Paces**: Calculate optimal training zones based on your race performances
- **Running Form Metrics**: Analyze stride length, vertical ratio, ground contact time, and more (device-dependent)
- **Heart Rate Zone Analysis**: Get actual time spent in each zone with percentage breakdowns
- **Training Load Monitoring**: Track weekly mileage, intensity distribution, and injury risk

### Goal Setting & Progress
- **Race Goal Planning**: Set target times and track progress toward race objectives
- **Performance Trends**: Analyze 6-month to 1-year running performance evolution
- **Training Recommendations**: Get phase-appropriate guidance based on your race timeline

## 🛠️ Manual Installation

If you prefer to set up manually or the automatic installation fails:

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/leewnsdud/garmin-connect-mcp.git
cd garmin-connect-mcp
uv sync
```

### 2. Configure Environment

```bash
cp .env.template .env
```

Edit `.env` with your Garmin Connect credentials:
```env
GARMIN_USERNAME=YOUR_EMAIL@EXAMPLE.COM
GARMIN_PASSWORD=your_password
```

### 3. Set Up Authentication

```bash
uv run python setup_garmin_auth.py
```

This will:
- Authenticate with your Garmin Connect account
- Handle Multi-Factor Authentication if enabled
- Generate and store authentication tokens
- Test API access


## 💬 Usage Examples

Try these prompts with the MCP server:

```
"Analyze my recent running performance and suggest training paces for my upcoming 10K race"
```

```
"What's my current VO2 Max and how has it changed over the past 6 months?"
```

```
"Create a 16-week marathon training plan based on my current fitness level"
```

```
"Analyze my training load for the past 4 weeks and assess injury risk"
```

## 📚 Available Tools

| Tool | Description | Example Use |
|------|-------------|-------------|
| `get_personal_records` | Retrieve PRs, VO2 Max, and training status | "What are my personal best times?" |
| `get_recent_running_activities` | List recent runs with details | "Show my last 10 runs" |
| `get_activity_details` | Get comprehensive metrics including heart rate zones | "Analyze my long run from Saturday" |
| `get_advanced_running_metrics` | Access running form data | "How's my running form efficiency?" |
| `analyze_heart_rate_zones` | Analyze HR zone distribution | "Was my tempo run at the right intensity?" |
| `calculate_training_paces` | Generate Jack Daniels training paces | "Calculate my training zones from my 5K PR" |
| `set_race_goal` | Set and track race objectives | "Set a goal for sub-3:30 marathon" |
| `analyze_training_load` | Assess training volume and intensity | "Am I training too hard?" |
| `get_running_trends` | Long-term performance analysis | "How has my running improved this year?" |
| `get_health_metrics` | Daily health data including sleep and body battery | "What's my recovery status today?" |

## 🔧 Troubleshooting

### Authentication Issues

```bash
# Check authentication status
uv run python setup_garmin_auth.py check

# Reset authentication
uv run python setup_garmin_auth.py reset
```

### Connection Problems

```bash
# Test direct connection
uv run python -c "
import asyncio
from main import GarminConnectMCP

async def test():
    server = GarminConnectMCP()
    await server._authenticate()
    print('✅ Connection successful!')

asyncio.run(test())
"
```

### Common Issues

1. **"No activities found"**: Ensure your Garmin device is syncing properly
2. **"Authentication failed"**: Check credentials and 2FA settings
3. **"Missing metrics"**: Some advanced metrics require compatible Garmin devices
4. **"Rate limited"**: Wait a few minutes between requests

## 🏃‍♂️ Training Philosophy

This MCP server supports evidence-based training methodologies:

- **Jack Daniels' Running Formula**: VDOT-based training intensity zones
- **Periodization**: Structured training phases with appropriate load progression
- **Recovery-Focused**: Monitors stress and adaptation to prevent overtraining
- **Data-Driven**: All recommendations based on your actual performance data

## 🔒 Security & Privacy

- Credentials stored securely in environment variables
- OAuth tokens managed automatically by the garminconnect library
- No sensitive data is logged or cached
- All data stays local on your machine

## 📋 Requirements

- Python 3.13+
- Valid Garmin Connect account
- Garmin device with running activity data
- uv package manager

## 🤝 Contributing

Contributions are welcome! Please ensure new features support evidence-based training methodologies.

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Resources

- [Garmin Connect](https://connect.garmin.com)
- [Jack Daniels' VDOT Calculator](https://runsmartproject.com/calculator/)
- [MCP Documentation](https://modelcontextprotocol.io)