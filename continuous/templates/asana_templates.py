#!/usr/bin/env python3
"""
Industry-specific use case templates for realistic Asana data generation.
Maps industries to use cases to Asana platform features.
"""

from typing import Dict, List, Any


# Custom Field Type Constants
CUSTOM_FIELD_TEXT = "text"
CUSTOM_FIELD_NUMBER = "number"
CUSTOM_FIELD_ENUM = "enum"  # Single-select dropdown
CUSTOM_FIELD_MULTI_ENUM = "multi_enum"  # Multi-select
CUSTOM_FIELD_DATE = "date"
CUSTOM_FIELD_PEOPLE = "people"


INDUSTRY_TEMPLATES = {
    "healthcare": {
        "name": "Healthcare",
        "use_cases": [
            {
                "name": "EMR System Migration",
                "description": "Electronic Medical Records system upgrade and data migration",
                "custom_fields": [
                    {"name": "Patient Records Count", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "HIPAA Compliance Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "In Progress", "Compliant", "Needs Review"]},
                    {"name": "Provider Training", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "Scheduled", "In Progress", "Completed"]},
                    {"name": "Go-Live Date", "type": CUSTOM_FIELD_DATE},
                    {"name": "Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Risk Level", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Low", "Medium", "High", "Critical"]},
                ],
                "sections": ["Assessment", "Planning", "Data Migration", "Testing", "Go-Live", "Post-Launch Support"],
                "tags": ["patient-safety", "regulatory", "training-required", "data-sensitive", "critical-system"],
                "milestones": ["Assessment Complete", "Migration Plan Approved", "Test Migration Complete", "Go-Live", "30-Day Review"],
                "portfolios": True,
                "portfolio_name": "Health IT Modernization"
            },
            {
                "name": "New Hospital Wing Construction",
                "description": "Construction and setup of new patient care facility",
                "custom_fields": [
                    {"name": "Construction Phase", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Planning", "Foundation", "Framing", "MEP", "Interior", "Completion"]},
                    {"name": "Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Safety Inspections", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Due", "Scheduled", "Passed", "Failed", "Remediated"]},
                    {"name": "Regulatory Approvals", "type": CUSTOM_FIELD_MULTI_ENUM,
                     "options": ["Building Permit", "Fire Safety", "Health Dept", "ADA Compliance", "Final Occupancy"]},
                    {"name": "Contractor", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Completion Date", "type": CUSTOM_FIELD_DATE},
                ],
                "sections": ["Permits & Approvals", "Foundation", "Structure", "MEP Systems", "Interior Build-Out", "Inspections & Certification"],
                "tags": ["construction", "safety-critical", "regulatory", "high-budget", "multi-year"],
                "milestones": ["Groundbreaking", "Foundation Complete", "Structure Complete", "Certificate of Occupancy", "Grand Opening"],
                "portfolios": True,
                "portfolio_name": "Facilities Expansion"
            },
            {
                "name": "Clinical Trial Management",
                "description": "Multi-site clinical research trial coordination",
                "custom_fields": [
                    {"name": "Trial Phase", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Phase I", "Phase II", "Phase III", "Phase IV"]},
                    {"name": "Patient Enrollment", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "FDA Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Pre-Submission", "Under Review", "Approved", "Conditional Approval"]},
                    {"name": "IRB Approval", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Pending", "Approved", "Needs Modification", "Expired"]},
                    {"name": "Study Site", "type": CUSTOM_FIELD_TEXT},
                ],
                "sections": ["Protocol Development", "IRB Submission", "Site Setup", "Patient Recruitment", "Data Collection", "Analysis & Reporting"],
                "tags": ["research", "regulatory", "patient-safety", "data-analysis", "multi-site"],
                "milestones": ["IRB Approval", "First Patient Enrolled", "Enrollment Complete", "Data Lock", "Study Publication"],
                "portfolios": True,
                "portfolio_name": "Clinical Research Pipeline"
            }
        ]
    },
    "technology": {
        "name": "Technology / SaaS",
        "use_cases": [
            {
                "name": "Q4 Product Launch",
                "description": "Major product release with new features and infrastructure",
                "custom_fields": [
                    {"name": "Story Points", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Sprint", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Feature Flag", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Release Version", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Priority", "type": CUSTOM_FIELD_ENUM,
                     "options": ["P0 - Critical", "P1 - High", "P2 - Medium", "P3 - Low"]},
                    {"name": "Engineering Team", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Platform", "Frontend", "Backend", "Mobile", "DevOps", "QA"]},
                ],
                "sections": ["Backlog", "Sprint Planning", "In Development", "Code Review", "QA Testing", "Staging", "Production"],
                "tags": ["critical-path", "customer-request", "technical-debt", "breaking-change", "performance", "security"],
                "milestones": ["Feature Complete", "Code Freeze", "Beta Release", "GA Release", "Post-Launch Review"],
                "portfolios": True,
                "portfolio_name": "2024 Product Roadmap"
            },
            {
                "name": "Cloud Infrastructure Migration",
                "description": "Migration from on-premise to cloud infrastructure",
                "custom_fields": [
                    {"name": "Migration Phase", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Assessment", "Planning", "Pilot", "Migration", "Optimization", "Complete"]},
                    {"name": "Service Category", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Compute", "Storage", "Database", "Networking", "Security", "Monitoring"]},
                    {"name": "Cost Estimate", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Downtime Required", "type": CUSTOM_FIELD_ENUM,
                     "options": ["None", "Minimal (<1hr)", "Moderate (1-4hr)", "Extended (>4hr)"]},
                    {"name": "Migration Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "In Progress", "Testing", "Completed", "Rolled Back"]},
                ],
                "sections": ["Discovery", "Architecture Design", "Proof of Concept", "Migration Execution", "Testing & Validation", "Cutover"],
                "tags": ["infrastructure", "high-risk", "cost-optimization", "scalability", "security"],
                "milestones": ["Architecture Approved", "Pilot Complete", "First Workload Migrated", "Full Migration", "Decommission Legacy"],
                "portfolios": True,
                "portfolio_name": "Digital Transformation"
            },
            {
                "name": "API Platform Rollout",
                "description": "New developer API platform and ecosystem",
                "custom_fields": [
                    {"name": "API Version", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Breaking Change", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Yes", "No"]},
                    {"name": "Documentation Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "In Progress", "Review", "Published"]},
                    {"name": "Developer Beta Users", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "SLA Tier", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Standard", "Premium", "Enterprise"]},
                ],
                "sections": ["API Design", "Implementation", "Documentation", "Developer Beta", "Launch", "Developer Support"],
                "tags": ["api", "developer-experience", "documentation", "backward-compatibility", "performance"],
                "milestones": ["API Spec Finalized", "Beta Launch", "GA Launch", "1000 Developers", "Rate Limit Optimization"],
                "portfolios": True,
                "portfolio_name": "Platform Services"
            }
        ]
    },
    "financial_services": {
        "name": "Financial Services",
        "use_cases": [
            {
                "name": "SOX Compliance Audit Preparation",
                "description": "Annual Sarbanes-Oxley compliance audit and remediation",
                "custom_fields": [
                    {"name": "Risk Level", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Low", "Medium", "High", "Critical"]},
                    {"name": "Compliance Framework", "type": CUSTOM_FIELD_MULTI_ENUM,
                     "options": ["SOX", "SOC2", "PCI-DSS", "GDPR", "CCPA"]},
                    {"name": "Audit Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "In Progress", "Control Testing", "Remediation", "Closed"]},
                    {"name": "Remediation Priority", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Immediate", "30 Days", "60 Days", "90 Days"]},
                    {"name": "Control Owner", "type": CUSTOM_FIELD_TEXT},
                ],
                "sections": ["Gap Analysis", "Control Documentation", "Testing", "Remediation", "Management Review", "External Audit"],
                "tags": ["sox-compliance", "high-risk", "board-visibility", "regulatory", "financial-reporting"],
                "milestones": ["Scoping Complete", "Internal Testing Complete", "Remediation Complete", "Management Sign-Off", "Audit Complete"],
                "portfolios": True,
                "portfolio_name": "Regulatory & Compliance"
            },
            {
                "name": "New Banking Product Launch",
                "description": "Launch of new consumer banking product",
                "custom_fields": [
                    {"name": "Product Stage", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Concept", "Development", "Testing", "Soft Launch", "General Availability"]},
                    {"name": "Regulatory Approval", "type": CUSTOM_FIELD_MULTI_ENUM,
                     "options": ["FDIC", "OCC", "State Banking", "Consumer Protection"]},
                    {"name": "Marketing Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Target Customer Segment", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Mass Market", "Premium", "Private Banking", "Business Banking"]},
                    {"name": "Expected Accounts", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                ],
                "sections": ["Product Design", "Regulatory Filing", "System Integration", "Marketing Campaign", "Soft Launch", "Full Launch"],
                "tags": ["product-launch", "regulatory", "marketing", "customer-acquisition", "revenue-generating"],
                "milestones": ["Product Approved", "Systems Ready", "Marketing Launch", "First 1000 Accounts", "Profitability Target"],
                "portfolios": True,
                "portfolio_name": "Product Innovation"
            },
            {
                "name": "Fraud Detection System Upgrade",
                "description": "AI-powered fraud detection implementation",
                "custom_fields": [
                    {"name": "Implementation Phase", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Design", "Development", "Testing", "Pilot", "Production", "Optimization"]},
                    {"name": "False Positive Rate", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Detection Accuracy", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                    {"name": "System Performance", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Needs Improvement", "Meets Target", "Exceeds Target"]},
                ],
                "sections": ["Requirements", "Model Development", "Integration", "Testing", "Pilot Program", "Full Deployment"],
                "tags": ["security", "ai-ml", "fraud-prevention", "customer-protection", "risk-management"],
                "milestones": ["Model Trained", "Integration Complete", "Pilot Launch", "Production Deployment", "Performance Targets Met"],
                "portfolios": True,
                "portfolio_name": "Risk Management Systems"
            }
        ]
    },
    "retail": {
        "name": "Retail / E-commerce",
        "use_cases": [
            {
                "name": "Holiday Season Campaign",
                "description": "Black Friday and holiday season marketing campaign",
                "custom_fields": [
                    {"name": "Campaign Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Channel", "type": CUSTOM_FIELD_MULTI_ENUM,
                     "options": ["Email", "Social Media", "Paid Search", "Display Ads", "In-Store", "TV/Radio"]},
                    {"name": "ROI Target", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                    {"name": "Customer Segment", "type": CUSTOM_FIELD_ENUM,
                     "options": ["New Customers", "Returning Customers", "VIP Customers", "Lapsed Customers"]},
                    {"name": "Campaign Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Planning", "Creative Development", "Review", "Scheduled", "Live", "Complete"]},
                ],
                "sections": ["Creative Brief", "Asset Creation", "Review & Approval", "Scheduling", "Launch", "Monitor & Optimize"],
                "tags": ["marketing", "high-revenue", "time-sensitive", "customer-acquisition", "seasonal"],
                "milestones": ["Campaign Kickoff", "Assets Approved", "Launch Day", "Peak Sales Day", "Campaign Wrap-Up"],
                "portfolios": True,
                "portfolio_name": "Seasonal Marketing"
            },
            {
                "name": "Store Expansion Project",
                "description": "New retail location opening",
                "custom_fields": [
                    {"name": "Store Number", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Square Footage", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Investment Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Opening Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Site Selection", "Lease Negotiation", "Build-Out", "Staffing", "Pre-Opening", "Open"]},
                    {"name": "Revenue Target", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                ],
                "sections": ["Site Selection", "Lease & Permits", "Construction", "Merchandising", "Staffing & Training", "Grand Opening"],
                "tags": ["expansion", "real-estate", "capital-project", "new-location", "hiring"],
                "milestones": ["Site Secured", "Construction Start", "Hiring Complete", "Soft Opening", "Grand Opening"],
                "portfolios": True,
                "portfolio_name": "Store Network Expansion"
            },
            {
                "name": "Inventory Management System",
                "description": "New inventory and supply chain platform implementation",
                "custom_fields": [
                    {"name": "Vendor", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Integration Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "In Progress", "Testing", "Complete"]},
                    {"name": "Locations Migrated", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Accuracy Improvement", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                ],
                "sections": ["Vendor Selection", "System Configuration", "Data Migration", "Store Rollout", "Training", "Optimization"],
                "tags": ["supply-chain", "operations", "efficiency", "cost-reduction", "technology"],
                "milestones": ["Vendor Selected", "Pilot Store Live", "50% Rollout", "100% Rollout", "ROI Achieved"],
                "portfolios": True,
                "portfolio_name": "Operations Modernization"
            }
        ]
    },
    "construction": {
        "name": "Construction / Real Estate",
        "use_cases": [
            {
                "name": "Commercial Building Development",
                "description": "Multi-tenant office building construction",
                "custom_fields": [
                    {"name": "Project Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Contractor", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Permit Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Application Submitted", "Under Review", "Approved", "Expired"]},
                    {"name": "Inspection Date", "type": CUSTOM_FIELD_DATE},
                    {"name": "Construction Phase", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Pre-Construction", "Foundation", "Framing", "MEP", "Interior", "Landscaping", "Final"]},
                    {"name": "Leasing Status", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                ],
                "sections": ["Planning & Permits", "Site Preparation", "Foundation", "Structure", "Building Systems", "Interior Finish", "Occupancy"],
                "tags": ["construction", "real-estate", "permitting", "safety", "sustainability"],
                "milestones": ["Permits Approved", "Groundbreaking", "Foundation Complete", "Topping Out", "Certificate of Occupancy"],
                "portfolios": True,
                "portfolio_name": "Development Projects"
            },
            {
                "name": "Infrastructure Renovation",
                "description": "Major renovation of existing commercial property",
                "custom_fields": [
                    {"name": "Renovation Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Building System", "type": CUSTOM_FIELD_MULTI_ENUM,
                     "options": ["HVAC", "Electrical", "Plumbing", "Elevators", "Facade", "Roof"]},
                    {"name": "Tenant Impact", "type": CUSTOM_FIELD_ENUM,
                     "options": ["None", "Minimal", "Moderate", "Relocation Required"]},
                    {"name": "Energy Efficiency Gain", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                ],
                "sections": ["Assessment", "Design", "Tenant Coordination", "Demolition", "Construction", "Testing & Commissioning"],
                "tags": ["renovation", "sustainability", "energy-efficiency", "tenant-relations", "modernization"],
                "milestones": ["Design Approved", "Tenant Coordination Complete", "Construction Start", "Systems Commissioned", "Project Complete"],
                "portfolios": True,
                "portfolio_name": "Asset Management"
            }
        ]
    },
    "manufacturing": {
        "name": "Manufacturing",
        "use_cases": [
            {
                "name": "Factory Automation Initiative",
                "description": "Implementation of robotics and automation systems",
                "custom_fields": [
                    {"name": "Production Line", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Automation Phase", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Planning", "Equipment Selection", "Installation", "Testing", "Training", "Production"]},
                    {"name": "ROI Target", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                    {"name": "Safety Certification", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "In Progress", "Certified", "Needs Renewal"]},
                    {"name": "Production Increase %", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                ],
                "sections": ["Assessment", "Equipment Procurement", "Installation", "Integration", "Testing", "Training", "Go-Live"],
                "tags": ["automation", "safety-critical", "production", "roi-tracking", "workforce-training"],
                "milestones": ["Equipment Ordered", "Installation Complete", "Testing Passed", "Production Start", "Target ROI Achieved"],
                "portfolios": True,
                "portfolio_name": "Manufacturing Excellence"
            },
            {
                "name": "Quality Management System Certification",
                "description": "ISO 9001 quality management system implementation",
                "custom_fields": [
                    {"name": "ISO Standard", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Audit Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Preparation", "Internal Audit", "External Audit", "Certified", "Surveillance"]},
                    {"name": "Non-Conformances", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Process Owner", "type": CUSTOM_FIELD_TEXT},
                ],
                "sections": ["Gap Analysis", "Process Documentation", "Implementation", "Internal Audit", "Corrective Actions", "Certification Audit"],
                "tags": ["quality", "compliance", "iso-certification", "process-improvement", "audit"],
                "milestones": ["Gap Analysis Complete", "Processes Documented", "Internal Audit Passed", "Certification Achieved"],
                "portfolios": True,
                "portfolio_name": "Quality & Compliance"
            },
            {
                "name": "Supply Chain Optimization",
                "description": "End-to-end supply chain transformation and optimization",
                "custom_fields": [
                    {"name": "Supplier Tier", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Tier 1", "Tier 2", "Tier 3", "Logistics Partner"]},
                    {"name": "Lead Time Reduction", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                    {"name": "Cost Savings", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Inventory Turnover", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                ],
                "sections": ["Current State Analysis", "Supplier Evaluation", "Process Redesign", "System Implementation", "Pilot", "Rollout"],
                "tags": ["supply-chain", "cost-reduction", "logistics", "supplier-management", "inventory"],
                "milestones": ["Baseline Established", "Suppliers Onboarded", "Pilot Complete", "Full Rollout", "Savings Target Met"],
                "portfolios": True,
                "portfolio_name": "Supply Chain Transformation"
            }
        ]
    },
    "education": {
        "name": "Education",
        "use_cases": [
            {
                "name": "Learning Management System Rollout",
                "description": "New LMS platform implementation across campus",
                "custom_fields": [
                    {"name": "Department", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Faculty Training", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "Scheduled", "In Progress", "Completed"]},
                    {"name": "Course Migration %", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Student Adoption %", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Platform", "type": CUSTOM_FIELD_TEXT},
                ],
                "sections": ["Platform Selection", "Pilot Program", "Faculty Training", "Course Migration", "Student Onboarding", "Full Deployment"],
                "tags": ["edtech", "training", "digital-learning", "faculty-support", "student-success"],
                "milestones": ["Platform Selected", "Pilot Successful", "Faculty Trained", "Semester Launch", "Full Adoption"],
                "portfolios": True,
                "portfolio_name": "Digital Learning Initiative"
            },
            {
                "name": "Campus Facilities Expansion",
                "description": "New academic building and student center construction",
                "custom_fields": [
                    {"name": "Building Type", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Academic", "Residential", "Athletic", "Administrative", "Student Center"]},
                    {"name": "Construction Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Capacity (Students)", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "LEED Certification", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Pursuing", "Silver", "Gold", "Platinum"]},
                ],
                "sections": ["Planning & Fundraising", "Design", "Permitting", "Construction", "Furnishing", "Opening"],
                "tags": ["construction", "capital-project", "fundraising", "sustainability", "campus-improvement"],
                "milestones": ["Funding Secured", "Design Approved", "Groundbreaking", "Construction Complete", "Grand Opening"],
                "portfolios": True,
                "portfolio_name": "Campus Development"
            },
            {
                "name": "Accreditation Preparation",
                "description": "Regional accreditation review and self-study",
                "custom_fields": [
                    {"name": "Standard Number", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Evidence Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "Collecting", "Review", "Complete"]},
                    {"name": "Committee", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Site Visit Date", "type": CUSTOM_FIELD_DATE},
                ],
                "sections": ["Self-Study Planning", "Evidence Collection", "Report Writing", "Review & Revision", "Site Visit Prep", "Site Visit"],
                "tags": ["accreditation", "compliance", "assessment", "quality-assurance", "institutional-effectiveness"],
                "milestones": ["Self-Study Started", "Draft Complete", "Internal Review", "Report Submitted", "Site Visit Complete"],
                "portfolios": True,
                "portfolio_name": "Accreditation & Quality"
            }
        ]
    },
    "government": {
        "name": "Government / Public Sector",
        "use_cases": [
            {
                "name": "Digital Services Transformation",
                "description": "Modernization of citizen-facing digital services",
                "custom_fields": [
                    {"name": "Service Category", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Permits", "Benefits", "Licensing", "Payments", "Information"]},
                    {"name": "Accessibility Compliance", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "In Progress", "WCAG 2.1 AA", "WCAG 2.1 AAA"]},
                    {"name": "User Satisfaction", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                    {"name": "Transaction Volume", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                ],
                "sections": ["Discovery", "User Research", "Design", "Development", "Testing", "Launch", "Continuous Improvement"],
                "tags": ["digital-services", "citizen-experience", "accessibility", "agile", "user-centered-design"],
                "milestones": ["User Research Complete", "Beta Launch", "Public Launch", "Migration Complete", "Decommission Legacy"],
                "portfolios": True,
                "portfolio_name": "Digital Transformation"
            },
            {
                "name": "Infrastructure Improvement Project",
                "description": "Public infrastructure repair and modernization",
                "custom_fields": [
                    {"name": "Asset Type", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Roads", "Bridges", "Water", "Sewer", "Parks", "Buildings"]},
                    {"name": "Federal Funding", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Community Impact", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Low", "Moderate", "High", "Critical"]},
                    {"name": "Completion Date", "type": CUSTOM_FIELD_DATE},
                ],
                "sections": ["Planning & Design", "Environmental Review", "Procurement", "Construction", "Inspection", "Closeout"],
                "tags": ["infrastructure", "public-works", "capital-improvement", "community-impact", "federal-funding"],
                "milestones": ["Funding Approved", "Design Complete", "Contract Awarded", "Construction Start", "Project Complete"],
                "portfolios": True,
                "portfolio_name": "Capital Improvements"
            },
            {
                "name": "Emergency Response System Upgrade",
                "description": "911 dispatch and emergency response modernization",
                "custom_fields": [
                    {"name": "System Component", "type": CUSTOM_FIELD_ENUM,
                     "options": ["CAD", "Radio", "Mapping", "Mobile", "Records", "Integration"]},
                    {"name": "Agency", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Police", "Fire", "EMS", "Dispatch", "Multi-Agency"]},
                    {"name": "Response Time Target", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                    {"name": "Training Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "In Progress", "Certified", "Refresher Needed"]},
                ],
                "sections": ["Needs Assessment", "Vendor Selection", "Installation", "Integration", "Training", "Go-Live", "Optimization"],
                "tags": ["public-safety", "emergency-services", "mission-critical", "training", "interoperability"],
                "milestones": ["Requirements Finalized", "Vendor Selected", "System Installed", "Training Complete", "Cutover Complete"],
                "portfolios": True,
                "portfolio_name": "Public Safety Modernization"
            }
        ]
    },
    "energy": {
        "name": "Energy / Utilities",
        "use_cases": [
            {
                "name": "Smart Grid Implementation",
                "description": "Smart meter and grid modernization deployment",
                "custom_fields": [
                    {"name": "Service Territory", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Meters Deployed", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Grid Reliability %", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Outage Reduction", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                    {"name": "Deployment Phase", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Planning", "Pilot", "Rollout", "Optimization", "Complete"]},
                ],
                "sections": ["Planning", "Procurement", "Pilot Program", "Full Deployment", "Customer Education", "Optimization"],
                "tags": ["smart-grid", "modernization", "reliability", "customer-service", "iot"],
                "milestones": ["Pilot Complete", "50% Deployment", "Full Deployment", "Customer Portal Live", "ROI Achieved"],
                "portfolios": True,
                "portfolio_name": "Grid Modernization"
            },
            {
                "name": "Renewable Energy Integration",
                "description": "Solar and wind energy facility development",
                "custom_fields": [
                    {"name": "Energy Source", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Solar", "Wind", "Hydro", "Battery Storage", "Hybrid"]},
                    {"name": "Capacity (MW)", "type": CUSTOM_FIELD_NUMBER, "precision": 1},
                    {"name": "Regulatory Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Application", "Under Review", "Approved", "Conditional", "Operating"]},
                    {"name": "Carbon Offset (tons)", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                ],
                "sections": ["Site Selection", "Environmental Review", "Engineering", "Permitting", "Construction", "Commissioning"],
                "tags": ["renewable-energy", "sustainability", "regulatory", "environmental", "clean-energy"],
                "milestones": ["Site Secured", "Permits Approved", "Construction Start", "Grid Connection", "Commercial Operation"],
                "portfolios": True,
                "portfolio_name": "Renewable Energy Portfolio"
            },
            {
                "name": "Pipeline Integrity Management",
                "description": "Natural gas pipeline inspection and maintenance program",
                "custom_fields": [
                    {"name": "Pipeline Segment", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Inspection Method", "type": CUSTOM_FIELD_ENUM,
                     "options": ["In-Line Inspection", "Direct Assessment", "Pressure Testing", "Visual"]},
                    {"name": "Risk Level", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Low", "Medium", "High", "Critical"]},
                    {"name": "Last Inspection", "type": CUSTOM_FIELD_DATE},
                    {"name": "Integrity Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Good", "Monitor", "Repair Required", "Replace Required"]},
                ],
                "sections": ["Planning", "Inspection", "Analysis", "Remediation", "Verification", "Documentation"],
                "tags": ["safety", "compliance", "asset-management", "regulatory", "maintenance"],
                "milestones": ["Inspection Complete", "Analysis Complete", "Repairs Completed", "Verification Passed", "Regulatory Filing"],
                "portfolios": True,
                "portfolio_name": "Asset Integrity"
            }
        ]
    },
    "media": {
        "name": "Media / Entertainment",
        "use_cases": [
            {
                "name": "Content Production Campaign",
                "description": "Multi-platform content series production and launch",
                "custom_fields": [
                    {"name": "Content Type", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Series", "Film", "Documentary", "Digital", "Podcast", "Live Event"]},
                    {"name": "Production Stage", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Development", "Pre-Production", "Production", "Post-Production", "Distribution"]},
                    {"name": "Platform", "type": CUSTOM_FIELD_MULTI_ENUM,
                     "options": ["Streaming", "Broadcast", "Theatrical", "Social Media", "Podcast", "YouTube"]},
                    {"name": "Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Release Date", "type": CUSTOM_FIELD_DATE},
                ],
                "sections": ["Development", "Pre-Production", "Principal Photography", "Post-Production", "Marketing", "Distribution"],
                "tags": ["production", "creative", "multi-platform", "marketing", "premiere"],
                "milestones": ["Greenlight", "Production Start", "Wrap", "Picture Lock", "Launch"],
                "portfolios": True,
                "portfolio_name": "Content Pipeline"
            },
            {
                "name": "Streaming Platform Launch",
                "description": "New streaming service platform and content library",
                "custom_fields": [
                    {"name": "Platform Feature", "type": CUSTOM_FIELD_MULTI_ENUM,
                     "options": ["VOD", "Live", "Download", "4K", "Profiles", "Recommendations"]},
                    {"name": "Content Hours", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Subscriber Target", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Launch Market", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Platform Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Development", "Beta", "Soft Launch", "Public Launch", "Growth"]},
                ],
                "sections": ["Platform Development", "Content Acquisition", "Beta Testing", "Marketing Campaign", "Launch", "Growth"],
                "tags": ["streaming", "platform", "content-licensing", "subscriber-growth", "technology"],
                "milestones": ["Platform Beta", "Content Library Target", "Beta Launch", "Public Launch", "Subscriber Goal"],
                "portfolios": True,
                "portfolio_name": "Digital Platforms"
            },
            {
                "name": "Live Event Production",
                "description": "Major live broadcast event planning and execution",
                "custom_fields": [
                    {"name": "Event Type", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Awards Show", "Sports", "Concert", "News Special", "Reality", "Variety"]},
                    {"name": "Venue", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Expected Viewers", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Broadcast Networks", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Rehearsal Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "Tech Rehearsal", "Dress Rehearsal", "Ready"]},
                ],
                "sections": ["Planning", "Venue & Logistics", "Technical Setup", "Rehearsals", "Live Broadcast", "Wrap & Archive"],
                "tags": ["live-production", "broadcast", "event", "technical", "high-profile"],
                "milestones": ["Venue Secured", "Technical Design Complete", "Rehearsals Complete", "Live Broadcast", "Post-Event"],
                "portfolios": True,
                "portfolio_name": "Live Events"
            }
        ]
    },
    "travel": {
        "name": "Travel / Hospitality",
        "use_cases": [
            {
                "name": "Airport Expansion Project",
                "description": "Major airport terminal and runway expansion",
                "custom_fields": [
                    {"name": "Project Budget", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Regulatory Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Pending", "FAA Review", "Approved", "Conditional Approval", "Delayed"]},
                    {"name": "FAA Compliance", "type": CUSTOM_FIELD_MULTI_ENUM,
                     "options": ["Environmental Review", "Safety Standards", "Noise Compliance", "Airspace Analysis"]},
                    {"name": "Launch Date", "type": CUSTOM_FIELD_DATE},
                    {"name": "Project Phase", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Planning", "Design", "Permits", "Construction", "Testing", "Operational"]},
                    {"name": "Passenger Capacity Increase", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                ],
                "sections": ["Pre-Planning", "Environmental & Permits", "Design", "Construction", "Systems Testing", "Operational Readiness"],
                "tags": ["safety-critical", "noise-compliance", "environmental-review", "infrastructure", "multi-year"],
                "milestones": ["Groundbreaking", "Runway Complete", "Terminal Structure Complete", "First Flight", "Grand Opening"],
                "portfolios": True,
                "portfolio_name": "Infrastructure Development"
            },
            {
                "name": "Fleet Modernization Program",
                "description": "Airline fleet upgrade and aircraft acquisition",
                "custom_fields": [
                    {"name": "Aircraft Type", "type": CUSTOM_FIELD_TEXT},
                    {"name": "Delivery Date", "type": CUSTOM_FIELD_DATE},
                    {"name": "Aircraft Cost", "type": CUSTOM_FIELD_NUMBER, "precision": 2},
                    {"name": "Training Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Not Started", "Pilot Training", "Crew Training", "Maintenance Training", "Complete"]},
                    {"name": "Certification Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Pending", "In Progress", "Approved", "Conditional"]},
                ],
                "sections": ["Aircraft Selection", "Procurement", "Certification", "Crew Training", "Maintenance Setup", "Entry Into Service"],
                "tags": ["fleet", "safety", "training", "regulatory", "capital-investment"],
                "milestones": ["Aircraft Order", "First Delivery", "Crew Certified", "First Revenue Flight", "Fleet Complete"],
                "portfolios": True,
                "portfolio_name": "Fleet Strategy"
            },
            {
                "name": "Hotel Property Opening",
                "description": "New hotel location launch",
                "custom_fields": [
                    {"name": "Property Type", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Full Service", "Limited Service", "Extended Stay", "Resort", "Boutique"]},
                    {"name": "Room Count", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Opening Date", "type": CUSTOM_FIELD_DATE},
                    {"name": "Hiring Progress", "type": CUSTOM_FIELD_NUMBER, "precision": 0},
                    {"name": "Pre-Opening Status", "type": CUSTOM_FIELD_ENUM,
                     "options": ["Planning", "Construction", "Furnishing", "Staffing", "Training", "Soft Opening", "Grand Opening"]},
                ],
                "sections": ["Development", "Construction", "FF&E Installation", "Hiring & Training", "Soft Opening", "Grand Opening"],
                "tags": ["hospitality", "real-estate", "staffing", "customer-experience", "brand-standards"],
                "milestones": ["Construction Complete", "Hiring Complete", "Soft Opening", "Grand Opening", "Full Occupancy"],
                "portfolios": True,
                "portfolio_name": "Property Development"
            }
        ]
    }
}


def get_industry_template(industry: str) -> Dict[str, Any]:
    """
    Get template for a specific industry.

    Args:
        industry: Industry key (e.g., 'healthcare', 'technology')

    Returns:
        Industry template dictionary
    """
    return INDUSTRY_TEMPLATES.get(industry.lower(), {})


def get_use_case(industry: str, use_case_name: str) -> Dict[str, Any]:
    """
    Get specific use case for an industry.

    Args:
        industry: Industry key
        use_case_name: Name of the use case

    Returns:
        Use case dictionary or None
    """
    template = get_industry_template(industry)
    if template and 'use_cases' in template:
        for uc in template['use_cases']:
            if uc['name'] == use_case_name:
                return uc
    return None


def get_all_use_cases(industry: str) -> List[Dict[str, Any]]:
    """
    Get all use cases for an industry.

    Args:
        industry: Industry key

    Returns:
        List of use case dictionaries
    """
    template = get_industry_template(industry)
    return template.get('use_cases', [])


def get_default_use_case(industry: str) -> Dict[str, Any]:
    """
    Get the first/default use case for an industry.

    Args:
        industry: Industry key

    Returns:
        First use case dictionary or empty dict
    """
    use_cases = get_all_use_cases(industry)
    return use_cases[0] if use_cases else {}


def get_random_use_case(industry: str) -> Dict[str, Any]:
    """
    Get a random use case for an industry.

    Args:
        industry: Industry key

    Returns:
        Random use case dictionary or None
    """
    import random
    use_cases = get_all_use_cases(industry)
    return random.choice(use_cases) if use_cases else None


def get_all_industries() -> List[str]:
    """Get list of all available industries."""
    return list(INDUSTRY_TEMPLATES.keys())


# Example usage
if __name__ == "__main__":
    # List all industries
    print("Available industries:")
    for industry in get_all_industries():
        template = get_industry_template(industry)
        print(f"  - {template['name']}: {len(template['use_cases'])} use cases")

    # Show healthcare use cases
    print("\nHealthcare use cases:")
    for uc in get_all_use_cases('healthcare'):
        print(f"  - {uc['name']}")
        print(f"    Custom Fields: {len(uc['custom_fields'])}")
        print(f"    Sections: {', '.join(uc['sections'])}")
        print(f"    Tags: {', '.join(uc['tags'][:3])}...")
