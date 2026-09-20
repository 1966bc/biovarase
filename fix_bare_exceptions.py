# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""
Automated tool to fix bare exception handlers in Python files.

This script fixes two patterns:
1. except Exception: → except Exception as e:
2. except (Type1, Type2): → except (Type1, Type2) as e:

Creates automatic backups before modification.

Usage:
    python3 fix_bare_exceptions.py file1.py file2.py ...
"""
import re
import sys
import shutil
from pathlib import Path
from typing import Tuple


def fix_bare_exceptions(filepath: str) -> Tuple[int, bool]:
    """
    Fix bare exception handlers in a Python file.

    Args:
        filepath: Path to Python file to fix

    Returns:
        Tuple of (fixes_count, success)
    """
    try:
        path = Path(filepath)

        # Read file
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        total_fixes = 0

        # Pattern 1: except Exception:
        pattern1 = r'(\s+)except Exception:\s*\n'
        replacement1 = r'\1except Exception as e:\n'
        content, count1 = re.subn(pattern1, replacement1, content)
        total_fixes += count1

        # Pattern 2: except (Type1, Type2, ...):
        pattern2 = r'(\s+)except \(([^)]+)\):\s*\n'
        replacement2 = r'\1except (\2) as e:\n'
        content, count2 = re.subn(pattern2, replacement2, content)
        total_fixes += count2

        if total_fixes > 0:
            # Create backup
            backup_path = path.with_suffix('.py.bak')
            shutil.copy2(path, backup_path)

            # Write fixed content
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ Fixed {total_fixes} exception handler(s) in: {filepath}")
            print(f"   Backup created: {backup_path}")
            return total_fixes, True
        else:
            print(f"ℹ️  No changes needed: {filepath}")
            return 0, True

    except Exception as e:
        print(f"❌ Failed to process {filepath}")
        print(f"❌ Error: {e}")
        return 0, False


def main():
    """Process all files provided as command-line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python3 fix_bare_exceptions.py file1.py file2.py ...")
        sys.exit(1)

    total_files = 0
    total_fixes = 0
    failed_files = []

    for filepath in sys.argv[1:]:
        try:
            # Skip if not a file
            if not Path(filepath).is_file():
                print(f"⚠️  Skipping (not a file): {filepath}")
                continue

            fixes, success = fix_bare_exceptions(filepath)
            total_files += 1
            total_fixes += fixes

            if not success:
                failed_files.append(filepath)
        except Exception as e:
            print(f"❌ Failed to process file")
            print(f"❌ Error reading file: {e}")
            failed_files.append(filepath)

    # Summary
    print("\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   Files processed: {total_files}")
    print(f"   Total fixes: {total_fixes}")
    print(f"   Failed files: {len(failed_files)}")

    if failed_files:
        print("\n❌ Failed files:")
        for f in failed_files:
            print(f"   - {f}")

    print("="*60)


if __name__ == "__main__":
    main()
