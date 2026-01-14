#!/usr/bin/env python3
"""
MAMS-004: Standalone Naming Standards Engine Test
"""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass 
class NamingTransformation:
    original_name: str
    suggested_name: str
    transformation_type: str
    applied_rule: str
    confidence: float
    reason: str
    validation_passed: bool = False


class SimpleNamingEngine:
    """Simplified naming standards engine for testing"""
    
    def transform_service_name(self, original_name: str, service_type: str = None) -> NamingTransformation:
        """Transform service name to standard format"""
        
        # Extract domain from name
        domain = re.sub(r'(Service|Manager|Handler|Repository|Client|Gateway)$', '', original_name)
        domain = re.sub(r'^(Core|Unified|Base)', '', domain)
        domain = domain[0].upper() + domain[1:] if domain else 'Unknown'
        
        # Determine pattern based on type and name
        if 'Cache' in original_name or 'Pool' in original_name or 'Session' in original_name:
            suggested_name = f"Core{domain}Service"
            pattern_type = 'CORE_SERVICE'
        elif 'Client' in original_name or 'Gateway' in original_name:
            suggested_name = f"{domain}Client"
            pattern_type = 'CLIENT_SERVICE'
        elif 'Repository' in original_name:
            suggested_name = f"Unified{domain}Repository" 
            pattern_type = 'UNIFIED_REPOSITORY'
        else:
            suggested_name = f"Unified{domain}Service"
            pattern_type = 'UNIFIED_SERVICE'
        
        return NamingTransformation(
            original_name=original_name,
            suggested_name=suggested_name,
            transformation_type=pattern_type,
            applied_rule=f"SERVICE_{pattern_type}",
            confidence=0.9,
            reason=f"Applied {pattern_type} naming pattern",
            validation_passed=True
        )
    
    def transform_method_name(self, original_name: str) -> NamingTransformation:
        """Transform method name to standard format"""
        
        # Detect CRUD patterns
        if re.search(r'(create|add|new|insert)', original_name, re.IGNORECASE):
            entity = self._extract_entity(original_name)
            suggested_name = f"create_{entity}"
            pattern_type = 'CRUD_CREATE'
        elif re.search(r'(get|find|fetch|retrieve)', original_name, re.IGNORECASE):
            entity = self._extract_entity(original_name)
            suggested_name = f"get_{entity}"
            pattern_type = 'CRUD_READ'
        elif re.search(r'(update|modify|edit)', original_name, re.IGNORECASE):
            entity = self._extract_entity(original_name)
            suggested_name = f"update_{entity}"
            pattern_type = 'CRUD_UPDATE'
        elif re.search(r'(delete|remove)', original_name, re.IGNORECASE):
            entity = self._extract_entity(original_name)
            suggested_name = f"delete_{entity}"
            pattern_type = 'CRUD_DELETE'
        else:
            # Convert to snake_case
            suggested_name = re.sub(r'([a-z])([A-Z])', r'\1_\2', original_name).lower()
            pattern_type = 'SNAKE_CASE'
        
        return NamingTransformation(
            original_name=original_name,
            suggested_name=suggested_name,
            transformation_type=pattern_type,
            applied_rule=f"METHOD_{pattern_type}",
            confidence=0.85,
            reason=f"Applied {pattern_type} naming pattern",
            validation_passed=True
        )
    
    def transform_endpoint_path(self, original_path: str) -> NamingTransformation:
        """Transform endpoint path to REST standards"""
        
        # Add versioning if missing
        if not '/api/v' in original_path:
            if original_path.startswith('/api/'):
                suggested_path = original_path.replace('/api/', '/api/v2/')
            else:
                suggested_path = f"/api/v2{original_path}"
            pattern_type = 'VERSIONED'
        else:
            suggested_path = original_path
            pattern_type = 'ALREADY_VERSIONED'
        
        return NamingTransformation(
            original_name=original_path,
            suggested_name=suggested_path,
            transformation_type=pattern_type,
            applied_rule=f"ENDPOINT_{pattern_type}",
            confidence=0.8,
            reason=f"Applied {pattern_type} endpoint pattern",
            validation_passed=True
        )
    
    def _extract_entity(self, method_name: str) -> str:
        """Extract entity name from method"""
        # Remove common prefixes
        clean_name = re.sub(r'^(create|get|find|update|delete|list|add|new|insert|fetch|retrieve|modify|edit|remove)', '', method_name, flags=re.IGNORECASE)
        
        # Extract first word
        words = re.findall(r'[A-Z][a-z]*', clean_name)
        if words:
            return words[0].lower()
        return 'item'


def test_naming_engine():
    """Test the naming engine with sample data"""
    
    print("MAMS-004: Naming Standards Engine Test")
    print("=" * 50)
    
    engine = SimpleNamingEngine()
    
    # Test services
    test_services = [
        ('AuthService', 'SERVICE'),
        ('CacheManager', 'MANAGER'),
        ('PaymentGateway', 'CLIENT'),
        ('UserRepository', 'REPOSITORY'),
        ('SessionHandler', 'HANDLER')
    ]
    
    print("Service Name Transformations:")
    print("-" * 30)
    for service_name, service_type in test_services:
        transform = engine.transform_service_name(service_name, service_type)
        print(f"  {transform.original_name} → {transform.suggested_name}")
        print(f"    Rule: {transform.applied_rule}, Confidence: {transform.confidence}")
    
    # Test methods
    test_methods = [
        'login', 'logout', 'createUser', 'getUserById', 'updateProfile',
        'deleteAccount', 'findUserByEmail', 'processPayment', 'validateInput'
    ]
    
    print("\nMethod Name Transformations:")
    print("-" * 30)
    for method_name in test_methods:
        transform = engine.transform_method_name(method_name)
        print(f"  {transform.original_name} → {transform.suggested_name}")
        print(f"    Rule: {transform.applied_rule}")
    
    # Test endpoints
    test_endpoints = [
        '/api/users/{id}',
        '/users',
        '/auth/login',
        '/api/v1/payments',
        '/admin/reports'
    ]
    
    print("\nEndpoint Path Transformations:")
    print("-" * 30)
    for endpoint_path in test_endpoints:
        transform = engine.transform_endpoint_path(endpoint_path)
        print(f"  {transform.original_name} → {transform.suggested_name}")
        print(f"    Rule: {transform.applied_rule}")
    
    print("\n✅ MAMS-004 Naming Standards Engine Test Complete")
    
    # Summary statistics
    service_transforms = [engine.transform_service_name(s[0], s[1]) for s in test_services]
    method_transforms = [engine.transform_method_name(m) for m in test_methods]
    endpoint_transforms = [engine.transform_endpoint_path(e) for e in test_endpoints]
    
    all_transforms = service_transforms + method_transforms + endpoint_transforms
    avg_confidence = sum(t.confidence for t in all_transforms) / len(all_transforms)
    
    print(f"\nSummary:")
    print(f"  Total Transformations: {len(all_transforms)}")
    print(f"  Average Confidence: {avg_confidence:.3f}")
    print(f"  Services Transformed: {len(service_transforms)}")
    print(f"  Methods Transformed: {len(method_transforms)}")
    print(f"  Endpoints Transformed: {len(endpoint_transforms)}")


if __name__ == "__main__":
    test_naming_engine()