# Okta Templates Quick Reference

## Overview
Comprehensive Okta organization templates for realistic identity and access management data generation across 10 industries and 3 organization sizes.

## File Location
```
/Users/joecastellanos/Documents/Projects/data generatorv2/continuous/templates/okta_templates.py
```

## Quick Import
```python
from continuous.templates import (
    ORG_SIZE_TEMPLATES,
    OKTA_INDUSTRY_TEMPLATES,
    COMMON_APPS,
    get_app_assignment_pattern,
    generate_sample_user_profile,
    calculate_user_distribution
)
```

## Industries (10)
1. **healthcare** - Healthcare organizations, hospitals, clinics
2. **financial_services** - Banks, investment firms, insurance
3. **technology** - Software companies, SaaS providers
4. **manufacturing** - Industrial production, supply chain
5. **travel** - Airlines, hotels, hospitality
6. **retail** - Retail stores, e-commerce
7. **education** - Universities, colleges, schools
8. **government** - Federal, state, local agencies
9. **energy** - Utilities, renewable energy
10. **media** - Media companies, entertainment, studios

## Organization Sizes (3)
- **startup**: 10-50 users, 4 departments, minimal hierarchy
- **midsize**: 100-500 users, 10 departments, standard structure
- **enterprise**: 1,000-10,000 users, 16 departments, complex hierarchy

## Key Statistics
- **70+ Common Applications** across 15 categories
- **126 Departments** total across all industries
- **150 Job Roles** defined
- **204 Industry-Specific Apps**
- **14 Department Patterns** for app assignment
- **5 Role Patterns** for app assignment

## Common Usage Pattern

```python
from continuous.templates import okta_templates as okta
from continuous.connections.okta_connection import OktaConnection

# 1. Select industry and size
industry = 'healthcare'
size = 'midsize'
target_users = 200

# 2. Get configurations
industry_config = okta.get_industry_config(industry)
size_config = okta.get_org_size_config(size)

# 3. Calculate user distribution
departments = industry_config['departments'][:8]
distribution = okta.calculate_user_distribution(target_users, departments)

# 4. Initialize Okta client
client = OktaConnection(token=OKTA_TOKEN, org_url=OKTA_ORG_URL)

# 5. Create department groups
groups = {}
for dept in departments:
    group = client.create_group(name=dept, description=f"{dept} Department")
    groups[dept] = group['id']

# 6. Create users
for dept, user_count in distribution.items():
    for i in range(user_count):
        # Generate profile
        profile = okta.generate_sample_user_profile(industry, dept, size)
        
        # Create user
        user = client.create_user(profile=profile['profile'], activate=True)
        
        # Add to group
        client.add_user_to_group(groups[dept], user['id'])
        
        # Assign apps
        apps = okta.get_app_assignment_pattern(
            industry, dept, profile['profile']['title'], size
        )
        # (Map app names to IDs and assign)
```

## Helper Functions

### Configuration
- `get_org_size_config(size)` - Get org size configuration
- `get_industry_config(industry)` - Get industry configuration
- `get_group_structure_template(type)` - Get group structure

### Industry Data
- `get_departments_for_industry(industry)` - List departments
- `get_apps_for_industry(industry)` - List industry-specific apps
- `get_user_titles_for_department(industry, dept)` - Get job titles

### Generation
- `generate_sample_user_profile(industry, dept, size)` - Generate user profile
- `calculate_user_distribution(total, depts)` - Distribute users across departments
- `get_app_assignment_pattern(industry, dept, role, size)` - Get apps for user

### Utilities
- `get_all_industries()` - List all industry keys
- `get_all_org_sizes()` - List all org size keys

## App Assignment Logic

Apps are assigned based on multiple factors:
1. **Universal Apps** (everyone): Okta Dashboard, Google Workspace, Slack, Zoom
2. **Department Apps**: Engineering gets GitHub, Jira; Sales gets Salesforce, Outreach
3. **Role Apps**: Managers get Workday, BambooHR; Engineers get AWS Console
4. **Industry Apps**: Healthcare gets Epic EMR, MEDITECH; Finance gets Bloomberg Terminal

## Industry-Specific Features

### Healthcare
- Departments: Clinical, Nursing, Compliance
- Apps: Epic EMR, MEDITECH, Cerner
- Attributes: license_number, npi_number, hipaa_trained
- Compliance: HIPAA, HITECH

### Technology
- Departments: Engineering, Product, DevOps
- Apps: GitHub, Jira, AWS Console, Datadog
- Attributes: tech_stack, github_username, oncall_rotation
- Compliance: SOC2

### Financial Services
- Departments: Trading, Compliance, Risk Management
- Apps: Bloomberg Terminal, Thomson Reuters, Salesforce Financial
- Attributes: series_licenses, finra_registered, sox_trained
- Compliance: SOX, SOC2, PCI-DSS, FINRA

## Example Outputs

### Sample User Profile
```python
{
  'profile': {
    'firstName': 'Alex',
    'lastName': 'Smith',
    'email': 'alex.smith@example.com',
    'login': 'alex.smith@example.com',
    'department': 'Engineering',
    'title': 'Software Engineer',
    'employeeNumber': 'EMP6615',
    'startDate': '2023-04-30',
    'location': 'San Francisco'
  }
}
```

### Sample User Distribution (100 users, Technology)
```
Engineering: 27 users
Sales: 23 users
Customer Success: 9 users
Marketing: 8 users
IT: 8 users
HR: 6 users
```

### Sample App Assignment (Technology Engineer)
```
Universal: Okta Dashboard, Google Workspace, Slack, Zoom
Department: GitHub, Jira, Datadog, AWS Console, PagerDuty
Role: GitHub, AWS Console
Industry: CircleCI, Terraform Cloud, New Relic
Total: 18 apps
```

## Template Structure

### ORG_SIZE_TEMPLATES
```python
{
  "startup": {
    "name": "Small Startup",
    "user_count_range": (10, 50),
    "departments": [...],
    "group_structure": "standard"
  }
}
```

### INDUSTRY_TEMPLATES
```python
{
  "healthcare": {
    "name": "Healthcare",
    "departments": [...],
    "apps": [...],
    "roles": [...],
    "user_attributes": {...},
    "compliance_requirements": [...]
  }
}
```

### COMMON_APPS
```python
[
  {
    "name": "Slack",
    "category": "communication",
    "universal": True,
    "essential": True
  }
]
```

## Validation
All templates have been validated:
- ✓ All 10 industries defined
- ✓ All 3 org sizes defined
- ✓ All helper functions tested
- ✓ Profile generation works
- ✓ Distribution algorithm correct
- ✓ App assignment working
- ✓ No namespace conflicts
- ✓ Backward compatible

## Integration Points
- Works with `OktaConnection` from `continuous/connections/okta_connection.py`
- Compatible with existing Asana templates
- Exports available from `continuous/templates/__init__.py`
- No conflicts with existing code

## Next Steps
1. Use templates to design organization structure
2. Create groups based on departments/roles
3. Generate user profiles with `generate_sample_user_profile()`
4. Create users via `OktaConnection.create_user()`
5. Assign apps based on `get_app_assignment_pattern()`

## Resources
- Main file: `continuous/templates/okta_templates.py` (1,240 lines)
- Module exports: `continuous/templates/__init__.py`
- Okta client: `continuous/connections/okta_connection.py`

---
**Generated:** 2025-10-28
**Status:** Production Ready ✓
