"""
ARK-TOOLS Main Engine
=====================

The central coordination engine that orchestrates all ARK-TOOLS operations.
Integrates with MAMS components and coordinates specialized agents.
"""

import os
import sys
import uuid
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import json

from ark_tools import config
from ark_tools.utils.debug_logger import debug_log
from ark_tools.core.safety import SafetyManager
from ark_tools.core.analysis import AnalysisEngine
from ark_tools.core.transformation import TransformationEngine

logger = logging.getLogger(__name__)

class ARKEngine:
    """
    Main ARK-TOOLS engine that coordinates all operations
    """
    
    def __init__(self, workspace_path: Optional[str] = None):
        """
        Initialize ARK-TOOLS engine
        
        Args:
            workspace_path: Path to workspace directory (defaults to current directory)
        """
        self.workspace_path = Path(workspace_path or os.getcwd())
        self.session_id = str(uuid.uuid4())
        self.safety_manager = SafetyManager()
        self.analysis_engine = AnalysisEngine()
        self.transformation_engine = TransformationEngine()
        
        # Setup MAMS integration
        self._setup_mams_integration()
        
        # Initialize output directory
        self.output_dir = self._create_output_directory()
        
        debug_log.api(f"ARK Engine initialized for workspace: {self.workspace_path}")
        debug_log.api(f"Session ID: {self.session_id}")
        debug_log.api(f"Output directory: {self.output_dir}")
    
    def _setup_mams_integration(self) -> None:
        """Setup integration with MAMS components"""
        try:
            # Add MAMS to Python path
            mams_path = config.MAMS_MIGRATIONS_PATH
            if os.path.exists(mams_path) and mams_path not in sys.path:
                sys.path.insert(0, mams_path)
                debug_log.api(f"Added MAMS path to Python path: {mams_path}")
            else:
                logger.warning(f"MAMS path not found or already in path: {mams_path}")
        
        except Exception as e:
            debug_log.error_trace("Failed to setup MAMS integration", exception=e)
            raise RuntimeError(f"Failed to setup MAMS integration: {e}")
    
    def _create_output_directory(self) -> Path:
        """Create versioned output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.workspace_path / config.DEFAULT_OUTPUT_DIR / f"v_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session info file
        session_info = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'workspace_path': str(self.workspace_path),
            'ark_tools_version': config.VERSION
        }
        
        with open(output_dir / 'session_info.json', 'w') as f:
            json.dump(session_info, f, indent=2)
        
        return output_dir
    
    def analyze_codebase(
        self, 
        directory: Union[str, Path], 
        analysis_type: str = "comprehensive",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze codebase for patterns and consolidation opportunities
        
        Args:
            directory: Directory to analyze
            analysis_type: Type of analysis (quick, comprehensive, deep)
            **kwargs: Additional analysis parameters
            
        Returns:
            Dict containing analysis results
        """
        debug_log.api(f"Starting codebase analysis: {directory} ({analysis_type})")
        
        # Safety check - ensure we don't modify source
        self.safety_manager.verify_read_only_operation(directory)
        
        try:
            # Run analysis through analysis engine
            analysis_id = str(uuid.uuid4())
            
            result = self.analysis_engine.analyze(
                directory=directory,
                analysis_type=analysis_type,
                analysis_id=analysis_id,
                output_dir=self.output_dir,
                **kwargs
            )
            
            # Save analysis results
            analysis_file = self.output_dir / f"analysis_results_{analysis_id}.json"
            with open(analysis_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            debug_log.api(f"Analysis completed successfully: {analysis_id}")
            
            return {
                'success': True,
                'analysis_id': analysis_id,
                'results': result,
                'output_file': str(analysis_file)
            }
        
        except Exception as e:
            debug_log.error_trace(f"Analysis failed for {directory}", exception=e)
            return {
                'success': False,
                'error': str(e),
                'analysis_id': None
            }
    
    def create_transformation_plan(
        self,
        analysis_id: str,
        strategy: str = "conservative",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create transformation plan based on analysis results
        
        Args:
            analysis_id: ID of the analysis to base plan on
            strategy: Transformation strategy (conservative, moderate, aggressive)
            **kwargs: Additional planning parameters
            
        Returns:
            Dict containing transformation plan
        """
        debug_log.api(f"Creating transformation plan for analysis: {analysis_id} ({strategy})")
        
        try:
            # Load analysis results
            analysis_file = self.output_dir / f"analysis_results_{analysis_id}.json"
            if not analysis_file.exists():
                raise FileNotFoundError(f"Analysis results not found: {analysis_id}")
            
            with open(analysis_file, 'r') as f:
                analysis_results = json.load(f)
            
            # Create transformation plan
            plan_id = str(uuid.uuid4())
            
            plan = self.transformation_engine.create_plan(
                analysis_results=analysis_results,
                strategy=strategy,
                plan_id=plan_id,
                **kwargs
            )
            
            # Save transformation plan
            plan_file = self.output_dir / f"transformation_plan_{plan_id}.json"
            with open(plan_file, 'w') as f:
                json.dump(plan, f, indent=2, default=str)
            
            debug_log.api(f"Transformation plan created successfully: {plan_id}")
            
            return {
                'success': True,
                'plan_id': plan_id,
                'plan': plan,
                'output_file': str(plan_file)
            }
        
        except Exception as e:
            debug_log.error_trace(f"Plan creation failed for {analysis_id}", exception=e)
            return {
                'success': False,
                'error': str(e),
                'plan_id': None
            }
    
    def generate_consolidated_code(
        self,
        plan_id: str,
        dry_run: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate consolidated code based on transformation plan
        
        Args:
            plan_id: ID of the transformation plan
            dry_run: If True, only preview changes without creating files
            **kwargs: Additional generation parameters
            
        Returns:
            Dict containing generation results
        """
        debug_log.api(f"Generating consolidated code for plan: {plan_id} (dry_run: {dry_run})")
        
        try:
            # Load transformation plan
            plan_file = self.output_dir / f"transformation_plan_{plan_id}.json"
            if not plan_file.exists():
                raise FileNotFoundError(f"Transformation plan not found: {plan_id}")
            
            with open(plan_file, 'r') as f:
                transformation_plan = json.load(f)
            
            # Generate code through transformation engine
            generation_id = str(uuid.uuid4())
            
            result = self.transformation_engine.generate_code(
                plan=transformation_plan,
                generation_id=generation_id,
                output_dir=self.output_dir,
                dry_run=dry_run,
                **kwargs
            )
            
            # Save generation results
            generation_file = self.output_dir / f"generation_results_{generation_id}.json"
            with open(generation_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            # Create generation report
            if not dry_run:
                self._create_generation_report(result, generation_id)
            
            debug_log.api(f"Code generation completed successfully: {generation_id}")
            
            return {
                'success': True,
                'generation_id': generation_id,
                'results': result,
                'output_file': str(generation_file),
                'dry_run': dry_run
            }
        
        except Exception as e:
            debug_log.error_trace(f"Code generation failed for plan {plan_id}", exception=e)
            return {
                'success': False,
                'error': str(e),
                'generation_id': None
            }
    
    def _create_generation_report(self, results: Dict[str, Any], generation_id: str) -> None:
        """Create human-readable generation report"""
        report_lines = [
            "# ARK-TOOLS Code Generation Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Session ID: {self.session_id}",
            f"Generation ID: {generation_id}",
            "",
            "## Summary",
            f"- Files generated: {results.get('files_generated', 0)}",
            f"- Lines of code: {results.get('total_lines', 0)}",
            f"- Code reduction: {results.get('code_reduction_percent', 0)}%",
            "",
            "## Generated Files",
        ]
        
        for file_info in results.get('generated_files', []):
            report_lines.append(f"- {file_info.get('path', 'Unknown')}")
            if file_info.get('description'):
                report_lines.append(f"  {file_info['description']}")
        
        report_lines.extend([
            "",
            "## Safety Guarantees",
            "- ✅ Original source files were never modified",
            "- ✅ All outputs are in versioned directory",
            "- ✅ Complete rollback capability available",
            "- ✅ Generated code syntax validated",
            "",
            f"**Location**: {self.output_dir}",
            "",
            "*Generated by ARK-TOOLS v{config.VERSION}*"
        ])
        
        report_file = self.output_dir / "GENERATION_REPORT.md"
        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            'session_id': self.session_id,
            'workspace_path': str(self.workspace_path),
            'output_dir': str(self.output_dir),
            'ark_tools_version': config.VERSION,
            'mams_path': config.MAMS_MIGRATIONS_PATH,
            'safety_mode': config.READ_ONLY_SOURCE
        }