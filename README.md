# Lead Hunter Toolkit • Consulting Pack v1

A comprehensive SMB consulting tool combining lead generation, automated analysis, and personalized outreach. Transform leads into clients with AI-powered dossiers, audits, and quick wins.

## 🎯 What's New: Consulting Pack v1

**The toolkit has been transformed into a complete consulting solution** for SMB digital consulting, with:

- **🤖 LLM-Powered Analysis**: Classification, dossiers, audits using local models (LM Studio/Ollama)
- **📊 Multi-Dimensional Scoring**: Quality, fit, and priority scores for lead prioritization
- **📝 Personalized Outreach**: Generate 3 message variants (email/LinkedIn/SMS) in EN/FR/DE
- **📋 Client Dossiers**: RAG-based summaries with cited sources and 48h quick wins
- **🔍 SEO Audits**: LLM-enhanced page analysis with actionable recommendations
- **⚡ Onboarding Wizard**: Automated client onboarding (crawl → audit → quick wins)
- **🌍 Multilingual**: Full support for English, French, German
- **🎨 Vertical Presets**: Optimized for restaurants, retail, professional services
- **🔌 Plugin System**: Extensible architecture for custom workflows

---

## 📚 Quick Start for Consultants

### Installation

```bash
# 1. Clone and setup
git clone https://github.com/nicolasestrem/leadhunter_toolkit_max.git
cd leadhunter_toolkit_max

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
# source .venv/bin/activate    # Linux/Mac

# 3. Install dependencies
pip install -U pip
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

### LLM Setup

The toolkit works best with **local LLMs** via LM Studio or Ollama:

**Option 1: LM Studio** (Recommended)
1. Download LM Studio: https://lmstudio.ai/
2. Load a model (e.g., `qwen/qwen3-4b-2507` or `openai/gpt-oss-20b`)
3. Start local server (default: `http://localhost:1234`)
4. Configure in `config/models.yml` or settings.json

**Option 2: Ollama**
1. Install Ollama: https://ollama.ai/
2. Pull model: `ollama pull llama3`
3. Server runs at `http://localhost:11434`

**Option 3: OpenAI API**
- Add your API key to settings.json
- Set `llm_base` to `https://api.openai.com`

### Configuration

Edit `config/models.yml` or use settings.json:

```yaml
# Your LM Studio endpoint
default_endpoint: "https://lm.leophir.com/"

# Model aliases
models:
  gpt-oss-20b:
    id: "openai/gpt-oss-20b"
    temperature: 0.2
    max_tokens: 2048
```

---

## 🚀 Core Features

### 1. Lead Classification & Scoring

**Multi-dimensional lead scoring** with LLM-based classification:

```python
from leads.classify_score import classify_and_score_lead
from llm.adapter import LLMAdapter
from config.loader import get_config

# Setup
config = get_config().get_merged_config()
adapter = LLMAdapter.from_config(config)

# Classify and score
lead_record = classify_and_score_lead(
    lead=lead,
    llm_adapter=adapter,
    content_sample=page_content,
    use_llm=True
)

# Results
print(f"Quality: {lead_record.score_quality}/10")  # Data completeness
print(f"Fit: {lead_record.score_fit}/10")          # SMB target match
print(f"Priority: {lead_record.score_priority}/10")  # Overall ranking
print(f"Type: {lead_record.business_type}")
print(f"Issues: {lead_record.issue_flags}")
print(f"Signals: {lead_record.quality_signals}")
```

### 2. Personalized Outreach

**Generate 3 variants** with deliverability checking:

```python
from outreach.compose import compose_outreach

result = compose_outreach(
    lead_data=lead_record.dict(),
    llm_adapter=adapter,
    dossier_summary="Brief company overview...",
    message_type='email',  # or 'linkedin', 'sms'
    language='de',         # or 'en', 'fr'
    tone='friendly',       # or 'professional', 'direct'
    output_dir=Path('out/client/outreach')
)

# Each variant includes:
# - Subject line (email)
# - Message body (personalized)
# - CTA
# - Deliverability score (0-100)
```

**Deliverability Features**:
- Spam word detection with alternatives
- Word count validation (80-140 for email)
- Link limit enforcement
- Subject line optimization
- Personalization checks

### 3. Client Dossiers

**RAG-based comprehensive analysis** with cited sources:

```python
from dossier.build import build_dossier

dossier = build_dossier(
    lead_data=lead_record.dict(),
    pages=[
        {'url': 'https://example.com', 'content': '...'},
        {'url': 'https://example.com/about', 'content': '...'},
    ],
    llm_adapter=adapter,
    output_dir=Path('out/client/dossiers')
)

# Dossier includes:
# - Company overview (2-3 sentences)
# - Services/products list
# - Digital presence analysis
# - Signals (positive, growth, pain)
# - Issues detected (with sources)
# - 48h quick wins (prioritized)
```

### 4. SEO Audits & Quick Wins

**LLM-enhanced page auditing**:

```python
from audit.page_audit import audit_page
from audit.quick_wins import generate_quick_wins

# Audit page
audit = audit_page(
    url='https://example.com',
    html_content=html,
    llm_adapter=adapter,
    use_llm=True
)

print(f"Score: {audit.score}/100 (Grade {audit.grade})")
print(f"Content: {audit.content_score}/100")
print(f"Technical: {audit.technical_score}/100")
print(f"SEO: {audit.seo_score}/100")

# Generate quick wins
tasks = generate_quick_wins(audit, max_wins=8)

for task in tasks:
    print(f"{task.task.title}: {task.priority_score:.1f}/10")
```

### 5. Onboarding Wizard

**Automated client onboarding** (crawl → audit → quick wins):

```python
from onboarding.wizard import run_onboarding

result = await run_onboarding(
    domain='client-site.com',
    llm_adapter=adapter,
    max_crawl_pages=10,
    max_audit_pages=3,
    output_dir=Path('out/client/audits')
)

# Generates:
# - Audit summary for each page
# - Aggregated quick wins (top 8)
# - Markdown report for client
```

---

## 🌍 Multilingual Support

**Full support for EN, FR, DE** in all features:

```python
from locale.i18n import get_tone_preset, format_message
from locale.formats import format_phone, format_currency, format_date

# Tone presets per language
tone = get_tone_preset('de', 'friendly')
# → greeting: "Hallo"
# → closing: "Viele Grüße"

# Format phone numbers
phone_de = format_phone("+49 30 12345678", "de")
# → "+49 30 12345678"

# Format currency
price_de = format_currency(1234.56, "de")
# → "1.234,56 €"

# Format dates
date_de = format_date(datetime.now(), "de")
# → "12.10.2025"
```

---

## 🎨 Vertical Presets

**Pre-configured for common SMB verticals**:

```python
import yaml

# Load restaurant preset
with open('presets/verticals/restaurant.yml') as f:
    preset = yaml.safe_load(f)

# Includes:
# - Adjusted scoring weights (social_weight higher for restaurants)
# - Outreach focus areas (reservations, GMB, reviews)
# - Audit priorities (images, local SEO)
# - Quick wins templates
```

**Available Presets**:
- `restaurant.yml`: Restaurants, cafés, bistros
- `retail.yml`: Retail stores, e-commerce
- `professional_services.yml`: Consultants, lawyers, agencies

---

## 🔌 Plugin System

**Extend functionality with custom plugins**:

```python
# plugins/my_plugin.py

def register():
    return {
        'version': '1.0.0',
        'description': 'Custom plugin',
        'hooks': {
            'after_lead_classification': modify_lead,
            'before_outreach_generation': add_context
        }
    }

def modify_lead(lead_record):
    # Customize lead processing
    return lead_record

def add_context(lead_data, message_type):
    # Add custom outreach context
    return lead_data
```

Plugins auto-load from `plugins/` directory.

---

## 📖 Documentation

- **[CLIENT_PLAYBOOK.md](docs/CLIENT_PLAYBOOK.md)**: Day-1 workflow for consultants
- **[CLAUDE.md](CLAUDE.md)**: Architecture and implementation details
- **[config/defaults.yml](config/defaults.yml)**: All configurable settings
- **[config/models.yml](config/models.yml)**: LLM model configurations

---

## 🏗️ Architecture

```
leadhunter_toolkit_max/
├── config/              # Configuration system
│   ├── models.yml       # LLM model presets
│   ├── defaults.yml     # App defaults
│   └── loader.py        # Config merging
├── llm/                 # LLM adapter & prompts
│   ├── adapter.py       # OpenAI-compatible client
│   ├── prompt_loader.py # YAML prompt loader
│   └── prompt_library/  # Structured prompts
│       ├── classify.yml
│       ├── outreach.yml
│       ├── dossier.yml
│       └── audit.yml
├── leads/               # Lead processing
│   ├── contacts_extract.py  # Extract from markdown
│   └── classify_score.py    # LLM classification
├── outreach/            # Outreach generation
│   ├── compose.py       # Message composer
│   └── deliverability_checks.py
├── dossier/             # Client dossiers
│   └── build.py         # RAG-based builder
├── audit/               # Page auditing
│   ├── page_audit.py    # LLM-enhanced audit
│   └── quick_wins.py    # Priority generation
├── onboarding/          # Client onboarding
│   └── wizard.py        # Automated workflow
├── locale/              # Internationalization
│   ├── i18n.py          # Language support
│   └── formats.py       # Locale formatting
├── presets/             # Vertical presets
│   └── verticals/
│       ├── restaurant.yml
│       ├── retail.yml
│       └── professional_services.yml
├── plugins/             # Plugin system
│   ├── loader.py        # Dynamic loading
│   └── example_plugin.py
└── tests/               # Test suite
    ├── test_llm_adapter.py
    ├── test_contacts_extract.py
    ├── test_scoring.py
    └── test_locale_formats.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_llm_adapter.py

# Run with coverage
pytest --cov=. --cov-report=html
```

**Test Coverage**:
- LLM adapter (11 tests)
- Contact extraction (12 tests)
- Scoring algorithms (10 tests)
- Locale formatting (15 tests)

---

## 🔧 Configuration

### config/models.yml

```yaml
default_endpoint: "https://lm.leophir.com/"

models:
  gpt-oss-20b:
    id: "openai/gpt-oss-20b"
    temperature: 0.2
    max_tokens: 2048

  # Task-specific presets
  classification:
    temperature: 0.1  # Low for consistency

  outreach:
    temperature: 0.7  # High for creativity
```

### config/defaults.yml

```yaml
locale:
  language: "en"
  country: "de"
  city: "Berlin"

llm:
  base_url: "https://lm.leophir.com/"
  model: "openai/gpt-oss-20b"
  temperature: 0.2
  max_tokens: 2048

scoring:
  email_weight: 2.0
  phone_weight: 1.0
  social_weight: 0.5
```

---

## 🎯 Use Cases

### 1. Restaurant Consultant (Berlin)

```python
# 1. Find leads
leads = search_restaurants("berlin mitte")

# 2. Classify & score
for lead in leads:
    lead_record = classify_and_score_lead(lead, adapter, ...)
    if lead_record.score_fit >= 8:
        # High-fit lead

# 3. Build dossier
dossier = build_dossier(lead_record, pages, adapter)

# 4. Generate outreach (German, friendly tone)
outreach = compose_outreach(
    lead_record, adapter,
    message_type='email', language='de', tone='friendly'
)

# 5. Run audit
audit_result = await run_onboarding(domain, adapter)
```

### 2. E-commerce Consultant (Paris)

```python
# Use retail preset
preset = load_preset('retail')
config['scoring'].update(preset['scoring'])

# Focus on conversion optimization
# French language, professional tone
```

### 3. Professional Services (Munich)

```python
# Use professional services preset
preset = load_preset('professional_services')

# Focus on lead generation
# German language, professional tone
```

---

## 💡 Best Practices

### LLM Model Selection

**For Classification**: Low temperature (0.1-0.2)
- `qwen/qwen3-4b-2507` (fast, good accuracy)
- `openai/gpt-oss-20b` (balanced)

**For Outreach**: Higher temperature (0.7)
- Creativity important for personalization

**For Audits/Dossiers**: Low temperature (0.1-0.2)
- Factual accuracy critical

### Prompt Engineering

All prompts in `llm/prompt_library/*.yml`:
- Include few-shot examples
- Specify output format (JSON)
- Add deliverability rules
- Provide context limits

### Vertical Customization

Create custom presets in `presets/verticals/`:
- Adjust scoring weights for industry
- Define industry-specific quick wins
- Add relevant keywords
- Customize outreach angles

---

## 🚦 Roadmap

### ✅ Completed (Backend ~80%)
- Config system
- LLM adapter
- Lead classification & scoring
- Outreach system
- Dossier builder
- Audit & quick wins
- Onboarding wizard
- Multilingual support
- Vertical presets
- Plugin system

### 🔄 In Progress (UI)
- Leads tab (advanced filters, exports)
- Outreach tab (3-variant display, copy buttons)
- Dossier tab (preview, sources view)
- Audit tab (visual scoring, issue tracking)
- Project selector (workspace management)

### 📋 Planned
- Sample projects with expected outputs
- Video tutorials
- More vertical presets (healthcare, automotive, etc.)
- Advanced analytics dashboard
- Team collaboration features

---

## 📄 License

See LICENSE file for details.

---

## 🤝 Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

---

## Original Features (Still Available)

### Lead Hunting

- BFS crawl within same host with contact/about prioritization
- Robots.txt aware by default
- Heuristic company name cleanup from <title> and H1
- Email + phone extraction including mailto: links
- Social discovery
- Keyword-based tagging
- Scoring with country-domain bonus
- Export to CSV, JSON and XLSX
- Optional Google Places enrichment

### Installation (Original)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -U pip
pip install -r requirements.txt
streamlit run app.py
```

### Google API Setup

To use Google Custom Search instead of DuckDuckGo:

1. Get API key: https://console.cloud.google.com/apis/credentials
2. Create search engine: https://programmablesearchengine.google.com/
3. Configure in Settings tab

**Notes**:
- Exports land in `out/` folder
- Keep concurrency respectful
- Presets saved in `presets/`

---

**Built with 🤖 [Claude Code](https://claude.com/claude-code)**
