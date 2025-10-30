# API Server Multi-Connection Support - Implementation Summary

## Overview

The API server (`api_server.py`) has been successfully updated to support multiple connection types (Asana and Okta) for the data generator v2 project. This document summarizes all changes, new endpoints, and provides usage examples.

## Version Information

- **Version**: 2.0.0
- **Supported Connection Types**: Asana, Okta
- **Backward Compatible**: Yes (defaults to Asana for legacy requests)

---

## 1. Endpoints Added/Modified

### Modified Endpoints

#### `POST /api/jobs/start`
**Status**: Modified
**Purpose**: Start a new continuous generation job (now supports both Asana and Okta)

**New Behavior**:
- Reads `connection_type` from request body (defaults to "asana")
- Routes to appropriate service based on connection type
- Validates connection-specific required fields
- Returns `connection_type` in response

**Asana Request Example**:
```json
{
  "connection_type": "asana",
  "industry": "technology",
  "workspace_gid": "123456789",
  "user_tokens": [
    {"name": "user1", "token": "1/234567890abcdef"},
    {"name": "user2", "token": "1/234567890ghijkl"}
  ],
  "anthropic_api_key": "sk-ant-..."
}
```

**Okta Request Example**:
```json
{
  "connection_type": "okta",
  "industry": "technology",
  "org_url": "https://dev-123456.okta.com",
  "org_size": "midsize",
  "initial_users": 50,
  "user_tokens": [
    {
      "name": "admin1",
      "token": "00abc123...",
      "org_url": "https://dev-123456.okta.com"
    }
  ],
  "anthropic_api_key": "sk-ant-..."
}
```

**Response**:
```json
{
  "success": true,
  "job_id": "job_abc123",
  "connection_type": "okta",
  "message": "Okta continuous generation started - Job ID: job_abc123"
}
```

---

#### `POST /api/jobs/<job_id>/cleanup`
**Status**: Modified
**Purpose**: Clean up platform data for a job (now supports both Asana and Okta)

**New Behavior**:
- Reads `connection_type` from job state
- Routes to appropriate cleanup method
- Returns connection-specific cleanup results

**Asana Response**:
```json
{
  "success": true,
  "deleted_projects": 10,
  "deleted_tasks": 150,
  "deleted_subtasks": 300,
  "total_projects": 10,
  "failed_projects": []
}
```

**Okta Response**:
```json
{
  "success": true,
  "users_deleted": 50,
  "groups_deleted": 8,
  "assignments_removed": 200,
  "errors": []
}
```

---

#### `POST /api/validate_token`
**Status**: Modified
**Purpose**: Validate API token (now supports both Asana and Okta)

**New Behavior**:
- Reads `connection_type` from request body (defaults to "asana")
- Validates token using appropriate platform API
- Returns platform-specific user information

**Asana Request**:
```json
{
  "connection_type": "asana",
  "api_key": "1/234567890abcdef"
}
```

**Okta Request**:
```json
{
  "connection_type": "okta",
  "token": "00abc123...",
  "org_url": "https://dev-123456.okta.com"
}
```

**Okta Response**:
```json
{
  "success": true,
  "valid": true,
  "connection_type": "okta",
  "user": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "id": "00u1abc2def3ghi4"
  }
}
```

---

#### `GET /api/health`
**Status**: Modified
**Purpose**: Health check endpoint

**New Response**:
```json
{
  "success": true,
  "status": "running",
  "active_jobs": 3,
  "connection_types_supported": ["asana", "okta"],
  "version": "2.0.0"
}
```

---

### New Okta-Specific Endpoints

#### `POST /api/okta/orgs`
**Purpose**: Get Okta org information and validate access

**Request**:
```json
{
  "token": "00abc123...",
  "org_url": "https://dev-123456.okta.com"
}
```

**Response**:
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

---

#### `POST /api/okta/apps`
**Purpose**: List applications in Okta org

**Request**:
```json
{
  "token": "00abc123...",
  "org_url": "https://dev-123456.okta.com",
  "limit": 50
}
```

**Response**:
```json
{
  "success": true,
  "apps": [
    {
      "id": "0oa1abc2def3ghi4",
      "name": "Slack",
      "label": "Slack",
      "status": "ACTIVE",
      "created": "2024-01-15T10:30:00.000Z",
      "lastUpdated": "2024-01-20T14:45:00.000Z"
    }
  ],
  "total": 1
}
```

---

#### `POST /api/okta/users`
**Purpose**: List users in Okta org

**Request**:
```json
{
  "token": "00abc123...",
  "org_url": "https://dev-123456.okta.com",
  "limit": 50
}
```

**Response**:
```json
{
  "success": true,
  "users": [
    {
      "id": "00u1abc2def3ghi4",
      "name": "Jane Smith",
      "email": "jane.smith@example.com",
      "login": "jane.smith@example.com",
      "status": "ACTIVE",
      "created": "2024-01-10T09:00:00.000Z",
      "lastUpdated": "2024-01-25T16:30:00.000Z"
    }
  ],
  "total": 1
}
```

---

#### `POST /api/okta/groups`
**Purpose**: List groups in Okta org

**Request**:
```json
{
  "token": "00abc123...",
  "org_url": "https://dev-123456.okta.com",
  "limit": 50
}
```

**Response**:
```json
{
  "success": true,
  "groups": [
    {
      "id": "00g1abc2def3ghi4",
      "name": "Engineering Department",
      "description": "All engineering team members",
      "type": "OKTA_GROUP",
      "created": "2024-01-05T08:00:00.000Z",
      "lastUpdated": "2024-01-22T11:15:00.000Z"
    }
  ],
  "total": 1
}
```

---

## 2. Connection-Type Routing Implementation

### Route Decision Flow

```
Request → Extract connection_type → Route to Service
    |
    ├─ "asana" → AsanaClientPool → ContinuousService (Asana)
    |
    └─ "okta" → OktaClientPool → OktaService
```

### Key Routing Points

1. **Job Start** (`/api/jobs/start`):
   - Validates connection-specific required fields
   - Creates appropriate client pool
   - Instantiates correct service class
   - Returns job_id with connection_type

2. **Job Cleanup** (`/api/jobs/<job_id>/cleanup`):
   - Loads state to get connection_type
   - Routes to `cleanup_asana_data()` or `cleanup_platform_data()`
   - Returns connection-specific results

3. **Job Restart** (`restart_running_jobs()`):
   - Reads connection_type from saved state
   - Recreates appropriate service
   - Maintains backward compatibility with legacy jobs

---

## 3. Token Validation

### Asana Token Validation
- Uses `AsanaClient.validate_token()`
- Returns user name and email
- No additional fields required

### Okta Token Validation
- Uses `OktaConnection.validate_token()`
- Requires both `token` and `org_url`
- Returns user name, email, and Okta user ID
- Validates org accessibility

**Error Handling**:
- 400: Missing required fields
- 401: Invalid token or unauthorized
- 500: Server error

---

## 4. Job Creation Flow

### Asana Job Creation
1. Validate required fields: `industry`, `workspace_gid`, `user_tokens`, `anthropic_api_key`
2. Create `AsanaClientPool` with user tokens
3. Validate at least one valid client exists
4. Create `ContinuousService` instance
5. Start background thread
6. Return job_id

### Okta Job Creation
1. Validate required fields: `industry`, `org_url`, `user_tokens`, `org_size`, `anthropic_api_key`
2. Validate `org_url` format (must start with `https://`)
3. Validate each token has `org_url` field
4. Create `OktaClientPool` with user tokens
5. Validate at least one valid client exists
6. Create `OktaService` instance
7. Start background thread
8. Return job_id

---

## 5. Cleanup Operations

### Asana Cleanup
**Method**: `ContinuousService.cleanup_asana_data()`

**Deletion Order**:
1. Subtasks (bottom-up)
2. Tasks
3. Projects
4. Custom fields
5. Tags
6. Portfolios

**Response Fields**:
- `deleted_projects`
- `deleted_tasks`
- `deleted_subtasks`
- `total_projects`
- `failed_projects`

### Okta Cleanup
**Method**: `OktaService.cleanup_platform_data()`

**Deletion Order**:
1. App assignments (remove users from apps)
2. Users (deactivate → delete)
3. Groups

**Response Fields**:
- `users_deleted`
- `groups_deleted`
- `assignments_removed`
- `errors`

---

## 6. Job Restart Logic

### Multi-Connection Restart Flow

```python
def restart_running_jobs():
    for job in get_all_jobs():
        if job['status'] in ['running', 'paused']:
            state = load_state(job_id)
            connection_type = state.get('connection_type', 'asana')

            if connection_type == 'asana':
                # Create AsanaClientPool
                # Create ContinuousService
                # Start thread

            elif connection_type == 'okta':
                # Create OktaClientPool
                # Create OktaService
                # Start thread
```

**Features**:
- Automatically detects connection type from state
- Creates appropriate client pool
- Instantiates correct service class
- Restores job state and status
- Handles deletion markers
- Backward compatible with legacy jobs

---

## 7. Testing Approach

### Unit Testing

**Test Categories**:
1. Token validation for both platforms
2. Job creation with different connection types
3. Cleanup operations for both platforms
4. Job restart with mixed connection types
5. Error handling for invalid connection types

**Example Test**:
```python
def test_okta_job_creation():
    config = {
        "connection_type": "okta",
        "org_url": "https://dev-123.okta.com",
        "org_size": "midsize",
        "industry": "technology",
        "user_tokens": [{"name": "admin", "token": "00abc", "org_url": "https://dev-123.okta.com"}],
        "anthropic_api_key": "sk-ant-..."
    }

    response = client.post('/api/jobs/start', json=config)

    assert response.status_code == 200
    assert response.json['connection_type'] == 'okta'
    assert 'job_id' in response.json
```

### Integration Testing

**Test Scenarios**:
1. Create Asana job → verify state → cleanup
2. Create Okta job → verify state → cleanup
3. Create both job types → verify isolation
4. Restart server → verify both job types resume
5. Mixed cleanup → verify correct routing

---

## 8. Example API Calls for Okta Jobs

### Complete Okta Job Workflow

#### Step 1: Validate Token
```bash
curl -X POST http://localhost:5001/api/validate_token \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "token": "00abc123def456ghi789",
    "org_url": "https://dev-123456.okta.com"
  }'
```

#### Step 2: Get Org Information
```bash
curl -X POST http://localhost:5001/api/okta/orgs \
  -H "Content-Type: application/json" \
  -d '{
    "token": "00abc123def456ghi789",
    "org_url": "https://dev-123456.okta.com"
  }'
```

#### Step 3: List Available Apps
```bash
curl -X POST http://localhost:5001/api/okta/apps \
  -H "Content-Type: application/json" \
  -d '{
    "token": "00abc123def456ghi789",
    "org_url": "https://dev-123456.okta.com",
    "limit": 20
  }'
```

#### Step 4: Start Okta Job
```bash
curl -X POST http://localhost:5001/api/jobs/start \
  -H "Content-Type: application/json" \
  -d '{
    "connection_type": "okta",
    "industry": "technology",
    "org_url": "https://dev-123456.okta.com",
    "org_size": "midsize",
    "initial_users": 50,
    "activity_level": "medium",
    "user_tokens": [
      {
        "name": "admin1",
        "token": "00abc123def456ghi789",
        "org_url": "https://dev-123456.okta.com"
      }
    ],
    "anthropic_api_key": "sk-ant-api03-..."
  }'
```

#### Step 5: Monitor Job
```bash
curl http://localhost:5001/api/jobs/job_abc123
```

#### Step 6: Get Activity Log
```bash
curl http://localhost:5001/api/jobs/job_abc123/activity_log?limit=50
```

#### Step 7: Cleanup Job
```bash
curl -X POST http://localhost:5001/api/jobs/job_abc123/cleanup
```

---

## 9. Configuration Validation

### Validation Helper

The server validates configurations before starting jobs:

**Asana Validation**:
- ✓ `connection_type` (optional, defaults to "asana")
- ✓ `industry` (required)
- ✓ `workspace_gid` (required)
- ✓ `user_tokens` (required, array)
- ✓ `anthropic_api_key` (required)
- ✓ At least one valid token

**Okta Validation**:
- ✓ `connection_type: "okta"` (required)
- ✓ `industry` (required)
- ✓ `org_url` (required, must start with `https://`)
- ✓ `org_size` (required: "startup", "midsize", or "enterprise")
- ✓ `user_tokens` (required, array with `org_url` for each token)
- ✓ `anthropic_api_key` (required)
- ✓ At least one valid token

**Error Responses**:
```json
{
  "success": false,
  "error": "Missing required field for Okta: org_size"
}
```

---

## 10. Error Handling

### Connection-Specific Errors

**Okta Errors**:
- 401: Invalid SSWS token
- 404: Org not found / Invalid org_url
- 429: Rate limit exceeded
- 400: Invalid org_url format
- 400: Missing org_url in token config

**Asana Errors**:
- 401: Invalid API token
- 404: Workspace not found
- 429: Rate limit exceeded

**Generic Errors**:
- 400: Unsupported connection type
- 400: Missing required fields
- 500: Server error

---

## 11. Limitations and Future Improvements

### Current Limitations

1. **Okta-Specific**:
   - No support for custom user schema attributes
   - Password reset and MFA enrollment are logged but not executed
   - Limited to SSWS token authentication (no OAuth 2.0)

2. **General**:
   - Single org per Okta job (can't span multiple orgs)
   - No cross-platform operations (can't mix Asana and Okta in one job)

### Future Improvements

1. **New Connection Types**:
   - Salesforce support
   - Google Workspace support
   - Microsoft 365 support

2. **Enhanced Features**:
   - Job templates for common scenarios
   - Scheduled cleanup operations
   - Real-time activity streaming via WebSocket
   - Job cloning across connection types

3. **Okta Enhancements**:
   - OAuth 2.0 authentication
   - Custom user schema support
   - MFA policy management
   - System log event generation

4. **Monitoring**:
   - Prometheus metrics endpoint
   - Health checks per connection type
   - Rate limit monitoring dashboard

---

## 12. Backward Compatibility

### Legacy Job Support

All changes maintain backward compatibility:

✅ **Legacy Asana jobs work without modification**
- Jobs without `connection_type` default to "asana"
- Existing endpoints unchanged for Asana operations
- State manager automatically migrates legacy jobs

✅ **No breaking changes to existing API**
- All Asana endpoints maintain same interface
- New `connection_type` parameter is optional
- Default behavior unchanged

✅ **Automatic migration**
- StateManager adds `connection_type: "asana"` to legacy jobs
- Job restart logic handles both old and new formats

---

## 13. File Changes Summary

### Modified Files

1. **`api_server.py`**
   - Added OktaClientPool and OktaService imports
   - Updated `restart_running_jobs()` for multi-connection support
   - Modified `/api/jobs/start` endpoint
   - Modified `/api/jobs/<job_id>/cleanup` endpoint
   - Modified `/api/validate_token` endpoint
   - Modified `/api/health` endpoint
   - Added `/api/okta/orgs` endpoint
   - Added `/api/okta/apps` endpoint
   - Added `/api/okta/users` endpoint
   - Added `/api/okta/groups` endpoint
   - Updated startup banner

2. **`continuous/connections/okta_connection.py`**
   - Added `suspend_user()` method
   - Added `unsuspend_user()` method
   - Added `remove_user_from_app()` method

### Dependencies

No new dependencies required. All changes use existing libraries:
- Flask (existing)
- OktaConnection (existing)
- OktaService (existing)
- StateManager (existing, already supports multi-connection)

---

## Quick Reference

### Endpoint Summary

| Endpoint | Method | Connection Type | Purpose |
|----------|--------|----------------|---------|
| `/api/jobs/start` | POST | Both | Start new job |
| `/api/jobs` | GET | Both | List all jobs |
| `/api/jobs/<id>` | GET | Both | Get job details |
| `/api/jobs/<id>/cleanup` | POST | Both | Cleanup job data |
| `/api/jobs/<id>/delete` | DELETE | Both | Delete job |
| `/api/validate_token` | POST | Both | Validate API token |
| `/api/workspaces` | POST | Asana | List Asana workspaces |
| `/api/okta/orgs` | POST | Okta | Get Okta org info |
| `/api/okta/apps` | POST | Okta | List Okta apps |
| `/api/okta/users` | POST | Okta | List Okta users |
| `/api/okta/groups` | POST | Okta | List Okta groups |
| `/api/health` | GET | Both | Server health check |

---

## Conclusion

The API server now provides production-ready multi-connection support with:

✅ Clean separation between Asana and Okta logic
✅ Comprehensive error handling
✅ Backward compatibility with legacy jobs
✅ Connection-specific validation
✅ Proper cleanup operations for both platforms
✅ Automatic job restart with correct service type
✅ Full Okta org management capabilities

The implementation follows the "minimal changes" principle while providing a solid foundation for future connection types.
