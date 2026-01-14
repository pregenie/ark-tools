"""
MAMS Core Module
================

Master Automated Migration System components for fast structural analysis.
"""

from .compressor import CodeCompressor

# Import key MAMS components if they exist
try:
    from .extractors.component_extractor import ComponentExtractor
except ImportError:
    ComponentExtractor = None

try:
    from .mams_008_dependency_resolution_engine import DependencyResolutionEngine
except ImportError:
    DependencyResolutionEngine = None

__all__ = [
    'CodeCompressor',
    'ComponentExtractor',
    'DependencyResolutionEngine'
]