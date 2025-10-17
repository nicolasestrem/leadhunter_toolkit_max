#!/usr/bin/env python3
"""
Integration script for enhanced sidebar
Replaces the sidebar section in app.py with enhanced version
"""

import sys
from pathlib import Path

def integrate_sidebar():
    """Integrate the enhanced sidebar into the main application file.

    This function replaces the existing sidebar section in 'app.py' with the
    enhanced version from 'sidebar_enhanced.py'. It creates a backup of the
    original 'app.py' before making any modifications.
    """

    # File paths
    app_path = Path("app.py")
    enhanced_path = Path("sidebar_enhanced.py")
    backup_path = Path("app.py.backup")

    # Check files exist
    if not app_path.exists():
        print("❌ Error: app.py not found")
        return False

    if not enhanced_path.exists():
        print("❌ Error: sidebar_enhanced.py not found")
        return False

    # Read files
    print("📖 Reading files...")
    with open(app_path, 'r', encoding='utf-8') as f:
        app_lines = f.readlines()

    with open(enhanced_path, 'r', encoding='utf-8') as f:
        enhanced_content = f.read()

    # Remove the comment header from enhanced sidebar
    enhanced_lines = []
    skip_header = True
    for line in enhanced_content.split('\n'):
        if skip_header:
            if line.strip().startswith('# ---- Sidebar ----'):
                skip_header = False
                enhanced_lines.append(line + '\n')
            continue
        enhanced_lines.append(line + '\n')

    # Create backup
    print("💾 Creating backup: app.py.backup")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.writelines(app_lines)

    # Calculate line ranges (0-indexed for list operations)
    # Lines 275-471 in editor = indices 274-470 in list
    start_idx = 274  # Line 275
    end_idx = 471    # Line 472 (exclusive)

    # Verify we're replacing the right section
    if not app_lines[start_idx].strip().startswith('# ---- Sidebar ----'):
        print("⚠️  Warning: Line 275 doesn't start with '# ---- Sidebar ----'")
        print(f"   Found: {app_lines[start_idx].strip()[:50]}")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Aborted")
            return False

    # Replace the section
    print(f"🔄 Replacing lines {start_idx + 1}-{end_idx}...")
    new_app_lines = app_lines[:start_idx] + enhanced_lines + app_lines[end_idx:]

    # Write the new file
    print("💾 Writing enhanced app.py...")
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_app_lines)

    # Summary
    print("\n✅ Integration complete!")
    print(f"   • Backup saved: {backup_path}")
    print(f"   • Original lines: {len(app_lines)}")
    print(f"   • New lines: {len(new_app_lines)}")
    print(f"   • Difference: {len(new_app_lines) - len(app_lines):+d} lines")

    print("\n📋 Next steps:")
    print("   1. Test the app: streamlit run app.py")
    print("   2. Verify vertical presets work")
    print("   3. Verify plugin management works")
    print("   4. If issues occur, restore: cp app.py.backup app.py")

    return True


def rollback():
    """Roll back to the backup version of the application file.

    This function restores the 'app.py' file from the 'app.py.backup' file,
    reverting any changes made by the integration script.
    """
    app_path = Path("app.py")
    backup_path = Path("app.py.backup")

    if not backup_path.exists():
        print("❌ Error: No backup found (app.py.backup)")
        return False

    print("🔄 Rolling back to backup...")
    with open(backup_path, 'r', encoding='utf-8') as f:
        backup_content = f.read()

    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(backup_content)

    print("✅ Rollback complete! app.py restored from backup.")
    return True


def show_help():
    """Show the usage help message for the script."""
    print("""
Enhanced Sidebar Integration Script
====================================

Usage:
    python integrate_sidebar.py [command]

Commands:
    integrate    - Integrate enhanced sidebar into app.py (default)
    rollback     - Restore app.py from backup
    help         - Show this help message

Examples:
    python integrate_sidebar.py
    python integrate_sidebar.py integrate
    python integrate_sidebar.py rollback

Notes:
    • Creates backup at app.py.backup before modifying
    • Replaces lines 275-471 in app.py
    • Enhanced sidebar from sidebar_enhanced.py
    • See SIDEBAR_ENHANCEMENTS.md for details
    """)


if __name__ == "__main__":
    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "integrate"

    if command == "integrate":
        success = integrate_sidebar()
        sys.exit(0 if success else 1)

    elif command == "rollback":
        success = rollback()
        sys.exit(0 if success else 1)

    elif command in ["help", "-h", "--help"]:
        show_help()
        sys.exit(0)

    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python integrate_sidebar.py help' for usage")
        sys.exit(1)
