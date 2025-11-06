#!/usr/bin/env python3
"""
Prospect Context Analyzer for Mimic SaaS Platform.
Analyzes prospect information and provides platform-specific recommendations
for data generation configuration.
"""

import anthropic
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime


class ProspectContextAnalyzer:
    """
    Analyzes prospect context using Claude API and generates platform-specific
    recommendations for synthetic data generation.
    """

    # Company size display names
    COMPANY_SIZE_LABELS = {
        "smb": "SMB (1-1,000 employees)",
        "mid_market": "Mid-Market (1,001-5,000 employees)",
        "enterprise": "Enterprise (5,001-10,000 employees)",
        "strategic": "Strategic Enterprise (10,000+ employees)"
    }

    # Platform-specific prompts for context extraction
    PLATFORM_EXTRACTION_PROMPTS = {
        "asana": """You are analyzing prospect information for an Asana workspace data generation tool.

Extract the following structured information from the prospect context:

UNIVERSAL ATTRIBUTES:
- Industry/sector (healthcare, finance, technology, retail, manufacturing, etc.)
- Company size: IMPORTANT - Use these exact employee count thresholds:
  * "smb" if employees 1-1000 (Small and Medium Business)
  * "mid_market" if employees 1001-5000
  * "enterprise" if employees 5001-10000
  * "strategic" if employees > 10000 (Strategic Enterprise)
- Revenue size (if mentioned)
- Organizational complexity (simple, moderate, complex)

ASANA-SPECIFIC ATTRIBUTES:
- Project management maturity (basic, intermediate, advanced)
- Team collaboration patterns (siloed, cross-functional, matrix)
- Workflow complexity (simple, moderate, complex)
- Cross-functional needs (low, medium, high)
- Typical project types (e.g., product development, marketing campaigns, operations)
- Portfolio management needs (yes/no)
- Custom field requirements (low, medium, high)

Return ONLY valid JSON with this exact structure (no additional text):
{
    "industry": "string",
    "company_size": "smb|mid_market|enterprise|strategic",
    "revenue_size": "string or null",
    "org_complexity": "simple|moderate|complex",
    "pm_maturity": "basic|intermediate|advanced",
    "collaboration_pattern": "siloed|cross-functional|matrix",
    "workflow_complexity": "simple|moderate|complex",
    "cross_functional_needs": "low|medium|high",
    "project_types": ["string"],
    "portfolio_needs": "yes|no",
    "custom_field_needs": "low|medium|high",
    "key_insights": ["string"]
}""",

        "salesforce": """You are analyzing prospect information for a Salesforce CRM data generation tool.

Extract the following structured information from the prospect context:

UNIVERSAL ATTRIBUTES:
- Industry/sector (healthcare, finance, technology, retail, manufacturing, etc.)
- Company size: IMPORTANT - Use these exact employee count thresholds:
  * "smb" if employees 1-1000 (Small and Medium Business)
  * "mid_market" if employees 1001-5000
  * "enterprise" if employees 5001-10000
  * "strategic" if employees > 10000 (Strategic Enterprise)
- Revenue size (if mentioned)
- Organizational complexity (simple, moderate, complex)

SALESFORCE-SPECIFIC ATTRIBUTES:
- Sales process complexity (simple, moderate, complex)
- Average deal sizes (small: <$10K, medium: $10K-$100K, large: $100K-$1M, enterprise: $1M+)
- Sales cycle length (short: <30 days, medium: 30-90 days, long: 90+ days)
- Account structures (simple, hierarchical, complex)
- Opportunity management needs (basic, standard, advanced)
- Territory management (yes/no)
- Support case volume (low, medium, high)
- Sales motion (new_business, expansion, balanced)

Return ONLY valid JSON with this exact structure (no additional text):
{
    "industry": "string",
    "company_size": "smb|mid_market|enterprise|strategic",
    "revenue_size": "string or null",
    "org_complexity": "simple|moderate|complex",
    "sales_complexity": "simple|moderate|complex",
    "deal_sizes": "small|medium|large|enterprise",
    "sales_cycle": "short|medium|long",
    "account_structure": "simple|hierarchical|complex",
    "opp_management": "basic|standard|advanced",
    "territory_mgmt": "yes|no",
    "case_volume": "low|medium|high",
    "sales_motion": "new_business|expansion|balanced",
    "key_insights": ["string"]
}""",

        "okta": """You are analyzing prospect information for an Okta identity management data generation tool.

Extract the following structured information from the prospect context:

UNIVERSAL ATTRIBUTES:
- Industry/sector (healthcare, finance, technology, retail, manufacturing, etc.)
- Company size: IMPORTANT - Use these exact employee count thresholds:
  * "smb" if employees 1-1000 (Small and Medium Business)
  * "mid_market" if employees 1001-5000
  * "enterprise" if employees 5001-10000
  * "strategic" if employees > 10000 (Strategic Enterprise)
- Revenue size (if mentioned)
- Organizational complexity (simple, moderate, complex)

OKTA-SPECIFIC ATTRIBUTES:
- Identity management maturity (basic, intermediate, advanced)
- User provisioning needs (simple, moderate, complex)
- Application count (few: <10, moderate: 10-50, many: 50+)
- Security requirements (standard, elevated, high-security)
- Compliance requirements (basic, moderate, strict)
- Multi-location (yes/no)
- Department structure (flat, moderate, complex)

Return ONLY valid JSON with this exact structure (no additional text):
{
    "industry": "string",
    "company_size": "smb|mid_market|enterprise|strategic",
    "revenue_size": "string or null",
    "org_complexity": "simple|moderate|complex",
    "identity_maturity": "basic|intermediate|advanced",
    "provisioning_needs": "simple|moderate|complex",
    "app_count": "few|moderate|many",
    "security_requirements": "standard|elevated|high-security",
    "compliance_reqs": "basic|moderate|strict",
    "multi_location": "yes|no",
    "dept_structure": "flat|moderate|complex",
    "key_insights": ["string"]
}"""
    }

    def __init__(self, api_key: str):
        """
        Initialize the analyzer with Anthropic API key.

        Args:
            api_key: Anthropic API key for Claude
        """
        self.api_key = api_key
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"  # Claude 3 Haiku - fast and cost effective

    def analyze_prospect_context(
        self,
        prospect_text: str,
        platform: str,
        connection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze prospect context and extract structured data.

        Args:
            prospect_text: Free-form text about the prospect
            platform: Platform type (asana, salesforce, okta)
            connection_name: Optional connection name for additional context

        Returns:
            Dictionary with extracted structured data
        """
        if not prospect_text or not prospect_text.strip():
            return self._get_default_context(platform)

        platform = platform.lower()
        if platform not in self.PLATFORM_EXTRACTION_PROMPTS:
            raise ValueError(f"Unsupported platform: {platform}")

        extraction_prompt = self.PLATFORM_EXTRACTION_PROMPTS[platform]

        # Build the full prompt
        full_prompt = f"""{extraction_prompt}

PROSPECT CONTEXT:
{prospect_text}

{f'CONNECTION NAME: {connection_name}' if connection_name else ''}

Analyze the above prospect context and extract the structured information.
Be intelligent about inferring details even if not explicitly stated.
For example, if they mention "Fortune 500 company", infer enterprise size and high complexity.
If information is missing, use reasonable defaults based on what is provided.

Return ONLY the JSON object, no additional text or explanation."""

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,  # Lower temperature for more consistent extraction
                messages=[{"role": "user", "content": full_prompt}]
            )

            response_text = message.content[0].text.strip()
            print(f"Claude response: {response_text}")

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                extracted_data = json.loads(json_match.group())
                print(f"Extracted data: {json.dumps(extracted_data, indent=2)}")

                # Add metadata
                extracted_data["platform"] = platform
                extracted_data["raw_text"] = prospect_text
                extracted_data["analyzed_at"] = datetime.now().isoformat()
                extracted_data["connection_name"] = connection_name

                # Add display label for company size
                company_size = extracted_data.get("company_size", "smb")
                extracted_data["company_size_label"] = self.COMPANY_SIZE_LABELS.get(
                    company_size,
                    company_size.replace("_", " ").title()
                )

                return extracted_data
            else:
                print(f"Failed to extract JSON from response: {response_text}")
                return self._get_default_context(platform)

        except Exception as e:
            print(f"Error analyzing prospect context: {e}")
            print(f"Error type: {type(e).__name__}")
            if hasattr(e, 'response'):
                print(f"API Response: {e.response}")
            import traceback
            traceback.print_exc()
            return self._get_default_context(platform)

    def _get_default_context(self, platform: str) -> Dict[str, Any]:
        """
        Get default context when analysis fails or no input provided.

        Args:
            platform: Platform type

        Returns:
            Default context dictionary
        """
        base_defaults = {
            "industry": "technology",
            "company_size": "smb",
            "revenue_size": None,
            "org_complexity": "moderate",
            "key_insights": ["Using default settings"],
            "platform": platform,
            "raw_text": "",
            "analyzed_at": datetime.now().isoformat()
        }

        platform_defaults = {
            "asana": {
                "pm_maturity": "intermediate",
                "collaboration_pattern": "cross-functional",
                "workflow_complexity": "moderate",
                "cross_functional_needs": "medium",
                "project_types": ["product_development"],
                "portfolio_needs": "no",
                "custom_field_needs": "medium"
            },
            "salesforce": {
                "sales_complexity": "moderate",
                "deal_sizes": "medium",
                "sales_cycle": "medium",
                "account_structure": "simple",
                "opp_management": "standard",
                "territory_mgmt": "no",
                "case_volume": "medium",
                "sales_motion": "balanced"
            },
            "okta": {
                "identity_maturity": "intermediate",
                "provisioning_needs": "moderate",
                "app_count": "moderate",
                "security_requirements": "standard",
                "compliance_reqs": "moderate",
                "multi_location": "no",
                "dept_structure": "moderate"
            }
        }

        platform_specific = platform_defaults.get(platform, {})
        return {**base_defaults, **platform_specific}

    def generate_recommendations(
        self,
        extracted_context: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """
        Generate platform-specific configuration recommendations based on extracted context.

        Args:
            extracted_context: Extracted prospect context data
            platform: Platform type

        Returns:
            Dictionary with recommended configuration settings
        """
        platform = platform.lower()

        if platform == "asana":
            return self._generate_asana_recommendations(extracted_context)
        elif platform == "salesforce":
            return self._generate_salesforce_recommendations(extracted_context)
        elif platform == "okta":
            return self._generate_okta_recommendations(extracted_context)
        else:
            return {}

    def _generate_asana_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Asana-specific recommendations."""
        recommendations = {
            "industry": context.get("industry", "technology"),
            "org_size": context.get("company_size", "midsize"),
            "reasoning": []
        }

        # Determine data volume based on company size and complexity
        company_size = context.get("company_size", "smb")
        org_complexity = context.get("org_complexity", "moderate")

        # Size-based recommendations
        if company_size == "smb":
            recommendations["data_volume"] = "light"
            recommendations["initial_projects"] = 3
            recommendations["reasoning"].append("SMB (1-1000 employees) → lightweight project setup")
        elif company_size == "mid_market":
            recommendations["data_volume"] = "medium"
            recommendations["initial_projects"] = 5
            recommendations["reasoning"].append("Mid-Market (1001-5000 employees) → balanced portfolio")
        elif company_size == "enterprise":
            recommendations["data_volume"] = "heavy"
            recommendations["initial_projects"] = 7
            recommendations["reasoning"].append("Enterprise (5001-10000 employees) → extensive projects")
        elif company_size == "strategic":
            recommendations["data_volume"] = "heavy"
            recommendations["initial_projects"] = 10
            recommendations["reasoning"].append("Strategic Enterprise (10000+ employees) → complex portfolio")
        else:
            recommendations["data_volume"] = "medium"
            recommendations["initial_projects"] = 3

        # Complexity can override volume
        if org_complexity == "complex":
            if recommendations["data_volume"] == "light":
                recommendations["data_volume"] = "medium"
            recommendations["reasoning"].append("Complex organization → increased data needs")

        # Activity level based on PM maturity and collaboration pattern
        pm_maturity = context.get("pm_maturity", "intermediate")
        collaboration = context.get("collaboration_pattern", "cross-functional")

        if pm_maturity == "advanced" or collaboration == "matrix":
            recommendations["activity_level"] = "high"
            recommendations["reasoning"].append("Advanced PM maturity/matrix structure → high activity level")
        elif pm_maturity == "basic" or collaboration == "siloed":
            recommendations["activity_level"] = "low"
            recommendations["reasoning"].append("Basic PM maturity/siloed teams → lower activity level")
        else:
            recommendations["activity_level"] = "medium"
            recommendations["reasoning"].append("Intermediate PM maturity → medium activity level")

        # Comment frequency based on collaboration
        if collaboration == "matrix" or context.get("cross_functional_needs") == "high":
            recommendations["comment_frequency"] = 0.8
            recommendations["reasoning"].append("High collaboration needs → more frequent comments")
        elif collaboration == "siloed":
            recommendations["comment_frequency"] = 0.3
            recommendations["reasoning"].append("Siloed teams → less frequent comments")
        else:
            recommendations["comment_frequency"] = 0.5

        # Project frequency based on workflow complexity
        workflow_complexity = context.get("workflow_complexity", "moderate")
        if workflow_complexity == "complex":
            recommendations["project_frequency"] = 7  # New project every week
            recommendations["reasoning"].append("Complex workflows → more frequent new projects")
        elif workflow_complexity == "simple":
            recommendations["project_frequency"] = 21  # Every 3 weeks
            recommendations["reasoning"].append("Simple workflows → less frequent new projects")
        else:
            recommendations["project_frequency"] = 14  # Every 2 weeks

        return recommendations

    def _generate_salesforce_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Salesforce-specific recommendations."""
        recommendations = {
            "industry": context.get("industry", "technology"),
            "org_size": context.get("company_size", "midsize"),
            "reasoning": []
        }

        # Data volume based on company size
        company_size = context.get("company_size", "smb")
        if company_size == "smb":
            recommendations["data_volume"] = "light"
            recommendations["initial_accounts"] = 50
            recommendations["reasoning"].append("SMB (1-1000 employees) → moderate account base")
        elif company_size == "mid_market":
            recommendations["data_volume"] = "medium"
            recommendations["initial_accounts"] = 150
            recommendations["reasoning"].append("Mid-Market (1001-5000 employees) → substantial accounts")
        elif company_size == "enterprise":
            recommendations["data_volume"] = "heavy"
            recommendations["initial_accounts"] = 300
            recommendations["reasoning"].append("Enterprise (5001-10000 employees) → large account portfolio")
        elif company_size == "strategic":
            recommendations["data_volume"] = "heavy"
            recommendations["initial_accounts"] = 500
            recommendations["reasoning"].append("Strategic Enterprise (10000+ employees) → extensive accounts")
        else:
            recommendations["data_volume"] = "medium"
            recommendations["initial_accounts"] = 50

        # Sales focus based on sales motion
        sales_motion = context.get("sales_motion", "balanced")
        recommendations["sales_focus"] = sales_motion
        if sales_motion == "new_business":
            recommendations["reasoning"].append("New business focus → prioritize lead and opportunity generation")
        elif sales_motion == "expansion":
            recommendations["reasoning"].append("Expansion focus → prioritize existing account upsells")
        else:
            recommendations["reasoning"].append("Balanced approach → mix of new and expansion opportunities")

        # Activity level based on sales complexity and cycle
        sales_complexity = context.get("sales_complexity", "moderate")
        sales_cycle = context.get("sales_cycle", "medium")

        if sales_complexity == "complex" or sales_cycle == "long":
            recommendations["activity_level"] = "medium"
            recommendations["reasoning"].append("Complex/long sales cycle → moderate activity with detailed tracking")
        elif sales_complexity == "simple" or sales_cycle == "short":
            recommendations["activity_level"] = "high"
            recommendations["reasoning"].append("Simple/short sales cycle → high velocity activity")
        else:
            recommendations["activity_level"] = "medium"

        # Case volume based on extracted context
        case_volume = context.get("case_volume", "medium")
        recommendations["case_volume"] = case_volume
        if case_volume == "high":
            recommendations["reasoning"].append("High support volume → generate many support cases")
        elif case_volume == "low":
            recommendations["reasoning"].append("Low support volume → minimal case generation")

        return recommendations

    def _generate_okta_recommendations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Okta-specific recommendations."""
        recommendations = {
            "industry": context.get("industry", "technology"),
            "org_size": context.get("company_size", "midsize"),
            "reasoning": []
        }

        # User volume based on company size
        company_size = context.get("company_size", "smb")
        if company_size == "smb":
            recommendations["data_volume"] = "light"
            recommendations["initial_users"] = 100
            recommendations["reasoning"].append("SMB (1-1000 employees) → moderate user base")
        elif company_size == "mid_market":
            recommendations["data_volume"] = "medium"
            recommendations["initial_users"] = 500
            recommendations["reasoning"].append("Mid-Market (1001-5000 employees) → substantial users")
        elif company_size == "enterprise":
            recommendations["data_volume"] = "heavy"
            recommendations["initial_users"] = 1500
            recommendations["reasoning"].append("Enterprise (5001-10000 employees) → large user base")
        elif company_size == "strategic":
            recommendations["data_volume"] = "heavy"
            recommendations["initial_users"] = 3000
            recommendations["reasoning"].append("Strategic Enterprise (10000+ employees) → extensive user base")
        else:
            recommendations["data_volume"] = "medium"
            recommendations["initial_users"] = 100

        # Activity level based on identity maturity
        identity_maturity = context.get("identity_maturity", "intermediate")
        if identity_maturity == "advanced":
            recommendations["activity_level"] = "high"
            recommendations["reasoning"].append("Advanced identity management → high activity with frequent changes")
        elif identity_maturity == "basic":
            recommendations["activity_level"] = "low"
            recommendations["reasoning"].append("Basic identity management → minimal changes")
        else:
            recommendations["activity_level"] = "medium"

        return recommendations


# Example usage and testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prospect_context_analyzer.py <ANTHROPIC_API_KEY> [prospect_text] [platform]")
        sys.exit(1)

    api_key = sys.argv[1]
    prospect_text = sys.argv[2] if len(sys.argv) > 2 else "Mid-size healthcare company, 300 employees, complex regulatory requirements"
    platform = sys.argv[3] if len(sys.argv) > 3 else "asana"

    analyzer = ProspectContextAnalyzer(api_key)

    print("=" * 80)
    print(f"Testing Prospect Context Analyzer - {platform.upper()}")
    print("=" * 80)
    print(f"\nProspect Text: {prospect_text}\n")

    # Extract context
    print("Extracting context...")
    extracted = analyzer.analyze_prospect_context(prospect_text, platform, "Demo Connection")
    print("\nExtracted Context:")
    print(json.dumps(extracted, indent=2))

    # Generate recommendations
    print("\n" + "=" * 80)
    print("Generating Recommendations...")
    print("=" * 80)
    recommendations = analyzer.generate_recommendations(extracted, platform)
    print("\nRecommendations:")
    print(json.dumps(recommendations, indent=2))
