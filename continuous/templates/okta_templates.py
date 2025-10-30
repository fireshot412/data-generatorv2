#!/usr/bin/env python3
"""
Okta organization templates for realistic identity and access management data generation.

Defines organization structures across different sizes (startup, mid-size, enterprise)
and industries (healthcare, finance, technology, manufacturing, travel, retail, education,
government, energy, media).

Supports:
- User profile templates with custom attributes
- Group structures (departments, teams, roles)
- Application catalogs (universal and industry-specific)
- Realistic user distribution patterns
- App assignment patterns by department and role
"""

from typing import Dict, List, Any, Tuple
import random


# ============================================================================
# ORGANIZATION SIZE TEMPLATES
# ============================================================================

ORG_SIZE_TEMPLATES = {
    "startup": {
        "name": "Small Startup",
        "user_count_range": (10, 50),
        "description": "Small startup organization with flat structure, minimal departments, and essential SaaS tools",
        "departments": ["Engineering", "Product", "Sales", "Operations"],
        "group_structure": "standard",
        "executive_ratio": 0.15,  # 15% executives/managers
        "typical_apps_count": (8, 15),
        "locations": ["San Francisco", "Remote"],
        "has_complex_hierarchy": False,
        "custom_attributes": ["department", "title", "startDate", "location"]
    },
    "midsize": {
        "name": "Mid-Size Company",
        "user_count_range": (100, 500),
        "description": "Mid-size company with established departments, multiple teams, and comprehensive tooling",
        "departments": [
            "Engineering", "Product Management", "Sales", "Marketing",
            "Customer Success", "Finance", "HR", "IT", "Operations", "Legal"
        ],
        "group_structure": "standard",
        "executive_ratio": 0.10,  # 10% executives/managers
        "typical_apps_count": (20, 35),
        "locations": ["San Francisco", "New York", "Austin", "Remote"],
        "has_complex_hierarchy": True,
        "custom_attributes": [
            "department", "title", "manager", "employeeNumber",
            "startDate", "location", "division", "costCenter"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "user_count_range": (1000, 10000),
        "description": "Large enterprise with complex org structure, multiple divisions, global presence, and extensive app portfolio",
        "departments": [
            "Engineering", "Product Management", "Sales", "Marketing",
            "Customer Success", "Finance", "Accounting", "HR",
            "IT", "Security", "Operations", "Legal", "Compliance",
            "Procurement", "Facilities", "Business Development"
        ],
        "group_structure": "complex",
        "executive_ratio": 0.08,  # 8% executives/managers
        "typical_apps_count": (40, 80),
        "locations": [
            "San Francisco", "New York", "Austin", "Seattle", "Boston",
            "Chicago", "London", "Dublin", "Singapore", "Sydney", "Remote"
        ],
        "has_complex_hierarchy": True,
        "custom_attributes": [
            "department", "title", "manager", "employeeNumber", "startDate",
            "location", "division", "costCenter", "businessUnit", "region",
            "employeeType", "workLocation"
        ]
    }
}


# ============================================================================
# GROUP STRUCTURE TEMPLATES
# ============================================================================

GROUP_STRUCTURE_TEMPLATES = {
    "standard": {
        "description": "Standard group structure for startups and mid-size companies",
        "departments": True,  # Create department groups
        "teams": True,  # Create team groups within departments
        "roles": True,  # Create role-based groups (e.g., "Managers", "Engineers")
        "locations": False,  # Location-based groups
        "all_employees": True,  # Universal "Everyone" group
        "app_specific": False  # Groups for specific app access
    },
    "complex": {
        "description": "Complex group structure for enterprises with multiple organizational dimensions",
        "departments": True,
        "teams": True,
        "roles": True,
        "locations": True,
        "all_employees": True,
        "app_specific": True,  # Groups for specific app access
        "divisions": True,  # Division-level groups
        "projects": True  # Project-based groups
    }
}


# ============================================================================
# USER PROFILE TEMPLATES
# ============================================================================

USER_PROFILE_TEMPLATES = {
    "standard_fields": [
        "firstName",
        "lastName",
        "email",
        "login",
        "mobilePhone",
        "secondEmail"
    ],
    "custom_attributes": {
        "department": {
            "type": "string",
            "description": "User's primary department"
        },
        "title": {
            "type": "string",
            "description": "Job title"
        },
        "employeeNumber": {
            "type": "string",
            "description": "Unique employee identifier"
        },
        "manager": {
            "type": "string",
            "description": "Manager's email or user ID"
        },
        "location": {
            "type": "string",
            "description": "Primary work location"
        },
        "startDate": {
            "type": "string",
            "description": "Employment start date (ISO 8601)"
        },
        "division": {
            "type": "string",
            "description": "Business division or unit"
        },
        "costCenter": {
            "type": "string",
            "description": "Financial cost center code"
        },
        "businessUnit": {
            "type": "string",
            "description": "Business unit identifier"
        },
        "region": {
            "type": "string",
            "description": "Geographic region"
        },
        "employeeType": {
            "type": "string",
            "description": "Employment type (Full-time, Part-time, Contractor)"
        },
        "workLocation": {
            "type": "string",
            "description": "Work arrangement (Office, Remote, Hybrid)"
        }
    }
}


# ============================================================================
# COMMON APPLICATIONS
# ============================================================================

COMMON_APPS = [
    # Identity & Access
    {"name": "Okta Dashboard", "category": "identity", "universal": True, "essential": True},
    {"name": "Okta Admin Console", "category": "identity", "universal": False, "roles": ["IT", "Security"]},

    # Productivity Suites
    {"name": "Google Workspace", "category": "productivity", "universal": True, "essential": True},
    {"name": "Microsoft 365", "category": "productivity", "universal": True, "essential": True},
    {"name": "Office 365", "category": "productivity", "universal": True, "essential": True},

    # Communication
    {"name": "Slack", "category": "communication", "universal": True, "essential": True},
    {"name": "Microsoft Teams", "category": "communication", "universal": True, "essential": True},
    {"name": "Zoom", "category": "communication", "universal": True, "essential": True},
    {"name": "Webex", "category": "communication", "universal": False},
    {"name": "Discord", "category": "communication", "universal": False},

    # CRM & Sales
    {"name": "Salesforce", "category": "crm", "universal": False, "departments": ["Sales", "Marketing", "Customer Success"]},
    {"name": "HubSpot", "category": "crm", "universal": False, "departments": ["Sales", "Marketing"]},
    {"name": "Outreach", "category": "sales", "universal": False, "departments": ["Sales"]},
    {"name": "Gong", "category": "sales", "universal": False, "departments": ["Sales", "Customer Success"]},
    {"name": "LinkedIn Sales Navigator", "category": "sales", "universal": False, "departments": ["Sales", "Marketing"]},
    {"name": "ZoomInfo", "category": "sales", "universal": False, "departments": ["Sales", "Marketing"]},

    # HR & Talent
    {"name": "Workday", "category": "hr", "universal": False, "departments": ["HR", "Finance"]},
    {"name": "BambooHR", "category": "hr", "universal": False, "departments": ["HR"]},
    {"name": "Greenhouse", "category": "hr", "universal": False, "departments": ["HR"]},
    {"name": "Lever", "category": "hr", "universal": False, "departments": ["HR"]},
    {"name": "Lattice", "category": "hr", "universal": False, "departments": ["HR"]},
    {"name": "15Five", "category": "hr", "universal": False, "departments": ["HR"]},

    # Finance & Accounting
    {"name": "NetSuite", "category": "finance", "universal": False, "departments": ["Finance", "Accounting"]},
    {"name": "QuickBooks", "category": "finance", "universal": False, "departments": ["Finance", "Accounting"]},
    {"name": "Expensify", "category": "finance", "universal": False},
    {"name": "Bill.com", "category": "finance", "universal": False, "departments": ["Finance", "Accounting"]},
    {"name": "Coupa", "category": "finance", "universal": False, "departments": ["Finance", "Procurement"]},
    {"name": "Concur", "category": "finance", "universal": False},

    # Project Management
    {"name": "Asana", "category": "project_management", "universal": False},
    {"name": "Jira", "category": "project_management", "universal": False, "departments": ["Engineering", "Product"]},
    {"name": "Monday.com", "category": "project_management", "universal": False},
    {"name": "Trello", "category": "project_management", "universal": False},
    {"name": "ClickUp", "category": "project_management", "universal": False},

    # Engineering & Development
    {"name": "GitHub", "category": "engineering", "universal": False, "departments": ["Engineering"]},
    {"name": "GitLab", "category": "engineering", "universal": False, "departments": ["Engineering"]},
    {"name": "Bitbucket", "category": "engineering", "universal": False, "departments": ["Engineering"]},
    {"name": "Jenkins", "category": "engineering", "universal": False, "departments": ["Engineering"]},
    {"name": "CircleCI", "category": "engineering", "universal": False, "departments": ["Engineering"]},
    {"name": "Datadog", "category": "engineering", "universal": False, "departments": ["Engineering", "IT"]},
    {"name": "New Relic", "category": "engineering", "universal": False, "departments": ["Engineering", "IT"]},
    {"name": "PagerDuty", "category": "engineering", "universal": False, "departments": ["Engineering", "IT"]},
    {"name": "Splunk", "category": "engineering", "universal": False, "departments": ["Engineering", "IT", "Security"]},

    # Cloud Infrastructure
    {"name": "AWS Console", "category": "cloud", "universal": False, "departments": ["Engineering", "IT"]},
    {"name": "Azure Portal", "category": "cloud", "universal": False, "departments": ["Engineering", "IT"]},
    {"name": "Google Cloud Platform", "category": "cloud", "universal": False, "departments": ["Engineering", "IT"]},
    {"name": "Terraform Cloud", "category": "cloud", "universal": False, "departments": ["Engineering", "IT"]},

    # Security
    {"name": "1Password", "category": "security", "universal": True},
    {"name": "LastPass", "category": "security", "universal": True},
    {"name": "CrowdStrike", "category": "security", "universal": False, "departments": ["IT", "Security"]},
    {"name": "Duo Security", "category": "security", "universal": True},
    {"name": "Qualys", "category": "security", "universal": False, "departments": ["IT", "Security"]},

    # Marketing
    {"name": "Marketo", "category": "marketing", "universal": False, "departments": ["Marketing"]},
    {"name": "Pardot", "category": "marketing", "universal": False, "departments": ["Marketing"]},
    {"name": "Google Analytics", "category": "analytics", "universal": False, "departments": ["Marketing", "Product"]},
    {"name": "Adobe Creative Cloud", "category": "marketing", "universal": False, "departments": ["Marketing", "Design"]},
    {"name": "Canva", "category": "marketing", "universal": False, "departments": ["Marketing"]},
    {"name": "Hootsuite", "category": "marketing", "universal": False, "departments": ["Marketing"]},

    # Analytics & BI
    {"name": "Tableau", "category": "analytics", "universal": False, "departments": ["Finance", "Sales", "Marketing"]},
    {"name": "Looker", "category": "analytics", "universal": False, "departments": ["Finance", "Sales", "Marketing"]},
    {"name": "Power BI", "category": "analytics", "universal": False, "departments": ["Finance", "Sales", "Marketing"]},
    {"name": "Amplitude", "category": "analytics", "universal": False, "departments": ["Product", "Marketing"]},
    {"name": "Mixpanel", "category": "analytics", "universal": False, "departments": ["Product", "Marketing"]},

    # Customer Support
    {"name": "Zendesk", "category": "support", "universal": False, "departments": ["Customer Success", "Support"]},
    {"name": "Intercom", "category": "support", "universal": False, "departments": ["Customer Success", "Support"]},
    {"name": "Freshdesk", "category": "support", "universal": False, "departments": ["Customer Success", "Support"]},

    # Documentation & Knowledge
    {"name": "Confluence", "category": "documentation", "universal": False},
    {"name": "Notion", "category": "documentation", "universal": False},
    {"name": "Google Drive", "category": "documentation", "universal": True},
    {"name": "Dropbox", "category": "documentation", "universal": False},
    {"name": "Box", "category": "documentation", "universal": False},
]


# ============================================================================
# APP ASSIGNMENT PATTERNS
# ============================================================================

APP_ASSIGNMENT_PATTERNS = {
    "universal": [
        "Okta Dashboard",
        "Google Workspace",
        "Slack",
        "Zoom",
        "1Password",
        "Google Drive"
    ],
    "by_department": {
        "Engineering": [
            "GitHub", "Jira", "Datadog", "AWS Console", "PagerDuty",
            "Confluence", "CircleCI", "New Relic", "Terraform Cloud"
        ],
        "Product Management": [
            "Jira", "Confluence", "Amplitude", "Mixpanel", "Google Analytics",
            "Tableau", "Figma"
        ],
        "Product": [
            "Jira", "Confluence", "Amplitude", "Mixpanel", "Google Analytics"
        ],
        "Sales": [
            "Salesforce", "Outreach", "LinkedIn Sales Navigator", "ZoomInfo",
            "Gong", "Tableau"
        ],
        "Marketing": [
            "HubSpot", "Marketo", "Google Analytics", "Adobe Creative Cloud",
            "Canva", "Hootsuite", "Salesforce"
        ],
        "Customer Success": [
            "Salesforce", "Zendesk", "Intercom", "Gong", "Tableau"
        ],
        "Support": [
            "Zendesk", "Intercom", "Freshdesk", "Salesforce"
        ],
        "Finance": [
            "NetSuite", "QuickBooks", "Expensify", "Bill.com", "Coupa",
            "Tableau", "Workday"
        ],
        "Accounting": [
            "NetSuite", "QuickBooks", "Bill.com", "Expensify"
        ],
        "HR": [
            "Workday", "BambooHR", "Greenhouse", "Lever", "Lattice", "15Five"
        ],
        "IT": [
            "Okta Admin Console", "AWS Console", "Datadog", "PagerDuty",
            "Splunk", "CrowdStrike"
        ],
        "Security": [
            "Okta Admin Console", "CrowdStrike", "Qualys", "Splunk"
        ],
        "Legal": [
            "Salesforce", "Confluence"
        ],
        "Operations": [
            "Monday.com", "Asana", "Tableau"
        ]
    },
    "by_role": {
        "Manager": ["Workday", "BambooHR", "Lattice", "Tableau"],
        "Executive": ["Salesforce", "Tableau", "Workday", "Looker"],
        "Engineer": ["GitHub", "Jira", "AWS Console", "Datadog"],
        "Designer": ["Adobe Creative Cloud", "Figma", "Canva"],
        "Analyst": ["Tableau", "Looker", "Power BI", "Google Analytics"]
    }
}


# ============================================================================
# INDUSTRY TEMPLATES
# ============================================================================

INDUSTRY_TEMPLATES = {
    "healthcare": {
        "name": "Healthcare",
        "description": "Healthcare organizations including hospitals, clinics, and medical practices",
        "departments": [
            "Clinical", "Nursing", "Administration", "Billing", "IT",
            "Compliance", "Research", "Quality Assurance", "Patient Services", "Pharmacy"
        ],
        "apps": [
            # Industry-specific
            "Epic EMR", "MEDITECH", "Cerner", "Allscripts", "Athenahealth",
            "Salesforce Health Cloud", "Veeva CRM", "eClinicalWorks",
            "NextGen Healthcare", "McKesson", "Oracle Health",
            # Compliance & security
            "Qualys", "CrowdStrike", "Splunk", "1Password",
            # General business
            "Workday", "Salesforce", "Tableau", "Microsoft 365",
            "Slack", "Zoom", "Confluence"
        ],
        "roles": [
            "Physician", "Surgeon", "Nurse Practitioner", "Registered Nurse",
            "Medical Assistant", "Administrator", "Billing Specialist",
            "Compliance Officer", "Research Coordinator", "IT Specialist",
            "Quality Analyst", "Patient Coordinator", "Pharmacist",
            "Lab Technician", "Medical Records Clerk"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "license_number": "string",
            "specialty": "string",
            "clinic_location": "string",
            "npi_number": "string",
            "dea_number": "string",
            "hipaa_trained": "boolean",
            "hipaa_training_date": "date"
        },
        "group_patterns": {
            "clinical": ["Physicians", "Nurses", "Medical Assistants"],
            "administrative": ["Billing", "Patient Services", "Administration"],
            "it_security": ["IT", "Compliance", "Security"],
            "specialty": ["Cardiology", "Oncology", "Pediatrics", "Emergency"]
        },
        "compliance_requirements": ["HIPAA", "HITECH"],
        "sensitive_data": True
    },

    "financial_services": {
        "name": "Financial Services",
        "description": "Banks, investment firms, insurance companies, and financial technology companies",
        "departments": [
            "Trading", "Investment Banking", "Wealth Management", "Retail Banking",
            "Compliance", "Risk Management", "IT", "Operations",
            "Audit", "Legal", "Customer Service", "Finance"
        ],
        "apps": [
            # Industry-specific
            "Bloomberg Terminal", "Thomson Reuters Eikon", "FactSet",
            "Salesforce Financial Services Cloud", "Workday Financial Management",
            "FIS", "Fiserv", "Jack Henry", "Temenos", "Finastra",
            "Guidewire", "Duck Creek", "Applied Epic",
            # Compliance & security
            "Qualys", "CrowdStrike", "Splunk", "Duo Security",
            # General business
            "NetSuite", "Tableau", "Microsoft 365", "Slack"
        ],
        "roles": [
            "Financial Advisor", "Portfolio Manager", "Trader", "Analyst",
            "Relationship Manager", "Compliance Officer", "Risk Analyst",
            "Auditor", "Operations Specialist", "IT Security Specialist",
            "Branch Manager", "Customer Service Representative",
            "Underwriter", "Claims Adjuster", "Actuary"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "series_licenses": "string",  # Series 7, 63, etc.
            "finra_registered": "boolean",
            "business_unit": "string",
            "trading_desk": "string",
            "sox_trained": "boolean",
            "sox_training_date": "date",
            "data_classification_level": "string"
        },
        "group_patterns": {
            "front_office": ["Trading", "Investment Banking", "Wealth Management"],
            "middle_office": ["Risk Management", "Compliance"],
            "back_office": ["Operations", "IT", "Finance"],
            "licenses": ["Series 7 Licensed", "Series 63 Licensed", "CFA"]
        },
        "compliance_requirements": ["SOX", "SOC2", "PCI-DSS", "GLBA", "FINRA"],
        "sensitive_data": True
    },

    "technology": {
        "name": "Technology / SaaS",
        "description": "Software companies, SaaS providers, and technology startups",
        "departments": [
            "Engineering", "Product Management", "Design", "Sales",
            "Marketing", "Customer Success", "DevOps", "Security",
            "Data Science", "QA", "IT", "HR", "Finance", "Legal"
        ],
        "apps": [
            # Engineering
            "GitHub", "GitLab", "Jira", "Confluence", "CircleCI",
            "Jenkins", "Datadog", "New Relic", "PagerDuty", "Terraform Cloud",
            "AWS Console", "Azure Portal", "Google Cloud Platform",
            # Product & design
            "Figma", "Amplitude", "Mixpanel", "Google Analytics", "Miro",
            # Sales & marketing
            "Salesforce", "HubSpot", "Outreach", "Gong", "Marketo",
            # General
            "Slack", "Zoom", "Notion", "Linear", "Asana"
        ],
        "roles": [
            "Software Engineer", "Senior Software Engineer", "Staff Engineer",
            "Engineering Manager", "Product Manager", "Product Designer",
            "UX Researcher", "DevOps Engineer", "Site Reliability Engineer",
            "Data Scientist", "Data Engineer", "QA Engineer",
            "Security Engineer", "Sales Engineer", "Account Executive",
            "Customer Success Manager", "Marketing Manager"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "level": "string",  # IC1-IC6, M1-M4
            "team": "string",
            "tech_stack": "string",
            "github_username": "string",
            "oncall_rotation": "boolean"
        },
        "group_patterns": {
            "engineering_teams": ["Platform", "Frontend", "Backend", "Mobile", "Infrastructure"],
            "product_squads": ["Growth", "Core Product", "Enterprise", "Developer Experience"],
            "levels": ["IC Contributors", "Senior IC", "Staff+", "Managers", "Directors"]
        },
        "compliance_requirements": ["SOC2"],
        "sensitive_data": False
    },

    "manufacturing": {
        "name": "Manufacturing",
        "description": "Manufacturing, industrial production, and supply chain companies",
        "departments": [
            "Production", "Quality Control", "Supply Chain", "Logistics",
            "Maintenance", "Engineering", "Safety", "IT", "HR",
            "Finance", "Procurement", "R&D", "Operations"
        ],
        "apps": [
            # Industry-specific
            "SAP ERP", "Oracle Manufacturing", "JD Edwards", "Infor CloudSuite",
            "Siemens PLM", "PTC Windchill", "Dassault ENOVIA",
            "Rockwell FactoryTalk", "GE Digital", "AVEVA",
            # Quality & compliance
            "ETQ Reliance", "MasterControl", "TrackWise", "Qualys",
            # General business
            "Workday", "NetSuite", "Tableau", "Microsoft 365", "Slack"
        ],
        "roles": [
            "Production Manager", "Plant Manager", "Production Supervisor",
            "Quality Engineer", "Quality Inspector", "Process Engineer",
            "Manufacturing Engineer", "Supply Chain Manager", "Logistics Coordinator",
            "Maintenance Technician", "Safety Manager", "Procurement Specialist",
            "Production Planner", "Inventory Manager", "R&D Engineer"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "plant_location": "string",
            "shift": "string",
            "certifications": "string",
            "safety_trained": "boolean",
            "safety_training_date": "date",
            "equipment_authorizations": "string"
        },
        "group_patterns": {
            "plants": ["Plant A", "Plant B", "Plant C"],
            "shifts": ["Day Shift", "Night Shift", "Swing Shift"],
            "functions": ["Production", "Quality", "Maintenance", "Engineering"]
        },
        "compliance_requirements": ["ISO 9001", "ISO 14001", "OSHA"],
        "sensitive_data": False
    },

    "travel": {
        "name": "Travel / Hospitality",
        "description": "Airlines, hotels, travel agencies, and hospitality services",
        "departments": [
            "Operations", "Customer Service", "Reservations", "Revenue Management",
            "Sales", "Marketing", "IT", "HR", "Finance",
            "Safety", "Flight Operations", "Ground Operations", "Maintenance"
        ],
        "apps": [
            # Industry-specific
            "Sabre", "Amadeus", "Opera PMS", "Mews", "Cloudbeds",
            "IDeaS Revenue Management", "Duetto", "SynXis",
            "Salesforce Travel Cloud", "TravelClick", "Passkey",
            # General business
            "Workday", "Salesforce", "Tableau", "Microsoft 365",
            "Slack", "Zoom", "Zendesk"
        ],
        "roles": [
            "Pilot", "Flight Attendant", "Gate Agent", "Reservation Agent",
            "Hotel Manager", "Front Desk Agent", "Concierge",
            "Revenue Manager", "Sales Manager", "Customer Service Representative",
            "Operations Manager", "Maintenance Technician", "Safety Officer",
            "Travel Consultant", "Tour Guide"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "location": "string",
            "base_airport": "string",
            "employee_id": "string",
            "faa_licensed": "boolean",
            "license_type": "string",
            "safety_trained": "boolean"
        },
        "group_patterns": {
            "locations": ["LAX", "JFK", "ORD", "ATL", "DFW"],
            "operational": ["Flight Crew", "Ground Crew", "Maintenance"],
            "customer_facing": ["Reservations", "Customer Service", "Concierge"]
        },
        "compliance_requirements": ["FAA", "TSA", "ADA"],
        "sensitive_data": True
    },

    "retail": {
        "name": "Retail / E-commerce",
        "description": "Retail stores, e-commerce platforms, and omnichannel retailers",
        "departments": [
            "Store Operations", "E-commerce", "Merchandising", "Buying",
            "Supply Chain", "Marketing", "Customer Service", "IT",
            "HR", "Finance", "Loss Prevention", "Real Estate"
        ],
        "apps": [
            # Industry-specific
            "Shopify", "Magento", "BigCommerce", "Square POS",
            "Oracle Retail", "SAP Retail", "Manhattan Associates",
            "Blue Yonder", "Aptos", "Salesforce Commerce Cloud",
            # Marketing & analytics
            "Google Analytics", "Adobe Analytics", "Klaviyo", "Braze",
            # General business
            "NetSuite", "Workday", "Tableau", "Slack", "Zendesk"
        ],
        "roles": [
            "Store Manager", "Assistant Manager", "Sales Associate",
            "Cashier", "Visual Merchandiser", "Buyer", "Merchandising Manager",
            "E-commerce Manager", "Supply Chain Manager", "Inventory Manager",
            "Marketing Manager", "Customer Service Representative",
            "Loss Prevention Officer", "Warehouse Manager"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "store_number": "string",
            "location": "string",
            "employee_type": "string",
            "pos_access": "boolean",
            "discount_level": "string"
        },
        "group_patterns": {
            "stores": ["Store 001", "Store 002", "Store 003", "E-commerce"],
            "regions": ["Northeast", "Southeast", "Midwest", "West Coast"],
            "channels": ["Retail", "E-commerce", "Wholesale"]
        },
        "compliance_requirements": ["PCI-DSS", "ADA"],
        "sensitive_data": True
    },

    "education": {
        "name": "Education",
        "description": "Universities, colleges, K-12 schools, and educational institutions",
        "departments": [
            "Academic Affairs", "Student Services", "Admissions", "Financial Aid",
            "IT", "HR", "Finance", "Facilities", "Athletics",
            "Library", "Research", "Development", "Alumni Relations"
        ],
        "apps": [
            # Industry-specific
            "Canvas LMS", "Blackboard", "Moodle", "Google Classroom",
            "Banner", "PeopleSoft Campus Solutions", "Ellucian Colleague",
            "Slate CRM", "TargetX", "Salesforce Education Cloud",
            "Workday Student", "Anthology", "Instructure",
            # General
            "Google Workspace", "Microsoft 365", "Zoom", "Slack",
            "Tableau", "Workday"
        ],
        "roles": [
            "Professor", "Associate Professor", "Assistant Professor",
            "Lecturer", "Teaching Assistant", "Academic Advisor",
            "Admissions Counselor", "Financial Aid Counselor",
            "Student Services Coordinator", "Registrar", "Librarian",
            "IT Support Specialist", "Facilities Manager", "Athletic Director",
            "Development Officer", "Alumni Relations Manager"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "faculty_type": "string",
            "tenure_status": "string",
            "department_affiliation": "string",
            "building": "string",
            "office_number": "string",
            "ferpa_trained": "boolean"
        },
        "group_patterns": {
            "academic_departments": ["Computer Science", "Business", "Engineering", "Liberal Arts"],
            "schools": ["School of Business", "School of Engineering", "College of Arts & Sciences"],
            "roles": ["Faculty", "Staff", "Administrators", "Students"]
        },
        "compliance_requirements": ["FERPA"],
        "sensitive_data": True
    },

    "government": {
        "name": "Government / Public Sector",
        "description": "Federal, state, and local government agencies",
        "departments": [
            "Administration", "Public Works", "Public Safety", "IT",
            "HR", "Finance", "Legal", "Communications", "Planning",
            "Transportation", "Health Services", "Social Services"
        ],
        "apps": [
            # Industry-specific
            "Tyler Technologies", "CivicPlus", "Granicus", "OpenGov",
            "Infor Public Sector", "Oracle Public Sector", "SAP Public Services",
            "Accela", "Cartegraph", "GovQA", "SeeClickFix",
            # Security & compliance
            "FedRAMP Authorized Apps", "Splunk", "CrowdStrike",
            # General
            "Microsoft 365 GCC", "Workday", "Tableau", "Zoom Government"
        ],
        "roles": [
            "City Manager", "Department Director", "Program Manager",
            "Public Works Supervisor", "Police Officer", "Firefighter",
            "Emergency Dispatcher", "Social Worker", "Urban Planner",
            "IT Specialist", "Administrative Assistant", "Budget Analyst",
            "Public Information Officer", "Compliance Officer"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "security_clearance": "string",
            "badge_number": "string",
            "agency": "string",
            "office_location": "string",
            "authorized_systems": "string"
        },
        "group_patterns": {
            "agencies": ["Police", "Fire", "Public Works", "Administration"],
            "clearance_levels": ["Public Trust", "Confidential", "Secret"],
            "functions": ["Public Safety", "Administrative", "Operations"]
        },
        "compliance_requirements": ["FISMA", "FedRAMP", "NIST 800-53"],
        "sensitive_data": True
    },

    "energy": {
        "name": "Energy / Utilities",
        "description": "Electric, gas, water utilities, and renewable energy companies",
        "departments": [
            "Operations", "Grid Management", "Field Services", "Customer Service",
            "Engineering", "IT", "Safety", "Compliance", "Finance",
            "HR", "Environmental", "Asset Management", "Trading"
        ],
        "apps": [
            # Industry-specific
            "OSI PI System", "GE Digital APM", "AVEVA", "Schneider Electric",
            "Oracle Utilities", "SAP IS-U", "Itron", "Landis+Gyr",
            "Siemens Energy", "ABB Ability", "Emerson DeltaV",
            # Security & compliance
            "Nozomi Networks", "Dragos", "Claroty", "Splunk",
            # General
            "Workday", "Salesforce", "Tableau", "Microsoft 365"
        ],
        "roles": [
            "Plant Manager", "Operations Engineer", "Control Room Operator",
            "Field Technician", "Lineworker", "Electrician",
            "Substation Engineer", "Grid Operator", "Energy Trader",
            "Customer Service Representative", "Meter Reader",
            "Compliance Manager", "Safety Manager", "Environmental Engineer"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "facility": "string",
            "certifications": "string",
            "nerc_cip_trained": "boolean",
            "safety_clearance": "string",
            "vehicle_number": "string",
            "shift": "string"
        },
        "group_patterns": {
            "facilities": ["Power Plant A", "Substation B", "Distribution Center C"],
            "operational": ["Generation", "Transmission", "Distribution"],
            "shifts": ["Day Shift", "Night Shift", "On-Call"]
        },
        "compliance_requirements": ["NERC CIP", "FERC", "EPA", "OSHA"],
        "sensitive_data": True
    },

    "media": {
        "name": "Media / Entertainment",
        "description": "Media companies, studios, streaming services, and entertainment content creators",
        "departments": [
            "Production", "Post-Production", "Content", "Programming",
            "Distribution", "Sales", "Marketing", "IT", "Finance",
            "Legal", "HR", "Operations", "Technology", "Creative"
        ],
        "apps": [
            # Industry-specific
            "Avid Media Composer", "Adobe Premiere Pro", "Final Cut Pro",
            "DaVinci Resolve", "Frame.io", "Evercast", "Shotgun",
            "Xytech MediaPulse", "Dalet", "Ross Video", "Vantage",
            "Salesforce Media Cloud", "Rights Logic", "FilmTrack",
            # General
            "Slack", "Zoom", "Monday.com", "Box", "Google Workspace",
            "Workday", "NetSuite"
        ],
        "roles": [
            "Producer", "Director", "Editor", "Camera Operator",
            "Production Assistant", "Post-Production Supervisor",
            "Content Manager", "Programming Executive", "Acquisitions Manager",
            "Distribution Manager", "Sales Executive", "Marketing Manager",
            "IT Engineer", "Broadcast Engineer", "Creative Director"
        ],
        "user_attributes": {
            "department": "string",
            "title": "string",
            "union_affiliation": "string",
            "project_assignments": "string",
            "facility_access": "string",
            "equipment_authorizations": "string",
            "imdb_id": "string"
        },
        "group_patterns": {
            "production_teams": ["Drama", "Comedy", "Documentary", "News"],
            "facilities": ["Studio A", "Studio B", "Post-Production", "Remote"],
            "unions": ["DGA", "SAG-AFTRA", "IATSE", "WGA"]
        },
        "compliance_requirements": ["FCC", "Union Agreements"],
        "sensitive_data": True
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_org_size_config(size: str) -> Dict[str, Any]:
    """
    Get configuration for an organization size.

    Args:
        size: Organization size key ('startup', 'midsize', 'enterprise')

    Returns:
        Organization size configuration dictionary

    Example:
        >>> config = get_org_size_config('startup')
        >>> print(config['user_count_range'])
        (10, 50)
    """
    return ORG_SIZE_TEMPLATES.get(size.lower(), {})


def get_industry_config(industry: str) -> Dict[str, Any]:
    """
    Get configuration for an industry.

    Args:
        industry: Industry key (e.g., 'healthcare', 'technology')

    Returns:
        Industry configuration dictionary

    Example:
        >>> config = get_industry_config('healthcare')
        >>> print(config['departments'])
        ['Clinical', 'Nursing', 'Administration', ...]
    """
    return INDUSTRY_TEMPLATES.get(industry.lower(), {})


def get_departments_for_industry(industry: str) -> List[str]:
    """
    Get department list for an industry.

    Args:
        industry: Industry key

    Returns:
        List of department names

    Example:
        >>> departments = get_departments_for_industry('technology')
        >>> print(departments[:3])
        ['Engineering', 'Product Management', 'Design']
    """
    config = get_industry_config(industry)
    return config.get('departments', [])


def get_apps_for_industry(industry: str) -> List[str]:
    """
    Get application list for an industry (includes both industry-specific and common apps).

    Args:
        industry: Industry key

    Returns:
        List of application names

    Example:
        >>> apps = get_apps_for_industry('healthcare')
        >>> print('Epic EMR' in apps)
        True
    """
    config = get_industry_config(industry)
    return config.get('apps', [])


def get_user_titles_for_department(industry: str, department: str) -> List[str]:
    """
    Get realistic job titles for a department in an industry.

    Uses the industry's role list and filters/maps based on department.
    For unmapped combinations, returns generic titles.

    Args:
        industry: Industry key
        department: Department name

    Returns:
        List of job titles appropriate for the department

    Example:
        >>> titles = get_user_titles_for_department('technology', 'Engineering')
        >>> print(titles[:2])
        ['Software Engineer', 'Senior Software Engineer']
    """
    config = get_industry_config(industry)
    all_roles = config.get('roles', [])

    # Department-specific role mappings
    role_mappings = {
        "Engineering": ["Engineer", "Software", "Developer", "Architect", "DevOps", "SRE"],
        "Sales": ["Sales", "Account Executive", "Representative"],
        "Marketing": ["Marketing", "Manager", "Coordinator", "Specialist"],
        "IT": ["IT", "System", "Network", "Administrator", "Support"],
        "HR": ["HR", "Recruiter", "Coordinator", "Benefits"],
        "Finance": ["Finance", "Accountant", "Analyst", "Controller"],
        "Operations": ["Operations", "Manager", "Coordinator"],
        "Customer Success": ["Customer Success", "Account Manager", "Support"],
    }

    # Get keywords for the department
    keywords = role_mappings.get(department, [department])

    # Filter roles that match keywords
    matching_roles = [
        role for role in all_roles
        if any(keyword.lower() in role.lower() for keyword in keywords)
    ]

    # If no matches, return generic titles with department prefix
    if not matching_roles:
        matching_roles = [
            f"{department} Manager",
            f"Senior {department} Specialist",
            f"{department} Specialist",
            f"{department} Coordinator",
            f"{department} Associate"
        ]

    return matching_roles


def calculate_user_distribution(total_users: int, departments: List[str]) -> Dict[str, int]:
    """
    Calculate how many users should be in each department.

    Uses realistic distribution patterns with some randomization:
    - Core operational departments get 50-60% of users
    - Support departments get 20-30%
    - Admin/overhead departments get 10-20%

    Args:
        total_users: Total number of users to distribute
        departments: List of department names

    Returns:
        Dictionary mapping department name to user count

    Example:
        >>> distribution = calculate_user_distribution(100, ['Engineering', 'Sales', 'HR'])
        >>> print(sum(distribution.values()))
        100
    """
    # Define department categories and their weights
    core_departments = ["Engineering", "Sales", "Clinical", "Production", "Operations"]
    support_departments = ["Marketing", "Customer Success", "IT", "Quality", "Supply Chain"]
    admin_departments = ["HR", "Finance", "Legal", "Administration"]

    distribution = {}
    remaining_users = total_users

    # Categorize departments
    core = [d for d in departments if any(c in d for c in core_departments)]
    support = [d for d in departments if any(s in d for s in support_departments)]
    admin = [d for d in departments if any(a in d for a in admin_departments)]
    other = [d for d in departments if d not in core and d not in support and d not in admin]

    # Allocate users based on category
    core_allocation = int(total_users * random.uniform(0.50, 0.60)) if core else 0
    support_allocation = int(total_users * random.uniform(0.20, 0.30)) if support else 0
    admin_allocation = total_users - core_allocation - support_allocation

    # Distribute within each category
    if core:
        for dept in core:
            count = max(1, int(core_allocation / len(core) * random.uniform(0.8, 1.2)))
            distribution[dept] = min(count, remaining_users)
            remaining_users -= distribution[dept]

    if support:
        for dept in support:
            count = max(1, int(support_allocation / len(support) * random.uniform(0.8, 1.2)))
            distribution[dept] = min(count, remaining_users)
            remaining_users -= distribution[dept]

    if admin:
        for dept in admin:
            count = max(1, int(admin_allocation / len(admin) * random.uniform(0.8, 1.2)))
            distribution[dept] = min(count, remaining_users)
            remaining_users -= distribution[dept]

    if other:
        for dept in other:
            count = max(1, remaining_users // len(other))
            distribution[dept] = count
            remaining_users -= count

    # Distribute any remaining users
    if remaining_users > 0:
        for dept in departments[:remaining_users]:
            distribution[dept] = distribution.get(dept, 0) + 1

    return distribution


def get_app_assignment_pattern(
    industry: str,
    department: str,
    role: str,
    org_size: str = "midsize"
) -> List[str]:
    """
    Get list of apps that should be assigned to a user based on their attributes.

    Combines:
    - Universal apps (everyone gets these)
    - Department-specific apps
    - Role-specific apps
    - Industry-specific apps

    Args:
        industry: Industry key
        department: Department name
        role: Job title/role
        org_size: Organization size ('startup', 'midsize', 'enterprise')

    Returns:
        List of application names that should be assigned to the user

    Example:
        >>> apps = get_app_assignment_pattern('technology', 'Engineering', 'Software Engineer')
        >>> print('GitHub' in apps)
        True
        >>> print('Okta Dashboard' in apps)
        True
    """
    assigned_apps = []

    # Universal apps (everyone gets these)
    assigned_apps.extend(APP_ASSIGNMENT_PATTERNS["universal"])

    # Department-specific apps
    dept_apps = APP_ASSIGNMENT_PATTERNS["by_department"].get(department, [])
    assigned_apps.extend(dept_apps)

    # Role-specific apps (check if role contains keywords)
    for role_keyword, apps in APP_ASSIGNMENT_PATTERNS["by_role"].items():
        if role_keyword.lower() in role.lower():
            assigned_apps.extend(apps)

    # Industry-specific apps (sample some)
    industry_config = get_industry_config(industry)
    industry_apps = industry_config.get('apps', [])

    # For smaller orgs, assign fewer industry-specific apps
    if org_size == "startup":
        num_industry_apps = min(3, len(industry_apps))
    elif org_size == "midsize":
        num_industry_apps = min(5, len(industry_apps))
    else:  # enterprise
        num_industry_apps = min(8, len(industry_apps))

    if industry_apps:
        assigned_apps.extend(random.sample(industry_apps, num_industry_apps))

    # Remove duplicates while preserving order
    seen = set()
    unique_apps = []
    for app in assigned_apps:
        if app not in seen:
            seen.add(app)
            unique_apps.append(app)

    return unique_apps


def get_all_industries() -> List[str]:
    """
    Get list of all available industries.

    Returns:
        List of industry keys

    Example:
        >>> industries = get_all_industries()
        >>> print('healthcare' in industries)
        True
        >>> print(len(industries))
        10
    """
    return list(INDUSTRY_TEMPLATES.keys())


def get_all_org_sizes() -> List[str]:
    """
    Get list of all available organization sizes.

    Returns:
        List of org size keys

    Example:
        >>> sizes = get_all_org_sizes()
        >>> print(sizes)
        ['startup', 'midsize', 'enterprise']
    """
    return list(ORG_SIZE_TEMPLATES.keys())


def get_group_structure_template(structure_type: str) -> Dict[str, Any]:
    """
    Get group structure configuration.

    Args:
        structure_type: Structure type ('standard' or 'complex')

    Returns:
        Group structure configuration dictionary

    Example:
        >>> structure = get_group_structure_template('complex')
        >>> print(structure['departments'])
        True
    """
    return GROUP_STRUCTURE_TEMPLATES.get(structure_type, GROUP_STRUCTURE_TEMPLATES["standard"])


def generate_sample_user_profile(
    industry: str,
    department: str,
    org_size: str = "midsize"
) -> Dict[str, Any]:
    """
    Generate a sample user profile for testing.

    Args:
        industry: Industry key
        department: Department name
        org_size: Organization size

    Returns:
        Sample user profile dictionary

    Example:
        >>> profile = generate_sample_user_profile('technology', 'Engineering')
        >>> print(profile['profile']['department'])
        'Engineering'
    """
    from datetime import datetime, timedelta

    industry_config = get_industry_config(industry)
    titles = get_user_titles_for_department(industry, department)
    title = random.choice(titles) if titles else f"{department} Specialist"

    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    email = f"{first_name.lower()}.{last_name.lower()}@example.com"

    profile = {
        "firstName": first_name,
        "lastName": last_name,
        "email": email,
        "login": email,
        "department": department,
        "title": title
    }

    # Add org-size specific attributes
    size_config = get_org_size_config(org_size)
    custom_attrs = size_config.get('custom_attributes', [])

    if 'employeeNumber' in custom_attrs:
        profile['employeeNumber'] = f"EMP{random.randint(1000, 9999)}"

    if 'startDate' in custom_attrs:
        days_ago = random.randint(30, 1825)  # 1 month to 5 years
        start_date = datetime.now() - timedelta(days=days_ago)
        profile['startDate'] = start_date.strftime('%Y-%m-%d')

    if 'location' in custom_attrs and size_config.get('locations'):
        profile['location'] = random.choice(size_config['locations'])

    return {"profile": profile}


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("OKTA ORGANIZATION TEMPLATES")
    print("=" * 80)

    # Show all industries
    print("\nAvailable Industries:")
    for industry in get_all_industries():
        config = get_industry_config(industry)
        print(f"  • {config['name']}")
        print(f"    Departments: {len(config['departments'])}")
        print(f"    Apps: {len(config['apps'])}")
        print(f"    Roles: {len(config['roles'])}")

    # Show all org sizes
    print("\nAvailable Organization Sizes:")
    for size in get_all_org_sizes():
        config = get_org_size_config(size)
        print(f"  • {config['name']}")
        print(f"    User Range: {config['user_count_range'][0]}-{config['user_count_range'][1]}")
        print(f"    Departments: {len(config['departments'])}")

    # Show sample user distribution
    print("\nSample User Distribution (100 users in Technology):")
    tech_config = get_industry_config('technology')
    distribution = calculate_user_distribution(100, tech_config['departments'])
    for dept, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dept}: {count} users")

    # Show sample app assignment
    print("\nSample App Assignment (Technology Engineer):")
    apps = get_app_assignment_pattern('technology', 'Engineering', 'Software Engineer')
    print(f"  Total apps: {len(apps)}")
    print(f"  Apps: {', '.join(apps[:10])}...")

    # Show sample user profile
    print("\nSample User Profile:")
    profile = generate_sample_user_profile('healthcare', 'Clinical', 'enterprise')
    for key, value in profile['profile'].items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 80)
