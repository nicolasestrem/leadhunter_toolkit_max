# Client Day-1 Playbook

## Overview

This playbook describes how to run a complete lead → outreach → audit cycle using the Lead Hunter Toolkit Consulting Pack.

**Timeline**: 2-4 hours for complete client package
**Output**: Dossier + Audit + 3 Outreach Drafts + Quick Wins Deck

---

## Phase 1: Discovery & Research (30-60 mins)

### Step 1: Initial Lead Capture

**Input**: Client domain or search query

**Actions**:
1. Run search/crawl to discover leads
   ```python
   # Via CLI or Streamlit Hunt tab
   python -c "from search import ddg_sites; print(ddg_sites('restaurants berlin mitte', max=10))"
   ```

2. Review discovered leads
3. Select target client

**Output**: Lead record with contact info

### Step 2: Lead Classification & Scoring

**Actions**:
1. Extract contacts from crawled pages
2. Run LLM classification
   ```python
   from leads.classify_score import classify_and_score_lead
   from llm.adapter import LLMAdapter

   adapter = LLMAdapter.from_config(config)
   lead_record = classify_and_score_lead(lead, adapter, content_sample, use_llm=True)
   ```

3. Review scores:
   - Quality: Data completeness
   - Fit: SMB target match
   - Priority: Overall ranking

**Output**: LeadRecord with multi-dimensional scores

### Step 3: Build Dossier

**Actions**:
1. Aggregate crawled pages (home, about, contact, services)
2. Run dossier generation
   ```python
   from dossier.build import build_dossier

   dossier = build_dossier(
       lead_data=lead_record.dict(),
       pages=[{'url': ..., 'content': ...}],
       llm_adapter=adapter,
       output_dir=Path('out/client_name/dossiers')
   )
   ```

3. Review dossier sections:
   - Company overview
   - Services/products
   - Digital presence analysis
   - Signals (positive/growth/pain)
   - Issues detected
   - 48h quick wins

**Output**: Markdown dossier + sources.json

---

## Phase 2: Audit & Analysis (45-90 mins)

### Step 4: Run Onboarding Audit

**Actions**:
1. Use onboarding wizard to crawl + audit site
   ```python
   from onboarding.wizard import run_onboarding

   result = await run_onboarding(
       domain='client-site.com',
       llm_adapter=adapter,
       max_crawl_pages=10,
       max_audit_pages=3,
       output_dir=Path('out/client_name/audits')
   )
   ```

2. Review audit results:
   - Overall score (0-100)
   - Content/Technical/SEO subscores
   - Issues by severity
   - Page-by-page analysis

**Output**: Onboarding report with audit scores + quick wins deck

### Step 5: Generate Quick Wins

**Actions**:
1. Review quick wins from dossier
2. Review quick wins from audit
3. Prioritize by impact × effort
4. Select top 5-8 for client presentation

**Output**: Prioritized quick wins list

---

## Phase 3: Outreach Preparation (30-45 mins)

### Step 6: Compose Outreach Drafts

**Actions**:
1. Choose message type (email, LinkedIn, SMS)
2. Select language (EN, FR, DE)
3. Choose tone (professional, friendly, direct)
4. Generate 3 variants
   ```python
   from outreach.compose import compose_outreach

   result = compose_outreach(
       lead_data=lead_record.dict(),
       llm_adapter=adapter,
       dossier_summary=dossier.company_overview,
       message_type='email',
       language='de',
       tone='friendly',
       output_dir=Path('out/client_name/outreach')
   )
   ```

5. Review deliverability scores
6. Select best variant or blend elements

**Output**: 3 outreach variants with deliverability analysis

### Step 7: Package for Client

**Actions**:
1. Export one-click pack (if UI implemented)
2. Or manually compile:
   - Dossier markdown
   - Audit report
   - Quick wins deck
   - 3 outreach drafts

**Output**: Client package (ZIP or folder)

---

## Phase 4: Delivery & Follow-up (15-30 mins)

### Step 8: Client Presentation

**Materials**:
1. **Dossier** (5-10 min read)
   - Company overview
   - Current state analysis
   - Opportunities identified

2. **Quick Wins Deck** (Top 5-8 tasks)
   - Prioritized by impact × effort
   - 48h timeline
   - Clear actions and expected results

3. **Outreach Drafts** (Optional)
   - 3 personalized variants
   - Ready to use for lead generation

**Talking Points**:
- "I analyzed X pages of your website"
- "Found Y opportunities for improvement"
- "Here are Z quick wins we can implement in 48 hours"
- "Expected impact: [specific metrics from quick wins]"

### Step 9: Project Scoping

**Based on Findings**:

**Tier 1: Quick Wins Only** (€500-1,500)
- 48h implementation
- Focus on top 3-5 quick wins
- Immediate impact
- No long-term commitment

**Tier 2: Quick Wins + Foundation** (€2,000-5,000)
- 1-2 week project
- Quick wins + technical foundation
- Example: SSL + GMB + menu online + booking system
- Measurable ROI

**Tier 3: Comprehensive Upgrade** (€5,000-15,000)
- 4-8 week project
- Full site improvements
- Ongoing support option
- Custom solution

---

## Tools & Templates

### Configuration

**Vertical Presets**:
- `presets/verticals/restaurant.yml`: Restaurant-specific rules
- `presets/verticals/retail.yml`: Retail/e-commerce rules
- `presets/verticals/professional_services.yml`: Services rules

**Usage**:
```python
# Load vertical preset
import yaml
with open('presets/verticals/restaurant.yml') as f:
    preset = yaml.safe_load(f)

# Apply scoring adjustments
config['scoring'].update(preset['scoring'])
```

### Multilingual Support

**Languages**: EN, FR, DE

**Usage**:
```python
from locale.i18n import get_tone_preset, format_message

# Get German friendly tone
tone = get_tone_preset('de', 'friendly')
# Returns: greeting, closing, formality

# Format message
message = format_message(
    template="{greeting},\n\n{body}\n\n{closing}",
    language='de',
    tone='friendly',
    body="Message content..."
)
```

### Export Formats

**All systems support**:
- Markdown (human-readable)
- JSON (machine-readable)
- JSONL (for leads)
- CSV/XLSX (for spreadsheet tools)

---

## Success Metrics

**Track These KPIs**:

1. **Lead Qualification**
   - Time to qualify: Target < 30 mins
   - Fit score distribution
   - Conversion rate (qualified → client)

2. **Deliverables Quality**
   - Dossier accuracy (client feedback)
   - Quick wins completion rate
   - Outreach response rate

3. **Client Outcomes**
   - Quick wins implemented
   - Measurable improvements
   - Project conversion (quick wins → full project)

**Target Benchmarks**:
- 80%+ quick wins completion rate
- 15-25% outreach response rate
- 30%+ quick wins → full project conversion

---

## Common Scenarios

### Scenario 1: Restaurant (Berlin)

**Discovery**: Search "restaurants berlin mitte"
**Vertical**: Restaurant preset
**Language**: German
**Tone**: Friendly

**Quick Wins Focus**:
1. Google Business Profile
2. Instagram optimization
3. Online menu
4. Reservation system

**Outreach Angle**: Local SEO + online reservations

---

### Scenario 2: Boutique (Paris)

**Discovery**: Crawl specific domain
**Vertical**: Retail preset
**Language**: French
**Tone**: Professional

**Quick Wins Focus**:
1. Product photography
2. Shipping information
3. Mobile optimization
4. Google Shopping feed

**Outreach Angle**: E-commerce conversion

---

### Scenario 3: Consultant (Munich)

**Discovery**: LinkedIn → website
**Vertical**: Professional services preset
**Language**: German
**Tone**: Professional

**Quick Wins Focus**:
1. Consultation booking
2. Case studies
3. Service landing pages
4. Trust badges

**Outreach Angle**: Lead generation + authority

---

## Troubleshooting

### Issue: Low fit scores

**Solutions**:
- Check vertical preset alignment
- Review business type classification
- Adjust fit criteria in preset

### Issue: Poor deliverability scores

**Solutions**:
- Remove spam words (check deliverability report)
- Shorten message (80-140 words for email)
- Limit links (max 1 for email)
- Improve personalization

### Issue: Generic quick wins

**Solutions**:
- Provide more context in dossier
- Use higher quality LLM model
- Review and customize manually
- Add industry-specific prompts

---

## Next Steps

After successful delivery:

1. **Implement quick wins** (if client approves)
2. **Track results** (analytics, rankings, conversions)
3. **Report outcomes** (before/after metrics)
4. **Propose next phase** (based on results)

**Retention Strategy**:
- Monthly quick wins packages
- Quarterly audits
- Ongoing support retainer
- Performance-based pricing

---

## Resources

**Documentation**:
- README.md: Technical setup
- CLAUDE.md: Architecture overview
- config/defaults.yml: All settings

**Support**:
- Issues: GitHub repository
- Community: [Link to community]
- Updates: [Link to changelog]
