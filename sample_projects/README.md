# Sample Projects - Lead Hunter Toolkit Consulting Pack

This directory contains example projects demonstrating the consulting pack capabilities with realistic input and expected outputs.

## Purpose

These samples serve as:
- **Reference examples** for new users learning the system
- **Test data** for validating consulting pack functionality
- **Documentation** showing expected system behavior
- **Quality benchmarks** for comparison during development

## Projects Included

### 1. Restaurant Example (`restaurant_example/`)

**Business Profile**: Bella Trattoria Berlin - Italian restaurant in Prenzlauer Berg

**Demonstrates**:
- Restaurant vertical preset application (higher weights for phone/social)
- Multi-channel contact enrichment (email, phone, social media)
- German-language outreach generation
- Local SEO optimization recommendations
- Google My Business audit findings
- Quick-win identification for hospitality businesses

**Key Features**:
- Complete social media presence (Instagram, Facebook, Google Business)
- Multiple contact methods
- High-quality score (9.5/10) due to complete data
- Vertical-specific outreach focusing on reservations and local visibility

### 2. Retail Example (`retail_example/`)

**Business Profile**: Naturkosmetik Müller - Organic cosmetics shop in Munich

**Demonstrates**:
- Retail vertical preset application
- Lead with growth potential (limited current presence)
- E-commerce opportunity identification
- Content marketing recommendations
- Lower initial quality score (6.5/10) but high fit score (8.0/10)
- Niche market positioning analysis

**Key Features**:
- Family-owned business authenticity
- Digital transformation opportunities
- Social media growth potential
- Local discovery optimization

## File Structure

Each project contains:

```
project_name/
├── input.json              # Raw lead data (as extracted from web)
└── expected_output.json    # Complete consulting pack output
```

### Input Format

Lead data with standard fields:
- Basic info: domain, name, website
- Contact: emails[], phones[]
- Social: facebook, instagram, google_business, etc.
- Location: address, city, country
- Metadata: tags[], status, notes
- Content: content_sample (for LLM analysis)

### Expected Output Format

Comprehensive consulting pack results:

**classification**: Scoring and categorization
- business_type, score_quality, score_fit, score_priority
- issue_flags[], quality_signals[]
- vertical_applied

**dossier**: Business intelligence
- business_overview, digital_presence, opportunities
- target_audience, competitive_position

**outreach_variants**: 3 message variations
- Different angles: quick-win, opportunity-focused, problem-focused
- Localized (German) content
- Deliverability scores
- Vertical context indicators

**audit_findings**: Technical assessment
- priority_issues[] with severity and quick-win recommendations
- strengths[] highlighting positive aspects

**quick_wins**: Actionable recommendations
- Title, description, estimated time/impact
- Step-by-step implementation guides

## Using the Samples

### Manual Testing

1. **Load input into the system**:
   ```bash
   # Copy input data to test
   cp sample_projects/restaurant_example/input.json test_lead.json
   ```

2. **Process through consulting pack**:
   - Run classification with restaurant vertical active
   - Generate dossier
   - Compose outreach in German
   - Run audit and generate quick wins

3. **Compare output**:
   - Check scores match expected ranges
   - Verify vertical context applied correctly
   - Validate outreach quality and deliverability
   - Review recommendations relevance

### Automated Validation

Use the helper scripts (see below) to automate validation:

```bash
# Run full validation
python sample_projects/validate_sample.py restaurant_example

# Generate new samples
python sample_projects/generate_sample.py --vertical restaurant --output my_test

# Execute workflow
python sample_projects/run_sample.py restaurant_example
```

## Helper Scripts

### `generate_sample.py`

Creates new sample projects with realistic data.

**Usage**:
```bash
python sample_projects/generate_sample.py \\
  --vertical restaurant \\
  --city Berlin \\
  --output new_restaurant_example
```

**Features**:
- Generates realistic business data
- Creates appropriate vertical configuration
- Produces expected outputs based on scoring logic
- Supports multiple verticals and cities

### `run_sample.py`

Executes the full consulting pack workflow on a sample.

**Usage**:
```bash
python sample_projects/run_sample.py restaurant_example
```

**Process**:
1. Loads input.json
2. Applies appropriate vertical preset
3. Runs classification and scoring
4. Builds dossier
5. Generates outreach variants
6. Performs audit and identifies quick wins
7. Saves actual output for comparison

### `validate_sample.py`

Validates actual output against expected output.

**Usage**:
```bash
python sample_projects/validate_sample.py restaurant_example
```

**Checks**:
- Score ranges (within ±0.5 of expected)
- Required fields presence
- Vertical context application
- Outreach deliverability thresholds (≥85)
- Audit findings completeness
- Quick wins actionability

**Exit codes**:
- 0: Validation passed
- 1: Validation failed with differences reported

## Validation Criteria

### Classification Validation

- ✅ `score_quality` within ±0.5 of expected
- ✅ `score_fit` within ±1.0 of expected
- ✅ `score_priority` within ±0.8 of expected
- ✅ `business_type` matches expected
- ✅ `vertical_applied` matches active vertical

### Outreach Validation

- ✅ 3 variants generated (quick-win, opportunity, problem)
- ✅ All deliverability scores ≥ 85
- ✅ Vertical context indicators present
- ✅ Localized content (German for these examples)
- ✅ Subject lines 30-60 characters
- ✅ Body word count 80-140 for email

### Dossier Validation

- ✅ All required sections present
- ✅ Opportunities list has ≥3 items
- ✅ Digital presence assessed
- ✅ Competitive position described

### Audit Validation

- ✅ Priority issues identified (≥2)
- ✅ Quick wins provided for each issue
- ✅ Strengths listed (≥2)
- ✅ Severity levels appropriate

### Quick Wins Validation

- ✅ ≥3 quick wins identified
- ✅ Each has estimated time and impact
- ✅ Implementation steps provided (≥3 steps each)
- ✅ Time estimates reasonable (15 min - 6 hours)

## Adding New Samples

To add a new sample project:

1. **Create directory**:
   ```bash
   mkdir sample_projects/new_example
   ```

2. **Create input.json** with lead data

3. **Generate expected output** manually or with helper script

4. **Validate** against existing samples for consistency

5. **Document** specific features being demonstrated

6. **Update this README** with new example description

## Integration with Tests

These samples can be used in automated tests:

```python
# Example test using samples
def test_restaurant_classification():
    with open('sample_projects/restaurant_example/input.json') as f:
        lead_data = json.load(f)

    # Run classification
    result = classify_and_score_lead(lead, llm_adapter)

    # Load expected
    with open('sample_projects/restaurant_example/expected_output.json') as f:
        expected = json.load(f)

    # Validate
    assert abs(result.score_quality - expected['classification']['score_quality']) < 0.5
    assert result.business_type == expected['classification']['business_type']
```

## Best Practices

1. **Keep samples realistic** - Use plausible business names, addresses, and data
2. **Update regularly** - As system evolves, refresh expected outputs
3. **Document edge cases** - Create samples for unusual scenarios
4. **Version control** - Track changes to samples over time
5. **Cross-reference** - Link samples to specific features or bugs

## Troubleshooting

**Q: My output doesn't match expected output**
- Check if vertical preset is active
- Verify LLM temperature settings
- Confirm scoring weights in config
- Review recent code changes

**Q: Deliverability scores too low**
- Check spam word list is up-to-date
- Verify message length constraints
- Review exclamation mark detection
- Validate link count rules

**Q: Classification scores vary**
- LLM responses have some variance (temp > 0)
- Check ±tolerance ranges in validation
- Ensure content_sample is provided
- Verify config weights applied

## Contributing

When contributing new samples:

1. Follow existing naming conventions
2. Include comprehensive expected outputs
3. Add validation rules if needed
4. Update this README
5. Test with helper scripts
6. Submit PR with explanation of what's demonstrated

## License

These samples are part of the Lead Hunter Toolkit and follow the project license.
