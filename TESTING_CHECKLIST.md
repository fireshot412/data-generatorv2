# API Server Multi-Connection Testing Checklist

## Pre-Testing Setup

- [ ] Ensure Python environment is activated
- [ ] Install all dependencies: `pip install -r requirements.txt`
- [ ] Have valid Asana API token ready
- [ ] Have valid Okta SSWS token and org URL ready
- [ ] Clear any existing job state files: `rm -rf job_*.json`

---

## 1. Server Startup Tests

### Test 1.1: Server Starts Successfully
```bash
python3 api_server.py
```

**Expected Output**:
```
============================================================
Multi-Platform Continuous Data Generator - API Server
Supported Platforms: Asana, Okta
============================================================

Starting server on http://localhost:5001
Open http://localhost:5001 in your browser

Press Ctrl+C to stop
============================================================

Checking for jobs to restart...
============================================================
No jobs to restart
============================================================
```

- [ ] Server starts without errors
- [ ] Port 5001 is accessible
- [ ] Multi-platform message displayed
- [ ] Job restart check completes

---

### Test 1.2: Health Check
```bash
curl http://localhost:5001/api/health
```

**Expected Response**:
```json
{
  "success": true,
  "status": "running",
  "active_jobs": 0,
  "connection_types_supported": ["asana", "okta"],
  "version": "2.0.0"
}
```

- [ ] Returns 200 status
- [ ] Shows both connection types
- [ ] Version is 2.0.0
- [ ] Active jobs is 0

---

## 2. Asana Token Validation Tests

### Test 2.1: Valid Asana Token
```bash
curl -X POST http://localhost:5001/api/validate_token \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "asana",
    "api_key": "YOUR_ASANA_TOKEN"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "valid": true,
  "connection_type": "asana",
  "user": {
    "name": "Your Name",
    "email": "your.email@example.com"
  }
}
```

- [ ] Returns 200 status
- [ ] Valid is true
- [ ] User info is populated
- [ ] Connection type is "asana"

---

### Test 2.2: Invalid Asana Token
```bash
curl -X POST http://localhost:5001/api/validate_token \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "asana",
    "api_key": "invalid_token"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "valid": false,
  "connection_type": "asana"
}
```

- [ ] Returns 200 status
- [ ] Valid is false
- [ ] Connection type is "asana"

---

### Test 2.3: Backward Compatibility (No connection_type)
```bash
curl -X POST http://localhost:5001/api/validate_token \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_ASANA_TOKEN"
  }'
```

**Expected**: Should default to Asana validation

- [ ] Defaults to Asana
- [ ] Works same as Test 2.1

---

## 3. Okta Token Validation Tests

### Test 3.1: Valid Okta Token
```bash
curl -X POST http://localhost:5001/api/validate_token \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "token": "YOUR_OKTA_SSWS_TOKEN",
    "org_url": "https://dev-123456.okta.com"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "valid": true,
  "connection_type": "okta",
  "user": {
    "name": "Admin User",
    "email": "admin@example.com",
    "id": "00u1abc2def3ghi4"
  }
}
```

- [ ] Returns 200 status
- [ ] Valid is true
- [ ] User info includes Okta ID
- [ ] Connection type is "okta"

---

### Test 3.2: Invalid Okta Token
```bash
curl -X POST http://localhost:5001/api/validate_token \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "token": "invalid_token",
    "org_url": "https://dev-123456.okta.com"
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "valid": false,
  "connection_type": "okta",
  "error": "..."
}
```

- [ ] Returns 401 status
- [ ] Valid is false
- [ ] Error message present

---

### Test 3.3: Missing org_url
```bash
curl -X POST http://localhost:5001/api/validate_token \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "token": "YOUR_OKTA_SSWS_TOKEN"
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "error": "No org_url provided"
}
```

- [ ] Returns 400 status
- [ ] Error message about missing org_url

---

## 4. Okta Organization Tests

### Test 4.1: Get Okta Org Info
```bash
curl -X POST http://localhost:5001/api/okta/orgs \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_OKTA_SSWS_TOKEN",
    "org_url": "https://dev-123456.okta.com"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "org": {
    "org_url": "https://dev-123456.okta.com",
    "org_name": "dev-123456",
    "accessible": true,
    "authenticated_user": {
      "name": "Admin User",
      "email": "admin@example.com"
    }
  }
}
```

- [ ] Returns 200 status
- [ ] Org info populated
- [ ] Org name extracted correctly
- [ ] Authenticated user info present

---

### Test 4.2: List Okta Apps
```bash
curl -X POST http://localhost:5001/api/okta/apps \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_OKTA_SSWS_TOKEN",
    "org_url": "https://dev-123456.okta.com",
    "limit": 10
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "apps": [
    {
      "id": "0oa1abc2def3ghi4",
      "name": "App Name",
      "label": "App Label",
      "status": "ACTIVE",
      "created": "2024-01-15T10:30:00.000Z",
      "lastUpdated": "2024-01-20T14:45:00.000Z"
    }
  ],
  "total": 1
}
```

- [ ] Returns 200 status
- [ ] Apps array populated
- [ ] Each app has required fields
- [ ] Total count matches

---

### Test 4.3: List Okta Users
```bash
curl -X POST http://localhost:5001/api/okta/users \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_OKTA_SSWS_TOKEN",
    "org_url": "https://dev-123456.okta.com",
    "limit": 10
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "users": [
    {
      "id": "00u1abc2def3ghi4",
      "name": "User Name",
      "email": "user@example.com",
      "login": "user@example.com",
      "status": "ACTIVE",
      "created": "...",
      "lastUpdated": "..."
    }
  ],
  "total": 1
}
```

- [ ] Returns 200 status
- [ ] Users array populated
- [ ] Each user has required fields
- [ ] Total count matches

---

### Test 4.4: List Okta Groups
```bash
curl -X POST http://localhost:5001/api/okta/groups \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_OKTA_SSWS_TOKEN",
    "org_url": "https://dev-123456.okta.com",
    "limit": 10
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "groups": [
    {
      "id": "00g1abc2def3ghi4",
      "name": "Group Name",
      "description": "Group Description",
      "type": "OKTA_GROUP",
      "created": "...",
      "lastUpdated": "..."
    }
  ],
  "total": 1
}
```

- [ ] Returns 200 status
- [ ] Groups array populated
- [ ] Each group has required fields
- [ ] Total count matches

---

## 5. Asana Job Tests

### Test 5.1: Create Asana Job
```bash
curl -X POST http://localhost:5001/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "asana",
    "industry": "technology",
    "workspace_gid": "YOUR_WORKSPACE_GID",
    "user_tokens": [
      {"name": "user1", "token": "YOUR_ASANA_TOKEN"}
    ],
    "anthropic_api_key": "YOUR_ANTHROPIC_KEY"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "job_id": "job_abc123",
  "connection_type": "asana",
  "message": "Asana continuous generation started - Job ID: job_abc123"
}
```

- [ ] Returns 200 status
- [ ] Job ID is returned
- [ ] Connection type is "asana"
- [ ] Job file created (`job_abc123.json`)
- [ ] Job appears in active_jobs

---

### Test 5.2: Missing Workspace GID (Asana)
```bash
curl -X POST http://localhost:5001/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "asana",
    "industry": "technology",
    "user_tokens": [
      {"name": "user1", "token": "YOUR_ASANA_TOKEN"}
    ],
    "anthropic_api_key": "YOUR_ANTHROPIC_KEY"
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "error": "Missing required field for Asana: workspace_gid"
}
```

- [ ] Returns 400 status
- [ ] Error message specifies missing field

---

## 6. Okta Job Tests

### Test 6.1: Create Okta Job
```bash
curl -X POST http://localhost:5001/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "industry": "technology",
    "org_url": "https://dev-123456.okta.com",
    "org_size": "midsize",
    "initial_users": 20,
    "user_tokens": [
      {
        "name": "admin1",
        "token": "YOUR_OKTA_TOKEN",
        "org_url": "https://dev-123456.okta.com"
      }
    ],
    "anthropic_api_key": "YOUR_ANTHROPIC_KEY"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "job_id": "job_xyz789",
  "connection_type": "okta",
  "message": "Okta continuous generation started - Job ID: job_xyz789"
}
```

- [ ] Returns 200 status
- [ ] Job ID is returned
- [ ] Connection type is "okta"
- [ ] Job file created (`job_xyz789.json`)
- [ ] Job appears in active_jobs

---

### Test 6.2: Missing org_size (Okta)
```bash
curl -X POST http://localhost:5001/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "industry": "technology",
    "org_url": "https://dev-123456.okta.com",
    "user_tokens": [
      {
        "name": "admin1",
        "token": "YOUR_OKTA_TOKEN",
        "org_url": "https://dev-123456.okta.com"
      }
    ],
    "anthropic_api_key": "YOUR_ANTHROPIC_KEY"
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "error": "Missing required field for Okta: org_size"
}
```

- [ ] Returns 400 status
- [ ] Error message specifies missing field

---

### Test 6.3: Invalid org_url Format
```bash
curl -X POST http://localhost:5001/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "industry": "technology",
    "org_url": "dev-123456.okta.com",
    "org_size": "midsize",
    "user_tokens": [
      {
        "name": "admin1",
        "token": "YOUR_OKTA_TOKEN",
        "org_url": "dev-123456.okta.com"
      }
    ],
    "anthropic_api_key": "YOUR_ANTHROPIC_KEY"
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "error": "org_url must start with https://"
}
```

- [ ] Returns 400 status
- [ ] Error message about org_url format

---

### Test 6.4: Missing org_url in Token
```bash
curl -X POST http://localhost:5001/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "industry": "technology",
    "org_url": "https://dev-123456.okta.com",
    "org_size": "midsize",
    "user_tokens": [
      {
        "name": "admin1",
        "token": "YOUR_OKTA_TOKEN"
      }
    ],
    "anthropic_api_key": "YOUR_ANTHROPIC_KEY"
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "error": "Each user token must include org_url for Okta"
}
```

- [ ] Returns 400 status
- [ ] Error message about missing org_url in token

---

## 7. Job Management Tests

### Test 7.1: List All Jobs
```bash
curl http://localhost:5001/api/jobs
```

**Expected Response**:
```json
{
  "success": true,
  "jobs": [
    {
      "job_id": "job_abc123",
      "connection_type": "asana",
      "status": "running",
      "industry": "technology",
      ...
    },
    {
      "job_id": "job_xyz789",
      "connection_type": "okta",
      "status": "running",
      "industry": "technology",
      ...
    }
  ]
}
```

- [ ] Returns 200 status
- [ ] Shows both job types
- [ ] Connection type included for each job

---

### Test 7.2: Get Specific Job
```bash
curl http://localhost:5001/api/jobs/job_abc123
```

**Expected Response**:
```json
{
  "success": true,
  "job": {
    "job_id": "job_abc123",
    "connection_type": "asana",
    "status": "running",
    ...
  }
}
```

- [ ] Returns 200 status
- [ ] Job details populated
- [ ] Connection type present

---

### Test 7.3: Pause Job
```bash
curl -X POST http://localhost:5001/api/jobs/job_abc123/pause
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Job job_abc123 paused"
}
```

- [ ] Returns 200 status
- [ ] Job status changes to "paused"
- [ ] Job state file updated

---

### Test 7.4: Resume Job
```bash
curl -X POST http://localhost:5001/api/jobs/job_abc123/resume
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Job job_abc123 resumed"
}
```

- [ ] Returns 200 status
- [ ] Job status changes to "running"
- [ ] Activity generation resumes

---

## 8. Cleanup Tests

### Test 8.1: Cleanup Asana Job
```bash
curl -X POST http://localhost:5001/api/jobs/job_abc123/cleanup
```

**Expected Response**:
```json
{
  "success": true,
  "deleted_projects": 5,
  "deleted_tasks": 50,
  "deleted_subtasks": 100,
  "total_projects": 5,
  "failed_projects": []
}
```

- [ ] Returns 200 status
- [ ] Projects deleted from Asana
- [ ] Tasks deleted from Asana
- [ ] Subtasks deleted from Asana

---

### Test 8.2: Cleanup Okta Job
```bash
curl -X POST http://localhost:5001/api/jobs/job_xyz789/cleanup
```

**Expected Response**:
```json
{
  "success": true,
  "users_deleted": 20,
  "groups_deleted": 5,
  "assignments_removed": 80,
  "errors": []
}
```

- [ ] Returns 200 status
- [ ] Users deleted from Okta
- [ ] Groups deleted from Okta
- [ ] App assignments removed

---

## 9. Job Restart Tests

### Test 9.1: Restart Server with Mixed Jobs
**Steps**:
1. Create both Asana and Okta jobs
2. Verify both are running
3. Stop server (Ctrl+C)
4. Restart server
5. Check jobs list

**Expected**:
- [ ] Both jobs show in restart log
- [ ] Asana job restarts as AsanaService
- [ ] Okta job restarts as OktaService
- [ ] Both jobs resume activity generation

---

### Test 9.2: Restart with Paused Jobs
**Steps**:
1. Create and pause jobs
2. Restart server
3. Check job status

**Expected**:
- [ ] Paused jobs restart in paused state
- [ ] Jobs don't generate activity until resumed

---

## 10. Error Handling Tests

### Test 10.1: Unsupported Connection Type
```bash
curl -X POST http://localhost:5001/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "salesforce",
    "industry": "technology"
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "error": "Unsupported connection type: salesforce"
}
```

- [ ] Returns 400 status
- [ ] Error message indicates unsupported type

---

### Test 10.2: Invalid Tokens
**Steps**:
1. Try to create job with invalid tokens
2. Verify error handling

**Expected**:
- [ ] Returns 400 status
- [ ] Error indicates no valid tokens

---

## 11. Integration Tests

### Test 11.1: Full Asana Workflow
**Steps**:
1. Validate token
2. List workspaces
3. Create job
4. Monitor activity
5. Pause job
6. Resume job
7. Cleanup
8. Delete job

**Expected**:
- [ ] All steps complete successfully
- [ ] Data created in Asana
- [ ] Data cleaned up properly

---

### Test 11.2: Full Okta Workflow
**Steps**:
1. Validate token
2. Get org info
3. List apps/users/groups
4. Create job
5. Monitor activity
6. Cleanup
7. Delete job

**Expected**:
- [ ] All steps complete successfully
- [ ] Users/groups created in Okta
- [ ] Data cleaned up properly

---

### Test 11.3: Mixed Jobs Workflow
**Steps**:
1. Create Asana job
2. Create Okta job
3. Verify both running independently
4. Cleanup both
5. Verify isolation (Asana cleanup doesn't affect Okta)

**Expected**:
- [ ] Jobs don't interfere with each other
- [ ] Cleanup operations are isolated
- [ ] State management works correctly

---

## 12. Performance Tests

### Test 12.1: Concurrent Job Creation
**Steps**:
1. Create 3 Asana jobs simultaneously
2. Create 3 Okta jobs simultaneously
3. Monitor server resources

**Expected**:
- [ ] All jobs created successfully
- [ ] No thread conflicts
- [ ] Reasonable memory usage

---

### Test 12.2: Rate Limit Handling
**Steps**:
1. Create job with high activity level
2. Monitor for rate limit errors
3. Verify graceful handling

**Expected**:
- [ ] Rate limits logged
- [ ] Service pauses appropriately
- [ ] No crashes

---

## Testing Summary

**Total Tests**: 50+

**Categories**:
- Server Startup: 2 tests
- Token Validation: 6 tests
- Okta Organization: 4 tests
- Asana Jobs: 2 tests
- Okta Jobs: 4 tests
- Job Management: 4 tests
- Cleanup: 2 tests
- Job Restart: 2 tests
- Error Handling: 2 tests
- Integration: 3 tests
- Performance: 2 tests

**Pass Criteria**:
- All tests must pass
- No server crashes
- Proper error handling
- Clean state management
- Successful cleanup operations

---

## Notes

- Replace `YOUR_ASANA_TOKEN`, `YOUR_OKTA_TOKEN`, `YOUR_OKTA_ORG_URL`, etc. with actual values
- Run tests in order for best results
- Monitor server logs for detailed error information
- Check job state files for debugging
- Verify platform data (Asana/Okta) is created and cleaned up properly
