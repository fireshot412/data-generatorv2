# Testing Guide

Quick guide to test the complete system end-to-end.

## Prerequisites Test

```bash
# 1. Check Python version (need 3.8+)
python3 --version

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify installations
python3 -c "import anthropic; print('✓ Anthropic installed')"
python3 -c "import flask; print('✓ Flask installed')"
python3 -c "import requests; print('✓ Requests installed')"
```

## Unit Tests (Individual Components)

### Test 1: LLM Generator

```bash
python3 continuous/llm_generator.py YOUR_ANTHROPIC_API_KEY
```

**Expected Output:**
```
Testing LLM Generator
============================================================

Generating project name for Healthcare:
  -> Electronic Health Records Migration

Generating task name:
  -> Update HIPAA documentation

Generating comment (starting work):
  -> Starting work on this. Will coordinate with compliance...

Generating comment (blocked):
  -> Blocked - waiting on security review from InfoSec team

API Usage Stats:
  api_calls: 4
  input_tokens: 234
  output_tokens: 89
```

### Test 2: State Manager

```bash
python3 continuous/state_manager.py
```

**Expected Output:**
```
Created job: abc12345

All jobs: 1
  abc12345: running - healthcare

State stats:
  Projects: 1
  Tasks: 1
  Comments: 1
```

### Test 3: Scheduler

```bash
python3 continuous/scheduler.py
```

**Expected Output:**
```
Testing Activity Scheduler
============================================================

Time: Tuesday 09:00 AM
  Working hours: True
  Burst time: True
  Should generate: True

Time: Tuesday 02:30 PM
  Working hours: True
  Burst time: False
  Should generate: True

Time: Tuesday 07:00 PM
  Working hours: False
  Burst time: False
  Should generate: False

Time: Saturday 10:00 AM
  Working hours: False
  Burst time: False
  Should generate: False

Testing activity selection
  Activity 1: comment_start_work
  Activity 2: comment_progress
  Activity 3: comment_blocked
  Activity 4: create_task
  ...
```

### Test 4: Asana Client

```bash
python3 continuous/asana_client.py YOUR_ASANA_API_TOKEN
```

**Expected Output:**
```
Testing Asana Client...
✓ Token is valid
✓ User: Your Name (your.email@example.com)
```

## Integration Test (API Server)

### Test 1: Start Server

```bash
python3 api_server.py
```

**Expected Output:**
```
============================================================
Asana Continuous Data Generator - API Server
============================================================

Starting server on http://localhost:5000
Open http://localhost:5000 in your browser

Press Ctrl+C to stop
============================================================
 * Running on http://0.0.0.0:5000
```

**Keep this running for next tests.**

### Test 2: Health Check

Open new terminal:

```bash
curl http://localhost:5000/api/health
```

**Expected:**
```json
{
  "success": true,
  "status": "running",
  "active_jobs": 0
}
```

### Test 3: Get Jobs (Empty)

```bash
curl http://localhost:5000/api/jobs
```

**Expected:**
```json
{
  "success": true,
  "jobs": []
}
```

### Test 4: Validate Token

```bash
curl -X POST http://localhost:5000/api/validate_token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_ASANA_TOKEN"}'
```

**Expected:**
```json
{
  "success": true,
  "valid": true,
  "user": {
    "name": "Your Name",
    "email": "your.email@example.com"
  }
}
```

## End-to-End Test (Web UI)

### Test 1: Load UI

1. Open browser: `http://localhost:5000`
2. Should see:
   - Header: "Asana Data Generator"
   - Two tabs: "Continuous Mode" and "Active Jobs"
   - Industry grid with 10 industries
   - Form fields for API keys
   - User token section

**✓ Pass if UI loads without errors**

### Test 2: Industry Selection

1. Click different industries
2. Verify they highlight when selected
3. Click "Technology"

**✓ Pass if clicking changes selection**

### Test 3: Add/Remove Users

1. Default: 1 user token field visible
2. Click "+ Add Another User"
3. Second field appears
4. Click "×" on second field
5. Second field removed
6. Try removing first field
7. Should show error: "You must have at least one user token"

**✓ Pass if add/remove works with minimum enforced**

### Test 4: Duration Toggle

1. Select "Fixed" radio button
2. Days input enabled
3. Enter "7"
4. Select "Indefinite" radio button
5. Days input disabled

**✓ Pass if radio buttons toggle correctly**

### Test 5: Slider

1. Drag "Activity Pattern" slider
2. Verify it moves smoothly
3. Check value updates (0.0 to 1.0)

**✓ Pass if slider works**

### Test 6: Start Job (Minimal Test)

**Setup:** Use a test workspace you don't mind filling with data.

1. Fill out form:
   - Industry: Technology
   - Anthropic Key: (your key)
   - Workspace GID: (your test workspace)
   - User 1: "TestBot" + (your token)
   - Duration: Fixed, 1 day
   - Activity: Low
   - Leave rest as defaults

2. Click "Start Continuous Generation 🚀"

3. Button should:
   - Show "Starting..."
   - Disable temporarily

4. Expected result:
   - Success alert: "✓ Continuous generation started! Job ID: ..."
   - After 2 seconds, switches to "Active Jobs" tab

5. On Active Jobs tab:
   - Should see new job card
   - Status: "Running"
   - Stats: Projects: 0 (initially)

6. Wait 2-3 minutes, click "🔄 Refresh Jobs"
   - Stats should update
   - Projects: 1-2
   - Tasks: 3-5
   - Comments: 0-2

7. Check your Asana workspace:
   - Should see new projects
   - Should see tasks in projects

**✓ Pass if job starts and creates data**

### Test 7: Pause/Resume

1. Click "⏸ Pause" on running job
2. Status changes to "Paused"
3. Button changes to "▶️ Resume"
4. Click "▶️ Resume"
5. Status back to "Running"
6. Button back to "⏸ Pause"

**✓ Pass if pause/resume toggles**

### Test 8: Stop Job

1. Click "⏹ Stop"
2. Confirmation dialog appears
3. Click OK
4. Status changes to "Stopped"
5. Action buttons change (no pause/resume)
6. Can still view log, delete

**✓ Pass if stop works with confirmation**

### Test 9: Delete Job

1. Click "🗑 Delete"
2. Warning dialog appears
3. Click OK
4. Job removed from list

**✓ Pass if delete removes job**

## Load Test (Optional)

Test multiple concurrent jobs:

1. Start Job 1: Healthcare, 3 days, Low activity
2. Start Job 2: Finance, 2 days, Medium activity
3. Start Job 3: Technology, 1 day, High activity

4. Verify:
   - All 3 jobs appear in dashboard
   - Each has different stats
   - All update independently
   - Can pause/resume each individually

**✓ Pass if multiple jobs run simultaneously**

## Error Testing

### Test 1: Invalid Anthropic Key

1. Enter fake key: "sk-ant-api03-fake"
2. Fill rest of form
3. Click Start
4. Should show error alert
5. Job should NOT start

**✓ Pass if invalid key caught**

### Test 2: Invalid Asana Token

1. Enter valid Anthropic key
2. Enter fake Asana token: "2/fake/token"
3. Click Start
4. Should show error: "No valid Asana API tokens provided"

**✓ Pass if invalid token caught**

### Test 3: Missing Required Field

1. Leave Anthropic key blank
2. Click Start
3. Browser should show HTML5 validation error

**✓ Pass if required validation works**

### Test 4: Empty User Tokens

1. Remove all user token fields (try to)
2. Should prevent removing last one
3. Error: "You must have at least one user token"

**✓ Pass if minimum enforced**

## Performance Test

### Test Job Creation Speed

```bash
time curl -X POST http://localhost:5000/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "technology",
    "workspace_gid": "YOUR_GID",
    "duration_days": 1,
    "initial_projects": 2,
    "activity_level": "low",
    "working_hours": "us_workforce",
    "burst_factor": 0.5,
    "task_completion_rate": 20,
    "blocked_task_frequency": 15,
    "blocked_task_duration": 2,
    "comment_frequency": 0.5,
    "new_project_frequency_days": 14,
    "privacy": "public",
    "user_tokens": [{"name": "Test", "token": "YOUR_TOKEN"}],
    "anthropic_api_key": "YOUR_KEY"
  }'
```

**Expected:** < 5 seconds

**✓ Pass if completes quickly**

### Test Dashboard Refresh Speed

```bash
time curl http://localhost:5000/api/jobs
```

**Expected:** < 500ms (even with 10+ jobs)

**✓ Pass if fast response**

## State File Verification

After running a job for a few minutes:

```bash
# List state files
ls -lh job_*.json

# View a state file
cat job_abc12345.json | python3 -m json.tool | head -50
```

**Expected:**
- Valid JSON
- Contains: job_id, status, projects, tasks, activity_log, stats
- File size: 10-500 KB depending on runtime

**✓ Pass if state file is valid JSON with expected structure**

## Cleanup

After testing:

```bash
# Stop API server (Ctrl+C in server terminal)

# Delete test state files
rm job_*.json

# Delete test projects from Asana workspace manually
```

## Troubleshooting Test Failures

### Server won't start
- Check port 5000 not already in use: `lsof -i :5000`
- Try different port in api_server.py
- Check Python version: `python3 --version`

### UI won't load
- Check server is running
- Check browser console for errors
- Try different browser
- Clear browser cache

### Jobs won't start
- Verify API keys are valid
- Check workspace GID is correct
- Look at server terminal for errors
- Check Python imports worked

### No data being generated
- Check job status is "Running" not "Paused"
- Check if it's during working hours (9am-6pm PT for US Workforce)
- Low activity = sparse generation (wait longer)
- Check server terminal for errors

### Rate limit errors
- This is normal! System auto-handles
- Will pause and resume
- Reduce activity level for future jobs

## Success Criteria

All tests should pass:

- [x] All Python modules import without errors
- [x] API server starts successfully
- [x] UI loads at http://localhost:5000
- [x] Can start a job via UI
- [x] Job creates data in Asana
- [x] Dashboard shows job stats
- [x] Can pause/resume job
- [x] Can stop job
- [x] Can delete job
- [x] State files are created and valid
- [x] Error handling works (invalid keys, etc.)

If all pass: **System is working correctly!** 🎉

---

**Ready for production use!**
