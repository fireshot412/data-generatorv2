# Prospect Context Feature - Implementation Guide

## Overview

The Prospect Context feature enhances Mimic's data generation by allowing sales engineers to input information about their prospects and receive intelligent, platform-specific recommendations for data generation configuration.

## Architecture

### Components

1. **Backend Module**: `continuous/prospect_context_analyzer.py`
   - Uses Claude Sonnet to analyze prospect information
   - Extracts structured data from free-form text
   - Generates platform-specific recommendations

2. **API Endpoint**: `/api/prospect-context/analyze`
   - Accepts prospect text, platform type, and connection info
   - Returns extracted context and recommendations

3. **Frontend UI**: Enhanced job creation modal in `dashboard.html`
   - Platform-aware input with dynamic placeholders
   - Real-time analysis with loading states
   - Beautiful recommendation display with reasoning
   - One-click application of recommendations

## User Flow

### Step-by-Step

1. **Select Platform & Connection**
   - User selects a connection (Asana, Salesforce, or Okta)
   - Prospect context placeholder updates based on platform

2. **Enter Prospect Context** (Optional but Recommended)
   - User enters free-form text about their prospect
   - Examples:
     - **Asana**: "Mid-size healthcare provider with 500 employees, managing complex patient care workflows across 3 hospital locations"
     - **Salesforce**: "Enterprise software company selling to Fortune 500 accounts with $500K+ deal sizes and 6-9 month sales cycles"
     - **Okta**: "Financial services firm with 1,200 employees. High security requirements, managing 50+ SaaS applications"

3. **Analyze Context**
   - User clicks "✨ Analyze & Get Recommendations"
   - System sends request to Claude API
   - Loading state displays during analysis

4. **Review Recommendations**
   - System displays:
     - **Detected Attributes**: Industry, company size, complexity
     - **Key Insights**: Platform-specific observations
     - **Reasoning**: Why each setting is recommended

5. **Apply or Dismiss**
   - **Apply**: Automatically populates form fields with recommendations
   - **Dismiss**: Ignore recommendations and proceed manually
   - **Skip**: Skip the prospect context step entirely

6. **Review & Create Job**
   - User can further adjust any auto-populated settings
   - Prospect context is saved with job metadata
   - Job proceeds with tailored configuration

## Platform-Specific Extraction

### Asana

**Extracted Attributes:**
- Project management maturity (basic, intermediate, advanced)
- Team collaboration patterns (siloed, cross-functional, matrix)
- Workflow complexity (simple, moderate, complex)
- Cross-functional needs (low, medium, high)
- Portfolio management needs
- Custom field requirements

**Recommendations Generated:**
- Data volume (light, medium, heavy)
- Initial project count
- Activity level
- Comment frequency
- Project creation frequency

### Salesforce

**Extracted Attributes:**
- Sales process complexity
- Average deal sizes (small, medium, large, enterprise)
- Sales cycle length (short, medium, long)
- Account structures
- Opportunity management needs
- Territory management requirements
- Support case volume

**Recommendations Generated:**
- Data volume
- Initial account count
- Sales focus (new_business, expansion, balanced)
- Activity level
- Case generation volume

### Okta

**Extracted Attributes:**
- Identity management maturity
- User provisioning needs
- Application count
- Security requirements
- Compliance requirements
- Multi-location setup
- Department structure complexity

**Recommendations Generated:**
- Data volume
- Initial user count
- Activity level
- Organization size profile

## Technical Details

### API Request Format

```json
POST /api/prospect-context/analyze
{
  "prospect_text": "Mid-size healthcare company with 300 employees...",
  "platform": "asana",
  "connection_name": "Acme Healthcare Demo",
  "anthropic_api_key": "sk-ant-..."
}
```

### API Response Format

```json
{
  "success": true,
  "extracted_context": {
    "industry": "healthcare",
    "company_size": "midsize",
    "org_complexity": "complex",
    "pm_maturity": "intermediate",
    "collaboration_pattern": "cross-functional",
    "workflow_complexity": "complex",
    "cross_functional_needs": "high",
    "project_types": ["patient_care", "compliance"],
    "portfolio_needs": "yes",
    "custom_field_needs": "high",
    "key_insights": [
      "Complex regulatory environment",
      "Multi-location coordination needs",
      "High cross-departmental collaboration"
    ],
    "platform": "asana",
    "raw_text": "Mid-size healthcare...",
    "analyzed_at": "2025-11-05T12:34:56Z"
  },
  "recommendations": {
    "industry": "healthcare",
    "org_size": "midsize",
    "data_volume": "heavy",
    "initial_projects": 5,
    "activity_level": "high",
    "comment_frequency": 0.8,
    "project_frequency": 7,
    "reasoning": [
      "Large/complex organization → more projects and heavier data volume",
      "Advanced PM maturity/matrix structure → high activity level",
      "High collaboration needs → more frequent comments",
      "Complex workflows → more frequent new projects"
    ]
  }
}
```

### Job Metadata Storage

When a job is created, prospect context is stored in the job config:

```json
{
  "job_id": "abc123",
  "config": {
    "industry": "healthcare",
    "org_size": "midsize",
    // ... other config fields
    "prospect_context": {
      "raw_text": "Mid-size healthcare company...",
      "analyzed_at": "2025-11-05T12:34:56Z",
      "extracted_context": { /* ... */ },
      "recommendations": { /* ... */ }
    }
  }
}
```

## Testing Guide

### Manual Testing Steps

1. **Test with Asana Connection**
   ```
   Prospect Context: "Startup tech company with 20 engineers building a SaaS product.
   Need to track sprint planning and feature development across 3 teams."

   Expected:
   - Industry: technology
   - Size: startup
   - Data volume: light
   - Activity level: medium-high
   ```

2. **Test with Salesforce Connection**
   ```
   Prospect Context: "Enterprise manufacturing company with 5,000 employees.
   Complex B2B sales with $1M+ deals and 12-month sales cycles.
   Selling industrial equipment to Fortune 500 accounts."

   Expected:
   - Industry: manufacturing
   - Size: enterprise
   - Deal sizes: enterprise
   - Sales cycle: long
   - Data volume: heavy
   ```

3. **Test with Okta Connection**
   ```
   Prospect Context: "Financial services firm with strict SOC2 and HIPAA compliance.
   1,200 employees across 5 offices managing 60+ cloud applications."

   Expected:
   - Industry: finance/financial_services
   - Size: midsize/enterprise
   - Security requirements: high-security
   - Compliance: strict
   - App count: many
   - Initial users: 200-500
   ```

4. **Test Skip Functionality**
   - Click "Skip This Step" button
   - Verify form proceeds with defaults
   - Verify no prospect context stored in job

5. **Test Apply Recommendations**
   - Enter prospect context and analyze
   - Click "Apply These Settings"
   - Verify form fields update correctly
   - Adjust some fields manually
   - Create job and verify config includes both recommendations and manual adjustments

### Edge Cases

1. **Empty Prospect Text**
   - Should show error: "Please enter prospect context first"

2. **No Connection Selected**
   - Should show error: "Please select a connection first"

3. **API Error Handling**
   - Invalid API key → Shows error toast
   - Network error → Shows error toast
   - Malformed response → Falls back to defaults

4. **Platform Switching**
   - Change connection from Asana to Salesforce
   - Verify placeholder text updates
   - Verify recommendation applies correct platform settings

## Code Organization

```
continuous/
  prospect_context_analyzer.py    # Main analysis module
    - ProspectContextAnalyzer class
    - Platform-specific prompts
    - Recommendation engines

api_server.py                      # API endpoint
  - /api/prospect-context/analyze

dashboard.html                     # Frontend UI
  - Prospect context input section
  - JavaScript functions:
    - updateProspectContextPlaceholder()
    - analyzeProspectContext()
    - displayRecommendations()
    - applyRecommendations()
    - dismissRecommendations()
    - skipProspectContext()
```

## Configuration

### Required

- **Anthropic API Key**: Must be configured in Settings
- **Valid Connection**: At least one platform connection must exist

### Optional

- All prospect context inputs are optional
- System uses intelligent defaults if no context provided

## Future Enhancements (Phase 2)

1. **Salesforce API Integration**
   - Auto-populate prospect context from Salesforce Account/Opportunity
   - Read company size, industry, and deal information automatically

2. **Historical Learning**
   - Store successful prospect contexts and recommendations
   - Improve recommendations based on past patterns

3. **Custom Templates**
   - Allow users to save prospect context templates
   - Quick-select common prospect types

4. **Enhanced Analytics**
   - Track which recommendations are most commonly accepted
   - Show correlation between prospect attributes and data patterns

## Troubleshooting

### Issue: Recommendations not applying

**Solution**:
- Check browser console for JavaScript errors
- Verify connection is selected
- Ensure advanced options section is expanded if modifying those fields

### Issue: Analysis fails with error

**Solution**:
- Verify Anthropic API key is valid
- Check API rate limits
- Review error message in browser console
- Verify internet connectivity

### Issue: Placeholder not updating

**Solution**:
- Ensure connection is fully selected
- Check that `updateProspectContextPlaceholder()` is called
- Verify connection has valid vendor field

## Security Considerations

1. **API Key Handling**
   - API keys sent securely via HTTPS
   - Not logged or stored in prospect context

2. **Data Privacy**
   - Prospect text stored only in job metadata
   - Can be deleted by deleting the job
   - No external sharing of prospect information

3. **Input Validation**
   - All inputs sanitized before display
   - HTML escaping in recommendation display
   - No code execution from user input

## Performance

- **Analysis Time**: Typically 2-5 seconds (Claude API call)
- **Token Usage**: ~500-1000 tokens per analysis (Sonnet model)
- **Caching**: No caching implemented (each analysis is fresh)

## Compatibility

- **Browsers**: Chrome, Firefox, Safari, Edge (modern versions)
- **Platforms**: Asana, Salesforce, Okta
- **Python**: 3.8+
- **Dependencies**: anthropic>=0.18.0

## Support

For issues or questions:
1. Check browser console for errors
2. Review server logs for API errors
3. Verify Anthropic API key and quota
4. Check network connectivity

## License

This feature is part of the Mimic SaaS platform.
