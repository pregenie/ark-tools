"""
Integration tests for ARK-TOOLS setup system
============================================

Tests the complete setup workflow including detection, configuration, and validation.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from ark_tools.setup.orchestrator import SetupOrchestrator
from ark_tools.setup.detector import DetectedEnvironment, DetectedService
from ark_tools.setup.configurator import ServiceMode


class TestSetupIntegration:
    """Integration tests for setup system"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance"""
        return SetupOrchestrator()
    
    @pytest.fixture
    def mock_env_file(self):
        """Create a mock environment file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("DATABASE_URL=postgresql://user:pass@localhost:5432/db\n")
            f.write("REDIS_URL=redis://localhost:6379/0\n")
            f.write("OPENAI_API_KEY=sk-test123\n")
            f.write("PROJECT_NAME=test_project\n")
            f.name
        yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def mock_docker_services(self):
        """Mock Docker services"""
        return [
            DetectedService(
                service_type='postgresql',
                host='localhost',
                port=5432,
                source='docker',
                is_running=True,
                container_id='postgres123',
                container_name='postgres_container'
            ),
            DetectedService(
                service_type='redis',
                host='localhost',
                port=6379,
                source='docker',
                is_running=True,
                container_id='redis456',
                container_name='redis_container'
            )
        ]
    
    def test_quick_setup_workflow(self, orchestrator, mock_env_file, mock_docker_services):
        """Test quick setup workflow end-to-end"""
        # Mock environment detection
        mock_env = DetectedEnvironment(
            path=mock_env_file,
            project_name='test_project',
            has_database=True,
            has_redis=True,
            has_ai_keys=True
        )
        
        with patch.object(orchestrator.env_detector, 'scan_for_env_files', return_value=[mock_env]):
            with patch.object(orchestrator.service_detector, 'scan_docker_containers', return_value=mock_docker_services):
                # Run quick setup
                success, message = orchestrator.quick_setup(mock_env_file)
                
                assert success is True
                assert "successfully" in message.lower()
                assert orchestrator.setup_complete is True
                
                # Verify PostgreSQL configuration
                assert orchestrator.configurator.config.postgresql is not None
                assert orchestrator.configurator.config.postgresql.host == 'localhost'
                assert orchestrator.configurator.config.postgresql.port == 5432
                
                # Verify Redis configuration
                assert orchestrator.configurator.config.redis is not None
                assert orchestrator.configurator.config.redis.host == 'localhost'
                assert orchestrator.configurator.config.redis.port == 6379
                
                # Verify inherited API keys
                assert orchestrator.configurator.config.openai_api_key == 'sk-test123'
    
    def test_custom_setup_workflow(self, orchestrator):
        """Test custom setup with user-provided options"""
        config_options = {
            'deployment_mode': 'production',
            'enable_websockets': True,
            'enable_monitoring': True,
            'enable_security_scan': False
        }
        
        success, message = orchestrator.custom_setup(config_options)
        
        assert success is True
        assert orchestrator.setup_complete is True
        assert orchestrator.configurator.config.deployment_mode == 'production'
        assert orchestrator.configurator.config.enable_websockets is True
        assert orchestrator.configurator.config.enable_monitoring is True
        assert orchestrator.configurator.config.enable_security_scan is False
    
    @pytest.mark.asyncio
    async def test_connection_validation(self, orchestrator):
        """Test service connection validation"""
        # Mock successful PostgreSQL connection
        with patch.object(orchestrator.validator, 'test_postgresql', new_callable=AsyncMock) as mock_pg:
            mock_pg.return_value = {
                'connected': True,
                'version': 'PostgreSQL 14.5',
                'has_pgvector': True
            }
            
            # Mock successful Redis connection
            with patch.object(orchestrator.validator, 'test_redis', new_callable=AsyncMock) as mock_redis:
                mock_redis.return_value = {
                    'connected': True,
                    'version': '7.0.5'
                }
                
                # Configure services
                orchestrator.configurator.config.postgresql = MagicMock()
                orchestrator.configurator.config.postgresql.host = 'localhost'
                orchestrator.configurator.config.postgresql.port = 5432
                orchestrator.configurator.config.postgresql.credentials = {
                    'username': 'user',
                    'password': 'pass',
                    'database': 'test'
                }
                
                orchestrator.configurator.config.redis = MagicMock()
                orchestrator.configurator.config.redis.host = 'localhost'
                orchestrator.configurator.config.redis.port = 6379
                orchestrator.configurator.config.redis.credentials = {}
                orchestrator.configurator.config.redis.database_number = 0
                
                # Test connections
                results = await orchestrator.test_all_connections()
                
                assert 'postgresql' in results
                assert results['postgresql']['connected'] is True
                assert 'PostgreSQL 14.5' in results['postgresql']['message']
                
                assert 'redis' in results
                assert results['redis']['connected'] is True
                assert '7.0.5' in results['redis']['message']
    
    def test_configuration_save(self, orchestrator):
        """Test configuration file generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup configuration
            orchestrator.setup_complete = True
            orchestrator.configurator.config.ark_secret_key = 'test-secret'
            orchestrator.configurator.config.postgresql = MagicMock()
            orchestrator.configurator.config.postgresql.to_env_dict.return_value = {
                'DATABASE_URL': 'postgresql://localhost:5432/ark_tools'
            }
            
            # Mock the save method
            with patch.object(orchestrator.configurator.config, 'save') as mock_save:
                mock_save.return_value = (True, ['.env', 'docker-compose.yml'])
                
                success, files = orchestrator.save_configuration(tmpdir)
                
                assert success is True
                assert '.env' in files
                assert 'docker-compose.yml' in files
                mock_save.assert_called_once_with(Path(tmpdir))
    
    def test_environment_detection(self, orchestrator, mock_env_file):
        """Test environment file detection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test .env files
            env1 = Path(tmpdir) / '.env'
            env1.write_text("DATABASE_URL=postgresql://localhost/db1")
            
            env2 = Path(tmpdir) / 'project' / '.env'
            env2.parent.mkdir()
            env2.write_text("REDIS_URL=redis://localhost:6379")
            
            # Set search path
            orchestrator.env_detector.search_paths = [tmpdir]
            
            # Scan for env files
            envs = orchestrator.env_detector.scan_for_env_files()
            
            assert len(envs) >= 1
            env_paths = [env.path for env in envs]
            assert str(env1) in env_paths
    
    def test_service_detection_merge(self, orchestrator, mock_docker_services):
        """Test merging Docker and environment services"""
        # Mock Docker detection
        with patch.object(orchestrator.service_detector, 'scan_docker_containers', return_value=mock_docker_services):
            # Mock system service detection
            system_services = [
                DetectedService(
                    service_type='postgresql',
                    host='localhost',
                    port=5433,  # Different port
                    source='native',
                    is_running=True
                )
            ]
            with patch.object(orchestrator.service_detector, 'scan_system_services', return_value=system_services):
                # Mock environment with service info
                mock_env = DetectedEnvironment(
                    path='.env',
                    has_database=True,
                    env_data={'DATABASE_URL': 'postgresql://remote:5434/db'}
                )
                orchestrator.env_detector.detected_environments = [mock_env]
                
                # Merge services
                all_services = orchestrator.service_detector.merge_with_env_services(orchestrator.env_detector)
                
                # Should have Docker, system, and env services
                assert len(all_services) >= 3
                sources = [s.source for s in all_services]
                assert 'docker' in sources
                assert 'native' in sources
    
    def test_minimal_setup(self, orchestrator):
        """Test minimal setup without external dependencies"""
        orchestrator.configurator.create_minimal_config()
        
        assert orchestrator.configurator.config.deployment_mode == 'development'
        assert orchestrator.configurator.config.use_sqlite_fallback is True
        assert orchestrator.configurator.config.postgresql is None
        assert orchestrator.configurator.config.redis is None
        assert orchestrator.configurator.config.enable_monitoring is False
    
    def test_setup_summary(self, orchestrator):
        """Test setup summary generation"""
        # Configure services
        orchestrator.setup_complete = True
        orchestrator.configurator.config.deployment_mode = 'production'
        orchestrator.configurator.config.enable_websockets = True
        orchestrator.configurator.config.openai_api_key = 'sk-test'
        
        summary = orchestrator.get_setup_summary()
        
        assert summary['setup_complete'] is True
        assert summary['deployment_mode'] == 'production'
        assert summary['features']['websockets'] is True
        assert 'openai' in summary['integrations']
        
        # Should have warnings for missing services
        assert len(summary['warnings']) > 0
        assert any('PostgreSQL' in w for w in summary['warnings'])
        assert any('Redis' in w for w in summary['warnings'])
    
    @pytest.mark.asyncio
    async def test_async_detection(self, orchestrator, mock_docker_services):
        """Test async detection methods"""
        with patch.object(orchestrator.env_detector, 'scan_for_env_files', return_value=[]):
            envs = await orchestrator.detect_environment_async()
            assert isinstance(envs, list)
        
        with patch.object(orchestrator.service_detector, 'scan_docker_containers', return_value=mock_docker_services):
            with patch.object(orchestrator.service_detector, 'scan_system_services', return_value=[]):
                services = await orchestrator.detect_services_async()
                assert isinstance(services, list)
                assert len(services) >= len(mock_docker_services)


class TestSetupCLI:
    """Test CLI interface"""
    
    def test_cli_quick_setup(self):
        """Test CLI quick setup command"""
        from ark_tools.setup.cli import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('ark_tools.setup.cli.SetupOrchestrator') as mock_orchestrator:
            instance = mock_orchestrator.return_value
            instance.quick_setup.return_value = (True, "Setup successful")
            instance.save_configuration.return_value = (True, ['.env'])
            
            result = runner.invoke(cli, ['setup', '--mode', 'quick', '--parent-env', '.env'])
            
            assert result.exit_code == 0
            assert "✅" in result.output
            instance.quick_setup.assert_called_once()
    
    def test_cli_validate(self):
        """Test configuration validation command"""
        from ark_tools.setup.cli import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env') as f:
            f.write("DATABASE_URL=test")
            f.flush()
            
            with patch('ark_tools.setup.cli.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                
                with patch('ark_tools.setup.cli.SetupOrchestrator') as mock_orchestrator:
                    instance = mock_orchestrator.return_value
                    
                    # Mock async test
                    async def mock_test():
                        return {
                            'postgresql': {'connected': True, 'message': 'Connected'},
                            'redis': {'connected': False, 'message': 'Connection failed'}
                        }
                    
                    with patch('asyncio.run', return_value=mock_test()):
                        result = runner.invoke(cli, ['validate'])
                        
                        assert result.exit_code == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])