"""
Health Check API Routes
======================

Health check endpoints for monitoring and load balancer integration.
"""

from datetime import datetime
from flask import Blueprint, jsonify
import sys

from ark_tools import config
from ark_tools.database.base import db_manager
from ark_tools.utils.debug_logger import debug_log

health_bp = Blueprint('health', __name__)

@health_bp.route('/', methods=['GET'])
@health_bp.route('/ping', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    
    GET /health/
    GET /health/ping
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'ark-tools-api',
        'version': config.VERSION
    }), 200

@health_bp.route('/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with component status
    
    GET /health/detailed
    """
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ark-tools-api',
            'version': config.VERSION,
            'checks': {}
        }
        
        # Database health check
        try:
            db_status = db_manager.check_connection()
            health_status['checks']['database'] = {
                'status': 'healthy' if db_status['connected'] else 'unhealthy',
                'details': db_status
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Python environment check
        health_status['checks']['python'] = {
            'status': 'healthy',
            'version': sys.version,
            'platform': sys.platform
        }
        
        # Configuration check
        config_validation = config.validate_environment()
        health_status['checks']['configuration'] = {
            'status': 'healthy' if config_validation['valid'] else 'degraded',
            'issues': config_validation['issues'],
            'warnings': config_validation['warnings']
        }
        
        # MAMS integration check
        try:
            import os
            mams_path = config.MAMS_MIGRATIONS_PATH
            mams_exists = os.path.exists(mams_path)
            health_status['checks']['mams_integration'] = {
                'status': 'healthy' if mams_exists else 'degraded',
                'path': mams_path,
                'accessible': mams_exists
            }
        except Exception as e:
            health_status['checks']['mams_integration'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Determine overall status
        check_statuses = [check['status'] for check in health_status['checks'].values()]
        if 'unhealthy' in check_statuses:
            health_status['status'] = 'unhealthy'
            status_code = 503
        elif 'degraded' in check_statuses:
            health_status['status'] = 'degraded'
            status_code = 200
        else:
            status_code = 200
        
        debug_log.api(f"Health check completed: {health_status['status']}")
        return jsonify(health_status), status_code
    
    except Exception as e:
        debug_log.error_trace("Health check failed", exception=e)
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration
    
    GET /health/ready
    """
    try:
        # Check if service is ready to accept traffic
        ready_checks = []
        
        # Database connectivity
        try:
            db_status = db_manager.check_connection()
            if db_status['connected']:
                ready_checks.append(True)
            else:
                ready_checks.append(False)
        except:
            ready_checks.append(False)
        
        # Basic functionality
        ready_checks.append(True)  # API is responding
        
        is_ready = all(ready_checks)
        
        return jsonify({
            'ready': is_ready,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'ark-tools-api'
        }), 200 if is_ready else 503
    
    except Exception as e:
        debug_log.error_trace("Readiness check failed", exception=e)
        return jsonify({
            'ready': False,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """
    Liveness check for Kubernetes/container orchestration
    
    GET /health/live
    """
    # Simple liveness check - if we can respond, we're alive
    return jsonify({
        'alive': True,
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'ark-tools-api'
    }), 200