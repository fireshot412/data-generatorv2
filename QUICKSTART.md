# Quick Start Guide

Get up and running with Continuous Data Generation in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Asana account with API access
- Anthropic API key
- 2-3 Asana API tokens from different users

## Step 1: Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

## Step 2: Set Up API Keys (2 minutes)

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```bash
# Get from https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-xxx

# Get from https://app.asana.com/0/my-apps
ASANA_TOKEN_USER1=2/1234567890/xxx
ASANA_TOKEN_USER2=2/1234567890/yyy
ASANA_TOKEN_USER3=2/1234567890/zzz
```

## Step 3: Start the Server (30 seconds)

```bash
python api_server.py
```

You should see:
```
Asana Continuous Data Generator - API Server
============================================================

Starting server on http://localhost:5000
Open http://localhost:5000 in your browser
```

## Step 4: Open the Web UI (30 seconds)

Open your browser to: **http://localhost:5000**

## Step 5: Start Your First Job (1 minute)

### In the Web UI:

The new UI has everything you need on one screen!

1. **Industry Theme**: Click on your preferred industry (e.g., "Healthcare", "Technology")

2. **Add API Keys**:
   - **Anthropic API Key**: Paste your Claude API key
   - **Asana Workspace GID**: Enter your workspace ID (from URL)
   - **Workspace Name**: Give it a friendly name (optional)

3. **Add User Tokens**:
   - First user: Enter name (e.g., "Alice") and paste their Asana token
   - Click **"+ Add Another User"** for Bob, Charlie, etc.
   - **Tip**: Add 2-3 users minimum for realistic collaboration

4. **Configure Duration**:
   - Select **"Fixed"** and enter **2 days** for testing
   - (Or choose "Indefinite" for continuous running)

5. **Set Activity Level**:
   - Choose **"Low"** for first test (stays under API limits)

6. **Advanced Settings**: Leave defaults for now

7. **Click "Start Continuous Generation 🚀"**

The UI will automatically switch to the **Active Jobs** tab where you can monitor progress!

## Step 6: Monitor Progress (ongoing)

Watch the dashboard to see:
- Real-time activity updates
- Comments being added
- Tasks progressing through states
- API usage tracking

## Verify in Asana

Open your Asana workspace in another tab and watch:
- New projects appearing
- Tasks being created
- Comments from different "users"
- Tasks moving through workflow states

## Your First Job is Running!

The system will now:
- Generate realistic project and task names
- Create industry-specific comments
- Simulate team collaboration
- Progress tasks through lifecycle (new → in progress → blocked → completed)
- All during realistic work hours with burst patterns

## Common First-Time Settings

### Conservative (Recommended for First Try)
```
Duration: 1-2 days
Activity Level: Low
Initial Projects: 2
Working Hours: US Workforce
Burst Factor: 0.5 (middle)
```

### Moderate Demo Data
```
Duration: 5-7 days
Activity Level: Medium
Initial Projects: 3
Working Hours: US Workforce
Burst Factor: 0.3 (more bursty)
```

### Active Sprint Simulation
```
Duration: 14 days
Activity Level: High
Initial Projects: 5
Working Hours: Global
Burst Factor: 0.2 (very bursty)
```

## Troubleshooting

**"No valid Asana API tokens provided"**
- Double-check tokens in your `.env` file
- Test tokens at https://app.asana.com/api/1.0/users/me

**"Service not generating activity"**
- Check if it's outside working hours (9am-6pm PT if US Workforce)
- Give it 5-10 minutes - activity is spread realistically
- Check dashboard for any errors

**"Rate limit hit"**
- Normal! System will auto-pause and resume
- Reduce activity level for future jobs

## Next Steps

Once your first job is running smoothly:

1. **Try different industries** to see varied content
2. **Adjust activity patterns** (burst vs steady)
3. **Add more users** for richer conversations
4. **Increase duration** for longer-term data
5. **Export activity logs** for analysis

## Tips

- Start small (1-2 days) to learn the system
- Monitor for first 30 minutes to ensure it's working
- Add at least 3 user tokens for realistic conversations
- Check the activity log to see what's being generated
- Asana has rate limits (1500 calls/hour) - low activity respects this

## Need Help?

- Check `README.md` for detailed documentation
- Review `IMPLEMENTATION_SUMMARY.md` for technical details
- Look at `example_config.json` for all configuration options
- Check error logs in the dashboard

---

**That's it!** You now have realistic, continuous Asana data being generated. Watch it evolve over time as your simulated team works on projects.
