# Changelog

All notable changes to the Asana Data Generator project.

## [2.0.0] - Continuous Mode Release - 2024-10-15

### Major Features Added

#### Continuous Generation Mode
- Complete background service for ongoing data generation
- Runs indefinitely or for specified duration (days/weeks/months)
- Simulates realistic team activity patterns over time

#### Industry Theme Support
- 10 industry themes with contextually relevant content
- Finance, Healthcare, Manufacturing, Travel, Technology, Retail, Education, Government, Energy, Media
- AI-powered content generation using Claude API
- Applies to both point-in-time and continuous modes

#### Realistic Work Patterns
- **Working Hours Simulation**: US Workforce (9am-6pm PT) or Global (24-hour)
- **Burst Time Patterns**: Activity peaks at 9am, 1pm, 4pm
- **Weekend Handling**: Rare activity on weekends for urgent items
- **Configurable Activity Levels**: Low, Medium, High
- **Burst vs Steady Slider**: Control concentration of activity

#### Task Lifecycle Simulation
- Tasks progress through realistic states:
  - New → In Progress → (possibly Blocked) → Completed
- Blocked tasks with realistic blockers (15% default)
- Automatic unblocking after average duration (2 days default)
- Task dependencies support
- Realistic completion rates (20% per week default)

#### Multi-User Collaboration
- Distributed activities across multiple users
- Back-and-forth conversations between users
- Task reassignments
- Out-of-office messages
- Token validation and management

#### AI-Powered Content Generation
- Claude API integration for realistic content
- Project names contextual to industry
- Task names and descriptions
- Comment variations:
  - Starting work
  - Progress updates
  - Blockers and unblocking
  - Completion announcements
  - Conversations
  - Out-of-office notifications
- Usage tracking for cost management

### New Modules

#### `continuous/llm_generator.py` (370 lines)
- LLMGenerator class with Claude API integration
- 10+ content generation methods
- Industry-specific context
- API usage tracking
- Fallback content for failures

#### `continuous/state_manager.py` (350 lines)
- StateManager class for JSON-based persistence
- Job state tracking
- Activity logging
- API usage counters
- Error tracking
- Support for multiple concurrent jobs

#### `continuous/scheduler.py` (400 lines)
- ActivityScheduler class
- Working hours detection
- Burst time identification
- Activity type selection based on state
- Task lifecycle management
- Statistics tracking

#### `continuous/asana_client.py` (370 lines)
- AsanaClient wrapper class
- AsanaClientPool for multi-user management
- Rate limiting protection
- Token validation
- Error handling (401, 429, etc.)
- Request counting

#### `continuous/service.py` (600 lines)
- ContinuousService orchestrator
- Async main loop
- Activity generation pipeline
- Error recovery
- State persistence
- Pause/resume/stop controls

### API Server

#### `api_server.py` (370 lines)
- Flask REST API for UI integration
- Job management endpoints (start, stop, pause, resume, delete)
- Job listing and details
- Activity log viewing
- Token validation
- Workspace fetching
- Health check endpoint
- Threading for concurrent jobs

### Documentation

#### New Files
- `README.md` (500+ lines) - Comprehensive user guide
- `QUICKSTART.md` - 5-minute getting started guide
- `IMPLEMENTATION_SUMMARY.md` - Technical overview for developers
- `CHANGELOG.md` - This file
- `.env.example` - Environment variables template
- `example_config.json` - Configuration reference

### Configuration

#### New Settings
- `industry` - Industry theme selection
- `duration_days` - Job duration or "indefinite"
- `initial_projects` - Number of starting projects
- `activity_level` - Low, Medium, High
- `working_hours` - US Workforce or Global
- `burst_factor` - Bursty vs steady (0.0-1.0)
- `comment_frequency` - Comments per task per day
- `task_completion_rate` - % completed per week
- `blocked_task_frequency` - % of tasks blocked
- `blocked_task_duration` - Average blocked days
- `new_project_frequency_days` - Days between new projects

### Dependencies Added
- `anthropic>=0.18.0` - Claude API client
- `Flask>=3.0.0` - Web framework
- `flask-cors>=4.0.0` - CORS support
- `asyncio-extras>=1.3.2` - Async utilities
- `python-dotenv>=1.0.0` - Environment variables

### Error Handling Improvements
- Graceful rate limit handling with auto-pause/resume
- Invalid token detection with dashboard warnings
- Service interruption recovery
- LLM API failure fallbacks
- Comprehensive error logging

### Monitoring & Observability
- Real-time job status dashboard
- Activity log viewer with pagination
- API usage tracking (Asana & LLM)
- Statistics counters
- Error log with timestamps
- Health check endpoint

### State Persistence
- JSON-based state files (`job_{id}.json`)
- Automatic saving after each activity
- Resume capability after crashes
- Activity history (last 1000 entries)
- Error history (last 100 entries)
- API usage tracking with daily reset

---

## [1.0.0] - Initial Release

### Features
- Point-in-time project creation
- CLI interface for project setup
- Multi-user API token management
- Task and subtask creation
- Comment generation
- Workspace selection
- User permission verification
- Public/private project support

### Core Files
- `create_asana_project.py` - CLI tool
- `asana_project_creator.html` - Web UI (basic)

---

## Roadmap / Future Enhancements

### Planned for Future Releases

#### v2.1.0 - Enhanced UI
- [ ] Visual dashboard with charts
- [ ] Timeline view of activities
- [ ] Real-time activity feed
- [ ] Configuration templates (save/load)
- [ ] Bulk job operations

#### v2.2.0 - Advanced Features
- [ ] LLM response caching for cost reduction
- [ ] Per-user custom work schedules
- [ ] Email/Slack notifications
- [ ] Webhook integrations
- [ ] Export to CSV/Excel
- [ ] Analytics and reports

#### v2.3.0 - Multi-Platform
- [ ] Jira support
- [ ] Monday.com support
- [ ] Trello support
- [ ] Generic REST API connector

#### v3.0.0 - Enterprise Features
- [ ] Database backend (PostgreSQL)
- [ ] Multi-tenancy support
- [ ] User authentication
- [ ] Team management
- [ ] Usage quotas
- [ ] Advanced scheduling
- [ ] Custom LLM prompts

---

## Migration Guide

### From v1.0.0 to v2.0.0

**No breaking changes** - all existing functionality preserved.

**New Setup Required**:
1. Install new dependencies: `pip install -r requirements.txt`
2. Add Anthropic API key to `.env` file
3. Run API server for continuous mode: `python api_server.py`

**Existing Files**:
- `create_asana_project.py` - Still works as before
- `asana_project_creator.html` - Will be enhanced in future update

**New Workflow**:
- Old: Run CLI tool → Creates data once
- New: Start API server → Launch continuous jobs → Data generates over time

Both workflows are supported simultaneously.

---

## Contributors

- Implementation: Asana Data Generator Team
- AI Integration: Claude (Anthropic)
- Testing: Community contributors

## Support

For issues, questions, or feature requests, please refer to the documentation:
- `README.md` - User guide
- `QUICKSTART.md` - Getting started
- `IMPLEMENTATION_SUMMARY.md` - Technical details
