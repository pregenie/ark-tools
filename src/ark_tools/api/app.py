"""
ARK-TOOLS Flask Application Factory
==================================

Creates and configures the Flask application with all necessary components.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

from ark_tools import config
from ark_tools.utils.debug_logger import debug_log
from ark_tools.database.base import db_manager

logger = logging.getLogger(__name__)

def create_app(config_dict: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure Flask application
    
    Args:
        config_dict: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Configure Flask app
    _configure_app(app, config_dict)
    
    # Initialize extensions
    _initialize_extensions(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Setup error handlers
    _setup_error_handlers(app)
    
    # Setup request/response hooks
    _setup_request_hooks(app)
    
    debug_log.api("Flask application created and configured")
    
    return app

def _configure_app(app: Flask, config_dict: Optional[Dict[str, Any]] = None) -> None:
    """Configure Flask application settings"""
    
    # Basic Flask configuration
    app.config.update({
        'SECRET_KEY': config.SECRET_KEY,
        'DEBUG': os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        'TESTING': os.getenv('FLASK_TESTING', 'false').lower() == 'true',
        
        # Database configuration
        'DATABASE_URL': config.DATABASE_URL,
        
        # CORS configuration
        'CORS_ORIGINS': ['http://localhost:3000', 'http://localhost:5173'],
        
        # WebSocket configuration
        'SOCKETIO_ENABLED': config.ENABLE_WEBSOCKETS,
        'SOCKETIO_ASYNC_MODE': 'threading',
        
        # API configuration
        'API_VERSION': 'v1',
        'API_PREFIX': '/api/v1',
        
        # Security configuration
        'WTF_CSRF_ENABLED': False,  # Disabled for API
        'SESSION_COOKIE_SECURE': not app.config['DEBUG'],
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        
        # JSON configuration
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': app.config['DEBUG'],
        
        # File upload configuration
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
        
        # Request timeout
        'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
    })
    
    # Apply custom configuration
    if config_dict:
        app.config.update(config_dict)
    
    debug_log.api(f"Flask app configured (DEBUG: {app.config['DEBUG']})")

def _initialize_extensions(app: Flask) -> None:
    """Initialize Flask extensions"""
    
    # Initialize CORS
    CORS(app, 
         resources={
             "/api/*": {
                 "origins": app.config['CORS_ORIGINS'],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                 "supports_credentials": True
             }
         })
    
    debug_log.api("CORS initialized")
    
    # Initialize SocketIO if enabled
    if app.config.get('SOCKETIO_ENABLED', True):
        socketio = SocketIO(
            app,
            cors_allowed_origins=app.config['CORS_ORIGINS'],
            async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading'),
            logger=app.config['DEBUG'],
            engineio_logger=app.config['DEBUG']
        )
        
        # Store socketio in app for access in routes
        app.socketio = socketio
        
        # Setup WebSocket event handlers
        _setup_websocket_handlers(socketio)
        
        debug_log.api("SocketIO initialized")
    
    # Initialize database
    try:
        # Test database connection
        db_status = db_manager.check_connection()
        if db_status['connected']:
            debug_log.database("Database connection verified")
        else:
            debug_log.database(f"Database connection failed: {db_status.get('error')}", level="ERROR")
    except Exception as e:
        debug_log.error_trace("Database initialization failed", exception=e)

def _register_blueprints(app: Flask) -> None:
    """Register Flask blueprints"""
    
    # Import blueprints
    from ark_tools.api.v1 import api_v1_bp
    from ark_tools.api.health import health_bp
    
    # Register API v1 blueprint
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    debug_log.api("API v1 blueprint registered")
    
    # Register health check blueprint
    app.register_blueprint(health_bp, url_prefix='/health')
    debug_log.api("Health check blueprint registered")

def _setup_error_handlers(app: Flask) -> None:
    """Setup global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized', 
            'message': 'Authentication required',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded',
            'status_code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        debug_log.api(f"Internal server error: {error}", level="ERROR")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    
    debug_log.api("Error handlers configured")

def _setup_request_hooks(app: Flask) -> None:
    """Setup request/response hooks"""
    
    @app.before_request
    def before_request():
        # Log incoming requests in debug mode
        if app.config['DEBUG']:
            debug_log.api(f"Incoming request: {request.method} {request.path}")
        
        # Add request timestamp
        request.start_time = datetime.utcnow()
    
    @app.after_request
    def after_request(response):
        # Add CORS headers for all responses
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        # Add security headers
        response.headers.add('X-Content-Type-Options', 'nosniff')
        response.headers.add('X-Frame-Options', 'DENY')
        response.headers.add('X-XSS-Protection', '1; mode=block')
        
        # Log response time in debug mode
        if app.config['DEBUG'] and hasattr(request, 'start_time'):
            duration = (datetime.utcnow() - request.start_time).total_seconds()
            debug_log.api(f"Request completed: {request.method} {request.path} ({response.status_code}) in {duration:.3f}s")
        
        return response
    
    debug_log.api("Request hooks configured")

def _setup_websocket_handlers(socketio: SocketIO) -> None:
    """Setup WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        debug_log.websocket("Client connected")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        debug_log.websocket("Client disconnected")
    
    @socketio.on('ping')
    def handle_ping():
        debug_log.websocket("Ping received")
        socketio.emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    @socketio.on('subscribe_analysis')
    def handle_subscribe_analysis(data):
        analysis_id = data.get('analysis_id')
        if analysis_id:
            debug_log.websocket(f"Client subscribed to analysis updates: {analysis_id}")
            # Join room for analysis updates
            from flask_socketio import join_room
            join_room(f"analysis_{analysis_id}")
    
    @socketio.on('subscribe_transformation')
    def handle_subscribe_transformation(data):
        plan_id = data.get('plan_id')
        if plan_id:
            debug_log.websocket(f"Client subscribed to transformation updates: {plan_id}")
            # Join room for transformation updates
            from flask_socketio import join_room
            join_room(f"transformation_{plan_id}")
    
    debug_log.websocket("WebSocket handlers configured")