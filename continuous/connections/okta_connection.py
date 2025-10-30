#!/usr/bin/env python3
"""
Okta API Client implementing BaseConnection interface.
Provides Okta-specific functionality for user, group, and application management.

This implementation maps Okta concepts to the BaseConnection abstraction:
- Groups (Okta) -> Projects (BaseConnection)
- Users (Okta) -> Tasks (BaseConnection)
- Apps (Okta) -> Custom Okta functionality

API Reference: https://developer.okta.com/docs/reference/core-okta-api/
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

from continuous.connections.base_connection import (
    BaseConnection,
    BaseClientPool,
    ConnectionError as BaseConnectionError,
    RateLimitError as BaseRateLimitError
)


# Okta-specific exceptions (for backwards compatibility)
class OktaAPIError(BaseConnectionError):
    """Custom exception for Okta API errors."""
    pass


class OktaRateLimitError(BaseRateLimitError):
    """Custom exception for rate limit errors."""
    pass


class OktaConnection(BaseConnection):
    """
    Okta API client implementing the BaseConnection interface.

    Supports CRUD operations for:
    - Users: Create, update, deactivate, activate, list
    - Groups: Create, delete, add/remove members, list
    - Apps: List, assign users/groups to apps, get assignments

    Authentication:
        Uses SSWS (Single Sign-On Web Services) token authentication.
        Header format: Authorization: SSWS {token}

    Rate Limits:
        Okta enforces org-wide and endpoint-specific rate limits.
        This client tracks X-Rate-Limit-* headers and logs warnings.

    Pagination:
        Okta uses Link headers for pagination (rel="next", rel="prev").
        List methods support limit parameter (default 200, max depends on endpoint).

    Example:
        >>> client = OktaConnection(token="00abc...", org_url="https://dev-123.okta.com")
        >>> if client.validate_token():
        ...     user = client.create_user({
        ...         "firstName": "John",
        ...         "lastName": "Doe",
        ...         "email": "john.doe@example.com",
        ...         "login": "john.doe@example.com"
        ...     })
        ...     print(f"Created user: {user['id']}")
    """

    def __init__(self, token: str, org_url: str, user_name: str = "Unknown"):
        """
        Initialize Okta connection.

        Args:
            token: Okta SSWS API token
            org_url: Okta organization URL (e.g., https://dev-123456.okta.com)
            user_name: Name of the user (for logging)
        """
        super().__init__(token, user_name)
        self.org_url = org_url.rstrip('/')  # Remove trailing slash if present
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.logger = logging.getLogger(f"OktaConnection.{user_name}")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with SSWS token authorization.

        Returns:
            Headers dictionary with Authorization and Content-Type
        """
        return {
            "Authorization": f"SSWS {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make API request with error handling and rate limit tracking.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL, e.g., "users" or "groups/{id}")
            data: Request body data (for POST/PUT)
            params: Query parameters

        Returns:
            Response data (JSON decoded)

        Raises:
            OktaAPIError: For API errors (401, 404, etc.)
            OktaRateLimitError: For rate limit errors (429)
        """
        # Ensure endpoint doesn't start with /
        endpoint = endpoint.lstrip('/')
        url = f"{self.org_url}/api/v1/{endpoint}"

        # Rate limiting
        self._handle_rate_limiting()

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self._get_headers(), params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self._get_headers(), json=data, params=params)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self._get_headers(), json=data, params=params)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self._get_headers(), params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Track rate limit headers
            self._track_rate_limits(response)

            # Check for rate limiting (429)
            if response.status_code == 429:
                retry_after = int(response.headers.get("X-Rate-Limit-Reset", 60))
                raise OktaRateLimitError(
                    f"Rate limit exceeded. Reset at epoch: {retry_after}"
                )

            # Check for authentication errors (401)
            if response.status_code == 401:
                self.is_valid = False
                raise OktaAPIError("Invalid or expired SSWS token")

            # Check for not found (404)
            if response.status_code == 404:
                raise OktaAPIError(f"Resource not found: {endpoint}")

            # Check for other errors
            response.raise_for_status()

            # Return empty dict for 204 No Content (successful DELETE)
            if response.status_code == 204:
                return {}

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e}"
            try:
                error_detail = response.json()
                error_msg += f", Details: {error_detail}"
            except:
                error_msg += f", Response: {response.text}"
            raise OktaAPIError(error_msg)
        except requests.exceptions.RequestException as e:
            raise OktaAPIError(f"Request error: {e}")

    def _track_rate_limits(self, response: requests.Response):
        """
        Track rate limit headers from Okta responses.

        Logs warnings when approaching rate limits (< 10% remaining).

        Args:
            response: HTTP response object
        """
        limit = response.headers.get("X-Rate-Limit-Limit")
        remaining = response.headers.get("X-Rate-Limit-Remaining")
        reset = response.headers.get("X-Rate-Limit-Reset")

        if remaining:
            self.rate_limit_remaining = int(remaining)
        if reset:
            self.rate_limit_reset = int(reset)

        # Warn if approaching rate limit
        if limit and remaining:
            limit_int = int(limit)
            remaining_int = int(remaining)
            if remaining_int < (limit_int * 0.1):  # Less than 10% remaining
                self.logger.warning(
                    f"Rate limit warning: {remaining_int}/{limit_int} requests remaining. "
                    f"Resets at epoch {reset}"
                )

    def validate_token(self) -> bool:
        """
        Validate that the SSWS token is valid by calling /api/v1/users/me.

        Returns:
            True if valid, False otherwise
        """
        try:
            self.get_user_info()
            self.is_valid = True
            return True
        except OktaAPIError:
            self.is_valid = False
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current authenticated user information.

        Calls: GET /api/v1/users/me

        Returns:
            User data dictionary with fields:
                - id: User ID
                - status: User status (ACTIVE, DEPROVISIONED, etc.)
                - profile: User profile (firstName, lastName, email, login, etc.)
        """
        return self._make_request("GET", "users/me")

    # ========== OKTA USERS API ==========

    def create_user(self, profile: Dict[str, Any], activate: bool = True,
                   credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new user in Okta.

        Calls: POST /api/v1/users

        Args:
            profile: User profile dictionary with required fields:
                - firstName: User's first name
                - lastName: User's last name
                - email: User's email address
                - login: User's login (usually same as email)
                Optional fields:
                - mobilePhone, secondEmail, etc.
            activate: Whether to activate user immediately (default True)
            credentials: Optional credentials dict with password/recovery_question

        Returns:
            Created user data dictionary with 'id' field

        Example:
            >>> user = client.create_user({
            ...     "firstName": "John",
            ...     "lastName": "Doe",
            ...     "email": "john.doe@example.com",
            ...     "login": "john.doe@example.com"
            ... })
        """
        data = {"profile": profile}

        if credentials:
            data["credentials"] = credentials

        params = {"activate": str(activate).lower()}

        return self._make_request("POST", "users", data=data, params=params)

    def update_user(self, user_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile attributes.

        Calls: POST /api/v1/users/{userId}

        Args:
            user_id: Okta user ID
            profile: Dictionary of profile fields to update

        Returns:
            Updated user data dictionary
        """
        data = {"profile": profile}
        return self._make_request("POST", f"users/{user_id}", data=data)

    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user (transitions to DEPROVISIONED status).
        User must be in STAGED or PROVISIONED status.

        Calls: POST /api/v1/users/{userId}/lifecycle/deactivate

        Args:
            user_id: Okta user ID

        Returns:
            True if successful
        """
        try:
            self._make_request("POST", f"users/{user_id}/lifecycle/deactivate")
            return True
        except OktaAPIError:
            return False

    def activate_user(self, user_id: str, send_email: bool = False) -> bool:
        """
        Activate a user (transitions to ACTIVE status).

        Calls: POST /api/v1/users/{userId}/lifecycle/activate

        Args:
            user_id: Okta user ID
            send_email: Whether to send activation email to user

        Returns:
            True if successful
        """
        try:
            params = {"sendEmail": str(send_email).lower()}
            self._make_request("POST", f"users/{user_id}/lifecycle/activate", params=params)
            return True
        except OktaAPIError:
            return False

    def delete_user(self, user_id: str, send_email: bool = False) -> bool:
        """
        Delete a user permanently.
        User must be deactivated first.

        Calls: DELETE /api/v1/users/{userId}

        Args:
            user_id: Okta user ID
            send_email: Whether to send notification email

        Returns:
            True if successful
        """
        try:
            params = {"sendEmail": str(send_email).lower()}
            self._make_request("DELETE", f"users/{user_id}", params=params)
            return True
        except OktaAPIError:
            return False

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user details by ID.

        Calls: GET /api/v1/users/{userId}

        Args:
            user_id: Okta user ID

        Returns:
            User data dictionary
        """
        return self._make_request("GET", f"users/{user_id}")

    def list_users(self, limit: int = 200, query: Optional[str] = None,
                  filter_expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List users in the organization.

        Calls: GET /api/v1/users

        Note: This method fetches only the first page. For full pagination,
        use the Link header from _make_request response.

        Args:
            limit: Number of results per page (default 200, max 200)
            query: Search query for firstName, lastName, or email
            filter_expr: Okta filter expression (e.g., 'status eq "ACTIVE"')

        Returns:
            List of user dictionaries

        Example:
            >>> users = client.list_users(limit=50, filter_expr='status eq "ACTIVE"')
        """
        params = {"limit": limit}

        if query:
            params["q"] = query
        if filter_expr:
            params["filter"] = filter_expr

        response = self._make_request("GET", "users", params=params)

        # Response is a list for /users endpoint
        return response if isinstance(response, list) else []

    def get_user_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all groups a user belongs to.

        Calls: GET /api/v1/users/{userId}/groups

        Args:
            user_id: Okta user ID

        Returns:
            List of group dictionaries
        """
        response = self._make_request("GET", f"users/{user_id}/groups")
        return response if isinstance(response, list) else []

    def suspend_user(self, user_id: str) -> bool:
        """
        Suspend a user (transitions to SUSPENDED status).

        Calls: POST /api/v1/users/{userId}/lifecycle/suspend

        Args:
            user_id: Okta user ID

        Returns:
            True if successful
        """
        try:
            self._make_request("POST", f"users/{user_id}/lifecycle/suspend")
            return True
        except OktaAPIError:
            return False

    def unsuspend_user(self, user_id: str) -> bool:
        """
        Unsuspend a user (transitions back to ACTIVE status).

        Calls: POST /api/v1/users/{userId}/lifecycle/unsuspend

        Args:
            user_id: Okta user ID

        Returns:
            True if successful
        """
        try:
            self._make_request("POST", f"users/{user_id}/lifecycle/unsuspend")
            return True
        except OktaAPIError:
            return False

    # ========== OKTA GROUPS API ==========

    def create_group(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new group in Okta.

        Calls: POST /api/v1/groups

        Args:
            name: Group name
            description: Group description (optional)

        Returns:
            Created group data dictionary with 'id' field

        Example:
            >>> group = client.create_group("Engineering", "Engineering team")
            >>> group_id = group['id']
        """
        data = {
            "profile": {
                "name": name,
                "description": description
            }
        }

        return self._make_request("POST", "groups", data=data)

    def update_group(self, group_id: str, name: Optional[str] = None,
                    description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update group profile.

        Calls: PUT /api/v1/groups/{groupId}

        Args:
            group_id: Okta group ID
            name: New group name (optional)
            description: New group description (optional)

        Returns:
            Updated group data dictionary
        """
        data = {"profile": {}}

        if name is not None:
            data["profile"]["name"] = name
        if description is not None:
            data["profile"]["description"] = description

        return self._make_request("PUT", f"groups/{group_id}", data=data)

    def delete_group(self, group_id: str) -> bool:
        """
        Delete a group permanently.

        Calls: DELETE /api/v1/groups/{groupId}

        Args:
            group_id: Okta group ID

        Returns:
            True if successful
        """
        try:
            self._make_request("DELETE", f"groups/{group_id}")
            return True
        except OktaAPIError:
            return False

    def get_group(self, group_id: str) -> Dict[str, Any]:
        """
        Get group details by ID.

        Calls: GET /api/v1/groups/{groupId}

        Args:
            group_id: Okta group ID

        Returns:
            Group data dictionary
        """
        return self._make_request("GET", f"groups/{group_id}")

    def list_groups(self, limit: int = 200, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List groups in the organization.

        Calls: GET /api/v1/groups

        Args:
            limit: Number of results per page (default 200)
            query: Search query for group name

        Returns:
            List of group dictionaries
        """
        params = {"limit": limit}

        if query:
            params["q"] = query

        response = self._make_request("GET", "groups", params=params)
        return response if isinstance(response, list) else []

    def add_user_to_group(self, group_id: str, user_id: str) -> bool:
        """
        Add a user to a group.

        Calls: PUT /api/v1/groups/{groupId}/users/{userId}

        Args:
            group_id: Okta group ID
            user_id: Okta user ID

        Returns:
            True if successful
        """
        try:
            self._make_request("PUT", f"groups/{group_id}/users/{user_id}")
            return True
        except OktaAPIError:
            return False

    def remove_user_from_group(self, group_id: str, user_id: str) -> bool:
        """
        Remove a user from a group.

        Calls: DELETE /api/v1/groups/{groupId}/users/{userId}

        Args:
            group_id: Okta group ID
            user_id: Okta user ID

        Returns:
            True if successful
        """
        try:
            self._make_request("DELETE", f"groups/{group_id}/users/{user_id}")
            return True
        except OktaAPIError:
            return False

    def get_group_members(self, group_id: str, limit: int = 200) -> List[str]:
        """
        Get all user IDs that are members of a group.

        Calls: GET /api/v1/groups/{groupId}/users

        Args:
            group_id: Okta group ID
            limit: Number of results per page (default 200)

        Returns:
            List of user IDs
        """
        params = {"limit": limit}
        response = self._make_request("GET", f"groups/{group_id}/users", params=params)

        users = response if isinstance(response, list) else []
        return [user.get("id") for user in users if "id" in user]

    # ========== OKTA APPS API ==========

    def list_apps(self, limit: int = 200, filter_expr: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List applications in the organization.

        Calls: GET /api/v1/apps

        Args:
            limit: Number of results per page (default 200)
            filter_expr: Okta filter expression (e.g., 'status eq "ACTIVE"')

        Returns:
            List of app dictionaries with 'id', 'name', 'label', etc.
        """
        params = {"limit": limit}

        if filter_expr:
            params["filter"] = filter_expr

        response = self._make_request("GET", "apps", params=params)
        return response if isinstance(response, list) else []

    def get_app(self, app_id: str) -> Dict[str, Any]:
        """
        Get application details by ID.

        Calls: GET /api/v1/apps/{appId}

        Args:
            app_id: Okta app ID

        Returns:
            App data dictionary
        """
        return self._make_request("GET", f"apps/{app_id}")

    def assign_user_to_app(self, app_id: str, user_id: str,
                          app_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assign a user to an application.

        Calls: POST /api/v1/apps/{appId}/users

        Args:
            app_id: Okta app ID
            user_id: Okta user ID
            app_profile: Optional app-specific profile data

        Returns:
            Assignment data dictionary
        """
        data = {"id": user_id}

        if app_profile:
            data["profile"] = app_profile

        return self._make_request("POST", f"apps/{app_id}/users", data=data)

    def assign_group_to_app(self, app_id: str, group_id: str,
                           app_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assign a group to an application.

        Calls: PUT /api/v1/apps/{appId}/groups/{groupId}

        Args:
            app_id: Okta app ID
            group_id: Okta group ID
            app_profile: Optional app-specific profile data

        Returns:
            Assignment data dictionary
        """
        data = {}
        if app_profile:
            data["profile"] = app_profile

        return self._make_request("PUT", f"apps/{app_id}/groups/{group_id}", data=data)

    def get_app_user_assignments(self, app_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Get all user assignments for an application.

        Calls: GET /api/v1/apps/{appId}/users

        Args:
            app_id: Okta app ID
            limit: Number of results per page (default 200)

        Returns:
            List of assignment dictionaries
        """
        params = {"limit": limit}
        response = self._make_request("GET", f"apps/{app_id}/users", params=params)
        return response if isinstance(response, list) else []

    def get_app_group_assignments(self, app_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Get all group assignments for an application.

        Calls: GET /api/v1/apps/{appId}/groups

        Args:
            app_id: Okta app ID
            limit: Number of results per page (default 200)

        Returns:
            List of assignment dictionaries
        """
        params = {"limit": limit}
        response = self._make_request("GET", f"apps/{app_id}/groups", params=params)
        return response if isinstance(response, list) else []

    def remove_user_from_app(self, app_id: str, user_id: str) -> bool:
        """
        Remove a user's assignment from an application.

        Calls: DELETE /api/v1/apps/{appId}/users/{userId}

        Args:
            app_id: Okta app ID
            user_id: Okta user ID

        Returns:
            True if successful
        """
        try:
            self._make_request("DELETE", f"apps/{app_id}/users/{user_id}")
            return True
        except OktaAPIError:
            return False

    # ========== BASECONNECTION COMPATIBILITY MAPPINGS ==========
    # These methods map BaseConnection abstractions to Okta equivalents

    def create_project(self, workspace_gid: str, name: str, notes: str = "",
                      **kwargs) -> Dict[str, Any]:
        """
        BaseConnection compatibility: Maps to create_group().

        In Okta context:
        - workspace_gid is ignored (Okta groups are org-wide)
        - Project -> Group

        Args:
            workspace_gid: Ignored (Okta groups are org-wide)
            name: Group name
            notes: Group description
            **kwargs: Ignored

        Returns:
            Created group data with 'id' mapped to 'gid' for compatibility
        """
        group = self.create_group(name=name, description=notes)
        # Add 'gid' alias for BaseConnection compatibility
        group['gid'] = group['id']
        return group

    def delete_project(self, project_gid: str):
        """
        BaseConnection compatibility: Maps to delete_group().

        Args:
            project_gid: Group ID to delete
        """
        self.delete_group(project_gid)

    def create_task(self, project_gid: str, name: str, notes: str = "",
                   assignee: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        BaseConnection compatibility: Maps to create_user().

        In Okta context:
        - Task -> User
        - project_gid is used to add user to group after creation
        - name is used as firstName, notes as lastName
        - assignee is ignored

        Args:
            project_gid: Group ID to add user to (optional)
            name: User's first name
            notes: User's last name (or email if not provided)
            assignee: Ignored
            **kwargs: Can include 'email' and 'login'

        Returns:
            Created user data with 'id' mapped to 'gid' for compatibility
        """
        # Generate email from name if not provided
        email = kwargs.get('email', f"{name.lower().replace(' ', '.')}.{notes.lower().replace(' ', '.')}@example.com")
        login = kwargs.get('login', email)

        profile = {
            "firstName": name,
            "lastName": notes or "User",
            "email": email,
            "login": login
        }

        user = self.create_user(profile=profile, activate=kwargs.get('activate', True))

        # Add user to group if project_gid provided
        if project_gid:
            self.add_user_to_group(project_gid, user['id'])

        # Add 'gid' alias for BaseConnection compatibility
        user['gid'] = user['id']
        return user

    def delete_task(self, task_gid: str):
        """
        BaseConnection compatibility: Maps to deactivate_user().

        Note: This only deactivates the user, does not permanently delete.
        Use delete_user() for permanent deletion.

        Args:
            task_gid: User ID to deactivate
        """
        self.deactivate_user(task_gid)

    def add_members_to_project(self, project_gid: str, member_gids: List[str]):
        """
        BaseConnection compatibility: Maps to add_user_to_group().

        Args:
            project_gid: Group ID
            member_gids: List of user IDs to add to group
        """
        for user_id in member_gids:
            self.add_user_to_group(project_gid, user_id)

    def get_workspace_users(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        BaseConnection compatibility: Maps to list_users().

        Args:
            workspace_gid: Ignored (Okta users are org-wide)

        Returns:
            List of users with 'gid' alias added
        """
        users = self.list_users()
        # Add 'gid' alias for each user
        for user in users:
            user['gid'] = user['id']
        return users

    def get_task(self, task_gid: str) -> Dict[str, Any]:
        """
        BaseConnection compatibility: Maps to get_user().

        Args:
            task_gid: User ID

        Returns:
            User data with 'gid' alias added
        """
        user = self.get_user(task_gid)
        user['gid'] = user['id']
        return user

    def get_project_tasks(self, project_gid: str) -> List[Dict[str, Any]]:
        """
        BaseConnection compatibility: Maps to get_group_members().

        Returns full user objects for all members of the group.

        Args:
            project_gid: Group ID

        Returns:
            List of user objects with 'gid' alias added
        """
        # Get member IDs
        response = self._make_request("GET", f"groups/{project_gid}/users")
        users = response if isinstance(response, list) else []

        # Add 'gid' alias for each user
        for user in users:
            user['gid'] = user.get('id')

        return users

    # ========== NOT IMPLEMENTED METHODS ==========
    # These BaseConnection methods don't have direct Okta equivalents

    def create_subtask(self, parent_task_gid: str, name: str, notes: str = "",
                      assignee: Optional[str] = None) -> Dict[str, Any]:
        """Not applicable to Okta. Users don't have subtasks."""
        raise NotImplementedError(
            "Subtasks are not supported in Okta. "
            "Consider using custom user attributes or groups instead."
        )

    def update_task(self, task_gid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        BaseConnection compatibility: Maps to update_user().

        Args:
            task_gid: User ID
            updates: Dictionary of profile fields to update

        Returns:
            Updated user data
        """
        user = self.update_user(task_gid, updates)
        user['gid'] = user['id']
        return user

    def complete_task(self, task_gid: str) -> Dict[str, Any]:
        """Not directly applicable to Okta. Consider deactivating the user instead."""
        raise NotImplementedError(
            "Task completion is not supported in Okta. "
            "Use deactivate_user() to deactivate a user instead."
        )

    def get_task_subtasks(self, task_gid: str) -> List[Dict[str, Any]]:
        """Not applicable to Okta. Users don't have subtasks."""
        raise NotImplementedError("Subtasks are not supported in Okta.")

    def set_task_assignee(self, task_gid: str, assignee_gid: str) -> Dict[str, Any]:
        """Not directly applicable to Okta users."""
        raise NotImplementedError(
            "Task assignee concept doesn't apply to Okta users. "
            "Consider using manager attribute or group membership instead."
        )

    def add_comment(self, task_gid: str, text: str) -> Dict[str, Any]:
        """Not applicable to Okta. Users don't have comments."""
        raise NotImplementedError(
            "Comments are not supported in Okta user API. "
            "Consider using custom user attributes for notes."
        )

    def create_custom_field(self, workspace_gid: str, name: str, field_type: str,
                           description: str = "", **kwargs) -> Dict[str, Any]:
        """
        Custom fields in Okta are managed through user schema.
        This is a complex operation requiring admin permissions.
        """
        raise NotImplementedError(
            "Custom field creation in Okta requires schema management. "
            "Use Okta Admin Console to add custom user attributes."
        )

    def add_custom_field_to_project(self, project_gid: str, custom_field_gid: str):
        """Not applicable to Okta groups."""
        raise NotImplementedError("Custom fields on groups are not supported in Okta.")

    def get_workspace_custom_fields(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """Custom fields in Okta require schema API."""
        raise NotImplementedError(
            "Use Okta User Schema API to retrieve custom attributes."
        )

    def delete_custom_field(self, custom_field_gid: str):
        """Custom field deletion requires schema management."""
        raise NotImplementedError(
            "Custom field deletion requires Okta schema management."
        )

    def create_custom_field_value(self, task_gid: str, custom_field_gid: str,
                                  value: Any) -> Dict[str, Any]:
        """
        Setting custom attributes on users is supported through update_user().
        """
        raise NotImplementedError(
            "Use update_user() with custom profile attributes instead. "
            "Example: update_user(user_id, {'customAttribute': 'value'})"
        )

    def create_section(self, project_gid: str, name: str) -> Dict[str, Any]:
        """Not applicable to Okta groups."""
        raise NotImplementedError("Sections are not supported in Okta groups.")

    def get_project_sections(self, project_gid: str) -> List[Dict[str, Any]]:
        """Not applicable to Okta groups."""
        raise NotImplementedError("Sections are not supported in Okta groups.")

    def add_task_to_section(self, task_gid: str, section_gid: str):
        """Not applicable to Okta."""
        raise NotImplementedError("Sections are not supported in Okta.")

    def create_tag(self, workspace_gid: str, name: str, **kwargs) -> Dict[str, Any]:
        """
        Tags can be simulated using Okta groups.
        Create a group with a 'tag:' prefix to simulate tags.
        """
        raise NotImplementedError(
            "Tags are not directly supported in Okta. "
            "Consider creating groups with 'tag:' prefix or using custom attributes."
        )

    def add_tag_to_task(self, task_gid: str, tag_gid: str):
        """Tags are not natively supported. Use groups or custom attributes."""
        raise NotImplementedError(
            "Use add_user_to_group() to add users to tag-like groups instead."
        )

    def get_workspace_tags(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """Tags are not natively supported in Okta."""
        raise NotImplementedError("Tags are not supported in Okta.")

    def delete_tag(self, tag_gid: str):
        """Tags are not natively supported in Okta."""
        raise NotImplementedError("Tags are not supported in Okta.")

    def create_portfolio(self, workspace_gid: str, name: str, **kwargs) -> Dict[str, Any]:
        """Not applicable to Okta."""
        raise NotImplementedError("Portfolios are not supported in Okta.")

    def add_project_to_portfolio(self, portfolio_gid: str, project_gid: str):
        """Not applicable to Okta."""
        raise NotImplementedError("Portfolios are not supported in Okta.")

    def get_workspace_portfolios(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """Not applicable to Okta."""
        raise NotImplementedError("Portfolios are not supported in Okta.")

    def delete_portfolio(self, portfolio_gid: str):
        """Not applicable to Okta."""
        raise NotImplementedError("Portfolios are not supported in Okta.")

    def add_followers(self, task_gid: str, followers: List[str]):
        """Not applicable to Okta users."""
        raise NotImplementedError("Followers are not supported in Okta.")

    def remove_followers(self, task_gid: str, followers: List[str]):
        """Not applicable to Okta users."""
        raise NotImplementedError("Followers are not supported in Okta.")

    def add_task_dependency(self, task_gid: str, depends_on_gid: str):
        """Not applicable to Okta users."""
        raise NotImplementedError("Task dependencies are not supported in Okta.")

    def create_milestone(self, project_gid: str, name: str, due_date: str,
                        notes: str = "", assignee: Optional[str] = None) -> Dict[str, Any]:
        """Not applicable to Okta."""
        raise NotImplementedError("Milestones are not supported in Okta.")


class OktaClientPool(BaseClientPool):
    """
    Pool of Okta clients for multi-user simulation.

    Manages multiple SSWS tokens representing different admin users.
    Useful for simulating activity from multiple administrators.

    Example:
        >>> user_tokens = [
        ...     {"name": "admin1", "token": "00abc...", "org_url": "https://dev-123.okta.com"},
        ...     {"name": "admin2", "token": "00def...", "org_url": "https://dev-123.okta.com"}
        ... ]
        >>> pool = OktaClientPool(user_tokens)
        >>> client = pool.get_random_client()
        >>> user_id = pool.get_user_id("admin1")
    """

    def __init__(self, user_tokens: List[Dict[str, str]]):
        """
        Initialize client pool with multiple Okta admin tokens.

        Args:
            user_tokens: List of dictionaries with keys:
                - name: User identifier
                - token: SSWS API token
                - org_url: Okta organization URL

        Example:
            >>> pool = OktaClientPool([
            ...     {"name": "admin1", "token": "00abc...", "org_url": "https://dev-123.okta.com"},
            ...     {"name": "admin2", "token": "00def...", "org_url": "https://dev-123.okta.com"}
            ... ])
        """
        # Call parent with empty dict (we'll populate clients manually)
        super().__init__({})

        for user_config in user_tokens:
            user_name = user_config.get("name")
            token = user_config.get("token")
            org_url = user_config.get("org_url")

            if not all([user_name, token, org_url]):
                print(f"✗ Invalid config for user: {user_config}")
                continue

            client = OktaConnection(token=token, org_url=org_url, user_name=user_name)
            try:
                # Validate token on initialization
                if client.validate_token():
                    self.clients[user_name] = client
                    # Cache the user's Okta ID
                    user_info = client.get_user_info()
                    self.user_gids[user_name] = user_info.get("id")
                    print(f"✓ Initialized Okta client for {user_name}")
                else:
                    print(f"✗ Invalid token for {user_name}")
            except Exception as e:
                print(f"✗ Error initializing client for {user_name}: {e}")

    def get_client(self, user_name: str) -> Optional[OktaConnection]:
        """
        Get client for a specific user.

        Args:
            user_name: User identifier

        Returns:
            OktaConnection or None if not found/invalid
        """
        client = self.clients.get(user_name)
        if client and not client.is_valid:
            print(f"⚠ Token for {user_name} is no longer valid")
            return None
        return client

    def get_random_client(self) -> Optional[OktaConnection]:
        """
        Get a random valid client from the pool.

        Returns:
            Random OktaConnection or None if no valid clients
        """
        import random
        valid_clients = [c for c in self.clients.values() if c.is_valid]
        return random.choice(valid_clients) if valid_clients else None

    def get_valid_clients(self) -> List[OktaConnection]:
        """
        Get all valid clients.

        Returns:
            List of valid OktaConnections
        """
        return [c for c in self.clients.values() if c.is_valid]

    def get_valid_user_names(self) -> List[str]:
        """
        Get names of all users with valid tokens.

        Returns:
            List of user identifiers
        """
        return [name for name, client in self.clients.items() if client.is_valid]

    def get_user_gid(self, user_name: str) -> Optional[str]:
        """
        Get the Okta user ID for a given user identifier.

        Args:
            user_name: User identifier

        Returns:
            Okta user ID or None if not found
        """
        return self.user_gids.get(user_name)

    def validate_all_tokens(self) -> Dict[str, bool]:
        """
        Validate all tokens in the pool.

        Returns:
            Dictionary mapping user names to validation status
        """
        results = {}
        for user_name, client in self.clients.items():
            results[user_name] = client.validate_token()
        return results


# Example usage and testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python okta_connection.py <SSWS_TOKEN> <ORG_URL>")
        print("Example: python okta_connection.py 00abc123... https://dev-123456.okta.com")
        sys.exit(1)

    token = sys.argv[1]
    org_url = sys.argv[2]

    # Test single client
    print("=" * 60)
    print("Testing Okta Connection")
    print("=" * 60)

    client = OktaConnection(token=token, org_url=org_url, user_name="Test User")

    # Validate token
    print("\n1. Validating token...")
    if client.validate_token():
        print("✓ Token is valid")

        # Get user info
        user = client.get_user_info()
        print(f"✓ Authenticated as: {user.get('profile', {}).get('firstName')} {user.get('profile', {}).get('lastName')}")
        print(f"  Email: {user.get('profile', {}).get('email')}")
        print(f"  User ID: {user.get('id')}")

        # List users
        print("\n2. Listing users (first 5)...")
        users = client.list_users(limit=5)
        print(f"✓ Found {len(users)} users")
        for u in users[:5]:
            profile = u.get('profile', {})
            print(f"  - {profile.get('firstName')} {profile.get('lastName')} ({u.get('id')})")

        # List groups
        print("\n3. Listing groups (first 5)...")
        groups = client.list_groups(limit=5)
        print(f"✓ Found {len(groups)} groups")
        for g in groups[:5]:
            profile = g.get('profile', {})
            print(f"  - {profile.get('name')}: {profile.get('description')} ({g.get('id')})")

        # List apps
        print("\n4. Listing apps (first 5)...")
        apps = client.list_apps(limit=5)
        print(f"✓ Found {len(apps)} apps")
        for app in apps[:5]:
            print(f"  - {app.get('label')} ({app.get('id')})")

        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
    else:
        print("✗ Token is invalid")
        sys.exit(1)
