"""
ARK-TOOLS Setup System
======================

Intelligent setup system with environment detection, service discovery,
and both CLI and Web UI configuration interfaces.
"""

from .detector import EnvironmentDetector, ServiceDetector
from .configurator import SetupConfigurator
from .orchestrator import SetupOrchestrator
from .cli import SetupCLI
from .web import create_setup_app

__all__ = [
    'EnvironmentDetector',
    'ServiceDetector',
    'SetupConfigurator',
    'SetupOrchestrator',
    'SetupCLI',
    'create_setup_app'
]