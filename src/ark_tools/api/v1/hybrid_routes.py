"""
Hybrid Analysis API Routes
===========================

API endpoints for MAMS/LLM hybrid code analysis.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
from pathlib import Path
import os

from ark_tools.agents.architect import ArchitectAgent
from ark_tools.utils.debug_logger import debug_log
from ark_tools import config

# Create blueprint
hybrid_bp = Blueprint('hybrid', __name__)

# Initialize architect agent with LLM config
architect_config = {
    'llm_model_path': config.LLM_MODEL_PATH,
    'context_size': config.LLM_CONTEXT_SIZE,
    'max_tokens': config.LLM_MAX_TOKENS,
    'threads': config.LLM_THREADS,
    'temperature': config.LLM_TEMPERATURE
}

architect_agent = ArchitectAgent(config=architect_config)


@hybrid_bp.route('/analyze', methods=['POST'])
def hybrid_analyze():
    """
    Perform hybrid MAMS/LLM analysis on a codebase.
    
    Request JSON:
        {
            "directory": "/path/to/code",
            "strategy": "hybrid" | "fast" | "deep" | "compress_only",
            "max_files": 50,
            "include_suggestions": true
        }
    
    Returns:
        JSON with analysis results including domains, structure, and timing
    """
    try:
        data = request.get_json()
        
        # Validate input
        directory = data.get('directory')
        if not directory:
            return jsonify({'error': 'Directory path is required'}), 400
        
        directory_path = Path(directory)
        if not directory_path.exists():
            return jsonify({'error': f'Directory does not exist: {directory}'}), 400
        
        if not directory_path.is_dir():
            return jsonify({'error': f'Not a directory: {directory}'}), 400
        
        # Get analysis parameters
        strategy = data.get('strategy', 'hybrid')
        max_files = data.get('max_files', 50)
        include_suggestions = data.get('include_suggestions', False)
        
        debug_log.api(f"Starting hybrid analysis: {directory} (strategy: {strategy})")
        
        # Perform hybrid analysis
        result = architect_agent.execute_operation(
            'perform_hybrid_analysis',
            {
                'directory': directory,
                'strategy': strategy,
                'max_files': max_files
            }
        )
        
        # Check if operation was successful
        if not result.success:
            return jsonify({
                'error': result.error or 'Analysis failed',
                'operation_id': result.operation_id
            }), 500
        
        analysis_data = result.data
        
        # Add code organization suggestions if requested
        if include_suggestions and analysis_data.get('domains'):
            suggestions_result = architect_agent.execute_operation(
                'suggest_code_organization',
                {
                    'domains': analysis_data['domains'],
                    'structure': analysis_data.get('structure', {})
                }
            )
            
            if suggestions_result.success:
                analysis_data['suggestions'] = suggestions_result.data
        
        return jsonify({
            'success': True,
            'operation_id': result.operation_id,
            'analysis': analysis_data
        })
        
    except Exception as e:
        debug_log.error_trace("Hybrid analysis failed", exception=e)
        return jsonify({'error': str(e)}), 500


@hybrid_bp.route('/analyze/domains', methods=['POST'])
def analyze_domains():
    """
    Analyze semantic domains in code using LLM.
    
    Request JSON:
        {
            "directory": "/path/to/code" | "code_skeleton": "compressed code",
            "context": "optional context",
            "include_intent": true
        }
    
    Returns:
        JSON with domain analysis and optional intent analysis
    """
    try:
        data = request.get_json()
        
        # Either directory or code_skeleton required
        directory = data.get('directory')
        code_skeleton = data.get('code_skeleton')
        
        if not directory and not code_skeleton:
            return jsonify({'error': 'Either directory or code_skeleton is required'}), 400
        
        parameters = {
            'context': data.get('context', ''),
            'include_intent': data.get('include_intent', False)
        }
        
        if directory:
            parameters['directory'] = directory
        if code_skeleton:
            parameters['code_skeleton'] = code_skeleton
        
        debug_log.api("Starting domain analysis")
        
        # Perform domain analysis
        result = architect_agent.execute_operation(
            'analyze_semantic_domains',
            parameters
        )
        
        if not result.success:
            return jsonify({
                'error': result.error or 'Domain analysis failed',
                'operation_id': result.operation_id
            }), 500
        
        return jsonify({
            'success': True,
            'operation_id': result.operation_id,
            'domains': result.data
        })
        
    except Exception as e:
        debug_log.error_trace("Domain analysis failed", exception=e)
        return jsonify({'error': str(e)}), 500


@hybrid_bp.route('/compress', methods=['POST'])
def compress_code():
    """
    Compress code to AST skeleton for LLM analysis.
    
    Request JSON:
        {
            "directory": "/path/to/code",
            "max_files": 50,
            "exclude_patterns": ["test_", "__pycache__"]
        }
    
    Returns:
        JSON with compressed code skeletons and statistics
    """
    try:
        from ark_tools.mams_core.compressor import CodeCompressor
        
        data = request.get_json()
        
        directory = data.get('directory')
        if not directory:
            return jsonify({'error': 'Directory path is required'}), 400
        
        directory_path = Path(directory)
        if not directory_path.exists() or not directory_path.is_dir():
            return jsonify({'error': f'Invalid directory: {directory}'}), 400
        
        max_files = data.get('max_files', 50)
        exclude_patterns = data.get('exclude_patterns', None)
        
        debug_log.api(f"Compressing code from: {directory}")
        
        # Perform compression
        compressor = CodeCompressor()
        compressed = compressor.compress_directory(
            directory_path,
            max_files=max_files,
            exclude_patterns=exclude_patterns
        )
        
        # Calculate statistics
        total_chars = sum(len(v) for v in compressed.values())
        estimated_tokens = total_chars // 4  # Rough estimate
        
        return jsonify({
            'success': True,
            'compressed_files': compressed,
            'statistics': {
                'files_compressed': len(compressed),
                'total_characters': total_chars,
                'estimated_tokens': estimated_tokens,
                'compression_ratio': 0.2  # Approximate
            }
        })
        
    except Exception as e:
        debug_log.error_trace("Code compression failed", exception=e)
        return jsonify({'error': str(e)}), 500


@hybrid_bp.route('/model/info', methods=['GET'])
def get_model_info():
    """
    Get information about the loaded LLM model.
    
    Returns:
        JSON with model configuration and status
    """
    try:
        from ark_tools.llm_engine.engine import LLMAnalysisEngine
        
        # Create engine instance to get info
        engine = LLMAnalysisEngine(config=architect_config)
        model_info = engine.get_model_info()
        
        # Add configuration info
        model_info['config'] = {
            'context_size': config.LLM_CONTEXT_SIZE,
            'max_tokens': config.LLM_MAX_TOKENS,
            'threads': config.LLM_THREADS,
            'temperature': config.LLM_TEMPERATURE,
            'gpu_enabled': config.LLM_ENABLE_GPU
        }
        
        return jsonify({
            'success': True,
            'model': model_info
        })
        
    except Exception as e:
        debug_log.error_trace("Failed to get model info", exception=e)
        return jsonify({'error': str(e)}), 500


@hybrid_bp.route('/model/download', methods=['POST'])
def download_model():
    """
    Download a specific LLM model.
    
    Request JSON:
        {
            "model_name": "codellama-7b-instruct",
            "model_url": "https://huggingface.co/..."
        }
    
    Returns:
        JSON with download status
    """
    # This would implement model downloading logic
    # For now, return instructions
    return jsonify({
        'success': False,
        'message': 'Model download not yet implemented',
        'instructions': [
            'To download models manually:',
            '1. Visit https://huggingface.co/models?library=gguf',
            '2. Download the desired GGUF model',
            '3. Save to ~/.ark_tools/models/',
            '4. Update ARK_LLM_MODEL_PATH in .env'
        ]
    })


@hybrid_bp.route('/reports/generate', methods=['POST'])
def generate_report():
    """
    Generate a report from analysis results.
    
    Request JSON:
        {
            "analysis_data": {...},  # Analysis results
            "format": ["json", "markdown", "html"],
            "output_dir": "/path/to/reports"
        }
    
    Returns:
        JSON with paths to generated reports
    """
    try:
        from ark_tools.reporting import ReportGenerator, HybridAnalysisCollector
        from ark_tools.reporting.base import ReportConfig
        
        data = request.get_json()
        analysis_data = data.get('analysis_data')
        
        if not analysis_data:
            return jsonify({'error': 'Analysis data is required'}), 400
        
        # Configure report generation
        output_dir = data.get('output_dir', '.ark_reports')
        formats = data.get('format', ['json', 'markdown', 'html'])
        
        report_config = ReportConfig(
            output_dir=Path(output_dir),
            generate_markdown='markdown' in formats,
            generate_html='html' in formats
        )
        
        # Collect and generate reports
        collector = HybridAnalysisCollector(analysis_data)
        report_data = collector.collect()
        
        generator = ReportGenerator(config=report_config)
        report_paths = generator.generate_reports(report_data)
        
        return jsonify({
            'success': True,
            'reports': {str(k): str(v) for k, v in report_paths.items()},
            'report_dir': str(report_config.output_dir / 'latest')
        })
        
    except Exception as e:
        debug_log.error_trace("Report generation failed", exception=e)
        return jsonify({'error': str(e)}), 500


@hybrid_bp.route('/reports/latest', methods=['GET'])
def get_latest_report():
    """
    Get the latest report summary.
    
    Returns:
        JSON with latest report summary
    """
    try:
        report_dir = Path('.ark_reports/latest')
        
        if not report_dir.exists():
            return jsonify({'error': 'No reports found'}), 404
        
        # Load summary if it exists
        summary_file = report_dir / 'summary.json'
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
        else:
            # Load master and create summary
            master_file = report_dir / 'master.json'
            if not master_file.exists():
                return jsonify({'error': 'No report data found'}), 404
            
            with open(master_file) as f:
                master_data = json.load(f)
                summary = master_data.get('summary', {})
        
        return jsonify({
            'success': True,
            'summary': summary,
            'report_dir': str(report_dir.resolve())
        })
        
    except Exception as e:
        debug_log.error_trace("Failed to get latest report", exception=e)
        return jsonify({'error': str(e)}), 500


@hybrid_bp.route('/reports/history', methods=['GET'])
def get_report_history():
    """
    Get history of all analysis reports.
    
    Returns:
        JSON with report history
    """
    try:
        history_file = Path('.ark_reports/history.json')
        
        if not history_file.exists():
            return jsonify({
                'success': True,
                'history': {'runs': []},
                'message': 'No report history found'
            })
        
        with open(history_file) as f:
            history = json.load(f)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        debug_log.error_trace("Failed to get report history", exception=e)
        return jsonify({'error': str(e)}), 500


@hybrid_bp.route('/reports/<report_id>', methods=['GET'])
def get_report(report_id: str):
    """
    Get a specific report by ID or timestamp.
    
    Args:
        report_id: Report run ID or timestamp
        
    Returns:
        JSON with report data
    """
    try:
        import json
        
        # Check if it's a run ID or timestamp
        report_base = Path('.ark_reports')
        
        # Try to find by timestamp first
        report_dir = report_base / report_id
        
        if not report_dir.exists():
            # Try to find by run ID in history
            history_file = report_base / 'history.json'
            if history_file.exists():
                with open(history_file) as f:
                    history = json.load(f)
                    for run in history.get('runs', []):
                        if run.get('run_id') == report_id:
                            report_dir = report_base / run.get('directory')
                            break
        
        if not report_dir.exists():
            return jsonify({'error': 'Report not found'}), 404
        
        # Load master report
        master_file = report_dir / 'master.json'
        if master_file.exists():
            with open(master_file) as f:
                master_data = json.load(f)
        else:
            master_data = {}
        
        # Get available report files
        available_reports = {}
        for report_file in report_dir.glob('*.json'):
            available_reports[report_file.stem] = str(report_file)
        
        if (report_dir / 'presentation').exists():
            for pres_file in (report_dir / 'presentation').glob('*'):
                available_reports[pres_file.name] = str(pres_file)
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'data': master_data,
            'available_files': available_reports
        })
        
    except Exception as e:
        debug_log.error_trace(f"Failed to get report {report_id}", exception=e)
        return jsonify({'error': str(e)}), 500


# Register error handlers
@hybrid_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@hybrid_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500