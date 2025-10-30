#!/usr/bin/env python3
"""
Template library for industry-specific use cases.
Supports multiple platform types (Asana, Okta, Salesforce).
"""

# Asana templates
from continuous.templates.asana_templates import (
    INDUSTRY_TEMPLATES as ASANA_INDUSTRY_TEMPLATES,
    get_industry_template,
    get_use_case,
    get_all_use_cases,
    get_default_use_case,
    get_random_use_case,
    get_all_industries
)

# Okta templates
from continuous.templates.okta_templates import (
    ORG_SIZE_TEMPLATES,
    INDUSTRY_TEMPLATES as OKTA_INDUSTRY_TEMPLATES,
    COMMON_APPS,
    GROUP_STRUCTURE_TEMPLATES,
    USER_PROFILE_TEMPLATES,
    APP_ASSIGNMENT_PATTERNS,
    get_org_size_config,
    get_industry_config,
    get_departments_for_industry,
    get_apps_for_industry,
    get_user_titles_for_department,
    calculate_user_distribution,
    get_app_assignment_pattern,
    get_all_industries as get_all_okta_industries,
    get_all_org_sizes,
    get_group_structure_template,
    generate_sample_user_profile
)

# Salesforce templates
from continuous.templates.salesforce_templates import (
    ORG_SIZE_TEMPLATES as SALESFORCE_ORG_SIZE_TEMPLATES,
    INDUSTRY_TEMPLATES as SALESFORCE_INDUSTRY_TEMPLATES,
    SALES_PROCESS_TEMPLATES,
    OPPORTUNITY_TYPES,
    LEAD_SOURCES,
    CONTACT_ROLES,
    CASE_TEMPLATES,
    ACCOUNT_TYPES,
    ACCOUNT_SEGMENTS,
    TERRITORY_TEMPLATES,
    WIN_LOSS_REASONS,
    get_org_size_config as get_salesforce_org_size_config,
    get_industry_config as get_salesforce_industry_config,
    calculate_account_distribution,
    get_sales_process,
    generate_opportunity_data,
    get_typical_products,
    calculate_sales_team_size,
    get_seasonal_multiplier,
    calculate_opportunity_stage_duration,
    get_win_loss_reason,
    get_all_industries as get_all_salesforce_industries,
    get_all_org_sizes as get_all_salesforce_org_sizes,
    get_territory_structure
)

# Legacy exports (Asana)
INDUSTRY_TEMPLATES = ASANA_INDUSTRY_TEMPLATES

__all__ = [
    # Asana exports
    'ASANA_INDUSTRY_TEMPLATES',
    'INDUSTRY_TEMPLATES',
    'get_industry_template',
    'get_use_case',
    'get_all_use_cases',
    'get_default_use_case',
    'get_random_use_case',
    'get_all_industries',

    # Okta exports
    'ORG_SIZE_TEMPLATES',
    'OKTA_INDUSTRY_TEMPLATES',
    'COMMON_APPS',
    'GROUP_STRUCTURE_TEMPLATES',
    'USER_PROFILE_TEMPLATES',
    'APP_ASSIGNMENT_PATTERNS',
    'get_org_size_config',
    'get_industry_config',
    'get_departments_for_industry',
    'get_apps_for_industry',
    'get_user_titles_for_department',
    'calculate_user_distribution',
    'get_app_assignment_pattern',
    'get_all_okta_industries',
    'get_all_org_sizes',
    'get_group_structure_template',
    'generate_sample_user_profile',

    # Salesforce exports
    'SALESFORCE_ORG_SIZE_TEMPLATES',
    'SALESFORCE_INDUSTRY_TEMPLATES',
    'SALES_PROCESS_TEMPLATES',
    'OPPORTUNITY_TYPES',
    'LEAD_SOURCES',
    'CONTACT_ROLES',
    'CASE_TEMPLATES',
    'ACCOUNT_TYPES',
    'ACCOUNT_SEGMENTS',
    'TERRITORY_TEMPLATES',
    'WIN_LOSS_REASONS',
    'get_salesforce_org_size_config',
    'get_salesforce_industry_config',
    'calculate_account_distribution',
    'get_sales_process',
    'generate_opportunity_data',
    'get_typical_products',
    'calculate_sales_team_size',
    'get_seasonal_multiplier',
    'calculate_opportunity_stage_duration',
    'get_win_loss_reason',
    'get_all_salesforce_industries',
    'get_all_salesforce_org_sizes',
    'get_territory_structure',
]
