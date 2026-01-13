"""
Setup Orchestrator
==================

Coordinates the entire setup process, managing detection, configuration,
validation, and deployment.
"""

import asyncio
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

from ark_tools.setup.detector import EnvironmentDetector, ServiceDetector
from ark_tools.setup.configurator import SetupConfigurator, ServiceMode
from ark_tools.setup.validator import ConnectionValidator

logger = logging.getLogger(__name__)

class SetupOrchestrator:
    """
    Orchestrates the complete ARK-TOOLS setup process
    """
    
    def __init__(self):
        self.env_detector = EnvironmentDetector()
        self.service_detector = ServiceDetector()
        self.configurator = SetupConfigurator()
        self.validator = ConnectionValidator()
        
        # Store detection results
        self.detected_envs = []
        self.detected_services = []
        self.selected_env = None
        
        # Setup state
        self.setup_complete = False
        self.setup_log = []
    
    def log(self, message: str, level: str = "info") -> None:
        """Log a setup message"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.setup_log.append(log_entry)
        
        # Also use standard logging
        log_func = getattr(logger, level, logger.info)
        log_func(message)
    
    async def detect_environment_async(self, search_paths: Optional[List[str]] = None) -> List[Any]:
        """Async wrapper for environment detection"""
        if search_paths:
            self.env_detector.search_paths = search_paths
        
        loop = asyncio.get_event_loop()
        self.detected_envs = await loop.run_in_executor(None, self.env_detector.scan_for_env_files)
        
        self.log(f"Detected {len(self.detected_envs)} environment files")
        return self.detected_envs
    
    async def detect_services_async(self) -> List[Any]:
        """Async wrapper for service detection"""
        loop = asyncio.get_event_loop()
        
        # Detect Docker services
        docker_services = await loop.run_in_executor(None, self.service_detector.scan_docker_containers)
        self.log(f"Detected {len(docker_services)} Docker services")
        
        # Detect system services
        system_services = await loop.run_in_executor(None, self.service_detector.scan_system_services)
        self.log(f"Detected {len(system_services)} system services")
        
        # Merge with environment information
        all_services = docker_services + system_services
        self.detected_services = await loop.run_in_executor(
            None, 
            self.service_detector.merge_with_env_services,
            self.env_detector
        )
        
        return self.detected_services
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """Test all configured service connections"""
        results = {}
        
        # Test PostgreSQL
        if self.configurator.config.postgresql:
            pg_config = self.configurator.config.postgresql
            self.log("Testing PostgreSQL connection...")
            
            result = await self.validator.test_postgresql(
                pg_config.host,
                pg_config.port,
                pg_config.credentials.get('username'),
                pg_config.credentials.get('password'),
                pg_config.credentials.get('database') or pg_config.create_database
            )
            
            results['postgresql'] = {
                'connected': result['connected'],
                'message': result.get('error') or f"Connected to PostgreSQL {result.get('version', '')}"
            }
            
            if result['connected']:
                self.log("PostgreSQL connection successful", "info")
                if not result.get('has_pgvector'):
                    self.log("pgvector extension not detected - will use fallback", "warning")
            else:
                self.log(f"PostgreSQL connection failed: {result.get('error')}", "error")
        
        # Test Redis
        if self.configurator.config.redis:
            redis_config = self.configurator.config.redis
            self.log("Testing Redis connection...")
            
            result = await self.validator.test_redis(
                redis_config.host,
                redis_config.port,
                redis_config.credentials.get('password'),
                redis_config.database_number or 0
            )
            
            results['redis'] = {
                'connected': result['connected'],
                'message': result.get('error') or f"Connected to Redis {result.get('version', '')}"
            }
            
            if result['connected']:
                self.log("Redis connection successful", "info")
            else:
                self.log(f"Redis connection failed: {result.get('error')}", "error")
        
        return results
    
    def quick_setup(self, parent_env_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Quick setup with intelligent defaults
        
        Args:
            parent_env_path: Path to parent project env file to inherit from
            
        Returns:
            Tuple of (success, message)
        """
        self.log("Starting quick setup...")
        
        try:
            # 1. Detect environment files
            self.detected_envs = self.env_detector.scan_for_env_files()
            
            # Select parent environment
            if parent_env_path:
                for env in self.detected_envs:
                    if env.path == parent_env_path:
                        self.selected_env = env
                        break
            else:
                # Auto-select best parent
                self.selected_env = self.env_detector.get_parent_project_env()
            
            if self.selected_env:
                self.log(f"Selected parent environment: {self.selected_env.path}")
                
                # Inherit credentials
                inherit_keys = [
                    'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
                    'DATABASE_URL', 'REDIS_URL'
                ]
                self.configurator.inherit_from_env(self.selected_env, inherit_keys)
            
            # 2. Detect services
            self.detected_services = self.service_detector.scan_docker_containers()
            self.detected_services.extend(self.service_detector.scan_system_services())
            self.detected_services = self.service_detector.merge_with_env_services(self.env_detector)
            
            self.log(f"Found {len(self.detected_services)} services")
            
            # 3. Auto-configure services
            # PostgreSQL
            postgres_services = [s for s in self.detected_services if s.service_type == 'postgresql']
            if postgres_services:
                # Use the first running PostgreSQL
                for pg_service in postgres_services:
                    if pg_service.is_running:
                        config = self.configurator.configure_from_detected_service(
                            pg_service,
                            ServiceMode.USE_EXISTING,
                            database_name='ark_tools'
                        )
                        self.configurator.config.postgresql = config
                        self.log(f"Configured PostgreSQL: {pg_service.host}:{pg_service.port}")
                        break
            
            # Redis
            redis_services = [s for s in self.detected_services if s.service_type == 'redis']
            if redis_services:
                # Use the first running Redis
                for redis_service in redis_services:
                    if redis_service.is_running:
                        config = self.configurator.configure_from_detected_service(
                            redis_service,
                            ServiceMode.SHARE_EXISTING,
                            database_number=2
                        )
                        self.configurator.config.redis = config
                        self.log(f"Configured Redis: {redis_service.host}:{redis_service.port}")
                        break
            
            # 4. Generate secrets
            self.configurator.generate_secrets()
            self.log("Generated secure secret keys")
            
            # 5. Detect MAMS
            if self.configurator.detect_mams_path():
                self.log(f"Found MAMS at: {self.configurator.config.mams_base_path}")
            else:
                self.log("MAMS not found - will use fallback analysis", "warning")
            
            # 6. Validate configuration
            is_valid, issues = self.configurator.config.validate_config()
            
            if issues:
                for issue in issues:
                    self.log(issue, "warning")
            
            self.setup_complete = True
            return True, "Quick setup completed successfully"
            
        except Exception as e:
            error_msg = f"Quick setup failed: {str(e)}"
            self.log(error_msg, "error")
            return False, error_msg
    
    def custom_setup(self, config_options: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Custom setup with user-provided options
        
        Args:
            config_options: Dictionary of configuration options
            
        Returns:
            Tuple of (success, message)
        """
        self.log("Starting custom setup...")
        
        try:
            # Apply user configurations
            for key, value in config_options.items():
                if hasattr(self.configurator.config, key):
                    setattr(self.configurator.config, key, value)
            
            # Generate secrets if not provided
            if not self.configurator.config.ark_secret_key:
                self.configurator.generate_secrets()
            
            # Detect MAMS if not configured
            if not self.configurator.config.mams_base_path:
                self.configurator.detect_mams_path()
            
            # Validate configuration
            is_valid, issues = self.configurator.config.validate_config()
            
            if not is_valid:
                return False, f"Configuration invalid: {', '.join(issues)}"
            
            self.setup_complete = True
            return True, "Custom setup completed successfully"
            
        except Exception as e:
            error_msg = f"Custom setup failed: {str(e)}"
            self.log(error_msg, "error")
            return False, error_msg
    
    def save_configuration(self, output_dir: str = ".") -> Tuple[bool, List[str]]:
        """
        Save the configuration to files
        
        Args:
            output_dir: Directory to save configuration files
            
        Returns:
            Tuple of (success, list of created files)
        """
        if not self.setup_complete:
            self.log("Setup not complete, cannot save configuration", "error")
            return False, []
        
        self.log(f"Saving configuration to {output_dir}")
        
        output_path = Path(output_dir)
        success, files = self.configurator.config.save(output_path)
        
        if success:
            self.log(f"Configuration saved successfully: {', '.join(files)}")
        else:
            self.log("Failed to save configuration", "error")
        
        return success, files
    
    def get_setup_summary(self) -> Dict[str, Any]:
        """Get a summary of the setup configuration"""
        config = self.configurator.config
        
        summary = {
            'setup_complete': self.setup_complete,
            'deployment_mode': config.deployment_mode,
            'services': {},
            'features': {
                'websockets': config.enable_websockets,
                'monitoring': config.enable_monitoring,
                'security_scan': config.enable_security_scan
            },
            'integrations': {},
            'warnings': []
        }
        
        # Service summary
        if config.postgresql:
            summary['services']['postgresql'] = {
                'mode': config.postgresql.mode.value,
                'host': config.postgresql.host,
                'port': config.postgresql.port
            }
        
        if config.redis:
            summary['services']['redis'] = {
                'mode': config.redis.mode.value,
                'host': config.redis.host,
                'port': config.redis.port
            }
        
        # Integration summary
        if config.mams_base_path:
            summary['integrations']['mams'] = config.mams_base_path
        
        if config.openai_api_key:
            summary['integrations']['openai'] = 'configured'
        
        if config.anthropic_api_key:
            summary['integrations']['anthropic'] = 'configured'
        
        # Add warnings
        if not config.postgresql:
            summary['warnings'].append("No PostgreSQL configured - will use SQLite fallback")
        
        if not config.redis:
            summary['warnings'].append("No Redis configured - caching disabled")
        
        if not config.openai_api_key and not config.anthropic_api_key:
            summary['warnings'].append("No AI provider keys - AI features disabled")
        
        return summary
    
    def get_next_steps(self) -> List[str]:
        """Get next steps after setup"""
        steps = []
        
        if self.setup_complete:
            steps.append("1. Review the generated .env file")
            steps.append("2. Start services: docker-compose up -d")
            steps.append("3. Verify health: curl http://localhost:5000/health/detailed")
            steps.append("4. Run first analysis: /ark-analyze directory=/your/code")
            
            config = self.configurator.config
            
            if config.postgresql and not config.postgresql.credentials:
                steps.append("⚠️ Add PostgreSQL credentials to .env file")
            
            if config.mams_base_path and not Path(config.mams_base_path).exists():
                steps.append(f"⚠️ MAMS path not found: {config.mams_base_path}")
        else:
            steps.append("Complete setup before proceeding")
        
        return steps