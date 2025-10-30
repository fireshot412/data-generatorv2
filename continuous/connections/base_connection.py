#!/usr/bin/env python3
"""
Base connection class defining the interface all connections must implement.
Provides abstraction for different platform types (Asana, Okta, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import time


class ConnectionError(Exception):
    """Custom exception for connection errors."""
    pass


class RateLimitError(Exception):
    """Custom exception for rate limit errors."""
    pass


class BaseConnection(ABC):
    """
    Abstract base class for platform connections.
    All connection implementations must inherit from this class and implement all abstract methods.
    """

    def __init__(self, api_key: str, user_name: str = "Unknown"):
        """
        Initialize connection.

        Args:
            api_key: API token/key for the platform
            user_name: Name of the user (for logging)
        """
        self.api_key = api_key
        self.user_name = user_name
        self.is_valid = True
        self.last_request_time = None
        self.request_count = 0

    @abstractmethod
    def validate_token(self) -> bool:
        """
        Validate that the API token is valid.

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information (useful for validation).

        Returns:
            User data dictionary
        """
        pass

    # ========== PROJECT/WORKSPACE OPERATIONS ==========

    @abstractmethod
    def create_project(self, workspace_gid: str, name: str, notes: str = "",
                      **kwargs) -> Dict[str, Any]:
        """
        Create a new project/workspace.

        Args:
            workspace_gid: Workspace/organization GID
            name: Project name
            notes: Project description
            **kwargs: Platform-specific parameters

        Returns:
            Created project data
        """
        pass

    @abstractmethod
    def delete_project(self, project_gid: str):
        """
        Delete a project (and all its contents).

        Args:
            project_gid: Project GID to delete
        """
        pass

    @abstractmethod
    def add_members_to_project(self, project_gid: str, member_gids: List[str]):
        """
        Add members to a project.

        Args:
            project_gid: Project GID
            member_gids: List of user GIDs to add
        """
        pass

    @abstractmethod
    def get_workspace_users(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all users in a workspace.

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of users
        """
        pass

    # ========== TASK OPERATIONS ==========

    @abstractmethod
    def create_task(self, project_gid: str, name: str, notes: str = "",
                   assignee: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Create a new task in a project.

        Args:
            project_gid: Project GID
            name: Task name
            notes: Task description
            assignee: Assignee user GID (optional)
            **kwargs: Platform-specific parameters (due_date, start_date, etc.)

        Returns:
            Created task data
        """
        pass

    @abstractmethod
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
            Created subtask data
        """
        pass

    @abstractmethod
    def update_task(self, task_gid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update task fields.

        Args:
            task_gid: Task GID
            updates: Dictionary of fields to update

        Returns:
            Updated task data
        """
        pass

    @abstractmethod
    def complete_task(self, task_gid: str) -> Dict[str, Any]:
        """
        Mark a task as completed.

        Args:
            task_gid: Task GID

        Returns:
            Updated task data
        """
        pass

    @abstractmethod
    def delete_task(self, task_gid: str):
        """
        Delete a task.

        Args:
            task_gid: Task GID to delete
        """
        pass

    @abstractmethod
    def get_task(self, task_gid: str) -> Dict[str, Any]:
        """
        Get task details.

        Args:
            task_gid: Task GID

        Returns:
            Task data
        """
        pass

    @abstractmethod
    def get_project_tasks(self, project_gid: str) -> List[Dict[str, Any]]:
        """
        Get all tasks in a project.

        Args:
            project_gid: Project GID

        Returns:
            List of tasks
        """
        pass

    @abstractmethod
    def get_task_subtasks(self, task_gid: str) -> List[Dict[str, Any]]:
        """
        Get all subtasks for a task.

        Args:
            task_gid: Parent task GID

        Returns:
            List of subtasks
        """
        pass

    @abstractmethod
    def set_task_assignee(self, task_gid: str, assignee_gid: str) -> Dict[str, Any]:
        """
        Change task assignee.

        Args:
            task_gid: Task GID
            assignee_gid: New assignee user GID

        Returns:
            Updated task data
        """
        pass

    # ========== COMMENT OPERATIONS ==========

    @abstractmethod
    def add_comment(self, task_gid: str, text: str) -> Dict[str, Any]:
        """
        Add a comment to a task.

        Args:
            task_gid: Task GID
            text: Comment text

        Returns:
            Created comment data
        """
        pass

    # ========== CUSTOM FIELD OPERATIONS ==========

    @abstractmethod
    def create_custom_field(self, workspace_gid: str, name: str, field_type: str,
                           description: str = "", **kwargs) -> Dict[str, Any]:
        """
        Create a custom field in a workspace.

        Args:
            workspace_gid: Workspace GID
            name: Custom field name
            field_type: Type (text, number, enum, multi_enum, date, people)
            description: Field description
            **kwargs: Additional field-specific parameters

        Returns:
            Created custom field data
        """
        pass

    @abstractmethod
    def add_custom_field_to_project(self, project_gid: str, custom_field_gid: str):
        """
        Add a custom field to a project.

        Args:
            project_gid: Project GID
            custom_field_gid: Custom field GID
        """
        pass

    @abstractmethod
    def get_workspace_custom_fields(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all custom fields in a workspace.

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of custom fields
        """
        pass

    @abstractmethod
    def delete_custom_field(self, custom_field_gid: str):
        """
        Delete a custom field.

        Args:
            custom_field_gid: Custom field GID
        """
        pass

    @abstractmethod
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
        pass

    # ========== SECTION OPERATIONS ==========

    @abstractmethod
    def create_section(self, project_gid: str, name: str) -> Dict[str, Any]:
        """
        Create a section in a project.

        Args:
            project_gid: Project GID
            name: Section name

        Returns:
            Created section data
        """
        pass

    @abstractmethod
    def get_project_sections(self, project_gid: str) -> List[Dict[str, Any]]:
        """
        Get all sections in a project.

        Args:
            project_gid: Project GID

        Returns:
            List of sections
        """
        pass

    @abstractmethod
    def add_task_to_section(self, task_gid: str, section_gid: str):
        """
        Move a task to a specific section.

        Args:
            task_gid: Task GID
            section_gid: Section GID
        """
        pass

    # ========== TAG OPERATIONS ==========

    @abstractmethod
    def create_tag(self, workspace_gid: str, name: str, **kwargs) -> Dict[str, Any]:
        """
        Create a tag in a workspace.

        Args:
            workspace_gid: Workspace GID
            name: Tag name
            **kwargs: Platform-specific parameters (e.g., color)

        Returns:
            Created tag data
        """
        pass

    @abstractmethod
    def add_tag_to_task(self, task_gid: str, tag_gid: str):
        """
        Add a tag to a task.

        Args:
            task_gid: Task GID
            tag_gid: Tag GID
        """
        pass

    @abstractmethod
    def get_workspace_tags(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all tags in a workspace.

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of tags
        """
        pass

    @abstractmethod
    def delete_tag(self, tag_gid: str):
        """
        Delete a tag.

        Args:
            tag_gid: Tag GID
        """
        pass

    # ========== PORTFOLIO OPERATIONS ==========

    @abstractmethod
    def create_portfolio(self, workspace_gid: str, name: str, **kwargs) -> Dict[str, Any]:
        """
        Create a portfolio in a workspace.

        Args:
            workspace_gid: Workspace GID
            name: Portfolio name
            **kwargs: Platform-specific parameters

        Returns:
            Created portfolio data
        """
        pass

    @abstractmethod
    def add_project_to_portfolio(self, portfolio_gid: str, project_gid: str):
        """
        Add a project to a portfolio.

        Args:
            portfolio_gid: Portfolio GID
            project_gid: Project GID
        """
        pass

    @abstractmethod
    def get_workspace_portfolios(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all portfolios in a workspace.

        Args:
            workspace_gid: Workspace GID

        Returns:
            List of portfolios
        """
        pass

    @abstractmethod
    def delete_portfolio(self, portfolio_gid: str):
        """
        Delete a portfolio.

        Args:
            portfolio_gid: Portfolio GID
        """
        pass

    # ========== FOLLOWER OPERATIONS ==========

    @abstractmethod
    def add_followers(self, task_gid: str, followers: List[str]):
        """
        Add followers to a task.

        Args:
            task_gid: Task GID
            followers: List of user GIDs
        """
        pass

    @abstractmethod
    def remove_followers(self, task_gid: str, followers: List[str]):
        """
        Remove followers from a task.

        Args:
            task_gid: Task GID
            followers: List of user GIDs
        """
        pass

    # ========== DEPENDENCY OPERATIONS ==========

    @abstractmethod
    def add_task_dependency(self, task_gid: str, depends_on_gid: str):
        """
        Add a dependency between tasks.

        Args:
            task_gid: Task GID that depends on another
            depends_on_gid: Task GID that must be completed first
        """
        pass

    # ========== MILESTONE OPERATIONS ==========

    @abstractmethod
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
        pass

    # ========== UTILITY METHODS ==========

    def get_request_count(self) -> int:
        """
        Get number of API requests made.

        Returns:
            Request count
        """
        return self.request_count

    def reset_request_count(self):
        """Reset request counter."""
        self.request_count = 0

    def _handle_rate_limiting(self):
        """
        Handle rate limiting with simple delay between requests.
        Subclasses can override for more sophisticated rate limiting.
        """
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < 0.1:  # Minimum 100ms between requests
                time.sleep(0.1 - elapsed)

        self.last_request_time = time.time()
        self.request_count += 1


class BaseClientPool(ABC):
    """
    Abstract base class for connection pool management.
    Handles multiple user tokens for multi-user simulation.
    """

    def __init__(self, user_tokens: Dict[str, str]):
        """
        Initialize client pool.

        Args:
            user_tokens: Dictionary mapping user names to API tokens
        """
        self.clients: Dict[str, BaseConnection] = {}
        self.user_gids: Dict[str, str] = {}  # Cache mapping: user_name -> user_gid

    @abstractmethod
    def get_client(self, user_name: str) -> Optional[BaseConnection]:
        """
        Get client for a specific user.

        Args:
            user_name: User name

        Returns:
            Connection instance or None if not found/invalid
        """
        pass

    @abstractmethod
    def get_random_client(self) -> Optional[BaseConnection]:
        """
        Get a random valid client from the pool.

        Returns:
            Random connection instance or None if no valid clients
        """
        pass

    @abstractmethod
    def get_valid_clients(self) -> List[BaseConnection]:
        """
        Get all valid clients.

        Returns:
            List of valid connection instances
        """
        pass

    @abstractmethod
    def get_valid_user_names(self) -> List[str]:
        """
        Get names of all users with valid tokens.

        Returns:
            List of user names
        """
        pass

    @abstractmethod
    def get_user_gid(self, user_name: str) -> Optional[str]:
        """
        Get the platform user GID for a given user name.

        Args:
            user_name: User name

        Returns:
            User GID or None if not found
        """
        pass

    def get_total_requests(self) -> int:
        """
        Get total API requests across all clients.

        Returns:
            Total request count
        """
        return sum(client.get_request_count() for client in self.clients.values())

    def reset_all_request_counts(self):
        """Reset request counters for all clients."""
        for client in self.clients.values():
            client.reset_request_count()
