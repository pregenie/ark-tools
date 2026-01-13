"""
ARK-TOOLS Specialized Agents
============================

AI-powered specialized agents that handle different aspects of code analysis
and transformation through coordinated agentic workflows.

Available Agents:
- ark-architect: System design integrity and architecture enforcement
- ark-detective: Pattern detection and consolidation opportunity identification  
- ark-transformer: Safe code transformation using LibCST
- ark-guardian: Test generation and regression prevention
"""

from .base import BaseAgent, AgentResult
from .architect import ArchitectAgent
from .detective import DetectiveAgent
from .transformer import TransformerAgent
from .guardian import GuardianAgent
from .coordinator import AgentCoordinator

__all__ = [
    'BaseAgent',
    'AgentResult',
    'ArchitectAgent', 
    'DetectiveAgent',
    'TransformerAgent',
    'GuardianAgent',
    'AgentCoordinator'
]