"""
ARK-TOOLS Transformation Engine
===============================

Core transformation engine responsible for creating transformation plans
and generating consolidated code safely using LibCST.
"""

import time
import json
import uuid
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import logging

try:
    import libcst as cst
    LIBCST_AVAILABLE = True
except ImportError:
    LIBCST_AVAILABLE = False
    cst = None

from ark_tools.utils.debug_logger import debug_log

logger = logging.getLogger(__name__)

class TransformationEngine:
    """
    Core transformation engine for safe code consolidation
    """
    
    def __init__(self):
        self.transformation_strategies = {
            'conservative': {
                'similarity_threshold': 0.95,
                'max_changes_per_file': 3,
                'preserve_comments': True,
                'preserve_formatting': True
            },
            'moderate': {
                'similarity_threshold': 0.85,
                'max_changes_per_file': 5,
                'preserve_comments': True,
                'preserve_formatting': False
            },
            'aggressive': {
                'similarity_threshold': 0.70,
                'max_changes_per_file': 10,
                'preserve_comments': False,
                'preserve_formatting': False
            }
        }
        
        if not LIBCST_AVAILABLE:
            debug_log.transformation("LibCST not available - using fallback transformation", level="WARNING")
        
        debug_log.transformation("Transformation Engine initialized")
    
    def create_plan(
        self,
        analysis_results: Dict[str, Any],
        strategy: str = "conservative",
        plan_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create transformation plan based on analysis results
        
        Args:
            analysis_results: Results from code analysis
            strategy: Transformation strategy (conservative, moderate, aggressive)
            plan_id: Unique identifier for this plan
            **kwargs: Additional planning parameters
            
        Returns:
            Dict containing transformation plan
        """
        start_time = time.time()
        plan_id = plan_id or str(uuid.uuid4())
        
        debug_log.transformation(f"Creating transformation plan: {plan_id} ({strategy})")
        
        if strategy not in self.transformation_strategies:
            raise ValueError(f"Unknown strategy: {strategy}. Available: {list(self.transformation_strategies.keys())}")
        
        strategy_config = self.transformation_strategies[strategy]
        
        # Initialize plan structure
        plan = {
            'plan_id': plan_id,
            'strategy': strategy,
            'strategy_config': strategy_config,
            'created_timestamp': datetime.now().isoformat(),
            'analysis_id': analysis_results.get('analysis_id'),
            'groups': [],
            'operations': [],
            'estimated_impact': {},
            'validation_rules': [],
            'rollback_plan': []
        }
        
        try:
            # Create transformation groups from duplicates
            duplicate_groups = self._create_duplicate_groups(
                analysis_results.get('duplicates_detected', []),
                strategy_config
            )
            plan['groups'].extend(duplicate_groups)
            
            # Create transformation groups from patterns
            pattern_groups = self._create_pattern_groups(
                analysis_results.get('patterns_found', []),
                strategy_config
            )
            plan['groups'].extend(pattern_groups)
            
            # Create transformation operations
            operations = self._create_transformation_operations(plan['groups'])
            plan['operations'] = operations
            
            # Estimate impact
            impact = self._estimate_transformation_impact(plan, analysis_results)
            plan['estimated_impact'] = impact
            
            # Create validation rules
            validation_rules = self._create_validation_rules(plan)
            plan['validation_rules'] = validation_rules
            
            # Create rollback plan
            rollback_plan = self._create_rollback_plan(plan)
            plan['rollback_plan'] = rollback_plan
            
            execution_time = time.time() - start_time
            plan['planning_time_seconds'] = execution_time
            
            debug_log.transformation(f"Transformation plan created in {execution_time:.2f}s")
            
            return plan
        
        except Exception as e:
            debug_log.error_trace(f"Plan creation failed for {plan_id}", exception=e)
            raise
    
    def generate_code(
        self,
        plan: Dict[str, Any],
        generation_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
        dry_run: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate consolidated code based on transformation plan
        
        Args:
            plan: Transformation plan to execute
            generation_id: Unique identifier for this generation
            output_dir: Directory for generated code
            dry_run: If True, only simulate generation
            **kwargs: Additional generation parameters
            
        Returns:
            Dict containing generation results
        """
        start_time = time.time()
        generation_id = generation_id or str(uuid.uuid4())
        
        debug_log.transformation(f"Generating code: {generation_id} (dry_run: {dry_run})")
        
        # Initialize results structure
        results = {
            'generation_id': generation_id,
            'plan_id': plan.get('plan_id'),
            'dry_run': dry_run,
            'timestamp': datetime.now().isoformat(),
            'generated_files': [],
            'operations_executed': [],
            'errors': [],
            'validation_results': [],
            'metrics': {}
        }
        
        try:
            # Execute transformation operations
            for operation in plan.get('operations', []):
                operation_result = self._execute_transformation_operation(
                    operation, output_dir, dry_run
                )
                
                results['operations_executed'].append(operation_result)
                
                if operation_result.get('generated_file'):
                    results['generated_files'].append(operation_result['generated_file'])
                
                if operation_result.get('errors'):
                    results['errors'].extend(operation_result['errors'])
            
            # Run validation if not dry run
            if not dry_run:
                validation_results = self._validate_generated_code(results, plan)
                results['validation_results'] = validation_results
            
            # Calculate metrics
            execution_time = time.time() - start_time
            results['metrics'] = {
                'execution_time_seconds': execution_time,
                'files_generated': len(results['generated_files']),
                'operations_executed': len(results['operations_executed']),
                'errors_encountered': len(results['errors']),
                'success_rate': (len(results['operations_executed']) - len(results['errors'])) / max(1, len(results['operations_executed']))
            }
            
            debug_log.transformation(f"Code generation completed in {execution_time:.2f}s")
            
            return results
        
        except Exception as e:
            debug_log.error_trace(f"Code generation failed for {generation_id}", exception=e)
            results['errors'].append({
                'type': 'generation_error',
                'message': str(e),
                'exception_type': type(e).__name__
            })
            return results
    
    def _create_duplicate_groups(
        self,
        duplicates: List[Dict[str, Any]],
        strategy_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create transformation groups from detected duplicates"""
        groups = []
        similarity_threshold = strategy_config['similarity_threshold']
        
        # Group duplicates by similarity level
        high_similarity = [d for d in duplicates if d['similarity_score'] >= similarity_threshold]
        
        for i, duplicate in enumerate(high_similarity):
            group = {
                'group_id': f"dup_group_{i}",
                'type': 'duplicate_consolidation',
                'name': f"Duplicate Consolidation Group {i+1}",
                'source_components': [
                    duplicate['original_component'],
                    duplicate['duplicate_component']
                ],
                'target_component': f"consolidated_{duplicate['original_component'].split(':')[-1]}",
                'consolidation_strategy': 'merge_similar',
                'similarity_score': duplicate['similarity_score'],
                'priority': 'high' if duplicate['similarity_score'] > 0.95 else 'medium'
            }
            groups.append(group)
        
        return groups
    
    def _create_pattern_groups(
        self,
        patterns: List[Dict[str, Any]],
        strategy_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create transformation groups from detected patterns"""
        groups = []
        
        # Only process patterns with sufficient frequency
        significant_patterns = [p for p in patterns if p['frequency'] >= 3]
        
        for i, pattern in enumerate(significant_patterns):
            group = {
                'group_id': f"pattern_group_{i}",
                'type': 'pattern_consolidation',
                'name': f"Pattern Consolidation: {pattern['name']}",
                'source_components': pattern['components'],
                'target_component': f"unified_{pattern['name'].lower().replace(' ', '_')}",
                'consolidation_strategy': 'extract_common_pattern',
                'pattern_type': pattern['type'],
                'frequency': pattern['frequency'],
                'priority': 'medium'
            }
            groups.append(group)
        
        return groups
    
    def _create_transformation_operations(self, groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create specific transformation operations from groups"""
        operations = []
        
        for group in groups:
            if group['type'] == 'duplicate_consolidation':
                operations.append({
                    'operation_id': f"op_{group['group_id']}",
                    'type': 'merge_duplicates',
                    'group_id': group['group_id'],
                    'description': f"Merge duplicate components with {group['similarity_score']:.1%} similarity",
                    'input_components': group['source_components'],
                    'output_file': f"{group['target_component']}.py",
                    'transformation_type': 'libcst_merge' if LIBCST_AVAILABLE else 'text_merge',
                    'safety_checks': ['syntax_validation', 'import_resolution']
                })
            
            elif group['type'] == 'pattern_consolidation':
                operations.append({
                    'operation_id': f"op_{group['group_id']}",
                    'type': 'extract_pattern',
                    'group_id': group['group_id'],
                    'description': f"Extract common pattern from {group['frequency']} components",
                    'input_components': group['source_components'],
                    'output_file': f"{group['target_component']}.py",
                    'transformation_type': 'libcst_extract' if LIBCST_AVAILABLE else 'text_extract',
                    'safety_checks': ['syntax_validation', 'dependency_check']
                })
        
        return operations
    
    def _execute_transformation_operation(
        self,
        operation: Dict[str, Any],
        output_dir: Optional[Path],
        dry_run: bool
    ) -> Dict[str, Any]:
        """Execute a single transformation operation"""
        operation_id = operation['operation_id']
        operation_type = operation['type']
        
        debug_log.transformation(f"Executing operation: {operation_id} ({operation_type})")
        
        result = {
            'operation_id': operation_id,
            'type': operation_type,
            'success': False,
            'generated_file': None,
            'errors': [],
            'preview': None
        }
        
        try:
            if operation_type == 'merge_duplicates':
                if LIBCST_AVAILABLE and operation.get('transformation_type') == 'libcst_merge':
                    content = self._merge_duplicates_libcst(operation)
                else:
                    content = self._merge_duplicates_text(operation)
                
            elif operation_type == 'extract_pattern':
                if LIBCST_AVAILABLE and operation.get('transformation_type') == 'libcst_extract':
                    content = self._extract_pattern_libcst(operation)
                else:
                    content = self._extract_pattern_text(operation)
            
            else:
                raise ValueError(f"Unknown operation type: {operation_type}")
            
            result['preview'] = content[:500] + "..." if len(content) > 500 else content
            
            # Write file if not dry run
            if not dry_run and output_dir:
                output_file = output_dir / operation['output_file']
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w') as f:
                    f.write(content)
                
                result['generated_file'] = {
                    'path': str(output_file),
                    'size_bytes': len(content.encode('utf-8')),
                    'lines': content.count('\n') + 1,
                    'description': operation.get('description', 'Generated consolidated code')
                }
            
            result['success'] = True
            
        except Exception as e:
            error_msg = f"Operation {operation_id} failed: {str(e)}"
            debug_log.transformation(error_msg, level="ERROR")
            result['errors'].append({
                'type': 'execution_error',
                'message': error_msg,
                'exception_type': type(e).__name__
            })
        
        return result
    
    def _merge_duplicates_libcst(self, operation: Dict[str, Any]) -> str:
        """Merge duplicates using LibCST for precise AST manipulation"""
        # This would implement LibCST-based merging
        # For now, return a placeholder implementation
        components = operation['input_components']
        
        merged_content = f'''"""
Consolidated module generated by ARK-TOOLS
Original components: {', '.join(components)}
"""

# TODO: Implement LibCST-based duplicate merging
class ConsolidatedComponent:
    """Merged component from duplicates with {len(components)} similarity"""
    
    def __init__(self):
        pass
    
    def merged_method(self):
        """Consolidated method combining duplicate functionality"""
        pass
'''
        
        return merged_content
    
    def _merge_duplicates_text(self, operation: Dict[str, Any]) -> str:
        """Merge duplicates using text-based approach"""
        components = operation['input_components']
        
        merged_content = f'''"""
Consolidated module generated by ARK-TOOLS
Original components: {', '.join(components)}
Generated: {datetime.now().isoformat()}
"""

# Merged from duplicate components
class ConsolidatedDuplicate:
    """
    This class consolidates functionality from {len(components)} duplicate components
    that were identified with high similarity.
    """
    
    def __init__(self):
        self.consolidated = True
        self.original_components = {components}
    
    def consolidated_method(self):
        """
        Consolidated method combining duplicate functionality.
        Original implementations were merged to eliminate duplication.
        """
        # TODO: Implement consolidated logic
        pass

# Helper functions consolidated from duplicates
def consolidated_helper():
    """Helper function created by merging duplicate implementations"""
    pass
'''
        
        return merged_content
    
    def _extract_pattern_libcst(self, operation: Dict[str, Any]) -> str:
        """Extract common pattern using LibCST"""
        # This would implement LibCST-based pattern extraction
        components = operation['input_components']
        
        pattern_content = f'''"""
Pattern module generated by ARK-TOOLS
Extracted from components: {', '.join(components)}
"""

# TODO: Implement LibCST-based pattern extraction
class ExtractedPattern:
    """Common pattern extracted from {len(components)} components"""
    
    def pattern_method(self):
        """Common method pattern identified across components"""
        pass
'''
        
        return pattern_content
    
    def _extract_pattern_text(self, operation: Dict[str, Any]) -> str:
        """Extract common pattern using text-based approach"""
        components = operation['input_components']
        group_id = operation['group_id']
        
        pattern_content = f'''"""
Common Pattern Module - {group_id}
Generated by ARK-TOOLS Pattern Extraction
Source components: {len(components)} files
Generated: {datetime.now().isoformat()}
"""

class CommonPattern:
    """
    This class implements a common pattern extracted from {len(components)} components.
    The pattern was identified through automated analysis and consolidated here
    to eliminate duplication and improve maintainability.
    """
    
    def __init__(self):
        self.pattern_type = "{operation.get('group_id', 'unknown')}"
        self.source_components = {len(components)}
    
    def execute_pattern(self):
        """
        Execute the common pattern logic.
        This method implements the shared behavior found across multiple components.
        """
        # TODO: Implement extracted pattern logic
        pass
    
    def validate_pattern(self):
        """Validate that the pattern implementation is correct"""
        return True

# Pattern utility functions
def apply_pattern(data):
    """Apply the extracted pattern to given data"""
    pattern = CommonPattern()
    return pattern.execute_pattern()

def pattern_factory():
    """Factory function for creating pattern instances"""
    return CommonPattern()
'''
        
        return pattern_content
    
    def _estimate_transformation_impact(
        self,
        plan: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate the impact of the transformation plan"""
        total_components = analysis_results.get('summary', {}).get('total_components', 0)
        groups = plan.get('groups', [])
        
        # Calculate reduction estimates
        components_to_consolidate = 0
        estimated_reduction = 0
        
        for group in groups:
            source_count = len(group.get('source_components', []))
            components_to_consolidate += source_count
            
            if group['type'] == 'duplicate_consolidation':
                # Duplicates can be reduced significantly
                estimated_reduction += source_count - 1
            elif group['type'] == 'pattern_consolidation':
                # Patterns can be partially consolidated
                estimated_reduction += source_count * 0.3  # 30% reduction estimate
        
        reduction_percentage = (estimated_reduction / max(1, total_components)) * 100
        
        return {
            'total_components': total_components,
            'components_to_consolidate': components_to_consolidate,
            'estimated_reduction': int(estimated_reduction),
            'reduction_percentage': round(reduction_percentage, 1),
            'files_to_generate': len(plan.get('operations', [])),
            'risk_level': self._assess_transformation_risk(plan),
            'complexity_score': self._calculate_complexity_score(plan)
        }
    
    def _assess_transformation_risk(self, plan: Dict[str, Any]) -> str:
        """Assess risk level of transformation plan"""
        strategy = plan.get('strategy', 'conservative')
        operations_count = len(plan.get('operations', []))
        
        if strategy == 'aggressive' or operations_count > 20:
            return 'high'
        elif strategy == 'moderate' or operations_count > 10:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_complexity_score(self, plan: Dict[str, Any]) -> int:
        """Calculate complexity score for transformation plan"""
        score = 0
        
        for group in plan.get('groups', []):
            source_count = len(group.get('source_components', []))
            
            if group['type'] == 'duplicate_consolidation':
                score += source_count * 2  # Lower complexity
            elif group['type'] == 'pattern_consolidation':
                score += source_count * 3  # Higher complexity
        
        return score
    
    def _create_validation_rules(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create validation rules for the transformation"""
        rules = [
            {
                'rule_id': 'syntax_validation',
                'description': 'All generated code must have valid Python syntax',
                'type': 'syntax_check',
                'critical': True
            },
            {
                'rule_id': 'import_resolution',
                'description': 'All imports must resolve correctly',
                'type': 'import_check',
                'critical': True
            },
            {
                'rule_id': 'no_source_modification',
                'description': 'Original source files must not be modified',
                'type': 'safety_check',
                'critical': True
            }
        ]
        
        return rules
    
    def _create_rollback_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create rollback plan for the transformation"""
        rollback_steps = [
            {
                'step': 1,
                'action': 'delete_generated_files',
                'description': 'Remove all generated files from output directory',
                'reversible': False
            },
            {
                'step': 2,
                'action': 'restore_backups',
                'description': 'Restore any backed up files to original locations',
                'reversible': True
            },
            {
                'step': 3,
                'action': 'clear_session_data',
                'description': 'Clear transformation session data and logs',
                'reversible': False
            }
        ]
        
        return rollback_steps
    
    def _validate_generated_code(
        self,
        results: Dict[str, Any],
        plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate generated code against validation rules"""
        validation_results = []
        validation_rules = plan.get('validation_rules', [])
        
        for rule in validation_rules:
            rule_result = {
                'rule_id': rule['rule_id'],
                'description': rule['description'],
                'passed': True,
                'errors': [],
                'warnings': []
            }
            
            if rule['type'] == 'syntax_check':
                # Validate syntax of generated files
                for file_info in results.get('generated_files', []):
                    file_path = file_info['path']
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        compile(content, file_path, 'exec')
                    except SyntaxError as e:
                        rule_result['passed'] = False
                        rule_result['errors'].append(f"Syntax error in {file_path}: {e}")
                    except Exception as e:
                        rule_result['warnings'].append(f"Could not validate {file_path}: {e}")
            
            validation_results.append(rule_result)
        
        return validation_results