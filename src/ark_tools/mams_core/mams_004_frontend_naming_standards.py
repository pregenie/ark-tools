#!/usr/bin/env python3
"""
MAMS-004: Frontend Naming Standards Engine
Applies consistent naming standards to React/TypeScript frontend services
"""

import os
import re
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from arkyvus.services.unified_logger import UnifiedLogger
except ImportError:
    class UnifiedLogger:
        @staticmethod
        def getLogger(name):
            import logging
            return logging.getLogger(name)

logger = UnifiedLogger.getLogger(__name__)

@dataclass
class NamingViolation:
    """Represents a naming standards violation"""
    service_id: str
    service_name: str
    violation_type: str
    current_name: str
    suggested_name: str
    severity: str  # 'error', 'warning', 'info'
    rule: str
    reasoning: str

@dataclass
class NamingStandardResult:
    """Result of applying naming standards"""
    service_id: str
    original_name: str
    standardized_name: str
    name_changed: bool
    violations: List[NamingViolation]
    confidence: float

class FrontendNamingStandardsEngine:
    """
    Applies and validates frontend naming standards according to MAMS-004 specification
    """
    
    def __init__(self):
        self.naming_rules = self._load_frontend_naming_rules()
        self.processed_services = []
        
    def _load_frontend_naming_rules(self) -> Dict[str, Any]:
        """Load frontend-specific naming standards"""
        return {
            "service_naming": {
                "patterns": {
                    "UNIFIED_FRONTEND_SERVICE": {
                        "prefix": "Unified",
                        "suffix": "Service", 
                        "format": "{Prefix}{Domain}{Suffix}",
                        "example": "UnifiedFrontendService",
                        "description": "Core frontend services (API clients, data services)"
                    },
                    "COMPONENT_SERVICE": {
                        "prefix": "",
                        "suffix": "Component",
                        "format": "{Domain}{Suffix}",
                        "example": "AuthComponent", 
                        "description": "React components providing UI functionality"
                    },
                    "HOOK_SERVICE": {
                        "prefix": "use",
                        "suffix": "",
                        "format": "{Prefix}{Domain}",
                        "example": "useAuth",
                        "description": "React hooks for state management and logic"
                    },
                    "CONTEXT_SERVICE": {
                        "prefix": "",
                        "suffix": "Context",
                        "format": "{Domain}{Suffix}",
                        "example": "AuthContext",
                        "description": "React context providers for global state"
                    },
                    "UTILITY_SERVICE": {
                        "prefix": "",
                        "suffix": "Utils",
                        "format": "{Domain}{Suffix}",
                        "example": "DateUtils",
                        "description": "Utility functions and helper modules"
                    }
                },
                "rules": [
                    "PascalCase for components and services",
                    "camelCase for hooks (use prefix)",
                    "No underscores in names",
                    "Max 40 characters for frontend names",
                    "Descriptive and domain-specific",
                    "Consistent suffix patterns"
                ]
            },
            "consolidation_targets": {
                "service": "UnifiedFrontendServices",
                "client": "UnifiedUIComponents", 
                "utility": "UnifiedFrontendUtilities",
                "manager": "UnifiedStateManagers"
            },
            "forbidden_patterns": [
                r".*[_].*",  # No underscores
                r"^[a-z].*Service$",  # Services must start uppercase
                r"^[A-Z].*service$",  # Service suffix must be capitalized
                r".*\d+$",  # No trailing numbers
                r".{41,}",  # Max 40 characters
            ],
            "required_patterns": {
                "component": r"^[A-Z][a-zA-Z]*Component$",
                "hook": r"^use[A-Z][a-zA-Z]*$", 
                "context": r"^[A-Z][a-zA-Z]*Context$",
                "service": r"^[A-Z][a-zA-Z]*Service$",
                "utility": r"^[A-Z][a-zA-Z]*Utils?$"
            }
        }
    
    async def process_all_frontend_services(self) -> List[NamingStandardResult]:
        """Process all frontend services for naming standards"""
        logger.info("🎯 Starting frontend naming standards processing")
        
        # Get classified frontend services from database
        services = await self._get_classified_frontend_services()
        logger.info(f"Processing {len(services)} frontend services for naming standards")
        
        results = []
        
        for service in services:
            try:
                result = await self._process_service_naming(service)
                results.append(result)
                
                # Store naming standard result in database
                await self._store_naming_standard_result(result)
                
            except Exception as e:
                logger.error(f"Failed to process naming for service {service.get('service_name', 'unknown')}: {str(e)}")
                continue
        
        # Generate summary report
        summary = self._generate_naming_summary(results)
        logger.info(f"✅ Naming standards processing complete.\n{json.dumps(summary, indent=2)}")
        
        return results
    
    async def _get_classified_frontend_services(self) -> List[Dict[str, Any]]:
        """Get classified frontend services from database"""
        import asyncpg
        
        conn = await asyncpg.connect("postgresql://admin:chooters@db:5432/arkyvus_db")
        try:
            records = await conn.fetch("""
                SELECT msc.id, msc.source_type, msc.full_qualified_name, msc.service_name, 
                       msc.method_name, msc.method_signature, msc.current_state, 
                       msc.discovery_metadata, mc.migration_type, mc.suggested_target
                FROM migration_source_catalog msc
                LEFT JOIN migration_classifications mc ON msc.id = mc.service_id
                WHERE msc.full_qualified_name LIKE 'frontend.%'
                ORDER BY msc.service_name
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
                    'file_path': json.loads(record['discovery_metadata']).get('file_path', '') if record['discovery_metadata'] else '',
                    'migration_type': record['migration_type'],
                    'suggested_target': record['suggested_target']
                })
            return services
        finally:
            await conn.close()
    
    async def _process_service_naming(self, service: Dict[str, Any]) -> NamingStandardResult:
        """Process naming standards for a single service"""
        service_name = service['service_name']
        source_type = service['source_type']
        migration_type = service.get('migration_type', '')
        suggested_target = service.get('suggested_target', '')
        
        violations = []
        
        # Validate current name
        violations.extend(self._validate_current_name(service, source_type))
        
        # Generate standardized name
        standardized_name = self._generate_standardized_name(service, source_type, migration_type)
        
        # Check if name needs changing
        name_changed = service_name != standardized_name
        
        if name_changed:
            violations.append(NamingViolation(
                service_id=service['id'],
                service_name=service_name,
                violation_type='naming_convention',
                current_name=service_name,
                suggested_name=standardized_name,
                severity='warning',
                rule=f'{source_type}_naming_pattern',
                reasoning=f'Name should follow {source_type} naming convention: {standardized_name}'
            ))
        
        # Calculate confidence
        confidence = self._calculate_naming_confidence(service, violations)
        
        return NamingStandardResult(
            service_id=service['id'],
            original_name=service_name,
            standardized_name=standardized_name,
            name_changed=name_changed,
            violations=violations,
            confidence=confidence
        )
    
    def _validate_current_name(self, service: Dict[str, Any], source_type: str) -> List[NamingViolation]:
        """Validate current service name against standards"""
        violations = []
        service_name = service['service_name']
        service_id = service['id']
        
        # Check forbidden patterns
        for forbidden_pattern in self.naming_rules["forbidden_patterns"]:
            if re.search(forbidden_pattern, service_name):
                violations.append(NamingViolation(
                    service_id=service_id,
                    service_name=service_name,
                    violation_type='forbidden_pattern',
                    current_name=service_name,
                    suggested_name='',
                    severity='error',
                    rule=f'forbidden_pattern_{forbidden_pattern}',
                    reasoning=f'Name violates forbidden pattern: {forbidden_pattern}'
                ))
        
        # Check required patterns for type
        type_map = {
            'client': 'component',
            'utility': 'utility', 
            'service': 'service',
            'manager': 'context'
        }
        
        pattern_type = type_map.get(source_type, 'service')
        if pattern_type in self.naming_rules["required_patterns"]:
            required_pattern = self.naming_rules["required_patterns"][pattern_type]
            if not re.match(required_pattern, service_name):
                violations.append(NamingViolation(
                    service_id=service_id,
                    service_name=service_name,
                    violation_type='pattern_mismatch',
                    current_name=service_name,
                    suggested_name='',
                    severity='warning',
                    rule=f'required_pattern_{pattern_type}',
                    reasoning=f'Name should match pattern: {required_pattern}'
                ))
        
        return violations
    
    def _generate_standardized_name(self, service: Dict[str, Any], source_type: str, migration_type: str) -> str:
        """Generate standardized name based on type and migration strategy"""
        service_name = service['service_name']
        suggested_target = service.get('suggested_target', '')
        
        # If service is being consolidated, use target name
        if migration_type == 'CONSOLIDATION' and suggested_target:
            return suggested_target
        
        # Clean and standardize current name
        clean_name = self._clean_service_name(service_name)
        
        # Apply type-specific naming patterns
        type_patterns = {
            'client': self._apply_component_pattern,
            'utility': self._apply_utility_pattern,
            'service': self._apply_service_pattern,
            'manager': self._apply_context_pattern
        }
        
        pattern_func = type_patterns.get(source_type, self._apply_service_pattern)
        standardized = pattern_func(clean_name, service)
        
        return standardized
    
    def _clean_service_name(self, name: str) -> str:
        """Clean service name of common issues"""
        # Remove underscores and convert to PascalCase
        if '_' in name:
            parts = name.split('_')
            name = ''.join(part.capitalize() for part in parts)
        
        # Ensure proper capitalization
        if name and name[0].islower():
            name = name[0].upper() + name[1:]
        
        # Remove trailing numbers
        name = re.sub(r'\d+$', '', name)
        
        # Truncate if too long
        if len(name) > 35:  # Leave room for suffix
            name = name[:35]
        
        return name
    
    def _apply_component_pattern(self, clean_name: str, service: Dict[str, Any]) -> str:
        """Apply component naming pattern"""
        if not clean_name.endswith('Component') and not clean_name.endswith('Context'):
            # Determine if it's a context or component
            file_path = service.get('file_path', '')
            if 'context' in file_path.lower():
                return f"{clean_name}Context"
            else:
                return f"{clean_name}Component"
        return clean_name
    
    def _apply_utility_pattern(self, clean_name: str, service: Dict[str, Any]) -> str:
        """Apply utility naming pattern"""
        # Check if it's a hook
        if clean_name.startswith('use') and len(clean_name) > 3 and clean_name[3].isupper():
            return clean_name  # Already proper hook name
        elif 'hook' in service.get('file_path', '').lower():
            # Convert to hook pattern
            if not clean_name.startswith('use'):
                return f"use{clean_name}"
        else:
            # Regular utility
            if not clean_name.endswith('Utils') and not clean_name.endswith('Util'):
                return f"{clean_name}Utils"
        
        return clean_name
    
    def _apply_service_pattern(self, clean_name: str, service: Dict[str, Any]) -> str:
        """Apply service naming pattern"""
        if not clean_name.endswith('Service'):
            return f"{clean_name}Service"
        return clean_name
    
    def _apply_context_pattern(self, clean_name: str, service: Dict[str, Any]) -> str:
        """Apply context naming pattern"""
        if not clean_name.endswith('Context'):
            return f"{clean_name}Context"
        return clean_name
    
    def _calculate_naming_confidence(self, service: Dict[str, Any], violations: List[NamingViolation]) -> float:
        """Calculate confidence in naming standards application"""
        base_confidence = 0.9
        
        # Reduce confidence for each violation
        error_violations = len([v for v in violations if v.severity == 'error'])
        warning_violations = len([v for v in violations if v.severity == 'warning'])
        
        confidence = base_confidence - (error_violations * 0.3) - (warning_violations * 0.1)
        
        return max(0.0, min(1.0, confidence))
    
    async def _store_naming_standard_result(self, result: NamingStandardResult) -> None:
        """Store naming standard result in database"""
        import asyncpg
        
        conn = await asyncpg.connect("postgresql://admin:chooters@db:5432/arkyvus_db")
        try:
            # Store in migration_naming_standards table
            await conn.execute("""
                INSERT INTO migration_naming_standards 
                (service_id, original_name, standardized_name, pattern_type, 
                 naming_rules, validation_status, confidence_score, violations_count, created_at)
                VALUES ($1, $2, $3, 'frontend_service', $4, $5, $6, $7, CURRENT_TIMESTAMP)
                ON CONFLICT (service_id) DO UPDATE SET
                    original_name = EXCLUDED.original_name,
                    standardized_name = EXCLUDED.standardized_name,
                    naming_rules = EXCLUDED.naming_rules,
                    validation_status = EXCLUDED.validation_status,
                    confidence_score = EXCLUDED.confidence_score,
                    violations_count = EXCLUDED.violations_count,
                    updated_at = CURRENT_TIMESTAMP
            """, 
            result.service_id,
            result.original_name,
            result.standardized_name,
            json.dumps({
                'violations': [
                    {
                        'type': v.violation_type,
                        'severity': v.severity,
                        'rule': v.rule,
                        'reasoning': v.reasoning,
                        'current': v.current_name,
                        'suggested': v.suggested_name
                    } for v in result.violations
                ],
                'name_changed': result.name_changed
            }),
            'valid' if len([v for v in result.violations if v.severity == 'error']) == 0 else 'invalid',
            result.confidence,
            len(result.violations)
            )
            
        finally:
            await conn.close()
    
    def _generate_naming_summary(self, results: List[NamingStandardResult]) -> Dict[str, Any]:
        """Generate summary of naming standards processing"""
        if not results:
            return {}
        
        total_services = len(results)
        names_changed = len([r for r in results if r.name_changed])
        total_violations = sum(len(r.violations) for r in results)
        avg_confidence = sum(r.confidence for r in results) / total_services
        
        violation_types = {}
        for result in results:
            for violation in result.violations:
                violation_types[violation.violation_type] = violation_types.get(violation.violation_type, 0) + 1
        
        return {
            'total_services': total_services,
            'names_changed': names_changed,
            'names_unchanged': total_services - names_changed,
            'change_percentage': round((names_changed / total_services) * 100, 1),
            'total_violations': total_violations,
            'average_confidence': round(avg_confidence, 3),
            'violation_types': violation_types,
            'standardization_targets': {
                'components': len([r for r in results if 'Component' in r.standardized_name]),
                'services': len([r for r in results if 'Service' in r.standardized_name]),
                'hooks': len([r for r in results if r.standardized_name.startswith('use')]),
                'contexts': len([r for r in results if 'Context' in r.standardized_name]),
                'utilities': len([r for r in results if 'Utils' in r.standardized_name])
            }
        }

async def main():
    """Main execution function for testing"""
    engine = FrontendNamingStandardsEngine()
    results = await engine.process_all_frontend_services()
    
    print(f"🎯 Frontend Naming Standards Complete!")
    print(f"📊 Processed {len(results)} frontend services")
    
    for result in results[:10]:  # Show first 10
        status = "✅" if not result.name_changed else "🔄"
        print(f"{status} {result.original_name} -> {result.standardized_name}")
        if result.violations:
            for violation in result.violations[:2]:  # Show first 2 violations
                print(f"    ⚠️  {violation.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())