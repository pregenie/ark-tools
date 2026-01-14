"""
System Resource Checker
=======================

Checks system resources and Docker capacity for ARK-TOOLS deployment.
"""

import subprocess
import json
import psutil
import platform
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemResources:
    """System resource information"""
    # CPU
    cpu_count: int
    cpu_percent: float
    
    # Memory
    memory_total_gb: float
    memory_available_gb: float
    memory_percent: float
    
    # Disk
    disk_total_gb: float
    disk_available_gb: float
    disk_percent: float
    
    # Docker
    docker_available: bool
    docker_running_containers: int
    docker_images_size_gb: float
    docker_containers_size_gb: float
    
    # Platform
    platform: str
    python_version: str
    
    # Recommendations
    can_run_ark_tools: bool
    warnings: List[str]
    recommendations: List[str]


class SystemChecker:
    """
    Check system resources and provide recommendations for ARK-TOOLS deployment
    """
    
    # Minimum requirements
    MIN_MEMORY_GB = 2.0  # Minimum RAM for basic operation
    RECOMMENDED_MEMORY_GB = 4.0  # Recommended RAM for smooth operation
    MIN_DISK_GB = 5.0  # Minimum disk space
    RECOMMENDED_DISK_GB = 10.0  # Recommended disk space
    MIN_CPU_CORES = 2  # Minimum CPU cores
    RECOMMENDED_CPU_CORES = 4  # Recommended CPU cores
    
    def check_system_resources(self) -> SystemResources:
        """
        Comprehensive system resource check
        
        Returns:
            SystemResources object with all system information
        """
        warnings = []
        recommendations = []
        
        # CPU Information
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_count < self.MIN_CPU_CORES:
            warnings.append(f"⚠️ Only {cpu_count} CPU cores detected. Minimum {self.MIN_CPU_CORES} recommended.")
        elif cpu_count < self.RECOMMENDED_CPU_CORES:
            recommendations.append(f"💡 {cpu_count} CPU cores detected. {self.RECOMMENDED_CPU_CORES} cores recommended for better performance.")
        
        # Memory Information
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        memory_percent = memory.percent
        
        if memory_available_gb < self.MIN_MEMORY_GB:
            warnings.append(f"⚠️ Only {memory_available_gb:.1f}GB RAM available. Minimum {self.MIN_MEMORY_GB}GB required.")
        elif memory_available_gb < self.RECOMMENDED_MEMORY_GB:
            recommendations.append(f"💡 {memory_available_gb:.1f}GB RAM available. {self.RECOMMENDED_MEMORY_GB}GB recommended for smooth operation.")
        
        # Disk Information
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024**3)
        disk_available_gb = disk.free / (1024**3)
        disk_percent = disk.percent
        
        if disk_available_gb < self.MIN_DISK_GB:
            warnings.append(f"⚠️ Only {disk_available_gb:.1f}GB disk space available. Minimum {self.MIN_DISK_GB}GB required.")
        elif disk_available_gb < self.RECOMMENDED_DISK_GB:
            recommendations.append(f"💡 {disk_available_gb:.1f}GB disk space available. {self.RECOMMENDED_DISK_GB}GB recommended.")
        
        # Docker Information
        docker_info = self._check_docker_resources()
        
        if not docker_info['available']:
            warnings.append("⚠️ Docker is not available. ARK-TOOLS requires Docker for containerized execution.")
            recommendations.append("💡 Install Docker Desktop or Docker Engine to run ARK-TOOLS in containers.")
        elif docker_info['running_containers'] > 20:
            recommendations.append(f"💡 {docker_info['running_containers']} containers running. Consider stopping unused containers.")
        
        # Platform Information
        platform_info = platform.system()
        python_version = platform.python_version()
        
        # Determine if system can run ARK-TOOLS
        can_run = len(warnings) == 0
        
        # Add alternatives if system is constrained
        if not can_run:
            if memory_available_gb < self.MIN_MEMORY_GB:
                recommendations.append("🔄 Alternative: Use cloud-based deployment (AWS/GCP/Azure)")
                recommendations.append("🔄 Alternative: Use lightweight mode with SQLite instead of PostgreSQL")
            
            if not docker_info['available']:
                recommendations.append("🔄 Alternative: Run ARK-TOOLS directly on host (less isolated)")
        
        return SystemResources(
            cpu_count=cpu_count,
            cpu_percent=cpu_percent,
            memory_total_gb=memory_total_gb,
            memory_available_gb=memory_available_gb,
            memory_percent=memory_percent,
            disk_total_gb=disk_total_gb,
            disk_available_gb=disk_available_gb,
            disk_percent=disk_percent,
            docker_available=docker_info['available'],
            docker_running_containers=docker_info['running_containers'],
            docker_images_size_gb=docker_info['images_size_gb'],
            docker_containers_size_gb=docker_info['containers_size_gb'],
            platform=platform_info,
            python_version=python_version,
            can_run_ark_tools=can_run,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _check_docker_resources(self) -> Dict[str, Any]:
        """Check Docker-specific resources"""
        result = {
            'available': False,
            'running_containers': 0,
            'images_size_gb': 0.0,
            'containers_size_gb': 0.0
        }
        
        try:
            # Check if Docker is available
            version_result = subprocess.run(
                ['docker', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if version_result.returncode != 0:
                return result
            
            result['available'] = True
            
            # Get Docker system df for space usage
            df_result = subprocess.run(
                ['docker', 'system', 'df', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if df_result.returncode == 0:
                df_data = json.loads(df_result.stdout)
                
                # Parse images size
                if 'Images' in df_data:
                    for item in df_data['Images']:
                        if item.get('Type') == 'Images':
                            size_str = item.get('Size', '0')
                            result['images_size_gb'] = self._parse_size_to_gb(size_str)
                
                # Parse containers size
                if 'Containers' in df_data:
                    for item in df_data['Containers']:
                        if item.get('Type') == 'Containers':
                            size_str = item.get('Size', '0')
                            result['containers_size_gb'] = self._parse_size_to_gb(size_str)
            
            # Count running containers
            ps_result = subprocess.run(
                ['docker', 'ps', '-q'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if ps_result.returncode == 0:
                container_ids = ps_result.stdout.strip().split('\n')
                result['running_containers'] = len([c for c in container_ids if c])
            
        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            pass
        
        return result
    
    def _parse_size_to_gb(self, size_str: str) -> float:
        """Parse Docker size string to GB"""
        try:
            # Remove any extra text
            size_str = size_str.strip()
            
            # Parse different units
            if 'GB' in size_str:
                return float(size_str.replace('GB', '').strip())
            elif 'MB' in size_str:
                return float(size_str.replace('MB', '').strip()) / 1024
            elif 'KB' in size_str:
                return float(size_str.replace('KB', '').strip()) / (1024 * 1024)
            elif 'B' in size_str:
                return float(size_str.replace('B', '').strip()) / (1024 * 1024 * 1024)
            else:
                return 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def get_deployment_recommendation(self, resources: SystemResources) -> str:
        """
        Get deployment recommendation based on system resources
        
        Args:
            resources: System resources information
            
        Returns:
            Deployment recommendation string
        """
        if not resources.can_run_ark_tools:
            return "minimal"  # Use minimal setup with SQLite
        
        if resources.memory_available_gb >= self.RECOMMENDED_MEMORY_GB and \
           resources.disk_available_gb >= self.RECOMMENDED_DISK_GB and \
           resources.docker_available:
            return "full"  # Full containerized deployment
        
        if resources.docker_available:
            return "standard"  # Standard containerized deployment
        
        return "hybrid"  # Mix of containers and host services