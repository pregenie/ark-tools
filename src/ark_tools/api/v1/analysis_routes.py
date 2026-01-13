"""
Analysis API Routes
==================

REST endpoints for code analysis operations.
"""

import time
from typing import Dict, Any
from flask import request, jsonify, current_app
from pathlib import Path

from ark_tools.api.v1.blueprint import api_v1_bp
from ark_tools.core.engine import ARKEngine
from ark_tools.core.safety import SafetyManager
from ark_tools.database.base import db_manager
from ark_tools.database.models.analysis import Analysis
from ark_tools.utils.debug_logger import debug_log

@api_v1_bp.route('/analysis', methods=['POST'])
def start_analysis():
    """
    Start a new code analysis
    
    POST /api/v1/analysis
    Body: {
        "directory": "/path/to/code",
        "analysis_type": "comprehensive",  // quick, comprehensive, deep
        "parameters": {...}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        directory = data.get('directory')
        analysis_type = data.get('analysis_type', 'comprehensive')
        parameters = data.get('parameters', {})
        
        # Validate required fields
        if not directory:
            return jsonify({'error': 'directory is required'}), 400
        
        # Validate analysis type
        if analysis_type not in ['quick', 'comprehensive', 'deep']:
            return jsonify({'error': 'analysis_type must be one of: quick, comprehensive, deep'}), 400
        
        # Validate directory exists
        if not Path(directory).exists():
            return jsonify({'error': f'Directory does not exist: {directory}'}), 400
        
        debug_log.api(f"Starting analysis: {directory} ({analysis_type})")
        
        # Initialize ARK Engine
        engine = ARKEngine()
        
        # Protect source directory
        safety_manager = SafetyManager()
        safety_manager.protect_source_directory(directory)
        
        # Start analysis
        result = engine.analyze_codebase(
            directory=directory,
            analysis_type=analysis_type,
            **parameters
        )
        
        if result['success']:
            # Save analysis to database
            analysis_record = _save_analysis_to_db(
                result['analysis_id'],
                directory,
                analysis_type,
                parameters,
                result['results']
            )
            
            # Emit WebSocket event if SocketIO is available
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('analysis_started', {
                    'analysis_id': result['analysis_id'],
                    'status': 'running',
                    'directory': directory,
                    'analysis_type': analysis_type
                })
            
            response_data = {
                'success': True,
                'analysis_id': result['analysis_id'],
                'status': 'running',
                'directory': directory,
                'analysis_type': analysis_type,
                'output_file': result.get('output_file'),
                'estimated_duration_seconds': _estimate_analysis_duration(analysis_type, result['results'])
            }
            
            debug_log.api(f"Analysis started successfully: {result['analysis_id']}")
            return jsonify(response_data), 202  # Accepted
        
        else:
            debug_log.api(f"Analysis failed: {result.get('error')}", level="ERROR")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Analysis failed'),
                'analysis_id': None
            }), 500
    
    except Exception as e:
        debug_log.error_trace("Analysis start failed", exception=e)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_v1_bp.route('/analysis/<analysis_id>', methods=['GET'])
def get_analysis_status(analysis_id: str):
    """
    Get analysis status and results
    
    GET /api/v1/analysis/{analysis_id}
    """
    try:
        debug_log.api(f"Getting analysis status: {analysis_id}")
        
        # Get analysis from database
        with db_manager.get_session() as session:
            analysis = session.query(Analysis).filter(
                Analysis.analysis_id == analysis_id
            ).first()
            
            if not analysis:
                return jsonify({'error': 'Analysis not found'}), 404
            
            # Build response
            response_data = {
                'analysis_id': analysis.analysis_id,
                'status': analysis.status,
                'directory': analysis.directory_path,
                'analysis_type': analysis.analysis_type,
                'started_at': analysis.started_at.isoformat(),
                'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
                'execution_time_seconds': analysis.execution_time_seconds,
                'summary': {
                    'total_files': analysis.total_files,
                    'total_components': analysis.total_components,
                    'patterns_found': analysis.patterns_found,
                    'duplicates_found': analysis.duplicates_found
                }
            }
            
            # Include error if analysis failed
            if analysis.error_message:
                response_data['error'] = analysis.error_message
            
            # Include detailed results if completed
            if analysis.status == 'completed' and analysis.results:
                response_data['results'] = _format_analysis_results(analysis)
            
            return jsonify(response_data), 200
    
    except Exception as e:
        debug_log.error_trace(f"Failed to get analysis status: {analysis_id}", exception=e)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_v1_bp.route('/analysis/<analysis_id>/results', methods=['GET'])
def get_analysis_results(analysis_id: str):
    """
    Get detailed analysis results
    
    GET /api/v1/analysis/{analysis_id}/results
    """
    try:
        debug_log.api(f"Getting analysis results: {analysis_id}")
        
        with db_manager.get_session() as session:
            analysis = session.query(Analysis).filter(
                Analysis.analysis_id == analysis_id
            ).first()
            
            if not analysis:
                return jsonify({'error': 'Analysis not found'}), 404
            
            if analysis.status != 'completed':
                return jsonify({
                    'error': 'Analysis not completed',
                    'status': analysis.status
                }), 400
            
            # Get detailed results including patterns and duplicates
            results_data = {
                'analysis_id': analysis.analysis_id,
                'summary': {
                    'total_files': analysis.total_files,
                    'total_components': analysis.total_components,
                    'patterns_found': analysis.patterns_found,
                    'duplicates_found': analysis.duplicates_found
                },
                'files_analyzed': [
                    {
                        'file_path': result.file_path,
                        'file_type': result.file_type,
                        'components_extracted': result.components_extracted,
                        'complexity_score': result.complexity_score,
                        'functions_count': result.functions_count,
                        'classes_count': result.classes_count
                    }
                    for result in analysis.results
                ],
                'patterns_detected': [
                    {
                        'pattern_name': pattern.pattern_name,
                        'pattern_type': pattern.pattern_type,
                        'frequency': pattern.frequency,
                        'confidence_score': pattern.confidence_score,
                        'consolidation_potential': pattern.consolidation_potential
                    }
                    for pattern in analysis.patterns
                ],
                'duplicates_detected': [
                    {
                        'duplicate_id': duplicate.duplicate_id,
                        'similarity_score': duplicate.similarity_score,
                        'duplicate_type': duplicate.duplicate_type,
                        'priority': duplicate.priority,
                        'original_file': duplicate.original_file_path,
                        'duplicate_file': duplicate.duplicate_file_path
                    }
                    for duplicate in analysis.duplicates
                ]
            }
            
            return jsonify(results_data), 200
    
    except Exception as e:
        debug_log.error_trace(f"Failed to get analysis results: {analysis_id}", exception=e)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_v1_bp.route('/analysis', methods=['GET'])
def list_analyses():
    """
    List all analyses with optional filtering
    
    GET /api/v1/analysis?status=completed&limit=10&offset=0
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        analysis_type = request.args.get('analysis_type')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        debug_log.api(f"Listing analyses (status: {status}, type: {analysis_type}, limit: {limit})")
        
        with db_manager.get_session() as session:
            query = session.query(Analysis)
            
            # Apply filters
            if status:
                query = query.filter(Analysis.status == status)
            if analysis_type:
                query = query.filter(Analysis.analysis_type == analysis_type)
            
            # Order by most recent first
            query = query.order_by(Analysis.started_at.desc())
            
            # Apply pagination
            total_count = query.count()
            analyses = query.offset(offset).limit(limit).all()
            
            # Format response
            analyses_data = [
                {
                    'analysis_id': analysis.analysis_id,
                    'directory': analysis.directory_path,
                    'analysis_type': analysis.analysis_type,
                    'status': analysis.status,
                    'started_at': analysis.started_at.isoformat(),
                    'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
                    'execution_time_seconds': analysis.execution_time_seconds,
                    'total_files': analysis.total_files,
                    'patterns_found': analysis.patterns_found,
                    'duplicates_found': analysis.duplicates_found
                }
                for analysis in analyses
            ]
            
            return jsonify({
                'analyses': analyses_data,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + limit) < total_count
                }
            }), 200
    
    except Exception as e:
        debug_log.error_trace("Failed to list analyses", exception=e)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_v1_bp.route('/analysis/<analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id: str):
    """
    Delete an analysis and its results
    
    DELETE /api/v1/analysis/{analysis_id}
    """
    try:
        debug_log.api(f"Deleting analysis: {analysis_id}")
        
        with db_manager.get_session() as session:
            analysis = session.query(Analysis).filter(
                Analysis.analysis_id == analysis_id
            ).first()
            
            if not analysis:
                return jsonify({'error': 'Analysis not found'}), 404
            
            # Check if analysis is currently running
            if analysis.status == 'running':
                return jsonify({
                    'error': 'Cannot delete running analysis',
                    'status': analysis.status
                }), 400
            
            # Delete analysis (cascades to related records)
            session.delete(analysis)
            session.commit()
            
            debug_log.api(f"Analysis deleted successfully: {analysis_id}")
            
            return jsonify({
                'success': True,
                'message': 'Analysis deleted successfully'
            }), 200
    
    except Exception as e:
        debug_log.error_trace(f"Failed to delete analysis: {analysis_id}", exception=e)
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

# Helper functions

def _save_analysis_to_db(
    analysis_id: str,
    directory: str,
    analysis_type: str,
    parameters: Dict[str, Any],
    results: Dict[str, Any]
) -> Analysis:
    """Save analysis to database"""
    try:
        with db_manager.get_session() as session:
            analysis = Analysis(
                analysis_id=analysis_id,
                directory_path=directory,
                analysis_type=analysis_type,
                status='running',
                parameters=parameters,
                total_files=results.get('summary', {}).get('total_files'),
                total_components=results.get('summary', {}).get('total_components'),
                patterns_found=results.get('summary', {}).get('patterns_found'),
                duplicates_found=results.get('summary', {}).get('duplicates_found')
            )
            
            session.add(analysis)
            session.commit()
            
            debug_log.database(f"Analysis saved to database: {analysis_id}")
            return analysis
    
    except Exception as e:
        debug_log.error_trace(f"Failed to save analysis to database: {analysis_id}", exception=e)
        raise

def _estimate_analysis_duration(analysis_type: str, results: Dict[str, Any]) -> int:
    """Estimate analysis duration in seconds"""
    total_files = results.get('summary', {}).get('total_files', 0)
    
    if analysis_type == 'quick':
        return max(30, total_files * 2)  # 2 seconds per file minimum 30 seconds
    elif analysis_type == 'comprehensive':
        return max(60, total_files * 5)  # 5 seconds per file, minimum 1 minute
    else:  # deep
        return max(120, total_files * 10)  # 10 seconds per file, minimum 2 minutes

def _format_analysis_results(analysis: Analysis) -> Dict[str, Any]:
    """Format analysis results for API response"""
    return {
        'patterns': [
            {
                'pattern_id': pattern.pattern_id,
                'name': pattern.pattern_name,
                'type': pattern.pattern_type,
                'frequency': pattern.frequency,
                'confidence': pattern.confidence_score,
                'consolidation_potential': pattern.consolidation_potential,
                'components': pattern.components_involved,
                'description': pattern.description
            }
            for pattern in analysis.patterns
        ],
        'duplicates': [
            {
                'duplicate_id': duplicate.duplicate_id,
                'similarity_score': duplicate.similarity_score,
                'duplicate_type': duplicate.duplicate_type,
                'priority': duplicate.priority,
                'original_component': duplicate.original_component_id,
                'duplicate_component': duplicate.duplicate_component_id,
                'original_file': duplicate.original_file_path,
                'duplicate_file': duplicate.duplicate_file_path,
                'consolidation_strategy': duplicate.consolidation_strategy
            }
            for duplicate in analysis.duplicates
        ],
        'recommendations': [
            # Generate recommendations based on patterns and duplicates
            {
                'type': 'consolidation',
                'priority': 'high',
                'message': f"Consider consolidating {analysis.duplicates_found} duplicate pairs",
                'action': 'Create transformation plan for high-similarity duplicates'
            }
        ] if analysis.duplicates_found > 0 else []
    }