# Dual-Model Configuration Guide

## Overview

Lead Hunter Toolkit now supports a **dual-model architecture** for granular control over performance and quality. This system uses two specialized models optimized for different workloads:

- **Small Model (Mistral 7B)**: Fast extraction, structured analysis, and categorization
- **Large Model (Llama 3 8B)**: Creative writing, advanced reasoning, and complex synthesis

## ⚠️ Important: LM Studio Multi-Model Limitation

**LM Studio can only serve ONE model at a time.** This is a fundamental limitation of LM Studio's architecture - while you can have multiple models downloaded, only one can be loaded into memory and served through the API endpoint.

### Solutions for True Dual-Model Operation

To achieve simultaneous dual-model operation, you have several options:

#### ✅ **Option 1: LM Studio + Ollama (Recommended)**

Use two different model servers:
- **LM Studio** (`https://lm.leophir.com/`) → Mistral 7B (small_model) for fast extraction
- **Ollama** (`http://oll.leophir.com/`) → Llama 3 8B (large_model) for creative tasks

**Setup**:
1. In LM Studio: Load `mistralai/mistral-7b-instruct-v0.3`
2. In Ollama: Pull and serve `llama3:8b` model
3. The configuration in `config/models.yml` already uses this split

**Pros**: True simultaneous operation, no manual switching
**Cons**: Requires running two servers, more resource intensive

#### Option 2: Single Model (Simplified)

Use only one model for all tasks:
- Choose **Mistral 7B** if speed is priority
- Choose **Llama 3 8B** if quality is priority

**Setup**: Update all tasks in `config/models.yml` to use the same model

**Pros**: Simple, lower resource usage
**Cons**: No task-specific optimization

#### Option 3: Manual Model Switching

Keep the current configuration but manually switch models in LM Studio based on your workflow:
- Load **Mistral 7B** when doing SEO audits, classification, extraction
- Load **Llama 3 8B** when doing outreach, dossiers, creative writing

**Pros**: Flexibility, full optimization
**Cons**: Requires manual intervention, models not available simultaneously

### Current Configuration

The default configuration uses **Option 1 (LM Studio + Ollama)**:
- Small model tasks → LM Studio endpoint
- Large model tasks → Ollama endpoint

If your Ollama endpoint is offline, the application will fall back to whatever model is currently loaded in LM Studio.

### Setting Up Ollama (for Option 1)

If you want to use the recommended LM Studio + Ollama setup:

1. **Install Ollama**:
   ```bash
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # macOS
   brew install ollama

   # Windows: Download from https://ollama.com/download
   ```

2. **Pull Llama 3 8B model**:
   ```bash
   ollama pull llama3:8b
   ```

3. **Serve Ollama** (if not auto-started):
   ```bash
   ollama serve
   ```
   By default, Ollama serves on `http://localhost:11434`

4. **Update endpoint** (if using localhost instead of `oll.leophir.com`):
   Edit `config/models.yml` and update the Ollama endpoint:
   ```yaml
   large_model:
     endpoint: "http://localhost:11434"
   ```

5. **Verify it's working**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Architecture

### Model Definitions

#### Small Model: `mistralai/mistral-7b-instruct-v0.3`

**Optimized for**: Speed-critical structured tasks

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Temperature | 0.4 | Balanced determinism with some creativity |
| Top-K | 30 | Focused vocabulary for structured output |
| Top-P | 0.9 | Nucleus sampling for quality |
| Max Tokens | 4096 | Sufficient for extraction tasks |
| Context | 4096 | Fast inference |

**Use Cases**:
- AI-powered web scraping and extraction
- SEO content audits
- Lead classification and categorization
- Structured JSON output
- Fast analytical tasks

#### Large Model: `llama3:8b` (via Ollama)

**Optimized for**: Quality and creative reasoning

**Note**: The large model is served via Ollama (not LM Studio) to enable true simultaneous dual-model operation.

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Temperature | 0.6-0.7 | Higher creativity for writing tasks |
| Top-K | 40 | Broader vocabulary for expression |
| Top-P | 0.9 | Nucleus sampling for quality |
| Max Tokens | 8192 | Extended output for long-form content |
| Context | 8192 | Complex reasoning support |

**Use Cases**:
- French outreach message generation
- Lead summarization with insights
- Dossier building and analysis
- Complex multi-step reasoning
- High-quality content generation

## Task-to-Model Mapping

### Automatic Model Selection

| Feature | Tab | Model | Temperature | Rationale |
|---------|-----|-------|-------------|-----------|
| Search Scraper (AI Extraction) | Search Scraper | Mistral 7B | 0.4 | Fast JSON extraction from web sources |
| SEO Content Audit | SEO Tools | Mistral 7B | 0.4 | Structured analysis of meta tags, headings, etc. |
| Lead Classification | Hunt (background) | Mistral 7B | 0.4 | Deterministic keyword-based tagging |
| Lead Summarization | Review | Llama 3 8B | 0.6 | Advanced reasoning for insights |
| Outreach Generation | Outreach | Llama 3 8B | 0.7 | Creative French email writing |
| Dossier Building | Dossier | Llama 3 8B | 0.6 | Complex multi-source synthesis |

### Model Presets in `config/models.yml`

```yaml
models:
  # Primary models
  small_model:
    id: "mistralai/mistral-7b-instruct-v0.3"
    temperature: 0.4
    top_k: 30
    top_p: 0.9

  large_model:
    id: "meta-llama-3-8b-instruct.gguf"
    temperature: 0.7
    top_k: 40
    top_p: 0.9

  # Task-specific presets
  classification:
    # Uses small_model
    id: "mistralai/mistral-7b-instruct-v0.3"
    temperature: 0.4

  outreach:
    # Uses large_model
    id: "meta-llama-3-8b-instruct.gguf"
    temperature: 0.7

  audit:
    # Uses small_model
    id: "mistralai/mistral-7b-instruct-v0.3"
    temperature: 0.4
```

## Configuration

### Via UI (Streamlit)

1. **Open Settings Sidebar**
2. **Navigate to "Advanced LLM Settings" Expander**
3. **Configure Parameters**:
   - **Temperature**: Controls randomness (0.0 = deterministic, 2.0 = very creative)
   - **Top-K**: Limits vocabulary to top K tokens (30-50 typical)
   - **Top-P**: Cumulative probability threshold (0.8-0.95 typical)
   - **Max Tokens**: Maximum response length

### Via `settings.json`

```json
{
  "llm_base": "https://lm.leophir.com/",
  "llm_key": "your-api-key",
  "llm_model": "mistralai/mistral-7b-instruct-v0.3",
  "llm_temperature": 0.4,
  "llm_top_k": 40,
  "llm_top_p": 0.9,
  "llm_max_tokens": 2048
}
```

### Via `config/defaults.yml`

Global defaults for all features:

```yaml
llm:
  base_url: "https://lm.leophir.com/"
  model: "mistralai/mistral-7b-instruct-v0.3"
  temperature: 0.4
  top_k: 40
  top_p: 0.9
  max_tokens: 2048
  timeout: 60
```

## Implementation Details

### Code Architecture

#### 1. LLM Adapter (`llm/adapter.py`)

The unified adapter supports both models with consistent parameters:

```python
from llm.adapter import LLMAdapter

# Create adapter with small model
adapter = LLMAdapter(
    base_url="https://lm.leophir.com/",
    model="mistralai/mistral-7b-instruct-v0.3",
    temperature=0.4,
    top_k=30,
    top_p=0.9,
    max_tokens=4096
)

# Or from config
from config.loader import ConfigLoader
config_loader = ConfigLoader()
config = config_loader.get_merged_config()
adapter = LLMAdapter.from_config(config, model_override="large_model")
```

#### 2. LLM Client (`llm_client.py`)

Legacy client for backward compatibility:

```python
from llm_client import LLMClient

client = LLMClient(
    base_url="https://lm.leophir.com/",
    model="meta-llama-3-8b-instruct.gguf",
    temperature=0.6,
    top_k=40,
    top_p=0.9,
    max_tokens=2048
)

summary = client.summarize_leads(leads, "Summarize top 10 opportunities")
```

#### 3. Config Loader (`config/loader.py`)

Merges configuration from multiple sources with proper precedence:

```python
from config.loader import ConfigLoader

loader = ConfigLoader()

# Get specific model config
model_config = loader.get_model_config("small_model")

# Get merged config (settings.json overrides defaults.yml)
config = loader.get_merged_config()
llm_config = config['llm']  # Contains base_url, model, temperature, top_k, top_p
```

### Parameter Flow

```
settings.json (highest priority)
    ↓
config/defaults.yml
    ↓
config/models.yml (task presets)
    ↓
llm/adapter.py or llm_client.py
    ↓
OpenAI-compatible API (LM Studio)
```

## Sampling Parameters Explained

### Temperature

Controls randomness in token selection:
- **0.0**: Completely deterministic (always picks most likely token)
- **0.4**: Slightly creative, good for structured tasks
- **0.6-0.7**: Balanced for analytical writing
- **1.0**: High creativity
- **2.0**: Very creative, unpredictable

**Recommendations**:
- Classification/Extraction: 0.2-0.4
- Analysis/Summarization: 0.5-0.7
- Creative Writing: 0.7-0.9

**API Support**: ✅ Sent via OpenAI-compatible API

### Top-K

⚠️ **IMPORTANT**: Top-K is **NOT supported** by OpenAI-compatible APIs (including LM Studio's endpoint). You must configure this parameter **directly in LM Studio's model settings**.

Limits vocabulary to top K most probable tokens:
- **Lower (10-30)**: More focused, consistent output
- **Medium (30-50)**: Balanced diversity
- **Higher (50-100)**: More diverse vocabulary

**Recommendations**:
- Structured output (JSON): 20-30 → **Configure in LM Studio for Mistral 7B**
- General tasks: 30-50
- Creative writing: 40-60 → **Configure in LM Studio for Llama 3 8B**

**API Support**: ❌ Must be configured in LM Studio model settings (not sent via API)

**How to Configure in LM Studio**:
1. Load your model in LM Studio
2. Click on model settings/parameters
3. Set "Top-K" to desired value (30 for Mistral 7B, 40 for Llama 3 8B)
4. Save model configuration

### Top-P (Nucleus Sampling)

Cumulative probability threshold:
- **Lower (0.7-0.8)**: Conservative, safer outputs
- **Medium (0.85-0.95)**: Balanced quality
- **Higher (0.95-1.0)**: Maximum diversity

**Recommendations**:
- Most tasks: 0.9
- Extraction/Classification: 0.8-0.9
- Creative tasks: 0.9-0.95

**API Support**: ✅ Sent via OpenAI-compatible API

## Workflow Examples

### Example 1: Fast Lead Extraction

```python
# Search Scraper tab automatically uses small_model
# User input: "Find plumbers in Bordeaux"
# Result: Fast extraction using Mistral 7B with top_k=30

# Behind the scenes (ui/tabs/search_scraper_tab.py):
scraper = SearchScraper(
    llm_model="mistralai/mistral-7b-instruct-v0.3",
    temperature=0.4
)
```

### Example 2: Quality French Outreach

```python
# Outreach tab automatically uses large_model
# User selects lead and clicks "Generate Outreach"
# Result: High-quality French email variants using Llama 3 8B

# Behind the scenes (ui/tabs/outreach_tab.py):
adapter = LLMAdapter.from_config(config)  # Uses 'outreach' preset
# → meta-llama-3-8b-instruct.gguf with temp=0.7
```

### Example 3: SEO Content Audit

```python
# SEO Tools tab uses small_model for fast analysis
# User inputs URL: "https://example.com"
# Result: Structured SEO metrics using Mistral 7B

# Behind the scenes (ui/tabs/seo_tools_tab.py):
client = LLMClient(
    model="mistralai/mistral-7b-instruct-v0.3",
    temperature=0.4,
    top_k=30
)
```

## Performance Benchmarks

### Typical Response Times (Local LM Studio)

| Task | Model | Tokens | Response Time | Quality |
|------|-------|--------|---------------|---------|
| JSON Extraction | Mistral 7B | ~500 | 3-5s | Excellent |
| SEO Audit | Mistral 7B | ~1000 | 5-8s | Excellent |
| Lead Summary | Llama 3 8B | ~800 | 8-12s | Outstanding |
| French Outreach | Llama 3 8B | ~400 | 6-10s | Outstanding |

### GPU Requirements

**Mistral 7B (Q4_K_M)**:
- VRAM: ~5-6 GB
- Layers on GPU: All (32)
- Speed: ~30-40 tokens/sec

**Llama 3 8B (Q4_K_M)**:
- VRAM: ~6-7 GB
- Layers on GPU: 30-32 (leave 1-2GB free)
- Speed: ~25-35 tokens/sec

**Recommended Hardware**:
- Minimum: RTX 3060 12GB
- Recommended: RTX 4070 12GB or RTX 4080 16GB
- Optimal: RTX 4090 24GB (both models in VRAM simultaneously)

## Troubleshooting

### Issue: "Unexpected keyword argument 'top_k'"

**Symptom**: `TypeError: Completions.create() got an unexpected keyword argument 'top_k'`

**Cause**: OpenAI-compatible APIs (including LM Studio) don't support `top_k` as an API parameter.

**Solution**:
1. ✅ **Already Fixed**: Latest version doesn't send `top_k` via API
2. Configure `top_k` directly in LM Studio:
   - Open LM Studio
   - Load your model
   - Go to Model Settings
   - Set Top-K: 30 for Mistral 7B, 40 for Llama 3 8B
   - Save configuration
3. The UI slider is for **reference only** - it documents the recommended value but doesn't send it to the API

### Issue: "Only user and assistant roles are supported!"

**Symptom**: `Error rendering prompt with jinja template: "Only user and assistant roles are supported!"`

**Cause**: Mistral 7B's Jinja prompt template only accepts `user` and `assistant` roles, not `system` role. This is a model-specific constraint.

**Solution**:
1. ✅ **Already Fixed**: Latest version prepends system messages to user messages instead of using separate system role
2. The fix automatically combines system and user messages into a single user message
3. No configuration changes needed - the adapter handles this transparently
4. Both `chat_with_system()` and `chat_with_system_async()` now compatible with Mistral

**Technical Details**:
- Old behavior: `[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]`
- New behavior: `[{"role": "user", "content": "system_msg\n\nuser_msg"}]`
- This maintains the same context while being compatible with Mistral's template constraints

### Issue: Model Not Found

**Symptom**: `Model 'mistralai/mistral-7b-instruct-v0.3' not found`

**Solution**:
1. Check model is loaded in LM Studio
2. Verify model ID matches exactly in LM Studio
3. Check endpoint is accessible: `curl https://lm.leophir.com/v1/models`

### Issue: Slow Response Times

**Symptom**: Responses taking >20 seconds

**Solution**:
1. Check GPU layers: Should be set to max in LM Studio
2. Verify VRAM not exhausted: Use `nvidia-smi`
3. Reduce `max_tokens` if response too long
4. Use `small_model` for faster tasks

### Issue: Low-Quality Outputs

**Symptom**: Responses are too generic or repetitive

**Solution**:
1. Increase `temperature` (try 0.6-0.7)
2. Increase `top_k` (try 40-50)
3. Check using correct model for task:
   - Creative tasks → `large_model`
   - Structured tasks → `small_model`

### Issue: JSON Parsing Errors

**Symptom**: Invalid JSON from extraction tasks

**Solution**:
1. Lower `temperature` (try 0.2-0.4)
2. Use `small_model` (Mistral 7B)
3. Set `top_k=30` for more focused output
4. Add explicit JSON schema in prompt

## Migration Guide

### From Single-Model Setup

If you were using a single model configuration, here's how to migrate:

**Old `settings.json`**:
```json
{
  "llm_model": "llama-3-8b-instruct-64k",
  "llm_temperature": 0.2
}
```

**New `settings.json`** (automatic):
```json
{
  "llm_model": "mistralai/mistral-7b-instruct-v0.3",
  "llm_temperature": 0.4,
  "llm_top_k": 40,
  "llm_top_p": 0.9,
  "llm_max_tokens": 2048
}
```

**Note**: Individual tabs override model selection automatically. Your French outreach will still use Llama 3 8B even if settings default to Mistral 7B.

### Custom Model Overrides

To use a different model for specific tasks:

1. **Edit `config/models.yml`**:
```yaml
outreach:
  id: "your-custom-model-id"
  temperature: 0.8
  top_k: 50
```

2. **Or override in code**:
```python
adapter = LLMAdapter.from_config(config, model_override="your-custom-model")
```

## Best Practices

### 1. Match Model to Task

- **Use Mistral 7B** for:
  - Extraction (emails, contacts, structured data)
  - Classification and categorization
  - SEO audits and technical analysis
  - JSON/structured output

- **Use Llama 3 8B** for:
  - French language content generation
  - Creative writing and personalization
  - Complex reasoning and synthesis
  - Long-form summaries with insights

### 2. Temperature Guidelines

| Task Type | Temperature Range | Reasoning |
|-----------|-------------------|-----------|
| Extraction | 0.2-0.4 | Deterministic, consistent |
| Classification | 0.3-0.5 | Slight creativity for edge cases |
| Analysis | 0.5-0.7 | Balanced insights |
| Creative Writing | 0.7-0.9 | High quality, diverse output |

### 3. Context Management

- Keep prompts under 50% of max context window
- Mistral 7B: ~2000 tokens for prompt
- Llama 3 8B: ~4000 tokens for prompt
- Reserve space for response generation

### 4. Error Handling

Always wrap LLM calls with proper error handling:

```python
try:
    result = adapter.chat(messages)
    if not result or "Error" in result:
        logger.error("LLM call failed")
        return fallback_response
except Exception as e:
    logger.error(f"LLM exception: {e}")
    return fallback_response
```

## API Reference

### LLMAdapter Class

```python
class LLMAdapter:
    def __init__(
        self,
        base_url: str,
        api_key: str = "not-needed",
        model: str = "openai/gpt-oss-20b",
        temperature: float = 0.2,
        top_k: int | None = None,
        top_p: float | None = None,
        max_tokens: int = 2048,
        timeout: int = 60
    )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs
    ) -> str

    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs
    ) -> str

    @classmethod
    def from_config(
        cls,
        config: Dict[str, Any],
        model_override: str | None = None
    ) -> 'LLMAdapter'
```

### LLMClient Class

```python
class LLMClient:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        top_k: int | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None
    )

    def summarize_leads(
        self,
        leads: List[dict],
        instruction: str = "Summarize the top opportunities in 10 bullets."
    ) -> str
```

## Future Enhancements

### Planned Features

1. **Dynamic Model Selection**: Auto-select model based on task complexity
2. **Model Ensemble**: Combine outputs from both models for critical tasks
3. **Fine-tuned Models**: Domain-specific Mistral/Llama variants
4. **Quantization Options**: Support for Q2_K, Q3_K_S, Q5_K_M, etc.
5. **Multi-GPU Support**: Distribute models across multiple GPUs

### Community Contributions

To add a new model:

1. Add entry to `config/models.yml`
2. Test with representative tasks
3. Document performance characteristics
4. Submit PR with benchmarks

## Support

For issues or questions:
- GitHub Issues: https://github.com/nicolasestrem/leadhunter_toolkit_max/issues
- Documentation: See CLAUDE.md for architecture details
- Model Configs: See config/models.yml for full model catalog

---

**Last Updated**: 2025-10-13
**Version**: 1.0.0
**Author**: Lead Hunter Toolkit Team
