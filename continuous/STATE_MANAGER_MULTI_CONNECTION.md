# StateManager Multi-Connection Support

## Overview

The `StateManager` class has been updated to support multiple connection types (Asana, Okta, and future platforms) while maintaining full backward compatibility with existing Asana-only job files.

## Summary of Changes

### 1. Connection Type Field
- **New field**: `connection_type` added to all job state files
- **Values**: `"asana"`, `"okta"`, or custom values for future platforms
- **Default**: Jobs without this field are automatically migrated as "asana" (legacy support)

### 2. Connection-Specific Data Structures

#### Asana Jobs (`connection_type: "asana"`)
```json
{
  "connection_type": "asana",
  "projects": [],
  "used_scenarios": [],
  "created_object_ids": {
    "portfolios": [],
    "custom_fields": [],
    "tags": [],
    "sections": []
  },
  "stats": {
    "projects_created": 0,
    "tasks_created": 0,
    "subtasks_created": 0,
    "comments_added": 0,
    "task_state_changes": 0,
    "tasks_completed": 0,
    "custom_fields_created": 0,
    "sections_created": 0,
    "tags_created": 0,
    "portfolios_created": 0,
    "errors": 0
  },
  "api_usage": {
    "asana_calls_today": 0,
    "llm_calls_today": 0,
    "llm_tokens_today": 0,
    "last_reset": "2025-10-30T00:00:00+00:00"
  }
}
```

#### Okta Jobs (`connection_type: "okta"`)
```json
{
  "connection_type": "okta",
  "users": [],
  "groups": [],
  "app_assignments": [],
  "stats": {
    "users_created": 0,
    "groups_created": 0,
    "app_assignments_created": 0,
    "user_group_assignments": 0,
    "user_activations": 0,
    "user_deactivations": 0,
    "errors": 0
  },
  "api_usage": {
    "okta_calls_today": 0,
    "llm_calls_today": 0,
    "llm_tokens_today": 0,
    "last_reset": "2025-10-30T00:00:00+00:00"
  }
}
```

### 3. Common State Structure

All connection types share these common fields:
```json
{
  "job_id": "abc123",
  "connection_type": "asana|okta|...",
  "job_name": "My Job",
  "status": "running|paused|stopped|completed",
  "created_at": "2025-10-30T00:00:00+00:00",
  "started_at": "2025-10-30T00:00:00+00:00",
  "last_activity": "2025-10-30T00:00:00+00:00",
  "last_saved": "2025-10-30T00:00:00+00:00",
  "config": {...},
  "activity_log": [...],
  "errors": [...]
}
```

## Updated Methods

### `create_new_job(config: Dict[str, Any]) -> str`
- **Change**: Extracts `connection_type` from config
- **Default**: Defaults to "asana" if not specified
- **Behavior**: Initializes appropriate data structures based on connection type

**Example**:
```python
# Asana job
asana_config = {
    "connection_type": "asana",
    "workspace_gid": "123456",
    "industry": "healthcare"
}
asana_job_id = manager.create_new_job(asana_config)

# Okta job
okta_config = {
    "connection_type": "okta",
    "domain": "dev-123456.okta.com",
    "job_name": "User Provisioning"
}
okta_job_id = manager.create_new_job(okta_config)
```

### `load_state(job_id: str) -> Optional[Dict[str, Any]]`
- **Change**: Automatically migrates legacy jobs
- **Behavior**: Calls `_migrate_legacy_job()` to add connection_type to old files
- **Backward Compatibility**: Legacy jobs without connection_type get "asana" added

### `get_all_jobs(connection_type: Optional[str] = None) -> List[Dict[str, Any]]`
- **Change**: Added optional `connection_type` parameter for filtering
- **Behavior**: Returns all jobs or filters by connection type
- **Returns**: Job summaries now include `connection_type` field

**Example**:
```python
# Get all jobs
all_jobs = manager.get_all_jobs()

# Get only Asana jobs
asana_jobs = manager.get_all_jobs(connection_type="asana")

# Get only Okta jobs
okta_jobs = manager.get_all_jobs(connection_type="okta")
```

## New Helper Methods

### `get_jobs_by_connection_type(connection_type: str) -> List[Dict[str, Any]]`
Convenience method for filtering jobs by connection type.

**Example**:
```python
asana_jobs = manager.get_jobs_by_connection_type("asana")
okta_jobs = manager.get_jobs_by_connection_type("okta")
```

### `get_connection_type(job_id: str) -> Optional[str]`
Get the connection type for a specific job.

**Example**:
```python
conn_type = manager.get_connection_type("abc123")
if conn_type == "asana":
    # Handle Asana job
elif conn_type == "okta":
    # Handle Okta job
```

### `validate_state_structure(state: Dict[str, Any]) -> bool`
Validate that a state dictionary has all required fields for its connection type.

**Example**:
```python
state = manager.load_state(job_id)
if manager.validate_state_structure(state):
    # State is valid
    pass
```

## Migration Strategy

### Automatic Migration
Legacy jobs (without `connection_type`) are automatically migrated when loaded:

1. **Detection**: `load_state()` checks if `connection_type` exists
2. **Migration**: `_migrate_legacy_job()` adds `connection_type: "asana"`
3. **In-Memory Only**: Migration happens in-memory; file is not modified until next save
4. **Transparent**: No user intervention required

### Manual Migration
To permanently migrate all legacy jobs:

```python
manager = StateManager("./continuous")

# Get all jobs (triggers in-memory migration)
jobs = manager.get_all_jobs()

# Re-save each job to persist the migration
for job in jobs:
    state = manager.load_state(job["job_id"])
    manager.save_state(job["job_id"], state)
```

## Backward Compatibility

### Guarantees
1. **Existing Asana jobs work unchanged**: Jobs created before this update continue to function
2. **No breaking changes**: All existing methods maintain their original behavior
3. **Graceful degradation**: Missing `connection_type` defaults to "asana"
4. **Data preservation**: No data loss during migration

### Testing Legacy Jobs
```python
# Simulate a legacy job file (no connection_type)
legacy_state = {
    "job_id": "legacy123",
    "status": "running",
    "config": {"industry": "finance"},
    "projects": [],
    "stats": {"projects_created": 5}
}

# Migration happens automatically
migrated = manager._migrate_legacy_job(legacy_state)
assert migrated["connection_type"] == "asana"
```

## Activity Log Format

The activity log is connection-agnostic and works for all types:

```json
{
  "timestamp": "2025-10-30T00:00:00+00:00",
  "action": "create_project|create_user|create_group|...",
  "details": {...}
}
```

**Asana Activities**:
- `create_project`, `create_task`, `add_comment`, `update_task_status`

**Okta Activities**:
- `create_user`, `create_group`, `assign_app`, `activate_user`, `deactivate_user`

## Connection-Agnostic Methods

These methods work unchanged for all connection types:
- `save_state()` - Saves any state structure
- `load_state()` - Loads any state structure (with migration)
- `update_last_activity()` - Updates timestamp
- `update_job_status()` - Updates job status
- `log_activity()` - Logs activities
- `log_error()` - Logs errors
- `mark_for_deletion()` - Marks jobs for deletion
- `delete_job()` - Deletes job files

## Connection-Specific Methods

These methods are Asana-specific and should only be used with Asana jobs:
- `add_project()`
- `add_task()`
- `update_task_status()`
- `add_comment()`
- `get_task_by_id()`
- `get_tasks_by_status()`

**Important**: Future generators (Okta, etc.) should implement their own helper methods similar to these Asana-specific ones.

## Integration Examples

### Creating Jobs

```python
manager = StateManager("./continuous")

# Asana job
asana_config = {
    "connection_type": "asana",
    "workspace_gid": "123456",
    "workspace_name": "My Workspace",
    "industry": "healthcare"
}
asana_job = manager.create_new_job(asana_config)

# Okta job
okta_config = {
    "connection_type": "okta",
    "domain": "dev-123456.okta.com",
    "job_name": "User Onboarding"
}
okta_job = manager.create_new_job(okta_config)
```

### Querying Jobs

```python
# All jobs
all_jobs = manager.get_all_jobs()
print(f"Total jobs: {len(all_jobs)}")

# Filter by type
asana_jobs = manager.get_jobs_by_connection_type("asana")
okta_jobs = manager.get_jobs_by_connection_type("okta")

# Check connection type
job_type = manager.get_connection_type("abc123")
if job_type == "asana":
    # Use Asana-specific methods
    manager.add_project(job_id, project_data)
elif job_type == "okta":
    # Use Okta-specific methods
    # (to be implemented in Okta generator)
    pass
```

### Working with State

```python
# Load state (automatic migration for legacy jobs)
state = manager.load_state(job_id)

# Validate state structure
if manager.validate_state_structure(state):
    # Safe to proceed
    pass

# Access connection-specific data
if state["connection_type"] == "asana":
    projects = state["projects"]
    stats = state["stats"]["projects_created"]
elif state["connection_type"] == "okta":
    users = state["users"]
    stats = state["stats"]["users_created"]
```

## Testing

### Unit Tests

```python
import pytest
from continuous.state_manager import StateManager

def test_asana_job_creation():
    manager = StateManager("./test_states")
    config = {"connection_type": "asana", "workspace_gid": "123"}
    job_id = manager.create_new_job(config)

    state = manager.load_state(job_id)
    assert state["connection_type"] == "asana"
    assert "projects" in state
    assert "stats" in state

def test_okta_job_creation():
    manager = StateManager("./test_states")
    config = {"connection_type": "okta", "domain": "dev.okta.com"}
    job_id = manager.create_new_job(config)

    state = manager.load_state(job_id)
    assert state["connection_type"] == "okta"
    assert "users" in state
    assert "groups" in state

def test_legacy_migration():
    manager = StateManager("./test_states")
    legacy_state = {
        "job_id": "test123",
        "status": "running",
        "config": {},
        "projects": []
    }

    migrated = manager._migrate_legacy_job(legacy_state)
    assert migrated["connection_type"] == "asana"

def test_filtering_by_connection_type():
    manager = StateManager("./test_states")

    # Create jobs of different types
    manager.create_new_job({"connection_type": "asana"})
    manager.create_new_job({"connection_type": "okta"})

    asana_jobs = manager.get_jobs_by_connection_type("asana")
    okta_jobs = manager.get_jobs_by_connection_type("okta")

    assert len(asana_jobs) == 1
    assert len(okta_jobs) == 1
```

### Integration Tests

Run the example code:
```bash
python3 continuous/state_manager.py
```

Expected output shows:
- Asana job creation with projects/tasks
- Okta job creation with users/groups
- Filtering by connection type
- Legacy migration
- Validation

## Future Extensions

To add support for a new connection type:

1. **Update `create_new_job()`**: Add new connection type case
2. **Define state structure**: Add connection-specific fields
3. **Define statistics**: Add connection-specific stats
4. **Update validation**: Add validation rules in `validate_state_structure()`
5. **Create helper methods**: Add connection-specific helper methods (like `add_project()` for Asana)

**Example for Salesforce**:
```python
elif connection_type == "salesforce":
    state.update({
        "accounts": [],
        "contacts": [],
        "opportunities": [],
        "stats": {
            "accounts_created": 0,
            "contacts_created": 0,
            "opportunities_created": 0,
            "errors": 0
        },
        "api_usage": {
            "salesforce_calls_today": 0,
            "llm_calls_today": 0,
            "llm_tokens_today": 0,
            "last_reset": now
        }
    })
```

## Performance Considerations

- **No performance impact**: Changes are minimal and don't affect I/O operations
- **Migration overhead**: Negligible (single field addition in-memory)
- **Filtering**: O(n) scan with optional early exit
- **File format**: JSON remains human-readable and debuggable

## Conclusion

The StateManager now supports multiple connection types with:
- ✅ Full backward compatibility
- ✅ Automatic migration
- ✅ Connection-specific data structures
- ✅ Connection-agnostic core methods
- ✅ Helper methods for filtering and validation
- ✅ Extensible design for future platforms
