#!/usr/bin/env python3
"""
Example script demonstrating Salesforce Connection usage.
Shows common CRM workflows and operations.
"""

from salesforce_connection import (
    SalesforceConnection,
    SalesforceClientPool,
    SalesforceAPIError,
    SalesforceRateLimitError
)


def example_basic_connection():
    """Example: Basic connection and validation."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Connection")
    print("=" * 60)

    client = SalesforceConnection(
        api_key='',  # Not used
        user_name="Sales Manager",
        username="manager@company.com",
        password="your_password",
        security_token="your_security_token",
        domain="login"  # Use 'test' for sandbox
    )

    # Validate connection
    if client.validate_token():
        print("✓ Connected to Salesforce")

        # Get user info
        user = client.get_user_info()
        print(f"✓ User: {user['name']} ({user['email']})")

        # Check API usage
        usage = client.get_api_usage()
        print(f"✓ API Usage: {usage['used']}/{usage['daily_limit']} "
              f"({usage['percentage_used']:.1f}%)")
    else:
        print("✗ Connection failed")

    return client


def example_account_workflow(client):
    """Example: Complete account (project) workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Account Management Workflow")
    print("=" * 60)

    try:
        # Create new account (customer)
        print("\n1. Creating new account...")
        account = client.create_project(
            workspace_gid='',
            name="Acme Corporation",
            notes="Enterprise manufacturing company - high value prospect",
            industry="Manufacturing",
            annual_revenue=5000000,
            phone="415-555-1234",
            website="https://acme.com",
            billing_city="San Francisco",
            billing_state="CA",
            billing_country="USA"
        )
        print(f"✓ Created account: {account['name']} (ID: {account['gid']})")

        # Get all accounts
        print("\n2. Querying all accounts...")
        result = client.execute_soql("SELECT Id, Name, Industry FROM Account LIMIT 5")
        print(f"✓ Found {result['totalSize']} accounts:")
        for acc in result['records']:
            print(f"   - {acc['Name']} ({acc.get('Industry', 'N/A')})")

        return account

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")
        return None


def example_opportunity_workflow(client, account):
    """Example: Complete opportunity (task) workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Opportunity Management Workflow")
    print("=" * 60)

    if not account:
        print("⚠ No account provided, skipping")
        return None

    try:
        # Create opportunity
        print("\n1. Creating opportunity...")
        opportunity = client.create_task(
            project_gid=account['gid'],
            name="Q1 2025 Software License Deal",
            notes="Annual enterprise software license renewal opportunity",
            amount=250000,
            stage="Prospecting",
            close_date="2025-03-31",
            probability=60,
            type="Renewal"
        )
        print(f"✓ Created opportunity: {opportunity['name']}")
        print(f"   ID: {opportunity['gid']}")

        # Update opportunity stage
        print("\n2. Moving opportunity through sales pipeline...")
        stages = ["Qualification", "Needs Analysis", "Proposal/Price Quote"]
        for stage in stages:
            client.update_opportunity_stage(opportunity['gid'], stage)
            print(f"✓ Updated stage to: {stage}")

        # Update opportunity amount
        print("\n3. Updating deal size...")
        client.update_task(opportunity['gid'], {
            'amount': 300000,
            'probability': 85
        })
        print(f"✓ Updated: $300,000 (85% probability)")

        # Get opportunity details
        print("\n4. Retrieving opportunity details...")
        opp = client.get_task(opportunity['gid'])
        print(f"✓ Opportunity: {opp['name']}")
        print(f"   Stage: {opp['stage']}")
        print(f"   Amount: ${opp['amount']:,}")
        print(f"   Close Date: {opp['close_date']}")

        return opportunity

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")
        return None


def example_lead_conversion(client, account):
    """Example: Lead creation and conversion workflow."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Lead Conversion Workflow")
    print("=" * 60)

    try:
        # Create lead
        print("\n1. Creating new lead...")
        lead = client.create_lead(
            first_name="John",
            last_name="Smith",
            company="Tech Innovations Inc",
            email="john.smith@techinnovations.com",
            phone="650-555-9876",
            status="Open - Not Contacted",
            lead_source="Website"
        )
        print(f"✓ Created lead: {lead['name']} at {lead['company']}")
        print(f"   ID: {lead['gid']}")

        # Convert lead
        print("\n2. Converting lead to Account, Contact, and Opportunity...")
        conversion = client.convert_lead(
            lead_id=lead['gid'],
            create_opportunity=True,
            opportunity_name=f"{lead['company']} - New Business",
            close_date="2025-06-30"
        )
        print(f"✓ Lead converted successfully:")
        print(f"   Account ID: {conversion['account_id']}")
        print(f"   Contact ID: {conversion['contact_id']}")
        print(f"   Opportunity ID: {conversion['opportunity_id']}")

        return conversion

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")
        return None


def example_activity_tracking(client, opportunity):
    """Example: Activity and comment tracking."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Activity Tracking")
    print("=" * 60)

    if not opportunity:
        print("⚠ No opportunity provided, skipping")
        return

    try:
        # Log a call activity
        print("\n1. Logging call activity...")
        activity = client.log_activity(
            related_to_id=opportunity['gid'],
            subject="Discovery Call with Decision Maker",
            description="Discussed business requirements, pain points, and budget. "
                       "Customer is very interested and wants a demo next week.",
            type="Call",
            status="Completed",
            activity_date="2025-01-15"
        )
        print(f"✓ Logged activity: {activity['subject']}")

        # Add comment/note
        print("\n2. Adding opportunity note...")
        comment = client.add_comment(
            task_gid=opportunity['gid'],
            text="Customer confirmed budget of $300K. "
                 "Scheduling demo for Jan 22nd with CTO and CFO. "
                 "High confidence on closing this deal."
        )
        print(f"✓ Added note to opportunity")

        # Log follow-up email
        print("\n3. Logging email follow-up...")
        email = client.log_activity(
            related_to_id=opportunity['gid'],
            subject="Proposal Sent",
            description="Sent detailed proposal document with pricing and timeline. "
                       "Following up in 2 business days.",
            type="Email",
            status="Completed"
        )
        print(f"✓ Logged email activity")

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")


def example_contact_management(client, account):
    """Example: Contact management."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Contact Management")
    print("=" * 60)

    if not account:
        print("⚠ No account provided, skipping")
        return

    try:
        # Create primary contact
        print("\n1. Creating primary contact...")
        contact1 = client.create_contact(
            account_id=account['gid'],
            first_name="Sarah",
            last_name="Johnson",
            email="sarah.johnson@acme.com",
            phone="415-555-1111",
            title="VP of Operations"
        )
        print(f"✓ Created contact: {contact1['name']} ({contact1.get('email')})")

        # Create secondary contact
        print("\n2. Creating secondary contact...")
        contact2 = client.create_contact(
            account_id=account['gid'],
            first_name="Michael",
            last_name="Chen",
            email="michael.chen@acme.com",
            phone="415-555-2222",
            title="CTO"
        )
        print(f"✓ Created contact: {contact2['name']} ({contact2.get('email')})")

        # Query all contacts for account
        print("\n3. Querying all contacts for account...")
        result = client.execute_soql(f"""
            SELECT Id, Name, Email, Title
            FROM Contact
            WHERE AccountId = '{account['gid']}'
        """)
        print(f"✓ Found {result['totalSize']} contacts:")
        for contact in result['records']:
            print(f"   - {contact['Name']}: {contact.get('Title', 'N/A')}")

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")


def example_campaign_management(client, account):
    """Example: Campaign (portfolio) management."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Campaign Management")
    print("=" * 60)

    try:
        # Create campaign
        print("\n1. Creating marketing campaign...")
        campaign = client.create_portfolio(
            workspace_gid='',
            name="Q1 2025 Enterprise Outreach",
            description="Target Fortune 500 companies for product launch",
            type="Email",
            status="In Progress",
            start_date="2025-01-01",
            end_date="2025-03-31"
        )
        print(f"✓ Created campaign: {campaign['name']}")
        print(f"   ID: {campaign['gid']}")

        # Add account to campaign
        if account:
            print("\n2. Adding account to campaign...")
            client.add_project_to_portfolio(
                portfolio_gid=campaign['gid'],
                project_gid=account['gid']
            )
            print(f"✓ Added account to campaign")

        # Query campaigns
        print("\n3. Querying all active campaigns...")
        campaigns = client.get_workspace_portfolios('')
        print(f"✓ Found {len(campaigns)} active campaigns:")
        for camp in campaigns[:5]:  # Show first 5
            print(f"   - {camp['name']}: {camp['status']}")

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")


def example_case_management(client, account):
    """Example: Support case management."""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Case Management")
    print("=" * 60)

    if not account:
        print("⚠ No account provided, skipping")
        return

    try:
        # Create support case
        print("\n1. Creating support case...")
        case = client.create_case(
            account_id=account['gid'],
            subject="Software installation error on Windows 11",
            description="Customer reports error code 0x80070005 during installation. "
                       "Need urgent resolution as deployment is scheduled for next week.",
            priority="High",
            status="New",
            origin="Email"
        )
        print(f"✓ Created case: {case['subject']}")
        print(f"   ID: {case['gid']}")
        print(f"   Priority: High")

        # Close case (after resolution)
        print("\n2. Closing case after resolution...")
        client.close_case(
            case_id=case['gid'],
            status="Closed",
            resolution="Provided updated installer v2.1.5 that is compatible with Windows 11. "
                      "Customer confirmed successful installation."
        )
        print(f"✓ Case closed successfully")

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")


def example_soql_queries(client):
    """Example: Advanced SOQL queries."""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Advanced SOQL Queries")
    print("=" * 60)

    try:
        # Query high-value opportunities
        print("\n1. Querying high-value opportunities...")
        result = client.execute_soql("""
            SELECT Id, Name, StageName, Amount, CloseDate,
                   Account.Name, Owner.Name
            FROM Opportunity
            WHERE Amount > 100000
            AND IsClosed = FALSE
            ORDER BY Amount DESC
            LIMIT 5
        """)
        print(f"✓ Found {result['totalSize']} high-value opportunities:")
        for opp in result['records']:
            account_name = opp.get('Account', {}).get('Name', 'N/A')
            owner_name = opp.get('Owner', {}).get('Name', 'N/A')
            print(f"   - {opp['Name']}: ${opp.get('Amount', 0):,}")
            print(f"     Account: {account_name}, Owner: {owner_name}")

        # Query opportunities by stage
        print("\n2. Opportunities by stage...")
        result = client.execute_soql("""
            SELECT StageName, COUNT(Id) total, SUM(Amount) pipeline
            FROM Opportunity
            WHERE IsClosed = FALSE
            GROUP BY StageName
            ORDER BY SUM(Amount) DESC
        """)
        print(f"✓ Pipeline by stage:")
        for record in result['records']:
            total = record['total']
            pipeline = record.get('pipeline', 0)
            print(f"   - {record['StageName']}: {total} opps, "
                  f"${pipeline:,.2f}" if pipeline else "N/A")

        # Query recent activities
        print("\n3. Recent activities...")
        result = client.execute_soql("""
            SELECT Id, Subject, Type, Status, ActivityDate,
                   Owner.Name, What.Name
            FROM Task
            WHERE ActivityDate = THIS_WEEK
            ORDER BY ActivityDate DESC
            LIMIT 10
        """)
        print(f"✓ Found {result['totalSize']} activities this week")

    except SalesforceAPIError as e:
        print(f"✗ Error: {e}")


def example_multi_user_pool():
    """Example: Multi-user client pool."""
    print("\n" + "=" * 60)
    print("EXAMPLE 10: Multi-User Client Pool")
    print("=" * 60)

    user_credentials = {
        'sales_rep_1': {
            'username': 'rep1@company.com',
            'password': 'password1',
            'security_token': 'token1',
            'domain': 'login'
        },
        'sales_rep_2': {
            'username': 'rep2@company.com',
            'password': 'password2',
            'security_token': 'token2',
            'domain': 'login'
        },
        'sales_manager': {
            'username': 'manager@company.com',
            'password': 'password3',
            'security_token': 'token3',
            'domain': 'login'
        }
    }

    print("\n1. Initializing client pool...")
    pool = SalesforceClientPool(user_credentials)

    # Get valid users
    valid_users = pool.get_valid_user_names()
    print(f"✓ Initialized {len(valid_users)} valid clients:")
    for user in valid_users:
        print(f"   - {user}")

    # Get specific client
    print("\n2. Getting specific client...")
    rep1 = pool.get_client('sales_rep_1')
    if rep1:
        user = rep1.get_user_info()
        print(f"✓ Client for sales_rep_1: {user['name']}")

    # Get random client
    print("\n3. Getting random client...")
    random_client = pool.get_random_client()
    if random_client:
        print(f"✓ Random client: {random_client.user_name}")

    # Check total API usage
    print("\n4. Checking total API usage...")
    total_usage = pool.get_total_api_usage()
    print(f"✓ Total API usage across all clients:")
    print(f"   Used: {total_usage['total_used']}/{total_usage['total_limit']}")
    print(f"   Percentage: {total_usage['percentage_used']:.1f}%")
    print(f"   Clients: {total_usage['clients']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("SALESFORCE CONNECTION EXAMPLES")
    print("=" * 60)
    print("\nThis script demonstrates common Salesforce CRM workflows.")
    print("NOTE: Update credentials in each example function to run.")
    print("\n" + "=" * 60)

    # Note: These examples require valid credentials
    # Uncomment and update with your Salesforce credentials to run

    # # Example 1: Basic connection
    # client = example_basic_connection()
    #
    # # Example 2: Account workflow
    # account = example_account_workflow(client)
    #
    # # Example 3: Opportunity workflow
    # opportunity = example_opportunity_workflow(client, account)
    #
    # # Example 4: Lead conversion
    # conversion = example_lead_conversion(client, account)
    #
    # # Example 5: Activity tracking
    # example_activity_tracking(client, opportunity)
    #
    # # Example 6: Contact management
    # example_contact_management(client, account)
    #
    # # Example 7: Campaign management
    # example_campaign_management(client, account)
    #
    # # Example 8: Case management
    # example_case_management(client, account)
    #
    # # Example 9: SOQL queries
    # example_soql_queries(client)
    #
    # # Example 10: Multi-user pool
    # example_multi_user_pool()

    print("\n" + "=" * 60)
    print("To run examples, uncomment the function calls in main()")
    print("and update with your Salesforce credentials.")
    print("=" * 60)


if __name__ == "__main__":
    main()
