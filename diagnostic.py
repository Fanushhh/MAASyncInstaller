#!/usr/bin/env python3
"""
MAA Redux Sync Diagnostic Tool
"""

import sys
import json
import platform
from pathlib import Path

def main():
    print("=== MAA Redux Sync Diagnostic ===")
    print(f"Platform: {platform.system()}")
    print(f"Python version: {sys.version}")
    print()

    # Check if we're in the right directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")

    # Check for key files
    files_to_check = [
        "maa_redux_installer.py",
        "maa_sync.py",
        "config.json"
    ]

    print("\n=== File Check ===")
    for filename in files_to_check:
        file_path = current_dir / filename
        if file_path.exists():
            print(f"✅ {filename} - Found")
            if filename == "config.json":
                try:
                    with open(file_path, 'r') as f:
                        config = json.load(f)
                    print(f"   - Dropbox token length: {len(config.get('dropbox_token', ''))}")
                    print(f"   - Save file path: {config.get('save_file_path', 'Not set')}")
                    print(f"   - App name: {config.get('app_name', 'Not set')}")
                except Exception as e:
                    print(f"   - ❌ Error reading config: {e}")
        else:
            print(f"❌ {filename} - Missing")

    # Check Dropbox module
    print("\n=== Module Check ===")
    try:
        import dropbox
        print("✅ Dropbox module - Available")

        # Test with a dummy token to see the error format
        try:
            dbx = dropbox.Dropbox("dummy_token")
            dbx.users_get_current_account()
        except Exception as e:
            print(f"   - Expected error with dummy token: {type(e).__name__}")

    except ImportError:
        print("❌ Dropbox module - Not installed")
        print("   Run: pip install dropbox")

    # Check psutil module
    try:
        import psutil
        print("✅ psutil module - Available")
    except ImportError:
        print("❌ psutil module - Not installed")
        print("   Run: pip install psutil")

    print("\n=== Permissions Check ===")
    try:
        test_file = current_dir / "test_write.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        test_file.unlink()
        print("✅ Write permissions - OK")
    except Exception as e:
        print(f"❌ Write permissions - Error: {e}")

    print("\n=== Token Analysis ===")
    print("If you're having token issues:")
    print("1. Dropbox tokens should be ~140-150 characters long")
    print("2. They should start with 'sl.' for app tokens")
    print("3. Make sure there are no extra spaces or newlines")
    print("4. Ensure your Dropbox app has the correct permissions")

    print("\nDone! Share this output for further assistance.")

if __name__ == "__main__":
    main()