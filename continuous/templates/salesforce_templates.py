#!/usr/bin/env python3
"""
Salesforce CRM templates for realistic sales, customer relationship, and business data generation.

Defines organization structures across different sizes (startup, mid-size, enterprise)
and industries (healthcare, finance, technology, manufacturing, retail, energy, etc.)
for comprehensive Salesforce data generation.

Supports:
- Account and contact distribution patterns
- Opportunity pipeline templates with realistic conversion funnels
- Industry-specific product catalogs
- Sales process templates (stages, durations, conversion rates)
- Case management templates
- Territory and region structures
- Realistic deal sizes and sales cycle lengths
- Seasonal patterns and business rhythms
"""

from typing import Dict, List, Any, Tuple
import random
from datetime import datetime, timedelta


# ============================================================================
# ORGANIZATION SIZE TEMPLATES
# ============================================================================

ORG_SIZE_TEMPLATES = {
    "startup": {
        "name": "Startup",
        "description": "Early-stage company with small sales team, limited customer base, focused on rapid growth",
        "user_count_range": (5, 25),
        "account_count_range": (20, 150),
        "active_opportunity_range": (10, 50),
        "closed_won_monthly": (2, 8),
        "case_volume_monthly": (5, 30),
        "lead_volume_monthly": (50, 200),
        "sales_team_size": (2, 8),
        "sales_development_reps": (1, 3),
        "account_executives": (1, 4),
        "customer_success_managers": (0, 2),
        "sales_managers": (0, 1),
        "typical_deal_size": (5000, 50000),
        "enterprise_deal_percentage": 0.05,  # 5% of deals are enterprise
        "avg_sales_cycle_days": (30, 90),
        "territory_count": (1, 3),
        "product_count_range": (1, 5),
        "has_territory_management": False,
        "has_partner_channel": False,
        "forecast_categories": ["Pipeline", "Best Case", "Commit", "Closed"],
        "regions": ["North America"]
    },
    "midsize": {
        "name": "Mid-Size Company",
        "description": "Established company with structured sales processes, diverse customer base, multiple product lines",
        "user_count_range": (50, 250),
        "account_count_range": (25, 100),  # Reduced for POC - focus on quality over quantity
        "active_opportunity_range": (100, 500),
        "closed_won_monthly": (15, 60),
        "case_volume_monthly": (50, 300),
        "lead_volume_monthly": (300, 1500),
        "sales_team_size": (15, 60),
        "sales_development_reps": (5, 15),
        "account_executives": (8, 30),
        "customer_success_managers": (3, 12),
        "sales_managers": (2, 6),
        "typical_deal_size": (10000, 150000),
        "enterprise_deal_percentage": 0.15,  # 15% of deals are enterprise
        "avg_sales_cycle_days": (45, 120),
        "territory_count": (3, 12),
        "product_count_range": (5, 20),
        "has_territory_management": True,
        "has_partner_channel": True,
        "forecast_categories": ["Pipeline", "Best Case", "Commit", "Omitted", "Closed"],
        "regions": ["North America", "EMEA", "APAC"]
    },
    "enterprise": {
        "name": "Enterprise",
        "description": "Large corporation with complex sales org, global presence, extensive product portfolio, multiple business units",
        "user_count_range": (500, 5000),
        "account_count_range": (5000, 50000),
        "active_opportunity_range": (1000, 10000),
        "closed_won_monthly": (100, 500),
        "case_volume_monthly": (500, 5000),
        "lead_volume_monthly": (2000, 15000),
        "sales_team_size": (100, 1000),
        "sales_development_reps": (30, 200),
        "account_executives": (50, 500),
        "customer_success_managers": (20, 150),
        "sales_managers": (10, 80),
        "typical_deal_size": (25000, 1000000),
        "enterprise_deal_percentage": 0.30,  # 30% of deals are enterprise
        "avg_sales_cycle_days": (90, 270),
        "territory_count": (20, 100),
        "product_count_range": (20, 100),
        "has_territory_management": True,
        "has_partner_channel": True,
        "forecast_categories": ["Pipeline", "Best Case", "Commit", "Omitted", "Closed"],
        "regions": ["North America", "EMEA", "APAC", "LATAM", "MEA"]
    }
}


# ============================================================================
# SALES PROCESS TEMPLATES
# ============================================================================

SALES_PROCESS_TEMPLATES = {
    "b2b_enterprise": {
        "name": "Enterprise B2B Sales",
        "description": "Complex, consultative sales process for large enterprise deals",
        "stages": [
            {
                "name": "Prospecting",
                "probability": 10,
                "avg_duration_days": (7, 21),
                "typical_activities": ["Initial outreach", "Research", "Qualification"],
                "conversion_rate": 0.30,  # 30% move to next stage
                "is_closed": False
            },
            {
                "name": "Qualification",
                "probability": 20,
                "avg_duration_days": (7, 14),
                "typical_activities": ["Discovery call", "Needs analysis", "BANT qualification"],
                "conversion_rate": 0.50,
                "is_closed": False
            },
            {
                "name": "Discovery",
                "probability": 30,
                "avg_duration_days": (14, 30),
                "typical_activities": ["Deep dive sessions", "Stakeholder meetings", "Requirements gathering"],
                "conversion_rate": 0.60,
                "is_closed": False
            },
            {
                "name": "Solution Design",
                "probability": 40,
                "avg_duration_days": (14, 45),
                "typical_activities": ["Solution architecture", "Demo", "Proof of concept"],
                "conversion_rate": 0.65,
                "is_closed": False
            },
            {
                "name": "Proposal",
                "probability": 60,
                "avg_duration_days": (7, 21),
                "typical_activities": ["Proposal creation", "Pricing negotiation", "Legal review"],
                "conversion_rate": 0.70,
                "is_closed": False
            },
            {
                "name": "Negotiation",
                "probability": 75,
                "avg_duration_days": (7, 30),
                "typical_activities": ["Contract negotiation", "Executive alignment", "Deal finalization"],
                "conversion_rate": 0.75,
                "is_closed": False
            },
            {
                "name": "Closed Won",
                "probability": 100,
                "avg_duration_days": (0, 0),
                "typical_activities": ["Contract signed", "Handoff to implementation"],
                "conversion_rate": 1.0,
                "is_closed": True
            },
            {
                "name": "Closed Lost",
                "probability": 0,
                "avg_duration_days": (0, 0),
                "typical_activities": ["Lost reason analysis", "Relationship maintenance"],
                "conversion_rate": 0.0,
                "is_closed": True
            }
        ],
        "overall_win_rate": 0.18,  # 18% of all opportunities close won
        "avg_total_cycle_days": (90, 180),
        "discount_patterns": {
            "avg_discount_percentage": 12,
            "max_discount_percentage": 25,
            "discount_by_deal_size": {
                "small": (5, 10),
                "medium": (10, 15),
                "large": (12, 20),
                "enterprise": (15, 25)
            }
        }
    },
    "b2b_smb": {
        "name": "SMB B2B Sales",
        "description": "Faster, more transactional sales process for small to medium businesses",
        "stages": [
            {
                "name": "Lead",
                "probability": 10,
                "avg_duration_days": (1, 7),
                "typical_activities": ["Inbound qualification", "Outbound prospecting"],
                "conversion_rate": 0.40,
                "is_closed": False
            },
            {
                "name": "Qualified",
                "probability": 25,
                "avg_duration_days": (3, 7),
                "typical_activities": ["Discovery call", "Needs assessment"],
                "conversion_rate": 0.60,
                "is_closed": False
            },
            {
                "name": "Demo Scheduled",
                "probability": 40,
                "avg_duration_days": (3, 7),
                "typical_activities": ["Product demo", "Q&A"],
                "conversion_rate": 0.70,
                "is_closed": False
            },
            {
                "name": "Proposal Sent",
                "probability": 60,
                "avg_duration_days": (3, 14),
                "typical_activities": ["Proposal review", "Pricing discussion"],
                "conversion_rate": 0.65,
                "is_closed": False
            },
            {
                "name": "Negotiation",
                "probability": 80,
                "avg_duration_days": (3, 7),
                "typical_activities": ["Terms negotiation", "Contract review"],
                "conversion_rate": 0.80,
                "is_closed": False
            },
            {
                "name": "Closed Won",
                "probability": 100,
                "avg_duration_days": (0, 0),
                "typical_activities": ["Contract signed", "Onboarding scheduled"],
                "conversion_rate": 1.0,
                "is_closed": True
            },
            {
                "name": "Closed Lost",
                "probability": 0,
                "avg_duration_days": (0, 0),
                "typical_activities": ["Lost analysis", "Nurture campaign"],
                "conversion_rate": 0.0,
                "is_closed": True
            }
        ],
        "overall_win_rate": 0.30,  # 30% win rate for SMB
        "avg_total_cycle_days": (20, 45),
        "discount_patterns": {
            "avg_discount_percentage": 8,
            "max_discount_percentage": 15,
            "discount_by_deal_size": {
                "small": (0, 5),
                "medium": (5, 10),
                "large": (8, 15),
                "enterprise": (10, 15)
            }
        }
    },
    "renewal": {
        "name": "Renewal/Upsell Process",
        "description": "Customer renewal and expansion sales process",
        "stages": [
            {
                "name": "Renewal Identified",
                "probability": 60,
                "avg_duration_days": (30, 60),
                "typical_activities": ["Customer health check", "Usage review"],
                "conversion_rate": 0.85,
                "is_closed": False
            },
            {
                "name": "Renewal Engaged",
                "probability": 75,
                "avg_duration_days": (14, 30),
                "typical_activities": ["Business review", "Value demonstration"],
                "conversion_rate": 0.90,
                "is_closed": False
            },
            {
                "name": "Renewal Negotiation",
                "probability": 90,
                "avg_duration_days": (7, 14),
                "typical_activities": ["Contract renewal", "Pricing discussion"],
                "conversion_rate": 0.95,
                "is_closed": False
            },
            {
                "name": "Closed Won",
                "probability": 100,
                "avg_duration_days": (0, 0),
                "typical_activities": ["Contract signed", "Renewal confirmed"],
                "conversion_rate": 1.0,
                "is_closed": True
            },
            {
                "name": "Closed Lost",
                "probability": 0,
                "avg_duration_days": (0, 0),
                "typical_activities": ["Churn analysis", "Exit interview"],
                "conversion_rate": 0.0,
                "is_closed": True
            }
        ],
        "overall_win_rate": 0.72,  # 72% renewal rate (typical SaaS benchmark)
        "avg_total_cycle_days": (30, 90),
        "discount_patterns": {
            "avg_discount_percentage": 5,
            "max_discount_percentage": 10,
            "discount_by_deal_size": {
                "small": (0, 5),
                "medium": (3, 8),
                "large": (5, 10),
                "enterprise": (5, 10)
            }
        }
    },
    "partner_channel": {
        "name": "Partner/Channel Sales",
        "description": "Sales through partners, resellers, and channel partners",
        "stages": [
            {
                "name": "Partner Lead",
                "probability": 15,
                "avg_duration_days": (7, 14),
                "typical_activities": ["Partner referral", "Lead qualification"],
                "conversion_rate": 0.45,
                "is_closed": False
            },
            {
                "name": "Partner Qualified",
                "probability": 30,
                "avg_duration_days": (7, 14),
                "typical_activities": ["Joint discovery", "Partner collaboration"],
                "conversion_rate": 0.65,
                "is_closed": False
            },
            {
                "name": "Partner Demo",
                "probability": 50,
                "avg_duration_days": (7, 14),
                "typical_activities": ["Product demonstration", "Solution design"],
                "conversion_rate": 0.70,
                "is_closed": False
            },
            {
                "name": "Partner Proposal",
                "probability": 70,
                "avg_duration_days": (7, 21),
                "typical_activities": ["Proposal preparation", "Partner pricing"],
                "conversion_rate": 0.75,
                "is_closed": False
            },
            {
                "name": "Closed Won",
                "probability": 100,
                "avg_duration_days": (0, 0),
                "typical_activities": ["Deal registration", "Partner commission"],
                "conversion_rate": 1.0,
                "is_closed": True
            },
            {
                "name": "Closed Lost",
                "probability": 0,
                "avg_duration_days": (0, 0),
                "typical_activities": ["Partner feedback", "Competitive analysis"],
                "conversion_rate": 0.0,
                "is_closed": True
            }
        ],
        "overall_win_rate": 0.24,  # 24% win rate through partners
        "avg_total_cycle_days": (30, 75),
        "discount_patterns": {
            "avg_discount_percentage": 20,  # Higher due to partner margin
            "max_discount_percentage": 35,
            "discount_by_deal_size": {
                "small": (15, 25),
                "medium": (18, 28),
                "large": (20, 30),
                "enterprise": (22, 35)
            }
        }
    }
}


# ============================================================================
# OPPORTUNITY TYPES
# ============================================================================

OPPORTUNITY_TYPES = {
    "new_business": {
        "name": "New Business",
        "description": "Net new customer acquisition",
        "percentage_of_pipeline": 0.50,  # 50% of opportunities
        "preferred_sales_process": ["b2b_enterprise", "b2b_smb"],
        "typical_products": "all",
        "requires_credit_check": True
    },
    "upsell": {
        "name": "Upsell",
        "description": "Additional products/services to existing customers",
        "percentage_of_pipeline": 0.20,  # 20% of opportunities
        "preferred_sales_process": ["renewal"],
        "typical_products": "add_on",
        "requires_credit_check": False
    },
    "renewal": {
        "name": "Renewal",
        "description": "Contract renewal for existing customers",
        "percentage_of_pipeline": 0.20,  # 20% of opportunities
        "preferred_sales_process": ["renewal"],
        "typical_products": "current",
        "requires_credit_check": False
    },
    "expansion": {
        "name": "Expansion",
        "description": "Increased user count or usage for existing customers",
        "percentage_of_pipeline": 0.10,  # 10% of opportunities
        "preferred_sales_process": ["renewal"],
        "typical_products": "current",
        "requires_credit_check": False
    }
}


# ============================================================================
# LEAD SOURCES
# ============================================================================

LEAD_SOURCES = {
    "inbound": {
        "Web": 0.25,  # 25% of leads
        "Content Download": 0.15,
        "Webinar": 0.10,
        "Trial Signup": 0.10,
        "Contact Form": 0.08
    },
    "outbound": {
        "Outbound Call": 0.12,
        "Email Campaign": 0.08,
        "LinkedIn": 0.05
    },
    "referral": {
        "Customer Referral": 0.04,
        "Partner Referral": 0.03
    }
}


# ============================================================================
# CONTACT ROLES
# ============================================================================

CONTACT_ROLES = {
    "decision_maker": {
        "role": "Decision Maker",
        "influence_level": "High",
        "typical_titles": ["CEO", "CTO", "CFO", "VP", "Director"],
        "is_primary": True
    },
    "economic_buyer": {
        "role": "Economic Buyer",
        "influence_level": "High",
        "typical_titles": ["CFO", "VP Finance", "Procurement Director"],
        "is_primary": False
    },
    "champion": {
        "role": "Champion",
        "influence_level": "High",
        "typical_titles": ["Director", "Senior Manager", "Team Lead"],
        "is_primary": False
    },
    "influencer": {
        "role": "Influencer",
        "influence_level": "Medium",
        "typical_titles": ["Manager", "Senior Analyst", "Architect"],
        "is_primary": False
    },
    "end_user": {
        "role": "End User",
        "influence_level": "Low",
        "typical_titles": ["Analyst", "Specialist", "Coordinator"],
        "is_primary": False
    },
    "blocker": {
        "role": "Blocker",
        "influence_level": "Medium",
        "typical_titles": ["IT Director", "Security Manager", "Legal Counsel"],
        "is_primary": False
    }
}


# ============================================================================
# CASE TYPES AND PRIORITIES
# ============================================================================

CASE_TEMPLATES = {
    "types": {
        "Question": {
            "percentage": 0.40,
            "avg_resolution_hours": (2, 24),
            "requires_escalation_rate": 0.05,
            "satisfaction_avg": 4.2
        },
        "Problem": {
            "percentage": 0.30,
            "avg_resolution_hours": (8, 72),
            "requires_escalation_rate": 0.20,
            "satisfaction_avg": 3.8
        },
        "Feature Request": {
            "percentage": 0.15,
            "avg_resolution_hours": (24, 168),  # Often routed to product
            "requires_escalation_rate": 0.30,
            "satisfaction_avg": 4.0
        },
        "Bug": {
            "percentage": 0.10,
            "avg_resolution_hours": (24, 240),
            "requires_escalation_rate": 0.60,
            "satisfaction_avg": 3.5
        },
        "Billing": {
            "percentage": 0.05,
            "avg_resolution_hours": (4, 48),
            "requires_escalation_rate": 0.15,
            "satisfaction_avg": 4.0
        }
    },
    "priorities": {
        "Low": {
            "percentage": 0.40,
            "sla_hours": 48,
            "response_time_hours": 24
        },
        "Medium": {
            "percentage": 0.35,
            "sla_hours": 24,
            "response_time_hours": 8
        },
        "High": {
            "percentage": 0.20,
            "sla_hours": 8,
            "response_time_hours": 2
        },
        "Critical": {
            "percentage": 0.05,
            "sla_hours": 4,
            "response_time_hours": 1
        }
    },
    "statuses": ["New", "In Progress", "Waiting on Customer", "Escalated", "Resolved", "Closed"],
    "origins": {
        "Email": 0.40,
        "Phone": 0.25,
        "Web": 0.20,
        "Chat": 0.10,
        "Social": 0.05
    }
}


# ============================================================================
# ACCOUNT TYPES AND RECORD TYPES
# ============================================================================

ACCOUNT_TYPES = {
    "prospect": {
        "name": "Prospect",
        "description": "Potential customer not yet engaged",
        "typical_revenue": None,
        "has_opportunities": True,
        "has_cases": False,
        "percentage": 0.30
    },
    "customer": {
        "name": "Customer",
        "description": "Active paying customer",
        "typical_revenue": "positive",
        "has_opportunities": True,
        "has_cases": True,
        "percentage": 0.50
    },
    "partner": {
        "name": "Partner",
        "description": "Channel partner or reseller",
        "typical_revenue": "variable",
        "has_opportunities": True,
        "has_cases": False,
        "percentage": 0.10
    },
    "competitor": {
        "name": "Competitor",
        "description": "Competitive company for tracking",
        "typical_revenue": None,
        "has_opportunities": False,
        "has_cases": False,
        "percentage": 0.05
    },
    "former_customer": {
        "name": "Former Customer",
        "description": "Churned customer",
        "typical_revenue": None,
        "has_opportunities": True,
        "has_cases": False,
        "percentage": 0.05
    }
}


ACCOUNT_SEGMENTS = {
    "enterprise": {
        "name": "Enterprise",
        "employee_range": (5000, 100000),
        "annual_revenue_range": (500000000, 50000000000),
        "typical_deal_size": (100000, 5000000),
        "percentage": 0.10,
        "sales_process": "b2b_enterprise",
        "sales_cycle_days": (120, 270)
    },
    "mid_market": {
        "name": "Mid-Market",
        "employee_range": (200, 5000),
        "annual_revenue_range": (50000000, 500000000),
        "typical_deal_size": (25000, 150000),
        "percentage": 0.30,
        "sales_process": "b2b_enterprise",
        "sales_cycle_days": (60, 120)
    },
    "smb": {
        "name": "SMB",
        "employee_range": (10, 200),
        "annual_revenue_range": (1000000, 50000000),
        "typical_deal_size": (5000, 30000),
        "percentage": 0.60,
        "sales_process": "b2b_smb",
        "sales_cycle_days": (20, 60)
    }
}


# ============================================================================
# TERRITORY AND REGION TEMPLATES
# ============================================================================

TERRITORY_TEMPLATES = {
    "geographic": {
        "North America": {
            "regions": ["West", "Central", "East", "Canada"],
            "states": {
                "West": ["CA", "WA", "OR", "NV", "AZ", "CO", "UT"],
                "Central": ["TX", "IL", "OH", "MI", "MN", "WI", "MO"],
                "East": ["NY", "MA", "PA", "NJ", "VA", "NC", "FL", "GA"],
                "Canada": ["ON", "QC", "BC", "AB"]
            },
            "cities": {
                "major": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "San Francisco", "Toronto"],
                "secondary": ["Seattle", "Boston", "Austin", "Denver", "Atlanta", "Miami", "Dallas"]
            }
        },
        "EMEA": {
            "regions": ["UK & Ireland", "Northern Europe", "Central Europe", "Southern Europe", "Middle East"],
            "countries": {
                "UK & Ireland": ["United Kingdom", "Ireland"],
                "Northern Europe": ["Germany", "Netherlands", "Belgium", "Denmark", "Sweden", "Norway"],
                "Central Europe": ["France", "Switzerland", "Austria", "Poland"],
                "Southern Europe": ["Spain", "Italy", "Portugal", "Greece"],
                "Middle East": ["UAE", "Saudi Arabia", "Israel"]
            }
        },
        "APAC": {
            "regions": ["East Asia", "Southeast Asia", "Australia & NZ", "India"],
            "countries": {
                "East Asia": ["Japan", "South Korea", "China", "Hong Kong", "Taiwan"],
                "Southeast Asia": ["Singapore", "Malaysia", "Thailand", "Indonesia", "Philippines"],
                "Australia & NZ": ["Australia", "New Zealand"],
                "India": ["India"]
            }
        },
        "LATAM": {
            "regions": ["South America", "Central America", "Mexico"],
            "countries": {
                "South America": ["Brazil", "Argentina", "Chile", "Colombia", "Peru"],
                "Central America": ["Costa Rica", "Panama"],
                "Mexico": ["Mexico"]
            }
        }
    },
    "industry_vertical": {
        "industries": [
            "Technology", "Financial Services", "Healthcare", "Manufacturing",
            "Retail", "Energy", "Education", "Government", "Media", "Telecommunications"
        ]
    },
    "account_segment": {
        "segments": ["Enterprise", "Mid-Market", "SMB", "Strategic Accounts"]
    }
}


# ============================================================================
# INDUSTRY TEMPLATES
# ============================================================================

INDUSTRY_TEMPLATES = {
    "healthcare": {
        "name": "Healthcare",
        "description": "Healthcare providers, hospitals, medical device companies, pharmaceuticals",
        "account_types": {
            "Hospital System": 0.25,
            "Medical Practice": 0.30,
            "Medical Device Manufacturer": 0.15,
            "Pharmaceutical Company": 0.15,
            "Healthcare IT": 0.10,
            "Insurance Provider": 0.05
        },
        "typical_deal_size": {
            "small": (15000, 50000),
            "medium": (50000, 200000),
            "large": (200000, 1000000),
            "enterprise": (1000000, 10000000)
        },
        "sales_cycle_days": {
            "small": (60, 120),
            "medium": (90, 180),
            "large": (120, 270),
            "enterprise": (180, 365)
        },
        "product_catalog": {
            "EMR/EHR Solutions": {
                "base_price": 150000,
                "pricing_model": "per_hospital",
                "contract_term": 36,
                "products": [
                    {"name": "Core EMR Platform", "price": 150000},
                    {"name": "Patient Portal", "price": 25000},
                    {"name": "Clinical Analytics", "price": 50000},
                    {"name": "Integration Services", "price": 35000},
                    {"name": "Training & Support", "price": 20000}
                ]
            },
            "Medical Devices": {
                "base_price": 250000,
                "pricing_model": "per_device",
                "contract_term": 60,
                "products": [
                    {"name": "Diagnostic Equipment", "price": 250000},
                    {"name": "Monitoring Systems", "price": 150000},
                    {"name": "Service Contract", "price": 30000},
                    {"name": "Consumables", "price": 15000}
                ]
            },
            "Healthcare Analytics": {
                "base_price": 75000,
                "pricing_model": "per_year",
                "contract_term": 24,
                "products": [
                    {"name": "Population Health Analytics", "price": 75000},
                    {"name": "Quality Metrics Dashboard", "price": 40000},
                    {"name": "Risk Analytics", "price": 60000},
                    {"name": "Data Integration", "price": 35000}
                ]
            }
        },
        "compliance_fields": ["HIPAA_Compliant", "BAA_Required", "PHI_Handling"],
        "seasonal_patterns": {
            "Q1": 0.20,  # Budget planning
            "Q2": 0.25,
            "Q3": 0.25,
            "Q4": 0.30   # Year-end budget flush
        },
        "decision_makers": ["Chief Medical Officer", "CIO", "CFO", "Director of IT", "Practice Administrator"],
        "key_metrics": ["Patient Volume", "Number of Physicians", "Number of Beds", "Annual Patient Visits"]
    },

    "financial_services": {
        "name": "Financial Services",
        "description": "Banks, investment firms, insurance companies, fintech",
        "account_types": {
            "Commercial Bank": 0.20,
            "Investment Bank": 0.15,
            "Insurance Company": 0.20,
            "Wealth Management": 0.15,
            "Fintech": 0.20,
            "Credit Union": 0.10
        },
        "typical_deal_size": {
            "small": (25000, 75000),
            "medium": (75000, 300000),
            "large": (300000, 2000000),
            "enterprise": (2000000, 20000000)
        },
        "sales_cycle_days": {
            "small": (90, 150),
            "medium": (120, 210),
            "large": (150, 270),
            "enterprise": (180, 365)
        },
        "product_catalog": {
            "Core Banking Platform": {
                "base_price": 500000,
                "pricing_model": "per_branch",
                "contract_term": 60,
                "products": [
                    {"name": "Core Banking Software", "price": 500000},
                    {"name": "Digital Banking", "price": 200000},
                    {"name": "Mobile Banking", "price": 150000},
                    {"name": "ATM Network Management", "price": 100000},
                    {"name": "Fraud Detection", "price": 175000}
                ]
            },
            "Trading Platform": {
                "base_price": 750000,
                "pricing_model": "per_trader",
                "contract_term": 36,
                "products": [
                    {"name": "Trading Platform License", "price": 750000},
                    {"name": "Market Data Feeds", "price": 200000},
                    {"name": "Risk Management Module", "price": 300000},
                    {"name": "Compliance Suite", "price": 250000}
                ]
            },
            "Wealth Management CRM": {
                "base_price": 100000,
                "pricing_model": "per_advisor",
                "contract_term": 24,
                "products": [
                    {"name": "Advisor Workstation", "price": 100000},
                    {"name": "Client Portal", "price": 50000},
                    {"name": "Portfolio Analytics", "price": 75000},
                    {"name": "Reporting Suite", "price": 40000}
                ]
            }
        },
        "compliance_fields": ["SOX_Compliant", "PCI_DSS", "FINRA_Regulated", "SOC2_Required"],
        "seasonal_patterns": {
            "Q1": 0.30,  # Fiscal year planning
            "Q2": 0.25,
            "Q3": 0.20,  # Summer slowdown
            "Q4": 0.25
        },
        "decision_makers": ["CIO", "CTO", "CISO", "CFO", "Head of Trading", "Head of Compliance"],
        "key_metrics": ["AUM", "Number of Accounts", "Transaction Volume", "Number of Branches"]
    },

    "technology": {
        "name": "Technology / SaaS",
        "description": "Software companies, cloud providers, technology services",
        "account_types": {
            "SaaS Company": 0.35,
            "Enterprise Software": 0.25,
            "Cloud Provider": 0.15,
            "IT Services": 0.15,
            "Hardware Manufacturer": 0.10
        },
        "typical_deal_size": {
            "small": (10000, 40000),
            "medium": (40000, 150000),
            "large": (150000, 750000),
            "enterprise": (750000, 5000000)
        },
        "sales_cycle_days": {
            "small": (30, 60),
            "medium": (45, 90),
            "large": (60, 150),
            "enterprise": (120, 240)
        },
        "product_catalog": {
            "DevOps Platform": {
                "base_price": 50000,
                "pricing_model": "per_user",
                "contract_term": 12,
                "products": [
                    {"name": "CI/CD Pipeline", "price": 50000},
                    {"name": "Container Registry", "price": 25000},
                    {"name": "Security Scanning", "price": 35000},
                    {"name": "Monitoring & Observability", "price": 40000},
                    {"name": "Enterprise Support", "price": 20000}
                ]
            },
            "Cloud Infrastructure": {
                "base_price": 100000,
                "pricing_model": "consumption",
                "contract_term": 36,
                "products": [
                    {"name": "Compute Credits", "price": 100000},
                    {"name": "Storage Credits", "price": 50000},
                    {"name": "Network Credits", "price": 30000},
                    {"name": "Managed Services", "price": 75000}
                ]
            },
            "Developer Tools": {
                "base_price": 25000,
                "pricing_model": "per_developer",
                "contract_term": 12,
                "products": [
                    {"name": "IDE License", "price": 25000},
                    {"name": "Code Analytics", "price": 15000},
                    {"name": "Testing Suite", "price": 20000},
                    {"name": "Collaboration Tools", "price": 12000}
                ]
            }
        },
        "compliance_fields": ["SOC2_Type_II", "ISO_27001", "GDPR_Compliant"],
        "seasonal_patterns": {
            "Q1": 0.30,  # Budget refresh
            "Q2": 0.25,
            "Q3": 0.20,
            "Q4": 0.25
        },
        "decision_makers": ["CTO", "VP Engineering", "Director of DevOps", "Head of Infrastructure", "CISO"],
        "key_metrics": ["Developer Count", "Infrastructure Spend", "Cloud Footprint", "Application Count"]
    },

    "manufacturing": {
        "name": "Manufacturing",
        "description": "Industrial manufacturers, production facilities, supply chain",
        "account_types": {
            "Discrete Manufacturing": 0.35,
            "Process Manufacturing": 0.25,
            "Automotive": 0.15,
            "Aerospace": 0.10,
            "Electronics": 0.10,
            "Consumer Goods": 0.05
        },
        "typical_deal_size": {
            "small": (30000, 100000),
            "medium": (100000, 400000),
            "large": (400000, 2000000),
            "enterprise": (2000000, 15000000)
        },
        "sales_cycle_days": {
            "small": (60, 120),
            "medium": (90, 180),
            "large": (120, 270),
            "enterprise": (180, 365)
        },
        "product_catalog": {
            "Manufacturing Execution System": {
                "base_price": 300000,
                "pricing_model": "per_plant",
                "contract_term": 60,
                "products": [
                    {"name": "MES Core Platform", "price": 300000},
                    {"name": "Quality Management", "price": 150000},
                    {"name": "Inventory Management", "price": 100000},
                    {"name": "Production Scheduling", "price": 125000},
                    {"name": "IoT Integration", "price": 175000}
                ]
            },
            "Supply Chain Management": {
                "base_price": 250000,
                "pricing_model": "per_location",
                "contract_term": 36,
                "products": [
                    {"name": "Supply Chain Platform", "price": 250000},
                    {"name": "Demand Planning", "price": 100000},
                    {"name": "Supplier Portal", "price": 75000},
                    {"name": "Logistics Management", "price": 125000}
                ]
            },
            "Industrial IoT": {
                "base_price": 200000,
                "pricing_model": "per_sensor",
                "contract_term": 36,
                "products": [
                    {"name": "IoT Platform", "price": 200000},
                    {"name": "Predictive Maintenance", "price": 150000},
                    {"name": "Asset Monitoring", "price": 100000},
                    {"name": "Analytics Dashboard", "price": 75000}
                ]
            }
        },
        "compliance_fields": ["ISO_9001", "ISO_14001", "AS9100", "IATF_16949"],
        "seasonal_patterns": {
            "Q1": 0.25,
            "Q2": 0.25,
            "Q3": 0.20,  # Summer shutdowns
            "Q4": 0.30   # Capital budget spending
        },
        "decision_makers": ["VP Operations", "Plant Manager", "Director of Manufacturing", "CIO", "VP Supply Chain"],
        "key_metrics": ["Production Volume", "Number of Plants", "Employee Count", "SKU Count"]
    },

    "retail": {
        "name": "Retail / E-commerce",
        "description": "Retailers, e-commerce platforms, omnichannel commerce",
        "account_types": {
            "Department Store": 0.15,
            "Specialty Retail": 0.25,
            "E-commerce": 0.30,
            "Grocery": 0.15,
            "Convenience Store": 0.10,
            "Luxury Retail": 0.05
        },
        "typical_deal_size": {
            "small": (20000, 60000),
            "medium": (60000, 250000),
            "large": (250000, 1500000),
            "enterprise": (1500000, 10000000)
        },
        "sales_cycle_days": {
            "small": (45, 90),
            "medium": (60, 120),
            "large": (90, 180),
            "enterprise": (120, 270)
        },
        "product_catalog": {
            "E-commerce Platform": {
                "base_price": 150000,
                "pricing_model": "per_year",
                "contract_term": 24,
                "products": [
                    {"name": "Commerce Platform", "price": 150000},
                    {"name": "Mobile Commerce", "price": 75000},
                    {"name": "Order Management", "price": 60000},
                    {"name": "Inventory Sync", "price": 50000},
                    {"name": "Marketing Automation", "price": 40000}
                ]
            },
            "Point of Sale System": {
                "base_price": 100000,
                "pricing_model": "per_location",
                "contract_term": 36,
                "products": [
                    {"name": "POS Software", "price": 100000},
                    {"name": "Inventory Management", "price": 50000},
                    {"name": "Customer Loyalty", "price": 35000},
                    {"name": "Payment Processing", "price": 25000}
                ]
            },
            "Merchandising Platform": {
                "base_price": 120000,
                "pricing_model": "per_year",
                "contract_term": 24,
                "products": [
                    {"name": "Merchandise Planning", "price": 120000},
                    {"name": "Assortment Planning", "price": 80000},
                    {"name": "Price Optimization", "price": 90000},
                    {"name": "Promotion Management", "price": 60000}
                ]
            }
        },
        "compliance_fields": ["PCI_DSS", "GDPR_Compliant", "ADA_Compliant"],
        "seasonal_patterns": {
            "Q1": 0.15,  # Post-holiday slowdown
            "Q2": 0.25,
            "Q3": 0.30,  # Holiday prep
            "Q4": 0.30   # Holiday season
        },
        "decision_makers": ["CIO", "VP E-commerce", "Director of Merchandising", "CFO", "VP Store Operations"],
        "key_metrics": ["Annual Revenue", "Store Count", "E-commerce GMV", "SKU Count"]
    },

    "energy": {
        "name": "Energy / Utilities",
        "description": "Power generation, utilities, oil & gas, renewable energy - selling TO commercial/industrial customers",
        "account_types": {
            "Manufacturing Plant": 0.25,  # Large energy consumers
            "Commercial Real Estate": 0.20,  # Office buildings, shopping centers
            "Data Center": 0.15,  # High-density power users
            "Hospital / Healthcare System": 0.10,  # Critical infrastructure
            "Municipal Government": 0.10,  # Cities, counties
            "University / Education": 0.08,  # Campuses
            "Hotel / Hospitality": 0.07,  # Resorts, hotel chains
            "Warehouse / Distribution": 0.05  # Logistics facilities
        },
        "typical_deal_size": {
            "small": (50000, 150000),
            "medium": (150000, 600000),
            "large": (600000, 3000000),
            "enterprise": (3000000, 20000000)
        },
        "sales_cycle_days": {
            "small": (90, 180),
            "medium": (120, 240),
            "large": (180, 365),
            "enterprise": (270, 540)
        },
        "product_catalog": {
            "Grid Management System": {
                "base_price": 1000000,
                "pricing_model": "per_utility",
                "contract_term": 84,
                "products": [
                    {"name": "SCADA System", "price": 1000000},
                    {"name": "Outage Management", "price": 500000},
                    {"name": "Distribution Management", "price": 750000},
                    {"name": "Energy Trading Platform", "price": 600000}
                ]
            },
            "Asset Management": {
                "base_price": 400000,
                "pricing_model": "per_facility",
                "contract_term": 60,
                "products": [
                    {"name": "Asset Performance Management", "price": 400000},
                    {"name": "Predictive Maintenance", "price": 300000},
                    {"name": "Work Order Management", "price": 200000},
                    {"name": "Mobile Workforce", "price": 150000}
                ]
            },
            "Customer Information System": {
                "base_price": 500000,
                "pricing_model": "per_customer_account",
                "contract_term": 60,
                "products": [
                    {"name": "Billing System", "price": 500000},
                    {"name": "Customer Portal", "price": 200000},
                    {"name": "Meter Data Management", "price": 300000},
                    {"name": "Payment Processing", "price": 150000}
                ]
            }
        },
        "compliance_fields": ["NERC_CIP", "FERC_Compliant", "EPA_Regulations"],
        "seasonal_patterns": {
            "Q1": 0.25,
            "Q2": 0.25,
            "Q3": 0.20,
            "Q4": 0.30   # Capital project approvals
        },
        "decision_makers": ["CIO", "VP Operations", "Director of Grid Operations", "CFO", "VP Engineering"],
        "key_metrics": ["Customers Served", "Generation Capacity MW", "Service Territory", "Infrastructure Age"]
    },

    "telecommunications": {
        "name": "Telecommunications",
        "description": "Telecom operators, ISPs, network infrastructure",
        "account_types": {
            "Mobile Operator": 0.35,
            "Cable/Broadband": 0.25,
            "Fiber Provider": 0.20,
            "Satellite": 0.10,
            "MVNO": 0.10
        },
        "typical_deal_size": {
            "small": (40000, 120000),
            "medium": (120000, 500000),
            "large": (500000, 2500000),
            "enterprise": (2500000, 15000000)
        },
        "sales_cycle_days": {
            "small": (60, 120),
            "medium": (90, 180),
            "large": (120, 270),
            "enterprise": (180, 365)
        },
        "product_catalog": {
            "BSS/OSS Platform": {
                "base_price": 800000,
                "pricing_model": "per_subscriber",
                "contract_term": 60,
                "products": [
                    {"name": "Billing System", "price": 800000},
                    {"name": "Order Management", "price": 400000},
                    {"name": "Customer Care", "price": 350000},
                    {"name": "Network Inventory", "price": 450000}
                ]
            },
            "Network Management": {
                "base_price": 600000,
                "pricing_model": "per_network",
                "contract_term": 60,
                "products": [
                    {"name": "Network Monitoring", "price": 600000},
                    {"name": "Performance Management", "price": 400000},
                    {"name": "Fault Management", "price": 300000},
                    {"name": "Configuration Management", "price": 250000}
                ]
            },
            "Customer Experience": {
                "base_price": 300000,
                "pricing_model": "per_year",
                "contract_term": 36,
                "products": [
                    {"name": "Self-Service Portal", "price": 300000},
                    {"name": "Mobile App", "price": 200000},
                    {"name": "Analytics Platform", "price": 250000},
                    {"name": "AI Chatbot", "price": 150000}
                ]
            }
        },
        "compliance_fields": ["FCC_Compliant", "GDPR_Compliant", "CPNI_Protection"],
        "seasonal_patterns": {
            "Q1": 0.25,
            "Q2": 0.25,
            "Q3": 0.25,
            "Q4": 0.25   # Consistent throughout year
        },
        "decision_makers": ["CIO", "CTO", "VP Network Operations", "CFO", "VP Customer Experience"],
        "key_metrics": ["Subscriber Count", "Network Coverage", "ARPU", "Churn Rate"]
    },

    "education": {
        "name": "Education",
        "description": "Universities, K-12 schools, educational technology",
        "account_types": {
            "University": 0.30,
            "K-12 School District": 0.35,
            "Community College": 0.15,
            "Private School": 0.15,
            "EdTech Company": 0.05
        },
        "typical_deal_size": {
            "small": (15000, 50000),
            "medium": (50000, 200000),
            "large": (200000, 800000),
            "enterprise": (800000, 5000000)
        },
        "sales_cycle_days": {
            "small": (60, 120),
            "medium": (90, 180),
            "large": (120, 270),
            "enterprise": (180, 365)
        },
        "product_catalog": {
            "Learning Management System": {
                "base_price": 100000,
                "pricing_model": "per_student",
                "contract_term": 36,
                "products": [
                    {"name": "LMS Platform", "price": 100000},
                    {"name": "Mobile Learning", "price": 40000},
                    {"name": "Assessment Tools", "price": 50000},
                    {"name": "Analytics Dashboard", "price": 35000}
                ]
            },
            "Student Information System": {
                "base_price": 150000,
                "pricing_model": "per_school",
                "contract_term": 60,
                "products": [
                    {"name": "SIS Core", "price": 150000},
                    {"name": "Gradebook", "price": 40000},
                    {"name": "Parent Portal", "price": 30000},
                    {"name": "Attendance Tracking", "price": 25000}
                ]
            },
            "Campus Management": {
                "base_price": 200000,
                "pricing_model": "per_campus",
                "contract_term": 60,
                "products": [
                    {"name": "Enrollment Management", "price": 200000},
                    {"name": "Financial Aid", "price": 100000},
                    {"name": "Housing Management", "price": 75000},
                    {"name": "Events Management", "price": 50000}
                ]
            }
        },
        "compliance_fields": ["FERPA_Compliant", "COPPA_Compliant", "ADA_Accessible"],
        "seasonal_patterns": {
            "Q1": 0.15,
            "Q2": 0.20,
            "Q3": 0.45,  # Summer budget approvals
            "Q4": 0.20
        },
        "decision_makers": ["CIO", "Superintendent", "Provost", "VP IT", "Dean of Students"],
        "key_metrics": ["Student Enrollment", "Faculty Count", "Campus Count", "Annual Budget"]
    },

    "government": {
        "name": "Government / Public Sector",
        "description": "Federal, state, and local government agencies",
        "account_types": {
            "Federal Agency": 0.25,
            "State Government": 0.25,
            "Local Government": 0.30,
            "Public Safety": 0.15,
            "Defense": 0.05
        },
        "typical_deal_size": {
            "small": (30000, 100000),
            "medium": (100000, 500000),
            "large": (500000, 3000000),
            "enterprise": (3000000, 25000000)
        },
        "sales_cycle_days": {
            "small": (120, 240),
            "medium": (180, 365),
            "large": (270, 540),
            "enterprise": (365, 730)  # Can take 1-2 years
        },
        "product_catalog": {
            "Citizen Services Portal": {
                "base_price": 300000,
                "pricing_model": "per_agency",
                "contract_term": 60,
                "products": [
                    {"name": "Citizen Portal", "price": 300000},
                    {"name": "Permit Management", "price": 150000},
                    {"name": "Payment Processing", "price": 100000},
                    {"name": "Mobile App", "price": 125000}
                ]
            },
            "Case Management": {
                "base_price": 250000,
                "pricing_model": "per_department",
                "contract_term": 60,
                "products": [
                    {"name": "Case Management Platform", "price": 250000},
                    {"name": "Document Management", "price": 150000},
                    {"name": "Workflow Automation", "price": 100000},
                    {"name": "Reporting & Analytics", "price": 75000}
                ]
            },
            "Public Safety System": {
                "base_price": 500000,
                "pricing_model": "per_jurisdiction",
                "contract_term": 84,
                "products": [
                    {"name": "CAD System", "price": 500000},
                    {"name": "RMS Platform", "price": 400000},
                    {"name": "Mobile Data Terminals", "price": 300000},
                    {"name": "Evidence Management", "price": 200000}
                ]
            }
        },
        "compliance_fields": ["FedRAMP_Authorized", "FISMA_Compliant", "NIST_800_53"],
        "seasonal_patterns": {
            "Q1": 0.35,  # Fiscal year start (Oct 1 for federal)
            "Q2": 0.25,
            "Q3": 0.20,
            "Q4": 0.20
        },
        "decision_makers": ["CIO", "IT Director", "Program Manager", "Procurement Officer", "Agency Director"],
        "key_metrics": ["Population Served", "Annual Budget", "Employee Count", "Service Area"]
    },

    "media": {
        "name": "Media / Entertainment",
        "description": "Media companies, broadcasting, streaming, content production",
        "account_types": {
            "Broadcaster": 0.25,
            "Streaming Service": 0.25,
            "Production Studio": 0.20,
            "Publishing": 0.15,
            "Gaming": 0.15
        },
        "typical_deal_size": {
            "small": (25000, 80000),
            "medium": (80000, 300000),
            "large": (300000, 1500000),
            "enterprise": (1500000, 10000000)
        },
        "sales_cycle_days": {
            "small": (45, 90),
            "medium": (60, 120),
            "large": (90, 180),
            "enterprise": (120, 270)
        },
        "product_catalog": {
            "Content Management": {
                "base_price": 200000,
                "pricing_model": "per_year",
                "contract_term": 36,
                "products": [
                    {"name": "Digital Asset Management", "price": 200000},
                    {"name": "Metadata Management", "price": 100000},
                    {"name": "Rights Management", "price": 150000},
                    {"name": "Distribution Platform", "price": 175000}
                ]
            },
            "Streaming Platform": {
                "base_price": 300000,
                "pricing_model": "per_subscriber",
                "contract_term": 36,
                "products": [
                    {"name": "Video Platform", "price": 300000},
                    {"name": "CDN Services", "price": 200000},
                    {"name": "DRM Protection", "price": 150000},
                    {"name": "Analytics", "price": 100000}
                ]
            },
            "Production Tools": {
                "base_price": 150000,
                "pricing_model": "per_seat",
                "contract_term": 24,
                "products": [
                    {"name": "Production Suite", "price": 150000},
                    {"name": "Collaboration Platform", "price": 75000},
                    {"name": "Storage & Archive", "price": 125000},
                    {"name": "Rendering Services", "price": 100000}
                ]
            }
        },
        "compliance_fields": ["FCC_Compliant", "DMCA_Protection", "GDPR_Compliant"],
        "seasonal_patterns": {
            "Q1": 0.25,
            "Q2": 0.25,
            "Q3": 0.25,
            "Q4": 0.25   # Content production year-round
        },
        "decision_makers": ["CTO", "VP Technology", "Head of Production", "CFO", "VP Operations"],
        "key_metrics": ["Content Library Size", "Subscribers", "Production Volume", "Distribution Channels"]
    }
}


# ============================================================================
# WIN/LOSS REASONS
# ============================================================================

WIN_LOSS_REASONS = {
    "closed_won_reasons": {
        "Superior Product Features": 0.25,
        "Best Value/ROI": 0.20,
        "Strong Relationship": 0.15,
        "Competitive Pricing": 0.15,
        "Better Implementation Timeline": 0.10,
        "Superior Customer Support": 0.10,
        "Strategic Partnership": 0.05
    },
    "closed_lost_reasons": {
        "Lost to Competitor": 0.30,
        "Price Too High": 0.20,
        "No Decision / No Budget": 0.15,
        "Missing Features": 0.12,
        "Implementation Complexity": 0.08,
        "Poor Timing": 0.08,
        "Internal Solution": 0.05,
        "Went with Incumbent": 0.02
    },
    "top_competitors": [
        "Competitor A", "Competitor B", "Competitor C",
        "Open Source Alternative", "Build In-House"
    ]
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
        >>> print(config['account_count_range'])
        (20, 150)
    """
    return ORG_SIZE_TEMPLATES.get(size.lower(), ORG_SIZE_TEMPLATES['midsize'])


def get_industry_config(industry: str, org_size: str = "midsize") -> Dict[str, Any]:
    """
    Get comprehensive configuration for an industry and org size combination.

    Args:
        industry: Industry key (e.g., 'healthcare', 'technology')
        org_size: Organization size ('startup', 'midsize', 'enterprise')

    Returns:
        Industry configuration dictionary with org-size adjusted values

    Example:
        >>> config = get_industry_config('healthcare', 'enterprise')
        >>> print(config['name'])
        'Healthcare'
    """
    industry_config = INDUSTRY_TEMPLATES.get(industry.lower(), {})
    org_config = get_org_size_config(org_size)

    # Merge industry and org size configs
    combined_config = {**industry_config}
    combined_config['org_size'] = org_size
    combined_config['org_config'] = org_config

    return combined_config


def calculate_account_distribution(
    total_accounts: int,
    industry: str,
    org_size: str = "midsize"
) -> Dict[str, int]:
    """
    Calculate distribution of accounts across different account types for an industry.

    Uses industry-specific account type percentages to create realistic distribution.

    Args:
        total_accounts: Total number of accounts to distribute
        industry: Industry key
        org_size: Organization size

    Returns:
        Dictionary mapping account type to count

    Example:
        >>> distribution = calculate_account_distribution(1000, 'healthcare')
        >>> print(distribution)
        {'Hospital System': 250, 'Medical Practice': 300, ...}
    """
    industry_config = get_industry_config(industry, org_size)
    account_types = industry_config.get('account_types', {})

    if not account_types:
        # Default distribution if no industry-specific types
        return {"Prospect": int(total_accounts * 0.3), "Customer": int(total_accounts * 0.7)}

    distribution = {}
    remaining = total_accounts

    # Sort by percentage descending to allocate larger segments first
    sorted_types = sorted(account_types.items(), key=lambda x: x[1], reverse=True)

    for i, (account_type, percentage) in enumerate(sorted_types):
        if i == len(sorted_types) - 1:
            # Last type gets remaining accounts
            distribution[account_type] = remaining
        else:
            count = int(total_accounts * percentage)
            distribution[account_type] = count
            remaining -= count

    return distribution


def get_sales_process(
    industry: str,
    deal_type: str = "new_business",
    account_segment: str = "mid_market"
) -> Dict[str, Any]:
    """
    Get appropriate sales process template based on deal characteristics.

    Args:
        industry: Industry key
        deal_type: Type of opportunity ('new_business', 'renewal', 'upsell')
        account_segment: Account size ('enterprise', 'mid_market', 'smb')

    Returns:
        Sales process template with stages and conversion rates

    Example:
        >>> process = get_sales_process('technology', 'new_business', 'enterprise')
        >>> print(process['name'])
        'Enterprise B2B Sales'
    """
    # Determine appropriate process based on parameters
    if deal_type in ['renewal', 'upsell', 'expansion']:
        return SALES_PROCESS_TEMPLATES['renewal']

    if account_segment == 'smb':
        return SALES_PROCESS_TEMPLATES['b2b_smb']
    else:
        # mid_market and enterprise use enterprise process
        return SALES_PROCESS_TEMPLATES['b2b_enterprise']


def generate_opportunity_data(
    industry: str,
    account_segment: str = "mid_market",
    deal_type: str = "new_business",
    org_size: str = "midsize"
) -> Dict[str, Any]:
    """
    Generate realistic opportunity data including amount, products, timeline.

    Args:
        industry: Industry key
        account_segment: Account size segment
        deal_type: Opportunity type
        org_size: Organization size

    Returns:
        Dictionary with opportunity attributes

    Example:
        >>> opp = generate_opportunity_data('healthcare', 'enterprise', 'new_business')
        >>> print(opp['amount'])
        450000
    """
    industry_config = get_industry_config(industry, org_size)
    segment_config = ACCOUNT_SEGMENTS.get(account_segment, ACCOUNT_SEGMENTS['mid_market'])

    # Get deal size range for segment
    deal_size_range = segment_config['typical_deal_size']
    amount = random.randint(deal_size_range[0], deal_size_range[1])

    # Get sales cycle
    sales_cycle_range = segment_config['sales_cycle_days']
    sales_cycle_days = random.randint(sales_cycle_range[0], sales_cycle_range[1])

    # Get sales process
    sales_process = get_sales_process(industry, deal_type, account_segment)

    # Select random stage (weighted towards earlier stages for active pipeline)
    stage_weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.03, 0.02]
    stages = sales_process['stages']
    stage = random.choices(stages[:len(stage_weights)], weights=stage_weights[:len(stages)])[0]

    # Calculate close date based on current stage and remaining cycle time
    today = datetime.now()
    days_remaining = random.randint(7, sales_cycle_days)
    close_date = today + timedelta(days=days_remaining)

    return {
        "amount": amount,
        "stage": stage['name'],
        "probability": stage['probability'],
        "close_date": close_date.strftime('%Y-%m-%d'),
        "sales_cycle_days": sales_cycle_days,
        "type": OPPORTUNITY_TYPES[deal_type]['name'],
        "sales_process": sales_process['name']
    }


def get_typical_products(
    industry: str,
    deal_size: int = 100000
) -> List[Dict[str, Any]]:
    """
    Get appropriate product mix for an industry and deal size.

    Args:
        industry: Industry key
        deal_size: Total deal amount

    Returns:
        List of products with names and prices that sum to approximately deal_size

    Example:
        >>> products = get_typical_products('healthcare', 200000)
        >>> print(len(products))
        3
    """
    industry_config = get_industry_config(industry)
    product_catalog = industry_config.get('product_catalog', {})

    if not product_catalog:
        # Generic products if no industry-specific catalog
        return [{"name": "Professional Services", "price": deal_size}]

    selected_products = []
    remaining_amount = deal_size

    # Pick 1-3 product families
    num_families = min(random.randint(1, 3), len(product_catalog))
    families = random.sample(list(product_catalog.keys()), num_families)

    for family in families:
        family_products = product_catalog[family]['products']
        # Pick 1-3 products from this family
        num_products = min(random.randint(1, 3), len(family_products))
        products = random.sample(family_products, num_products)

        for product in products:
            # Scale price to fit remaining budget
            scaled_price = min(product['price'], remaining_amount)
            if scaled_price > 0:
                selected_products.append({
                    "name": product['name'],
                    "price": scaled_price,
                    "family": family
                })
                remaining_amount -= scaled_price

    # Adjust last product to match deal size exactly
    if selected_products and remaining_amount != 0:
        selected_products[-1]['price'] += remaining_amount

    return selected_products


def calculate_sales_team_size(
    org_size: str,
    industry: str = "technology"
) -> Dict[str, int]:
    """
    Calculate realistic sales team size and composition.

    Args:
        org_size: Organization size key
        industry: Industry key (some industries have different ratios)

    Returns:
        Dictionary with counts for each sales role

    Example:
        >>> team = calculate_sales_team_size('enterprise')
        >>> print(team['account_executives'])
        250
    """
    org_config = get_org_size_config(org_size)

    return {
        "sales_development_reps": random.randint(
            org_config['sales_development_reps'][0],
            org_config['sales_development_reps'][1]
        ),
        "account_executives": random.randint(
            org_config['account_executives'][0],
            org_config['account_executives'][1]
        ),
        "customer_success_managers": random.randint(
            org_config['customer_success_managers'][0],
            org_config['customer_success_managers'][1]
        ),
        "sales_managers": random.randint(
            org_config['sales_managers'][0],
            org_config['sales_managers'][1]
        ),
        "total_sales_team": org_config['sales_team_size'][1]
    }


def get_seasonal_multiplier(month: int, industry: str = "technology") -> float:
    """
    Get seasonal multiplier for opportunity creation/closure rates.

    Different industries have different seasonal patterns (e.g., retail spikes in Q4,
    government spikes in Q1, education spikes in Q3).

    Args:
        month: Month number (1-12)
        industry: Industry key

    Returns:
        Multiplier for that month (1.0 = average)

    Example:
        >>> multiplier = get_seasonal_multiplier(12, 'retail')
        >>> print(multiplier > 1.0)  # Q4 is strong for retail
        True
    """
    industry_config = get_industry_config(industry)
    seasonal_patterns = industry_config.get('seasonal_patterns', {
        "Q1": 0.25, "Q2": 0.25, "Q3": 0.25, "Q4": 0.25
    })

    # Map month to quarter
    quarter_map = {
        1: "Q1", 2: "Q1", 3: "Q1",
        4: "Q2", 5: "Q2", 6: "Q2",
        7: "Q3", 8: "Q3", 9: "Q3",
        10: "Q4", 11: "Q4", 12: "Q4"
    }

    quarter = quarter_map[month]
    quarter_percentage = seasonal_patterns[quarter]

    # Convert to multiplier (0.25 = 1.0x average, 0.30 = 1.2x, etc.)
    return quarter_percentage * 4


def calculate_opportunity_stage_duration(
    stage_name: str,
    sales_process: str = "b2b_enterprise"
) -> int:
    """
    Calculate realistic duration for an opportunity stage.

    Args:
        stage_name: Name of the stage
        sales_process: Sales process template key

    Returns:
        Duration in days

    Example:
        >>> days = calculate_opportunity_stage_duration('Discovery')
        >>> print(days)
        22
    """
    process = SALES_PROCESS_TEMPLATES.get(sales_process, SALES_PROCESS_TEMPLATES['b2b_enterprise'])

    for stage in process['stages']:
        if stage['name'] == stage_name:
            duration_range = stage['avg_duration_days']
            return random.randint(duration_range[0], duration_range[1])

    # Default if stage not found
    return random.randint(7, 30)


def get_win_loss_reason(is_won: bool) -> str:
    """
    Get a realistic win or loss reason with weighted probability.

    Args:
        is_won: True if opportunity was won, False if lost

    Returns:
        Reason string

    Example:
        >>> reason = get_win_loss_reason(True)
        >>> print(reason in WIN_LOSS_REASONS['closed_won_reasons'])
        True
    """
    if is_won:
        reasons = WIN_LOSS_REASONS['closed_won_reasons']
    else:
        reasons = WIN_LOSS_REASONS['closed_lost_reasons']

    # Weighted random selection
    return random.choices(
        list(reasons.keys()),
        weights=list(reasons.values())
    )[0]


def get_all_industries() -> List[str]:
    """
    Get list of all available industries.

    Returns:
        List of industry keys

    Example:
        >>> industries = get_all_industries()
        >>> print('healthcare' in industries)
        True
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


def get_territory_structure(org_size: str, territory_type: str = "geographic") -> Dict[str, Any]:
    """
    Get territory structure based on org size and territory type.

    Args:
        org_size: Organization size
        territory_type: Type of territory structure ('geographic', 'industry_vertical', 'account_segment')

    Returns:
        Territory structure configuration

    Example:
        >>> structure = get_territory_structure('enterprise', 'geographic')
        >>> print('North America' in structure)
        True
    """
    org_config = get_org_size_config(org_size)

    if not org_config['has_territory_management']:
        return {}

    return TERRITORY_TEMPLATES.get(territory_type, {})


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SALESFORCE CRM TEMPLATES")
    print("=" * 80)

    # Show all industries
    print("\nAvailable Industries:")
    for industry in get_all_industries():
        config = get_industry_config(industry)
        print(f"  • {config['name']}")
        print(f"    Account Types: {len(config.get('account_types', {}))}")
        print(f"    Product Families: {len(config.get('product_catalog', {}))}")
        print(f"    Decision Makers: {len(config.get('decision_makers', []))}")

    # Show all org sizes
    print("\nAvailable Organization Sizes:")
    for size in get_all_org_sizes():
        config = get_org_size_config(size)
        print(f"  • {config['name']}")
        print(f"    Accounts: {config['account_count_range'][0]:,}-{config['account_count_range'][1]:,}")
        print(f"    Sales Team: {config['sales_team_size'][0]}-{config['sales_team_size'][1]}")
        print(f"    Active Opportunities: {config['active_opportunity_range'][0]:,}-{config['active_opportunity_range'][1]:,}")

    # Show sample account distribution
    print("\nSample Account Distribution (1000 accounts in Healthcare):")
    distribution = calculate_account_distribution(1000, 'healthcare', 'enterprise')
    for account_type, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {account_type}: {count:,} accounts ({count/10:.1f}%)")

    # Show sample opportunity
    print("\nSample Enterprise Healthcare Opportunity:")
    opp = generate_opportunity_data('healthcare', 'enterprise', 'new_business', 'enterprise')
    for key, value in opp.items():
        print(f"  {key}: {value}")

    # Show sample products
    print("\nSample Product Mix ($500K Healthcare Deal):")
    products = get_typical_products('healthcare', 500000)
    total = 0
    for product in products:
        print(f"  {product['name']}: ${product['price']:,} ({product['family']})")
        total += product['price']
    print(f"  Total: ${total:,}")

    # Show sales team structure
    print("\nSample Sales Team (Enterprise):")
    team = calculate_sales_team_size('enterprise')
    for role, count in team.items():
        print(f"  {role.replace('_', ' ').title()}: {count:,}")

    # Show sales process
    print("\nEnterprise B2B Sales Process:")
    process = get_sales_process('technology', 'new_business', 'enterprise')
    print(f"  Process: {process['name']}")
    print(f"  Overall Win Rate: {process['overall_win_rate']*100:.1f}%")
    print(f"  Avg Cycle: {process['avg_total_cycle_days'][0]}-{process['avg_total_cycle_days'][1]} days")
    print(f"  Stages:")
    for stage in process['stages']:
        if not stage['is_closed']:
            print(f"    • {stage['name']} ({stage['probability']}%) - {stage['avg_duration_days'][0]}-{stage['avg_duration_days'][1]} days")

    # Show seasonal patterns
    print("\nSeasonal Multipliers (Retail Industry):")
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for i, month in enumerate(months, 1):
        multiplier = get_seasonal_multiplier(i, 'retail')
        print(f"  {month}: {multiplier:.2f}x", end="  ")
        if i % 4 == 0:
            print()

    print("\n" + "=" * 80)
