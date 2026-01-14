#!/usr/bin/env python3
"""
Syntax Checker for MAMS
Validates Python files have correct syntax before LibCST processing
"""

import sys
import ast
from pathlib import Path
from typing import List, Tuple

def check_file_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Try to parse with ast first (more lenient)
        try:
            ast.parse(source)
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        
        # Try to compile
        try:
            compile(source, str(file_path), 'exec')
        except SyntaxError as e:
            return False, f"Compilation error at line {e.lineno}: {e.msg}"
        
        # Check for incomplete blocks
        lines = source.splitlines()
        try_count = 0
        except_finally_count = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('try:'):
                try_count += 1
            elif stripped.startswith(('except', 'finally:')):
                except_finally_count += 1
        
        if try_count > except_finally_count:
            return False, f"Incomplete try block - {try_count} try statements but only {except_finally_count} except/finally clauses"
        
        return True, "✅ Syntax valid"
        
    except Exception as e:
        return False, f"Error reading file: {e}"

def check_directory(directory: Path, extensions: List[str] = ['.py']) -> None:
    """Check all Python files in a directory."""
    files = []
    for ext in extensions:
        files.extend(directory.rglob(f'*{ext}'))
    
    print(f"Checking {len(files)} Python files for syntax errors...")
    print("=" * 60)
    
    errors = []
    for file_path in files:
        valid, message = check_file_syntax(file_path)
        if not valid:
            errors.append((file_path, message))
            print(f"❌ {file_path.relative_to(directory)}")
            print(f"   {message}")
    
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ Found {len(errors)} files with syntax errors")
        print("\nThese files will fail LibCST validation:")
        for path, msg in errors[:10]:  # Show first 10
            print(f"  - {path.name}: {msg}")
    else:
        print("✅ All files have valid syntax")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Python syntax before LibCST validation")
    parser.add_argument('path', nargs='?', default='/app/arkyvus', help='File or directory to check')
    parser.add_argument('--fix-try-blocks', action='store_true', help='Attempt to fix incomplete try blocks')
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        valid, message = check_file_syntax(path)
        print(message)
        sys.exit(0 if valid else 1)
    elif path.is_dir():
        check_directory(path)
    else:
        print(f"Path not found: {path}")
        sys.exit(1)

if __name__ == "__main__":
    main()