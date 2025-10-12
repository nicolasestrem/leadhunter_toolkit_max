# Advanced Export System Guide

## Overview

The Lead Hunter Toolkit now features a comprehensive advanced export system with filtering, multiple formats, preview capabilities, and consulting pack ZIP generation.

## Architecture

### Core Modules

1. **export_advanced.py** - Core export functionality
   - `ExportFilter` - Dataclass for filter configuration
   - `apply_filters()` - Apply filters to lead lists
   - `export_filtered_csv/json/xlsx/markdown()` - Format-specific exports
   - `create_consulting_pack_zip()` - Complete consulting package in ZIP
   - `get_export_preview()` - Preview data before export

2. **export_sidebar.py** - Streamlit UI component
   - `render_export_sidebar()` - Complete sidebar export UI
   - Integrated into app.py sidebar

## Features

### 1. Advanced Filtering

**Score Filters:**
- Min/Max Score (legacy scoring)
- Min Quality Score (0-10)
- Min Fit Score (0-10)
- Min Priority Score (0-10)

**Business Type Filter:**
- Select one or more business types
- Dynamically generated from classified leads

**Tags Filter:**
- Select tags (any match)
- Filters leads containing any of the selected tags

**Status Filter:**
- Filter by lead status (new/contacted/qualified/rejected)

**Contact Filters:**
- Has emails only
- Has phones only

**Column Selection:**
- Choose specific columns to export
- Leave empty to export all columns

### 2. Export Formats

**CSV:**
- Compatible with Excel, Google Sheets
- Nested structures (lists/dicts) converted to JSON strings
- Preserves UTF-8 encoding

**JSON:**
- Structured data format
- Preserves nested objects
- Indent 2 for readability

**XLSX:**
- Native Excel format
- Uses openpyxl engine
- Nested structures converted to JSON strings

**Markdown:**
- Human-readable format
- Rich formatting with headers, links, metrics
- Perfect for documentation

### 3. Export Preview

Before exporting, preview feature shows:
- **Total filtered records**
- **Records with emails/phones**
- **Average scores** (legacy + multi-dimensional)
- **Business type distribution**
- **Sample records** (first 5)

### 4. Consulting Pack Export

Creates a complete ZIP package containing:

```
consulting_pack_export_YYYYMMDD_HHMMSS/
├── lead_info.json           # Lead data (JSON)
├── dossier.md               # Dossier (Markdown)
├── dossier.json             # Dossier (JSON)
├── outreach_variants.md     # All variants (Markdown)
├── outreach_variant_1_problem.txt    # Variant 1
├── outreach_variant_2_opportunity.txt # Variant 2
├── outreach_variant_3_quickwin.txt   # Variant 3
├── audit_report.md          # Audit (Markdown)
├── audit_findings.csv       # Audit issues (CSV)
└── summary.json             # Package metadata
```

**Use Case:** Share with clients, team members, or archive complete consulting engagement materials.

## Usage Examples

### Sidebar Export (Streamlit UI)

```python
# In app.py sidebar
from export_sidebar import render_export_sidebar

# Render the complete export UI
render_export_sidebar(project="my_project")
```

### Programmatic Export (Python)

```python
from export_advanced import (
    ExportFilter,
    export_filtered_csv,
    get_export_preview,
    create_consulting_pack_zip
)

# Example 1: Export high-quality leads only
filter = ExportFilter(
    min_quality=7.0,
    min_fit=6.0,
    has_emails=True,
    business_types=["restaurant", "retail"]
)

path, count = export_filtered_csv(leads, filter, project="berlin_restaurants")
print(f"Exported {count} leads to {path}")

# Example 2: Preview before export
preview, stats = get_export_preview(leads, filter, max_preview=5)
print(f"Would export {stats['total_filtered']} leads")
print(f"Average quality: {stats['avg_quality']:.1f}/10")

# Example 3: Create consulting pack
zip_path = create_consulting_pack_zip(
    lead=selected_lead,
    dossier_result=dossier,
    outreach_result=outreach,
    audit_result=audit,
    project="my_project"
)
print(f"Pack created: {zip_path}")
```

### Column Selection Example

```python
# Export only essential columns
filter = ExportFilter(
    columns=["name", "domain", "emails", "phones", "score_quality"]
)

path, count = export_filtered_xlsx(leads, filter, project="minimal_export")
```

### Date Range Export

```python
from datetime import datetime, timedelta

# Export leads from last 7 days
filter = ExportFilter(
    date_from=datetime.utcnow() - timedelta(days=7),
    date_to=datetime.utcnow()
)

path, count = export_filtered_json(leads, filter, project="recent_leads")
```

## Integration Guide

### Step 1: Import the Module

In your Streamlit app or Python script:

```python
from export_advanced import (
    ExportFilter,
    export_filtered_csv,
    export_filtered_json,
    export_filtered_xlsx,
    export_filtered_markdown,
    create_consulting_pack_zip,
    get_export_preview
)
```

### Step 2: Build Filter Configuration

```python
export_filter = ExportFilter(
    min_score=5.0,           # Legacy score
    max_score=10.0,
    min_quality=7.0,         # Multi-dimensional scores
    min_fit=6.0,
    min_priority=5.0,
    business_types=["restaurant", "cafe"],
    tags=["french", "organic"],
    statuses=["new", "qualified"],
    has_emails=True,
    has_phones=None,         # None = don't filter
    columns=None             # None = all columns
)
```

### Step 3: Export Data

```python
# Choose format and export
if format == "CSV":
    path, count = export_filtered_csv(leads, export_filter, project)
elif format == "JSON":
    path, count = export_filtered_json(leads, export_filter, project)
elif format == "XLSX":
    path, count = export_filtered_xlsx(leads, export_filter, project)
elif format == "Markdown":
    path, count = export_filtered_markdown(leads, export_filter, project)

print(f"Exported {count} records to {path}")
```

### Step 4: Provide Download (Streamlit)

```python
with open(path, "rb") as f:
    st.download_button(
        label=f"Download {format}",
        data=f.read(),
        file_name=os.path.basename(path),
        mime="text/csv"  # Adjust based on format
    )
```

## Output Directory Structure

```
out/
└── {project_name}/
    ├── leads/
    │   ├── leads_20250112_143022.csv
    │   ├── classified_leads_20250112_143045.json
    │   └── leads_all_20250112_143100.xlsx
    ├── pack_CompanyName_20250112_143200/
    │   └── [pack contents]
    └── pack_CompanyName_20250112_143200.zip
```

## Error Handling

All export functions include comprehensive error handling:

```python
try:
    path, count = export_filtered_csv(leads, filter, project)
    print(f"Success: {count} records exported")
except ValueError as e:
    print(f"Filter error: {e}")  # e.g., "No leads match the filter criteria"
except IOError as e:
    print(f"File write error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

### Large Datasets

For datasets > 10,000 leads:

1. **Use filtering** to reduce export size
2. **Select specific columns** to minimize data
3. **Use CSV format** for fastest processing
4. **Avoid Markdown** for very large datasets (formatting overhead)

### Memory Usage

- CSV: Low memory (streaming write)
- JSON: Moderate memory (in-memory serialization)
- XLSX: High memory (pandas DataFrame conversion)
- Markdown: High memory (string concatenation)

## Best Practices

### 1. Filter Before Export

Always use filters to export only relevant data:

```python
# Good: Export high-value leads only
filter = ExportFilter(min_priority=7.0, has_emails=True)

# Bad: Export everything unfiltered
filter = ExportFilter()  # No filters
```

### 2. Use Appropriate Format

- **CSV**: Spreadsheet analysis, CRM imports
- **JSON**: API integration, data pipelines
- **XLSX**: Excel users, formatted reports
- **Markdown**: Documentation, client reports

### 3. Preview First

Always preview before large exports:

```python
preview, stats = get_export_preview(leads, filter, max_preview=5)
if stats['total_filtered'] > 1000:
    print("Warning: Large export! Consider adding more filters")
```

### 4. Consulting Pack Completeness

Before creating pack, ensure you have all materials:

```python
has_dossier = st.session_state.get("dossier_result") is not None
has_outreach = st.session_state.get("outreach_result") is not None
has_audit = st.session_state.get("audit_result") is not None

if not (has_dossier and has_outreach and has_audit):
    st.warning("Pack incomplete. Generate all materials first.")
```

## Troubleshooting

### Issue: "No leads match the filter criteria"

**Solution:** Relax filter constraints or check data quality

```python
# Check what data exists
print(f"Total leads: {len(leads)}")
print(f"Leads with emails: {sum(1 for l in leads if l.get('emails'))}")
print(f"Business types: {set(l.get('business_type') for l in leads)}")
```

### Issue: Export file not created

**Solution:** Check permissions and disk space

```python
import os
from pathlib import Path

out_dir = Path("out") / project / "leads"
out_dir.mkdir(parents=True, exist_ok=True)
print(f"Export directory: {out_dir}")
print(f"Exists: {out_dir.exists()}")
print(f"Writable: {os.access(out_dir, os.W_OK)}")
```

### Issue: Nested data not displaying in Excel

**Solution:** This is expected behavior. Nested structures are JSON-encoded:

```python
# In Excel, cell will show:
# ["email1@example.com", "email2@example.com"]

# To extract in Excel, use JSON parsing add-ins or Python post-processing
```

## API Reference

### ExportFilter

```python
@dataclass
class ExportFilter:
    min_score: float = 0.0
    max_score: float = 10.0
    min_quality: float = 0.0
    min_fit: float = 0.0
    min_priority: float = 0.0
    business_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    has_emails: Optional[bool] = None
    has_phones: Optional[bool] = None
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None
    columns: Optional[List[str]] = None
```

### Export Functions

All export functions return `Tuple[str, int]` (file_path, record_count):

```python
def export_filtered_csv(
    leads: List[Dict[str, Any]],
    filters: ExportFilter,
    project: str = "default",
    filename_prefix: str = "leads"
) -> Tuple[str, int]

def export_filtered_json(...) -> Tuple[str, int]
def export_filtered_xlsx(...) -> Tuple[str, int]
def export_filtered_markdown(...) -> Tuple[str, int]
```

### Consulting Pack

```python
def create_consulting_pack_zip(
    lead: Dict[str, Any],
    dossier_result: Any = None,
    outreach_result: Any = None,
    audit_result: Any = None,
    project: str = "default"
) -> str  # Returns ZIP file path
```

### Preview Function

```python
def get_export_preview(
    leads: List[Dict[str, Any]],
    filters: ExportFilter,
    max_preview: int = 5
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]
# Returns: (preview_leads, statistics_dict)
```

## Migration from Old Export System

### Old System (exporters.py)

```python
# Old way
from exporters import export_csv, export_json
path = export_csv(leads)  # No filtering, all records
```

### New System (export_advanced.py)

```python
# New way
from export_advanced import export_filtered_csv, ExportFilter

# Same behavior (no filters)
path, count = export_filtered_csv(leads, ExportFilter(), project)

# Or with filtering
filter = ExportFilter(min_score=5.0, has_emails=True)
path, count = export_filtered_csv(leads, filter, project)
```

**Backwards Compatible:** Old export functions still work alongside new system.

## Future Enhancements

Planned features:

1. **PDF Export** - Generate formatted PDF reports
2. **Email Export** - Send exports directly to email
3. **Scheduled Exports** - Automatic periodic exports
4. **Export Templates** - Save filter configurations as templates
5. **Batch Export** - Export multiple filtered views at once
6. **Cloud Upload** - Direct upload to S3, GCS, Dropbox
7. **Excel Formatting** - Rich formatting in XLSX (colors, charts)
8. **Custom Schemas** - User-defined export column mappings

## Support

For issues, questions, or feature requests:
- Check `export_advanced.py` source code
- Review error messages and traceback
- Test with small datasets first
- Verify filter configuration

## License

Same as Lead Hunter Toolkit main license.
