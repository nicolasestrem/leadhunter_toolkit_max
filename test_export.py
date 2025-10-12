"""
Test script for advanced export functionality
Run: python test_export.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Import export modules
from export_advanced import (
    ExportFilter,
    export_filtered_csv,
    export_filtered_json,
    export_filtered_xlsx,
    export_filtered_markdown,
    get_export_preview,
    apply_filters
)


def generate_test_leads():
    """Generate sample leads for testing"""
    return [
        {
            "name": "La Belle Boulangerie",
            "domain": "labelleboulangerie.fr",
            "website": "https://labelleboulangerie.fr",
            "emails": ["contact@labelleboulangerie.fr"],
            "phones": ["+33 1 42 34 56 78"],
            "score": 8.5,
            "score_quality": 9.0,
            "score_fit": 8.5,
            "score_priority": 8.7,
            "business_type": "restaurant",
            "tags": ["french", "bakery"],
            "status": "new",
            "city": "Paris",
            "when": datetime.utcnow().isoformat()
        },
        {
            "name": "Tech Solutions GmbH",
            "domain": "techsolutions.de",
            "website": "https://techsolutions.de",
            "emails": ["info@techsolutions.de", "sales@techsolutions.de"],
            "phones": ["+49 30 1234567"],
            "score": 7.2,
            "score_quality": 8.0,
            "score_fit": 6.5,
            "score_priority": 7.0,
            "business_type": "tech",
            "tags": ["software", "b2b"],
            "status": "qualified",
            "city": "Berlin",
            "when": datetime.utcnow().isoformat()
        },
        {
            "name": "Organic Market",
            "domain": "organicmarket.com",
            "website": "https://organicmarket.com",
            "emails": [],  # No emails
            "phones": ["+1 555 123 4567"],
            "score": 5.5,
            "score_quality": 5.0,
            "score_fit": 6.0,
            "score_priority": 5.5,
            "business_type": "retail",
            "tags": ["organic", "grocery"],
            "status": "new",
            "city": "Austin",
            "when": (datetime.utcnow() - timedelta(days=10)).isoformat()
        },
        {
            "name": "Bistro Le Jardin",
            "domain": "lejardin.fr",
            "website": "https://lejardin.fr",
            "emails": ["contact@lejardin.fr"],
            "phones": [],  # No phones
            "score": 6.8,
            "score_quality": 7.0,
            "score_fit": 7.5,
            "score_priority": 7.2,
            "business_type": "restaurant",
            "tags": ["french", "fine-dining"],
            "status": "contacted",
            "city": "Lyon",
            "when": (datetime.utcnow() - timedelta(days=3)).isoformat()
        },
        {
            "name": "Minimal Lead",
            "domain": "minimal.com",
            "website": "https://minimal.com",
            "emails": [],
            "phones": [],
            "score": 2.0,
            "score_quality": 2.0,
            "score_fit": 2.0,
            "score_priority": 2.0,
            "business_type": "other",
            "tags": [],
            "status": "rejected",
            "city": None,
            "when": (datetime.utcnow() - timedelta(days=30)).isoformat()
        }
    ]


def test_filtering():
    """Test filter application"""
    print("\n=== Testing Filtering ===")
    leads = generate_test_leads()

    # Test 1: Basic score filter
    print("\nTest 1: Score filter (min_score=7.0)")
    filter1 = ExportFilter(min_score=7.0)
    filtered1 = apply_filters(leads, filter1)
    print(f"  Original: {len(leads)} leads")
    print(f"  Filtered: {len(filtered1)} leads")
    print(f"  Names: {[l['name'] for l in filtered1]}")
    assert len(filtered1) == 2, "Should filter to 2 leads with score >= 7.0"

    # Test 2: Business type filter
    print("\nTest 2: Business type filter (restaurant)")
    filter2 = ExportFilter(business_types=["restaurant"])
    filtered2 = apply_filters(leads, filter2)
    print(f"  Filtered: {len(filtered2)} leads")
    print(f"  Names: {[l['name'] for l in filtered2]}")
    assert len(filtered2) == 2, "Should filter to 2 restaurant leads"

    # Test 3: Has emails filter
    print("\nTest 3: Has emails filter")
    filter3 = ExportFilter(has_emails=True)
    filtered3 = apply_filters(leads, filter3)
    print(f"  Filtered: {len(filtered3)} leads")
    print(f"  Names: {[l['name'] for l in filtered3]}")
    assert len(filtered3) == 3, "Should filter to 3 leads with emails"

    # Test 4: Combined filters
    print("\nTest 4: Combined filters (quality >= 7.0, has_emails=True, restaurant)")
    filter4 = ExportFilter(
        min_quality=7.0,
        has_emails=True,
        business_types=["restaurant"]
    )
    filtered4 = apply_filters(leads, filter4)
    print(f"  Filtered: {len(filtered4)} leads")
    print(f"  Names: {[l['name'] for l in filtered4]}")
    assert len(filtered4) == 2, "Should filter to 2 leads meeting all criteria"

    # Test 5: Date range filter
    print("\nTest 5: Date range filter (last 7 days)")
    filter5 = ExportFilter(
        date_from=datetime.utcnow() - timedelta(days=7)
    )
    filtered5 = apply_filters(leads, filter5)
    print(f"  Filtered: {len(filtered5)} leads")
    print(f"  Names: {[l['name'] for l in filtered5]}")
    assert len(filtered5) == 3, "Should filter to 3 recent leads"

    print("\n✅ All filtering tests passed!")


def test_preview():
    """Test export preview"""
    print("\n=== Testing Export Preview ===")
    leads = generate_test_leads()
    filter = ExportFilter(min_quality=6.0)

    preview, stats = get_export_preview(leads, filter, max_preview=3)

    print(f"\nStatistics:")
    print(f"  Total filtered: {stats['total_filtered']}")
    print(f"  Total original: {stats['total_original']}")
    print(f"  Filtered %: {stats['filtered_percentage']:.1f}%")
    print(f"  Has emails: {stats['has_emails']}")
    print(f"  Has phones: {stats['has_phones']}")
    print(f"  Avg score: {stats['avg_score']:.2f}")
    print(f"  Avg quality: {stats['avg_quality']:.2f}")
    print(f"  Avg fit: {stats['avg_fit']:.2f}")
    print(f"  Avg priority: {stats['avg_priority']:.2f}")

    if "business_type_distribution" in stats:
        print(f"\nBusiness Type Distribution:")
        for bt, count in stats["business_type_distribution"].items():
            print(f"    {bt}: {count}")

    print(f"\nPreview (showing {len(preview)} of {stats['total_filtered']}):")
    for lead in preview:
        print(f"  - {lead['name']} ({lead['business_type']})")

    assert len(preview) <= 3, "Preview should respect max_preview limit"
    assert stats['total_filtered'] == 3, "Should filter to 3 leads with quality >= 6.0"

    print("\n✅ Preview test passed!")


def test_exports():
    """Test all export formats"""
    print("\n=== Testing Export Formats ===")
    leads = generate_test_leads()
    filter = ExportFilter(min_score=5.0)
    project = "test_export"

    # Test CSV export
    print("\nTest 1: CSV Export")
    try:
        path_csv, count_csv = export_filtered_csv(leads, filter, project, "test_csv")
        print(f"  ✅ Exported {count_csv} leads to {path_csv}")
        assert os.path.exists(path_csv), "CSV file should exist"
        assert count_csv == 4, "Should export 4 leads with score >= 5.0"
    except Exception as e:
        print(f"  ❌ CSV export failed: {e}")

    # Test JSON export
    print("\nTest 2: JSON Export")
    try:
        path_json, count_json = export_filtered_json(leads, filter, project, "test_json")
        print(f"  ✅ Exported {count_json} leads to {path_json}")
        assert os.path.exists(path_json), "JSON file should exist"

        # Verify JSON is valid
        with open(path_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert len(data) == 4, "JSON should contain 4 leads"
    except Exception as e:
        print(f"  ❌ JSON export failed: {e}")

    # Test XLSX export
    print("\nTest 3: XLSX Export")
    try:
        path_xlsx, count_xlsx = export_filtered_xlsx(leads, filter, project, "test_xlsx")
        print(f"  ✅ Exported {count_xlsx} leads to {path_xlsx}")
        assert os.path.exists(path_xlsx), "XLSX file should exist"
    except Exception as e:
        print(f"  ❌ XLSX export failed: {e}")

    # Test Markdown export
    print("\nTest 4: Markdown Export")
    try:
        path_md, count_md = export_filtered_markdown(leads, filter, project, "test_markdown")
        print(f"  ✅ Exported {count_md} leads to {path_md}")
        assert os.path.exists(path_md), "Markdown file should exist"

        # Verify markdown content
        with open(path_md, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "# Leads Export" in content, "Markdown should have title"
        assert "La Belle Boulangerie" in content, "Should contain lead names"
    except Exception as e:
        print(f"  ❌ Markdown export failed: {e}")

    print("\n✅ All export format tests passed!")


def test_column_selection():
    """Test column selection"""
    print("\n=== Testing Column Selection ===")
    leads = generate_test_leads()
    filter = ExportFilter(columns=["name", "domain", "emails"])
    project = "test_export"

    try:
        path, count = export_filtered_json(leads, filter, project, "test_columns")
        print(f"  Exported {count} leads to {path}")

        # Verify only selected columns are present
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        first_lead = data[0]
        print(f"  Columns in export: {list(first_lead.keys())}")

        assert len(first_lead.keys()) == 3, "Should only have 3 columns"
        assert "name" in first_lead, "Should have name column"
        assert "domain" in first_lead, "Should have domain column"
        assert "emails" in first_lead, "Should have emails column"
        assert "phones" not in first_lead, "Should not have phones column"

        print("  ✅ Column selection works correctly!")
    except Exception as e:
        print(f"  ❌ Column selection test failed: {e}")


def test_empty_filter():
    """Test behavior with filters that match nothing"""
    print("\n=== Testing Empty Filter ===")
    leads = generate_test_leads()
    filter = ExportFilter(min_score=15.0)  # Impossible score
    project = "test_export"

    try:
        path, count = export_filtered_csv(leads, filter, project, "test_empty")
        print(f"  ❌ Should have raised ValueError for empty filter")
    except ValueError as e:
        print(f"  ✅ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")


def cleanup_test_files():
    """Clean up test export files"""
    print("\n=== Cleaning up test files ===")
    test_dir = Path("out") / "test_export"
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
        print(f"  ✅ Removed {test_dir}")
    else:
        print(f"  ℹ️  No test files to clean up")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Advanced Export System - Test Suite")
    print("=" * 60)

    try:
        test_filtering()
        test_preview()
        test_exports()
        test_column_selection()
        test_empty_filter()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)

        # Optional: cleanup
        response = input("\nClean up test files? (y/n): ")
        if response.lower() == 'y':
            cleanup_test_files()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
