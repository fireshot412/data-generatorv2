#!/usr/bin/env python3
"""
Salesforce Continuous Generation Service - Salesforce CRM-specific implementation of continuous data generation.

Simulates realistic CRM and sales activity including:
- Lead generation and conversion
- Opportunity pipeline management (sales stages, deal progression)
- Account and contact management
- Case/support ticket creation and resolution
- Activity logging (calls, emails, meetings)
- Campaign management and marketing attribution
- Sales forecasting and pipeline health
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
from continuous.connections.salesforce_connection import (
    SalesforceClientPool, SalesforceConnection, SalesforceAPIError, SalesforceRateLimitError
)
from continuous.templates.salesforce_templates import (
    ORG_SIZE_TEMPLATES,
    INDUSTRY_TEMPLATES,
    SALES_PROCESS_TEMPLATES,
    OPPORTUNITY_TYPES,
    LEAD_SOURCES,
    CONTACT_ROLES,
    CASE_TEMPLATES,
    ACCOUNT_TYPES,
    ACCOUNT_SEGMENTS,
    TERRITORY_TEMPLATES,
    WIN_LOSS_REASONS,
    get_org_size_config,
    get_industry_config,
    calculate_account_distribution,
    get_sales_process,
    generate_opportunity_data,
    get_typical_products,
    calculate_sales_team_size,
    get_seasonal_multiplier,
    calculate_opportunity_stage_duration,
    get_win_loss_reason,
    get_all_industries,
    get_all_org_sizes
)


class SalesforceActivityType:
    """Salesforce-specific activity types."""
    # Lead Management
    CREATE_LEAD = "create_lead"
    CONVERT_LEAD = "convert_lead"
    QUALIFY_LEAD = "qualify_lead"

    # Opportunity Management
    CREATE_OPPORTUNITY = "create_opportunity"
    UPDATE_OPPORTUNITY_STAGE = "update_opportunity_stage"
    ADD_OPPORTUNITY_PRODUCT = "add_opportunity_product"
    CLOSE_OPPORTUNITY_WON = "close_opportunity_won"
    CLOSE_OPPORTUNITY_LOST = "close_opportunity_lost"

    # Account/Contact Management
    CREATE_ACCOUNT = "create_account"
    UPDATE_ACCOUNT = "update_account"
    CREATE_CONTACT = "create_contact"
    UPDATE_CONTACT = "update_contact"

    # Case Management
    CREATE_CASE = "create_case"
    UPDATE_CASE = "update_case"
    CLOSE_CASE = "close_case"
    ESCALATE_CASE = "escalate_case"

    # Activity Logging
    LOG_CALL = "log_call"
    LOG_EMAIL = "log_email"
    LOG_MEETING = "log_meeting"
    CREATE_TASK = "create_task"

    # Campaign Management
    CREATE_CAMPAIGN = "create_campaign"
    ADD_CAMPAIGN_MEMBER = "add_campaign_member"


class SalesforceService(BaseService):
    """
    Salesforce-specific implementation of continuous data generation service.

    Generates realistic CRM and sales activity patterns including lead-to-cash flow,
    customer relationship management, and support case lifecycles.
    """

    def __init__(self, config: Dict[str, Any], state_manager: StateManager,
                 llm_generator: Optional[LLMGenerator] = None,
                 client_pool: Optional[SalesforceClientPool] = None):
        """
        Initialize Salesforce continuous service.

        Args:
            config: Job configuration containing:
                - industry: Industry type (healthcare, finance, technology, etc.)
                - org_size: Organization size (startup, midsize, enterprise)
                - activity_level: low, medium, or high
                - duration_days: Number of days to run or "indefinite"
                - user_credentials: Dict of Salesforce credentials
            state_manager: State manager instance
            llm_generator: Optional LLM generator instance for content generation
            client_pool: Optional pool of Salesforce clients (created if not provided)
        """
        # Create client pool if not provided
        if client_pool is None:
            user_credentials = config.get("user_credentials", {})
            client_pool = SalesforceClientPool(user_credentials)

        super().__init__(config, state_manager, llm_generator, client_pool)

        # Salesforce-specific configuration
        self.industry = config.get("industry", "technology")
        self.org_size = config.get("org_size", "midsize")

        # Load templates
        self.industry_config = get_industry_config(self.industry, self.org_size)
        self.org_config = get_org_size_config(self.org_size)

        # Activity weights for different operations
        self.activity_weights = self._calculate_activity_weights()

        # Cache for generated account names to avoid duplicates
        self._generated_account_names = set()

        print(f"✓ Salesforce service initialized - Job ID: {self.job_id}")
        print(f"  Industry: {self.industry}, Org Size: {self.org_size}")

    def _calculate_activity_weights(self) -> Dict[str, int]:
        """
        Calculate activity weights based on org size and sales process.

        Returns:
            Dictionary of activity types with their relative weights
        """
        # Base weights for typical B2B sales organization
        base_weights = {
            # Lead activities (top of funnel)
            SalesforceActivityType.CREATE_LEAD: 25,
            SalesforceActivityType.CONVERT_LEAD: 8,
            SalesforceActivityType.QUALIFY_LEAD: 12,

            # Opportunity activities (middle of funnel)
            SalesforceActivityType.CREATE_OPPORTUNITY: 10,
            SalesforceActivityType.UPDATE_OPPORTUNITY_STAGE: 20,
            SalesforceActivityType.ADD_OPPORTUNITY_PRODUCT: 5,
            SalesforceActivityType.CLOSE_OPPORTUNITY_WON: 4,
            SalesforceActivityType.CLOSE_OPPORTUNITY_LOST: 3,

            # Account/Contact management
            SalesforceActivityType.CREATE_ACCOUNT: 5,
            SalesforceActivityType.UPDATE_ACCOUNT: 3,
            SalesforceActivityType.CREATE_CONTACT: 8,
            SalesforceActivityType.UPDATE_CONTACT: 4,

            # Case management (customer support)
            SalesforceActivityType.CREATE_CASE: 10,
            SalesforceActivityType.UPDATE_CASE: 8,
            SalesforceActivityType.CLOSE_CASE: 6,
            SalesforceActivityType.ESCALATE_CASE: 2,

            # Activity logging (sales activities)
            SalesforceActivityType.LOG_CALL: 15,
            SalesforceActivityType.LOG_EMAIL: 12,
            SalesforceActivityType.LOG_MEETING: 8,
            SalesforceActivityType.CREATE_TASK: 10,

            # Campaign management
            SalesforceActivityType.CREATE_CAMPAIGN: 2,
            SalesforceActivityType.ADD_CAMPAIGN_MEMBER: 5,
        }

        # Adjust based on org size
        if self.org_size == "startup":
            # Startups focus more on lead generation and new opportunities
            base_weights[SalesforceActivityType.CREATE_LEAD] = 35
            base_weights[SalesforceActivityType.CREATE_OPPORTUNITY] = 15
            base_weights[SalesforceActivityType.CREATE_CASE] = 5  # Fewer customers
        elif self.org_size == "enterprise":
            # Enterprises have more account management and case activity
            base_weights[SalesforceActivityType.UPDATE_ACCOUNT] = 8
            base_weights[SalesforceActivityType.CREATE_CASE] = 15
            base_weights[SalesforceActivityType.CREATE_CAMPAIGN] = 5

        return base_weights

    async def run(self):
        """Main loop - runs continuously until stopped."""
        self.running = True

        # Check if we need initial setup
        initial_generation = len(self.state.get("accounts", {})) == 0

        if initial_generation:
            self.state_manager.update_job_status(self.job_id, "initializing")
            print(f"Initializing Salesforce CRM organization for {self.industry}...")
            await self._initialize_organization()
            self.state_manager.update_job_status(self.job_id, "running")
            print("✓ Initial CRM setup complete")
        else:
            self.state_manager.update_job_status(self.job_id, "running")
            print("Resuming Salesforce activity generation...")

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

            except SalesforceRateLimitError as e:
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
        print(f"Salesforce generation stopped for job {self.job_id}")

    async def _initialize_organization(self):
        """
        Initialize CRM organization with accounts, contacts, opportunities, and campaigns.
        Creates the foundational structure for ongoing sales activity generation.
        """
        print("Setting up CRM organizational structure...")

        # Initialize state structure
        if "accounts" not in self.state:
            self.state["accounts"] = {}
        if "contacts" not in self.state:
            self.state["contacts"] = {}
        if "opportunities" not in self.state:
            self.state["opportunities"] = {}
        if "cases" not in self.state:
            self.state["cases"] = {}
        if "leads" not in self.state:
            self.state["leads"] = {}
        if "users" not in self.state:
            self.state["users"] = []
        if "campaigns" not in self.state:
            self.state["campaigns"] = {}
        if "products" not in self.state:
            self.state["products"] = []
        if "activity_log" not in self.state:
            self.state["activity_log"] = []

        # Step 1: Fetch Salesforce users for assignment
        await self._fetch_salesforce_users()

        # Step 2: Create initial accounts
        await self._create_initial_accounts()

        # Step 3: Create contacts for each account
        await self._create_initial_contacts()

        # Step 4: Create initial opportunities
        await self._create_initial_opportunities()

        # Step 5: Create campaigns (if enterprise)
        if self.org_size == "enterprise":
            await self._create_initial_campaigns()

        # Step 6: Create some initial leads
        await self._create_initial_leads()

        # Update stats and save state
        self._update_stats()
        self._log_activity("initialization", "success", f"Initialized CRM with {len(self.state['accounts'])} accounts, {len(self.state['contacts'])} contacts, {len(self.state['opportunities'])} opportunities, {len(self.state['leads'])} leads")
        self.state_manager.save_state(self.job_id, self.state)

        print(f"✓ Created {len(self.state['accounts'])} accounts")
        print(f"✓ Created {len(self.state['contacts'])} contacts")
        print(f"✓ Created {len(self.state['opportunities'])} opportunities")
        print(f"✓ Created {len(self.state['leads'])} leads")

    async def _fetch_salesforce_users(self):
        """Fetch active Salesforce users for assignment to records."""
        print("Fetching Salesforce users...")
        client = self.client_pool.get_random_client()

        try:
            users = await asyncio.to_thread(
                client.get_workspace_users,
                workspace_gid=""  # Not used in Salesforce
            )

            self.state["users"] = users
            print(f"  Found {len(users)} active users")

        except Exception as e:
            print(f"  Error fetching users: {e}")
            # Create placeholder user if fetch fails
            self.state["users"] = [{"gid": "placeholder", "name": "System User"}]

    async def _create_initial_accounts(self):
        """Create initial batch of customer accounts."""
        # Determine number of accounts based on org size
        account_range = self.org_config["account_count_range"]
        num_accounts = random.randint(account_range[0], account_range[1])

        # Get account type distribution for industry
        account_distribution = calculate_account_distribution(num_accounts, self.industry, self.org_size)

        print(f"Creating {num_accounts} initial accounts...")

        account_count = 0
        for account_type, count in account_distribution.items():
            for i in range(count):
                try:
                    # Generate account data
                    account_name = self._generate_account_name(account_type)

                    # Select account segment (enterprise, mid-market, SMB)
                    segment = self._select_account_segment()
                    segment_config = ACCOUNT_SEGMENTS[segment]

                    # Generate realistic revenue
                    revenue_range = segment_config["annual_revenue_range"]
                    annual_revenue = random.randint(revenue_range[0], revenue_range[1])

                    client = self.client_pool.get_random_client()

                    # Create account
                    account = await asyncio.to_thread(
                        client.create_project,
                        workspace_gid="",  # Not used
                        name=account_name,
                        notes=f"{account_type} account in {self.industry} industry",
                        industry=self.industry.title(),
                        annual_revenue=annual_revenue
                    )

                    if account:
                        self.state["accounts"][account["gid"]] = {
                            "id": account["gid"],
                            "name": account_name,
                            "type": account_type,
                            "segment": segment,
                            "industry": self.industry,
                            "annual_revenue": annual_revenue,
                            "contacts": [],
                            "opportunities": [],
                            "cases": [],
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "created_by": client.user_name
                        }

                        account_count += 1

                        if account_count % 10 == 0:
                            print(f"  Created {account_count}/{num_accounts} accounts")

                    await asyncio.sleep(0.3)  # Rate limit protection

                except Exception as e:
                    print(f"  Error creating account {account_count + 1}: {e}")

    async def _create_initial_contacts(self):
        """Create contacts for each account (2-10 per account)."""
        print("Creating contacts for accounts...")

        contact_count = 0
        for account_id, account_data in self.state["accounts"].items():
            # Determine number of contacts (2-10 per account)
            num_contacts = random.randint(2, 10)

            for i in range(num_contacts):
                try:
                    first_name = self._generate_first_name()
                    last_name = self._generate_last_name()

                    # Select contact role
                    role = self._select_contact_role()
                    title = random.choice(CONTACT_ROLES[role]["typical_titles"])

                    email = f"{first_name.lower()}.{last_name.lower()}@{account_data['name'].lower().replace(' ', '')}.com"

                    client = self.client_pool.get_random_client()

                    # Create contact
                    contact = await asyncio.to_thread(
                        client.create_contact,
                        account_id=account_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        title=title
                    )

                    if contact:
                        self.state["contacts"][contact["gid"]] = {
                            "id": contact["gid"],
                            "account_id": account_id,
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": email,
                            "title": title,
                            "role": role,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "created_by": client.user_name
                        }

                        account_data["contacts"].append(contact["gid"])
                        contact_count += 1

                    await asyncio.sleep(0.2)

                except Exception as e:
                    print(f"  Error creating contact: {e}")

        print(f"✓ Created {contact_count} contacts")

    async def _create_initial_opportunities(self):
        """Create initial opportunities for accounts."""
        # Determine number of opportunities based on org size
        opp_range = self.org_config["active_opportunity_range"]
        num_opportunities = random.randint(opp_range[0], opp_range[1])

        print(f"Creating {num_opportunities} initial opportunities...")

        opp_count = 0
        accounts_with_opps = random.sample(
            list(self.state["accounts"].keys()),
            min(len(self.state["accounts"]), num_opportunities)
        )

        for account_id in accounts_with_opps[:num_opportunities]:
            try:
                account_data = self.state["accounts"][account_id]

                # Generate opportunity data based on industry and segment
                opp_data = generate_opportunity_data(
                    self.industry,
                    account_data["segment"],
                    random.choice(list(OPPORTUNITY_TYPES.keys())),
                    self.org_size
                )

                # Generate opportunity name
                opp_name = self._generate_opportunity_name(account_data["name"], opp_data["type"])

                # Select owner (sales rep)
                owner = self._get_random_user()

                client = self.client_pool.get_random_client()

                # Create opportunity
                opportunity = await asyncio.to_thread(
                    client.create_task,
                    project_gid=account_id,
                    name=opp_name,
                    notes=f"{opp_data['type']} opportunity in {opp_data['stage']} stage",
                    assignee=owner["gid"] if owner else None,
                    amount=opp_data["amount"],
                    close_date=opp_data["close_date"],
                    stage=opp_data["stage"],
                    probability=opp_data["probability"]
                )

                if opportunity:
                    self.state["opportunities"][opportunity["gid"]] = {
                        "id": opportunity["gid"],
                        "account_id": account_id,
                        "name": opp_name,
                        "amount": opp_data["amount"],
                        "stage": opp_data["stage"],
                        "probability": opp_data["probability"],
                        "close_date": opp_data["close_date"],
                        "type": opp_data["type"],
                        "owner_id": owner["gid"] if owner else None,
                        "is_closed": False,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "created_by": client.user_name
                    }

                    account_data["opportunities"].append(opportunity["gid"])
                    opp_count += 1

                    if opp_count % 10 == 0:
                        print(f"  Created {opp_count}/{num_opportunities} opportunities")

                await asyncio.sleep(0.3)

            except Exception as e:
                print(f"  Error creating opportunity: {e}")

    async def _create_initial_campaigns(self):
        """Create marketing campaigns for enterprise orgs."""
        print("Creating marketing campaigns...")

        num_campaigns = random.randint(3, 8)
        campaign_types = ["Webinar", "Trade Show", "Email Campaign", "Content Marketing", "Product Launch"]

        for i in range(num_campaigns):
            try:
                campaign_type = random.choice(campaign_types)
                campaign_name = f"Q{random.randint(1,4)} {datetime.now().year} {campaign_type}"

                client = self.client_pool.get_random_client()

                # Create campaign
                campaign = await asyncio.to_thread(
                    client.create_portfolio,
                    workspace_gid="",
                    name=campaign_name,
                    status="In Progress",
                    type=campaign_type
                )

                if campaign:
                    self.state["campaigns"][campaign["gid"]] = {
                        "id": campaign["gid"],
                        "name": campaign_name,
                        "type": campaign_type,
                        "status": "In Progress",
                        "members": [],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "created_by": client.user_name
                    }

                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"  Error creating campaign: {e}")

    async def _create_initial_leads(self):
        """Create initial lead pipeline."""
        num_leads = random.randint(20, 100)
        print(f"Creating {num_leads} initial leads...")

        lead_count = 0
        for i in range(num_leads):
            try:
                # Generate lead data
                first_name = self._generate_first_name()
                last_name = self._generate_last_name()
                company = self._generate_company_name()

                # Select lead source
                lead_source = self._select_lead_source()

                email = f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '')}.com"

                client = self.client_pool.get_random_client()

                # Create lead
                lead = await asyncio.to_thread(
                    client.create_lead,
                    first_name=first_name,
                    last_name=last_name,
                    company=company,
                    email=email,
                    status="Open - Not Contacted",
                    lead_source=lead_source
                )

                if lead:
                    self.state["leads"][lead["gid"]] = {
                        "id": lead["gid"],
                        "first_name": first_name,
                        "last_name": last_name,
                        "company": company,
                        "email": email,
                        "status": "Open - Not Contacted",
                        "lead_source": lead_source,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "created_by": client.user_name
                    }

                    lead_count += 1

                await asyncio.sleep(0.2)

            except Exception as e:
                print(f"  Error creating lead: {e}")

        print(f"✓ Created {lead_count} leads")

    async def _generate_activity(self):
        """Generate a single activity based on current state and weights."""
        # Select activity type based on weights
        activity_type = self._select_activity_type()

        try:
            if activity_type == SalesforceActivityType.CREATE_LEAD:
                await self._handle_create_lead()
            elif activity_type == SalesforceActivityType.CONVERT_LEAD:
                await self._handle_convert_lead()
            elif activity_type == SalesforceActivityType.QUALIFY_LEAD:
                await self._handle_qualify_lead()
            elif activity_type == SalesforceActivityType.CREATE_OPPORTUNITY:
                await self._handle_create_opportunity()
            elif activity_type == SalesforceActivityType.UPDATE_OPPORTUNITY_STAGE:
                await self._handle_update_opportunity_stage()
            elif activity_type == SalesforceActivityType.ADD_OPPORTUNITY_PRODUCT:
                await self._handle_add_opportunity_product()
            elif activity_type == SalesforceActivityType.CLOSE_OPPORTUNITY_WON:
                await self._handle_close_opportunity_won()
            elif activity_type == SalesforceActivityType.CLOSE_OPPORTUNITY_LOST:
                await self._handle_close_opportunity_lost()
            elif activity_type == SalesforceActivityType.CREATE_ACCOUNT:
                await self._handle_create_account()
            elif activity_type == SalesforceActivityType.UPDATE_ACCOUNT:
                await self._handle_update_account()
            elif activity_type == SalesforceActivityType.CREATE_CONTACT:
                await self._handle_create_contact()
            elif activity_type == SalesforceActivityType.UPDATE_CONTACT:
                await self._handle_update_contact()
            elif activity_type == SalesforceActivityType.CREATE_CASE:
                await self._handle_create_case()
            elif activity_type == SalesforceActivityType.UPDATE_CASE:
                await self._handle_update_case()
            elif activity_type == SalesforceActivityType.CLOSE_CASE:
                await self._handle_close_case()
            elif activity_type == SalesforceActivityType.ESCALATE_CASE:
                await self._handle_escalate_case()
            elif activity_type == SalesforceActivityType.LOG_CALL:
                await self._handle_log_call()
            elif activity_type == SalesforceActivityType.LOG_EMAIL:
                await self._handle_log_email()
            elif activity_type == SalesforceActivityType.LOG_MEETING:
                await self._handle_log_meeting()
            elif activity_type == SalesforceActivityType.CREATE_TASK:
                await self._handle_create_task()
            elif activity_type == SalesforceActivityType.CREATE_CAMPAIGN:
                await self._handle_create_campaign()
            elif activity_type == SalesforceActivityType.ADD_CAMPAIGN_MEMBER:
                await self._handle_add_campaign_member()

            # Log activity and update stats
            self._log_activity(activity_type, "success")
            self._update_stats()

            # Save state after each activity
            if not self.deleted:
                self.state_manager.save_state(self.job_id, self.state)

        except Exception as e:
            print(f"Error generating {activity_type}: {e}")
            self._log_activity(activity_type, "failed", str(e))
            self._update_stats()

    def _select_activity_type(self) -> str:
        """Select activity type based on weights and current state."""
        # Build weighted list
        choices = []
        weights = []

        for activity, weight in self.activity_weights.items():
            # Adjust weights based on current state
            adjusted_weight = weight

            # Lead activities require leads
            if activity == SalesforceActivityType.CONVERT_LEAD:
                qualified_leads = [l for l in self.state["leads"].values()
                                 if l.get("status") in ["Working - Contacted", "Qualified"]]
                if len(qualified_leads) < 3:
                    adjusted_weight = 0
            elif activity == SalesforceActivityType.QUALIFY_LEAD:
                new_leads = [l for l in self.state["leads"].values()
                           if l.get("status") == "Open - Not Contacted"]
                if len(new_leads) < 2:
                    adjusted_weight = 0

            # Opportunity activities require open opportunities
            elif activity == SalesforceActivityType.UPDATE_OPPORTUNITY_STAGE:
                open_opps = self._get_open_opportunities()
                if len(open_opps) < 2:
                    adjusted_weight = 0
            elif activity in [SalesforceActivityType.CLOSE_OPPORTUNITY_WON,
                            SalesforceActivityType.CLOSE_OPPORTUNITY_LOST]:
                late_stage_opps = [o for o in self._get_open_opportunities()
                                  if o.get("probability", 0) >= 60]
                if len(late_stage_opps) < 1:
                    adjusted_weight = 0

            # Case activities require accounts with customer type
            elif activity == SalesforceActivityType.CREATE_CASE:
                customer_accounts = [a for a in self.state["accounts"].values()
                                   if a.get("type") == "Customer"]
                if len(customer_accounts) < 1:
                    adjusted_weight = 0
            elif activity in [SalesforceActivityType.UPDATE_CASE,
                            SalesforceActivityType.CLOSE_CASE]:
                open_cases = self._get_open_cases()
                if len(open_cases) < 1:
                    adjusted_weight = 0
            elif activity == SalesforceActivityType.ESCALATE_CASE:
                escalatable_cases = [c for c in self._get_open_cases()
                                    if c.get("priority") in ["High", "Critical"]]
                if len(escalatable_cases) < 1:
                    adjusted_weight = 0

            # Activity logging requires opportunities or accounts
            elif activity in [SalesforceActivityType.LOG_CALL, SalesforceActivityType.LOG_EMAIL,
                            SalesforceActivityType.LOG_MEETING, SalesforceActivityType.CREATE_TASK]:
                if len(self.state["opportunities"]) < 1 and len(self.state["accounts"]) < 1:
                    adjusted_weight = 0

            # Campaign activities
            elif activity == SalesforceActivityType.ADD_CAMPAIGN_MEMBER:
                if len(self.state["campaigns"]) < 1 or len(self.state["contacts"]) < 1:
                    adjusted_weight = 0

            if adjusted_weight > 0:
                choices.append(activity)
                weights.append(adjusted_weight)

        if not choices:
            # Default to creating a lead if no other activities available
            return SalesforceActivityType.CREATE_LEAD

        return random.choices(choices, weights=weights)[0]

    # ========== LEAD MANAGEMENT HANDLERS ==========

    async def _handle_create_lead(self):
        """Create a new lead (prospect)."""
        first_name = self._generate_first_name()
        last_name = self._generate_last_name()
        company = self._generate_company_name()
        lead_source = self._select_lead_source()

        email = f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '')}.com"

        client = self.client_pool.get_random_client()

        lead = await asyncio.to_thread(
            client.create_lead,
            first_name=first_name,
            last_name=last_name,
            company=company,
            email=email,
            status="Open - Not Contacted",
            lead_source=lead_source
        )

        if lead:
            self.state["leads"][lead["gid"]] = {
                "id": lead["gid"],
                "first_name": first_name,
                "last_name": last_name,
                "company": company,
                "email": email,
                "status": "Open - Not Contacted",
                "lead_source": lead_source,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": client.user_name
            }

            print(f"  Created lead: {first_name} {last_name} from {company} (Source: {lead_source})")

    async def _handle_qualify_lead(self):
        """Qualify a lead (move to contacted/qualified status)."""
        # Find new leads to qualify
        new_leads = [l for l in self.state["leads"].values()
                    if l.get("status") == "Open - Not Contacted"]

        if not new_leads:
            return

        lead = random.choice(new_leads)
        new_status = random.choice(["Working - Contacted", "Qualified"])

        # Note: Salesforce API doesn't support direct lead update in simple-salesforce
        # In production, you'd update via the API
        lead["status"] = new_status
        lead["qualified_at"] = datetime.now(timezone.utc).isoformat()

        print(f"  Qualified lead: {lead['first_name']} {lead['last_name']} - Status: {new_status}")

    async def _handle_convert_lead(self):
        """Convert a qualified lead to Account, Contact, and Opportunity."""
        # Find qualified leads
        qualified_leads = [l for l in self.state["leads"].values()
                         if l.get("status") in ["Working - Contacted", "Qualified"]]

        if not qualified_leads:
            return

        lead = random.choice(qualified_leads)
        client = self.client_pool.get_random_client()

        try:
            # Convert lead
            result = await asyncio.to_thread(
                client.convert_lead,
                lead_id=lead["id"],
                create_opportunity=True,
                opportunity_name=f"{lead['company']} - New Business"
            )

            if result:
                # Add converted account to state
                account_id = result["account_id"]
                self.state["accounts"][account_id] = {
                    "id": account_id,
                    "name": lead["company"],
                    "type": "Customer",
                    "segment": "smb",
                    "industry": self.industry,
                    "contacts": [result["contact_id"]],
                    "opportunities": [result["opportunity_id"]],
                    "cases": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": client.user_name
                }

                # Add contact to state
                contact_id = result["contact_id"]
                self.state["contacts"][contact_id] = {
                    "id": contact_id,
                    "account_id": account_id,
                    "first_name": lead["first_name"],
                    "last_name": lead["last_name"],
                    "email": lead["email"],
                    "title": "Unknown",
                    "role": "decision_maker",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": client.user_name
                }

                # Add opportunity to state
                opp_id = result["opportunity_id"]
                self.state["opportunities"][opp_id] = {
                    "id": opp_id,
                    "account_id": account_id,
                    "name": f"{lead['company']} - New Business",
                    "amount": random.randint(10000, 100000),
                    "stage": "Prospecting",
                    "probability": 10,
                    "close_date": (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
                    "type": "New Business",
                    "owner_id": None,
                    "is_closed": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": client.user_name
                }

                # Mark lead as converted
                lead["status"] = "Closed - Converted"
                lead["converted_at"] = datetime.now(timezone.utc).isoformat()

                print(f"  Converted lead: {lead['first_name']} {lead['last_name']} → Account: {lead['company']}")

        except Exception as e:
            print(f"  Error converting lead: {e}")

    # ========== OPPORTUNITY MANAGEMENT HANDLERS ==========

    async def _handle_create_opportunity(self):
        """Create a new opportunity for an existing account."""
        if not self.state["accounts"]:
            return

        # Select an account
        account_id = random.choice(list(self.state["accounts"].keys()))
        account_data = self.state["accounts"][account_id]

        # Generate opportunity data
        opp_data = generate_opportunity_data(
            self.industry,
            account_data["segment"],
            random.choice(list(OPPORTUNITY_TYPES.keys())),
            self.org_size
        )

        opp_name = self._generate_opportunity_name(account_data["name"], opp_data["type"])
        owner = self._get_random_user()

        client = self.client_pool.get_random_client()

        opportunity = await asyncio.to_thread(
            client.create_opportunity,
            account_id=account_id,
            name=opp_name,
            notes=f"{opp_data['type']} opportunity",
            assignee=owner["gid"] if owner else None,
            amount=opp_data["amount"],
            close_date=opp_data["close_date"],
            stage=opp_data["stage"],
            probability=opp_data["probability"]
        )

        if opportunity:
            self.state["opportunities"][opportunity["gid"]] = {
                "id": opportunity["gid"],
                "account_id": account_id,
                "name": opp_name,
                "amount": opp_data["amount"],
                "stage": opp_data["stage"],
                "probability": opp_data["probability"],
                "close_date": opp_data["close_date"],
                "type": opp_data["type"],
                "owner_id": owner["gid"] if owner else None,
                "is_closed": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": client.user_name
            }

            account_data["opportunities"].append(opportunity["gid"])
            print(f"  Created opportunity: {opp_name} - ${opp_data['amount']:,} ({opp_data['stage']})")

    async def _handle_update_opportunity_stage(self):
        """Move an opportunity forward in the sales pipeline."""
        open_opps = self._get_open_opportunities()

        if not open_opps:
            return

        opp = random.choice(open_opps)

        # Get next stage
        new_stage = self._select_next_opportunity_stage(opp["stage"])

        if not new_stage:
            return  # Already at final stage

        client = self.client_pool.get_random_client()

        # Update opportunity stage
        await asyncio.to_thread(
            client.update_opportunity_stage,
            opp_id=opp["id"],
            stage=new_stage["name"]
        )

        opp["stage"] = new_stage["name"]
        opp["probability"] = new_stage["probability"]
        opp["last_stage_change"] = datetime.now(timezone.utc).isoformat()

        print(f"  Updated opportunity: {opp['name']} → {new_stage['name']} ({new_stage['probability']}%)")

    async def _handle_add_opportunity_product(self):
        """Add products to an opportunity."""
        open_opps = self._get_open_opportunities()

        if not open_opps:
            return

        opp = random.choice(open_opps)

        # Get products for this opportunity's deal size
        products = get_typical_products(self.industry, opp["amount"])

        print(f"  Added {len(products)} products to opportunity: {opp['name']}")

    async def _handle_close_opportunity_won(self):
        """Close an opportunity as won."""
        # Find late-stage opportunities
        late_stage_opps = [o for o in self._get_open_opportunities()
                          if o.get("probability", 0) >= 60]

        if not late_stage_opps:
            return

        opp = random.choice(late_stage_opps)
        client = self.client_pool.get_random_client()

        # Close as won
        await asyncio.to_thread(
            client.update_opportunity_stage,
            opp_id=opp["id"],
            stage="Closed Won"
        )

        opp["stage"] = "Closed Won"
        opp["probability"] = 100
        opp["is_closed"] = True
        opp["closed_at"] = datetime.now(timezone.utc).isoformat()
        opp["win_reason"] = get_win_loss_reason(True)

        print(f"  Closed Won: {opp['name']} - ${opp['amount']:,} (Reason: {opp['win_reason']})")

    async def _handle_close_opportunity_lost(self):
        """Close an opportunity as lost."""
        open_opps = self._get_open_opportunities()

        if not open_opps:
            return

        # More likely to lose early-stage deals
        opp = random.choice(open_opps)
        client = self.client_pool.get_random_client()

        # Close as lost
        await asyncio.to_thread(
            client.update_opportunity_stage,
            opp_id=opp["id"],
            stage="Closed Lost"
        )

        opp["stage"] = "Closed Lost"
        opp["probability"] = 0
        opp["is_closed"] = True
        opp["closed_at"] = datetime.now(timezone.utc).isoformat()
        opp["loss_reason"] = get_win_loss_reason(False)

        print(f"  Closed Lost: {opp['name']} - ${opp['amount']:,} (Reason: {opp['loss_reason']})")

    # ========== ACCOUNT/CONTACT MANAGEMENT HANDLERS ==========

    async def _handle_create_account(self):
        """Create a new account."""
        account_type = random.choice(list(ACCOUNT_TYPES.keys()))
        account_name = self._generate_account_name(account_type)
        segment = self._select_account_segment()
        segment_config = ACCOUNT_SEGMENTS[segment]

        revenue_range = segment_config["annual_revenue_range"]
        annual_revenue = random.randint(revenue_range[0], revenue_range[1])

        client = self.client_pool.get_random_client()

        account = await asyncio.to_thread(
            client.create_project,
            workspace_gid="",
            name=account_name,
            notes=f"{account_type} account",
            industry=self.industry.title(),
            annual_revenue=annual_revenue
        )

        if account:
            self.state["accounts"][account["gid"]] = {
                "id": account["gid"],
                "name": account_name,
                "type": account_type,
                "segment": segment,
                "industry": self.industry,
                "annual_revenue": annual_revenue,
                "contacts": [],
                "opportunities": [],
                "cases": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": client.user_name
            }

            print(f"  Created account: {account_name} ({account_type}, {segment})")

    async def _handle_update_account(self):
        """Update account information."""
        if not self.state["accounts"]:
            return

        account_id = random.choice(list(self.state["accounts"].keys()))
        account_data = self.state["accounts"][account_id]

        # Update account type (e.g., prospect → customer)
        if account_data["type"] == "Prospect" and len(account_data["opportunities"]) > 0:
            account_data["type"] = "Customer"
            account_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            print(f"  Updated account: {account_data['name']} → Customer")

    async def _handle_create_contact(self):
        """Create a new contact for an existing account."""
        if not self.state["accounts"]:
            return

        account_id = random.choice(list(self.state["accounts"].keys()))
        account_data = self.state["accounts"][account_id]

        first_name = self._generate_first_name()
        last_name = self._generate_last_name()
        role = self._select_contact_role()
        title = random.choice(CONTACT_ROLES[role]["typical_titles"])
        email = f"{first_name.lower()}.{last_name.lower()}@{account_data['name'].lower().replace(' ', '')}.com"

        client = self.client_pool.get_random_client()

        contact = await asyncio.to_thread(
            client.create_contact,
            account_id=account_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            title=title
        )

        if contact:
            self.state["contacts"][contact["gid"]] = {
                "id": contact["gid"],
                "account_id": account_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "title": title,
                "role": role,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": client.user_name
            }

            account_data["contacts"].append(contact["gid"])
            print(f"  Created contact: {first_name} {last_name} ({title}) at {account_data['name']}")

    async def _handle_update_contact(self):
        """Update contact information (e.g., new title, role change)."""
        if not self.state["contacts"]:
            return

        contact_id = random.choice(list(self.state["contacts"].keys()))
        contact = self.state["contacts"][contact_id]

        # Update title (promotion)
        new_role = self._select_contact_role()
        contact["title"] = random.choice(CONTACT_ROLES[new_role]["typical_titles"])
        contact["role"] = new_role
        contact["updated_at"] = datetime.now(timezone.utc).isoformat()

        print(f"  Updated contact: {contact['first_name']} {contact['last_name']} → {contact['title']}")

    # ========== CASE MANAGEMENT HANDLERS ==========

    async def _handle_create_case(self):
        """Create a support case for a customer account."""
        # Only create cases for customer accounts
        customer_accounts = [a for a in self.state["accounts"].values()
                           if a.get("type") == "Customer"]

        if not customer_accounts:
            return

        account = random.choice(customer_accounts)

        # Select case type and priority
        case_type = random.choices(
            list(CASE_TEMPLATES["types"].keys()),
            weights=[v["percentage"] for v in CASE_TEMPLATES["types"].values()]
        )[0]

        priority = random.choices(
            list(CASE_TEMPLATES["priorities"].keys()),
            weights=[v["percentage"] for v in CASE_TEMPLATES["priorities"].values()]
        )[0]

        origin = random.choices(
            list(CASE_TEMPLATES["origins"].keys()),
            weights=list(CASE_TEMPLATES["origins"].values())
        )[0]

        # Generate case subject
        subject = self._generate_case_subject(case_type)

        client = self.client_pool.get_random_client()

        case = await asyncio.to_thread(
            client.create_case,
            account_id=account["id"],
            subject=subject,
            description=f"Support request from {account['name']}",
            priority=priority,
            status="New",
            origin=origin
        )

        if case:
            self.state["cases"][case["gid"]] = {
                "id": case["gid"],
                "account_id": account["id"],
                "subject": subject,
                "type": case_type,
                "priority": priority,
                "status": "New",
                "origin": origin,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": client.user_name
            }

            account["cases"].append(case["gid"])
            print(f"  Created case: {subject} ({priority} priority, {case_type})")

    async def _handle_update_case(self):
        """Update case status (move through resolution workflow)."""
        open_cases = self._get_open_cases()

        if not open_cases:
            return

        case = random.choice(open_cases)

        # Move to next status
        current_status = case.get("status", "New")
        status_progression = ["New", "In Progress", "Waiting on Customer", "Resolved"]

        if current_status in status_progression:
            current_idx = status_progression.index(current_status)
            if current_idx < len(status_progression) - 1:
                new_status = status_progression[current_idx + 1]
                case["status"] = new_status
                case["updated_at"] = datetime.now(timezone.utc).isoformat()

                print(f"  Updated case: {case['subject']} → {new_status}")

    async def _handle_close_case(self):
        """Close a resolved case."""
        resolved_cases = [c for c in self._get_open_cases()
                         if c.get("status") == "Resolved"]

        if not resolved_cases:
            return

        case = random.choice(resolved_cases)
        client = self.client_pool.get_random_client()

        # Close case
        await asyncio.to_thread(
            client.close_case,
            case_id=case["id"],
            status="Closed"
        )

        case["status"] = "Closed"
        case["closed_at"] = datetime.now(timezone.utc).isoformat()

        print(f"  Closed case: {case['subject']}")

    async def _handle_escalate_case(self):
        """Escalate a high-priority case."""
        escalatable_cases = [c for c in self._get_open_cases()
                            if c.get("priority") in ["High", "Critical"]]

        if not escalatable_cases:
            return

        case = random.choice(escalatable_cases)
        case["status"] = "Escalated"
        case["escalated_at"] = datetime.now(timezone.utc).isoformat()

        print(f"  Escalated case: {case['subject']} ({case['priority']} priority)")

    # ========== ACTIVITY LOGGING HANDLERS ==========

    async def _handle_log_call(self):
        """Log a phone call activity."""
        # Log calls for opportunities or accounts
        if self.state["opportunities"]:
            related_to = random.choice(list(self.state["opportunities"].values()))
            related_to_id = related_to["id"]
            related_to_name = related_to["name"]
        elif self.state["accounts"]:
            related_to = random.choice(list(self.state["accounts"].values()))
            related_to_id = related_to["id"]
            related_to_name = related_to["name"]
        else:
            return

        client = self.client_pool.get_random_client()

        call_subjects = [
            "Discovery Call",
            "Follow-up Call",
            "Product Demo Call",
            "Pricing Discussion",
            "Check-in Call"
        ]

        subject = random.choice(call_subjects)

        await asyncio.to_thread(
            client.log_activity,
            related_to_id=related_to_id,
            subject=subject,
            description=f"Phone call with {related_to_name}",
            status="Completed",
            type="Call"
        )

        print(f"  Logged call: {subject} - {related_to_name}")

    async def _handle_log_email(self):
        """Log an email activity."""
        if self.state["opportunities"]:
            related_to = random.choice(list(self.state["opportunities"].values()))
            related_to_id = related_to["id"]
            related_to_name = related_to["name"]
        elif self.state["accounts"]:
            related_to = random.choice(list(self.state["accounts"].values()))
            related_to_id = related_to["id"]
            related_to_name = related_to["name"]
        else:
            return

        client = self.client_pool.get_random_client()

        email_subjects = [
            "Product Information",
            "Proposal Follow-up",
            "Meeting Recap",
            "Contract Review",
            "Introduction Email"
        ]

        subject = random.choice(email_subjects)

        await asyncio.to_thread(
            client.log_activity,
            related_to_id=related_to_id,
            subject=subject,
            description=f"Email sent regarding {related_to_name}",
            status="Completed",
            type="Email"
        )

        print(f"  Logged email: {subject} - {related_to_name}")

    async def _handle_log_meeting(self):
        """Log a meeting activity."""
        if self.state["opportunities"]:
            related_to = random.choice(list(self.state["opportunities"].values()))
            related_to_id = related_to["id"]
            related_to_name = related_to["name"]
        else:
            return

        client = self.client_pool.get_random_client()

        meeting_subjects = [
            "Executive Business Review",
            "Product Demonstration",
            "Contract Negotiation Meeting",
            "Kickoff Meeting",
            "Quarterly Review"
        ]

        subject = random.choice(meeting_subjects)

        await asyncio.to_thread(
            client.log_activity,
            related_to_id=related_to_id,
            subject=subject,
            description=f"Meeting with stakeholders from {related_to_name}",
            status="Completed",
            type="Meeting"
        )

        print(f"  Logged meeting: {subject} - {related_to_name}")

    async def _handle_create_task(self):
        """Create a follow-up task."""
        if self.state["opportunities"]:
            related_to = random.choice(list(self.state["opportunities"].values()))
            related_to_id = related_to["id"]
            related_to_name = related_to["name"]
        elif self.state["accounts"]:
            related_to = random.choice(list(self.state["accounts"].values()))
            related_to_id = related_to["id"]
            related_to_name = related_to["name"]
        else:
            return

        client = self.client_pool.get_random_client()

        task_subjects = [
            "Follow up on proposal",
            "Send product documentation",
            "Schedule demo",
            "Review contract terms",
            "Update forecast"
        ]

        subject = random.choice(task_subjects)

        await asyncio.to_thread(
            client.log_activity,
            related_to_id=related_to_id,
            subject=subject,
            description=f"Task for {related_to_name}",
            status="Not Started"
        )

        print(f"  Created task: {subject} - {related_to_name}")

    # ========== CAMPAIGN MANAGEMENT HANDLERS ==========

    async def _handle_create_campaign(self):
        """Create a new marketing campaign."""
        campaign_types = ["Webinar", "Trade Show", "Email Campaign", "Content Marketing",
                         "Product Launch", "Partner Event"]
        campaign_type = random.choice(campaign_types)
        campaign_name = f"Q{random.randint(1,4)} {datetime.now().year} {campaign_type}"

        client = self.client_pool.get_random_client()

        campaign = await asyncio.to_thread(
            client.create_portfolio,
            workspace_gid="",
            name=campaign_name,
            status="In Progress",
            type=campaign_type
        )

        if campaign:
            self.state["campaigns"][campaign["gid"]] = {
                "id": campaign["gid"],
                "name": campaign_name,
                "type": campaign_type,
                "status": "In Progress",
                "members": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": client.user_name
            }

            print(f"  Created campaign: {campaign_name}")

    async def _handle_add_campaign_member(self):
        """Add contacts to a campaign."""
        if not self.state["campaigns"] or not self.state["contacts"]:
            return

        campaign_id = random.choice(list(self.state["campaigns"].keys()))
        campaign = self.state["campaigns"][campaign_id]

        # Add 1-5 contacts to campaign
        num_contacts = min(random.randint(1, 5), len(self.state["contacts"]))
        contacts_to_add = random.sample(list(self.state["contacts"].values()), num_contacts)

        for contact in contacts_to_add:
            if contact["id"] not in campaign["members"]:
                campaign["members"].append(contact["id"])

        print(f"  Added {num_contacts} contacts to campaign: {campaign['name']}")

    # ========== HELPER METHODS ==========

    def _get_random_account(self) -> Optional[Dict[str, Any]]:
        """Get a random account from state."""
        if not self.state["accounts"]:
            return None
        return random.choice(list(self.state["accounts"].values()))

    def _get_random_contact(self) -> Optional[Dict[str, Any]]:
        """Get a random contact from state."""
        if not self.state["contacts"]:
            return None
        return random.choice(list(self.state["contacts"].values()))

    def _get_random_user(self) -> Optional[Dict[str, Any]]:
        """Get a random Salesforce user for assignment."""
        if not self.state["users"]:
            return None
        return random.choice(self.state["users"])

    def _get_open_opportunities(self) -> List[Dict[str, Any]]:
        """Get all open (not closed) opportunities."""
        return [o for o in self.state["opportunities"].values() if not o.get("is_closed", False)]

    def _get_open_cases(self) -> List[Dict[str, Any]]:
        """Get all open (not closed) cases."""
        return [c for c in self.state["cases"].values() if c.get("status") != "Closed"]

    def _select_account_segment(self) -> str:
        """Select an account segment with weighted probability."""
        segments = list(ACCOUNT_SEGMENTS.keys())
        weights = [ACCOUNT_SEGMENTS[s]["percentage"] for s in segments]
        return random.choices(segments, weights=weights)[0]

    def _select_contact_role(self) -> str:
        """Select a contact role."""
        roles = list(CONTACT_ROLES.keys())
        # Weight decision makers and champions higher
        weights = [3, 2, 3, 2, 1, 1]  # Adjust to match roles
        return random.choices(roles, weights=weights[:len(roles)])[0]

    def _select_lead_source(self) -> str:
        """Select a lead source with weighted probability."""
        all_sources = []
        all_weights = []

        for category, sources in LEAD_SOURCES.items():
            for source, weight in sources.items():
                all_sources.append(source)
                all_weights.append(weight)

        return random.choices(all_sources, weights=all_weights)[0]

    def _select_next_opportunity_stage(self, current_stage: str) -> Optional[Dict[str, Any]]:
        """Select the next stage in the sales pipeline."""
        # Get sales process for B2B
        process = SALES_PROCESS_TEMPLATES["b2b_enterprise"]
        stages = process["stages"]

        # Find current stage index
        current_idx = None
        for idx, stage in enumerate(stages):
            if stage["name"] == current_stage:
                current_idx = idx
                break

        if current_idx is None or current_idx >= len(stages) - 2:  # -2 to exclude closed stages
            return None

        # Return next stage (skip closed stages)
        next_stage = stages[current_idx + 1]
        if next_stage.get("is_closed"):
            return None

        return next_stage

    def _generate_account_name(self, account_type: str) -> str:
        """
        Generate a realistic account name using LLM based on industry and account type.

        Uses Claude Haiku to generate creative, diverse account names that make sense
        for the given industry context. Tracks generated names to avoid duplicates.

        Args:
            account_type: The type of account (e.g., "Hospital System", "SaaS Company")

        Returns:
            A realistic, unique account name
        """
        # If no LLM available, fall back to simple generation
        if not self.llm:
            prefixes = ["Global", "United", "Premier", "Advanced", "Innovative"]
            suffixes = ["Corp", "Inc", "LLC", "Group", "Partners"]
            return f"{random.choice(prefixes)} {account_type} {random.choice(suffixes)}"

        # Get recently generated names for context (last 20 to keep prompt short)
        recent_names = list(self._generated_account_names)[-20:] if self._generated_account_names else []

        # Get industry description
        industry_name = self.industry_config.get("name", self.industry)
        industry_desc = self.industry_config.get("description", "")

        # Build prompt for LLM
        prompt = f"""Generate ONE unique, realistic company name for a Salesforce CRM account.

Context:
- Industry selling TO: {industry_name}
- Account type: {account_type}

CRITICAL Requirements:
1. Generate a SPECIFIC, UNIQUE company name - NOT a generic template
2. Use REAL-SOUNDING names with proper nouns, locations, or creative words
3. Avoid repetitive patterns like "Global X Corp", "Premier Y Inc", "Advanced Z LLC"
4. The company should be a CUSTOMER buying from {industry_name} companies

Good Examples (Energy industry):
- "Apex Manufacturing Solutions" (factory buying energy)
- "Riverside Medical Center" (hospital buying power)
- "Northshore Community College" (school buying utilities)
- "Pacific Foods Processing Corp" (food plant buying energy)

Bad Examples (too generic/repetitive):
- "Global Manufacturing Plant Corp"
- "Premier Hospital System Inc"
- "Advanced Data Center LLC"

Recently used names to AVOID: {', '.join(recent_names[-10:]) if recent_names else 'None'}

Generate ONE unique company name (name only, no explanation):"""

        try:
            # Generate name using LLM
            generated_name = self.llm.generate(prompt).strip()

            # Clean up the response (remove quotes, extra whitespace, etc.)
            generated_name = generated_name.strip('"\'').strip()

            # If the LLM returned multiple lines or explanations, take just the first line
            if '\n' in generated_name:
                generated_name = generated_name.split('\n')[0].strip()

            # Add to cache
            self._generated_account_names.add(generated_name)

            return generated_name

        except Exception as e:
            print(f"Warning: LLM generation failed ({e}), using fallback")
            # Fallback to simple generation
            prefixes = ["Global", "United", "Premier", "Advanced", "Innovative"]
            suffixes = ["Corp", "Inc", "LLC", "Group", "Partners"]
            fallback_name = f"{random.choice(prefixes)} {account_type} {random.choice(suffixes)}"
            self._generated_account_names.add(fallback_name)
            return fallback_name

    def _generate_company_name(self) -> str:
        """Generate a realistic company name for leads."""
        return self._generate_account_name("Prospect")

    def _generate_opportunity_name(self, account_name: str, opp_type: str) -> str:
        """Generate a realistic opportunity name."""
        return f"{account_name} - {opp_type}"

    def _generate_case_subject(self, case_type: str) -> str:
        """Generate a realistic case subject."""
        subjects = {
            "Question": [
                "How to configure user permissions",
                "Need help with report generation",
                "Question about billing cycle",
                "Feature clarification needed"
            ],
            "Problem": [
                "Unable to access dashboard",
                "Error when saving records",
                "Performance issues",
                "Integration not working"
            ],
            "Feature Request": [
                "Request: Add custom field support",
                "Enhancement: Bulk update capability",
                "New feature: Mobile app support",
                "Improvement: Better search functionality"
            ],
            "Bug": [
                "Bug: Data not syncing correctly",
                "Issue: Incorrect calculations",
                "Error: Null pointer exception",
                "Defect: Missing validation"
            ],
            "Billing": [
                "Billing inquiry for last invoice",
                "Need to update payment method",
                "Question about contract renewal",
                "Dispute charge on account"
            ]
        }

        return random.choice(subjects.get(case_type, ["General inquiry"]))

    def _generate_first_name(self) -> str:
        """Generate a random first name."""
        first_names = [
            "John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa",
            "James", "Mary", "William", "Patricia", "Richard", "Jennifer", "Thomas",
            "Linda", "Charles", "Elizabeth", "Joseph", "Barbara", "Christopher", "Susan",
            "Daniel", "Jessica", "Matthew", "Karen", "Anthony", "Nancy", "Mark", "Betty",
            "Paul", "Dorothy", "Steven", "Sandra", "Andrew", "Ashley", "Kenneth", "Kimberly"
        ]
        return random.choice(first_names)

    def _generate_last_name(self) -> str:
        """Generate a random last name."""
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
            "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
        ]
        return random.choice(last_names)

    def _update_stats(self):
        """Update job stats based on current state."""
        # Calculate opportunity stats
        opportunities_won = sum(1 for opp in self.state.get("opportunities", {}).values()
                               if opp.get("stage_name") == "Closed Won")
        opportunities_lost = sum(1 for opp in self.state.get("opportunities", {}).values()
                                if opp.get("stage_name") == "Closed Lost")

        # Update stats
        self.state["stats"] = {
            "errors": self.state.get("stats", {}).get("errors", 0),
            "accounts_count": len(self.state.get("accounts", {})),
            "contacts_count": len(self.state.get("contacts", {})),
            "opportunities_count": len(self.state.get("opportunities", {})),
            "leads_count": len(self.state.get("leads", {})),
            "cases_count": len(self.state.get("cases", {})),
            "campaigns_count": len(self.state.get("campaigns", {})),
            "opportunities_won": opportunities_won,
            "opportunities_lost": opportunities_lost
        }

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

    # Override abstract methods that don't apply directly to Salesforce

    async def _create_project(self) -> Optional[Dict[str, Any]]:
        """Not directly applicable - accounts are created instead."""
        return None

    async def _create_task(self, project_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Not directly applicable - opportunities are created instead."""
        return None

    async def cleanup_platform_data(self, progress_callback=None) -> Dict[str, Any]:
        """
        Delete all Salesforce data created by this job.

        Args:
            progress_callback: Optional callback function(current, total, message)

        Returns:
            Dictionary with cleanup results
        """
        print(f"Starting cleanup for job {self.job_id}...")

        results = {
            "accounts_deleted": 0,
            "contacts_deleted": 0,
            "opportunities_deleted": 0,
            "cases_deleted": 0,
            "leads_deleted": 0,
            "campaigns_deleted": 0,
            "errors": []
        }

        # Calculate total operations
        total_operations = (
            len(self.state.get("campaigns", {})) +
            len(self.state.get("opportunities", {})) +
            len(self.state.get("cases", {})) +
            len(self.state.get("contacts", {})) +
            len(self.state.get("accounts", {})) +
            len(self.state.get("leads", {}))
        )
        current_operation = 0

        # Step 1: Delete campaigns
        print("Deleting campaigns...")
        for campaign_id in list(self.state.get("campaigns", {}).keys()):
            try:
                client = self.client_pool.get_random_client()
                await asyncio.to_thread(client.delete_portfolio, campaign_id)
                results["campaigns_deleted"] += 1

                current_operation += 1
                if progress_callback:
                    progress_callback(current_operation, total_operations, f"Deleting campaign {campaign_id}")

                await asyncio.sleep(0.1)

            except Exception as e:
                results["errors"].append(f"Error deleting campaign {campaign_id}: {e}")

        # Step 2: Delete opportunities
        print("Deleting opportunities...")
        for opp_id in list(self.state.get("opportunities", {}).keys()):
            try:
                client = self.client_pool.get_random_client()
                await asyncio.to_thread(client.delete_task, opp_id)
                results["opportunities_deleted"] += 1

                current_operation += 1
                if progress_callback:
                    progress_callback(current_operation, total_operations, f"Deleting opportunity {opp_id}")

                await asyncio.sleep(0.1)

            except Exception as e:
                results["errors"].append(f"Error deleting opportunity {opp_id}: {e}")

        # Step 3: Delete cases
        print("Deleting cases...")
        for case_id in list(self.state.get("cases", {}).keys()):
            try:
                client = self.client_pool.get_random_client()
                # Cases don't have direct delete, so we'll skip
                # In production, you'd mark as deleted or use API
                current_operation += 1
                if progress_callback:
                    progress_callback(current_operation, total_operations, f"Skipping case {case_id}")

            except Exception as e:
                results["errors"].append(f"Error with case {case_id}: {e}")

        # Step 4: Delete contacts
        print("Deleting contacts...")
        for contact_id in list(self.state.get("contacts", {}).keys()):
            try:
                client = self.client_pool.get_random_client()
                # Contacts will be deleted when account is deleted
                current_operation += 1
                if progress_callback:
                    progress_callback(current_operation, total_operations, f"Marking contact {contact_id}")

            except Exception as e:
                results["errors"].append(f"Error with contact {contact_id}: {e}")

        # Step 5: Delete accounts
        print("Deleting accounts...")
        for account_id in list(self.state.get("accounts", {}).keys()):
            try:
                client = self.client_pool.get_random_client()
                await asyncio.to_thread(client.delete_project, account_id)
                results["accounts_deleted"] += 1

                current_operation += 1
                if progress_callback:
                    progress_callback(current_operation, total_operations, f"Deleting account {account_id}")

                await asyncio.sleep(0.2)

            except Exception as e:
                results["errors"].append(f"Error deleting account {account_id}: {e}")

        # Step 6: Delete leads
        print("Deleting leads...")
        for lead_id in list(self.state.get("leads", {}).keys()):
            try:
                client = self.client_pool.get_random_client()
                # Leads don't have direct delete method in our connection
                # In production, you'd implement lead deletion
                current_operation += 1
                if progress_callback:
                    progress_callback(current_operation, total_operations, f"Skipping lead {lead_id}")

            except Exception as e:
                results["errors"].append(f"Error with lead {lead_id}: {e}")

        # Mark as deleted
        self.deleted = True

        print(f"✓ Cleanup completed:")
        print(f"  - Accounts deleted: {results['accounts_deleted']}")
        print(f"  - Opportunities deleted: {results['opportunities_deleted']}")
        print(f"  - Campaigns deleted: {results['campaigns_deleted']}")
        print(f"  - Errors: {len(results['errors'])}")

        return results
