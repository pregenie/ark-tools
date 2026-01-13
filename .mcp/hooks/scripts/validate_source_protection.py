#!/usr/bin/env python3
"""
ARK-TOOLS Source Protection Validator
Enforces the Read-Only Source rule - prevents direct modification of source files
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import fnmatch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SourceProtectionValidator:
    """Validates that source files are not being modified directly"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.strict_mode = config.get('strict_mode', True)
        self.log_violations = config.get('log_violations', True)
        self.protected_patterns = config.get('protected_patterns', [])
        self.allowed_patterns = config.get('allowed_patterns', [])
        self.exception_patterns = config.get('exception_patterns', [])
        
    def validate_file_operation(self, file_path: str, operation: str = 'write') -> Dict[str, Any]:
        """
        Validate if a file operation is allowed under the Read-Only Source rule
        
        Args:
            file_path: Path to the file being operated on
            operation: Type of operation (write, delete, modify)
            
        Returns:
            Dict with validation result
        """
        
        result = {
            'allowed': True,
            'reason': '',
            'severity': 'info',
            'recommendations': []
        }
        
        # Normalize file path
        normalized_path = os.path.normpath(file_path)
        
        # Check if file matches protected patterns
        if self._is_protected_file(normalized_path):
            # Check if it's in an allowed location
            if not self._is_allowed_location(normalized_path):
                # Check for exceptions
                if not self._is_exception(normalized_path):
                    result.update({
                        'allowed': False,
                        'reason': f'Attempted to {operation} protected source file: {normalized_path}',
                        'severity': 'error',
                        'recommendations': [
                            'Use .ark_output/ directory for generated code',
                            'Use /ark-transform and /ark-generate commands for safe transformations',
                            f'Original file: {normalized_path}',
                            f'Suggested output: .ark_output/v_$(date +%Y%m%d_%H%M%S)/{os.path.basename(normalized_path)}'
                        ]
                    })
                    
                    if self.log_violations:
                        self._log_violation(normalized_path, operation, result)
        
        return result
    
    def _is_protected_file(self, file_path: str) -> bool:
        """Check if file matches protected patterns"""
        for pattern in self.protected_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    def _is_allowed_location(self, file_path: str) -> bool:
        """Check if file is in an allowed location"""
        for pattern in self.allowed_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    def _is_exception(self, file_path: str) -> bool:
        """Check if file matches exception patterns"""
        for pattern in self.exception_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    def _log_violation(self, file_path: str, operation: str, result: Dict[str, Any]):
        """Log source protection violations"""
        
        violation_log = {
            'timestamp': str(datetime.now()),
            'file_path': file_path,
            'operation': operation,
            'violation_type': 'source_modification_attempt',
            'severity': result['severity'],
            'reason': result['reason'],
            'user': os.getenv('USER', 'unknown'),
            'session_id': os.getenv('SESSION_ID', 'unknown')
        }
        
        # Log to file
        log_file = Path('logs/source_protection_violations.log')
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(violation_log) + '\n')
        
        # Log to console
        logger.error(f"SOURCE PROTECTION VIOLATION: {result['reason']}")
        
        # Send to monitoring system if configured
        self._send_to_monitoring(violation_log)
    
    def _send_to_monitoring(self, violation_log: Dict[str, Any]):
        """Send violation to monitoring system"""
        try:
            # Send to webhook if configured
            webhook_url = os.getenv('ERROR_WEBHOOK_URL')
            if webhook_url:
                import requests
                requests.post(webhook_url, json=violation_log, timeout=5)
        except Exception as e:
            logger.warning(f"Failed to send violation to monitoring: {e}")

def main():
    """Main validation function called by MCP hooks"""
    
    if len(sys.argv) < 2:
        logger.error("Usage: validate_source_protection.py <file_path> [operation]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    operation = sys.argv[2] if len(sys.argv) > 2 else 'write'
    
    # Load configuration
    config_file = Path(__file__).parent.parent / 'config.json'
    try:
        with open(config_file, 'r') as f:
            full_config = json.load(f)
            config = full_config.get('custom_validations', {}).get('prevent_source_modification', {}).get('config', {})
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        config = {
            'protected_patterns': ['**/src/**/*.py', '**/lib/**/*.js'],
            'allowed_patterns': ['**/.ark_output/**/*', '**/tests/**/*'],
            'strict_mode': True
        }
    
    # Create validator
    validator = SourceProtectionValidator(config)
    
    # Validate the operation
    result = validator.validate_file_operation(file_path, operation)
    
    # Output result
    if result['allowed']:
        print(f"✅ Operation allowed: {operation} on {file_path}")
        sys.exit(0)
    else:
        print(f"❌ BLOCKED: {result['reason']}")
        print("\n🛡️ ARK-TOOLS Read-Only Source Protection")
        print("Source files must never be modified directly!")
        print("\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"  • {rec}")
        
        # In strict mode, block the operation
        if validator.strict_mode:
            sys.exit(1)
        else:
            print("\n⚠️ Warning issued but operation allowed (non-strict mode)")
            sys.exit(0)

if __name__ == '__main__':
    main()