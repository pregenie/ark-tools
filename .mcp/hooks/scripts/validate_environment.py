#!/usr/bin/env python3
"""
ARK-TOOLS Environment Validator
Validates that all required tools and environment variables are available
"""

import sys
import os
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentValidator:
    """Validates environment prerequisites for ARK-TOOLS"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.fail_fast = config.get('fail_fast', False)
        self.report_missing = config.get('report_missing', True)
        self.required_commands = config.get('required_commands', [])
        self.optional_commands = config.get('optional_commands', [])
        self.required_env_vars = config.get('required_env_vars', [])
        
    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate the complete environment
        
        Returns:
            Dict with validation results
        """
        
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'command_checks': {},
            'env_var_checks': {},
            'recommendations': []
        }
        
        # Check required commands
        for command in self.required_commands:
            check_result = self._check_command(command)
            result['command_checks'][command] = check_result
            
            if not check_result['available']:
                result['valid'] = False
                result['errors'].append(f"Required command not found: {command}")
                
                if self.fail_fast:
                    return result
        
        # Check optional commands
        for command in self.optional_commands:
            check_result = self._check_command(command)
            result['command_checks'][command] = check_result
            
            if not check_result['available']:
                result['warnings'].append(f"Optional command not found: {command}")
                result['recommendations'].append(f"Install {command} for enhanced functionality")
        
        # Check required environment variables
        for env_var in self.required_env_vars:
            check_result = self._check_env_var(env_var)
            result['env_var_checks'][env_var] = check_result
            
            if not check_result['set']:
                result['valid'] = False
                result['errors'].append(f"Required environment variable not set: {env_var}")
        
        # Add specific recommendations
        result['recommendations'].extend(self._generate_recommendations(result))
        
        return result
    
    def _check_command(self, command: str) -> Dict[str, Any]:
        """Check if a command is available"""
        
        check_result = {
            'available': False,
            'version': None,
            'path': None,
            'error': None
        }
        
        try:
            # Check if command exists
            result = subprocess.run(['which', command], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                check_result['available'] = True
                check_result['path'] = result.stdout.strip()
                
                # Try to get version
                version_result = self._get_command_version(command)
                if version_result:
                    check_result['version'] = version_result
                    
        except subprocess.TimeoutExpired:
            check_result['error'] = f"Timeout checking {command}"
        except Exception as e:
            check_result['error'] = str(e)
        
        return check_result
    
    def _get_command_version(self, command: str) -> str:
        """Get version information for a command"""
        
        version_flags = ['--version', '-v', '-V', 'version']
        
        for flag in version_flags:
            try:
                result = subprocess.run([command, flag], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout:
                    # Extract version from first line
                    version_line = result.stdout.split('\n')[0]
                    return version_line.strip()
            except:
                continue
        
        return None
    
    def _check_env_var(self, env_var: str) -> Dict[str, Any]:
        """Check if environment variable is set"""
        
        value = os.getenv(env_var)
        
        return {
            'set': value is not None,
            'value': value if value else None,
            'masked_value': self._mask_sensitive_value(env_var, value) if value else None
        }
    
    def _mask_sensitive_value(self, env_var: str, value: str) -> str:
        """Mask sensitive environment variable values"""
        
        sensitive_patterns = ['password', 'secret', 'key', 'token', 'api']
        
        if any(pattern in env_var.lower() for pattern in sensitive_patterns):
            if len(value) > 4:
                return value[:2] + '*' * (len(value) - 4) + value[-2:]
            else:
                return '*' * len(value)
        
        return value
    
    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on validation results"""
        
        recommendations = []
        
        # Command-specific recommendations
        command_checks = result.get('command_checks', {})
        
        if 'docker' in command_checks and not command_checks['docker']['available']:
            recommendations.append("Install Docker: https://docs.docker.com/get-docker/")
        
        if 'docker-compose' in command_checks and not command_checks['docker-compose']['available']:
            recommendations.append("Install Docker Compose: https://docs.docker.com/compose/install/")
        
        if 'python3' in command_checks and not command_checks['python3']['available']:
            recommendations.append("Install Python 3.11+: https://www.python.org/downloads/")
        
        if 'mypy' in command_checks and not command_checks['mypy']['available']:
            recommendations.append("Install mypy: pip install mypy")
        
        if 'black' in command_checks and not command_checks['black']['available']:
            recommendations.append("Install black: pip install black")
        
        if 'prettier' in command_checks and not command_checks['prettier']['available']:
            recommendations.append("Install prettier: npm install -g prettier")
        
        # Environment variable recommendations
        env_checks = result.get('env_var_checks', {})
        
        if 'DATABASE_URL' in env_checks and not env_checks['DATABASE_URL']['set']:
            recommendations.append("Set DATABASE_URL: export DATABASE_URL='postgresql://user:pass@host:port/db'")
        
        if 'SECRET_KEY' in env_checks and not env_checks['SECRET_KEY']['set']:
            recommendations.append("Set SECRET_KEY: export SECRET_KEY='$(python3 -c \"import secrets; print(secrets.token_hex(32))\")'")
        
        return recommendations

def print_validation_report(result: Dict[str, Any]):
    """Print a comprehensive validation report"""
    
    print("\n" + "=" * 60)
    print("🔍 ARK-TOOLS Environment Validation Report")
    print("=" * 60)
    
    # Overall status
    if result['valid']:
        print("✅ Environment validation: PASSED")
    else:
        print("❌ Environment validation: FAILED")
    
    # Command checks
    print("\n📦 Command Availability:")
    command_checks = result.get('command_checks', {})
    
    for command, check_result in command_checks.items():
        if check_result['available']:
            version_info = f" ({check_result['version']})" if check_result['version'] else ""
            print(f"  ✅ {command}{version_info}")
        else:
            error_info = f" - {check_result['error']}" if check_result['error'] else ""
            print(f"  ❌ {command}{error_info}")
    
    # Environment variable checks
    print("\n🌍 Environment Variables:")
    env_checks = result.get('env_var_checks', {})
    
    for env_var, check_result in env_checks.items():
        if check_result['set']:
            masked_value = check_result.get('masked_value', 'set')
            print(f"  ✅ {env_var} = {masked_value}")
        else:
            print(f"  ❌ {env_var} (not set)")
    
    # Errors
    if result['errors']:
        print("\n🚨 Errors:")
        for error in result['errors']:
            print(f"  • {error}")
    
    # Warnings
    if result['warnings']:
        print("\n⚠️ Warnings:")
        for warning in result['warnings']:
            print(f"  • {warning}")
    
    # Recommendations
    if result['recommendations']:
        print("\n💡 Recommendations:")
        for recommendation in result['recommendations']:
            print(f"  • {recommendation}")
    
    print("\n" + "=" * 60)

def main():
    """Main validation function"""
    
    # Load configuration
    config_file = Path(__file__).parent.parent / 'config.json'
    try:
        with open(config_file, 'r') as f:
            full_config = json.load(f)
            config = full_config.get('custom_validations', {}).get('check_environment', {}).get('config', {})
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        config = {
            'required_commands': ['docker', 'docker-compose', 'python3'],
            'optional_commands': ['mypy', 'black', 'prettier'],
            'required_env_vars': ['DATABASE_URL'],
            'fail_fast': False,
            'report_missing': True
        }
    
    # Create validator
    validator = EnvironmentValidator(config)
    
    # Run validation
    result = validator.validate_environment()
    
    # Print report
    print_validation_report(result)
    
    # Return appropriate exit code
    if result['valid']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()