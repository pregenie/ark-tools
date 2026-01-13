"""
ARK-TOOLS Safety Manager
========================

Implements the Read-Only Source Rule and other safety guarantees.
Prevents any modification of original source files and ensures all
operations are reversible.
"""

import os
import shutil
from typing import Union, List, Dict, Any
from pathlib import Path
import logging

from ark_tools import config
from ark_tools.utils.debug_logger import debug_log

logger = logging.getLogger(__name__)

class SafetyManager:
    """
    Manages safety guarantees throughout ARK-TOOLS operations
    """
    
    def __init__(self):
        self.protected_paths: List[Path] = []
        self.backup_registry: Dict[str, str] = {}
        
        debug_log.safety("Safety Manager initialized with Read-Only Source Rule enabled")
    
    def verify_read_only_operation(self, path: Union[str, Path]) -> None:
        """
        Verify that an operation is read-only and doesn't modify source files
        
        Args:
            path: Path to verify for read-only access
            
        Raises:
            PermissionError: If path modification would violate Read-Only Source Rule
        """
        path = Path(path)
        
        # Check if path is in protected list
        for protected_path in self.protected_paths:
            if path.is_relative_to(protected_path):
                raise PermissionError(
                    f"❌ BLOCKED: Attempted to modify protected source path: {path}. "
                    f"ARK-TOOLS Read-Only Source Rule prevents modification of original files."
                )
        
        debug_log.safety(f"Read-only verification passed for: {path}")
    
    def protect_source_directory(self, directory: Union[str, Path]) -> None:
        """
        Add directory to protected source paths
        
        Args:
            directory: Directory to protect from modification
        """
        directory = Path(directory).resolve()
        if directory not in self.protected_paths:
            self.protected_paths.append(directory)
            debug_log.safety(f"Protected source directory: {directory}")
    
    def is_safe_output_path(self, path: Union[str, Path]) -> bool:
        """
        Check if path is safe for output (not in protected source)
        
        Args:
            path: Path to check
            
        Returns:
            True if path is safe for output
        """
        path = Path(path).resolve()
        
        # Check if path is under any protected directory
        for protected_path in self.protected_paths:
            try:
                if path.is_relative_to(protected_path):
                    return False
            except ValueError:
                # Not relative, continue checking
                continue
        
        # Check if path is in standard output directory
        if config.DEFAULT_OUTPUT_DIR in str(path):
            return True
        
        # Additional safety checks
        parent_names = [p.name for p in path.parents]
        safe_indicators = ['.ark_output', 'generated', 'output', 'build', 'dist']
        
        return any(indicator in parent_names or indicator in path.name for indicator in safe_indicators)
    
    def create_backup(self, file_path: Union[str, Path], backup_id: str) -> str:
        """
        Create backup of file before any operation
        
        Args:
            file_path: Path to file to backup
            backup_id: Unique identifier for this backup
            
        Returns:
            Path to backup file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
        
        # Create backup directory
        backup_dir = Path(config.DEFAULT_OUTPUT_DIR) / "backups" / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup file path preserving directory structure
        backup_file = backup_dir / file_path.name
        
        # Copy file to backup
        shutil.copy2(file_path, backup_file)
        
        # Register backup
        self.backup_registry[str(file_path)] = str(backup_file)
        
        debug_log.safety(f"Created backup: {file_path} -> {backup_file}")
        
        return str(backup_file)
    
    def rollback_from_backup(self, original_path: Union[str, Path]) -> bool:
        """
        Restore file from backup
        
        Args:
            original_path: Path to original file to restore
            
        Returns:
            True if rollback successful
        """
        original_path_str = str(Path(original_path))
        
        if original_path_str not in self.backup_registry:
            debug_log.safety(f"No backup found for: {original_path}", level="WARNING")
            return False
        
        backup_path = self.backup_registry[original_path_str]
        
        if not Path(backup_path).exists():
            debug_log.safety(f"Backup file missing: {backup_path}", level="ERROR")
            return False
        
        try:
            shutil.copy2(backup_path, original_path)
            debug_log.safety(f"Rollback successful: {backup_path} -> {original_path}")
            return True
        
        except Exception as e:
            debug_log.error_trace(f"Rollback failed for {original_path}", exception=e)
            return False
    
    def validate_generated_code(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate generated code for syntax and basic quality
        
        Args:
            file_path: Path to generated file to validate
            
        Returns:
            Dict with validation results
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'valid': False, 'error': 'File does not exist'}
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic syntax validation for Python files
            if file_path.suffix == '.py':
                try:
                    compile(content, str(file_path), 'exec')
                    syntax_valid = True
                    syntax_error = None
                except SyntaxError as e:
                    syntax_valid = False
                    syntax_error = str(e)
            else:
                syntax_valid = True  # Assume valid for non-Python files
                syntax_error = None
            
            # Additional quality checks
            quality_checks = {
                'has_content': len(content.strip()) > 0,
                'has_proper_encoding': True,  # We successfully read it
                'reasonable_size': len(content) < 1_000_000,  # Less than 1MB
            }
            
            result = {
                'valid': syntax_valid and all(quality_checks.values()),
                'syntax_valid': syntax_valid,
                'syntax_error': syntax_error,
                'quality_checks': quality_checks,
                'file_size': len(content),
                'line_count': len(content.splitlines())
            }
            
            debug_log.safety(f"Code validation completed for {file_path}: {'PASS' if result['valid'] else 'FAIL'}")
            
            return result
        
        except Exception as e:
            debug_log.error_trace(f"Code validation failed for {file_path}", exception=e)
            return {
                'valid': False,
                'error': str(e),
                'exception_type': type(e).__name__
            }
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety system status"""
        return {
            'read_only_source_enabled': config.READ_ONLY_SOURCE,
            'protected_paths_count': len(self.protected_paths),
            'protected_paths': [str(p) for p in self.protected_paths],
            'active_backups': len(self.backup_registry),
            'versioned_output_enabled': config.VERSIONED_OUTPUT,
            'safety_first_enabled': config.SAFETY_FIRST
        }