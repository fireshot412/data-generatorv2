#!/usr/bin/env python3
"""
Okta Continuous Generation Service - Okta-specific implementation of continuous data generation.

Simulates realistic organizational activity including:
- User lifecycle management (hiring, offboarding, transfers)
- Group management (departments, teams, roles)
- Application provisioning and de-provisioning
- Profile updates and organizational changes
"""

import asyncio
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from continuous.services.base_service import BaseService
from continuous.llm_generator import LLMGenerator
from continuous.state_manager import StateManager
from continuous.scheduler import ActivityScheduler, ActivityType
from continuous.connections.okta_connection import (
    OktaClientPool, OktaConnection, OktaAPIError, OktaRateLimitError
)
from continuous.templates.okta_templates import (
    INDUSTRY_TEMPLATES,
    ORG_SIZE_TEMPLATES,
    GROUP_STRUCTURE_TEMPLATES,
    USER_PROFILE_TEMPLATES,
    COMMON_APPS,
    get_industry_config,
    get_org_size_config,
    get_departments_for_industry,
    get_apps_for_industry,
    get_user_titles_for_department,
    get_app_assignment_pattern,
    calculate_user_distribution,
    generate_sample_user_profile
)


class OktaActivityType:
    """Okta-specific activity types."""
    CREATE_USER = "create_user"
    DEACTIVATE_USER = "deactivate_user"
    REACTIVATE_USER = "reactivate_user"
    UPDATE_USER_PROFILE = "update_user_profile"
    ASSIGN_USER_TO_GROUP = "assign_user_to_group"
    REMOVE_USER_FROM_GROUP = "remove_user_from_group"
    ASSIGN_APP_TO_USER = "assign_app_to_user"
    UNASSIGN_APP_FROM_USER = "unassign_app_from_user"
    CREATE_GROUP = "create_group"
    DELETE_GROUP = "delete_group"
    SUSPEND_USER = "suspend_user"
    UNSUSPEND_USER = "unsuspend_user"
    PASSWORD_RESET = "password_reset"
    MFA_ENROLLMENT = "mfa_enrollment"


class OktaService(BaseService):
    """
    Okta-specific implementation of continuous data generation service.

    Generates realistic organizational activity patterns including user lifecycle,
    group management, and application provisioning.
    """

    def __init__(self, config: Dict[str, Any], state_manager: StateManager,
                 llm_generator: Optional[LLMGenerator] = None,
                 client_pool: Optional[OktaClientPool] = None):
        """
        Initialize Okta continuous service.

        Args:
            config: Job configuration containing:
                - industry: Industry type (healthcare, finance, technology, etc.)
                - org_size: Organization size (startup, midsize, enterprise)
                - initial_users: Number of users to create initially
                - activity_level: low, medium, or high
                - duration_days: Number of days to run or "indefinite"
            state_manager: State manager instance
            llm_generator: Optional LLM generator instance for content generation
            client_pool: Optional pool of Okta clients (created if not provided)
        """
        # Create client pool if not provided
        if client_pool is None:
            client_pool = OktaClientPool(config.get("user_tokens", []))

        super().__init__(config, state_manager, llm_generator, client_pool)

        # Okta-specific configuration
        self.industry = config.get("industry", "technology")
        self.org_size = config.get("org_size", "midsize")
        self.initial_users = config.get("initial_users", 50)

        # Load templates
        self.industry_config = get_industry_config(self.industry)
        self.org_config = get_org_size_config(self.org_size)

        # Cache for Okta objects
        self.app_catalog = {}  # {app_name: app_id} - Maps app names to Okta app IDs
        self.managers = []  # List of manager user IDs

        # Activity weights for different operations
        self.activity_weights = self._calculate_activity_weights()

        print(f"✓ Okta service initialized - Job ID: {self.job_id}")
        print(f"  Industry: {self.industry}, Org Size: {self.org_size}")
        print(f"  Initial Users: {self.initial_users}")

    def _calculate_activity_weights(self) -> Dict[str, int]:
        """
        Calculate activity weights based on org size and configuration.

        Returns:
            Dictionary of activity types with their relative weights
        """
        # Base weights that can be adjusted by org size
        base_weights = {
            OktaActivityType.CREATE_USER: 30,           # New hires
            OktaActivityType.DEACTIVATE_USER: 10,       # Offboarding
            OktaActivityType.UPDATE_USER_PROFILE: 20,   # Profile changes
            OktaActivityType.ASSIGN_USER_TO_GROUP: 15,  # Group additions
            OktaActivityType.REMOVE_USER_FROM_GROUP: 5, # Group removals
            OktaActivityType.ASSIGN_APP_TO_USER: 15,    # App provisioning
            OktaActivityType.UNASSIGN_APP_FROM_USER: 3, # App de-provisioning
            OktaActivityType.CREATE_GROUP: 3,           # New teams
            OktaActivityType.DELETE_GROUP: 1,           # Team dissolution
            OktaActivityType.SUSPEND_USER: 2,           # Temporary suspension
            OktaActivityType.UNSUSPEND_USER: 2,         # Reactivation
            OktaActivityType.PASSWORD_RESET: 5,         # Password resets
            OktaActivityType.MFA_ENROLLMENT: 3,         # MFA setup
        }

        # Adjust weights based on org size
        if self.org_size == "startup":
            # Startups have more hiring, less bureaucracy
            base_weights[OktaActivityType.CREATE_USER] = 40
            base_weights[OktaActivityType.CREATE_GROUP] = 5
        elif self.org_size == "enterprise":
            # Enterprises have more profile updates, group changes
            base_weights[OktaActivityType.UPDATE_USER_PROFILE] = 30
            base_weights[OktaActivityType.ASSIGN_USER_TO_GROUP] = 20

        return base_weights

    async def run(self):
        """Main loop - runs continuously until stopped."""
        self.running = True

        # Check if we need initial setup
        initial_generation = len(self.state.get("groups", {})) == 0

        if initial_generation:
            self.state_manager.update_job_status(self.job_id, "initializing")
            print(f"Initializing Okta organization for {self.industry}...")
            await self._initialize_organization()
            self.state_manager.update_job_status(self.job_id, "running")
            print("✓ Initial organization setup complete")
        else:
            self.state_manager.update_job_status(self.job_id, "running")
            print("Resuming Okta activity generation...")

        # Main activity loop
        while self.running and self._should_continue():
            try:
                if self.paused:
                    await asyncio.sleep(60)
                    continue

                # Check for deletion marker
                if not self.deleted:
                    disk_state = self.state_manager.load_state(self.job_id)
                    if disk_state is None or disk_state.get("_deleting"):
                        print(f"[Job {self.job_id}] Deletion marker detected - exiting")
                        self.running = False
                        self.deleted = True
                        return

                    if disk_state.get("status") == "stopped":
                        print(f"[Job {self.job_id}] Job stopped - exiting")
                        self.running = False
                        return

                    self.state = disk_state

                # Check if it's time for activity
                current_time = datetime.now(timezone.utc)

                if self.scheduler.should_generate_activity(current_time):
                    await self._generate_activity()

                    # Update next activity time
                    next_time = self.scheduler.get_next_activity_time(current_time)
                    self.state_manager.update_next_activity_time(self.job_id, next_time.isoformat())
                else:
                    # Update next activity time if not set
                    if not self.state.get("next_activity_time"):
                        next_time = self.scheduler.get_next_activity_time(current_time)
                        self.state_manager.update_next_activity_time(self.job_id, next_time.isoformat())

                # Sleep before next check
                await asyncio.sleep(random.randint(30, 90))

            except OktaRateLimitError as e:
                print(f"⚠ Rate limit hit: {e}")
                self.state_manager.log_error(self.job_id, "rate_limit", str(e))
                # Pause for an hour
                await asyncio.sleep(3600)

            except Exception as e:
                print(f"✗ Error in main loop: {e}")
                self.state_manager.log_error(self.job_id, "general", str(e))
                await asyncio.sleep(300)  # 5 minutes before retry

        # Clean shutdown
        self.state_manager.update_job_status(self.job_id, "stopped")
        print(f"Okta generation stopped for job {self.job_id}")

    async def _initialize_organization(self):
        """
        Initialize organization with groups, users, and app assignments.
        Creates the foundational structure for ongoing activity generation.
        """
        print("Setting up organizational structure...")

        # Initialize state structure if needed
        if "groups" not in self.state:
            self.state["groups"] = {}
        if "users" not in self.state:
            self.state["users"] = {}
        if "app_assignments" not in self.state:
            self.state["app_assignments"] = {}
        if "activity_log" not in self.state:
            self.state["activity_log"] = []

        # Step 1: Create organizational groups
        await self._create_organizational_groups()

        # Step 2: Create initial users
        await self._create_initial_users()

        # Step 3: Assign users to groups
        await self._assign_users_to_groups()

        # Step 4: Discover and cache available apps
        await self._discover_apps()

        # Step 5: Assign apps to users based on department/role
        await self._assign_initial_apps()

        # Save state
        self.state_manager.save_state(self.job_id, self.state)

        print(f"✓ Created {len(self.state['groups'])} groups")
        print(f"✓ Created {len(self.state['users'])} users")
        print(f"✓ Created {len(self.state['app_assignments'])} app assignments")

    async def _create_organizational_groups(self):
        """Create department, team, and role-based groups."""
        client = self.client_pool.get_random_client()

        # Get departments from template
        departments = get_departments_for_industry(self.industry)

        # Create "All Employees" group
        try:
            all_employees = await asyncio.to_thread(
                client.create_group,
                name="All Employees",
                description="All employees in the organization"
            )
            if all_employees:
                self.state["groups"][all_employees["id"]] = {
                    "id": all_employees["id"],
                    "name": "All Employees",
                    "type": "all_employees",
                    "description": all_employees.get("description"),
                    "member_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": client.user_name
                }
                print(f"  Created group: All Employees")
        except Exception as e:
            print(f"  Error creating All Employees group: {e}")

        # Create department groups
        for dept in departments:
            try:
                # Use LLM to generate better group descriptions if available
                if self.llm_generator:
                    group_name = self.llm_generator.generate_group_name(
                        industry=self.industry,
                        department=dept,
                        group_type="department"
                    )
                    description = self.llm_generator.generate_group_description(
                        industry=self.industry,
                        group_name=group_name,
                        group_type="department"
                    )
                else:
                    group_name = f"{dept} Department"
                    description = f"Members of the {dept} department"

                group = await asyncio.to_thread(
                    client.create_group,
                    name=group_name,
                    description=description
                )
                if group:
                    self.state["groups"][group["id"]] = {
                        "id": group["id"],
                        "name": group_name,
                        "type": "department",
                        "department": dept,
                        "description": group.get("description"),
                        "member_count": 0,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "created_by": client.user_name
                    }
                    print(f"  Created department group: {dept}")

                await asyncio.sleep(0.5)  # Rate limit protection
            except Exception as e:
                print(f"  Error creating {dept} group: {e}")

        # Create role-based groups if org size supports it
        if self.org_config.get("has_complex_hierarchy"):
            role_groups = ["Managers", "Senior Engineers", "Directors", "Contractors"]
            for role in role_groups:
                try:
                    group = await asyncio.to_thread(
                        client.create_group,
                        name=role,
                        description=f"All {role.lower()} in the organization"
                    )
                    if group:
                        self.state["groups"][group["id"]] = {
                            "id": group["id"],
                            "name": role,
                            "type": "role",
                            "description": group.get("description"),
                            "member_count": 0,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "created_by": client.user_name
                        }
                        print(f"  Created role group: {role}")

                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  Error creating {role} group: {e}")

    async def _create_initial_users(self):
        """Create initial batch of users with realistic profiles."""
        print(f"Creating {self.initial_users} initial users...")

        departments = get_departments_for_industry(self.industry)
        roles = get_roles_for_industry(self.industry)
        locations = self.org_config.get("locations", ["Remote"])

        # Calculate user distribution across departments
        users_per_dept = self.initial_users // len(departments)
        remainder = self.initial_users % len(departments)

        user_count = 0

        for dept_idx, dept in enumerate(departments):
            # Add remainder users to first departments
            dept_users = users_per_dept + (1 if dept_idx < remainder else 0)

            for i in range(dept_users):
                try:
                    # Generate user profile
                    first_name = self._generate_first_name()
                    last_name = self._generate_last_name()
                    email = f"{first_name.lower()}.{last_name.lower()}@{self.industry.lower()}.example.com"

                    # Select appropriate role
                    is_manager = random.random() < self.org_config.get("executive_ratio", 0.1)
                    if is_manager:
                        title = random.choice(["Manager", "Director", "VP", "Senior Manager"])
                        title = f"{title} of {dept}"
                    else:
                        # Get department-appropriate role
                        dept_roles = [r for r in roles if dept.lower() in r.lower() or "specialist" in r.lower()]
                        if not dept_roles:
                            dept_roles = ["Specialist", "Analyst", "Associate", "Coordinator"]
                        title = random.choice(dept_roles)

                    profile = {
                        "firstName": first_name,
                        "lastName": last_name,
                        "email": email,
                        "login": email,
                        "department": dept,
                        "title": title,
                        "employeeNumber": f"EMP{str(user_count + 1000).zfill(5)}",
                        "location": random.choice(locations),
                        "startDate": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 1095))).isoformat()
                    }

                    # Use random client from pool
                    client = self.client_pool.get_random_client()

                    # Create user
                    user = await asyncio.to_thread(
                        client.create_user,
                        profile=profile,
                        activate=True
                    )

                    if user:
                        self.state["users"][user["id"]] = {
                            "id": user["id"],
                            "profile": profile,
                            "status": "ACTIVE",
                            "groups": [],
                            "apps": [],
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "created_by": client.user_name
                        }

                        # Track managers
                        if is_manager:
                            self.managers.append(user["id"])

                        user_count += 1

                        if user_count % 10 == 0:
                            print(f"  Created {user_count}/{self.initial_users} users")

                    await asyncio.sleep(0.2)  # Rate limit protection

                except Exception as e:
                    print(f"  Error creating user {user_count + 1}: {e}")

        print(f"✓ Created {user_count} users")

    async def _assign_users_to_groups(self):
        """Assign users to appropriate groups based on their profiles."""
        print("Assigning users to groups...")

        # Get "All Employees" group
        all_employees_group = None
        for group_id, group in self.state["groups"].items():
            if group["type"] == "all_employees":
                all_employees_group = group_id
                break

        assignment_count = 0

        for user_id, user in self.state["users"].items():
            profile = user["profile"]

            # Assign to "All Employees"
            if all_employees_group:
                try:
                    client = self.client_pool.get_random_client()
                    success = await asyncio.to_thread(
                        client.add_user_to_group,
                        user_id=user_id,
                        group_id=all_employees_group
                    )
                    if success:
                        user["groups"].append(all_employees_group)
                        self.state["groups"][all_employees_group]["member_count"] += 1
                        assignment_count += 1
                except Exception as e:
                    print(f"  Error adding user to All Employees: {e}")

            # Assign to department group
            dept = profile.get("department")
            if dept:
                for group_id, group in self.state["groups"].items():
                    if group["type"] == "department" and group.get("department") == dept:
                        try:
                            client = self.client_pool.get_random_client()
                            success = await asyncio.to_thread(
                                client.add_user_to_group,
                                user_id=user_id,
                                group_id=group_id
                            )
                            if success:
                                user["groups"].append(group_id)
                                self.state["groups"][group_id]["member_count"] += 1
                                assignment_count += 1
                        except Exception as e:
                            print(f"  Error adding user to {dept}: {e}")
                        break

            # Assign to role-based groups
            title = profile.get("title", "").lower()
            if "manager" in title or "director" in title or "vp" in title:
                for group_id, group in self.state["groups"].items():
                    if group["type"] == "role" and group["name"] == "Managers":
                        try:
                            client = self.client_pool.get_random_client()
                            success = await asyncio.to_thread(
                                client.add_user_to_group,
                                user_id=user_id,
                                group_id=group_id
                            )
                            if success:
                                user["groups"].append(group_id)
                                self.state["groups"][group_id]["member_count"] += 1
                                assignment_count += 1
                        except Exception as e:
                            print(f"  Error adding manager to role group: {e}")
                        break

            await asyncio.sleep(0.1)  # Rate limit protection

        print(f"✓ Created {assignment_count} group assignments")

    async def _discover_apps(self):
        """Discover and cache available apps in the Okta org."""
        print("Discovering available applications...")

        client = self.client_pool.get_random_client()

        try:
            # List all apps in the org
            apps = await asyncio.to_thread(client.list_apps, limit=200)

            if apps:
                for app in apps:
                    # Cache app by name for easy lookup
                    app_name = app.get("label", app.get("name", ""))
                    if app_name:
                        self.app_catalog[app_name] = app["id"]

                print(f"✓ Discovered {len(self.app_catalog)} applications")
            else:
                print("  No applications found in org")

        except Exception as e:
            print(f"  Error discovering apps: {e}")

    async def _assign_initial_apps(self):
        """Assign apps to users based on department and role."""
        print("Assigning applications to users...")

        # Get app assignment patterns from templates
        universal_apps = ["Slack", "Zoom", "Microsoft 365", "Google Workspace"]
        department_apps = self._get_department_apps()

        assignment_count = 0

        for user_id, user in self.state["users"].items():
            profile = user["profile"]
            dept = profile.get("department", "")
            title = profile.get("title", "").lower()

            apps_to_assign = []

            # Assign universal apps (everyone gets these)
            for app_name in universal_apps:
                if app_name in self.app_catalog:
                    apps_to_assign.append((app_name, self.app_catalog[app_name]))

            # Assign department-specific apps
            if dept in department_apps:
                dept_specific = department_apps[dept]
                for app_name in dept_specific:
                    if app_name in self.app_catalog:
                        apps_to_assign.append((app_name, self.app_catalog[app_name]))

            # Assign role-specific apps
            if "manager" in title or "director" in title:
                manager_apps = ["Workday", "Tableau", "Power BI"]
                for app_name in manager_apps:
                    if app_name in self.app_catalog:
                        apps_to_assign.append((app_name, self.app_catalog[app_name]))

            # Create assignments
            for app_name, app_id in apps_to_assign[:5]:  # Limit to 5 apps initially
                try:
                    client = self.client_pool.get_random_client()
                    assignment = await asyncio.to_thread(
                        client.assign_user_to_app,
                        user_id=user_id,
                        app_id=app_id
                    )

                    if assignment:
                        assignment_id = f"{app_id}_{user_id}"
                        self.state["app_assignments"][assignment_id] = {
                            "app_id": app_id,
                            "app_name": app_name,
                            "user_id": user_id,
                            "assigned_at": datetime.now(timezone.utc).isoformat(),
                            "assigned_by": client.user_name
                        }
                        user["apps"].append(app_id)
                        assignment_count += 1

                except Exception as e:
                    # Silently skip if app assignment fails
                    pass

            await asyncio.sleep(0.2)  # Rate limit protection

        print(f"✓ Created {assignment_count} app assignments")

    def _get_department_apps(self) -> Dict[str, List[str]]:
        """Get department-specific apps based on industry."""
        # Map departments to typical apps
        dept_apps = {
            "Engineering": ["GitHub", "Jira", "AWS", "DataDog", "PagerDuty"],
            "Sales": ["Salesforce", "HubSpot", "LinkedIn Sales Navigator", "Gong"],
            "Marketing": ["HubSpot", "Google Analytics", "Mailchimp", "Hootsuite"],
            "Finance": ["QuickBooks", "NetSuite", "Expensify", "Bill.com"],
            "HR": ["Workday", "BambooHR", "Greenhouse", "Culture Amp"],
            "IT": ["Okta Admin", "Jamf", "ServiceNow", "1Password"],
            "Product": ["Jira", "Figma", "Confluence", "ProductBoard"],
            "Customer Success": ["Zendesk", "Intercom", "Gainsight", "ChurnZero"],
            "Legal": ["DocuSign", "ContractWorks", "LexisNexis"],
            "Operations": ["Monday.com", "Asana", "Airtable", "Zapier"]
        }

        # Add industry-specific apps
        if self.industry == "healthcare":
            dept_apps["Clinical"] = ["Epic EMR", "Cerner", "MEDITECH"]
        elif self.industry == "finance":
            dept_apps["Trading"] = ["Bloomberg Terminal", "Reuters Eikon"]

        return dept_apps

    async def _generate_activity(self):
        """Generate a single activity based on current state and weights."""
        # Select activity type based on weights
        activity_type = self._select_activity_type()

        try:
            if activity_type == OktaActivityType.CREATE_USER:
                await self._handle_create_user()
            elif activity_type == OktaActivityType.DEACTIVATE_USER:
                await self._handle_deactivate_user()
            elif activity_type == OktaActivityType.UPDATE_USER_PROFILE:
                await self._handle_update_user()
            elif activity_type == OktaActivityType.ASSIGN_USER_TO_GROUP:
                await self._handle_assign_to_group()
            elif activity_type == OktaActivityType.REMOVE_USER_FROM_GROUP:
                await self._handle_remove_from_group()
            elif activity_type == OktaActivityType.ASSIGN_APP_TO_USER:
                await self._handle_assign_app()
            elif activity_type == OktaActivityType.UNASSIGN_APP_FROM_USER:
                await self._handle_unassign_app()
            elif activity_type == OktaActivityType.CREATE_GROUP:
                await self._handle_create_group()
            elif activity_type == OktaActivityType.DELETE_GROUP:
                await self._handle_delete_group()
            elif activity_type == OktaActivityType.SUSPEND_USER:
                await self._handle_suspend_user()
            elif activity_type == OktaActivityType.UNSUSPEND_USER:
                await self._handle_unsuspend_user()
            elif activity_type == OktaActivityType.PASSWORD_RESET:
                await self._handle_password_reset()
            elif activity_type == OktaActivityType.MFA_ENROLLMENT:
                await self._handle_mfa_enrollment()

            # Log activity
            self._log_activity(activity_type, "success")

            # Save state after each activity
            if not self.deleted:
                self.state_manager.save_state(self.job_id, self.state)

        except Exception as e:
            print(f"Error generating {activity_type}: {e}")
            self._log_activity(activity_type, "failed", str(e))

    def _select_activity_type(self) -> str:
        """Select activity type based on weights and current state."""
        # Build weighted list
        choices = []
        weights = []

        for activity, weight in self.activity_weights.items():
            # Adjust weights based on current state
            if activity == OktaActivityType.DEACTIVATE_USER:
                # Only if we have active users
                active_users = [u for u in self.state["users"].values() if u["status"] == "ACTIVE"]
                if len(active_users) < 10:
                    weight = 0  # Don't deactivate if too few users
            elif activity == OktaActivityType.DELETE_GROUP:
                # Only if we have enough groups
                if len(self.state["groups"]) < 10:
                    weight = 0
            elif activity == OktaActivityType.UNSUSPEND_USER:
                # Only if we have suspended users
                suspended_users = [u for u in self.state["users"].values() if u["status"] == "SUSPENDED"]
                if not suspended_users:
                    weight = 0

            if weight > 0:
                choices.append(activity)
                weights.append(weight)

        if not choices:
            # Default to creating a user if no other activities available
            return OktaActivityType.CREATE_USER

        return random.choices(choices, weights=weights)[0]

    async def _handle_create_user(self):
        """Handle new user creation (hiring)."""
        departments = get_departments_for_industry(self.industry)
        locations = self.org_config.get("locations", ["Remote"])

        # Generate user profile
        dept = random.choice(departments)

        # Use LLM generator if available, otherwise fall back to simple generation
        if self.llm_generator:
            # Generate job title first
            title = self._generate_job_title(dept)

            # Use LLM to generate realistic user profile
            profile = self.llm_generator.generate_user_profile(
                industry=self.industry,
                department=dept,
                title=title,
                org_size=self.org_size
            )

            # Ensure required fields are present
            if "employeeNumber" not in profile:
                profile["employeeNumber"] = f"EMP{str(len(self.state['users']) + 1000).zfill(5)}"
            if "startDate" not in profile:
                profile["startDate"] = datetime.now(timezone.utc).isoformat()
        else:
            # Fallback to simple generation
            first_name = self._generate_first_name()
            last_name = self._generate_last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@{self.industry.lower()}.example.com"

            profile = {
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "login": email,
                "department": dept,
                "title": self._generate_job_title(dept),
                "employeeNumber": f"EMP{str(len(self.state['users']) + 1000).zfill(5)}",
                "location": random.choice(locations),
                "startDate": datetime.now(timezone.utc).isoformat()
            }

        client = self.client_pool.get_random_client()

        user = await asyncio.to_thread(
            client.create_user,
            profile=profile,
            activate=True
        )

        if user:
            self.state["users"][user["id"]] = {
                "id": user["id"],
                "profile": profile,
                "status": "ACTIVE",
                "groups": [],
                "apps": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": client.user_name
            }

            print(f"  Created user: {profile['firstName']} {profile['lastName']} ({profile['title']})")

            # Assign to department group
            await self._assign_user_to_department(user["id"], dept)

            # Assign basic apps
            await self._assign_basic_apps(user["id"])

    async def _handle_deactivate_user(self):
        """Handle user deactivation (offboarding)."""
        # Find an active user to deactivate
        active_users = [u for u in self.state["users"].values() if u["status"] == "ACTIVE"]

        if not active_users:
            return

        user_data = random.choice(active_users)
        user_id = user_data["id"]

        client = self.client_pool.get_random_client()

        success = await asyncio.to_thread(
            client.deactivate_user,
            user_id=user_id
        )

        if success:
            user_data["status"] = "DEPROVISIONED"
            user_data["deactivated_at"] = datetime.now(timezone.utc).isoformat()
            profile = user_data["profile"]
            print(f"  Deactivated user: {profile['firstName']} {profile['lastName']}")

    async def _handle_update_user(self):
        """Handle user profile update (promotion, transfer)."""
        # Find an active user to update
        active_users = [u for u in self.state["users"].values() if u["status"] == "ACTIVE"]

        if not active_users:
            return

        user_data = random.choice(active_users)
        user_id = user_data["id"]
        profile = user_data["profile"].copy()

        # Determine update type
        update_type = random.choice(["promotion", "transfer", "location_change"])

        if update_type == "promotion":
            # Update title
            old_title = profile.get("title", "")
            if "Senior" not in old_title and "Manager" not in old_title:
                profile["title"] = f"Senior {old_title}"
            elif "Manager" not in old_title:
                profile["title"] = f"{old_title.replace('Senior', '')} Manager"
            else:
                profile["title"] = old_title.replace("Manager", "Director")
        elif update_type == "transfer":
            # Change department
            departments = get_departments_for_industry(self.industry)
            current_dept = profile.get("department", "")
            new_dept = random.choice([d for d in departments if d != current_dept])
            profile["department"] = new_dept
            profile["title"] = self._generate_job_title(new_dept)
        else:
            # Change location
            locations = self.org_config.get("locations", ["Remote"])
            current_location = profile.get("location", "")
            new_location = random.choice([l for l in locations if l != current_location])
            profile["location"] = new_location

        client = self.client_pool.get_random_client()

        updated_user = await asyncio.to_thread(
            client.update_user,
            user_id=user_id,
            profile=profile
        )

        if updated_user:
            user_data["profile"] = profile
            print(f"  Updated user: {profile['firstName']} {profile['lastName']} - {update_type}")

    async def _handle_assign_to_group(self):
        """Handle adding user to a group."""
        # Find a user not in all groups
        for user_data in self.state["users"].values():
            if user_data["status"] == "ACTIVE":
                # Find a group they're not in
                for group_id, group in self.state["groups"].items():
                    if group_id not in user_data["groups"]:
                        # Try to assign
                        client = self.client_pool.get_random_client()
                        success = await asyncio.to_thread(
                            client.add_user_to_group,
                            user_id=user_data["id"],
                            group_id=group_id
                        )

                        if success:
                            user_data["groups"].append(group_id)
                            group["member_count"] += 1
                            profile = user_data["profile"]
                            print(f"  Added {profile['firstName']} {profile['lastName']} to {group['name']}")
                            return

    async def _handle_remove_from_group(self):
        """Handle removing user from a group."""
        # Find a user in multiple groups
        for user_data in self.state["users"].values():
            if user_data["status"] == "ACTIVE" and len(user_data["groups"]) > 1:
                # Don't remove from "All Employees"
                removable_groups = [g for g in user_data["groups"]
                                   if self.state["groups"][g]["type"] != "all_employees"]

                if removable_groups:
                    group_id = random.choice(removable_groups)
                    client = self.client_pool.get_random_client()

                    success = await asyncio.to_thread(
                        client.remove_user_from_group,
                        user_id=user_data["id"],
                        group_id=group_id
                    )

                    if success:
                        user_data["groups"].remove(group_id)
                        self.state["groups"][group_id]["member_count"] -= 1
                        profile = user_data["profile"]
                        group_name = self.state["groups"][group_id]["name"]
                        print(f"  Removed {profile['firstName']} {profile['lastName']} from {group_name}")
                        return

    async def _handle_assign_app(self):
        """Handle assigning app to user."""
        if not self.app_catalog:
            return

        # Find a user who doesn't have all apps
        for user_data in self.state["users"].values():
            if user_data["status"] == "ACTIVE":
                # Find an app they don't have
                for app_name, app_id in self.app_catalog.items():
                    if app_id not in user_data["apps"]:
                        client = self.client_pool.get_random_client()

                        assignment = await asyncio.to_thread(
                            client.assign_user_to_app,
                            user_id=user_data["id"],
                            app_id=app_id
                        )

                        if assignment:
                            assignment_id = f"{app_id}_{user_data['id']}"
                            self.state["app_assignments"][assignment_id] = {
                                "app_id": app_id,
                                "app_name": app_name,
                                "user_id": user_data["id"],
                                "assigned_at": datetime.now(timezone.utc).isoformat(),
                                "assigned_by": client.user_name
                            }
                            user_data["apps"].append(app_id)
                            profile = user_data["profile"]
                            print(f"  Assigned {app_name} to {profile['firstName']} {profile['lastName']}")
                            return

    async def _handle_unassign_app(self):
        """Handle removing app from user."""
        # Find a user with multiple apps
        for user_data in self.state["users"].values():
            if user_data["status"] == "ACTIVE" and len(user_data["apps"]) > 2:
                app_id = random.choice(user_data["apps"])
                client = self.client_pool.get_random_client()

                success = await asyncio.to_thread(
                    client.remove_user_from_app,
                    user_id=user_data["id"],
                    app_id=app_id
                )

                if success:
                    user_data["apps"].remove(app_id)
                    # Remove from app_assignments
                    assignment_id = f"{app_id}_{user_data['id']}"
                    if assignment_id in self.state["app_assignments"]:
                        app_name = self.state["app_assignments"][assignment_id].get("app_name", "Unknown")
                        del self.state["app_assignments"][assignment_id]
                    else:
                        app_name = "Unknown"

                    profile = user_data["profile"]
                    print(f"  Removed {app_name} from {profile['firstName']} {profile['lastName']}")
                    return

    async def _handle_create_group(self):
        """Handle creating a new group."""
        # Determine group type
        departments = get_departments_for_industry(self.industry)
        dept = random.choice(departments)
        group_type = random.choice(["team", "project", "role"])

        # Use LLM generator if available, otherwise fall back to simple generation
        if self.llm_generator:
            group_name = self.llm_generator.generate_group_name(
                industry=self.industry,
                department=dept,
                group_type=group_type
            )
            description = self.llm_generator.generate_group_description(
                industry=self.industry,
                group_name=group_name,
                group_type=group_type
            )
        else:
            # Fallback to simple generation
            group_types = ["Project", "Committee", "Team", "Task Force"]
            group_prefixes = ["Innovation", "Digital", "Strategic", "Customer", "Product"]

            selected_type = random.choice(group_types)
            prefix = random.choice(group_prefixes)
            suffix = random.randint(100, 999)

            group_name = f"{prefix} {selected_type} {suffix}"
            description = f"Members of the {group_name}"

        client = self.client_pool.get_random_client()

        group = await asyncio.to_thread(
            client.create_group,
            name=group_name,
            description=description
        )

        if group:
            self.state["groups"][group["id"]] = {
                "id": group["id"],
                "name": group_name,
                "type": "project",
                "description": description,
                "member_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": client.user_name
            }
            print(f"  Created group: {group_name}")

    async def _handle_delete_group(self):
        """Handle deleting a group."""
        # Find a deletable group (not department or all_employees)
        deletable_groups = [
            (gid, g) for gid, g in self.state["groups"].items()
            if g["type"] not in ["department", "all_employees"] and g["member_count"] < 3
        ]

        if not deletable_groups:
            return

        group_id, group = random.choice(deletable_groups)
        client = self.client_pool.get_random_client()

        success = await asyncio.to_thread(
            client.delete_group,
            group_id=group_id
        )

        if success:
            # Remove group from all users
            for user_data in self.state["users"].values():
                if group_id in user_data["groups"]:
                    user_data["groups"].remove(group_id)

            group_name = group["name"]
            del self.state["groups"][group_id]
            print(f"  Deleted group: {group_name}")

    async def _handle_suspend_user(self):
        """Handle suspending a user."""
        # Find an active user to suspend
        active_users = [u for u in self.state["users"].values() if u["status"] == "ACTIVE"]

        if not active_users:
            return

        user_data = random.choice(active_users)
        user_id = user_data["id"]

        client = self.client_pool.get_random_client()

        success = await asyncio.to_thread(
            client.suspend_user,
            user_id=user_id
        )

        if success:
            user_data["status"] = "SUSPENDED"
            user_data["suspended_at"] = datetime.now(timezone.utc).isoformat()
            profile = user_data["profile"]
            print(f"  Suspended user: {profile['firstName']} {profile['lastName']}")

    async def _handle_unsuspend_user(self):
        """Handle unsuspending a user."""
        # Find a suspended user
        suspended_users = [u for u in self.state["users"].values() if u["status"] == "SUSPENDED"]

        if not suspended_users:
            return

        user_data = random.choice(suspended_users)
        user_id = user_data["id"]

        client = self.client_pool.get_random_client()

        success = await asyncio.to_thread(
            client.unsuspend_user,
            user_id=user_id
        )

        if success:
            user_data["status"] = "ACTIVE"
            if "suspended_at" in user_data:
                del user_data["suspended_at"]
            profile = user_data["profile"]
            print(f"  Unsuspended user: {profile['firstName']} {profile['lastName']}")

    async def _handle_password_reset(self):
        """Handle password reset for a user."""
        # Find an active user
        active_users = [u for u in self.state["users"].values() if u["status"] == "ACTIVE"]

        if not active_users:
            return

        user_data = random.choice(active_users)
        user_id = user_data["id"]
        profile = user_data["profile"]

        # Log the password reset event
        print(f"  Password reset initiated for: {profile['firstName']} {profile['lastName']}")

    async def _handle_mfa_enrollment(self):
        """Handle MFA enrollment for a user."""
        # Find an active user
        active_users = [u for u in self.state["users"].values() if u["status"] == "ACTIVE"]

        if not active_users:
            return

        user_data = random.choice(active_users)
        profile = user_data["profile"]

        # Log the MFA enrollment event
        print(f"  MFA enrolled for: {profile['firstName']} {profile['lastName']}")

    async def _assign_user_to_department(self, user_id: str, department: str):
        """Assign user to their department group."""
        for group_id, group in self.state["groups"].items():
            if group["type"] == "department" and group.get("department") == department:
                try:
                    client = self.client_pool.get_random_client()
                    success = await asyncio.to_thread(
                        client.add_user_to_group,
                        user_id=user_id,
                        group_id=group_id
                    )
                    if success:
                        self.state["users"][user_id]["groups"].append(group_id)
                        group["member_count"] += 1
                except Exception:
                    pass
                break

    async def _assign_basic_apps(self, user_id: str):
        """Assign basic apps to a new user."""
        basic_apps = ["Slack", "Zoom", "Microsoft 365"]

        for app_name in basic_apps:
            if app_name in self.app_catalog:
                try:
                    client = self.client_pool.get_random_client()
                    app_id = self.app_catalog[app_name]

                    assignment = await asyncio.to_thread(
                        client.assign_user_to_app,
                        user_id=user_id,
                        app_id=app_id
                    )

                    if assignment:
                        assignment_id = f"{app_id}_{user_id}"
                        self.state["app_assignments"][assignment_id] = {
                            "app_id": app_id,
                            "app_name": app_name,
                            "user_id": user_id,
                            "assigned_at": datetime.now(timezone.utc).isoformat(),
                            "assigned_by": client.user_name
                        }
                        self.state["users"][user_id]["apps"].append(app_id)
                except Exception:
                    pass

    def _generate_first_name(self) -> str:
        """Generate a random first name."""
        first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
            "James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Thomas",
            "Linda", "Charles", "Elizabeth", "Joseph", "Barbara", "Christopher", "Susan",
            "Daniel", "Jessica", "Matthew", "Karen", "Anthony", "Nancy", "Mark", "Betty",
            "Paul", "Dorothy", "Steven", "Sandra", "Andrew", "Ashley", "Kenneth", "Kimberly",
            "Joshua", "Donna", "Kevin", "Michelle", "Brian", "Carol", "George", "Amanda"
        ]
        return random.choice(first_names)

    def _generate_last_name(self) -> str:
        """Generate a random last name."""
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
            "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
            "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell"
        ]
        return random.choice(last_names)

    def _generate_job_title(self, department: str) -> str:
        """Generate a job title appropriate for the department."""
        titles_by_dept = {
            "Engineering": [
                "Software Engineer", "Senior Software Engineer", "Staff Engineer",
                "Engineering Manager", "DevOps Engineer", "QA Engineer", "Data Engineer"
            ],
            "Sales": [
                "Sales Representative", "Account Executive", "Sales Manager",
                "Business Development Representative", "Account Manager", "Sales Director"
            ],
            "Marketing": [
                "Marketing Manager", "Content Marketing Specialist", "SEO Specialist",
                "Marketing Director", "Brand Manager", "Product Marketing Manager"
            ],
            "Product": [
                "Product Manager", "Senior Product Manager", "Product Designer",
                "UX Designer", "Product Owner", "Product Director"
            ],
            "Finance": [
                "Accountant", "Financial Analyst", "Controller", "CFO",
                "Accounts Payable Specialist", "Financial Manager", "Bookkeeper"
            ],
            "HR": [
                "HR Manager", "Recruiter", "HR Business Partner", "HR Director",
                "Talent Acquisition Specialist", "HR Coordinator", "People Operations Manager"
            ],
            "IT": [
                "IT Support Specialist", "System Administrator", "Network Engineer",
                "IT Manager", "Security Engineer", "Database Administrator", "IT Director"
            ],
            "Operations": [
                "Operations Manager", "Operations Analyst", "Supply Chain Manager",
                "Operations Director", "Business Analyst", "Process Improvement Specialist"
            ],
            "Customer Success": [
                "Customer Success Manager", "Support Specialist", "Customer Success Director",
                "Technical Support Engineer", "Account Manager", "Implementation Specialist"
            ],
            "Legal": [
                "Legal Counsel", "Contract Manager", "Compliance Officer",
                "Paralegal", "Legal Director", "Corporate Attorney"
            ]
        }

        # Default titles if department not found
        default_titles = [
            "Specialist", "Manager", "Analyst", "Coordinator", "Associate", "Director"
        ]

        dept_titles = titles_by_dept.get(department, default_titles)
        return random.choice(dept_titles)

    def _log_activity(self, activity_type: str, status: str, details: str = None):
        """Log activity to state."""
        activity = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "activity_type": activity_type,
            "status": status,
            "details": details
        }

        self.state["activity_log"].append(activity)

        # Keep only last 1000 activities
        if len(self.state["activity_log"]) > 1000:
            self.state["activity_log"] = self.state["activity_log"][-1000:]

    # Override abstract methods that don't apply to Okta
    async def _create_project(self) -> Optional[Dict[str, Any]]:
        """Not applicable for Okta - groups are created instead."""
        return None

    async def _create_task(self, project_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Not applicable for Okta - users are created instead."""
        return None

    async def cleanup_platform_data(self, progress_callback=None) -> Dict[str, Any]:
        """
        Delete all Okta data created by this job.

        Args:
            progress_callback: Optional callback function(current, total, message)

        Returns:
            Dictionary with cleanup results
        """
        print(f"Starting cleanup for job {self.job_id}...")

        results = {
            "users_deleted": 0,
            "groups_deleted": 0,
            "assignments_removed": 0,
            "errors": []
        }

        # Calculate total operations
        total_operations = (
            len(self.state.get("users", {})) * 2 +  # Deactivate + delete
            len(self.state.get("groups", {})) +
            len(self.state.get("app_assignments", {}))
        )
        current_operation = 0

        # Step 1: Remove app assignments
        print("Removing app assignments...")
        for assignment_id, assignment in self.state.get("app_assignments", {}).items():
            try:
                client = self.client_pool.get_random_client()
                success = await asyncio.to_thread(
                    client.remove_user_from_app,
                    user_id=assignment["user_id"],
                    app_id=assignment["app_id"]
                )
                if success:
                    results["assignments_removed"] += 1

                current_operation += 1
                if progress_callback:
                    progress_callback(
                        current_operation,
                        total_operations,
                        f"Removing app assignment {current_operation}/{len(self.state.get('app_assignments', {}))}"
                    )

                await asyncio.sleep(0.1)

            except Exception as e:
                results["errors"].append(f"Error removing assignment {assignment_id}: {e}")

        # Step 2: Deactivate and delete users
        print("Deactivating and deleting users...")
        for user_id, user_data in self.state.get("users", {}).items():
            try:
                client = self.client_pool.get_random_client()

                # First deactivate if active
                if user_data.get("status") == "ACTIVE":
                    await asyncio.to_thread(client.deactivate_user, user_id)

                current_operation += 1
                if progress_callback:
                    progress_callback(
                        current_operation,
                        total_operations,
                        f"Deactivating user {user_data['profile']['firstName']} {user_data['profile']['lastName']}"
                    )

                await asyncio.sleep(0.2)

                # Then delete
                success = await asyncio.to_thread(client.delete_user, user_id)
                if success:
                    results["users_deleted"] += 1

                current_operation += 1
                if progress_callback:
                    progress_callback(
                        current_operation,
                        total_operations,
                        f"Deleting user {user_data['profile']['firstName']} {user_data['profile']['lastName']}"
                    )

                await asyncio.sleep(0.2)

            except Exception as e:
                results["errors"].append(f"Error deleting user {user_id}: {e}")

        # Step 3: Delete groups
        print("Deleting groups...")
        for group_id, group_data in self.state.get("groups", {}).items():
            try:
                client = self.client_pool.get_random_client()
                success = await asyncio.to_thread(client.delete_group, group_id)
                if success:
                    results["groups_deleted"] += 1

                current_operation += 1
                if progress_callback:
                    progress_callback(
                        current_operation,
                        total_operations,
                        f"Deleting group {group_data['name']}"
                    )

                await asyncio.sleep(0.1)

            except Exception as e:
                results["errors"].append(f"Error deleting group {group_id}: {e}")

        # Mark as deleted
        self.deleted = True

        print(f"✓ Cleanup completed:")
        print(f"  - Users deleted: {results['users_deleted']}")
        print(f"  - Groups deleted: {results['groups_deleted']}")
        print(f"  - Assignments removed: {results['assignments_removed']}")
        print(f"  - Errors: {len(results['errors'])}")

        return results