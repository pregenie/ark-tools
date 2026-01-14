#!/usr/bin/env python3
"""
Phase 1: LibCST Round-Trip Validator
The "Do No Harm" Foundation - Ensures we can read/write files perfectly
Must pass 100% before proceeding to Phase 2
"""

import libcst as cst
import hashlib
import difflib
from pathlib import Path
from typing import Tuple, List
import sys

class RoundTripValidator:
    """
    Validates that LibCST can round-trip files without ANY changes.
    This is the foundation - if this fails, nothing else will work.
    """
    
    def __init__(self):
        self.test_files = []
        self.results = []
        self.failed_files = []
        
    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate that a file can be round-tripped without changes.
        
        Returns:
            Tuple of (success, message)
        """
        print(f"Validating: {file_path.name}")
        
        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Calculate original hash
            original_hash = hashlib.sha256(original_content.encode()).hexdigest()
            
            # Parse with LibCST
            tree = cst.parse_module(original_content)
            
            # Convert back to code
            roundtrip_content = tree.code
            
            # Calculate roundtrip hash
            roundtrip_hash = hashlib.sha256(roundtrip_content.encode()).hexdigest()
            
            # Compare
            if original_hash == roundtrip_hash:
                return True, "✅ Perfect round-trip - all bytes preserved"
            else:
                # Something changed - show diff
                diff = self._generate_diff(original_content, roundtrip_content)
                # Save detailed error for inspection
                error_file = Path('/app/.migration/validation_error.txt')
                error_file.parent.mkdir(exist_ok=True)
                with open(error_file, 'w') as f:
                    f.write(f"File: {file_path}\n")
                    f.write(f"Original hash: {original_hash}\n")
                    f.write(f"Roundtrip hash: {roundtrip_hash}\n")
                    f.write(f"\nDiff:\n{diff}\n")
                    f.write(f"\nFirst 500 chars of original:\n{original_content[:500]}\n")
                    f.write(f"\nFirst 500 chars of roundtrip:\n{roundtrip_content[:500]}\n")
                return False, f"❌ Round-trip failed (see /app/.migration/validation_error.txt)\n{diff[:500]}"
                
        except Exception as e:
            # Save parse error details
            error_file = Path('/app/.migration/validation_error.txt')
            error_file.parent.mkdir(exist_ok=True)
            with open(error_file, 'w') as f:
                f.write(f"File: {file_path}\n")
                f.write(f"Parse error: {str(e)}\n")
                f.write(f"Error type: {type(e).__name__}\n")
                import traceback
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
            return False, f"❌ Parse error: {str(e)}"
    
    def _generate_diff(self, original: str, roundtrip: str) -> str:
        """Generate a readable diff between original and roundtrip"""
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            roundtrip.splitlines(keepends=True),
            fromfile='original',
            tofile='roundtrip',
            n=3
        ))
        return ''.join(diff_lines[:50])  # Limit output
    
    def validate_directory(self, directory: Path, sample_size: int = 50) -> bool:
        """
        Validate a sample of Python files from a directory.
        
        Returns:
            True if ALL files pass perfectly
        """
        py_files = list(directory.rglob('*.py'))[:sample_size]
        
        if not py_files:
            print(f"No Python files found in {directory}")
            return False
        
        print(f"\nValidating {len(py_files)} files from {directory}")
        print("=" * 60)
        
        all_passed = True
        for file_path in py_files:
            success, message = self.validate_file(file_path)
            self.results.append({
                'file': str(file_path),
                'success': success,
                'message': message
            })
            if not success:
                all_passed = False
                self.failed_files.append(str(file_path))
                print(f"  ❌ {file_path.name}")
                # Uncomment to see diff details:
                # print(message)
            else:
                print(f"  ✅ {file_path.name}")
        
        self._generate_report()
        return all_passed
    
    def validate_edge_cases(self) -> bool:
        """Test specific edge cases that often break parsers"""
        print("\nTesting Edge Cases")
        print("=" * 60)
        
        edge_cases = [
            ("Inline comments", '''def function():
    x = 5  # This is a comment
    return x  # Another comment
'''),
            ("Docstrings", '''def function():
    """
    This is a docstring.
    
    Args:
        x: Something
    """
    pass
'''),
            ("Complex decorators", '''@decorator1
@decorator2(arg1, arg2)
@decorator3.method()
def function():
    pass
'''),
            ("Type hints", '''def function(
    x: int,  # First param
    y: str = "default",  # Second param
) -> Optional[Dict[str, Any]]:  # Return type
    pass
'''),
            ("Global constants", '''DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 5

class Service:
    TIMEOUT = DEFAULT_TIMEOUT  # Use global
'''),
            ("F-strings", '''name = "world"
message = f"Hello {name}!"
complex = f"{name.upper()}: {2 + 2}"
'''),
        ]
        
        all_passed = True
        for name, code in edge_cases:
            try:
                tree = cst.parse_module(code)
                roundtrip = tree.code
                
                if code == roundtrip:
                    print(f"  ✅ {name}")
                else:
                    print(f"  ❌ {name} - content changed")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {name} - parse error: {e}")
                all_passed = False
        
        return all_passed
    
    def _generate_report(self):
        """Generate validation report"""
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print("\n" + "=" * 60)
        print("LIBCST ROUND-TRIP VALIDATION REPORT")
        print("=" * 60)
        print(f"Files tested: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        if total > 0:
            print(f"Success rate: {(passed/total*100):.1f}%")
        
        if self.failed_files:
            print("\n❌ FAILED FILES:")
            for f in self.failed_files[:10]:
                print(f"  - {f}")
            if len(self.failed_files) > 10:
                print(f"  ... and {len(self.failed_files) - 10} more")
        
        if total > 0 and passed == total:
            print("\n✅ ALL FILES PASSED - LibCST is ready for production!")
            print("You can proceed to Phase 2: Component Extraction")
        else:
            print("\n❌ VALIDATION FAILED - DO NOT PROCEED")
            print("LibCST configuration needs adjustment before continuing")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MAMS Phase 1: LibCST Round-Trip Validator")
    parser.add_argument('--sample-size', type=int, default=50, help='Number of files to validate')
    parser.add_argument('--directory', type=str, default='/app/arkyvus', help='Directory to validate')
    parser.add_argument('--skip-edge-cases', action='store_true', help='Skip edge case tests')
    args = parser.parse_args()
    
    validator = RoundTripValidator()
    
    print("Phase 1: LibCST Round-Trip Validation")
    print("=" * 60)
    
    # First test edge cases unless skipped
    edge_pass = True
    if not args.skip_edge_cases:
        edge_pass = validator.validate_edge_cases()
    
    # Then test actual codebase
    arkyvus_dir = Path(args.directory)
    if arkyvus_dir.exists():
        codebase_pass = validator.validate_directory(arkyvus_dir, sample_size=args.sample_size)
    else:
        print(f"Directory {arkyvus_dir} not found")
        codebase_pass = False
    
    # Save completion marker for status tracking
    migration_dir = Path('/app/.migration')
    migration_dir.mkdir(exist_ok=True)
    
    # Final verdict
    print("\n" + "=" * 60)
    if edge_pass and codebase_pass:
        print("✅ PHASE 1 COMPLETE - SAFE TO PROCEED")
        print("LibCST can safely read and write your codebase")
        (migration_dir / 'mams_phase1.complete').touch()
        sys.exit(0)
    else:
        print("❌ PHASE 1 FAILED - DO NOT PROCEED")
        print("Fix LibCST issues before moving to Phase 2")
        sys.exit(1)

if __name__ == "__main__":
    main()