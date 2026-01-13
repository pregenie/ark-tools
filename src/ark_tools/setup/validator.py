"""
Service Connection Validator
============================

Tests connections to services before committing to configuration.
"""

import asyncio
import socket
import subprocess
from typing import Dict, Any, Optional, Tuple
import logging

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

try:
    import redis.asyncio as aioredis
    AIOREDIS_AVAILABLE = True
except ImportError:
    AIOREDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class ConnectionValidator:
    """
    Validates connections to various services
    """
    
    async def test_postgresql(
        self,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        timeout: int = 5
    ) -> Dict[str, Any]:
        """
        Test PostgreSQL connection
        
        Args:
            host: Database host
            port: Database port
            username: Database username
            password: Database password
            database: Database name
            timeout: Connection timeout
            
        Returns:
            Dict with connection test results
        """
        result = {
            'connected': False,
            'error': None,
            'version': None,
            'has_pgvector': False,
            'database_exists': False,
            'can_create_database': False
        }
        
        # First check if port is open
        if not self._is_port_open(host, port, timeout):
            result['error'] = f"Cannot connect to {host}:{port}"
            return result
        
        if ASYNCPG_AVAILABLE:
            try:
                # Try to connect to postgres database first
                conn_string = f"postgresql://{username or 'postgres'}:{password or ''}@{host}:{port}/postgres"
                
                conn = await asyncio.wait_for(
                    asyncpg.connect(conn_string),
                    timeout=timeout
                )
                
                try:
                    # Get version
                    version = await conn.fetchval("SELECT version()")
                    result['version'] = version
                    result['connected'] = True
                    
                    # Check for pgvector
                    extensions = await conn.fetch(
                        "SELECT extname FROM pg_extension WHERE extname = 'vector'"
                    )
                    result['has_pgvector'] = len(extensions) > 0
                    
                    # Check if target database exists
                    if database:
                        databases = await conn.fetch(
                            "SELECT datname FROM pg_database WHERE datname = $1",
                            database
                        )
                        result['database_exists'] = len(databases) > 0
                    
                    # Check if we can create databases
                    current_user = await conn.fetchval("SELECT current_user")
                    can_create = await conn.fetchval(
                        "SELECT rolcreatedb FROM pg_roles WHERE rolname = $1",
                        current_user
                    )
                    result['can_create_database'] = bool(can_create)
                    
                finally:
                    await conn.close()
                    
            except asyncio.TimeoutError:
                result['error'] = "Connection timeout"
            except Exception as e:
                result['error'] = str(e)
                
                # Try fallback connection test with psql
                if not result['connected']:
                    result = self._test_postgresql_fallback(host, port, username, password, database)
        else:
            # Use fallback method
            result = self._test_postgresql_fallback(host, port, username, password, database)
        
        return result
    
    def _test_postgresql_fallback(
        self,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback PostgreSQL test using psql command"""
        result = {
            'connected': False,
            'error': None,
            'version': None,
            'has_pgvector': False,
            'database_exists': False,
            'can_create_database': False
        }
        
        try:
            # Build psql command
            cmd = ['psql', '-h', host, '-p', str(port)]
            
            if username:
                cmd.extend(['-U', username])
            
            if database:
                cmd.extend(['-d', database])
            else:
                cmd.extend(['-d', 'postgres'])
            
            cmd.extend(['-c', '\\l'])
            
            # Set password via environment
            env = {}
            if password:
                env['PGPASSWORD'] = password
            
            # Run command
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                env=env
            )
            
            if process.returncode == 0:
                result['connected'] = True
                # Parse output for database list
                if database and database in process.stdout:
                    result['database_exists'] = True
            else:
                if 'password authentication failed' in process.stderr:
                    result['error'] = "Authentication failed"
                elif 'does not exist' in process.stderr:
                    result['error'] = f"Database {database} does not exist"
                else:
                    result['error'] = process.stderr.strip()
                    
        except subprocess.TimeoutExpired:
            result['error'] = "Connection timeout"
        except FileNotFoundError:
            result['error'] = "psql command not found"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    async def test_redis(
        self,
        host: str,
        port: int,
        password: Optional[str] = None,
        database: int = 0,
        timeout: int = 5
    ) -> Dict[str, Any]:
        """
        Test Redis connection
        
        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            database: Database number
            timeout: Connection timeout
            
        Returns:
            Dict with connection test results
        """
        result = {
            'connected': False,
            'error': None,
            'version': None,
            'memory_usage': None,
            'is_cluster': False
        }
        
        # First check if port is open
        if not self._is_port_open(host, port, timeout):
            result['error'] = f"Cannot connect to {host}:{port}"
            return result
        
        if AIOREDIS_AVAILABLE:
            try:
                # Create Redis connection
                url = f"redis://:{password}@{host}:{port}/{database}" if password else f"redis://{host}:{port}/{database}"
                
                redis = aioredis.from_url(url, socket_connect_timeout=timeout)
                
                try:
                    # Test connection with PING
                    pong = await asyncio.wait_for(redis.ping(), timeout=timeout)
                    if pong:
                        result['connected'] = True
                    
                    # Get server info
                    info = await redis.info()
                    result['version'] = info.get('redis_version', 'unknown')
                    
                    # Get memory usage
                    result['memory_usage'] = info.get('used_memory_human', 'unknown')
                    
                    # Check if cluster mode
                    result['is_cluster'] = info.get('cluster_enabled', 0) == 1
                    
                finally:
                    await redis.close()
                    
            except asyncio.TimeoutError:
                result['error'] = "Connection timeout"
            except Exception as e:
                error_str = str(e)
                if 'NOAUTH' in error_str:
                    result['error'] = "Authentication required"
                elif 'wrong password' in error_str.lower():
                    result['error'] = "Invalid password"
                else:
                    result['error'] = error_str
        else:
            # Use fallback method
            result = self._test_redis_fallback(host, port, password, database)
        
        return result
    
    def _test_redis_fallback(
        self,
        host: str,
        port: int,
        password: Optional[str] = None,
        database: int = 0
    ) -> Dict[str, Any]:
        """Fallback Redis test using redis-cli command"""
        result = {
            'connected': False,
            'error': None,
            'version': None,
            'memory_usage': None,
            'is_cluster': False
        }
        
        try:
            # Build redis-cli command
            cmd = ['redis-cli', '-h', host, '-p', str(port)]
            
            if password:
                cmd.extend(['-a', password])
            
            if database != 0:
                cmd.extend(['-n', str(database)])
            
            cmd.append('ping')
            
            # Run command
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if process.returncode == 0 and 'PONG' in process.stdout:
                result['connected'] = True
                
                # Try to get version
                version_cmd = cmd[:-1] + ['info', 'server']
                version_process = subprocess.run(
                    version_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if version_process.returncode == 0:
                    for line in version_process.stdout.split('\n'):
                        if line.startswith('redis_version:'):
                            result['version'] = line.split(':')[1].strip()
                            break
            else:
                if 'NOAUTH' in process.stderr:
                    result['error'] = "Authentication required"
                elif 'invalid password' in process.stderr.lower():
                    result['error'] = "Invalid password"
                else:
                    result['error'] = process.stderr.strip() or "Connection failed"
                    
        except subprocess.TimeoutExpired:
            result['error'] = "Connection timeout"
        except FileNotFoundError:
            result['error'] = "redis-cli command not found"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _is_port_open(self, host: str, port: int, timeout: int = 5) -> bool:
        """
        Check if a port is open on a host
        
        Args:
            host: Host to check
            port: Port to check
            timeout: Connection timeout
            
        Returns:
            True if port is open
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except socket.error:
            return False
    
    async def test_all_services(self, services: list) -> Dict[str, Any]:
        """
        Test all configured services
        
        Args:
            services: List of service configurations
            
        Returns:
            Dict with test results for all services
        """
        results = {}
        
        for service in services:
            if service.get('type') == 'postgresql':
                result = await self.test_postgresql(
                    service.get('host', 'localhost'),
                    service.get('port', 5432),
                    service.get('username'),
                    service.get('password'),
                    service.get('database')
                )
                results['postgresql'] = result
                
            elif service.get('type') == 'redis':
                result = await self.test_redis(
                    service.get('host', 'localhost'),
                    service.get('port', 6379),
                    service.get('password'),
                    service.get('database', 0)
                )
                results['redis'] = result
        
        return results
    
    def check_pgvector_installation_command(self, os_type: str = 'linux') -> str:
        """
        Get the command to install pgvector based on OS
        
        Args:
            os_type: Operating system type (linux, macos, windows)
            
        Returns:
            Installation command string
        """
        commands = {
            'linux': "sudo apt-get install postgresql-14-pgvector",
            'macos': "brew install pgvector",
            'docker': "docker exec -it postgres_container psql -U postgres -c 'CREATE EXTENSION vector;'",
            'windows': "Download from https://github.com/pgvector/pgvector/releases"
        }
        
        return commands.get(os_type, commands['linux'])