# Architecture Overview

Visual guide to the Continuous Data Generator architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                           │
│                    (asana_project_creator.html)                  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Point-in-Time│  │  Continuous  │  │  Dashboard   │          │
│  │     Mode     │  │     Mode     │  │  & Logs      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                     Flask API Server                             │
│                      (api_server.py)                             │
│                                                                   │
│  Routes:                                                          │
│  • POST /api/jobs/start      • GET /api/jobs                    │
│  • POST /api/jobs/{id}/stop  • GET /api/jobs/{id}               │
│  • POST /api/jobs/{id}/pause • GET /api/jobs/{id}/activity_log  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ Creates/Manages
┌─────────────────────────────────────────────────────────────────┐
│                    Background Threads                            │
│                   (one per active job)                           │
│                                                                   │
│  Thread 1      Thread 2      Thread 3                           │
│  [Job abc]     [Job def]     [Job xyz]                          │
│     │              │              │                              │
│     ▼              ▼              ▼                              │
│  Service       Service       Service                            │
│  Instance      Instance      Instance                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ Each Service Contains
┌─────────────────────────────────────────────────────────────────┐
│                  ContinuousService Instance                      │
│                   (continuous/service.py)                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Main Async Loop (runs forever)              │    │
│  │                                                          │    │
│  │  while running:                                         │    │
│  │    1. Check if working hours? → Scheduler               │    │
│  │    2. Should generate activity? → Scheduler             │    │
│  │    3. Select activity type → Scheduler                  │    │
│  │    4. Generate content → LLM Generator                  │    │
│  │    5. Execute in Asana → Asana Client                   │    │
│  │    6. Save state → State Manager                        │    │
│  │    7. Sleep 30-90 seconds                               │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Scheduler   │  │LLM Generator │  │State Manager │
│ (scheduler.py)│  │(llm_generator)│  │(state_mgr.py)│
│              │  │              │  │              │
│ • Work hours │  │ • Claude API │  │ • JSON files │
│ • Burst time │  │ • Industries │  │ • Tracking   │
│ • Activity   │  │ • Content    │  │ • Logging    │
│   selection  │  │   types      │  │ • Stats      │
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                  ┌──────────────────┐
                  │  Asana Client    │
                  │ (asana_client.py)│
                  │                  │
                  │ • API wrapper    │
                  │ • Rate limiting  │
                  │ • Multi-user     │
                  │ • Error handling │
                  └──────────────────┘
                            │
                            ▼ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                       External APIs                              │
│                                                                   │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │    Asana API         │      │  Anthropic Claude    │        │
│  │  app.asana.com/api   │      │      API             │        │
│  │                      │      │  (Content Gen)       │        │
│  │ • Create projects    │      │                      │        │
│  │ • Create tasks       │      │ • Project names      │        │
│  │ • Add comments       │      │ • Task names         │        │
│  │ • Update statuses    │      │ • Comments           │        │
│  └──────────────────────┘      └──────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼ Results Visible In
┌─────────────────────────────────────────────────────────────────┐
│                      Asana Workspace                             │
│                    (User's actual workspace)                     │
│                                                                   │
│  Projects │ Tasks │ Comments │ Assignments                      │
│     ↑         ↑        ↑           ↑                             │
│     └─────────┴────────┴───────────┘                             │
│           Real data created                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Generating a Comment

```
1. User starts job via UI
         │
         ▼
2. API server creates ContinuousService
         │
         ▼
3. Service main loop checks: "Should generate activity?"
         │
         ▼
4. Scheduler: "Yes, it's 9:05am (burst time), working hours"
         │
         ▼
5. Scheduler selects activity type based on state
   Example: "COMMENT_START_WORK" (task is in 'new' state)
         │
         ▼
6. Service finds appropriate task from state
   Task: "Update HIPAA documentation" (healthcare industry)
         │
         ▼
7. LLM Generator creates realistic comment
   Input: industry="healthcare", user="Alice", task_name
   Output: "Starting work on this. Will coordinate with
            compliance team to ensure all requirements are met."
         │
         ▼
8. Asana Client makes API call
   POST /tasks/{task_id}/stories
   Body: {"text": "Starting work on this..."}
         │
         ▼
9. Asana API processes request
   → Creates comment in actual workspace
   → Returns success
         │
         ▼
10. State Manager updates job state
    • Mark task as "in_progress"
    • Increment comment counter
    • Log activity
    • Track API usage
    • Save to job_{id}.json
         │
         ▼
11. Service sleeps 30-90 seconds, then repeats
```

## Component Interactions

### Scheduler → Service
```python
# Scheduler determines WHEN and WHAT
should_generate = scheduler.should_generate_activity(current_time)
if should_generate:
    activity_type = scheduler.select_activity_type(state)
    task = scheduler.select_task_for_activity(state, activity_type)
```

### Service → LLM Generator
```python
# Service requests realistic content
if activity_type == COMMENT_START_WORK:
    comment = llm.generate_comment_starting_work(
        user_name=user,
        task_name=task["name"]
    )
```

### Service → Asana Client
```python
# Service executes in Asana
client = client_pool.get_client(user_name)
client.add_comment(task_id, comment_text)
```

### Service → State Manager
```python
# Service persists everything
state_manager.add_comment(job_id, task_id, comment)
state_manager.update_task_status(job_id, task_id, "in_progress")
state_manager.log_activity(job_id, "comment_added", details)
state_manager.increment_api_usage(job_id, "asana", 1)
```

## State File Structure

```json
job_abc123.json:
{
  "job_id": "abc123",
  "status": "running",
  "started_at": "2024-10-15T09:00:00Z",
  "last_activity": "2024-10-15T14:23:00Z",

  "config": {
    "industry": "healthcare",
    "duration_days": 7,
    "activity_level": "medium",
    ...
  },

  "projects": [
    {
      "id": "proj_001",
      "name": "Electronic Health Records Migration",
      "status": "in_progress",
      "created_at": "2024-10-15T09:15:00Z",
      "tasks": [
        {
          "id": "task_001",
          "name": "Update HIPAA documentation",
          "status": "in_progress",
          "assignee": "user_001",
          "assignee_name": "Alice",
          "started_at": "2024-10-15T09:30:00Z",
          "comment_count": 3,
          "last_comment_at": "2024-10-15T14:23:00Z"
        }
      ]
    }
  ],

  "activity_log": [
    {
      "timestamp": "2024-10-15T14:23:00Z",
      "action": "comment_added",
      "details": {
        "task_id": "task_001",
        "user": "Alice",
        "type": "start_work"
      }
    }
  ],

  "stats": {
    "projects_created": 2,
    "tasks_created": 15,
    "comments_added": 47,
    "tasks_completed": 3
  },

  "api_usage": {
    "asana_calls_today": 127,
    "llm_calls_today": 45,
    "llm_tokens_today": 8930
  }
}
```

## Threading Model

```
Main Process (api_server.py)
│
├─ Flask HTTP Server (handles requests)
│
├─ Thread 1: Job abc123
│  └─ Async Event Loop
│     └─ service.run()
│        └─ while loop
│
├─ Thread 2: Job def456
│  └─ Async Event Loop
│     └─ service.run()
│        └─ while loop
│
└─ Thread 3: Job xyz789
   └─ Async Event Loop
      └─ service.run()
         └─ while loop
```

Each job is completely independent:
- Own thread
- Own event loop
- Own state file
- Own API client pool
- Own LLM generator instance

## Error Handling Flow

```
                ┌─────────────────┐
                │ Activity Attempt│
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  API Call       │
                └────────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Success │    │429 Rate │    │401 Auth │
    │         │    │  Limit  │    │  Error  │
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
         ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │Continue │    │Generate │    │Mark     │
    │         │    │OOO msgs │    │Token    │
    │         │    │Pause 1hr│    │Invalid  │
    │         │    │Resume   │    │Continue │
    └─────────┘    └─────────┘    └─────────┘
```

## Security Considerations

```
┌──────────────────────────────────────────────┐
│         Security Boundaries                   │
│                                               │
│  User Input (UI)                             │
│      ↓                                        │
│  [Validation] → API Server                   │
│      ↓                                        │
│  [Environment Variables] → API Keys          │
│      ↓                                        │
│  [HTTPS] → External APIs                     │
│      ↓                                        │
│  [File Permissions] → State Files            │
│                                               │
│  Notes:                                       │
│  • API keys in .env (not committed)          │
│  • State files contain sensitive config      │
│  • CORS wide open (dev only)                 │
│  • No auth on API server (local use)         │
└──────────────────────────────────────────────┘
```

## Scalability Limits

```
Component          | Limit          | Bottleneck
─────────────────────────────────────────────────
Jobs (concurrent)  | ~10-20         | Threading
Tasks per project  | ~100-200       | Asana API
Projects per job   | ~20-30         | State file size
Activities/hour    | ~1000          | Asana rate limit
LLM calls/min      | ~60            | Anthropic rate limit
State file size    | ~10MB          | JSON parsing
```

## Performance Characteristics

```
Operation              | Time        | Notes
─────────────────────────────────────────────────────
LLM generation        | 1-2 sec     | Main bottleneck
Asana API call        | 100-300ms   | Network dependent
State save            | <10ms       | JSON write
Activity loop sleep   | 30-90 sec   | Configurable
Job startup           | 2-5 sec     | Init + first projects
```

## Module Dependencies

```
api_server.py
    ├─ Flask
    ├─ continuous/service.py
    │   ├─ continuous/llm_generator.py
    │   │   └─ anthropic
    │   ├─ continuous/state_manager.py
    │   │   └─ json (stdlib)
    │   ├─ continuous/scheduler.py
    │   │   └─ datetime, random (stdlib)
    │   └─ continuous/asana_client.py
    │       └─ requests
    └─ continuous/state_manager.py
```

All modules are loosely coupled through dependency injection.

---

This architecture provides:
- **Modularity**: Each component has single responsibility
- **Testability**: Components can be tested independently
- **Scalability**: Multiple jobs run independently
- **Reliability**: State persisted, recoverable from crashes
- **Maintainability**: Clear separation of concerns
