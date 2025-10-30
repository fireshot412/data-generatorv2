# Salesforce Connection - Quick Start Guide

## Installation

### Step 1: Install Dependencies

```bash
pip install simple-salesforce
```

### Step 2: Get Salesforce Credentials

You need three pieces of information:

1. **Username** - Your Salesforce login email
2. **Password** - Your Salesforce password
3. **Security Token** - Get this from Salesforce:
   - Log in to Salesforce
   - Go to: **Settings** → **My Personal Information** → **Reset My Security Token**
   - Click **Reset Security Token**
   - Check your email for the token

### Step 3: Test Connection

```bash
cd /Users/joecastellanos/Documents/Projects/data\ generatorv2/continuous/connections

python salesforce_connection.py your_email@company.com your_password your_security_token
```

## Basic Usage

### Single Client

```python
from continuous.connections.salesforce_connection import SalesforceConnection

# Initialize
client = SalesforceConnection(
    api_key='',
    user_name="Display Name",
    username="your_email@company.com",
    password="your_password",
    security_token="your_security_token",
    domain="login"  # Use "test" for sandbox
)

# Validate
if client.validate_token():
    print("✓ Connected!")

    # Get user info
    user = client.get_user_info()
    print(f"Logged in as: {user['name']}")
```

### Multi-User Pool

```python
from continuous.connections.salesforce_connection import SalesforceClientPool

credentials = {
    'user1': {
        'username': 'user1@company.com',
        'password': 'password1',
        'security_token': 'token1',
        'domain': 'login'
    },
    'user2': {
        'username': 'user2@company.com',
        'password': 'password2',
        'security_token': 'token2',
        'domain': 'login'
    }
}

pool = SalesforceClientPool(credentials)

# Get specific user's client
client = pool.get_client('user1')

# Get random client
random_client = pool.get_random_client()
```

## Common Operations

### Create Account (Customer)

```python
account = client.create_project(
    workspace_gid='',
    name="Acme Corporation",
    notes="Enterprise customer in manufacturing",
    industry="Manufacturing",
    annual_revenue=5000000
)
```

### Create Opportunity (Deal)

```python
opportunity = client.create_task(
    project_gid=account['gid'],
    name="Q1 Software License Deal",
    notes="Enterprise software renewal",
    amount=250000,
    stage="Prospecting",
    close_date="2025-03-31"
)
```

### Create Lead

```python
lead = client.create_lead(
    first_name="John",
    last_name="Smith",
    company="Tech Startup Inc",
    email="john@startup.com",
    status="Open - Not Contacted"
)
```

### Convert Lead

```python
conversion = client.convert_lead(
    lead_id=lead['gid'],
    create_opportunity=True,
    opportunity_name="Tech Startup - New Business"
)
```

### Create Contact

```python
contact = client.create_contact(
    account_id=account['gid'],
    first_name="Jane",
    last_name="Doe",
    email="jane@acme.com",
    title="VP of Sales"
)
```

### Log Activity

```python
activity = client.log_activity(
    related_to_id=opportunity['gid'],
    subject="Discovery Call",
    description="Discussed requirements and budget",
    type="Call",
    status="Completed"
)
```

### Add Comment

```python
comment = client.add_comment(
    task_gid=opportunity['gid'],
    text="Customer is very interested. Sending proposal on Friday."
)
```

### Update Opportunity Stage

```python
client.update_opportunity_stage(opportunity['gid'], "Qualification")
```

### Execute SOQL Query

```python
result = client.execute_soql("""
    SELECT Id, Name, Amount, StageName
    FROM Opportunity
    WHERE Amount > 100000
    ORDER BY Amount DESC
    LIMIT 10
""")

for opp in result['records']:
    print(f"{opp['Name']}: ${opp['Amount']}")
```

### Check API Usage

```python
usage = client.get_api_usage()
print(f"Used: {usage['used']}/{usage['daily_limit']}")
print(f"Remaining: {usage['remaining']}")
```

## Concept Mapping Reference

| Project Term | Salesforce Object |
|--------------|-------------------|
| Project | Account |
| Task | Opportunity |
| Subtask | Task/Contact |
| Comment | Note/Task |
| Section | OpportunityStage |
| Tag | Topic |
| Portfolio | Campaign |
| Milestone | Contract |

## Error Handling

```python
from continuous.connections.salesforce_connection import (
    SalesforceAPIError,
    SalesforceRateLimitError
)

try:
    account = client.create_project(workspace_gid='', name="Test")
except SalesforceRateLimitError as e:
    print(f"Rate limit: {e}")
except SalesforceAPIError as e:
    print(f"API error: {e}")
```

## Sandbox vs Production

```python
# Production
client = SalesforceConnection(..., domain="login")

# Sandbox (for testing)
client = SalesforceConnection(..., domain="test")
```

## API Rate Limits

- **Developer Edition**: 15,000 requests/day
- **Professional Edition**: 5,000 requests/day
- **Enterprise Edition**: 1,000,000 requests/day

Monitor usage regularly:

```python
usage = client.get_api_usage()
if usage['percentage_used'] > 80:
    print("⚠ Warning: Over 80% API usage")
```

## Examples

See `salesforce_example.py` for comprehensive examples:

```bash
python salesforce_example.py
```

## Documentation

- Full documentation: `SALESFORCE_README.md`
- Code examples: `salesforce_example.py`
- Module: `salesforce_connection.py`

## Troubleshooting

### "Invalid Session ID"
- Security token expired - reset it in Salesforce Settings
- Password changed - update credentials

### "Insufficient Access"
- Check user profile permissions
- Verify object and field-level security

### "Request Limit Exceeded"
- Wait for daily limit reset (midnight Salesforce server time)
- Reduce API calls
- Use bulk operations

### Connection Timeout
- Check internet connection
- Verify Salesforce instance is accessible
- Check if IP is in trusted range (Setup → Network Access)

## Support

For issues or questions:
1. Check the full README: `SALESFORCE_README.md`
2. Review examples: `salesforce_example.py`
3. Consult Salesforce documentation: https://developer.salesforce.com/

## Next Steps

1. ✓ Install `simple-salesforce`
2. ✓ Get credentials (username, password, security token)
3. ✓ Test connection
4. ✓ Review examples in `salesforce_example.py`
5. ✓ Read full documentation in `SALESFORCE_README.md`
6. Start building your CRM integration!
