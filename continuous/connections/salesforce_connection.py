#!/usr/bin/env python3
"""
Salesforce CRM API Client implementing BaseConnection interface.
Maps project/task abstraction to Salesforce CRM concepts.

CONCEPT MAPPING:
- project → Account (company/customer in CRM)
- task → Opportunity or Lead (sales opportunities/prospects)
- subtask → OpportunityLineItem or Contact (line items or related contacts)
- comment → Task/Note/ChatterPost (activity records and notes)
- section → OpportunityStage or custom grouping (sales pipeline stages)
- tag → Tag (standard Salesforce tags/topics)
- custom field → Custom Fields (extensible CRM fields)
- portfolio → Campaign or Account hierarchy (marketing campaigns or parent accounts)
- milestone → Contract or closed opportunity (important business milestones)

NOTE: Salesforce uses a different paradigm than project management tools.
We intelligently map concepts to maintain compatibility with BaseConnection
while respecting CRM domain semantics.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

try:
    from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
    from simple_salesforce.exceptions import SalesforceError
except ImportError:
    raise ImportError(
        "simple-salesforce library is required. Install with: pip install simple-salesforce"
    )

from continuous.connections.base_connection import (
    BaseConnection,
    BaseClientPool,
    ConnectionError as BaseConnectionError,
    RateLimitError as BaseRateLimitError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Salesforce-specific exceptions
class SalesforceAPIError(BaseConnectionError):
    """Custom exception for Salesforce API errors."""
    pass


class SalesforceRateLimitError(BaseRateLimitError):
    """Custom exception for rate limit errors."""
    pass


class SalesforceConnection(BaseConnection):
    """
    Salesforce CRM API client implementing the BaseConnection interface.

    Maps project management abstractions to CRM concepts:
    - Projects become Accounts (customers/companies)
    - Tasks become Opportunities (sales opportunities)
    - Subtasks become OpportunityLineItems or Contacts
    - Comments become Task/Note/Chatter posts
    - Sections become OpportunityStages
    - Tags remain Tags
    - Portfolios become Campaigns
    - Milestones become Contracts

    AUTHENTICATION:
    Uses OAuth 2.0 username-password flow with security token.
    The security_token is appended to the password for API authentication.

    API LIMITS:
    Salesforce has strict daily API request limits that vary by edition:
    - Developer: 15,000 requests/day
    - Enterprise: 1,000,000 requests/day
    We track usage and provide warnings as limits approach.
    """

    def __init__(
        self,
        api_key: str,  # Not used for Salesforce, kept for interface compatibility
        user_name: str = "Unknown",
        username: str = None,
        password: str = None,
        security_token: str = None,
        instance_url: str = None,
        domain: str = "login"  # Use 'test' for sandbox
    ):
        """
        Initialize Salesforce connection.

        Args:
            api_key: Not used (kept for BaseConnection interface compatibility)
            user_name: Display name for logging
            username: Salesforce username (email)
            password: Salesforce password
            security_token: Security token (appended to password)
            instance_url: Salesforce instance URL (e.g., https://na1.salesforce.com)
            domain: 'login' for production, 'test' for sandbox
        """
        super().__init__(api_key, user_name)

        self.username = username
        self.password = password
        self.security_token = security_token
        self.instance_url = instance_url
        self.domain = domain

        # Salesforce client
        self.sf = None

        # API usage tracking
        self.api_usage_limit = None
        self.api_usage_used = 0

        # Connect to Salesforce
        self._connect()

    def _connect(self):
        """
        Establish connection to Salesforce using OAuth 2.0 username-password flow.

        Raises:
            SalesforceAPIError: If authentication fails
        """
        try:
            # Combine password and security token
            full_password = f"{self.password}{self.security_token}" if self.security_token else self.password

            self.sf = Salesforce(
                username=self.username,
                password=full_password,
                security_token='',  # Already appended to password
                domain=self.domain,
                instance_url=self.instance_url
            )

            # Get API usage limits
            self._update_api_usage()

            logger.info(f"Connected to Salesforce as {self.username}")
            logger.info(f"API Usage: {self.api_usage_used}/{self.api_usage_limit}")

        except SalesforceAuthenticationFailed as e:
            self.is_valid = False
            raise SalesforceAPIError(f"Salesforce authentication failed: {e}")
        except Exception as e:
            self.is_valid = False
            raise SalesforceAPIError(f"Failed to connect to Salesforce: {e}")

    def _update_api_usage(self):
        """
        Update API usage statistics from Salesforce limits.

        Salesforce returns usage information in response headers.
        """
        try:
            # Query for limits using REST API
            limits = self.sf.limits()

            if limits and 'DailyApiRequests' in limits:
                self.api_usage_limit = limits['DailyApiRequests']['Max']
                self.api_usage_used = limits['DailyApiRequests']['Remaining']

                # Calculate actual used
                self.api_usage_used = self.api_usage_limit - self.api_usage_used

                # Warn if approaching limit (90% used)
                if self.api_usage_used / self.api_usage_limit > 0.9:
                    logger.warning(
                        f"Approaching API limit: {self.api_usage_used}/{self.api_usage_limit} "
                        f"({self.api_usage_used/self.api_usage_limit*100:.1f}%)"
                    )
        except Exception as e:
            logger.warning(f"Could not retrieve API limits: {e}")

    def _handle_rate_limiting(self):
        """
        Handle rate limiting for Salesforce API.

        Salesforce has per-second and daily limits.
        We implement conservative rate limiting to avoid hitting limits.
        """
        super()._handle_rate_limiting()

        # Update usage every 100 requests
        if self.request_count % 100 == 0:
            self._update_api_usage()

    def _make_request(self, operation: str, sobject: str = None,
                     record_id: str = None, data: Dict = None,
                     method: str = "GET") -> Any:
        """
        Make a Salesforce API request with error handling.

        Args:
            operation: Operation type (query, create, update, delete, get)
            sobject: Salesforce object type (Account, Opportunity, etc.)
            record_id: Record ID for get/update/delete operations
            data: Data for create/update operations
            method: HTTP method override

        Returns:
            Response data

        Raises:
            SalesforceAPIError: For API errors
            SalesforceRateLimitError: For rate limit errors
        """
        self._handle_rate_limiting()

        try:
            if operation == "query":
                result = self.sf.query(data)
                return result
            elif operation == "create":
                obj = getattr(self.sf, sobject)
                result = obj.create(data)
                return result
            elif operation == "update":
                obj = getattr(self.sf, sobject)
                result = obj.update(record_id, data)
                return result
            elif operation == "delete":
                obj = getattr(self.sf, sobject)
                result = obj.delete(record_id)
                return result
            elif operation == "get":
                obj = getattr(self.sf, sobject)
                result = obj.get(record_id)
                return result
            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except SalesforceError as e:
            error_msg = str(e)

            # Check for rate limiting
            if "REQUEST_LIMIT_EXCEEDED" in error_msg or "TooManyRequests" in error_msg:
                raise SalesforceRateLimitError(f"Rate limit exceeded: {error_msg}")

            # Check for authentication errors
            if "INVALID_SESSION_ID" in error_msg or "Session expired" in error_msg:
                self.is_valid = False
                raise SalesforceAPIError("Session expired or invalid")

            raise SalesforceAPIError(f"Salesforce API error: {error_msg}")
        except Exception as e:
            raise SalesforceAPIError(f"Request error: {e}")

    def validate_token(self) -> bool:
        """
        Validate that the Salesforce connection is valid.

        Returns:
            True if valid, False otherwise
        """
        try:
            self.get_user_info()
            self.is_valid = True
            return True
        except SalesforceAPIError:
            self.is_valid = False
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information.

        Returns:
            User data dictionary with user details
        """
        try:
            # Query for current user
            query = f"SELECT Id, Name, Email, Username, IsActive FROM User WHERE Username = '{self.username}'"
            result = self._make_request("query", data=query)

            if result['totalSize'] > 0:
                user = result['records'][0]
                return {
                    'gid': user['Id'],
                    'name': user['Name'],
                    'email': user['Email'],
                    'username': user['Username'],
                    'active': user['IsActive']
                }
            else:
                raise SalesforceAPIError("User not found")

        except Exception as e:
            raise SalesforceAPIError(f"Failed to get user info: {e}")

    # ========== PROJECT/WORKSPACE OPERATIONS ==========
    # In Salesforce: PROJECT = ACCOUNT (customer/company)

    def create_project(self, workspace_gid: str, name: str, notes: str = "",
                      **kwargs) -> Dict[str, Any]:
        """
        Create a new project (mapped to Account in Salesforce).

        In CRM context, a project represents a customer account/company.

        Args:
            workspace_gid: Not used in Salesforce (no workspace concept)
            name: Account name (company name)
            notes: Account description
            **kwargs: Additional Salesforce Account fields:
                - industry: Industry type
                - annual_revenue: Annual revenue
                - phone: Phone number
                - website: Company website
                - billing_city, billing_state, billing_country: Address

        Returns:
            Created Account data
        """
        account_data = {
            'Name': name,
            'Description': notes
        }

        # Add optional fields
        if 'industry' in kwargs:
            account_data['Industry'] = kwargs['industry']
        if 'annual_revenue' in kwargs:
            account_data['AnnualRevenue'] = kwargs['annual_revenue']
        if 'phone' in kwargs:
            account_data['Phone'] = kwargs['phone']
        if 'website' in kwargs:
            account_data['Website'] = kwargs['website']
        if 'billing_city' in kwargs:
            account_data['BillingCity'] = kwargs['billing_city']
        if 'billing_state' in kwargs:
            account_data['BillingState'] = kwargs['billing_state']
        if 'billing_country' in kwargs:
            account_data['BillingCountry'] = kwargs['billing_country']

        result = self._make_request("create", sobject="Account", data=account_data)

        if result and result.get('success'):
            # Return with gid for compatibility
            return {
                'gid': result['id'],
                'id': result['id'],
                'name': name,
                'notes': notes
            }
        else:
            raise SalesforceAPIError(f"Failed to create account: {result}")

    def delete_project(self, project_gid: str):
        """
        Delete a project (mapped to Account).

        WARNING: Deleting an Account may delete related Opportunities, Contacts, etc.
        depending on your Salesforce configuration.

        Args:
            project_gid: Account ID to delete
        """
        try:
            self._make_request("delete", sobject="Account", record_id=project_gid)
        except Exception as e:
            raise SalesforceAPIError(f"Failed to delete account: {e}")

    def add_members_to_project(self, project_gid: str, member_gids: List[str]):
        """
        Add members to a project (mapped to Account Team).

        Creates AccountTeamMember records to give users access to the account.

        Args:
            project_gid: Account ID
            member_gids: List of User IDs to add to account team
        """
        for user_id in member_gids:
            try:
                team_member_data = {
                    'AccountId': project_gid,
                    'UserId': user_id,
                    'TeamMemberRole': 'Account Manager'  # Default role
                }
                self._make_request("create", sobject="AccountTeamMember",
                                 data=team_member_data)
            except Exception as e:
                logger.warning(f"Could not add user {user_id} to account team: {e}")

    def get_workspace_users(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all users (mapped to active Salesforce users).

        Args:
            workspace_gid: Not used in Salesforce

        Returns:
            List of active users
        """
        try:
            query = "SELECT Id, Name, Email, Username FROM User WHERE IsActive = TRUE LIMIT 200"
            result = self._make_request("query", data=query)

            users = []
            for record in result['records']:
                users.append({
                    'gid': record['Id'],
                    'name': record['Name'],
                    'email': record['Email'],
                    'username': record.get('Username', '')
                })

            return users
        except Exception as e:
            raise SalesforceAPIError(f"Failed to get users: {e}")

    # ========== TASK OPERATIONS ==========
    # In Salesforce: TASK = OPPORTUNITY (sales opportunity)

    def create_task(self, project_gid: str, name: str, notes: str = "",
                   assignee: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Create a new task (mapped to Opportunity in Salesforce).

        In CRM context, a task represents a sales opportunity.

        Args:
            project_gid: Account ID (customer)
            name: Opportunity name
            notes: Opportunity description
            assignee: Owner User ID (sales rep)
            **kwargs: Additional Salesforce Opportunity fields:
                - amount: Deal amount
                - close_date: Expected close date (YYYY-MM-DD)
                - stage: Sales stage (default: 'Prospecting')
                - probability: Win probability (0-100)
                - type: Opportunity type
                - lead_source: Lead source

        Returns:
            Created Opportunity data
        """
        # Default close date is 30 days from now if not provided
        close_date = kwargs.get('close_date', kwargs.get('due_date'))
        if not close_date:
            from datetime import datetime, timedelta
            close_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

        opportunity_data = {
            'Name': name,
            'AccountId': project_gid,
            'Description': notes,
            'CloseDate': close_date,
            'StageName': kwargs.get('stage', 'Prospecting')
        }

        # Add optional fields
        if assignee:
            opportunity_data['OwnerId'] = assignee
        if 'amount' in kwargs:
            opportunity_data['Amount'] = kwargs['amount']
        if 'probability' in kwargs:
            opportunity_data['Probability'] = kwargs['probability']
        if 'type' in kwargs:
            opportunity_data['Type'] = kwargs['type']
        if 'lead_source' in kwargs:
            opportunity_data['LeadSource'] = kwargs['lead_source']

        result = self._make_request("create", sobject="Opportunity", data=opportunity_data)

        if result and result.get('success'):
            # Get full record to return assignee info
            opp = self._make_request("get", sobject="Opportunity", record_id=result['id'])
            return {
                'gid': result['id'],
                'id': result['id'],
                'name': name,
                'notes': notes,
                'assignee': {'gid': opp.get('OwnerId')} if opp.get('OwnerId') else None
            }
        else:
            raise SalesforceAPIError(f"Failed to create opportunity: {result}")

    def create_subtask(self, parent_task_gid: str, name: str, notes: str = "",
                      assignee: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a subtask (mapped to OpportunityLineItem or Contact).

        In CRM context, we map subtasks to:
        - OpportunityLineItem (product line items) if name suggests product
        - Contact (related person) otherwise

        Args:
            parent_task_gid: Opportunity ID
            name: Line item/contact name
            notes: Description
            assignee: Not used for line items

        Returns:
            Created record data
        """
        # Simple heuristic: if name contains "contact" or email-like, create Contact
        # Otherwise create OpportunityLineItem

        if any(keyword in name.lower() for keyword in ['contact', '@', 'person', 'client']):
            # Create as Contact
            # First get the AccountId from the Opportunity
            opp = self._make_request("get", sobject="Opportunity", record_id=parent_task_gid)
            account_id = opp.get('AccountId')

            contact_data = {
                'LastName': name,
                'Description': notes,
                'AccountId': account_id
            }

            if assignee:
                contact_data['OwnerId'] = assignee

            result = self._make_request("create", sobject="Contact", data=contact_data)

            if result and result.get('success'):
                return {
                    'gid': result['id'],
                    'id': result['id'],
                    'name': name,
                    'type': 'Contact'
                }
        else:
            # Create as OpportunityLineItem (requires PricebookEntry)
            # For simplicity, we'll create a Task record instead since line items
            # require complex setup with products and price books

            task_data = {
                'Subject': name,
                'Description': notes,
                'WhatId': parent_task_gid,  # Link to Opportunity
                'Status': 'Not Started',
                'Priority': 'Normal'
            }

            if assignee:
                task_data['OwnerId'] = assignee

            result = self._make_request("create", sobject="Task", data=task_data)

            if result and result.get('success'):
                return {
                    'gid': result['id'],
                    'id': result['id'],
                    'name': name,
                    'type': 'Task'
                }

        raise SalesforceAPIError("Failed to create subtask")

    def update_task(self, task_gid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update task fields (mapped to Opportunity).

        Args:
            task_gid: Opportunity ID
            updates: Dictionary of fields to update (maps to Salesforce fields)

        Returns:
            Success indicator
        """
        # Map common fields to Salesforce
        sf_updates = {}

        field_mapping = {
            'name': 'Name',
            'notes': 'Description',
            'assignee': 'OwnerId',
            'completed': 'IsClosed',
            'due_on': 'CloseDate',
            'stage': 'StageName',
            'amount': 'Amount',
            'probability': 'Probability'
        }

        for key, value in updates.items():
            sf_field = field_mapping.get(key, key)
            sf_updates[sf_field] = value

        result = self._make_request("update", sobject="Opportunity",
                                   record_id=task_gid, data=sf_updates)

        return {'success': True, 'gid': task_gid}

    def complete_task(self, task_gid: str) -> Dict[str, Any]:
        """
        Mark a task as completed (close Opportunity as won).

        Args:
            task_gid: Opportunity ID

        Returns:
            Updated opportunity data
        """
        return self.update_task(task_gid, {
            'StageName': 'Closed Won',
            'IsClosed': True
        })

    def delete_task(self, task_gid: str):
        """
        Delete a task (Opportunity).

        Args:
            task_gid: Opportunity ID to delete
        """
        try:
            self._make_request("delete", sobject="Opportunity", record_id=task_gid)
        except Exception as e:
            raise SalesforceAPIError(f"Failed to delete opportunity: {e}")

    def get_task(self, task_gid: str) -> Dict[str, Any]:
        """
        Get task details (Opportunity).

        Args:
            task_gid: Opportunity ID

        Returns:
            Opportunity data
        """
        try:
            opp = self._make_request("get", sobject="Opportunity", record_id=task_gid)
            return {
                'gid': opp['Id'],
                'name': opp.get('Name', ''),
                'notes': opp.get('Description', ''),
                'assignee': {'gid': opp.get('OwnerId')} if opp.get('OwnerId') else None,
                'stage': opp.get('StageName', ''),
                'amount': opp.get('Amount'),
                'close_date': opp.get('CloseDate')
            }
        except Exception as e:
            raise SalesforceAPIError(f"Failed to get opportunity: {e}")

    def get_project_tasks(self, project_gid: str) -> List[Dict[str, Any]]:
        """
        Get all tasks in a project (all Opportunities for an Account).

        Args:
            project_gid: Account ID

        Returns:
            List of opportunities
        """
        try:
            query = f"SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity WHERE AccountId = '{project_gid}'"
            result = self._make_request("query", data=query)

            tasks = []
            for record in result['records']:
                tasks.append({
                    'gid': record['Id'],
                    'name': record['Name'],
                    'stage': record.get('StageName', ''),
                    'amount': record.get('Amount'),
                    'close_date': record.get('CloseDate')
                })

            return tasks
        except Exception as e:
            raise SalesforceAPIError(f"Failed to get opportunities: {e}")

    def get_task_subtasks(self, task_gid: str) -> List[Dict[str, Any]]:
        """
        Get all subtasks for a task (Tasks related to Opportunity).

        Args:
            task_gid: Opportunity ID

        Returns:
            List of related tasks
        """
        try:
            query = f"SELECT Id, Subject, Status, Priority FROM Task WHERE WhatId = '{task_gid}'"
            result = self._make_request("query", data=query)

            subtasks = []
            for record in result['records']:
                subtasks.append({
                    'gid': record['Id'],
                    'name': record['Subject'],
                    'status': record.get('Status', ''),
                    'priority': record.get('Priority', '')
                })

            return subtasks
        except Exception as e:
            raise SalesforceAPIError(f"Failed to get subtasks: {e}")

    def set_task_assignee(self, task_gid: str, assignee_gid: str) -> Dict[str, Any]:
        """
        Change task assignee (Opportunity owner).

        Args:
            task_gid: Opportunity ID
            assignee_gid: New owner User ID

        Returns:
            Updated opportunity data
        """
        return self.update_task(task_gid, {'OwnerId': assignee_gid})

    # ========== COMMENT OPERATIONS ==========
    # In Salesforce: COMMENT = Task (activity) or Note or ChatterPost

    def add_comment(self, task_gid: str, text: str) -> Dict[str, Any]:
        """
        Add a comment to a task (create a Note or Chatter post).

        We create a Note for permanent comments.

        Args:
            task_gid: Opportunity ID
            text: Comment text

        Returns:
            Created note data
        """
        try:
            # Create ContentNote (newer API)
            note_data = {
                'Title': f'Comment on {task_gid[:8]}',
                'Content': text.encode('utf-8').hex()  # ContentNote requires hex encoding
            }

            # First create the ContentNote
            result = self._make_request("create", sobject="ContentNote", data=note_data)

            if result and result.get('success'):
                note_id = result['id']

                # Then link it to the Opportunity via ContentDocumentLink
                link_data = {
                    'ContentDocumentId': note_id,
                    'LinkedEntityId': task_gid,
                    'ShareType': 'V',  # Viewer permission
                    'Visibility': 'AllUsers'
                }
                self._make_request("create", sobject="ContentDocumentLink", data=link_data)

                return {
                    'gid': note_id,
                    'text': text
                }
        except Exception as e:
            # Fallback to Task (activity) if ContentNote fails
            logger.warning(f"ContentNote creation failed, using Task: {e}")

            task_data = {
                'Subject': 'Comment',
                'Description': text,
                'WhatId': task_gid,
                'Status': 'Completed',
                'ActivityDate': datetime.now().strftime('%Y-%m-%d')
            }

            result = self._make_request("create", sobject="Task", data=task_data)

            if result and result.get('success'):
                return {
                    'gid': result['id'],
                    'text': text
                }

        raise SalesforceAPIError("Failed to add comment")

    # ========== CUSTOM FIELD OPERATIONS ==========

    def create_custom_field(self, workspace_gid: str, name: str, field_type: str,
                           description: str = "", **kwargs) -> Dict[str, Any]:
        """
        Create a custom field (requires Salesforce admin permissions).

        NOTE: Custom field creation requires Metadata API, which is complex.
        This method returns a placeholder for interface compatibility.
        Use Salesforce Setup UI to create custom fields.

        Args:
            workspace_gid: Not used
            name: Field name
            field_type: Field type
            description: Field description
            **kwargs: Additional parameters

        Returns:
            Placeholder response
        """
        logger.warning(
            "Custom field creation requires Metadata API. "
            "Please create custom fields through Salesforce Setup UI."
        )

        return {
            'gid': f'custom_{name}',
            'name': name,
            'type': field_type,
            'description': description,
            'note': 'Created via Setup UI'
        }

    def add_custom_field_to_project(self, project_gid: str, custom_field_gid: str):
        """
        Add a custom field to a project (N/A in Salesforce).

        Custom fields are added to object types, not individual records.

        Args:
            project_gid: Not used
            custom_field_gid: Not used
        """
        logger.warning("Custom fields are managed at object level in Salesforce")

    def get_workspace_custom_fields(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all custom fields (requires describe call).

        Args:
            workspace_gid: Not used

        Returns:
            List of custom fields on common objects
        """
        try:
            custom_fields = []

            # Describe Account object to get custom fields
            account_desc = self.sf.Account.describe()
            for field in account_desc['fields']:
                if field['custom']:
                    custom_fields.append({
                        'gid': field['name'],
                        'name': field['label'],
                        'type': field['type'],
                        'object': 'Account'
                    })

            # Describe Opportunity object
            opp_desc = self.sf.Opportunity.describe()
            for field in opp_desc['fields']:
                if field['custom']:
                    custom_fields.append({
                        'gid': field['name'],
                        'name': field['label'],
                        'type': field['type'],
                        'object': 'Opportunity'
                    })

            return custom_fields
        except Exception as e:
            raise SalesforceAPIError(f"Failed to get custom fields: {e}")

    def delete_custom_field(self, custom_field_gid: str):
        """
        Delete a custom field (requires Metadata API).

        Use Salesforce Setup UI to delete custom fields.

        Args:
            custom_field_gid: Field name
        """
        logger.warning("Custom field deletion requires Metadata API")

    def create_custom_field_value(self, task_gid: str, custom_field_gid: str,
                                  value: Any) -> Dict[str, Any]:
        """
        Set a custom field value on a task (Opportunity).

        Args:
            task_gid: Opportunity ID
            custom_field_gid: Custom field API name
            value: Value to set

        Returns:
            Updated opportunity data
        """
        return self.update_task(task_gid, {custom_field_gid: value})

    # ========== SECTION OPERATIONS ==========
    # In Salesforce: SECTION = OpportunityStage or RecordType

    def create_section(self, project_gid: str, name: str) -> Dict[str, Any]:
        """
        Create a section (opportunity stage is predefined in Salesforce).

        Sections map to opportunity stages, which are configured in Setup.
        This method returns existing stages.

        Args:
            project_gid: Not used
            name: Stage name

        Returns:
            Stage information
        """
        # Return placeholder since stages are predefined
        return {
            'gid': f'stage_{name}',
            'name': name,
            'note': 'Opportunity stages are configured in Salesforce Setup'
        }

    def get_project_sections(self, project_gid: str) -> List[Dict[str, Any]]:
        """
        Get all sections (opportunity stages).

        Args:
            project_gid: Not used

        Returns:
            List of opportunity stages
        """
        try:
            # Get picklist values for StageName field
            opp_desc = self.sf.Opportunity.describe()

            stage_field = next(f for f in opp_desc['fields'] if f['name'] == 'StageName')

            stages = []
            for value in stage_field['picklistValues']:
                if value['active']:
                    stages.append({
                        'gid': value['value'],
                        'name': value['label']
                    })

            return stages
        except Exception as e:
            raise SalesforceAPIError(f"Failed to get opportunity stages: {e}")

    def add_task_to_section(self, task_gid: str, section_gid: str):
        """
        Move a task to a specific section (change opportunity stage).

        Args:
            task_gid: Opportunity ID
            section_gid: Stage name
        """
        self.update_task(task_gid, {'StageName': section_gid})

    # ========== TAG OPERATIONS ==========

    def create_tag(self, workspace_gid: str, name: str, **kwargs) -> Dict[str, Any]:
        """
        Create a tag (Salesforce Topics/Tags).

        Args:
            workspace_gid: Not used
            name: Tag name
            **kwargs: Not used

        Returns:
            Created tag data
        """
        try:
            # Create a Topic (tag)
            topic_data = {
                'Name': name
            }

            result = self._make_request("create", sobject="Topic", data=topic_data)

            if result and result.get('success'):
                return {
                    'gid': result['id'],
                    'name': name
                }
        except Exception as e:
            raise SalesforceAPIError(f"Failed to create tag: {e}")

    def add_tag_to_task(self, task_gid: str, tag_gid: str):
        """
        Add a tag to a task (create TopicAssignment).

        Args:
            task_gid: Opportunity ID
            tag_gid: Topic ID
        """
        try:
            assignment_data = {
                'TopicId': tag_gid,
                'EntityId': task_gid
            }

            self._make_request("create", sobject="TopicAssignment", data=assignment_data)
        except Exception as e:
            raise SalesforceAPIError(f"Failed to add tag: {e}")

    def get_workspace_tags(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all tags (Topics).

        Args:
            workspace_gid: Not used

        Returns:
            List of topics
        """
        try:
            query = "SELECT Id, Name FROM Topic ORDER BY Name LIMIT 200"
            result = self._make_request("query", data=query)

            tags = []
            for record in result['records']:
                tags.append({
                    'gid': record['Id'],
                    'name': record['Name']
                })

            return tags
        except Exception as e:
            raise SalesforceAPIError(f"Failed to get tags: {e}")

    def delete_tag(self, tag_gid: str):
        """
        Delete a tag (Topic).

        Args:
            tag_gid: Topic ID
        """
        try:
            self._make_request("delete", sobject="Topic", record_id=tag_gid)
        except Exception as e:
            raise SalesforceAPIError(f"Failed to delete tag: {e}")

    # ========== PORTFOLIO OPERATIONS ==========
    # In Salesforce: PORTFOLIO = Campaign

    def create_portfolio(self, workspace_gid: str, name: str, **kwargs) -> Dict[str, Any]:
        """
        Create a portfolio (mapped to Campaign).

        Args:
            workspace_gid: Not used
            name: Campaign name
            **kwargs: Additional campaign fields

        Returns:
            Created campaign data
        """
        campaign_data = {
            'Name': name,
            'IsActive': True,
            'Status': kwargs.get('status', 'Planned'),
            'Type': kwargs.get('type', 'Other')
        }

        if 'description' in kwargs:
            campaign_data['Description'] = kwargs['description']
        if 'start_date' in kwargs:
            campaign_data['StartDate'] = kwargs['start_date']
        if 'end_date' in kwargs:
            campaign_data['EndDate'] = kwargs['end_date']

        result = self._make_request("create", sobject="Campaign", data=campaign_data)

        if result and result.get('success'):
            return {
                'gid': result['id'],
                'name': name
            }
        else:
            raise SalesforceAPIError(f"Failed to create campaign: {result}")

    def add_project_to_portfolio(self, portfolio_gid: str, project_gid: str):
        """
        Add a project to a portfolio (link Account to Campaign).

        Creates a CampaignMember relationship.

        Args:
            portfolio_gid: Campaign ID
            project_gid: Account ID (we'll link the account's contacts)
        """
        try:
            # Get contacts from the account
            query = f"SELECT Id FROM Contact WHERE AccountId = '{project_gid}' LIMIT 10"
            result = self._make_request("query", data=query)

            # Add each contact to the campaign
            for contact in result['records']:
                member_data = {
                    'CampaignId': portfolio_gid,
                    'ContactId': contact['Id'],
                    'Status': 'Sent'
                }
                try:
                    self._make_request("create", sobject="CampaignMember", data=member_data)
                except Exception as e:
                    logger.warning(f"Could not add contact to campaign: {e}")

        except Exception as e:
            raise SalesforceAPIError(f"Failed to add account to campaign: {e}")

    def get_workspace_portfolios(self, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get all portfolios (Campaigns).

        Args:
            workspace_gid: Not used

        Returns:
            List of campaigns
        """
        try:
            query = "SELECT Id, Name, Status, Type FROM Campaign WHERE IsActive = TRUE LIMIT 200"
            result = self._make_request("query", data=query)

            portfolios = []
            for record in result['records']:
                portfolios.append({
                    'gid': record['Id'],
                    'name': record['Name'],
                    'status': record.get('Status', ''),
                    'type': record.get('Type', '')
                })

            return portfolios
        except Exception as e:
            raise SalesforceAPIError(f"Failed to get campaigns: {e}")

    def delete_portfolio(self, portfolio_gid: str):
        """
        Delete a portfolio (Campaign).

        Args:
            portfolio_gid: Campaign ID
        """
        try:
            self._make_request("delete", sobject="Campaign", record_id=portfolio_gid)
        except Exception as e:
            raise SalesforceAPIError(f"Failed to delete campaign: {e}")

    # ========== FOLLOWER OPERATIONS ==========

    def add_followers(self, task_gid: str, followers: List[str]):
        """
        Add followers to a task (Chatter followers).

        Args:
            task_gid: Opportunity ID
            followers: List of User IDs
        """
        for user_id in followers:
            try:
                follow_data = {
                    'ParentId': task_gid,
                    'SubscriberId': user_id
                }
                self._make_request("create", sobject="EntitySubscription", data=follow_data)
            except Exception as e:
                logger.warning(f"Could not add follower: {e}")

    def remove_followers(self, task_gid: str, followers: List[str]):
        """
        Remove followers from a task.

        Args:
            task_gid: Opportunity ID
            followers: List of User IDs
        """
        for user_id in followers:
            try:
                # Find the subscription
                query = f"SELECT Id FROM EntitySubscription WHERE ParentId = '{task_gid}' AND SubscriberId = '{user_id}'"
                result = self._make_request("query", data=query)

                if result['totalSize'] > 0:
                    sub_id = result['records'][0]['Id']
                    self._make_request("delete", sobject="EntitySubscription", record_id=sub_id)
            except Exception as e:
                logger.warning(f"Could not remove follower: {e}")

    # ========== DEPENDENCY OPERATIONS ==========

    def add_task_dependency(self, task_gid: str, depends_on_gid: str):
        """
        Add a dependency between tasks (not directly supported).

        We can create a Task record to document the dependency.

        Args:
            task_gid: Opportunity ID that depends on another
            depends_on_gid: Opportunity ID that must be completed first
        """
        try:
            task_data = {
                'Subject': f'Depends on {depends_on_gid}',
                'WhatId': task_gid,
                'Status': 'Not Started',
                'Priority': 'High'
            }
            self._make_request("create", sobject="Task", data=task_data)
        except Exception as e:
            logger.warning(f"Could not create dependency: {e}")

    # ========== MILESTONE OPERATIONS ==========
    # In Salesforce: MILESTONE = Contract

    def create_milestone(self, project_gid: str, name: str, due_date: str,
                        notes: str = "", assignee: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a milestone (mapped to Contract).

        Args:
            project_gid: Account ID
            name: Contract name
            due_date: End date
            notes: Contract description
            assignee: Owner User ID

        Returns:
            Created contract data
        """
        contract_data = {
            'AccountId': project_gid,
            'Status': 'Draft',
            'ContractTerm': 12,  # Default 12 months
            'StartDate': datetime.now().strftime('%Y-%m-%d')
        }

        if assignee:
            contract_data['OwnerId'] = assignee
        if notes:
            contract_data['Description'] = notes

        # Note: Contract requires specific fields based on your Salesforce config
        try:
            result = self._make_request("create", sobject="Contract", data=contract_data)

            if result and result.get('success'):
                return {
                    'gid': result['id'],
                    'name': name,
                    'due_date': due_date
                }
        except Exception as e:
            # Fallback to Opportunity with milestone flag
            logger.warning(f"Contract creation failed, using Opportunity: {e}")

            milestone_opp = self.create_task(
                project_gid=project_gid,
                name=f"Milestone: {name}",
                notes=notes,
                assignee=assignee,
                close_date=due_date,
                type='Milestone'
            )
            return milestone_opp

    # ========== SALESFORCE-SPECIFIC CRM METHODS ==========

    def create_lead(self, **kwargs) -> Dict[str, Any]:
        """
        Create a lead (prospect).

        Args:
            **kwargs: Lead fields:
                - last_name: Last name (required)
                - first_name: First name
                - company: Company name (required)
                - email: Email address
                - phone: Phone number
                - status: Lead status (default: 'Open - Not Contacted')
                - lead_source: Lead source

        Returns:
            Created lead data
        """
        if 'last_name' not in kwargs or 'company' not in kwargs:
            raise SalesforceAPIError("last_name and company are required for leads")

        lead_data = {
            'LastName': kwargs['last_name'],
            'Company': kwargs['company'],
            'Status': kwargs.get('status', 'Open - Not Contacted')
        }

        if 'first_name' in kwargs:
            lead_data['FirstName'] = kwargs['first_name']
        if 'email' in kwargs:
            lead_data['Email'] = kwargs['email']
        if 'phone' in kwargs:
            lead_data['Phone'] = kwargs['phone']
        if 'lead_source' in kwargs:
            lead_data['LeadSource'] = kwargs['lead_source']

        result = self._make_request("create", sobject="Lead", data=lead_data)

        if result and result.get('success'):
            return {
                'gid': result['id'],
                'id': result['id'],
                'name': f"{kwargs.get('first_name', '')} {kwargs['last_name']}".strip(),
                'company': kwargs['company']
            }
        else:
            raise SalesforceAPIError(f"Failed to create lead: {result}")

    def convert_lead(self, lead_id: str, **kwargs) -> Dict[str, Any]:
        """
        Convert a lead to Account, Contact, and Opportunity.

        Args:
            lead_id: Lead ID to convert
            **kwargs: Conversion parameters:
                - account_id: Existing Account ID (optional)
                - contact_id: Existing Contact ID (optional)
                - create_opportunity: Whether to create opportunity (default: True)
                - opportunity_name: Opportunity name

        Returns:
            Conversion result with Account, Contact, Opportunity IDs
        """
        # Lead conversion requires complex API call
        # Using SOAP API would be ideal, but we'll use a workaround with REST

        try:
            # Get lead details
            lead = self._make_request("get", sobject="Lead", record_id=lead_id)

            # Create Account if not provided
            account_id = kwargs.get('account_id')
            if not account_id:
                account_result = self._make_request("create", sobject="Account", data={
                    'Name': lead['Company']
                })
                account_id = account_result['id']

            # Create Contact if not provided
            contact_id = kwargs.get('contact_id')
            if not contact_id:
                contact_result = self._make_request("create", sobject="Contact", data={
                    'LastName': lead['LastName'],
                    'FirstName': lead.get('FirstName', ''),
                    'Email': lead.get('Email'),
                    'Phone': lead.get('Phone'),
                    'AccountId': account_id
                })
                contact_id = contact_result['id']

            # Create Opportunity if requested
            opportunity_id = None
            if kwargs.get('create_opportunity', True):
                opp_name = kwargs.get('opportunity_name', f"{lead['Company']} - Opportunity")
                opp_result = self._make_request("create", sobject="Opportunity", data={
                    'Name': opp_name,
                    'AccountId': account_id,
                    'StageName': 'Prospecting',
                    'CloseDate': kwargs.get('close_date',
                                          (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
                })
                opportunity_id = opp_result['id']

            # Update Lead status to converted
            self._make_request("update", sobject="Lead", record_id=lead_id, data={
                'Status': 'Closed - Converted'
            })

            return {
                'lead_id': lead_id,
                'account_id': account_id,
                'contact_id': contact_id,
                'opportunity_id': opportunity_id
            }

        except Exception as e:
            raise SalesforceAPIError(f"Failed to convert lead: {e}")

    def create_opportunity(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """
        Create an opportunity for an account.

        Args:
            account_id: Account ID
            **kwargs: Opportunity fields (see create_task for details)

        Returns:
            Created opportunity data
        """
        return self.create_task(
            project_gid=account_id,
            name=kwargs.get('name', 'New Opportunity'),
            notes=kwargs.get('notes', ''),
            assignee=kwargs.get('assignee'),
            **kwargs
        )

    def update_opportunity_stage(self, opp_id: str, stage: str) -> Dict[str, Any]:
        """
        Update opportunity stage.

        Args:
            opp_id: Opportunity ID
            stage: New stage name

        Returns:
            Updated opportunity data
        """
        return self.update_task(opp_id, {'StageName': stage})

    def create_case(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """
        Create a support case for an account.

        Args:
            account_id: Account ID
            **kwargs: Case fields:
                - subject: Case subject (required)
                - description: Case description
                - priority: Priority (Low, Medium, High)
                - status: Status (default: 'New')
                - origin: Case origin (Web, Phone, Email, etc.)

        Returns:
            Created case data
        """
        if 'subject' not in kwargs:
            raise SalesforceAPIError("subject is required for cases")

        case_data = {
            'AccountId': account_id,
            'Subject': kwargs['subject'],
            'Status': kwargs.get('status', 'New'),
            'Priority': kwargs.get('priority', 'Medium'),
            'Origin': kwargs.get('origin', 'Web')
        }

        if 'description' in kwargs:
            case_data['Description'] = kwargs['description']
        if 'contact_id' in kwargs:
            case_data['ContactId'] = kwargs['contact_id']

        result = self._make_request("create", sobject="Case", data=case_data)

        if result and result.get('success'):
            return {
                'gid': result['id'],
                'id': result['id'],
                'subject': kwargs['subject'],
                'status': case_data['Status']
            }
        else:
            raise SalesforceAPIError(f"Failed to create case: {result}")

    def close_case(self, case_id: str, **kwargs) -> Dict[str, Any]:
        """
        Close a support case.

        Args:
            case_id: Case ID
            **kwargs: Additional fields:
                - status: Close status (default: 'Closed')
                - resolution: Resolution notes

        Returns:
            Updated case data
        """
        case_updates = {
            'Status': kwargs.get('status', 'Closed')
        }

        if 'resolution' in kwargs:
            case_updates['Resolution__c'] = kwargs['resolution']

        result = self._make_request("update", sobject="Case",
                                   record_id=case_id, data=case_updates)

        return {'success': True, 'case_id': case_id}

    def create_contact(self, account_id: str, **kwargs) -> Dict[str, Any]:
        """
        Create a contact for an account.

        Args:
            account_id: Account ID
            **kwargs: Contact fields:
                - last_name: Last name (required)
                - first_name: First name
                - email: Email address
                - phone: Phone number
                - title: Job title

        Returns:
            Created contact data
        """
        if 'last_name' not in kwargs:
            raise SalesforceAPIError("last_name is required for contacts")

        contact_data = {
            'AccountId': account_id,
            'LastName': kwargs['last_name']
        }

        if 'first_name' in kwargs:
            contact_data['FirstName'] = kwargs['first_name']
        if 'email' in kwargs:
            contact_data['Email'] = kwargs['email']
        if 'phone' in kwargs:
            contact_data['Phone'] = kwargs['phone']
        if 'title' in kwargs:
            contact_data['Title'] = kwargs['title']

        result = self._make_request("create", sobject="Contact", data=contact_data)

        if result and result.get('success'):
            return {
                'gid': result['id'],
                'id': result['id'],
                'name': f"{kwargs.get('first_name', '')} {kwargs['last_name']}".strip(),
                'email': kwargs.get('email')
            }
        else:
            raise SalesforceAPIError(f"Failed to create contact: {result}")

    def log_activity(self, related_to_id: str, **kwargs) -> Dict[str, Any]:
        """
        Log an activity (Task) related to a record.

        Args:
            related_to_id: Record ID (Account, Opportunity, etc.)
            **kwargs: Activity fields:
                - subject: Activity subject (required)
                - description: Activity description
                - status: Status (default: 'Completed')
                - activity_date: Activity date (default: today)
                - type: Activity type (Call, Email, Meeting)

        Returns:
            Created task data
        """
        if 'subject' not in kwargs:
            raise SalesforceAPIError("subject is required for activities")

        task_data = {
            'WhatId': related_to_id,
            'Subject': kwargs['subject'],
            'Status': kwargs.get('status', 'Completed'),
            'ActivityDate': kwargs.get('activity_date', datetime.now().strftime('%Y-%m-%d'))
        }

        if 'description' in kwargs:
            task_data['Description'] = kwargs['description']
        if 'type' in kwargs:
            task_data['Type'] = kwargs['type']

        result = self._make_request("create", sobject="Task", data=task_data)

        if result and result.get('success'):
            return {
                'gid': result['id'],
                'id': result['id'],
                'subject': kwargs['subject'],
                'status': task_data['Status']
            }
        else:
            raise SalesforceAPIError(f"Failed to log activity: {result}")

    def execute_soql(self, query: str) -> Dict[str, Any]:
        """
        Execute a SOQL query.

        Args:
            query: SOQL query string

        Returns:
            Query results
        """
        try:
            return self._make_request("query", data=query)
        except Exception as e:
            raise SalesforceAPIError(f"SOQL query failed: {e}")

    def get_api_usage(self) -> Dict[str, Any]:
        """
        Get current API usage statistics.

        Returns:
            Dictionary with usage information
        """
        self._update_api_usage()

        return {
            'daily_limit': self.api_usage_limit,
            'used': self.api_usage_used,
            'remaining': self.api_usage_limit - self.api_usage_used if self.api_usage_limit else None,
            'percentage_used': (self.api_usage_used / self.api_usage_limit * 100) if self.api_usage_limit else None
        }


class SalesforceClientPool(BaseClientPool):
    """
    Pool of Salesforce clients for multi-user simulation.

    Manages multiple Salesforce connections with different credentials.
    """

    def __init__(self, user_credentials: Dict[str, Dict[str, str]]):
        """
        Initialize client pool.

        Args:
            user_credentials: Dictionary mapping user names to credential dictionaries:
                {
                    'user1': {
                        'username': 'user1@company.com',
                        'password': 'password',
                        'security_token': 'token',
                        'instance_url': 'https://na1.salesforce.com',
                        'domain': 'login'
                    },
                    ...
                }
        """
        super().__init__({})  # Pass empty dict since we don't use api_key

        for user_name, credentials in user_credentials.items():
            try:
                client = SalesforceConnection(
                    api_key='',  # Not used
                    user_name=user_name,
                    username=credentials.get('username'),
                    password=credentials.get('password'),
                    security_token=credentials.get('security_token'),
                    instance_url=credentials.get('instance_url'),
                    domain=credentials.get('domain', 'login')
                )

                # Validate connection
                if client.validate_token():
                    self.clients[user_name] = client
                    # Cache user GID
                    user_info = client.get_user_info()
                    self.user_gids[user_name] = user_info.get('gid')
                    logger.info(f"✓ Initialized Salesforce client for {user_name}")
                else:
                    logger.error(f"✗ Invalid credentials for {user_name}")

            except Exception as e:
                logger.error(f"✗ Error initializing client for {user_name}: {e}")

    def get_client(self, user_name: str) -> Optional[SalesforceConnection]:
        """
        Get client for a specific user.

        Args:
            user_name: User name

        Returns:
            SalesforceConnection or None if not found/invalid
        """
        client = self.clients.get(user_name)
        if client and not client.is_valid:
            logger.warning(f"⚠ Credentials for {user_name} are no longer valid")
            return None
        return client

    def get_random_client(self) -> Optional[SalesforceConnection]:
        """
        Get a random valid client from the pool.

        Returns:
            Random SalesforceConnection or None if no valid clients
        """
        import random
        valid_clients = [c for c in self.clients.values() if c.is_valid]
        return random.choice(valid_clients) if valid_clients else None

    def get_valid_clients(self) -> List[SalesforceConnection]:
        """
        Get all valid clients.

        Returns:
            List of valid SalesforceConnections
        """
        return [c for c in self.clients.values() if c.is_valid]

    def get_valid_user_names(self) -> List[str]:
        """
        Get names of all users with valid credentials.

        Returns:
            List of user names
        """
        return [name for name, client in self.clients.items() if client.is_valid]

    def get_user_gid(self, user_name: str) -> Optional[str]:
        """
        Get the Salesforce user ID for a given user name.

        Args:
            user_name: User name

        Returns:
            User ID or None if not found
        """
        return self.user_gids.get(user_name)

    def get_total_api_usage(self) -> Dict[str, Any]:
        """
        Get total API usage across all clients.

        Returns:
            Dictionary with aggregated usage statistics
        """
        total_used = 0
        total_limit = 0

        for client in self.clients.values():
            usage = client.get_api_usage()
            if usage['daily_limit']:
                total_limit += usage['daily_limit']
                total_used += usage['used']

        return {
            'total_limit': total_limit,
            'total_used': total_used,
            'total_remaining': total_limit - total_used,
            'percentage_used': (total_used / total_limit * 100) if total_limit else 0,
            'clients': len(self.clients)
        }


# Example usage
if __name__ == "__main__":
    import sys

    print("Salesforce Connection Module")
    print("=" * 50)
    print("\nThis module maps project management concepts to Salesforce CRM:")
    print("  - Project → Account (customer/company)")
    print("  - Task → Opportunity (sales opportunity)")
    print("  - Subtask → OpportunityLineItem or Contact")
    print("  - Comment → Task/Note/ChatterPost")
    print("  - Section → OpportunityStage")
    print("  - Tag → Tag/Topic")
    print("  - Portfolio → Campaign")
    print("  - Milestone → Contract")
    print("\n" + "=" * 50)

    if len(sys.argv) < 4:
        print("\nUsage: python salesforce_connection.py <USERNAME> <PASSWORD> <SECURITY_TOKEN>")
        print("\nExample:")
        print("  python salesforce_connection.py user@company.com myPassword abc123token")
        sys.exit(1)

    # Test single client
    username = sys.argv[1]
    password = sys.argv[2]
    security_token = sys.argv[3]

    print(f"\nTesting Salesforce Connection for {username}...")

    try:
        client = SalesforceConnection(
            api_key='',
            user_name="Test User",
            username=username,
            password=password,
            security_token=security_token,
            domain='login'  # Use 'test' for sandbox
        )

        # Validate connection
        if client.validate_token():
            print("✓ Connection is valid")

            # Get user info
            user = client.get_user_info()
            print(f"✓ User: {user['name']} ({user['email']})")

            # Get API usage
            usage = client.get_api_usage()
            print(f"✓ API Usage: {usage['used']}/{usage['daily_limit']} ({usage['percentage_used']:.1f}%)")

            # Test querying accounts
            print("\nTesting SOQL query...")
            result = client.execute_soql("SELECT Id, Name FROM Account LIMIT 5")
            print(f"✓ Found {result['totalSize']} accounts")
            for account in result['records']:
                print(f"  - {account['Name']} ({account['Id']})")

        else:
            print("✗ Connection is invalid")

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
