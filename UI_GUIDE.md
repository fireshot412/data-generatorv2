# Web UI Guide

The new web interface makes it easy to configure and manage continuous data generation jobs.

## Accessing the UI

1. Start the API server: `python api_server.py`
2. Open your browser to: **http://localhost:5000**

## UI Overview

The interface has two main tabs:

### 🚀 Continuous Mode Tab

This is where you configure and start new continuous generation jobs.

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│              Asana Data Generator                           │
│   Generate realistic Asana data - instantly or continuously │
├─────────────────────────────────────────────────────────────┤
│  [Continuous Mode]  [Active Jobs]                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🚀 Continuous Data Generation                              │
│                                                              │
│  Industry Theme (select one):                               │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐       │
│  │ Finance │ Health  │  Mfg    │ Travel  │  Tech   │       │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘       │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐       │
│  │ Retail  │  Edu    │  Gov    │ Energy  │  Media  │       │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘       │
│                                                              │
│  Anthropic API Key (Claude AI)                              │
│  [sk-ant-api03-..............................]              │
│                                                              │
│  Asana Workspace GID                                        │
│  [1234567890]                                               │
│                                                              │
│  Workspace Name (Optional)                                  │
│  [My Demo Workspace]                                        │
│                                                              │
│  Asana User API Tokens                                      │
│  ┌──────────────────────────────────────────────────┐      │
│  │ [Alice    ] [2/1234567890/xxxxx...] [×]         │      │
│  │ [Bob      ] [2/1234567890/yyyyy...] [×]         │      │
│  │ [Charlie  ] [2/1234567890/zzzzz...] [×]         │      │
│  └──────────────────────────────────────────────────┘      │
│  [+ Add Another User]                                       │
│                                                              │
│  Duration                                                   │
│  ○ Fixed: [7] days    ○ Indefinite (until stopped)         │
│                                                              │
│  Initial Projects                                           │
│  [3]                                                        │
│                                                              │
│  Activity Level                                             │
│  [Medium - Balanced, realistic activity ▼]                 │
│                                                              │
│  Working Hours Pattern                                      │
│  [US Workforce (9am-6pm PT, Mon-Fri) ▼]                    │
│                                                              │
│  Activity Pattern                                           │
│  Bursty ●─────────────○──────────────── Steady             │
│                                                              │
│  ⚙️ Advanced Settings                                       │
│                                                              │
│  Task Completion Rate (% per week)  [20]                   │
│  Blocked Task Frequency (%)         [15]                   │
│  Average Blocked Duration (days)    [2]                    │
│  Comment Frequency (per task/day)   [0.5]                  │
│  New Project Frequency (days)       [14]                   │
│                                                              │
│  [Start Continuous Generation 🚀]                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 📊 Active Jobs Tab

This shows all running, paused, and stopped jobs with real-time statistics.

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│              Asana Data Generator                           │
│   Generate realistic Asana data - instantly or continuously │
├─────────────────────────────────────────────────────────────┤
│  [Continuous Mode]  [Active Jobs]                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Active Continuous Jobs                                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Marketing Workspace (Healthcare)      [● Running]      │ │
│  │ Job ID: abc123 | Started: Oct 15, 9:00 AM             │ │
│  │                                                         │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┐        │ │
│  │  │    3     │    15    │    47    │     3    │        │ │
│  │  │ Projects │  Tasks   │ Comments │Completed │        │ │
│  │  └──────────┴──────────┴──────────┴──────────┘        │ │
│  │                                                         │ │
│  │  Runtime: 5h | Last activity: 2m ago                   │ │
│  │                                                         │ │
│  │  [⏸ Pause] [⏹ Stop] [📋 View Log] [🗑 Delete]         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Sales Workspace (Finance)         [⚠ Paused]          │ │
│  │ Job ID: def456 | Started: Oct 14, 2:00 PM             │ │
│  │                                                         │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┐        │ │
│  │  │    5     │    28    │    93    │     8    │        │ │
│  │  │ Projects │  Tasks   │ Comments │Completed │        │ │
│  │  └──────────┴──────────┴──────────┴──────────┘        │ │
│  │                                                         │ │
│  │  Runtime: 29h | Last activity: 45m ago                 │ │
│  │                                                         │ │
│  │  [▶️ Resume] [⏹ Stop] [📋 View Log] [🗑 Delete]        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [🔄 Refresh Jobs]                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Step-by-Step: Starting Your First Job

### 1. Get Your API Keys

**Anthropic API Key:**
- Go to https://console.anthropic.com/
- Sign up or log in
- Create a new API key
- Copy it (starts with `sk-ant-api03-...`)

**Asana Workspace GID:**
- Go to your Asana workspace
- Look at the URL: `https://app.asana.com/0/{WORKSPACE_GID}/...`
- Copy the workspace GID number

**Asana User API Tokens:**
- Go to https://app.asana.com/0/my-apps
- Click "Create New Personal Access Token"
- Name it (e.g., "Data Generator - Alice")
- Copy the token (starts with `2/...`)
- Repeat for 2-3 different users in your workspace

### 2. Fill Out the Form

1. **Select Industry**: Click on the industry that matches your use case
   - Healthcare for medical/clinical content
   - Finance for banking/investment content
   - Technology for software development content
   - etc.

2. **Paste API Keys**:
   - Anthropic key in the first field
   - Workspace GID in the second field
   - Give your workspace a friendly name

3. **Add Users**:
   - First user: Enter name (e.g., "Alice") and paste their token
   - Click "+ Add Another User"
   - Repeat for Bob, Charlie, etc.
   - **Tip**: Use 3-5 users for realistic conversations

4. **Configure Duration**:
   - For first test: Select "Fixed" and enter `2` days
   - For longer runs: Enter more days or select "Indefinite"

5. **Set Activity Level**:
   - **Low**: For testing, stays under API limits
   - **Medium**: Realistic team activity (recommended)
   - **High**: Very active, uses more API calls

6. **Choose Working Hours**:
   - **US Workforce**: 9am-6pm Pacific, Monday-Friday (recommended for demos)
   - **Global**: 24-hour activity across timezones

7. **Adjust Activity Pattern** (slider):
   - **Left (Bursty)**: Activity concentrated at 9am, 1pm, 4pm
   - **Middle**: Balanced
   - **Right (Steady)**: Evenly distributed throughout day

8. **Advanced Settings** (optional):
   - Leave defaults for first run
   - Adjust later based on what you want to test

### 3. Start the Job

Click **"Start Continuous Generation 🚀"**

You'll see:
- Success message: "✓ Continuous generation started! Job ID: abc123"
- Automatically switches to Active Jobs tab after 2 seconds

### 4. Monitor Progress

On the **Active Jobs** tab, you'll see:
- Job status (Running, Paused, Stopped)
- Real-time statistics:
  - Number of projects created
  - Number of tasks created
  - Number of comments added
  - Number of tasks completed
- Runtime (how long it's been running)
- Last activity timestamp

The dashboard auto-refreshes every 30 seconds.

### 5. Check Your Asana Workspace

Open your Asana workspace in another tab:
- You'll see new projects appearing
- Tasks being created with realistic names
- Comments from different users
- Tasks moving through states (in progress → blocked → completed)

**Everything is real data being created in your workspace!**

## Job Actions

### Pause a Job
- Click **⏸ Pause** to temporarily stop generation
- Job state is saved
- No new activities generated
- Click **▶️ Resume** to continue

### Stop a Job
- Click **⏹ Stop** to permanently stop generation
- Job state is saved
- Can view history but won't generate more data
- Cannot be resumed

### View Activity Log
- Click **📋 View Log** to see all generated activities
- Shows timestamps, users, actions
- Useful for debugging or auditing

### Delete a Job
- Click **🗑 Delete** to remove job and all history
- **Warning**: Cannot be undone!
- Stops job first if running
- Deletes the state file

## Tips for Success

### First-Time Setup
1. Start with **2 days duration** and **low activity**
2. Use **2-3 user tokens** minimum
3. Monitor for the first 30 minutes
4. Check your Asana workspace to verify data

### Avoiding Rate Limits
- Use **low activity** for longer durations
- **Global working hours** spreads activity more evenly
- Monitor API usage in the dashboard
- System auto-pauses if rate limit hit

### Realistic Scenarios
- **Quick Demo**: 1-2 days, medium activity, 3 users
- **Training Data**: 7-14 days, low activity, 5+ users
- **Load Testing**: 30+ days, high activity, 10+ users

### Multi-User Best Practices
- Use real users from your workspace
- Each user needs their own Personal Access Token
- More users = more realistic conversations
- 3-5 users is the sweet spot

## Troubleshooting

### "Failed to start job"
- Check all required fields are filled
- Verify API keys are valid
- Ensure workspace GID is correct
- Try pasting tokens again (no extra spaces)

### "No valid Asana API tokens provided"
- Test tokens at https://app.asana.com/api/1.0/users/me
- Make sure tokens have workspace access
- Check tokens aren't expired

### Job shows "Error" status
- Check dashboard for error details
- Common issues:
  - Invalid token for one user
  - Rate limit exceeded
  - Network connection lost
- Fix the issue, then start a new job

### Not seeing activity
- Check if it's during working hours (9am-6pm PT for US Workforce)
- Low activity = sparse generation (by design)
- Give it 10-15 minutes for first activities
- Check job status is "Running" not "Paused"

## Advanced Features

### Viewing Raw State Files
Jobs are stored as JSON files in the project directory:
```
job_abc123.json
```

You can open these to see:
- Complete job configuration
- All projects and tasks
- Activity log
- API usage stats
- Error history

### API Access
The UI uses REST API endpoints. You can also access directly:
```bash
# Get all jobs
curl http://localhost:5000/api/jobs

# Get specific job
curl http://localhost:5000/api/jobs/abc123

# Get activity log
curl http://localhost:5000/api/jobs/abc123/activity_log
```

See `README.md` for full API documentation.

## Next Steps

Once comfortable with the UI:
1. Try different industry themes
2. Adjust activity patterns to match your use case
3. Run longer durations for more data
4. Add more users for richer collaboration
5. Use activity logs to analyze what was generated

---

**The UI makes it easy to configure complex continuous generation jobs without touching any code!**
