"""
ARK-TOOLS API v1 Blueprint
==========================

Main blueprint for API v1 endpoints.
"""

from flask import Blueprint

from ark_tools.utils.debug_logger import debug_log

# Create the blueprint
api_v1_bp = Blueprint('api_v1', __name__)

# Import route modules to register them
from . import analysis_routes
from . import transformation_routes  
from . import project_routes
from . import agent_routes

debug_log.api("API v1 blueprint created with all routes")