#!/usr/bin/env python3
"""
Template library for industry-specific use cases.
Supports multiple platform types (Asana, Okta, future platforms).
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
]
