"""
Environment and Service Detection
==================================

Detects existing environment files, Docker containers, and services
that ARK-TOOLS can integrate with.
"""

import os
import json
import subprocess
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import logging
from urllib.parse import urlparse
import socket

logger = logging.getLogger(__name__)

@dataclass
class DetectedService:
    """Represents a detected service"""
    service_type: str  # postgresql, redis, etc.
    source: str  # docker, native, env_file
    host: str
    port: int
    container_name: Optional[str] = None
    container_id: Optional[str] = None
    version: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    env_file: Optional[str] = None
    is_running: bool = False
    compatible: bool = True
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

@dataclass
class DetectedEnvironment:
    """Represents a detected environment file"""
    path: str
    project_name: Optional[str] = None
    services: List[str] = None
    has_database: bool = False
    has_redis: bool = False
    has_ai_keys: bool = False
    variables: Dict[str, str] = None
    
    def __post_init__(self):
        if self.services is None:
            self.services = []
        if self.variables is None:
            self.variables = {}

class EnvironmentDetector:
    """
    Detects and analyzes environment files in the system
    """
    
    def __init__(self, search_paths: Optional[List[str]] = None):
        """
        Initialize environment detector
        
        Args:
            search_paths: Paths to search for env files
        """
        self.search_paths = search_paths or self._get_default_search_paths()
        self.detected_envs: List[DetectedEnvironment] = []
        
    def _get_default_search_paths(self) -> List[str]:
        """Get default paths to search for env files"""
        current_dir = Path.cwd()
        parent_dir = current_dir.parent
        
        paths = [
            str(current_dir),
            str(parent_dir),
            str(parent_dir / "*"),  # Sibling directories
            os.path.expanduser("~/.config"),
            os.path.expanduser("~/.docker"),
        ]
        
        return paths
    
    def scan_for_env_files(self) -> List[DetectedEnvironment]:
        """
        Scan for environment files in search paths
        
        Returns:
            List of detected environment files
        """
        env_patterns = ['.env', '.env.*', '*.env']
        detected = []
        seen_paths = set()
        
        for search_path in self.search_paths:
            base_path = Path(search_path)
            
            # Handle glob patterns
            if '*' in search_path:
                parent = base_path.parent
                pattern = base_path.name
                if parent.exists():
                    for path in parent.glob(pattern):
                        if path.is_dir():
                            self._scan_directory(path, env_patterns, detected, seen_paths)
            elif base_path.exists():
                if base_path.is_dir():
                    self._scan_directory(base_path, env_patterns, detected, seen_paths)
                elif base_path.is_file() and base_path.name.startswith('.env'):
                    if str(base_path) not in seen_paths:
                        env = self._analyze_env_file(base_path)
                        if env:
                            detected.append(env)
                            seen_paths.add(str(base_path))
        
        self.detected_envs = detected
        return detected
    
    def _scan_directory(self, directory: Path, patterns: List[str], 
                        detected: List[DetectedEnvironment], seen_paths: set) -> None:
        """Scan a directory for env files"""
        for pattern in patterns:
            for env_file in directory.glob(pattern):
                if env_file.is_file() and str(env_file) not in seen_paths:
                    # Skip .env.example files
                    if 'example' in env_file.name.lower():
                        continue
                        
                    env = self._analyze_env_file(env_file)
                    if env:
                        detected.append(env)
                        seen_paths.add(str(env_file))
    
    def _analyze_env_file(self, file_path: Path) -> Optional[DetectedEnvironment]:
        """
        Analyze an environment file
        
        Args:
            file_path: Path to env file
            
        Returns:
            DetectedEnvironment or None if cannot read
        """
        try:
            variables = {}
            services = []
            
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # Don't store sensitive values in memory
                        if any(sensitive in key.lower() for sensitive in 
                               ['password', 'secret', 'key', 'token']):
                            variables[key] = '***MASKED***'
                        else:
                            variables[key] = value
            
            # Detect services based on variable names
            env = DetectedEnvironment(
                path=str(file_path),
                project_name=file_path.parent.name,
                variables=variables
            )
            
            # Check for database
            db_vars = ['DATABASE_URL', 'POSTGRES_URL', 'DB_URL', 'POSTGRES_HOST']
            if any(var in variables for var in db_vars):
                env.has_database = True
                env.services.append('postgresql')
            
            # Check for Redis
            redis_vars = ['REDIS_URL', 'REDIS_HOST', 'CACHE_URL']
            if any(var in variables for var in redis_vars):
                env.has_redis = True
                env.services.append('redis')
            
            # Check for AI keys
            ai_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'CLAUDE_API_KEY']
            if any(var in variables for var in ai_vars):
                env.has_ai_keys = True
                env.services.append('ai_services')
            
            return env
            
        except Exception as e:
            logger.warning(f"Could not read env file {file_path}: {e}")
            return None
    
    def get_parent_project_env(self) -> Optional[DetectedEnvironment]:
        """
        Try to find the most likely parent project env file
        
        Returns:
            Best candidate parent environment or None
        """
        if not self.detected_envs:
            return None
        
        # Prioritize by:
        # 1. Sibling directories with 'arkyvus' in name
        # 2. Parent directory
        # 3. Most services available
        
        for env in self.detected_envs:
            if 'arkyvus' in env.project_name.lower():
                return env
        
        # Check parent directory
        parent_path = str(Path.cwd().parent)
        for env in self.detected_envs:
            if Path(env.path).parent == Path(parent_path):
                return env
        
        # Return the one with most services
        return max(self.detected_envs, 
                   key=lambda e: len(e.services),
                   default=None)

class ServiceDetector:
    """
    Detects running services through Docker and system inspection
    """
    
    def __init__(self):
        self.detected_services: List[DetectedService] = []
        self.docker_available = self._check_docker_available()
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is available and running"""
        try:
            result = subprocess.run(['docker', 'version'], 
                                    capture_output=True, 
                                    text=True,
                                    timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def scan_docker_containers(self) -> List[DetectedService]:
        """
        Scan running Docker containers for services
        
        Returns:
            List of detected services from Docker
        """
        if not self.docker_available:
            logger.info("Docker not available, skipping container scan")
            return []
        
        services = []
        
        try:
            # Get all running containers with their details
            result = subprocess.run(
                ['docker', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            container = json.loads(line)
                            service = self._analyze_container(container)
                            if service:
                                services.append(service)
                        except json.JSONDecodeError:
                            continue
            
            # Get more detailed information for each container
            for service in services:
                if service.container_id:
                    self._enrich_container_info(service)
            
        except subprocess.SubprocessError as e:
            logger.warning(f"Error scanning Docker containers: {e}")
        
        self.detected_services.extend(services)
        return services
    
    def _analyze_container(self, container: Dict[str, Any]) -> Optional[DetectedService]:
        """
        Analyze a Docker container to detect service type
        
        Args:
            container: Docker container info
            
        Returns:
            DetectedService or None
        """
        image = container.get('Image', '').lower()
        names = container.get('Names', '').lower()
        ports = container.get('Ports', '')
        
        # Detect PostgreSQL
        if any(pg in image for pg in ['postgres', 'pgvector', 'timescale']):
            port = self._extract_port(ports, 5432)
            return DetectedService(
                service_type='postgresql',
                source='docker',
                host='localhost',
                port=port,
                container_name=container.get('Names'),
                container_id=container.get('ID'),
                is_running=container.get('State') == 'running'
            )
        
        # Detect Redis
        elif 'redis' in image:
            port = self._extract_port(ports, 6379)
            return DetectedService(
                service_type='redis',
                source='docker',
                host='localhost',
                port=port,
                container_name=container.get('Names'),
                container_id=container.get('ID'),
                is_running=container.get('State') == 'running'
            )
        
        # Detect MongoDB
        elif 'mongo' in image:
            port = self._extract_port(ports, 27017)
            return DetectedService(
                service_type='mongodb',
                source='docker',
                host='localhost',
                port=port,
                container_name=container.get('Names'),
                container_id=container.get('ID'),
                is_running=container.get('State') == 'running'
            )
        
        return None
    
    def _extract_port(self, ports_string: str, default_port: int) -> int:
        """Extract port from Docker ports string"""
        if not ports_string:
            return default_port
        
        # Parse ports like "0.0.0.0:5432->5432/tcp"
        match = re.search(r':(\d+)->', ports_string)
        if match:
            return int(match.group(1))
        
        return default_port
    
    def _enrich_container_info(self, service: DetectedService) -> None:
        """
        Get additional information about a container
        
        Args:
            service: Service to enrich with more info
        """
        if not service.container_id:
            return
        
        try:
            # Get container environment variables
            result = subprocess.run(
                ['docker', 'inspect', service.container_id],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                inspect_data = json.loads(result.stdout)
                if inspect_data and len(inspect_data) > 0:
                    container_info = inspect_data[0]
                    
                    # Get version from environment or labels
                    env_vars = container_info.get('Config', {}).get('Env', [])
                    for env_var in env_vars:
                        if 'VERSION' in env_var:
                            _, version = env_var.split('=', 1)
                            service.version = version
                            break
                    
                    # Check for specific features
                    if service.service_type == 'postgresql':
                        # Check for pgvector extension
                        if 'pgvector' in container_info.get('Config', {}).get('Image', ''):
                            service.compatible = True
                        else:
                            service.warnings.append('pgvector extension may not be available')
                    
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            logger.warning(f"Could not enrich container info: {e}")
    
    def scan_system_services(self) -> List[DetectedService]:
        """
        Scan for services running natively on the system
        
        Returns:
            List of detected system services
        """
        services = []
        
        # Check common service ports
        service_ports = [
            ('postgresql', 5432),
            ('redis', 6379),
            ('mongodb', 27017),
            ('mysql', 3306),
        ]
        
        for service_type, port in service_ports:
            if self._is_port_open('localhost', port):
                # Verify it's actually the expected service
                if service_type == 'postgresql' and self._verify_postgresql(port):
                    services.append(DetectedService(
                        service_type='postgresql',
                        source='native',
                        host='localhost',
                        port=port,
                        is_running=True
                    ))
                elif service_type == 'redis' and self._verify_redis(port):
                    services.append(DetectedService(
                        service_type='redis',
                        source='native',
                        host='localhost',
                        port=port,
                        is_running=True
                    ))
        
        self.detected_services.extend(services)
        return services
    
    def _is_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except socket.error:
            return False
    
    def _verify_postgresql(self, port: int) -> bool:
        """Verify if a service is PostgreSQL"""
        try:
            # Try to connect with psql
            result = subprocess.run(
                ['psql', '-h', 'localhost', '-p', str(port), '-c', '\\l'],
                capture_output=True,
                text=True,
                timeout=2
            )
            # Check if it asks for password or connects
            return 'password' in result.stderr.lower() or result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _verify_redis(self, port: int) -> bool:
        """Verify if a service is Redis"""
        try:
            result = subprocess.run(
                ['redis-cli', '-p', str(port), 'ping'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return 'PONG' in result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def merge_with_env_services(self, env_detector: EnvironmentDetector) -> List[DetectedService]:
        """
        Merge detected services with environment file information
        
        Args:
            env_detector: Environment detector with found env files
            
        Returns:
            Enriched list of services with credentials
        """
        enriched_services = self.detected_services.copy()
        
        for env in env_detector.detected_envs:
            # Parse database URLs
            for key, value in env.variables.items():
                if 'DATABASE_URL' in key or 'POSTGRES' in key:
                    service = self._parse_database_url(value, env.path)
                    if service:
                        # Try to match with existing detected service
                        matched = False
                        for detected in enriched_services:
                            if (detected.service_type == service.service_type and
                                detected.port == service.port):
                                # Enrich with env info
                                detected.env_file = env.path
                                if not detected.credentials:
                                    detected.credentials = service.credentials
                                matched = True
                                break
                        
                        if not matched:
                            enriched_services.append(service)
                
                elif 'REDIS' in key:
                    service = self._parse_redis_url(value, env.path)
                    if service:
                        # Similar matching logic
                        matched = False
                        for detected in enriched_services:
                            if (detected.service_type == 'redis' and
                                detected.port == service.port):
                                detected.env_file = env.path
                                if not detected.credentials:
                                    detected.credentials = service.credentials
                                matched = True
                                break
                        
                        if not matched:
                            enriched_services.append(service)
        
        return enriched_services
    
    def _parse_database_url(self, url: str, env_file: str) -> Optional[DetectedService]:
        """Parse a database URL into a service"""
        if url == '***MASKED***':
            return None
        
        try:
            parsed = urlparse(url)
            
            return DetectedService(
                service_type='postgresql',
                source='env_file',
                host=parsed.hostname or 'localhost',
                port=parsed.port or 5432,
                env_file=env_file,
                credentials={
                    'username': parsed.username,
                    'password': '***MASKED***',
                    'database': parsed.path.lstrip('/') if parsed.path else None
                }
            )
        except Exception:
            return None
    
    def _parse_redis_url(self, url: str, env_file: str) -> Optional[DetectedService]:
        """Parse a Redis URL into a service"""
        if url == '***MASKED***':
            return None
        
        try:
            parsed = urlparse(url)
            
            return DetectedService(
                service_type='redis',
                source='env_file',
                host=parsed.hostname or 'localhost',
                port=parsed.port or 6379,
                env_file=env_file,
                credentials={
                    'password': '***MASKED***' if parsed.password else None,
                    'database': parsed.path.lstrip('/') if parsed.path else '0'
                }
            )
        except Exception:
            return None