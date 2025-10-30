#!/usr/bin/env python3
"""
Asana API Client implementing BaseConnection interface.
Provides all Asana-specific functionality for the data generator.
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from continuous.connections.base_connection import (
    BaseConnection,
    BaseClientPool,
    ConnectionError as BaseConnectionError,
    RateLimitError as BaseRateLimitError
)


# Asana-specific exceptions (for backwards compatibility)
class AsanaAPIError(BaseConnectionError):
    """Custom exception for Asana API errors."""
    pass


class AsanaRateLimitError(BaseRateLimitError):
    """Custom exception for rate limit errors."""
    pass


class AsanaConnection(BaseConnection):
    """Asana API client implementing the BaseConnection interface."""

    BASE_URL = "https://app.asana.com/api/1.0"

    def __init__(self, api_key: str, user_name: str = "Unknown"):
        """
        Initialize Asana connection.

        Args:
            api_key: Asana Personal Access Token
            user_name: Name of the user (for logging)
        """
        super().__init__(api_key, user_name)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make API request with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters

        Returns:
            Response data

        Raises:
            AsanaAPIError: For API errors
            AsanaRateLimitError: For rate limit errors
        """
        url = f"{self.BASE_URL}/{endpoint}"

        # Rate limiting
        self._handle_rate_limiting()

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self._get_headers(), params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self._get_headers(), json=data,
                                       params=params)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self._get_headers(), json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self._get_headers())
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise AsanaRateLimitError(f"Rate limit exceeded. Retry after {retry_after}s")

            # Check for authentication errors
            if response.status_code == 401:
                self.is_valid = False
                raise AsanaAPIError("Invalid or expired API token")

            # Check for other errors
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            raise AsanaAPIError(f"HTTP error: {e}, Response: {response.text}")
        except requests.exceptions.RequestException as e:
            raise AsanaAPIError(f"Request error: {e}")

    def validate_token(self) -> bool:
        """
        Validate that the API token is valid.

        Returns:
            True if valid, False otherwise
        """
        try:
            self.get_user_info()
            self.is_valid = True
            return True
        except AsanaAPIError:
            self.is_valid = False
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information (useful for validation).

        Returns:
            User data
        """
        response = self._make_request("GET", "users/me")
        return response["data"]

    def create_project(self, workspace_gid: str, name: str, notes: str = "",
                      color: str = "light-green", privacy: str = "private") -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            workspace_gid: Workspace GID
            name: Project name
            notes: Project description
            color: Project color
            privacy: Privacy setting ('public_to_workspace', 'private', or 'private_to_team')

        Returns:
            Created project data
        """
        data = {
            "data": {
                "name": name,
                "workspace": workspace_gid,
                "notes": notes,
                "color": color,
                "privacy_setting": privacy
            }
        }

        response = self._make_request("POST", "projects", data=data)
        return response["data"]

    def get_project(self, project_gid: str) -> Dict[str, Any]:
        """
        Get a single project by GID.

        Args:
            project_gid: Project GID

        Returns:
            Project data
        """
        response = self._make_request("GET", f"projects/{project_gid}")
        return response["data"]

    async def wait_until_project_available(self, project_gid: str, max_attempts: int = 10,
                                          initial_delay: float = 0.5) -> bool:
        """
        Poll the API until the project is available or max attempts reached.
        Uses exponential backoff: 0.5s, 1s, 2s, 4s, etc.

        Args:
            project_gid: Project GID to check
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (doubles each attempt)

        Returns:
            True if project became available, False if max attempts reached
        """
        import asyncio
        delay = initial_delay

        for attempt in range(max_attempts):
            try:
                self.get_project(project_gid)
                if attempt > 0:
                    print(f"    ✓ Project became available after {attempt + 1} attempt(s)")
                return True
            except AsanaAPIError as e:
                # If it's a 404 or "not found" error, the project isn't ready yet
                if "404" in str(e) or "Not Found" in str(e) or "Unknown object" in str(e):
                    if attempt < max_attempts - 1:  # Don't sleep on last attempt
                        print(f"    → Project not ready yet, waiting {delay}s... (attempt {attempt + 1}/{max_attempts})")
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, 8)  # Cap at 8 seconds
                    continue
                else:
                    # Different error, re-raise
                    raise

        print(f"    ⚠ Project did not become available after {max_attempts} attempts")
        return False

    def get_task(self, task_gid: str) -> Dict[str, Any]:
        """
        Get a single task by GID.

        Args:
            task_gid: Task GID

        Returns:
            Task data
        """
        params = {"opt_fields": "gid,name,assignee.gid,assignee.name"}
        response = self._make_request("GET", f"tasks/{task_gid}", params=params)
        return response["data"]

    async def wait_until_task_available(self, task_gid: str, max_attempts: int = 15,
                                       initial_delay: float = 0.5) -> bool:
        """
        Poll the API until the task is available or max attempts reached.
        Uses exponential backoff: 0.5s, 1s, 2s, 4s, etc.

        CRITICAL: Tasks need LONGER to propagate than projects in Asana's system.
        We need to wait not just for the task to be readable, but for it to be
        fully ready for child operations (subtasks, comments, etc.)

        Args:
            task_gid: Task GID to check
            max_attempts: Maximum number of retry attempts (increased to 15)
            initial_delay: Initial delay in seconds (doubles each attempt)

        Returns:
            True if task became available, False if max attempts reached
        """
        import asyncio
        delay = initial_delay

        for attempt in range(max_attempts):
            try:
                self.get_task(task_gid)
                # IMPORTANT: Even if we can read the task, give it extra time to stabilize
                # for child object creation (subtasks, comments)
                if attempt == 0:
                    # First successful read - wait 2 more seconds for full propagation
                    print(f"        → Task is readable, waiting 2s for full propagation...")
                    await asyncio.sleep(2)
                if attempt > 0:
                    print(f"        ✓ Task became available after {attempt + 1} attempt(s)")
                return True
            except AsanaAPIError as e:
                # If it's a 404 or "not found" error, the task isn't ready yet
                if "404" in str(e) or "Not Found" in str(e) or "Unknown object" in str(e):
                    if attempt < max_attempts - 1:  # Don't sleep on last attempt
                        print(f"        → Task not ready yet, waiting {delay}s... (attempt {attempt + 1}/{max_attempts})")
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, 5)  # Cap at 5 seconds
                    continue
                else:
                    # Different error, re-raise
                    raise

        print(f"        ⚠ Task did not become available after {max_attempts} attempts")
        return False

    def add_members_to_project(self, project_gid: str, member_gids: List[str]):
        """
        Add members to a project as admins.

        Args:
            project_gid: Project GID
            member_gids: List of user GIDs to add as admin members
        """
        for member_gid in member_gids:
            # First add the member
            data = {
                "data": {
                    "members": [member_gid]
                }
            }
            self._make_request("POST", f"projects/{project_gid}/addMembers", data=data)

            # Then get the project memberships to update the access level
            try:
                memberships = self._make_request("GET", f"projects/{project_gid}/project_memberships")
                for membership in memberships.get("data", []):
                    if membership.get("user", {}).get("gid") == member_gid:
                        membership_gid = membership["gid"]
                        membership_data = {
                            "data": {
                                "access_level": "admin"
                            }
                        }
                        self._make_request("PUT", f"project_memberships/{membership_gid}",
                                         data=membership_data)
                        break
            except Exception as e:
                print(f"      ⚠ Could not set admin role for member {member_gid}: {e}")

    def delete_project(self, project_gid: str):
        """
        Delete a project (and all its tasks/subtasks/comments).

        Args:
            project_gid: Project GID to delete
        """
        self._make_request("DELETE", f"projects/{project_gid}")

    def delete_task(self, task_gid: str):
        """
        Delete a task (moves to trash, recoverable for 30 days).

        Args:
            task_gid: Task GID to delete
        """
        self._make_request("DELETE", f"tasks/{task_gid}")

    def get_task_subtasks(self, task_gid: str) -> List[Dict[str, Any]]:
        """
        Get all subtasks for a task (handles pagination).

        Args:
            task_gid: Parent task GID

        Returns:
            List of all subtasks (across all pages)
        """
        all_subtasks = []
        offset = None

        while True:
            params = {"limit": 100}
            if offset:
                params["offset"] = offset

            response = self._make_request("GET", f"tasks/{task_gid}/subtasks", params=params)
            all_subtasks.extend(response.get("data", []))

            # Check for next page
            next_page = response.get("next_page")
            if next_page and next_page.get("offset"):
                offset = next_page["offset"]
            else:
                break

        return all_subtasks

    def create_task(self, project_gid: str, name: str, notes: str = "",
                   assignee: Optional[str] = None, due_date: Optional[str] = None,
                   start_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new task in a project.

        Args:
            project_gid: Project GID
            name: Task name
            notes: Task description
            assignee: Assignee user GID (optional)
            due_date: Due date in YYYY-MM-DD format (optional)
            start_date: Start date in YYYY-MM-DD format (optional, requires due_date)

        Returns:
            Created task data with assignee object populated
        """
        task_data = {
            "name": name,
            "projects": [project_gid],
            "notes": notes
        }

        if assignee:
            task_data["assignee"] = assignee

        if due_date:
            task_data["due_on"] = due_date

        # IMPORTANT: start_on can only be set if due_on is also set
        # NOTE: start_on is a premium feature - we'll try to set it, but gracefully fall back if not available
        if start_date and due_date:
            task_data["start_on"] = start_date

        data = {"data": task_data}

        # CRITICAL: Request assignee field in response so state_manager can extract it
        params = {"opt_fields": "gid,name,assignee.gid,assignee.name"}

        # Try to create task with start_on, fall back without it if premium feature error
        try:
            response = self._make_request("POST", "tasks", data=data, params=params)
            return response["data"]
        except AsanaAPIError as e:
            # If start_on is a premium feature, retry without it
            if "premium_only_setting_task_start_date" in str(e) and "start_on" in task_data:
                task_data.pop("start_on")
                data = {"data": task_data}
                response = self._make_request("POST", "tasks", data=data, params=params)
                return response["data"]
            else:
                raise

    def create_subtask(self, parent_task_gid: str, name: str, notes: str = "",
                      assignee: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a subtask under a parent task.

        Args:
            parent_task_gid: Parent task GID
            name: Subtask name
            notes: Subtask description
            assignee: Assignee user GID (optional)

        Returns:
            Created subtask data with assignee object populated
        """
        subtask_data = {
            "name": name,
            "notes": notes
        }

        if assignee:
            subtask_data["assignee"] = assignee

        data = {"data": subtask_data}

        # CRITICAL: Request assignee field in response so state_manager can extract it
        params = {"opt_fields": "gid,name,assignee.gid,assignee.name"}

        response = self._make_request("POST", f"tasks/{parent_task_gid}/subtasks", data=data, params=params)
        return response["data"]

    def add_comment(self, task_gid: str, text: str) -> Dict[str, Any]:
        """
        Add a comment to a task.

        Args:
            task_gid: Task GID
            text: Comment text

        Returns:
            Created comment data (story)
        """
        data = {
            "data": {
                "text": text
            }
        }

        response = self._make_request("POST", f"tasks/{task_gid}/stories", data=data)
        return response["data"]

    def update_task(self, task_gid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update task fields.

        Args:
            task_gid: Task GID
            updates: Dictionary of fields to update

        Returns:
            Updated task data
        """
        data = {"data": updates}

        response = self._make_request("PUT", f"tasks/{task_gid}", data=data)
        return response["data"]

    def complete_task(self, task_gid: str) -> Dict[str, Any]:
        """
        Mark a task as completed.

        Args:
            task_gid: Task GID

        Returns:
            Updated task data
        """
        return self.update_task(task_gid, {"completed": True})

    def set_task_assignee(self, task_gid: str, assignee_gid: str) -> Dict[str, Any]:
        """
        Change task assignee.

        Args:
            task_gid: Task GID
            assignee_gid: New assignee user GID

        Returns:
            Updated task data
        """
        return self.update_task(task_gid, {"assignee": assignee_gid})

    def add_task_dependency(self, task_gid: str, depends_on_gid: str):
        """
        Add a dependency between tasks.

        Args:
            task_gid: Task GID that depends on another
            depends_on_gid: Task GID that must be completed first
        """
        data = {
            "data": {
                "task": depends_on_gid
            }
        }

        self._make_request("POST", f"tasks/{task_gid}/addDependencies", data=data)

    def get_task(self, task_gid: str) -> Dict[str, Any]:
        """
        Get task details.

        Args:
            task_gid: Task GID

        Returns:
            Task data
        """
        response = self._make_request("GET", f"tasks/{task_gid}")
        return response["data"]

    def get_project_tasks(self, project_gid: str) -> List[Dict[str, Any]]:
        """
        Get all tasks in a project (handles pagination).

        Args:
            project_gid: Project GID

        Returns:
            List of all tasks (across all pages)
        """
        all_tasks = []
        offset = None

        while True:
            params = {"limit": 100}
            if offset:
                params["offset"] = offset

            response = self._make_request("GET", f"projects/{project_gid}/tasks", params=params)
            all_tasks.extend(response.get("data", []))

            # Check for next page
            next_page = response.get("next_page")
            if next_page and next_page.get("offset"):
                offset = next_page["offset"]
            else:
                break  # No more pages

        return all_tasks

    def get_workspace_users(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all users in a workspace.

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of users
        """
        response = self._make_request("GET", f"workspaces/{workspace_gid}/users")
        return response["data"]

    def get_workspace_projects(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all projects in a workspace (handles pagination).

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of all projects (across all pages)
        """
        all_projects = []
        offset = None

        while True:
            params = {"workspace": workspace_gid, "limit": 100}
            if offset:
                params["offset"] = offset

            response = self._make_request("GET", "projects", params=params)
            all_projects.extend(response.get("data", []))

            # Check for next page
            next_page = response.get("next_page")
            if next_page and next_page.get("offset"):
                offset = next_page["offset"]
            else:
                break

        return all_projects

    def get_user_tasks_in_workspace(self, workspace_gid: str, assignee_gid: str) -> List[Dict[str, Any]]:
        """
        Get all tasks assigned to a specific user in a workspace (handles pagination).
        This finds ALL tasks for a user, including orphaned tasks not in any project.

        Args:
            workspace_gid: Workspace GID
            assignee_gid: User GID

        Returns:
            List of all tasks (across all pages)
        """
        all_tasks = []
        offset = None

        while True:
            params = {
                "workspace": workspace_gid,
                "assignee": assignee_gid,
                "limit": 100,
                "completed_since": "now"  # Include incomplete and recently completed tasks
            }
            if offset:
                params["offset"] = offset

            response = self._make_request("GET", "tasks", params=params)
            all_tasks.extend(response.get("data", []))

            # Check for next page
            next_page = response.get("next_page")
            if next_page and next_page.get("offset"):
                offset = next_page["offset"]
            else:
                break

        return all_tasks

    def create_custom_field_value(self, task_gid: str, custom_field_gid: str,
                                  value: Any) -> Dict[str, Any]:
        """
        Set a custom field value on a task.

        Args:
            task_gid: Task GID
            custom_field_gid: Custom field GID
            value: Value to set

        Returns:
            Updated task data
        """
        data = {
            "data": {
                "custom_fields": {
                    custom_field_gid: value
                }
            }
        }

        response = self._make_request("PUT", f"tasks/{task_gid}", data=data)
        return response["data"]

    # ========== CUSTOM FIELDS ==========

    def create_custom_field(self, workspace_gid: str, name: str, field_type: str,
                           description: str = "", **kwargs) -> Dict[str, Any]:
        """
        Create a custom field in a workspace.

        Args:
            workspace_gid: Workspace GID
            name: Custom field name
            field_type: Type (text, number, enum, multi_enum, date, people)
            description: Field description
            **kwargs: Additional field-specific parameters (e.g., options, precision)

        Returns:
            Created custom field data
        """
        field_data = {
            "name": name,
            "resource_subtype": field_type,
            "workspace": workspace_gid,
            "description": description
        }

        # Add type-specific parameters
        if "precision" in kwargs:
            field_data["precision"] = kwargs["precision"]
        if "enum_options" in kwargs:
            field_data["enum_options"] = kwargs["enum_options"]

        data = {"data": field_data}
        response = self._make_request("POST", "custom_fields", data=data)
        return response["data"]

    def add_custom_field_to_project(self, project_gid: str, custom_field_gid: str):
        """
        Add a custom field to a project.

        Args:
            project_gid: Project GID
            custom_field_gid: Custom field GID
        """
        data = {
            "data": {
                "custom_field": custom_field_gid
            }
        }
        self._make_request("POST", f"projects/{project_gid}/addCustomFieldSetting", data=data)

    def get_workspace_custom_fields(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all custom fields in a workspace (handles pagination).

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of all custom fields (across all pages)
        """
        all_fields = []
        offset = None

        while True:
            params = {"limit": 100}
            if offset:
                params["offset"] = offset

            response = self._make_request("GET", f"workspaces/{workspace_gid}/custom_fields", params=params)
            all_fields.extend(response.get("data", []))

            # Check for next page
            next_page = response.get("next_page")
            if next_page and next_page.get("offset"):
                offset = next_page["offset"]
            else:
                break

        return all_fields

    # ========== SECTIONS ==========

    def create_section(self, project_gid: str, name: str) -> Dict[str, Any]:
        """
        Create a section in a project.

        Args:
            project_gid: Project GID
            name: Section name

        Returns:
            Created section data
        """
        data = {
            "data": {
                "name": name
            }
        }
        response = self._make_request("POST", f"projects/{project_gid}/sections", data=data)
        return response["data"]

    def get_project_sections(self, project_gid: str) -> List[Dict[str, Any]]:
        """
        Get all sections in a project.

        Args:
            project_gid: Project GID

        Returns:
            List of sections
        """
        response = self._make_request("GET", f"projects/{project_gid}/sections")
        return response["data"]

    def add_task_to_section(self, task_gid: str, section_gid: str):
        """
        Move a task to a specific section.

        Args:
            task_gid: Task GID
            section_gid: Section GID
        """
        data = {
            "data": {
                "task": task_gid
            }
        }
        self._make_request("POST", f"sections/{section_gid}/addTask", data=data)

    # ========== TAGS ==========

    def create_tag(self, workspace_gid: str, name: str, color: str = "none") -> Dict[str, Any]:
        """
        Create a tag in a workspace.

        Args:
            workspace_gid: Workspace GID
            name: Tag name
            color: Tag color

        Returns:
            Created tag data
        """
        data = {
            "data": {
                "name": name,
                "color": color,
                "workspace": workspace_gid
            }
        }
        response = self._make_request("POST", "tags", data=data)
        return response["data"]

    def add_tag_to_task(self, task_gid: str, tag_gid: str):
        """
        Add a tag to a task.

        Args:
            task_gid: Task GID
            tag_gid: Tag GID
        """
        data = {
            "data": {
                "tag": tag_gid
            }
        }
        self._make_request("POST", f"tasks/{task_gid}/addTag", data=data)

    def get_workspace_tags(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all tags in a workspace (handles pagination).

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of all tags (across all pages)
        """
        all_tags = []
        offset = None

        while True:
            params = {"limit": 100}
            if offset:
                params["offset"] = offset

            response = self._make_request("GET", f"workspaces/{workspace_gid}/tags", params=params)
            all_tags.extend(response.get("data", []))

            # Check for next page
            next_page = response.get("next_page")
            if next_page and next_page.get("offset"):
                offset = next_page["offset"]
            else:
                break

        return all_tags

    # ========== FOLLOWERS ==========

    def add_followers(self, task_gid: str, followers: List[str]):
        """
        Add followers to a task.

        Args:
            task_gid: Task GID
            followers: List of user GIDs
        """
        data = {
            "data": {
                "followers": followers
            }
        }
        self._make_request("POST", f"tasks/{task_gid}/addFollowers", data=data)

    def remove_followers(self, task_gid: str, followers: List[str]):
        """
        Remove followers from a task.

        Args:
            task_gid: Task GID
            followers: List of user GIDs
        """
        data = {
            "data": {
                "followers": followers
            }
        }
        self._make_request("POST", f"tasks/{task_gid}/removeFollowers", data=data)

    # ========== PORTFOLIOS ==========

    def create_portfolio(self, workspace_gid: str, name: str, color: str = "light-green",
                        public: bool = False) -> Dict[str, Any]:
        """
        Create a portfolio in a workspace.

        Args:
            workspace_gid: Workspace GID
            name: Portfolio name
            color: Portfolio color
            public: Whether portfolio is public

        Returns:
            Created portfolio data
        """
        data = {
            "data": {
                "name": name,
                "workspace": workspace_gid,
                "color": color,
                "public": public
            }
        }
        response = self._make_request("POST", "portfolios", data=data)
        return response["data"]

    def add_project_to_portfolio(self, portfolio_gid: str, project_gid: str):
        """
        Add a project to a portfolio.

        Args:
            portfolio_gid: Portfolio GID
            project_gid: Project GID
        """
        data = {
            "data": {
                "item": project_gid
            }
        }
        self._make_request("POST", f"portfolios/{portfolio_gid}/addItem", data=data)

    def get_portfolio_projects(self, portfolio_gid: str) -> List[Dict[str, Any]]:
        """
        Get all projects in a portfolio.

        Args:
            portfolio_gid: Portfolio GID

        Returns:
            List of projects
        """
        response = self._make_request("GET", f"portfolios/{portfolio_gid}/items")
        return response["data"]

    def get_workspace_portfolios(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all portfolios in a workspace (handles pagination).

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of all portfolios (across all pages)
        """
        # Get current user info to use as owner parameter
        user_info = self.get_user_info()
        user_gid = user_info.get("gid")

        all_portfolios = []
        offset = None

        while True:
            params = {"workspace": workspace_gid, "owner": user_gid, "limit": 100}
            if offset:
                params["offset"] = offset

            response = self._make_request("GET", "portfolios", params=params)
            all_portfolios.extend(response.get("data", []))

            # Check for next page
            next_page = response.get("next_page")
            if next_page and next_page.get("offset"):
                offset = next_page["offset"]
            else:
                break

        return all_portfolios

    def delete_portfolio(self, portfolio_gid: str):
        """
        Delete a portfolio.

        Args:
            portfolio_gid: Portfolio GID
        """
        self._make_request("DELETE", f"portfolios/{portfolio_gid}")

    def delete_custom_field(self, custom_field_gid: str):
        """
        Delete a custom field.

        Args:
            custom_field_gid: Custom field GID
        """
        self._make_request("DELETE", f"custom_fields/{custom_field_gid}")

    def delete_tag(self, tag_gid: str):
        """
        Delete a tag.

        Args:
            tag_gid: Tag GID
        """
        self._make_request("DELETE", f"tags/{tag_gid}")

    # ========== MILESTONES ==========

    def create_milestone(self, project_gid: str, name: str, due_date: str,
                        notes: str = "", assignee: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a milestone task.

        Args:
            project_gid: Project GID
            name: Milestone name
            due_date: Due date in YYYY-MM-DD format
            notes: Milestone description
            assignee: Assignee user GID (optional)

        Returns:
            Created milestone task data
        """
        task_data = {
            "name": name,
            "projects": [project_gid],
            "notes": notes,
            "due_on": due_date,
            "resource_subtype": "milestone"
        }

        if assignee:
            task_data["assignee"] = assignee

        data = {"data": task_data}
        response = self._make_request("POST", "tasks", data=data)
        return response["data"]


class AsanaClientPool(BaseClientPool):
    """Pool of Asana clients for multi-user simulation."""

    def __init__(self, user_tokens: Dict[str, str]):
        """
        Initialize client pool.

        Args:
            user_tokens: Dictionary mapping user names to API tokens
        """
        super().__init__(user_tokens)

        for user_name, api_key in user_tokens.items():
            client = AsanaConnection(api_key, user_name)
            try:
                # Validate token on initialization
                if client.validate_token():
                    self.clients[user_name] = client
                    # CRITICAL: Cache the user's GID for fast lookups
                    user_info = client.get_user_info()
                    self.user_gids[user_name] = user_info.get("gid")
                    print(f"✓ Initialized client for {user_name}")
                else:
                    print(f"✗ Invalid token for {user_name}")
            except Exception as e:
                print(f"✗ Error initializing client for {user_name}: {e}")

    def get_client(self, user_name: str) -> Optional[AsanaConnection]:
        """
        Get client for a specific user.

        Args:
            user_name: User name

        Returns:
            AsanaConnection or None if not found/invalid
        """
        client = self.clients.get(user_name)
        if client and not client.is_valid:
            print(f"⚠ Token for {user_name} is no longer valid")
            return None
        return client

    def get_random_client(self) -> Optional[AsanaConnection]:
        """
        Get a random valid client from the pool.

        Returns:
            Random AsanaConnection or None if no valid clients
        """
        import random
        valid_clients = [c for c in self.clients.values() if c.is_valid]
        return random.choice(valid_clients) if valid_clients else None

    def get_valid_clients(self) -> List[AsanaConnection]:
        """
        Get all valid clients.

        Returns:
            List of valid AsanaConnections
        """
        return [c for c in self.clients.values() if c.is_valid]

    def get_valid_user_names(self) -> List[str]:
        """
        Get names of all users with valid tokens.

        Returns:
            List of user names
        """
        return [name for name, client in self.clients.items() if client.is_valid]

    def get_user_gid(self, user_name: str) -> Optional[str]:
        """
        Get the Asana user GID for a given user name.

        Args:
            user_name: User name

        Returns:
            User GID or None if not found
        """
        return self.user_gids.get(user_name)


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python asana_connection.py <API_KEY>")
        sys.exit(1)

    # Test single client
    client = AsanaConnection(sys.argv[1], "Test User")

    print("Testing Asana Connection...")

    # Validate token
    if client.validate_token():
        print("✓ Token is valid")

        # Get user info
        user = client.get_user_info()
        print(f"✓ User: {user['name']} ({user['email']})")
    else:
        print("✗ Token is invalid")
