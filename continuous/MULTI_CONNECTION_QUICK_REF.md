# StateManager Multi-Connection Quick Reference

## Quick Comparison

### Before (Asana-only)
```python
# Create job - always Asana
config = {
    "workspace_gid": "123456",
    "industry": "healthcare"
}
job_id = manager.create_new_job(config)

# Get all jobs - no filtering
jobs = manager.get_all_jobs()
```

### After (Multi-connection)
```python
# Create Asana job
asana_config = {
    "connection_type": "asana",  # NEW
    "workspace_gid": "123456",
    "industry": "healthcare"
}
asana_job = manager.create_new_job(asana_config)

# Create Okta job
okta_config = {
    "connection_type": "okta",  # NEW
    "domain": "dev-123456.okta.com"
}
okta_job = manager.create_new_job(okta_config)

# Get all jobs - with optional filtering
all_jobs = manager.get_all_jobs()
asana_only = manager.get_all_jobs(connection_type="asana")  # NEW
okta_only = manager.get_jobs_by_connection_type("okta")  # NEW
```

## State Structure Comparison

### Common Fields (All Connection Types)
```json
{
  "job_id": "abc123",
  "connection_type": "asana|okta|...",
  "job_name": "...",
  "status": "running|paused|stopped|completed",
  "created_at": "...",
  "started_at": "...",
  "last_activity": "...",
  "config": {...},
  "activity_log": [...],
  "errors": [...]
}
```

### Asana-Specific Fields
```json
{
  "projects": [],
  "used_scenarios": [],
  "created_object_ids": {...},
  "stats": {
    "projects_created": 0,
    "tasks_created": 0,
    "subtasks_created": 0,
    "comments_added": 0,
    ...
  }
}
```

### Okta-Specific Fields
```json
{
  "users": [],
  "groups": [],
  "app_assignments": [],
  "stats": {
    "users_created": 0,
    "groups_created": 0,
    "app_assignments_created": 0,
    ...
  }
}
```

## Method Changes Summary

| Method | Change | Description |
|--------|--------|-------------|
| `create_new_job()` | Modified | Reads `connection_type` from config, initializes appropriate structure |
| `load_state()` | Modified | Automatically migrates legacy jobs (adds `connection_type: "asana"`) |
| `get_all_jobs()` | Modified | Added optional `connection_type` filter parameter |
| `get_jobs_by_connection_type()` | **NEW** | Convenience method for filtering jobs |
| `get_connection_type()` | **NEW** | Get connection type for a job |
| `validate_state_structure()` | **NEW** | Validate state has required fields |
| `_migrate_legacy_job()` | **NEW** | Internal migration logic |
| All other methods | Unchanged | Work with all connection types |

## Usage Patterns

### Pattern 1: Type-Aware Processing
```python
jobs = manager.get_all_jobs()
for job in jobs:
    state = manager.load_state(job["job_id"])

    if state["connection_type"] == "asana":
        # Process Asana job
        projects = state["projects"]
        for project in projects:
            # ...
    elif state["connection_type"] == "okta":
        # Process Okta job
        users = state["users"]
        for user in users:
            # ...
```

### Pattern 2: Type-Specific Queries
```python
# Only process Asana jobs
asana_jobs = manager.get_jobs_by_connection_type("asana")
for job in asana_jobs:
    manager.add_project(job["job_id"], project_data)

# Only process Okta jobs
okta_jobs = manager.get_jobs_by_connection_type("okta")
for job in okta_jobs:
    # Use Okta-specific operations
    pass
```

### Pattern 3: Connection Type Check
```python
def process_job(job_id):
    conn_type = manager.get_connection_type(job_id)

    if conn_type == "asana":
        return process_asana_job(job_id)
    elif conn_type == "okta":
        return process_okta_job(job_id)
    else:
        raise ValueError(f"Unknown connection type: {conn_type}")
```

## Migration Checklist

When migrating existing code:

- [ ] Update `create_new_job()` calls to include `connection_type` in config
- [ ] Add connection type filtering where needed
- [ ] Use type-aware processing for jobs
- [ ] Update job listing displays to show connection type
- [ ] Test with both new and legacy job files
- [ ] Consider implementing connection-specific helper methods (like Asana's `add_project()`)

## New Job Creation Template

```python
# Define config with connection type
config = {
    "connection_type": "asana|okta|...",  # REQUIRED
    "job_name": "My Job",
    # Connection-specific fields...
}

# Create job
job_id = manager.create_new_job(config)

# Verify
state = manager.load_state(job_id)
assert state["connection_type"] == config["connection_type"]
assert manager.validate_state_structure(state)
```

## Common Pitfalls

### ❌ Don't: Assume all jobs are Asana
```python
jobs = manager.get_all_jobs()
for job in jobs:
    state = manager.load_state(job["job_id"])
    projects = state["projects"]  # Error if Okta job!
```

### ✅ Do: Check connection type first
```python
jobs = manager.get_all_jobs()
for job in jobs:
    state = manager.load_state(job["job_id"])
    if state["connection_type"] == "asana":
        projects = state["projects"]
```

### ❌ Don't: Use Asana-specific methods on non-Asana jobs
```python
manager.add_project(okta_job_id, project)  # Error!
```

### ✅ Do: Use connection-agnostic or type-specific methods
```python
if manager.get_connection_type(job_id) == "asana":
    manager.add_project(job_id, project)
```

## Testing Your Integration

```python
# Test both connection types
def test_integration():
    manager = StateManager("./test")

    # Create jobs
    asana_id = manager.create_new_job({"connection_type": "asana"})
    okta_id = manager.create_new_job({"connection_type": "okta"})

    # Verify types
    assert manager.get_connection_type(asana_id) == "asana"
    assert manager.get_connection_type(okta_id) == "okta"

    # Verify filtering
    assert len(manager.get_jobs_by_connection_type("asana")) == 1
    assert len(manager.get_jobs_by_connection_type("okta")) == 1

    # Verify structures
    asana_state = manager.load_state(asana_id)
    okta_state = manager.load_state(okta_id)
    assert "projects" in asana_state
    assert "users" in okta_state
```

## Key Takeaways

1. **Backward Compatible**: Legacy jobs work without changes
2. **Minimal Code Changes**: Most existing code continues to work
3. **Type-Aware**: Check connection type before accessing connection-specific fields
4. **Extensible**: Easy to add new connection types in the future
5. **Safe Migration**: Automatic and transparent for legacy jobs
