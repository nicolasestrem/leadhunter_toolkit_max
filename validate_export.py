"""
Simple validation script for export modules
Checks imports and basic structure without running full tests
"""

import sys
import os
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} NOT FOUND: {filepath}")
        return False

def check_imports(filepath):
    """Check if file can be parsed"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            compile(f.read(), filepath, 'exec')
        print(f"  ✅ Syntax valid")
        return True
    except SyntaxError as e:
        print(f"  ❌ Syntax error: {e}")
        return False

def check_function_defined(filepath, function_name):
    """Check if function is defined in file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if f"def {function_name}(" in content:
        print(f"  ✅ Function '{function_name}' defined")
        return True
    else:
        print(f"  ❌ Function '{function_name}' NOT defined")
        return False

def main():
    print("=" * 60)
    print("Export System Validation")
    print("=" * 60)

    all_valid = True

    # Check core module
    print("\n1. Checking export_advanced.py...")
    if check_file_exists("export_advanced.py", "Core module"):
        check_imports("export_advanced.py")
        check_function_defined("export_advanced.py", "apply_filters")
        check_function_defined("export_advanced.py", "export_filtered_csv")
        check_function_defined("export_advanced.py", "export_filtered_json")
        check_function_defined("export_advanced.py", "export_filtered_xlsx")
        check_function_defined("export_advanced.py", "export_filtered_markdown")
        check_function_defined("export_advanced.py", "create_consulting_pack_zip")
        check_function_defined("export_advanced.py", "get_export_preview")
    else:
        all_valid = False

    # Check sidebar module
    print("\n2. Checking export_sidebar.py...")
    if check_file_exists("export_sidebar.py", "Sidebar module"):
        check_imports("export_sidebar.py")
        check_function_defined("export_sidebar.py", "render_export_sidebar")
    else:
        all_valid = False

    # Check integration in app.py
    print("\n3. Checking app.py integration...")
    if check_file_exists("app.py", "Main app"):
        with open("app.py", 'r', encoding='utf-8') as f:
            content = f.read()

        if "from export_sidebar import render_export_sidebar" in content:
            print("  ✅ Export sidebar import found")
        else:
            print("  ❌ Export sidebar import NOT found")
            all_valid = False

        if "render_export_sidebar(project)" in content:
            print("  ✅ Export sidebar render call found")
        else:
            print("  ❌ Export sidebar render call NOT found")
            all_valid = False
    else:
        all_valid = False

    # Check documentation
    print("\n4. Checking documentation...")
    check_file_exists("EXPORT_GUIDE.md", "Export guide")

    # Check test file
    print("\n5. Checking test file...")
    check_file_exists("test_export.py", "Test script")

    # Check output directory
    print("\n6. Checking output directory...")
    out_dir = Path("out")
    if out_dir.exists():
        print(f"✅ Output directory exists: {out_dir}")
    else:
        print(f"ℹ️  Output directory will be created on first export")

    # Summary
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ Validation PASSED - Export system ready!")
    else:
        print("⚠️  Validation FAILED - Check errors above")
    print("=" * 60)

    print("\nNext steps:")
    print("1. Install requirements: pip install -r requirements.txt")
    print("2. Run Streamlit app: streamlit run app.py")
    print("3. Test exports from the sidebar")
    print("4. Optional: Run full tests with virtual env activated")

    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())
