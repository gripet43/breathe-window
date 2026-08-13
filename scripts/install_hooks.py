#!/usr/bin/env python3
"""
Install Git pre-commit hook for automated regression prevention.
"""

import os
import stat

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
HOOKS_DIR = os.path.join(PROJECT_ROOT, ".git", "hooks")
PRE_COMMIT_PATH = os.path.join(HOOKS_DIR, "pre-commit")

HOOK_SCRIPT = """#!/bin/bash
# Breathe-Window Automated Pre-Commit Regression Check
echo "🔍 [GIT HOOK] Running Breathe-Window regression verification..."

python3 scripts/verify_project.py
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo "❌ [GIT HOOK] Commit rejected! Please fix the errors above before committing."
  echo "💡 Tip: You can run 'python3 scripts/build.py' to automatically sync and fix common issues."
  exit 1
fi

echo "✅ [GIT HOOK] Verification passed! Proceeding with commit."
exit 0
"""

def main():
    if not os.path.exists(HOOKS_DIR):
        print(f"No .git/hooks directory found at {HOOKS_DIR}. Skipping.")
        return
        
    with open(PRE_COMMIT_PATH, "w", encoding="utf-8") as f:
        f.write(HOOK_SCRIPT)
        
    st = os.stat(PRE_COMMIT_PATH)
    os.chmod(PRE_COMMIT_PATH, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"✓ Git pre-commit hook installed successfully at {PRE_COMMIT_PATH}")

if __name__ == "__main__":
    main()
