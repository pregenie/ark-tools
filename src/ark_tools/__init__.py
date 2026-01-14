"""
ARK-TOOLS: AI-Assisted Code Consolidation Platform
==================================================

A production-ready system for safely consolidating fragmented codebases using
specialized AI agents and agentic workflows.

Core Principles:
- Read-Only Source Rule: Never modifies original files
- AI-Assisted Development: Specialized agents handle different aspects
- Production Quality: Type hints, error handling, comprehensive testing
- Safety First: Versioned outputs, rollback capability, automated validation

Main Components:
- Core Analysis Engine: MAMS-based code analysis and pattern detection
- Specialized Agents: ark-architect, ark-detective, ark-transformer, ark-guardian
- Database Layer: PostgreSQL with pgvector for semantic analysis
- API Layer: Flask REST API with WebSocket support
- Safety System: Comprehensive quality enforcement and source protection
"""

__version__ = "2.0.0"
__author__ = "ARK-TOOLS Team"
__email__ = "team@ark-tools.dev"
__license__ = "MIT"

from typing import Dict, Any
import os
import logging
from pathlib import Path

# Configure default logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class ARKToolsConfig:
    """Global configuration for ARK-TOOLS"""
    
    # Version and Build Info
    VERSION = __version__
    BUILD_DATE = "2026-01-12"
    
    # Core Principles
    READ_ONLY_SOURCE = True
    VERSIONED_OUTPUT = True
    SAFETY_FIRST = True
    
    # Default Paths
    DEFAULT_OUTPUT_DIR = ".ark_output"
    DEFAULT_CONFIG_DIR = ".ark_config"
    DEFAULT_LOGS_DIR = "logs"
    
    # MAMS Integration
    MAMS_BASE_PATH = os.getenv('MAMS_BASE_PATH', '../arkyvus_project/arkyvus')
    MAMS_MIGRATIONS_PATH = os.getenv('MAMS_MIGRATIONS_PATH', f'{MAMS_BASE_PATH}/migrations')
    
    # Database Configuration
    DATABASE_URL = os.getenv('ARK_DATABASE_URL', 'postgresql://ark_admin:password@localhost:5432/ark_tools')
    REDIS_URL = os.getenv('ARK_REDIS_URL', 'redis://localhost:6379/0')
    
    # Security
    SECRET_KEY = os.getenv('ARK_SECRET_KEY', 'dev-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('ARK_JWT_SECRET_KEY', 'jwt-dev-key-change-in-production')
    
    # AI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # LLM Configuration (for embedded models)
    LLM_MODEL_PATH = os.getenv('ARK_LLM_MODEL_PATH', str(Path.home() / '.ark_tools/models/codellama-7b-instruct.gguf'))
    LLM_CONTEXT_SIZE = int(os.getenv('ARK_LLM_CONTEXT_SIZE', '8192'))
    LLM_MAX_TOKENS = int(os.getenv('ARK_LLM_MAX_TOKENS', '2048'))
    LLM_THREADS = int(os.getenv('ARK_LLM_THREADS', '8'))
    LLM_TEMPERATURE = float(os.getenv('ARK_LLM_TEMPERATURE', '0.1'))
    LLM_ENABLE_GPU = os.getenv('ARK_LLM_ENABLE_GPU', 'true').lower() == 'true'
    
    # Feature Flags
    ENABLE_WEBSOCKETS = os.getenv('ARK_ENABLE_WEBSOCKETS', 'true').lower() == 'true'
    ENABLE_MONITORING = os.getenv('ARK_ENABLE_MONITORING', 'true').lower() == 'true'
    ENABLE_SECURITY_SCAN = os.getenv('ARK_ENABLE_SECURITY_SCAN', 'true').lower() == 'true'
    
    @classmethod
    def validate_environment(cls) -> Dict[str, Any]:
        """Validate environment configuration"""
        issues = []
        warnings = []
        
        # Check required environment variables
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            issues.append("No AI API keys configured (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        
        # Check MAMS path
        if not os.path.exists(cls.MAMS_BASE_PATH):
            issues.append(f"MAMS base path not found: {cls.MAMS_BASE_PATH}")
        
        # Check development vs production settings
        if cls.SECRET_KEY.startswith('dev-'):
            warnings.append("Using development secret key")
        
        if cls.JWT_SECRET_KEY.startswith('jwt-dev-'):
            warnings.append("Using development JWT secret key")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

# Global configuration instance
config = ARKToolsConfig()

# Validate environment on import
validation_result = config.validate_environment()
if not validation_result['valid']:
    logger.warning(f"Environment validation failed: {validation_result['issues']}")
if validation_result['warnings']:
    logger.info(f"Environment warnings: {validation_result['warnings']}")

logger.info(f"ARK-TOOLS {__version__} initialized")