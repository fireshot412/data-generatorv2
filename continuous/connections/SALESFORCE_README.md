# Salesforce Connection Module

## Overview

The `salesforce_connection.py` module implements a comprehensive Salesforce CRM client that maps project management abstractions to CRM concepts. It extends the `BaseConnection` abstract class to provide full compatibility with the data generator framework while respecting CRM domain semantics.

## Installation

First, install the required dependency:

```bash
pip install simple-salesforce
```

## Concept Mapping

This module intelligently maps project management concepts to Salesforce CRM objects:

| Project Abstraction | Salesforce Object | Description |
|---------------------|-------------------|-------------|
| **Project** | Account | Company/customer in CRM |
| **Task** | Opportunity | Sales opportunity/deal |
| **Subtask** | Task/Contact/OpportunityLineItem | Activity record, related contact, or product line item |
| **Comment** | Task/Note/ChatterPost | Activity records, notes, or Chatter posts |
| **Section** | OpportunityStage | Sales pipeline stages (Prospecting, Qualification, Proposal, etc.) |
| **Tag** | Topic/Tag | Standard Salesforce tags and topics |
| **Custom Field** | Custom Field | Extensible CRM fields on any object |
| **Portfolio** | Campaign | Marketing campaigns grouping related opportunities |
| **Milestone** | Contract | Important business milestones or agreements |

## Authentication

The module uses OAuth 2.0 username-password flow with security token:

```python
from continuous.connections.salesforce_connection import SalesforceConnection

client = SalesforceConnection(
    api_key='',  # Not used, kept for interface compatibility
    user_name="Display Name",
    username="user@company.com",
    password="your_password",
    security_token="your_security_token",
    instance_url="https://na1.salesforce.com",  # Optional
    domain="login"  # Use "test" for sandbox
)
```

### Getting Your Security Token

1. Log in to Salesforce
2. Go to **Settings** > **My Personal Information** > **Reset My Security Token**
3. Click **Reset Security Token**
4. Check your email for the new security token

## Basic Usage

### Single Client

```python
from continuous.connections.salesforce_connection import SalesforceConnection

# Initialize connection
client = SalesforceConnection(
    api_key='',
    user_name="Sales Rep",
    username="salesrep@company.com",
    password="password123",
    security_token="abc123token",
    domain="login"
)

# Validate connection
if client.validate_token():
    print("✓ Connected to Salesforce")

    # Get user info
    user = client.get_user_info()
    print(f"Logged in as: {user['name']}")

    # Check API usage
    usage = client.get_api_usage()
    print(f"API Usage: {usage['used']}/{usage['daily_limit']}")
```

### Client Pool (Multi-User)

```python
from continuous.connections.salesforce_connection import SalesforceClientPool

# Initialize pool with multiple users
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
    }
}

pool = SalesforceClientPool(user_credentials)

# Get specific client
client = pool.get_client('sales_rep_1')

# Get random client
random_client = pool.get_random_client()

# Check total API usage
total_usage = pool.get_total_api_usage()
print(f"Total API calls across all users: {total_usage['total_used']}")
```

## CRM Operations

### Working with Accounts (Projects)

```python
# Create an account (customer/company)
account = client.create_project(
    workspace_gid='',  # Not used in Salesforce
    name="Acme Corporation",
    notes="Major enterprise customer in manufacturing",
    industry="Manufacturing",
    annual_revenue=5000000,
    phone="555-1234",
    website="https://acme.com",
    billing_city="San Francisco",
    billing_state="CA",
    billing_country="USA"
)
print(f"Created account: {account['gid']}")

# Add team members to account
user_ids = ['005...', '005...']
client.add_members_to_project(account['gid'], user_ids)

# Delete account (with all related records)
client.delete_project(account['gid'])
```

### Working with Opportunities (Tasks)

```python
# Create an opportunity
opportunity = client.create_task(
    project_gid=account['gid'],  # Account ID
    name="Q1 Software License Renewal",
    notes="Annual renewal of enterprise software licenses",
    assignee=sales_rep_id,
    amount=250000,
    stage="Prospecting",
    close_date="2025-03-31",
    probability=60,
    type="Renewal",
    lead_source="Existing Customer"
)

# Update opportunity
client.update_task(opportunity['gid'], {
    'stage': 'Qualification',
    'probability': 75,
    'amount': 300000
})

# Update opportunity stage
client.update_opportunity_stage(opportunity['gid'], 'Proposal/Price Quote')

# Get opportunity details
opp = client.get_task(opportunity['gid'])
print(f"Stage: {opp['stage']}, Amount: ${opp['amount']}")

# Close opportunity as won
client.complete_task(opportunity['gid'])

# Get all opportunities for an account
opportunities = client.get_project_tasks(account['gid'])
for opp in opportunities:
    print(f"- {opp['name']}: {opp['stage']} - ${opp['amount']}")
```

### Working with Leads

```python
# Create a lead (prospect)
lead = client.create_lead(
    first_name="John",
    last_name="Smith",
    company="Tech Startup Inc",
    email="john@techstartup.com",
    phone="555-5678",
    status="Open - Not Contacted",
    lead_source="Web"
)

# Convert lead to Account, Contact, and Opportunity
conversion = client.convert_lead(
    lead_id=lead['gid'],
    create_opportunity=True,
    opportunity_name="Tech Startup Inc - New Business",
    close_date="2025-06-30"
)

print(f"Account: {conversion['account_id']}")
print(f"Contact: {conversion['contact_id']}")
print(f"Opportunity: {conversion['opportunity_id']}")
```

### Working with Contacts

```python
# Create a contact
contact = client.create_contact(
    account_id=account['gid'],
    first_name="Jane",
    last_name="Doe",
    email="jane.doe@acme.com",
    phone="555-9876",
    title="VP of Operations"
)

# Create contact as subtask (alternate mapping)
contact_subtask = client.create_subtask(
    parent_task_gid=opportunity['gid'],
    name="contact: Jane Doe - Decision Maker",
    notes="Key decision maker for the deal",
    assignee=sales_rep_id
)
```

### Working with Activities

```python
# Log a call activity
activity = client.log_activity(
    related_to_id=opportunity['gid'],
    subject="Discovery Call",
    description="Discussed customer requirements and pain points",
    type="Call",
    status="Completed",
    activity_date="2025-01-15"
)

# Add comment/note to opportunity
comment = client.add_comment(
    task_gid=opportunity['gid'],
    text="Customer is very interested. Next step: send proposal by Friday."
)
```

### Working with Cases (Support Tickets)

```python
# Create a support case
case = client.create_case(
    account_id=account['gid'],
    subject="Software installation issue",
    description="Customer cannot install the software on Windows 11",
    priority="High",
    status="New",
    origin="Email"
)

# Close the case
client.close_case(
    case_id=case['gid'],
    status="Closed",
    resolution="Provided updated installer compatible with Windows 11"
)
```

### Working with Campaigns (Portfolios)

```python
# Create a campaign
campaign = client.create_portfolio(
    workspace_gid='',  # Not used
    name="Q1 2025 Enterprise Campaign",
    description="Target enterprise accounts for new product launch",
    type="Email",
    status="In Progress",
    start_date="2025-01-01",
    end_date="2025-03-31"
)

# Add account to campaign (links account's contacts)
client.add_project_to_portfolio(
    portfolio_gid=campaign['gid'],
    project_gid=account['gid']
)

# Get all campaigns
campaigns = client.get_workspace_portfolios('')
for camp in campaigns:
    print(f"- {camp['name']}: {camp['status']}")
```

### Working with Tags

```python
# Create a tag (topic)
tag = client.create_tag(
    workspace_gid='',
    name="Hot Lead"
)

# Add tag to opportunity
client.add_tag_to_task(
    task_gid=opportunity['gid'],
    tag_gid=tag['gid']
)

# Get all tags
tags = client.get_workspace_tags('')
```

### Working with Custom Fields

```python
# Get custom fields on Opportunity object
custom_fields = client.get_workspace_custom_fields('')
for field in custom_fields:
    if field['object'] == 'Opportunity':
        print(f"- {field['name']}: {field['type']}")

# Set custom field value
client.create_custom_field_value(
    task_gid=opportunity['gid'],
    custom_field_gid='CustomField__c',  # API name
    value="Custom Value"
)
```

### Working with Opportunity Stages (Sections)

```python
# Get all opportunity stages
stages = client.get_project_sections('')
for stage in stages:
    print(f"- {stage['name']}")

# Move opportunity to different stage
client.add_task_to_section(
    task_gid=opportunity['gid'],
    section_gid='Closed Won'
)
```

### SOQL Queries

```python
# Execute custom SOQL query
result = client.execute_soql("""
    SELECT Id, Name, StageName, Amount, CloseDate, Account.Name
    FROM Opportunity
    WHERE Amount > 100000
    AND StageName IN ('Proposal/Price Quote', 'Negotiation/Review')
    ORDER BY Amount DESC
    LIMIT 10
""")

print(f"Found {result['totalSize']} high-value opportunities:")
for opp in result['records']:
    print(f"- {opp['Name']}: ${opp['Amount']} ({opp['Account']['Name']})")
```

## API Rate Limits

Salesforce has strict daily API request limits:

- **Developer Edition**: 15,000 requests/day
- **Enterprise Edition**: 1,000,000 requests/day
- **Professional Edition**: 5,000 requests/day

The module automatically tracks API usage:

```python
# Check API usage
usage = client.get_api_usage()
print(f"Used: {usage['used']}/{usage['daily_limit']}")
print(f"Remaining: {usage['remaining']}")
print(f"Percentage: {usage['percentage_used']:.1f}%")

# For client pool
total_usage = pool.get_total_api_usage()
print(f"Total usage across {total_usage['clients']} users:")
print(f"  {total_usage['total_used']}/{total_usage['total_limit']}")
```

### Rate Limit Best Practices

1. **Monitor usage regularly** - Check `get_api_usage()` periodically
2. **Batch operations** - Use SOQL queries to retrieve multiple records at once
3. **Use bulk API** - For large data operations, consider Salesforce Bulk API
4. **Optimize queries** - Select only needed fields in SOQL
5. **Cache data** - Store frequently accessed data locally when possible

## Error Handling

The module provides custom exceptions:

```python
from continuous.connections.salesforce_connection import (
    SalesforceAPIError,
    SalesforceRateLimitError
)

try:
    account = client.create_project(
        workspace_gid='',
        name="Test Account"
    )
except SalesforceRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Wait and retry
except SalesforceAPIError as e:
    print(f"API error: {e}")
    # Handle error
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Logging

The module uses Python's `logging` module:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure for specific logger
logger = logging.getLogger('continuous.connections.salesforce_connection')
logger.setLevel(logging.INFO)
```

## Testing

Test the connection from command line:

```bash
cd /Users/joecastellanos/Documents/Projects/data\ generatorv2/continuous/connections

python salesforce_connection.py username@company.com password123 securitytoken
```

## Sandbox vs Production

For testing, use a Salesforce Sandbox:

```python
# Production
client = SalesforceConnection(
    ...,
    domain="login"
)

# Sandbox
client = SalesforceConnection(
    ...,
    domain="test"
)
```

## Important Notes

### Custom Field Creation

Custom fields require the Salesforce Metadata API, which is complex. The `create_custom_field()` method returns a placeholder. Create custom fields through the Salesforce Setup UI:

1. Setup > Object Manager > [Object] > Fields & Relationships
2. Click **New**
3. Select field type and configure

### Object Relationships

Understanding Salesforce relationships is crucial:

- **Account** - The company/customer
- **Contact** - Person associated with an Account
- **Opportunity** - Sales deal associated with an Account
- **Lead** - Prospect (not yet converted to Account/Contact)
- **Case** - Support ticket for an Account/Contact
- **Campaign** - Marketing campaign with CampaignMembers
- **Task** - Activity record (call, email, meeting, etc.)

### Data Model Differences

Salesforce has a fundamentally different data model than project management tools:

- **No Workspaces** - Salesforce is a single-tenant system per org
- **Predefined Stages** - Opportunity stages are configured in Setup
- **Complex Products** - OpportunityLineItems require Price Books and Products
- **Record Types** - Different page layouts and picklist values per record type

## Advanced Features

### Using Record Types

```python
# Query for record types
result = client.execute_soql("""
    SELECT Id, Name, DeveloperName
    FROM RecordType
    WHERE SObjectType = 'Opportunity'
""")

# Create opportunity with specific record type
opportunity = client.create_task(
    project_gid=account['gid'],
    name="Enterprise Deal",
    RecordTypeId=record_type_id
)
```

### Querying Related Records

```python
# Get opportunities with related account info
result = client.execute_soql("""
    SELECT Id, Name, StageName, Amount,
           Account.Name, Account.Industry,
           Owner.Name
    FROM Opportunity
    WHERE AccountId = '{}'
""".format(account['gid']))
```

### Working with Chatter

```python
# Add followers (Chatter)
client.add_followers(
    task_gid=opportunity['gid'],
    followers=[user_id_1, user_id_2]
)

# Remove followers
client.remove_followers(
    task_gid=opportunity['gid'],
    followers=[user_id_1]
)
```

## Troubleshooting

### Authentication Errors

```
SalesforceAPIError: Salesforce authentication failed
```

**Solutions:**
- Verify username and password
- Ensure security token is current (reset if needed)
- Check if IP address is trusted (Security > Network Access)
- Verify user has API access enabled

### API Limit Exceeded

```
SalesforceRateLimitError: Rate limit exceeded
```

**Solutions:**
- Wait until API limits reset (daily at midnight Salesforce server time)
- Reduce number of API calls
- Use bulk operations
- Contact Salesforce to increase limits

### Permission Errors

```
SalesforceAPIError: insufficient access rights
```

**Solutions:**
- Verify user has required object permissions
- Check profile and permission sets
- Ensure sharing rules allow access
- Verify field-level security

## Module Statistics

- **Total Lines**: 1,797
- **Total Methods**: 58
- **BaseConnection Methods Implemented**: 40+
- **CRM-Specific Methods**: 10+
- **Custom Exceptions**: 2

## References

- [Salesforce REST API Documentation](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- [simple-salesforce Library](https://github.com/simple-salesforce/simple-salesforce)
- [Salesforce Object Reference](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/)
- [SOQL Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/)

## License

This module is part of the data generator project and follows the same license.
