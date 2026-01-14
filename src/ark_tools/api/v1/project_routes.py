"""
Project API Routes
==================

API endpoints for project management.
"""

from flask import Blueprint, request, jsonify

# Create blueprint (placeholder for now)
project_bp = Blueprint('project', __name__)

@project_bp.route('/list', methods=['GET'])
def list_projects():
    """List projects (placeholder)."""
    return jsonify({'message': 'Project routes not yet implemented'}), 501