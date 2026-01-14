#!/usr/bin/env python3
"""
MAMS-003: Frontend Service Classification System
Classifies React/TypeScript frontend services by layer, object type, and migration strategy
"""

import os
import re
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from arkyvus.migrations.mams_001_database_schema import MigrationDatabaseManager
    from arkyvus.services.unified_logger import UnifiedLogger
except ImportError:
    # Fallback for testing
    class MigrationDatabaseManager:
        def __init__(self):
            pass
        async def get_discovered_frontend_services(self):
            import asyncpg
            conn = await asyncpg.connect("postgresql://admin:chooters@db:5432/arkyvus_db")
            try:
                records = await conn.fetch("""
                    SELECT id, source_type, full_qualified_name, service_name, method_name, 
                           method_signature, current_state, discovery_metadata
                    FROM migration_source_catalog 
                    WHERE full_qualified_name LIKE 'frontend.%'
                    ORDER BY service_name
                """)
                services = []
                for record in records:
                    services.append({
                        'id': str(record['id']),
                        'source_type': record['source_type'],
                        'full_qualified_name': record['full_qualified_name'],
                        'service_name': record['service_name'],
                        'method_name': record['method_name'],
                        'method_signature': json.loads(record['method_signature']) if record['method_signature'] else [],
                        'current_state': record['current_state'],
                        'file_path': json.loads(record['discovery_metadata']).get('file_path', '') if record['discovery_metadata'] else ''
                    })
                return services
            finally:
                await conn.close()
                
        async def update_service_classification(self, service_id, classification):
            import asyncpg
            conn = await asyncpg.connect("postgresql://admin:chooters@db:5432/arkyvus_db")
            try:
                # Map strategy to database enum values
                strategy_map = {
                    'consolidate': 'CONSOLIDATION',
                    'modernize': 'MODERNIZATION', 
                    'preserve': 'PRESERVE',
                    'deprecate': 'DEPRECATION'
                }
                db_strategy = strategy_map.get(classification['migration_strategy'], 'PRESERVE')
                
                await conn.execute("""
                    INSERT INTO migration_classifications 
                    (service_id, migration_type, migration_reason, priority, 
                     suggested_target, migration_metadata, created_at)
                    VALUES ($1, $2, $3, 'MEDIUM', $4, $5, CURRENT_TIMESTAMP)
                    ON CONFLICT (service_id) DO UPDATE SET
                        migration_type = EXCLUDED.migration_type,
                        migration_reason = EXCLUDED.migration_reason,
                        suggested_target = EXCLUDED.suggested_target,
                        migration_metadata = EXCLUDED.migration_metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, service_id, db_strategy, 
                     classification['reasoning'], classification.get('consolidation_target'),
                     json.dumps(classification))
            finally:
                await conn.close()
    
    class UnifiedLogger:
        @staticmethod
        def getLogger(name):
            import logging
            return logging.getLogger(name)

logger = UnifiedLogger.getLogger(__name__)

@dataclass
class ClassificationResult:
    """Frontend service classification result"""
    service_id: str
    service_name: str
    layer: str  # presentation, application, infrastructure, cross_cutting
    object_type: str  # service, component, hook, context, utility, client
    frontend_category: str  # ui_component, business_service, data_service, utility_service
    migration_strategy: str  # consolidate, modernize, preserve, deprecate
    characteristics: List[str]
    confidence: float
    reasoning: str
    consolidation_target: Optional[str] = None

class FrontendClassificationEngine:
    """
    Classifies frontend React/TypeScript services according to MAMS-003 specification
    """
    
    def __init__(self):
        self.db_manager = MigrationDatabaseManager()
        self.classification_rules = self._load_frontend_classification_rules()
        
    def _load_frontend_classification_rules(self) -> Dict[str, Any]:
        """Load frontend-specific classification rules"""
        return {
            "layer_rules": {
                "presentation": {
                    "indicators": [
                        "components/", "pages/", "layouts/", "ui/"
                    ],
                    "patterns": [
                        r".*Component\.tsx?$", r".*Page\.tsx?$", r".*Layout\.tsx?$",
                        r".*Modal\.tsx?$", r".*Dialog\.tsx?$", r".*Button\.tsx?$"
                    ],
                    "characteristics": [
                        "jsx_content", "react_component", "ui_rendering", "user_interaction"
                    ]
                },
                "application": {
                    "indicators": [
                        "services/", "hooks/", "contexts/", "stores/"
                    ],
                    "patterns": [
                        r".*Service\.ts$", r"use.*\.ts$", r".*Context\.tsx?$",
                        r".*Store\.ts$", r".*Manager\.ts$"
                    ],
                    "characteristics": [
                        "business_logic", "state_management", "data_flow", "api_orchestration"
                    ]
                },
                "infrastructure": {
                    "indicators": [
                        "api/", "config/", "utils/", "lib/"
                    ],
                    "patterns": [
                        r".*Client\.ts$", r".*Api\.ts$", r".*Config\.ts$",
                        r".*Utils?\.ts$", r".*Helper\.ts$"
                    ],
                    "characteristics": [
                        "external_integration", "configuration", "utility_functions", "data_access"
                    ]
                },
                "cross_cutting": {
                    "indicators": [
                        "shared/", "common/", "types/", "constants/"
                    ],
                    "patterns": [
                        r".*\.types\.ts$", r".*\.d\.ts$", r"constants\.ts$",
                        r"index\.ts$", r".*\.interface\.ts$"
                    ],
                    "characteristics": [
                        "type_definitions", "shared_constants", "common_utilities", "cross_domain"
                    ]
                }
            },
            "object_type_rules": {
                "component": {
                    "patterns": [
                        r".*Component\.tsx$", r".*\.component\.tsx$",
                        r"^[A-Z][a-zA-Z]*\.tsx$"  # PascalCase .tsx files
                    ],
                    "content_indicators": [
                        "export default", "React.FC", "JSX.Element", "return ("
                    ],
                    "characteristics": ["react_component", "renders_jsx", "props_interface"]
                },
                "service": {
                    "patterns": [
                        r".*Service\.ts$", r".*\.service\.ts$",
                        r".*Client\.ts$", r".*Api\.ts$"
                    ],
                    "content_indicators": [
                        "class ", "export class", "async ", "axios", "fetch"
                    ],
                    "characteristics": ["business_logic", "api_calls", "data_processing"]
                },
                "hook": {
                    "patterns": [
                        r"use[A-Z].*\.ts$", r".*\.hook\.ts$"
                    ],
                    "content_indicators": [
                        "export const use", "export function use", "useState", "useEffect"
                    ],
                    "characteristics": ["react_hook", "state_management", "lifecycle_logic"]
                },
                "context": {
                    "patterns": [
                        r".*Context\.tsx?$", r".*\.context\.tsx?$"
                    ],
                    "content_indicators": [
                        "createContext", "useContext", "Provider", "Context"
                    ],
                    "characteristics": ["state_provider", "global_state", "context_api"]
                },
                "utility": {
                    "patterns": [
                        r".*Utils?\.ts$", r".*Helper\.ts$", r".*\.util\.ts$"
                    ],
                    "content_indicators": [
                        "export const", "export function", "helper", "util"
                    ],
                    "characteristics": ["utility_functions", "helpers", "shared_logic"]
                }
            },
            "migration_strategy_rules": {
                "consolidate": {
                    "conditions": [
                        "duplicate_functionality", "small_service", "similar_services_exist"
                    ],
                    "indicators": [
                        "few_methods", "simple_logic", "common_patterns"
                    ]
                },
                "modernize": {
                    "conditions": [
                        "legacy_patterns", "outdated_dependencies", "performance_issues"
                    ],
                    "indicators": [
                        "class_components", "old_lifecycle_methods", "deprecated_apis"
                    ]
                },
                "preserve": {
                    "conditions": [
                        "complex_logic", "stable_implementation", "critical_functionality"
                    ],
                    "indicators": [
                        "many_methods", "complex_state", "important_business_logic"
                    ]
                },
                "deprecate": {
                    "conditions": [
                        "unused_code", "replaced_functionality", "technical_debt"
                    ],
                    "indicators": [
                        "no_imports", "commented_out", "TODO_remove"
                    ]
                }
            }
        }
    
    async def classify_all_frontend_services(self) -> List[ClassificationResult]:
        """Classify all discovered frontend services"""
        logger.info("🏗️ Starting frontend service classification")
        
        # Get discovered frontend services from database
        services = await self.db_manager.get_discovered_frontend_services()
        logger.info(f"Found {len(services)} frontend services to classify")
        
        classification_results = []
        
        for service in services:
            try:
                result = await self._classify_single_service(service)
                classification_results.append(result)
                
                # Store classification in database
                await self.db_manager.update_service_classification(
                    service['id'],
                    {
                        'layer': result.layer,
                        'object_type': result.object_type,
                        'frontend_category': result.frontend_category,
                        'migration_strategy': result.migration_strategy,
                        'characteristics': result.characteristics,
                        'confidence': result.confidence,
                        'reasoning': result.reasoning,
                        'consolidation_target': result.consolidation_target
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to classify service {service.get('service_name', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"✅ Classified {len(classification_results)} frontend services")
        
        # Generate classification summary
        summary = self._generate_classification_summary(classification_results)
        logger.info(f"📊 Classification Summary:\n{json.dumps(summary, indent=2)}")
        
        return classification_results
    
    async def _classify_single_service(self, service: Dict[str, Any]) -> ClassificationResult:
        """Classify a single frontend service"""
        service_name = service.get('service_name', '')
        file_path = service.get('file_path', '')
        method_signature = service.get('method_signature', {})
        source_type = service.get('source_type', '')
        
        # Determine layer
        layer = self._classify_layer(file_path, service_name, method_signature)
        
        # Determine object type
        object_type = self._classify_object_type(file_path, service_name, method_signature, source_type)
        
        # Determine frontend category
        frontend_category = self._classify_frontend_category(layer, object_type, service_name)
        
        # Determine migration strategy
        migration_strategy = self._classify_migration_strategy(service, layer, object_type)
        
        # Gather characteristics
        characteristics = self._gather_characteristics(service, layer, object_type)
        
        # Calculate confidence
        confidence = self._calculate_confidence(service, layer, object_type)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(service, layer, object_type, migration_strategy)
        
        # Determine consolidation target
        consolidation_target = self._determine_consolidation_target(service, migration_strategy, frontend_category)
        
        return ClassificationResult(
            service_id=service['id'],
            service_name=service_name,
            layer=layer,
            object_type=object_type,
            frontend_category=frontend_category,
            migration_strategy=migration_strategy,
            characteristics=characteristics,
            confidence=confidence,
            reasoning=reasoning,
            consolidation_target=consolidation_target
        )
    
    def _classify_layer(self, file_path: str, service_name: str, method_signature: Dict) -> str:
        """Classify service layer based on path and characteristics"""
        path_lower = file_path.lower()
        
        for layer, rules in self.classification_rules["layer_rules"].items():
            # Check path indicators
            for indicator in rules["indicators"]:
                if indicator in path_lower:
                    return layer
            
            # Check file patterns
            for pattern in rules["patterns"]:
                if re.search(pattern, file_path, re.IGNORECASE):
                    return layer
        
        # Default classification based on common patterns
        if any(term in path_lower for term in ["component", "page", "layout", "ui"]):
            return "presentation"
        elif any(term in path_lower for term in ["service", "hook", "context", "store"]):
            return "application" 
        elif any(term in path_lower for term in ["api", "config", "util", "lib"]):
            return "infrastructure"
        else:
            return "cross_cutting"
    
    def _classify_object_type(self, file_path: str, service_name: str, method_signature: Dict, source_type: str) -> str:
        """Classify object type based on file patterns and content"""
        # Use source_type if available and reliable
        if source_type in ["component", "hook", "context", "service", "utility"]:
            return source_type
        
        # Pattern-based classification
        for obj_type, rules in self.classification_rules["object_type_rules"].items():
            for pattern in rules["patterns"]:
                if re.search(pattern, file_path, re.IGNORECASE):
                    return obj_type
        
        # Fallback classification
        if file_path.endswith('.tsx'):
            return "component"
        elif file_path.endswith('.ts'):
            if service_name.startswith('use') and service_name[3].isupper():
                return "hook"
            elif 'service' in service_name.lower():
                return "service"
            else:
                return "utility"
        else:
            return "utility"
    
    def _classify_frontend_category(self, layer: str, object_type: str, service_name: str) -> str:
        """Classify into frontend-specific categories"""
        if layer == "presentation" and object_type == "component":
            return "ui_component"
        elif layer == "application" and object_type in ["service", "hook", "context"]:
            return "business_service"
        elif layer == "infrastructure" and object_type in ["service", "client"]:
            return "data_service"
        else:
            return "utility_service"
    
    def _classify_migration_strategy(self, service: Dict, layer: str, object_type: str) -> str:
        """Determine migration strategy based on service characteristics"""
        service_name = service.get('service_name', '')
        method_signature = service.get('method_signature', [])
        method_count = len(method_signature) if isinstance(method_signature, list) else 0
        
        # Simple services are consolidation candidates
        if method_count <= 3 and object_type in ["utility", "service"]:
            return "consolidate"
        
        # UI components usually preserved unless very simple
        if object_type == "component" and layer == "presentation":
            if method_count <= 2:
                return "consolidate"
            else:
                return "preserve"
        
        # Complex services preserved
        if method_count > 10:
            return "preserve"
        
        # Services with modern patterns preserved
        if object_type in ["hook", "context"] and layer == "application":
            return "preserve"
        
        # Default to modernize
        return "modernize"
    
    def _gather_characteristics(self, service: Dict, layer: str, object_type: str) -> List[str]:
        """Gather service characteristics"""
        characteristics = []
        
        # Add layer characteristics
        if layer in self.classification_rules["layer_rules"]:
            characteristics.extend(self.classification_rules["layer_rules"][layer]["characteristics"])
        
        # Add object type characteristics
        if object_type in self.classification_rules["object_type_rules"]:
            characteristics.extend(self.classification_rules["object_type_rules"][object_type]["characteristics"])
        
        # Add specific characteristics based on service analysis
        method_signature = service.get('method_signature', [])
        if 'async' in str(method_signature):
            characteristics.append("async_operations")
        
        if 'state' in service.get('service_name', '').lower():
            characteristics.append("state_management")
        
        return list(set(characteristics))  # Remove duplicates
    
    def _calculate_confidence(self, service: Dict, layer: str, object_type: str) -> float:
        """Calculate classification confidence"""
        confidence = 0.7  # Base confidence
        
        file_path = service.get('file_path', '')
        service_name = service.get('service_name', '')
        
        # Increase confidence for clear patterns
        if object_type == "component" and file_path.endswith('.tsx'):
            confidence += 0.2
        
        if object_type == "hook" and service_name.startswith('use'):
            confidence += 0.2
        
        if object_type == "context" and 'context' in service_name.lower():
            confidence += 0.2
        
        # Reduce confidence for unclear cases
        if layer == "cross_cutting":
            confidence -= 0.1
        
        return min(1.0, confidence)
    
    def _generate_reasoning(self, service: Dict, layer: str, object_type: str, migration_strategy: str) -> str:
        """Generate human-readable classification reasoning"""
        file_path = service.get('file_path', '')
        service_name = service.get('service_name', '')
        method_signature = service.get('method_signature', [])
        method_count = len(method_signature) if isinstance(method_signature, list) else 0
        
        reasoning_parts = [
            f"Classified as {layer} layer {object_type}",
            f"based on file path '{file_path}'"
        ]
        
        if object_type == "component" and file_path.endswith('.tsx'):
            reasoning_parts.append("(React component pattern detected)")
        
        if object_type == "hook" and service_name.startswith('use'):
            reasoning_parts.append("(React hook naming pattern)")
        
        reasoning_parts.append(f"Migration strategy '{migration_strategy}'")
        
        if migration_strategy == "consolidate":
            reasoning_parts.append(f"due to simple structure ({method_count} methods)")
        elif migration_strategy == "preserve":
            reasoning_parts.append("due to complexity and importance")
        
        return " ".join(reasoning_parts)
    
    def _determine_consolidation_target(self, service: Dict, migration_strategy: str, frontend_category: str) -> Optional[str]:
        """Determine target service for consolidation"""
        if migration_strategy != "consolidate":
            return None
        
        # Frontend-specific consolidation targets
        consolidation_map = {
            "ui_component": "UnifiedUIComponents",
            "business_service": "UnifiedFrontendServices", 
            "data_service": "UnifiedDataServices",
            "utility_service": "UnifiedFrontendUtilities"
        }
        
        return consolidation_map.get(frontend_category, "UnifiedFrontendServices")
    
    def _generate_classification_summary(self, results: List[ClassificationResult]) -> Dict[str, Any]:
        """Generate summary statistics for classification results"""
        if not results:
            return {}
        
        summary = {
            "total_services": len(results),
            "by_layer": {},
            "by_object_type": {},
            "by_frontend_category": {},
            "by_migration_strategy": {},
            "consolidation_targets": {},
            "average_confidence": sum(r.confidence for r in results) / len(results)
        }
        
        for result in results:
            # Count by layer
            summary["by_layer"][result.layer] = summary["by_layer"].get(result.layer, 0) + 1
            
            # Count by object type
            summary["by_object_type"][result.object_type] = summary["by_object_type"].get(result.object_type, 0) + 1
            
            # Count by frontend category
            summary["by_frontend_category"][result.frontend_category] = summary["by_frontend_category"].get(result.frontend_category, 0) + 1
            
            # Count by migration strategy
            summary["by_migration_strategy"][result.migration_strategy] = summary["by_migration_strategy"].get(result.migration_strategy, 0) + 1
            
            # Count consolidation targets
            if result.consolidation_target:
                summary["consolidation_targets"][result.consolidation_target] = summary["consolidation_targets"].get(result.consolidation_target, 0) + 1
        
        return summary

async def main():
    """Main execution function for testing"""
    engine = FrontendClassificationEngine()
    results = await engine.classify_all_frontend_services()
    
    print(f"🎯 Frontend Classification Complete!")
    print(f"📊 Classified {len(results)} frontend services")
    
    for result in results:
        print(f"\n🔍 {result.service_name}")
        print(f"   Layer: {result.layer}")
        print(f"   Type: {result.object_type}")
        print(f"   Category: {result.frontend_category}")
        print(f"   Strategy: {result.migration_strategy}")
        print(f"   Target: {result.consolidation_target or 'N/A'}")
        print(f"   Confidence: {result.confidence:.2f}")

if __name__ == "__main__":
    asyncio.run(main())