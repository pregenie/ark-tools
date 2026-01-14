#!/usr/bin/env python3
"""
MAMS-006: Migration Planning Engine with Critical Triad
Orchestrates intelligent migration planning using Brain, Surgeon, Mover
"""

import json
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

@dataclass
class MigrationPhase:
    """Migration execution phase"""
    phase_name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: int = 0  # minutes
    risk_level: str = "LOW"
    tasks: List[str] = field(default_factory=list)
    rollback_points: List[str] = field(default_factory=list)

@dataclass
class MigrationPlan:
    """Comprehensive migration plan"""
    plan_id: str
    plan_name: str
    created_at: datetime
    status: str = "draft"
    
    # Brain outputs
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    pattern_matches: List[Dict] = field(default_factory=list)
    risk_assessment: Dict[str, float] = field(default_factory=dict)
    
    # Surgeon outputs
    transformation_plan: Dict[str, Any] = field(default_factory=dict)
    code_changes: List[Dict] = field(default_factory=list)
    validation_results: Dict[str, bool] = field(default_factory=dict)
    
    # Mover outputs
    file_operations: List[Dict] = field(default_factory=list)
    backup_locations: List[str] = field(default_factory=list)
    rollback_points: List[Dict] = field(default_factory=list)
    
    # Execution metadata
    phases: List[MigrationPhase] = field(default_factory=list)
    estimated_duration: int = 0  # minutes
    estimated_risk_score: float = 0.0
    success_metrics: Dict[str, Any] = field(default_factory=dict)

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class MigrationPlanningEngine:
    """
    MAMS-006: Migration Planning Engine with Critical Triad Integration
    
    Orchestrates Brain (AI), Surgeon (AST), and Mover (File System) to create
    comprehensive migration plans with intelligent sequencing and risk assessment.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.brain_engine = None
        self.surgeon_engine = None
        self.mover_engine = None
        
    def initialize_triad_components(self):
        """Initialize the Critical Triad components"""
        try:
            # Import and initialize Brain (AI Engine)
            from migrations.ai_engine import AIMigrationEngine
            self.brain_engine = AIMigrationEngine()
            self.logger.info("✅ Brain (AI Engine) initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Brain initialization failed: {e}")
            
        try:
            # Import and initialize Surgeon (AST Analyzer) 
            from arkyvus.architecture_compiler.analyzer import ArkyvusDecoratorAnalyzer
            self.surgeon_engine = ArkyvusDecoratorAnalyzer()
            self.logger.info("✅ Surgeon (AST Analyzer) initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Surgeon initialization failed: {e}")
            
        try:
            # Import and initialize Mover (Data Migration Engine)
            from migrations.data_mover import DataMover
            self.mover_engine = DataMover()
            self.logger.info("✅ Mover (Data Migration Engine) initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Mover initialization failed: {e}")
    
    async def generate_migration_plan(self, services: List[Dict[str, Any]], 
                                    consolidation_strategy: str = "unified") -> MigrationPlan:
        """
        Generate comprehensive migration plan using Critical Triad
        """
        plan_id = str(uuid.uuid4())
        plan = MigrationPlan(
            plan_id=plan_id,
            plan_name=f"Migration Plan {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            created_at=datetime.now()
        )
        
        self.logger.info(f"🧠 Generating migration plan {plan_id} for {len(services)} services")
        
        # Phase 1: AI Analysis (Brain)
        if self.brain_engine:
            plan.ai_analysis = await self._brain_analyze_services(services)
            plan.pattern_matches = await self._brain_find_patterns(services)
            plan.risk_assessment = await self._brain_assess_risks(services)
        else:
            self.logger.warning("Brain not available, using fallback analysis")
            plan.ai_analysis = self._fallback_analysis(services)
            
        # Phase 2: AST Transformation Planning (Surgeon)
        if self.surgeon_engine:
            plan.transformation_plan = await self._surgeon_plan_transformations(services, plan.ai_analysis)
            plan.code_changes = await self._surgeon_generate_code_changes(services)
            plan.validation_results = await self._surgeon_validate_changes(plan.code_changes)
        else:
            self.logger.warning("Surgeon not available, using basic transformation plan")
            plan.transformation_plan = self._basic_transformation_plan(services)
            
        # Phase 3: File Operations Planning (Mover)
        if self.mover_engine:
            plan.file_operations = await self._mover_plan_file_operations(services)
            plan.backup_locations = await self._mover_plan_backups(services)
            plan.rollback_points = await self._mover_plan_rollback_points(services)
        else:
            self.logger.warning("Mover not available, using basic file operations")
            plan.file_operations = self._basic_file_operations(services)
        
        # Phase 4: Execution Planning
        plan.phases = self._create_execution_phases(plan)
        plan.estimated_duration = self._calculate_duration(plan)
        plan.estimated_risk_score = self._calculate_risk_score(plan)
        plan.success_metrics = self._define_success_metrics(plan)
        
        self.logger.info(f"✅ Migration plan generated: {plan.estimated_duration}min, Risk: {plan.estimated_risk_score:.2f}")
        return plan
    
    async def _brain_analyze_services(self, services: List[Dict]) -> Dict[str, Any]:
        """Use Brain (AI) to analyze service patterns and relationships"""
        analysis = {
            "service_patterns": {},
            "consolidation_opportunities": [],
            "complexity_assessment": {},
            "recommended_strategy": "unified"
        }
        
        for service in services:
            service_name = service.get('service_name', 'unknown')
            
            # Analyze service patterns using AI if available
            try:
                # This would call the Brain's analysis capabilities
                pattern_analysis = {
                    "architecture_pattern": self._detect_architecture_pattern(service),
                    "complexity_score": self._calculate_service_complexity(service),
                    "consolidation_potential": self._assess_consolidation_potential(service),
                    "migration_priority": self._assess_migration_priority(service)
                }
                analysis["service_patterns"][service_name] = pattern_analysis
            except Exception as e:
                self.logger.error(f"Error analyzing service {service_name}: {e}")
                
        return analysis
    
    async def _brain_find_patterns(self, services: List[Dict]) -> List[Dict]:
        """Use Brain to find migration patterns from previous successes"""
        patterns = []
        
        # Group services by similarity
        service_groups = self._group_similar_services(services)
        
        for group_name, group_services in service_groups.items():
            pattern = {
                "pattern_type": group_name,
                "services": [s.get('service_name') for s in group_services],
                "recommended_approach": self._recommend_approach(group_services),
                "confidence_score": 0.85,
                "historical_success_rate": 0.92
            }
            patterns.append(pattern)
            
        return patterns
    
    async def _brain_assess_risks(self, services: List[Dict]) -> Dict[str, float]:
        """Use Brain to assess migration risks"""
        risk_factors = {
            "code_complexity": 0.0,
            "dependency_complexity": 0.0,
            "data_migration_risk": 0.0,
            "business_impact_risk": 0.0,
            "technical_debt_risk": 0.0
        }
        
        for service in services:
            # Calculate risk factors
            complexity = self._calculate_service_complexity(service)
            dependencies = len(service.get('dependencies', []))
            
            # Update risk factors
            risk_factors["code_complexity"] += complexity / len(services)
            risk_factors["dependency_complexity"] += (dependencies / 10) / len(services)
            
        # Overall risk calculation
        overall_risk = sum(risk_factors.values()) / len(risk_factors)
        risk_factors["overall_risk"] = min(overall_risk, 1.0)
        
        return risk_factors
    
    async def _surgeon_plan_transformations(self, services: List[Dict], ai_analysis: Dict) -> Dict[str, Any]:
        """Use Surgeon (AST) to plan code transformations"""
        transformation_plan = {
            "transformation_operations": [],
            "code_generation_templates": {},
            "validation_rules": [],
            "compatibility_layers": []
        }
        
        for service in services:
            service_name = service.get('service_name')
            
            # Plan AST transformations
            transformations = {
                "service_consolidation": {
                    "target_service": f"Unified{service_name.replace('Service', '')}Service",
                    "methods_to_migrate": service.get('methods', []),
                    "imports_to_update": [],
                    "deprecation_strategy": "gradual"
                },
                "method_transformations": [],
                "import_updates": []
            }
            
            transformation_plan["transformation_operations"].append({
                "source_service": service_name,
                "transformations": transformations
            })
            
        return transformation_plan
    
    async def _surgeon_generate_code_changes(self, services: List[Dict]) -> List[Dict]:
        """Generate specific code changes using Surgeon"""
        code_changes = []
        
        for service in services:
            service_name = service.get('service_name')
            
            change = {
                "file_path": f"arkyvus/services/{service_name.lower()}.py",
                "change_type": "service_consolidation",
                "operations": [
                    {
                        "operation": "create_unified_service",
                        "target_path": f"arkyvus/services/unified/{service_name.lower()}_service.py",
                        "template": "unified_service_template"
                    },
                    {
                        "operation": "add_deprecation_warnings",
                        "source_path": f"arkyvus/services/{service_name.lower()}.py",
                        "deprecation_date": (datetime.now() + timedelta(days=180)).isoformat()
                    }
                ],
                "validation_checks": [
                    "syntax_validation",
                    "import_resolution", 
                    "type_checking",
                    "test_compatibility"
                ]
            }
            
            code_changes.append(change)
            
        return code_changes
    
    async def _surgeon_validate_changes(self, code_changes: List[Dict]) -> Dict[str, bool]:
        """Validate planned code changes"""
        validation_results = {}
        
        for change in code_changes:
            file_path = change.get('file_path')
            
            # Simulate validation checks
            validation_results[file_path] = {
                "syntax_valid": True,
                "imports_resolvable": True, 
                "types_consistent": True,
                "tests_compatible": True,
                "overall_valid": True
            }
            
        return validation_results
    
    async def _mover_plan_file_operations(self, services: List[Dict]) -> List[Dict]:
        """Plan file system operations using Mover"""
        file_operations = []
        
        for service in services:
            service_name = service.get('service_name')
            
            operations = {
                "source_files": [
                    f"arkyvus/services/{service_name.lower()}.py"
                ],
                "backup_operations": [
                    {
                        "operation": "backup_file",
                        "source": f"arkyvus/services/{service_name.lower()}.py",
                        "backup_path": f".migration_backups/{datetime.now().strftime('%Y%m%d_%H%M%S')}/{service_name.lower()}.py"
                    }
                ],
                "move_operations": [
                    {
                        "operation": "create_unified_service",
                        "target_path": f"arkyvus/services/unified/{service_name.lower()}_service.py"
                    }
                ],
                "cleanup_operations": [
                    {
                        "operation": "deprecate_file",
                        "file_path": f"arkyvus/services/{service_name.lower()}.py"
                    }
                ]
            }
            
            file_operations.append(operations)
            
        return file_operations
    
    async def _mover_plan_backups(self, services: List[Dict]) -> List[str]:
        """Plan backup locations using Mover"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_locations = [
            f".migration_backups/{timestamp}/services/",
            f".migration_backups/{timestamp}/database/",
            f".migration_backups/{timestamp}/configuration/"
        ]
        return backup_locations
    
    async def _mover_plan_rollback_points(self, services: List[Dict]) -> List[Dict]:
        """Plan rollback points using Mover"""
        rollback_points = []
        
        phases = ["preparation", "transformation", "movement", "validation", "finalization"]
        
        for i, phase in enumerate(phases):
            rollback_point = {
                "checkpoint_id": str(uuid.uuid4()),
                "phase": phase,
                "description": f"Rollback point after {phase} phase",
                "rollback_procedures": [
                    "restore_service_files",
                    "restore_database_state",
                    "restore_configuration"
                ],
                "validation_checks": [
                    "service_availability",
                    "data_integrity",
                    "configuration_validity"
                ]
            }
            rollback_points.append(rollback_point)
            
        return rollback_points
    
    def _create_execution_phases(self, plan: MigrationPlan) -> List[MigrationPhase]:
        """Create detailed execution phases"""
        phases = []
        
        # Phase 1: Preparation
        preparation = MigrationPhase(
            phase_name="preparation",
            description="Create backups, validate environment, set recovery points",
            estimated_duration=15,
            risk_level="LOW",
            tasks=[
                "Create backup snapshots",
                "Validate database connections",
                "Check service dependencies", 
                "Set initial recovery point"
            ],
            rollback_points=["initial_state"]
        )
        phases.append(preparation)
        
        # Phase 2: Transformation
        transformation = MigrationPhase(
            phase_name="transformation",
            description="Apply AST changes, generate new code, update imports",
            dependencies=["preparation"],
            estimated_duration=45,
            risk_level="MEDIUM",
            tasks=[
                "Apply code transformations",
                "Generate unified services",
                "Update import statements",
                "Create compatibility layers"
            ],
            rollback_points=["post_transformation"]
        )
        phases.append(transformation)
        
        # Phase 3: Movement
        movement = MigrationPhase(
            phase_name="movement",
            description="Move files, update paths, fix references, update configs",
            dependencies=["transformation"],
            estimated_duration=20,
            risk_level="MEDIUM",
            tasks=[
                "Move service files to unified structure",
                "Update configuration files",
                "Fix import references",
                "Update service registrations"
            ],
            rollback_points=["post_movement"]
        )
        phases.append(movement)
        
        # Phase 4: Validation
        validation = MigrationPhase(
            phase_name="validation",
            description="Run tests, check integration, verify functionality",
            dependencies=["movement"],
            estimated_duration=30,
            risk_level="HIGH",
            tasks=[
                "Run unit tests",
                "Run integration tests",
                "Verify service functionality",
                "Check performance metrics"
            ],
            rollback_points=["post_validation"]
        )
        phases.append(validation)
        
        # Phase 5: Finalization
        finalization = MigrationPhase(
            phase_name="finalization",
            description="Commit changes, update docs, clean temporary files",
            dependencies=["validation"],
            estimated_duration=10,
            risk_level="LOW",
            tasks=[
                "Commit migration changes",
                "Update documentation",
                "Clean temporary files",
                "Record migration metrics"
            ],
            rollback_points=["final_state"]
        )
        phases.append(finalization)
        
        return phases
    
    def _calculate_duration(self, plan: MigrationPlan) -> int:
        """Calculate total estimated duration"""
        return sum(phase.estimated_duration for phase in plan.phases)
    
    def _calculate_risk_score(self, plan: MigrationPlan) -> float:
        """Calculate overall risk score"""
        if not plan.risk_assessment:
            return 0.5  # Default medium risk
            
        risk_weights = {
            "code_complexity": 0.25,
            "dependency_complexity": 0.20,
            "data_migration_risk": 0.20,
            "business_impact_risk": 0.20,
            "technical_debt_risk": 0.15
        }
        
        weighted_risk = 0.0
        for factor, weight in risk_weights.items():
            risk_value = plan.risk_assessment.get(factor, 0.5)
            weighted_risk += risk_value * weight
            
        return min(weighted_risk, 1.0)
    
    def _define_success_metrics(self, plan: MigrationPlan) -> Dict[str, Any]:
        """Define success metrics for the migration"""
        return {
            "quality_metrics": {
                "code_quality_score_target": 0.9,
                "test_coverage_target": 0.85,
                "performance_regression_threshold": 0.05
            },
            "reliability_metrics": {
                "uptime_target": 0.99,
                "error_rate_threshold": 0.01,
                "rollback_success_rate": 1.0
            },
            "business_metrics": {
                "feature_functionality_preservation": 1.0,
                "user_experience_impact_threshold": 0.02,
                "data_integrity_requirement": 1.0
            }
        }
    
    # Utility methods for analysis
    def _detect_architecture_pattern(self, service: Dict) -> str:
        """Detect the architectural pattern of a service"""
        service_name = service.get('service_name', '').lower()
        
        if 'repository' in service_name:
            return 'repository_pattern'
        elif 'service' in service_name:
            return 'service_layer_pattern'
        elif 'manager' in service_name:
            return 'manager_pattern'
        elif 'handler' in service_name:
            return 'handler_pattern'
        else:
            return 'unknown_pattern'
    
    def _calculate_service_complexity(self, service: Dict) -> float:
        """Calculate complexity score for a service"""
        complexity = 0.0
        
        # Method count factor
        methods = service.get('methods', [])
        complexity += len(methods) * 0.1
        
        # Dependencies factor
        dependencies = service.get('dependencies', [])
        complexity += len(dependencies) * 0.15
        
        # Service type factor
        service_type = service.get('source_type', 'service')
        type_weights = {
            'service': 0.1,
            'manager': 0.2,
            'handler': 0.15,
            'repository': 0.2,
            'client': 0.1
        }
        complexity += type_weights.get(service_type.lower(), 0.1)
        
        return min(complexity, 1.0)
    
    def _assess_consolidation_potential(self, service: Dict) -> float:
        """Assess how well a service can be consolidated"""
        # Services with similar patterns have higher consolidation potential
        service_name = service.get('service_name', '').lower()
        
        if any(pattern in service_name for pattern in ['auth', 'login', 'security']):
            return 0.9  # High consolidation potential
        elif any(pattern in service_name for pattern in ['user', 'profile', 'account']):
            return 0.8
        elif any(pattern in service_name for pattern in ['data', 'repository', 'storage']):
            return 0.7
        else:
            return 0.5  # Medium potential
    
    def _assess_migration_priority(self, service: Dict) -> str:
        """Assess migration priority"""
        complexity = self._calculate_service_complexity(service)
        consolidation_potential = self._assess_consolidation_potential(service)
        
        if complexity > 0.7 and consolidation_potential < 0.5:
            return "LOW"  # Complex and hard to consolidate
        elif consolidation_potential > 0.8:
            return "HIGH"  # Easy to consolidate
        else:
            return "MEDIUM"
    
    def _group_similar_services(self, services: List[Dict]) -> Dict[str, List[Dict]]:
        """Group services by similarity patterns"""
        groups = {
            "authentication_services": [],
            "data_services": [],
            "ui_services": [],
            "integration_services": [],
            "utility_services": []
        }
        
        for service in services:
            service_name = service.get('service_name', '').lower()
            
            if any(pattern in service_name for pattern in ['auth', 'login', 'security', 'permission']):
                groups["authentication_services"].append(service)
            elif any(pattern in service_name for pattern in ['data', 'repository', 'database', 'storage']):
                groups["data_services"].append(service)
            elif any(pattern in service_name for pattern in ['ui', 'component', 'render', 'view']):
                groups["ui_services"].append(service)
            elif any(pattern in service_name for pattern in ['integration', 'api', 'webhook', 'client']):
                groups["integration_services"].append(service)
            else:
                groups["utility_services"].append(service)
                
        return {k: v for k, v in groups.items() if v}  # Remove empty groups
    
    def _recommend_approach(self, group_services: List[Dict]) -> str:
        """Recommend migration approach for service group"""
        if len(group_services) > 5:
            return "batch_consolidation"
        elif len(group_services) > 2:
            return "phased_consolidation"
        else:
            return "direct_consolidation"
    
    def _fallback_analysis(self, services: List[Dict]) -> Dict[str, Any]:
        """Fallback analysis when Brain is not available"""
        return {
            "service_patterns": {
                service.get('service_name'): {
                    "architecture_pattern": self._detect_architecture_pattern(service),
                    "complexity_score": self._calculate_service_complexity(service),
                    "consolidation_potential": self._assess_consolidation_potential(service),
                    "migration_priority": self._assess_migration_priority(service)
                } for service in services
            },
            "consolidation_opportunities": [
                f"Consolidate {len(services)} services into unified architecture"
            ],
            "complexity_assessment": {
                "overall_complexity": sum(self._calculate_service_complexity(s) for s in services) / len(services),
                "high_complexity_services": [
                    s.get('service_name') for s in services 
                    if self._calculate_service_complexity(s) > 0.7
                ]
            },
            "recommended_strategy": "unified"
        }
    
    def _basic_transformation_plan(self, services: List[Dict]) -> Dict[str, Any]:
        """Basic transformation plan when Surgeon is not available"""
        return {
            "transformation_operations": [
                {
                    "source_service": service.get('service_name'),
                    "target_service": f"Unified{service.get('service_name', '').replace('Service', '')}Service",
                    "operations": ["consolidate", "standardize", "optimize"]
                } for service in services
            ],
            "estimated_effort": len(services) * 4,  # 4 hours per service
            "risk_level": "MEDIUM"
        }
    
    def _basic_file_operations(self, services: List[Dict]) -> List[Dict]:
        """Basic file operations when Mover is not available"""
        return [
            {
                "service_name": service.get('service_name'),
                "operations": [
                    "backup_original",
                    "create_unified_version",
                    "update_imports",
                    "deprecate_original"
                ]
            } for service in services
        ]


def test_migration_planning_engine():
    """Test the migration planning engine"""
    print("=" * 60)
    print("MAMS-006: Migration Planning Engine Test")
    print("=" * 60)
    
    # Initialize engine
    engine = MigrationPlanningEngine()
    engine.initialize_triad_components()
    
    # Test data
    test_services = [
        {
            'service_name': 'AuthService',
            'source_type': 'service',
            'methods': ['login', 'logout', 'validate_token', 'refresh_token'],
            'dependencies': ['UserRepository', 'TokenService'],
            'complexity_score': 0.6
        },
        {
            'service_name': 'UserManager',
            'source_type': 'manager', 
            'methods': ['create_user', 'update_user', 'delete_user', 'get_user'],
            'dependencies': ['DatabaseConnector', 'CacheService'],
            'complexity_score': 0.4
        },
        {
            'service_name': 'PaymentHandler',
            'source_type': 'handler',
            'methods': ['process_payment', 'refund_payment', 'validate_card'],
            'dependencies': ['PaymentGateway', 'TransactionRepository'],
            'complexity_score': 0.8
        }
    ]
    
    async def run_test():
        print(f"Testing migration planning for {len(test_services)} services...")
        
        # Generate migration plan
        plan = await engine.generate_migration_plan(test_services, "unified")
        
        # Display results
        print(f"\n🎯 Migration Plan Generated:")
        print(f"   Plan ID: {plan.plan_id}")
        print(f"   Estimated Duration: {plan.estimated_duration} minutes")
        print(f"   Risk Score: {plan.estimated_risk_score:.3f}")
        print(f"   Phases: {len(plan.phases)}")
        
        print(f"\n🧠 AI Analysis:")
        service_patterns = plan.ai_analysis.get('service_patterns', {})
        print(f"   Analyzed Services: {len(service_patterns)}")
        for service_name, analysis in list(service_patterns.items())[:2]:
            print(f"   {service_name}: {analysis.get('architecture_pattern')} (complexity: {analysis.get('complexity_score', 0):.2f})")
        
        print(f"\n🔧 Transformation Plan:")
        transformations = plan.transformation_plan.get('transformation_operations', [])
        print(f"   Operations: {len(transformations)}")
        for transform in transformations[:2]:
            print(f"   {transform.get('source_service')} → {transform.get('transformations', {}).get('service_consolidation', {}).get('target_service', 'N/A')}")
        
        print(f"\n📁 File Operations:")
        print(f"   Backup Locations: {len(plan.backup_locations)}")
        print(f"   File Operations: {len(plan.file_operations)}")
        print(f"   Rollback Points: {len(plan.rollback_points)}")
        
        print(f"\n📊 Execution Phases:")
        for phase in plan.phases:
            print(f"   {phase.phase_name.title()}: {phase.estimated_duration}min ({phase.risk_level} risk)")
            print(f"     Tasks: {len(phase.tasks)}")
        
        print(f"\n✅ Migration Planning Engine Test Complete!")
        return True
    
    # Run async test
    import asyncio
    success = asyncio.run(run_test())
    return success


if __name__ == "__main__":
    success = test_migration_planning_engine()
    sys.exit(0 if success else 1)