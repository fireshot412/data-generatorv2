# Asana Continuous Data Generator

A powerful tool for generating realistic Asana project data with two modes:
1. **Point-in-Time Mode**: Creates projects, tasks, and comments instantly (existing functionality)
2. **Continuous Mode** (NEW): Generates realistic data over time, simulating actual team activity

## Features

### Continuous Mode Highlights
- **Realistic Activity Patterns**: Simulates team work hours, burst times (9am, post-lunch), and natural work rhythms
- **Industry-Specific Content**: Uses Claude AI to generate contextually relevant content for 10+ industries
- **Task Lifecycle Simulation**: Tasks progress through realistic states (new → in progress → blocked → completed)
- **Multi-User Simulation**: Distributes activities across multiple team members
- **Smart Rate Limiting**: Gracefully handles API limits with realistic OOO messages
- **Persistent State**: Resumes where it left off if stopped
- **Real-Time Dashboard**: Monitor active jobs, view logs, track API usage

### Supported Industries
- Finance/Banking
- Healthcare/Life Sciences
- Manufacturing/Industrial
- Travel/Hospitality
- Technology/Software
- Retail/E-commerce
- Education
- Government/Public Sector
- Energy/Utilities
- Media/Entertainment

## Installation

### Prerequisites
- Python 3.8+
- Asana account with API access
- Anthropic API key (for Claude AI)
- Multiple Asana API tokens (optional but recommended for multi-user simulation)

### Setup

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (optional but recommended):

Create a `.env` file:
```bash
# Anthropic API key for Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Asana API tokens for different users
ASANA_TOKEN_USER1=your_asana_token_1
ASANA_TOKEN_USER2=your_asana_token_2
ASANA_TOKEN_USER3=your_asana_token_3
```

**How to get API keys**:
- **Asana API Token**: Go to https://app.asana.com/0/my-apps → Create Personal Access Token
- **Anthropic API Key**: Sign up at https://console.anthropic.com/ and create an API key

## Usage

### Quick Start

1. **Start the API server**:
```bash
python api_server.py
```

2. **Open browser**:
Navigate to http://localhost:5000

3. **Configure and launch** (via the web UI):
   - **Select Industry**: Choose from 10 industry themes (Finance, Healthcare, Tech, etc.)
   - **Add API Keys**:
     - Anthropic API key for Claude AI
     - Asana workspace GID
     - Multiple user API tokens (click "+ Add Another User" for each)
   - **Configure Duration**: Fixed (X days) or Indefinite
   - **Set Activity Patterns**:
     - Activity level (Low/Medium/High)
     - Working hours (US Workforce or Global)
     - Burst vs Steady slider
   - **Advanced Settings**: Completion rates, blocked tasks, comment frequency
   - **Click "Start Continuous Generation 🚀"**

### Continuous Mode Configuration

**Duration**:
- Fixed: Runs for X days then stops
- Indefinite: Runs until manually stopped

**Activity Level**:
- **Low**: Sparse activity (30% of medium)
- **Medium**: Balanced, realistic activity
- **High**: Very active team (200% of medium)

**Working Hours**:
- **US Workforce**: 9am-6pm PT, Monday-Friday with burst patterns
- **Global**: 24-hour coverage with regional peaks

**Activity Pattern** (Burst vs Steady slider):
- **Bursty** (left): Concentrated activity at specific times (9am, 1pm, 4pm)
- **Steady** (right): Even distribution throughout day
- **Middle**: Mix of both

**Task Completion Rate**:
Percentage of tasks that get completed per week (e.g., 20% = 1 in 5 tasks completed weekly)

**Blocked Tasks**:
- **Frequency**: % of tasks that become blocked (e.g., 15% = roughly 1 in 7 tasks)
- **Duration**: Average days tasks stay blocked before unblocking

**Comment Frequency**:
Average comments per task per day (e.g., 0.5 = 1 comment every 2 days per task)

**New Project Frequency**:
Days between creating new projects (as old ones complete)

### Monitoring Jobs

The dashboard shows:
- **Status**: Running, Paused, Stopped, Error
- **Uptime**: How long the job has been running
- **Today's Activity**: Comments, task updates, completions
- **Stats**: Total projects, tasks, comments generated
- **API Usage**: Asana calls, LLM calls, tokens used
- **Errors/Warnings**: Invalid tokens, rate limits, etc.

### Managing Jobs

**View Activity Log**:
Click "View Log" to see:
- All activities generated (comments, task updates, etc.)
- Timestamps
- Which user performed each action
- Filter and search capabilities

**Pause/Resume**:
- Pause temporarily stops generation (can resume later)
- Useful if you need to slow down API usage

**Stop**:
- Permanently stops the job
- State is preserved - can view history
- Can be deleted later

**Delete**:
- Stops job and removes all state
- Cannot be undone

## Architecture

### Components

```
/
├── continuous/
│   ├── llm_generator.py       # Claude AI integration for content generation
│   ├── state_manager.py       # Persistent state storage (JSON files)
│   ├── scheduler.py           # Activity scheduling & work patterns
│   ├── asana_client.py        # Asana API wrapper with error handling
│   └── service.py             # Main continuous service orchestrator
├── api_server.py              # Flask REST API for UI communication
├── asana_project_creator.html # Web UI (point-in-time + continuous modes)
├── create_asana_project.py    # Original CLI tool (point-in-time)
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Data Flow

1. **User configures job** via HTML UI
2. **API server** creates ContinuousService instance
3. **Service** runs in background thread:
   - **Scheduler** determines when activity should occur
   - **LLM Generator** creates realistic content
   - **Asana Client** makes API calls
   - **State Manager** persists everything to JSON
4. **UI polls API** for updates and displays dashboard
5. **Activity Log** records every action for auditing

### State Persistence

State files are stored as `job_{id}.json` in the project directory:

```json
{
  "job_id": "abc123",
  "status": "running",
  "started_at": "2024-10-15T09:00:00Z",
  "config": { /* job configuration */ },
  "projects": [ /* all created projects and tasks */ ],
  "activity_log": [ /* chronological activity history */ ],
  "stats": { /* counters */ },
  "api_usage": { /* API call tracking */ },
  "errors": [ /* error log */ ]
}
```

## Error Handling

### Rate Limiting
When Asana API rate limits are hit:
1. Service pauses automatically
2. Generates realistic "out of office" messages
3. Waits for rate limit reset (typically 1 hour)
4. Resumes automatically

### Invalid Tokens
If a user's API token becomes invalid:
1. Marked in dashboard with warning
2. Other users continue working
3. LLM generates realistic "where's {user}?" messages
4. Admin can update token to bring user back

### Service Interruptions
If the service crashes or is stopped:
1. State is saved after every activity
2. On restart, loads state and resumes
3. Generates "sorry for delay" comments if gap was significant

## Cost Considerations

### Asana API
- Free tier: 1,500 requests/hour
- Monitor usage in dashboard
- Adjust activity level to stay within limits

### Claude API (LLM)
- Sonnet 4.5: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- Typical usage: 50-100 tokens per generation
- Dashboard shows total tokens used
- **Estimate**: Medium activity job for 7 days ≈ $5-15

## Tips & Best Practices

### Starting Out
1. Start with **1-2 day duration** and **low activity** to test
2. Use **2-3 user tokens** minimum for realistic simulation
3. Choose **industry theme** that matches your use case
4. Monitor dashboard for first hour to ensure everything works

### Realistic Scenarios
- **Demo Data Refresh**: 3-7 days, medium activity, 3-5 users
- **Long-Term Testing**: 30+ days, low-medium activity, 5+ users
- **High Activity Sprint**: 1-2 weeks, high activity, burst pattern

### Avoiding Rate Limits
- Use **low activity** for longer durations
- **Global working hours** spreads activity more evenly
- Monitor **API usage** in dashboard
- Service auto-slows if approaching limits

### Multi-User Simulation
- Use real Asana users from your workspace
- Each user needs their own Personal Access Token
- More users = more realistic conversations
- Users will see their own actions in Asana

## Troubleshooting

**"No valid Asana API tokens provided"**
- Check tokens are valid (test at https://app.asana.com/api/1.0/users/me)
- Ensure tokens have access to the workspace
- Verify tokens aren't expired

**"Rate limit exceeded"**
- Service will auto-pause and resume
- Reduce activity level if recurring
- Check API usage in dashboard

**"Job not generating activity"**
- Check if it's outside working hours
- Verify job status is "running" not "paused"
- Look for errors in dashboard

**"LLM generation failing"**
- Verify ANTHROPIC_API_KEY is set correctly
- Check API key has credits
- Service will fall back to generic content if LLM fails

**"State file not found"**
- State files are in project root as `job_{id}.json`
- Don't delete these while jobs are running
- Backup important job files before cleanup

## CLI Mode (Advanced)

For programmatic control, you can run services directly:

```python
from continuous.services.asana_service import AsanaService
from continuous.state_manager import StateManager
from continuous.llm_generator import LLMGenerator
from continuous.connections.asana_connection import AsanaClientPool
import asyncio

# Configure
config = {
    "industry": "healthcare",
    "duration_days": 7,
    "workspace_gid": "YOUR_WORKSPACE_GID",
    "activity_level": "medium",
    # ... other settings
}

# Initialize
state_manager = StateManager(".")
llm = LLMGenerator("YOUR_ANTHROPIC_KEY")
clients = AsanaClientPool({"User1": "TOKEN1", "User2": "TOKEN2"})

# Create and run
service = AsanaService(config, state_manager, llm, clients)
asyncio.run(service.run())
```

## API Reference

The Flask API exposes these endpoints:

**GET** `/api/jobs` - List all jobs
**GET** `/api/jobs/{id}` - Get job details
**GET** `/api/jobs/{id}/activity_log` - Get activity log (paginated)
**POST** `/api/jobs/start` - Start new job
**POST** `/api/jobs/{id}/stop` - Stop job
**POST** `/api/jobs/{id}/pause` - Pause job
**POST** `/api/jobs/{id}/resume` - Resume job
**DELETE** `/api/jobs/{id}/delete` - Delete job
**POST** `/api/validate_token` - Validate Asana token
**POST** `/api/workspaces` - Get workspaces for token
**GET** `/api/health` - Health check

See `api_server.py` for full documentation.

## Future Enhancements

Planned features (marked as TODO in code):
- [ ] LLM response caching for cost reduction
- [ ] More granular per-user activity controls
- [ ] Custom work schedules per user
- [ ] Email/Slack notifications for errors
- [ ] Analytics dashboard with charts
- [ ] Configuration templates (save/load presets)
- [ ] Multi-platform support (Jira, Monday.com)
- [ ] Export activity history to CSV
- [ ] Webhooks for integration

## Contributing

This is a demo/utility project. Feel free to fork and customize for your needs.

## License

MIT License - use freely for demos, testing, development.

## Support

For issues or questions:
1. Check Troubleshooting section above
2. Review error logs in dashboard
3. Verify API keys and tokens are valid
4. Check rate limits haven't been exceeded

## Credits

Built with:
- Python 3
- Flask (REST API)
- Anthropic Claude (AI content generation)
- Asana API (project management)

---

**Note**: This tool generates synthetic data for testing and demos. Always ensure you have appropriate permissions before generating data in production workspaces.
