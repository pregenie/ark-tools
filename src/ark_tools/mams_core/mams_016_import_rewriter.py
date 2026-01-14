#!/usr/bin/env python3
"""
MAMS-016: Import Resolution and Rewriting System
Handles all import path updates after file moves to maintain working codebase
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from arkyvus.utils.debug_logger import debug_log

@dataclass
class ImportUpdate:
    """Represents an import that needs to be updated"""
    file_path: str
    line_number: int
    old_import: str
    new_import: str
    import_type: str  # 'relative', 'alias', 'absolute'
    is_type_only: bool

@dataclass
class FileMove:
    """Represents a file being moved"""
    from_path: str
    to_path: str
    from_domain: str
    to_domain: str

@dataclass
class ImportRewritePlan:
    """Complete plan for rewriting imports"""
    file_moves: List[FileMove]
    import_updates: List[ImportUpdate]
    tsconfig_updates: Dict[str, str]
    affected_files: Set[str]
    total_updates: int
    
@dataclass
class TsConfigPaths:
    """TypeScript config path mappings"""
    base_url: str
    paths: Dict[str, List[str]]
    

class ImportRewriter:
    """
    Production-grade import rewriter for TypeScript/React files
    Handles relative imports, aliases, and maintains tsconfig paths
    """
    
    def __init__(self):
        self.tsconfig_paths = self._load_tsconfig_paths()
        self.move_mapping: Dict[str, str] = {}  # old path -> new path
        self.import_cache: Dict[str, List[str]] = {}  # file -> imports
        
    def _load_tsconfig_paths(self) -> TsConfigPaths:
        """Load TypeScript config path mappings"""
        tsconfig_locations = [
            '/app/client/tsconfig.json',
            '/Users/pregenie/Development/arkyvus_project/client/tsconfig.json',
            './client/tsconfig.json'
        ]
        
        for location in tsconfig_locations:
            tsconfig_path = Path(location)
            if tsconfig_path.exists():
                try:
                    config = json.loads(tsconfig_path.read_text())
                    compiler_options = config.get('compilerOptions', {})
                    
                    # Fix: Anchor paths to project root
                    base_url = compiler_options.get('baseUrl', '.')
                    if not base_url.startswith('/'):
                        base_url = str(tsconfig_path.parent / base_url)
                    
                    paths = compiler_options.get('paths', {})
                    
                    # Convert relative paths to absolute
                    absolute_paths = {}
                    for alias, targets in paths.items():
                        absolute_targets = []
                        for target in targets:
                            if not target.startswith('/'):
                                absolute_targets.append(str(Path(base_url) / target))
                            else:
                                absolute_targets.append(target)
                        absolute_paths[alias] = absolute_targets
                    
                    return TsConfigPaths(
                        base_url=base_url,
                        paths=absolute_paths
                    )
                except Exception as e:
                    debug_log.error_trace(f"Failed to load tsconfig from {location}", exception=e)
        
        # Default paths if no tsconfig found
        return TsConfigPaths(
            base_url='/app/client/src',
            paths={
                '@/*': ['/app/client/src/*'],
                '@/components/*': ['/app/client/src/components/*'],
                '@/services/*': ['/app/client/src/services/*'],
                '@/utils/*': ['/app/client/src/utils/*']
            }
        )
    
    async def create_rewrite_plan(self, file_moves: List[FileMove]) -> ImportRewritePlan:
        """
        Create comprehensive plan for rewriting imports
        """
        debug_log.api(f"Creating rewrite plan for {len(file_moves)} file moves", level="INFO")
        
        # Build move mapping
        self.move_mapping = {move.from_path: move.to_path for move in file_moves}
        
        # Find all files that need updates
        affected_files = await self._find_affected_files(file_moves)
        
        # Generate import updates for each affected file
        all_updates = []
        for file_path in affected_files:
            updates = await self._generate_file_updates(file_path, file_moves)
            all_updates.extend(updates)
        
        # Check if tsconfig needs updates
        tsconfig_updates = self._generate_tsconfig_updates(file_moves)
        
        return ImportRewritePlan(
            file_moves=file_moves,
            import_updates=all_updates,
            tsconfig_updates=tsconfig_updates,
            affected_files=affected_files,
            total_updates=len(all_updates)
        )
    
    async def _find_affected_files(self, file_moves: List[FileMove]) -> Set[str]:
        """Find all files affected by the moves"""
        affected = set()
        
        # Files being moved are affected
        for move in file_moves:
            affected.add(move.to_path)
        
        # Find all TypeScript/React files that might import moved files
        search_dirs = [
            '/app/client/src',
            '/Users/pregenie/Development/arkyvus_project/client/src'
        ]
        
        for search_dir in search_dirs:
            search_path = Path(search_dir)
            if search_path.exists():
                for file_path in search_path.rglob('*.ts*'):
                    if file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                        # Check if this file imports any moved files
                        if await self._file_imports_moved_files(file_path, file_moves):
                            affected.add(str(file_path))
                break
        
        return affected
    
    async def _file_imports_moved_files(self, file_path: Path, 
                                       file_moves: List[FileMove]) -> bool:
        """Check if a file imports any of the moved files"""
        try:
            content = file_path.read_text()
            
            for move in file_moves:
                # Check various import patterns
                moved_file_patterns = self._get_import_patterns_for_file(move.from_path)
                
                for pattern in moved_file_patterns:
                    if pattern in content:
                        return True
                        
        except Exception as e:
            debug_log.error_trace(f"Error checking imports in {file_path}", exception=e)
        
        return False
    
    def _get_import_patterns_for_file(self, file_path: str) -> List[str]:
        """Get possible import patterns for a file"""
        patterns = []
        
        # Remove extension
        path_no_ext = file_path
        for ext in ['.tsx', '.ts', '.jsx', '.js']:
            if path_no_ext.endswith(ext):
                path_no_ext = path_no_ext[:-len(ext)]
                break
        
        # Get file name
        file_name = Path(path_no_ext).name
        
        # Possible import patterns
        patterns.append(f"from '{file_name}'")
        patterns.append(f'from "{file_name}"')
        patterns.append(f"from './{file_name}'")
        patterns.append(f'from "./{file_name}"')
        patterns.append(f"from '../{file_name}'")
        
        # Check for alias imports
        if '/src/' in file_path:
            rel_to_src = file_path.split('/src/')[-1]
            patterns.append(f"from '@/{rel_to_src}'")
            patterns.append(f'from "@/{rel_to_src}"')
        
        return patterns
    
    async def _generate_file_updates(self, file_path: str, 
                                    file_moves: List[FileMove]) -> List[ImportUpdate]:
        """Generate import updates for a specific file"""
        updates = []
        
        try:
            content = Path(file_path).read_text()
            lines = content.split('\n')
            
            for line_no, line in enumerate(lines, 1):
                # Check if this is an import line
                if 'import' in line and 'from' in line:
                    # Extract import path
                    import_match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', line)
                    if import_match:
                        import_path = import_match.group(1)
                        
                        # Check if this import needs updating
                        for move in file_moves:
                            if self._import_references_file(import_path, move.from_path, file_path):
                                # Calculate new import path
                                new_import = self._calculate_new_import_path(
                                    file_path, move.from_path, move.to_path, import_path
                                )
                                
                                if new_import and new_import != import_path:
                                    updates.append(ImportUpdate(
                                        file_path=file_path,
                                        line_number=line_no,
                                        old_import=import_path,
                                        new_import=new_import,
                                        import_type=self._get_import_type(import_path),
                                        is_type_only='import type' in line
                                    ))
                                    
        except Exception as e:
            debug_log.error_trace(f"Error generating updates for {file_path}", exception=e)
        
        return updates
    
    def _import_references_file(self, import_path: str, target_file: str, 
                               from_file: str) -> bool:
        """Check if an import path references a specific file"""
        # Resolve import to actual file
        resolved = self._resolve_import(import_path, from_file)
        
        # Normalize paths for comparison
        if resolved:
            resolved_normalized = str(Path(resolved).resolve())
            target_normalized = str(Path(target_file).resolve())
            
            # Check if they're the same file
            return resolved_normalized == target_normalized
        
        return False
    
    def _resolve_import(self, import_path: str, from_file: str) -> Optional[str]:
        """Resolve an import path to an actual file path"""
        from_dir = Path(from_file).parent
        
        # Relative import
        if import_path.startswith('.'):
            resolved = from_dir
            parts = import_path.split('/')
            
            for part in parts:
                if part == '.':
                    continue
                elif part == '..':
                    resolved = resolved.parent
                else:
                    resolved = resolved / part
            
            # Try with extensions
            for ext in ['', '.tsx', '.ts', '.jsx', '.js', '/index.tsx', '/index.ts']:
                full_path = Path(str(resolved) + ext)
                if full_path.exists():
                    return str(full_path)
        
        # Alias import
        elif import_path.startswith('@'):
            # Match against tsconfig paths
            for alias_pattern, targets in self.tsconfig_paths.paths.items():
                # Convert pattern to regex
                pattern = alias_pattern.replace('*', '(.*)')
                match = re.match(f"^{pattern}$", import_path)
                
                if match:
                    # Try each target
                    for target_pattern in targets:
                        # Replace wildcard with matched value
                        if '*' in target_pattern and match.groups():
                            target = target_pattern.replace('*', match.group(1))
                        else:
                            target = target_pattern
                        
                        # Try with extensions
                        for ext in ['', '.tsx', '.ts', '.jsx', '.js', '/index.tsx', '/index.ts']:
                            full_path = Path(target + ext)
                            if full_path.exists():
                                return str(full_path)
        
        return None
    
    def _calculate_new_import_path(self, from_file: str, old_target: str,
                                  new_target: str, current_import: str) -> Optional[str]:
        """Calculate new import path after a file move"""
        import_type = self._get_import_type(current_import)
        
        if import_type == 'relative':
            # Calculate new relative path
            from_dir = Path(from_file).parent
            new_target_path = Path(new_target)
            
            # Calculate relative path from importing file to new location
            try:
                relative_path = new_target_path.relative_to(from_dir)
                
                # Format as import path
                import_path = './' + str(relative_path).replace('\\', '/')
                
                # Remove extension if present in original
                if not any(ext in current_import for ext in ['.tsx', '.ts', '.jsx', '.js']):
                    for ext in ['.tsx', '.ts', '.jsx', '.js']:
                        if import_path.endswith(ext):
                            import_path = import_path[:-len(ext)]
                            break
                
                return import_path
                
            except ValueError:
                # Need to go up directories
                common = os.path.commonpath([str(from_dir), str(new_target_path.parent)])
                
                # Count how many levels up
                levels_up = len(Path(from_dir).relative_to(common).parts)
                
                # Build relative path
                relative_parts = ['..'] * levels_up
                relative_parts.extend(new_target_path.relative_to(common).parts)
                
                import_path = '/'.join(relative_parts)
                
                # Remove extension if needed
                if not any(ext in current_import for ext in ['.tsx', '.ts', '.jsx', '.js']):
                    for ext in ['.tsx', '.ts', '.jsx', '.js']:
                        if import_path.endswith(ext):
                            import_path = import_path[:-len(ext)]
                            break
                
                return import_path
        
        elif import_type == 'alias':
            # Update alias import
            if '/src/' in new_target:
                rel_to_src = new_target.split('/src/')[-1]
                
                # Remove extension
                for ext in ['.tsx', '.ts', '.jsx', '.js']:
                    if rel_to_src.endswith(ext):
                        rel_to_src = rel_to_src[:-len(ext)]
                        break
                
                return f"@/{rel_to_src}"
        
        return None
    
    def _get_import_type(self, import_path: str) -> str:
        """Determine the type of import"""
        if import_path.startswith('.'):
            return 'relative'
        elif import_path.startswith('@'):
            return 'alias'
        elif import_path.startswith('/'):
            return 'absolute'
        else:
            return 'package'
    
    def _generate_tsconfig_updates(self, file_moves: List[FileMove]) -> Dict[str, str]:
        """Generate updates needed for tsconfig.json paths"""
        updates = {}
        
        # Check if any moves affect aliased paths
        for alias, targets in self.tsconfig_paths.paths.items():
            for target in targets:
                # Check if this target is affected by moves
                for move in file_moves:
                    if target in move.from_path or move.from_path in target:
                        # Calculate new target
                        new_target = target.replace(move.from_path, move.to_path)
                        
                        if new_target != target:
                            if alias not in updates:
                                updates[alias] = []
                            updates[alias].append(new_target)
        
        return updates
    
    async def apply_updates(self, plan: ImportRewritePlan, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply import updates to files
        """
        debug_log.api(f"Applying {plan.total_updates} import updates (dry_run={dry_run})", level="INFO")
        
        results = {
            'files_updated': 0,
            'imports_updated': 0,
            'errors': [],
            'updates_by_file': {}
        }
        
        # Group updates by file
        updates_by_file = {}
        for update in plan.import_updates:
            if update.file_path not in updates_by_file:
                updates_by_file[update.file_path] = []
            updates_by_file[update.file_path].append(update)
        
        # Apply updates to each file
        for file_path, updates in updates_by_file.items():
            try:
                if dry_run:
                    debug_log.api(f"[DRY RUN] Would update {len(updates)} imports in {file_path}", level="INFO")
                    results['updates_by_file'][file_path] = len(updates)
                else:
                    success = await self._apply_file_updates(file_path, updates)
                    if success:
                        results['files_updated'] += 1
                        results['imports_updated'] += len(updates)
                        results['updates_by_file'][file_path] = len(updates)
                    else:
                        results['errors'].append(f"Failed to update {file_path}")
                        
            except Exception as e:
                results['errors'].append(f"Error updating {file_path}: {str(e)}")
                debug_log.error_trace(f"Failed to update {file_path}", exception=e)
        
        return results
    
    async def _apply_file_updates(self, file_path: str, updates: List[ImportUpdate]) -> bool:
        """Apply updates to a single file"""
        try:
            path = Path(file_path)
            content = path.read_text()
            
            # Sort updates by line number (reverse) to avoid offset issues
            updates.sort(key=lambda x: x.line_number, reverse=True)
            
            lines = content.split('\n')
            
            for update in updates:
                line_idx = update.line_number - 1
                if 0 <= line_idx < len(lines):
                    line = lines[line_idx]
                    
                    # Replace old import with new
                    new_line = line.replace(
                        f'from \'{update.old_import}\'',
                        f'from \'{update.new_import}\''
                    ).replace(
                        f'from "{update.old_import}"',
                        f'from "{update.new_import}"'
                    )
                    
                    lines[line_idx] = new_line
            
            # Write back to file
            new_content = '\n'.join(lines)
            path.write_text(new_content)
            
            debug_log.api(f"Updated {len(updates)} imports in {file_path}", level="INFO")
            return True
            
        except Exception as e:
            debug_log.error_trace(f"Failed to apply updates to {file_path}", exception=e)
            return False
    
    async def validate_imports(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Validate that all imports resolve correctly
        """
        validation_errors = {}
        
        for file_path in file_paths:
            errors = await self._validate_file_imports(file_path)
            if errors:
                validation_errors[file_path] = errors
        
        return validation_errors
    
    async def _validate_file_imports(self, file_path: str) -> List[str]:
        """Validate imports in a single file"""
        errors = []
        
        try:
            content = Path(file_path).read_text()
            
            # Find all imports
            import_pattern = r'from\s+[\'"]([^\'"]+)[\'"]'
            imports = re.findall(import_pattern, content)
            
            for import_path in imports:
                # Skip external packages
                if not import_path.startswith('.') and not import_path.startswith('@'):
                    continue
                
                # Try to resolve
                resolved = self._resolve_import(import_path, file_path)
                if not resolved:
                    errors.append(f"Cannot resolve import: {import_path}")
                elif not Path(resolved).exists():
                    errors.append(f"Import target does not exist: {import_path} -> {resolved}")
                    
        except Exception as e:
            errors.append(f"Error validating file: {str(e)}")
        
        return errors


# Test functionality
if __name__ == "__main__":
    async def test_rewriter():
        rewriter = ImportRewriter()
        
        # Create test moves
        moves = [
            FileMove(
                from_path='/app/client/src/components/auth/Login.tsx',
                to_path='/app/client/src/domains/auth/components/Login.tsx',
                from_domain='auth',
                to_domain='auth'
            ),
            FileMove(
                from_path='/app/client/src/services/api.ts',
                to_path='/app/client/src/domains/shared/services/api.ts',
                from_domain='api',
                to_domain='shared'
            )
        ]
        
        # Create rewrite plan
        plan = await rewriter.create_rewrite_plan(moves)
        
        print(f"Rewrite Plan")
        print(f"============")
        print(f"File Moves: {len(plan.file_moves)}")
        print(f"Import Updates: {plan.total_updates}")
        print(f"Affected Files: {len(plan.affected_files)}")
        
        if plan.tsconfig_updates:
            print(f"\nTsconfig Updates:")
            for alias, targets in plan.tsconfig_updates.items():
                print(f"  {alias}: {targets}")
        
        if plan.import_updates:
            print(f"\nSample Import Updates (first 5):")
            for update in plan.import_updates[:5]:
                print(f"  {update.file_path}:{update.line_number}")
                print(f"    OLD: {update.old_import}")
                print(f"    NEW: {update.new_import}")
        
        # Test validation
        print(f"\nValidating imports...")
        validation_errors = await rewriter.validate_imports(list(plan.affected_files))
        if validation_errors:
            print(f"Validation errors found:")
            for file, errors in validation_errors.items():
                print(f"  {file}:")
                for error in errors:
                    print(f"    - {error}")
        else:
            print("All imports valid!")
    
    # Run test
    asyncio.run(test_rewriter())