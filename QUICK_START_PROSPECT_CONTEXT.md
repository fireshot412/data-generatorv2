# Quick Start: Prospect Context Feature

## What It Does

Automatically tailors synthetic data generation to match your prospect's profile by analyzing free-form text about their company and needs.

## How to Use (3 Easy Steps)

### Step 1: Start Creating a Job

1. Click "➕ New Job" button
2. Select your connection (Asana, Salesforce, or Okta)
3. Give your job a name

### Step 2: Add Prospect Context

In the "Prospect Context" field, describe your prospect. The placeholder will guide you based on your selected platform.

**Examples:**

**For Asana:**
```
Mid-size healthcare provider with 500 employees managing complex patient
care workflows across 3 hospital locations. Heavy regulatory compliance
requirements and need for cross-departmental collaboration.
```

**For Salesforce:**
```
Enterprise software company with 2,000 employees, selling to Fortune 500
accounts with $500K+ deal sizes and 6-9 month sales cycles. Complex
account hierarchies with strong territory management needs.
```

**For Okta:**
```
Financial services firm with 1,200 employees across 5 offices. High
security requirements, strict compliance (SOC2, HIPAA), managing 50+
SaaS applications with complex user provisioning workflows.
```

### Step 3: Get Recommendations

1. Click "✨ Analyze & Get Recommendations"
2. Wait 2-5 seconds for analysis
3. Review the recommendations:
   - **We detected**: See what the system understood about your prospect
   - **Why these settings**: Understand the reasoning behind each recommendation
4. Click "✓ Apply These Settings" to auto-populate the form
5. Adjust any fields if needed
6. Click "🚀 Start Continuous Generation"

## What Gets Recommended?

The system automatically recommends:

- ✅ **Industry theme** (healthcare, finance, technology, etc.)
- ✅ **Data volume** (light, medium, heavy)
- ✅ **Activity level** (low, medium, high)
- ✅ **Platform-specific settings**:
  - Asana: Project count, comment frequency, collaboration patterns
  - Salesforce: Account count, deal sizes, sales focus, case volume
  - Okta: User count, security requirements, application complexity

## Tips for Best Results

### Be Specific
❌ "Large company"
✅ "Enterprise manufacturing company with 5,000 employees across 12 locations"

### Include Key Details
- **Company size**: Number of employees, revenue, locations
- **Industry**: Healthcare, finance, technology, manufacturing, etc.
- **Complexity**: Simple workflows vs. complex multi-department processes
- **Key challenges**: What pain points does your prospect have?

### Platform-Specific Tips

**Asana Users - Include:**
- Team structure (siloed vs. cross-functional)
- Project types (product dev, marketing, operations)
- Collaboration needs
- Portfolio/program management requirements

**Salesforce Users - Include:**
- Deal sizes and sales cycles
- Account complexity (simple vs. hierarchical)
- Sales motion (new business vs. expansion)
- Support/service volume

**Okta Users - Include:**
- Number of applications
- Security/compliance requirements
- Multi-location setup
- Provisioning complexity

## Skipping is OK!

If you prefer to configure manually:
- Click "Skip This Step"
- Or leave the field empty
- System will use balanced defaults

## Editing After Analysis

After applying recommendations:
- ✅ All fields remain editable
- ✅ Manually adjust any settings
- ✅ Recommendations are just a starting point
- ✅ Your manual changes will be preserved

## Troubleshooting

**"Please configure your Anthropic API key in Settings first"**
→ Go to Settings and add your Anthropic API key

**Analysis seems stuck**
→ Check your internet connection
→ Verify API key is valid
→ Try again after a few seconds

**Recommendations don't match my needs**
→ Try adding more specific details
→ Or manually adjust settings after applying
→ You have full control!

## Example Workflow

1. Select "Asana - Acme Corp Workspace"
2. Name: "Q4 Product Launch Demo"
3. Prospect Context:
   ```
   Series B startup, 150 employees, building B2B SaaS product.
   Engineering team of 40 across Platform, Frontend, Backend, and Mobile.
   Running 2-week sprints with cross-functional feature teams.
   ```
4. Click "✨ Analyze & Get Recommendations"
5. System recommends:
   - Industry: Technology
   - Size: Midsize
   - Data Volume: Medium
   - Initial Projects: 3
   - Activity Level: High
   - Comment Frequency: 0.8
6. Click "✓ Apply These Settings"
7. Adjust "Initial Projects" to 4 (manual override)
8. Set Duration to "14 days"
9. Click "🚀 Start Continuous Generation"

Done! Your data generation is now tailored to match a Series B startup's realistic workflow patterns.

## Advanced: Viewing Stored Context

After creating a job:
1. Go to Jobs view
2. Click on your job
3. The prospect context is saved in job metadata
4. Useful for remembering which prospect each demo was configured for

## Need Help?

See the full documentation: `PROSPECT_CONTEXT_FEATURE.md`
