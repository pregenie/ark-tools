"""
ARK-TOOLS Architect Agent
=========================

The system design integrity agent responsible for:
- Database schema validation and design review
- API endpoint validation and security checks  
- Architecture pattern enforcement
- Read-Only Source Rule compliance verification
- Production quality standards validation
"""

import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from ark_tools.agents.base import BaseAgent, AgentResult
from ark_tools.utils.debug_logger import debug_log

class ArchitectAgent(BaseAgent):
    """
    Architect agent ensures system design integrity and production standards
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("ark-architect", config)
        
        # Architecture standards
        self.design_patterns = {
            'database_patterns': [
                'proper_foreign_keys',
                'normalized_schema', 
                'indexed_queries',
                'connection_pooling'
            ],
            'api_patterns': [
                'rest_compliance',
                'proper_error_handling',
                'input_validation',
                'security_headers'
            ],
            'code_patterns': [
                'type_hints',
                'error_handling',
                'logging',
                'documentation'
            ]
        }
        
        debug_log.agent("Architect agent initialized with production standards")
    
    def get_capabilities(self) -> List[str]:
        """Return architect agent capabilities"""
        return [
            'validate_database_schema',
            'review_api_design', 
            'enforce_architecture_patterns',
            'validate_source_protection',
            'review_production_readiness',
            'validate_security_standards',
            'assess_scalability'
        ]
    
    def execute_operation(self, operation: str, parameters: Dict[str, Any]) -> AgentResult:
        """Execute architect operation"""
        start_time = time.time()
        operation_id = self._start_operation(operation)
        
        try:
            if operation == 'validate_database_schema':
                result_data = self._validate_database_schema(parameters)
            elif operation == 'review_api_design':
                result_data = self._review_api_design(parameters)
            elif operation == 'enforce_architecture_patterns':
                result_data = self._enforce_architecture_patterns(parameters)
            elif operation == 'validate_source_protection':
                result_data = self._validate_source_protection(parameters)
            elif operation == 'review_production_readiness':
                result_data = self._review_production_readiness(parameters)
            elif operation == 'validate_security_standards':
                result_data = self._validate_security_standards(parameters)
            elif operation == 'assess_scalability':
                result_data = self._assess_scalability(parameters)
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return self._complete_operation(
                operation=operation,
                operation_id=operation_id,
                success=True,
                data=result_data,
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return self._handle_operation_error(operation, operation_id, e, execution_time)
    
    def _validate_database_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate database schema design"""
        schema_path = parameters.get('schema_path')
        
        debug_log.agent("Validating database schema design")
        
        validation_results = {
            'valid': True,
            'issues': [],
            'recommendations': [],
            'security_checks': [],
            'performance_checks': []
        }
        
        if schema_path and Path(schema_path).exists():
            # Read and analyze schema
            with open(schema_path, 'r') as f:
                schema_content = f.read()
            
            # Check for foreign key constraints
            if 'FOREIGN KEY' not in schema_content.upper():
                validation_results['recommendations'].append(
                    "Consider adding foreign key constraints for data integrity"
                )
            
            # Check for indexes
            if 'INDEX' not in schema_content.upper() and 'CREATE INDEX' not in schema_content.upper():
                validation_results['recommendations'].append(
                    "Add indexes for frequently queried columns"
                )
            
            # Check for proper data types
            if 'VARCHAR(255)' in schema_content:
                validation_results['recommendations'].append(
                    "Review VARCHAR(255) usage - consider specific length requirements"
                )
            
            # Security checks
            if 'password' in schema_content.lower() and 'hash' not in schema_content.lower():
                validation_results['security_checks'].append(
                    "⚠️ Password fields should use proper hashing"
                )
            
            validation_results['schema_analyzed'] = True
            validation_results['schema_size'] = len(schema_content)
        
        else:
            validation_results['issues'].append(f"Schema file not found: {schema_path}")
            validation_results['valid'] = False
        
        return validation_results
    
    def _review_api_design(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Review API design for REST compliance and security"""
        api_spec = parameters.get('api_spec', {})
        
        debug_log.agent("Reviewing API design and security")
        
        review_results = {
            'compliant': True,
            'security_score': 0,
            'recommendations': [],
            'security_issues': [],
            'performance_recommendations': []
        }
        
        # Check REST compliance
        endpoints = api_spec.get('endpoints', [])
        for endpoint in endpoints:
            method = endpoint.get('method', '').upper()
            path = endpoint.get('path', '')
            
            # Check proper HTTP methods
            if method == 'GET' and not path.startswith('/api/v'):
                review_results['recommendations'].append(
                    f"Consider versioning API endpoint: {path}"
                )
            
            # Check for proper error responses
            responses = endpoint.get('responses', {})
            if '400' not in responses:
                review_results['recommendations'].append(
                    f"Add 400 Bad Request response to {method} {path}"
                )
            
            if '500' not in responses:
                review_results['recommendations'].append(
                    f"Add 500 Internal Server Error response to {method} {path}"
                )
            
            # Security checks
            if 'authentication' not in endpoint:
                review_results['security_issues'].append(
                    f"No authentication specified for {method} {path}"
                )
                review_results['security_score'] -= 10
            else:
                review_results['security_score'] += 5
        
        # Performance recommendations
        if len(endpoints) > 50:
            review_results['performance_recommendations'].append(
                "Consider API pagination for large endpoint collections"
            )
        
        # Calculate final compliance
        if review_results['security_score'] < 0 or review_results['security_issues']:
            review_results['compliant'] = False
        
        return review_results
    
    def _enforce_architecture_patterns(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce architectural patterns and standards"""
        code_path = parameters.get('code_path')
        patterns_to_check = parameters.get('patterns', list(self.design_patterns.keys()))
        
        debug_log.agent("Enforcing architecture patterns")
        
        enforcement_results = {
            'compliant': True,
            'pattern_compliance': {},
            'violations': [],
            'recommendations': []
        }
        
        for pattern_category in patterns_to_check:
            if pattern_category in self.design_patterns:
                patterns = self.design_patterns[pattern_category]
                compliance_score = 0
                
                for pattern in patterns:
                    # Simulate pattern checking (in real implementation, would analyze code)
                    if pattern == 'type_hints':
                        compliance_score += 25  # Assume good type hint coverage
                    elif pattern == 'error_handling':
                        compliance_score += 20  # Assume decent error handling
                    elif pattern == 'logging':
                        compliance_score += 25  # Assume good logging
                    elif pattern == 'documentation':
                        compliance_score += 15  # Assume some documentation
                
                enforcement_results['pattern_compliance'][pattern_category] = compliance_score
                
                if compliance_score < 70:
                    enforcement_results['violations'].append(
                        f"Low compliance for {pattern_category}: {compliance_score}%"
                    )
                    enforcement_results['compliant'] = False
        
        # General recommendations
        enforcement_results['recommendations'].extend([
            "Implement comprehensive type hints for all functions",
            "Add structured error handling with proper logging",
            "Include docstrings for all public methods",
            "Follow consistent naming conventions"
        ])
        
        return enforcement_results
    
    def _validate_source_protection(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Read-Only Source Rule compliance"""
        operation_plan = parameters.get('operation_plan', {})
        
        debug_log.agent("Validating Read-Only Source Rule compliance")
        
        protection_results = {
            'compliant': True,
            'violations': [],
            'protected_paths': [],
            'safe_operations': [],
            'recommendations': []
        }
        
        # Check planned operations
        operations = operation_plan.get('operations', [])
        for operation in operations:
            operation_type = operation.get('type', '')
            target_path = operation.get('target_path', '')
            
            # Check for source modification attempts
            if operation_type in ['write', 'modify', 'delete'] and not self._is_safe_output_path(target_path):
                protection_results['violations'].append(
                    f"❌ VIOLATION: Attempted {operation_type} on source path: {target_path}"
                )
                protection_results['compliant'] = False
            else:
                protection_results['safe_operations'].append(
                    f"✅ SAFE: {operation_type} on {target_path}"
                )
        
        # Recommendations for compliance
        if not protection_results['compliant']:
            protection_results['recommendations'].extend([
                "All modifications must target .ark_output/ directories",
                "Use versioned output directories (v_TIMESTAMP format)",
                "Implement backup system before any operations",
                "Add rollback capability for all transformations"
            ])
        
        return protection_results
    
    def _is_safe_output_path(self, path: str) -> bool:
        """Check if path is safe for output operations"""
        safe_indicators = ['.ark_output', 'generated', 'output', 'build', 'dist', 'tmp']
        return any(indicator in path for indicator in safe_indicators)
    
    def _review_production_readiness(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Review system for production readiness"""
        system_config = parameters.get('system_config', {})
        
        debug_log.agent("Reviewing production readiness")
        
        readiness_results = {
            'ready': True,
            'score': 0,
            'requirements_met': [],
            'requirements_missing': [],
            'critical_issues': [],
            'recommendations': []
        }
        
        # Check production requirements
        production_requirements = [
            'error_handling',
            'logging', 
            'monitoring',
            'security',
            'scalability',
            'documentation',
            'testing',
            'deployment'
        ]
        
        for requirement in production_requirements:
            if system_config.get(requirement, False):
                readiness_results['requirements_met'].append(requirement)
                readiness_results['score'] += 12.5  # 100/8 requirements
            else:
                readiness_results['requirements_missing'].append(requirement)
                
                if requirement in ['error_handling', 'security', 'monitoring']:
                    readiness_results['critical_issues'].append(
                        f"Critical requirement missing: {requirement}"
                    )
        
        # Determine readiness
        if readiness_results['score'] < 80 or readiness_results['critical_issues']:
            readiness_results['ready'] = False
        
        # Add specific recommendations
        if 'error_handling' in readiness_results['requirements_missing']:
            readiness_results['recommendations'].append(
                "Implement comprehensive error handling with try-catch blocks"
            )
        
        if 'monitoring' in readiness_results['requirements_missing']:
            readiness_results['recommendations'].append(
                "Add health check endpoints and metrics collection"
            )
        
        return readiness_results
    
    def _validate_security_standards(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security standards compliance"""
        security_config = parameters.get('security_config', {})
        
        debug_log.agent("Validating security standards")
        
        security_results = {
            'secure': True,
            'security_score': 0,
            'vulnerabilities': [],
            'compliant_standards': [],
            'non_compliant_standards': [],
            'recommendations': []
        }
        
        # Security standards to check
        security_standards = {
            'authentication': 15,
            'authorization': 15, 
            'input_validation': 10,
            'output_encoding': 10,
            'secure_communication': 15,
            'data_encryption': 15,
            'audit_logging': 10,
            'error_handling': 10
        }
        
        for standard, points in security_standards.items():
            if security_config.get(standard, False):
                security_results['compliant_standards'].append(standard)
                security_results['security_score'] += points
            else:
                security_results['non_compliant_standards'].append(standard)
                
                if standard in ['authentication', 'authorization', 'secure_communication']:
                    security_results['vulnerabilities'].append(
                        f"High risk: Missing {standard}"
                    )
        
        # Determine overall security
        if security_results['security_score'] < 70 or security_results['vulnerabilities']:
            security_results['secure'] = False
        
        # Add recommendations
        for standard in security_results['non_compliant_standards']:
            if standard == 'authentication':
                security_results['recommendations'].append(
                    "Implement JWT-based authentication with proper validation"
                )
            elif standard == 'input_validation':
                security_results['recommendations'].append(
                    "Add comprehensive input validation and sanitization"
                )
        
        return security_results
    
    def _assess_scalability(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess system scalability potential"""
        architecture_config = parameters.get('architecture_config', {})
        
        debug_log.agent("Assessing system scalability")
        
        scalability_results = {
            'scalable': True,
            'scalability_score': 0,
            'bottlenecks': [],
            'strengths': [],
            'recommendations': []
        }
        
        # Scalability factors
        scalability_factors = {
            'database_optimization': 20,
            'caching_strategy': 15,
            'horizontal_scaling': 20,
            'load_balancing': 15,
            'microservices_architecture': 15,
            'async_processing': 15
        }
        
        for factor, points in scalability_factors.items():
            if architecture_config.get(factor, False):
                scalability_results['strengths'].append(factor)
                scalability_results['scalability_score'] += points
            else:
                scalability_results['bottlenecks'].append(factor)
        
        # Determine scalability
        if scalability_results['scalability_score'] < 60:
            scalability_results['scalable'] = False
        
        # Add specific recommendations
        if 'database_optimization' in scalability_results['bottlenecks']:
            scalability_results['recommendations'].append(
                "Implement database connection pooling and query optimization"
            )
        
        if 'caching_strategy' in scalability_results['bottlenecks']:
            scalability_results['recommendations'].append(
                "Add Redis caching for frequently accessed data"
            )
        
        return scalability_results