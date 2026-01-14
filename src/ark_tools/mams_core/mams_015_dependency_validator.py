#!/usr/bin/env python3
"""
MAMS-015: Frontend Dependency Graph Validator
Production-safe dependency validation with cycle detection and domain boundary enforcement
"""

import os
import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import asyncio

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from arkyvus.utils.debug_logger import debug_log
from arkyvus.migrations.mams_014_enhanced_frontend_analyzer import DomainOntology

@dataclass
class DependencyEdge:
    """Represents a dependency between two files"""
    source: str
    target: str
    import_path: str
    is_type_only: bool
    is_dynamic: bool
    line_number: int

@dataclass
class DomainBoundaryViolation:
    """Represents a domain boundary violation"""
    source_file: str
    target_file: str
    source_domain: str
    target_domain: str
    violation_type: str  # 'forbidden', 'not_allowed', 'circular'
    severity: str  # 'error', 'warning'
    description: str
    suggested_fix: Optional[str] = None

@dataclass
class CyclicDependency:
    """Represents a circular dependency"""
    cycle_path: List[str]
    involves_domains: Set[str]
    severity: str  # 'error', 'warning'
    description: str

@dataclass
class PublicSurfaceViolation:
    """Represents a public API surface violation"""
    file_path: str
    violation_type: str  # 'breaking_change', 'unstable_export', 'missing_type'
    current_export: str
    expected_export: Optional[str]
    consumers: List[str]
    description: str

@dataclass
class ValidationReport:
    """Complete validation report for frontend dependencies"""
    is_valid: bool
    total_files: int
    total_dependencies: int
    domain_violations: List[DomainBoundaryViolation]
    cyclic_dependencies: List[CyclicDependency]
    public_surface_violations: List[PublicSurfaceViolation]
    orphaned_files: List[str]
    statistics: Dict[str, Any]
    can_proceed_with_warnings: bool
    timestamp: str

@dataclass
class MigrationMove:
    """Represents a file migration move"""
    from_path: str
    to_path: str
    from_domain: str
    to_domain: str
    dependencies_in: List[str]
    dependencies_out: List[str]


class FrontendDependencyValidator:
    """
    Validates frontend dependency graph for safe migration
    Ensures domain boundaries, prevents cycles, and maintains public contracts
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.ontology = DomainOntology()
        self.domain_map: Dict[str, str] = {}  # file -> domain mapping
        self.public_exports: Dict[str, Set[str]] = {}  # file -> public exports
        self.file_contents_cache: Dict[str, str] = {}
        
    async def build_dependency_graph(self, classifications: List[Any]) -> nx.DiGraph:
        """
        Build comprehensive dependency graph from classifications
        """
        debug_log.api("Building dependency graph", level="INFO")
        
        # Reset graph
        self.graph.clear()
        
        # Add nodes with domain information
        for classification in classifications:
            file_path = classification.file_path
            domain = classification.primary_domain
            
            self.graph.add_node(file_path, domain=domain, 
                              confidence=classification.confidence,
                              requires_review=classification.requires_review)
            self.domain_map[file_path] = domain
            
            # Add edges from dependencies
            for dep in classification.dependencies:
                # Resolve dependency to actual file path
                resolved_path = await self._resolve_import_to_file(dep, file_path)
                if resolved_path and resolved_path != file_path:
                    self.graph.add_edge(file_path, resolved_path, 
                                      import_path=dep,
                                      is_type_only=self._is_type_import(dep))
        
        # Analyze graph properties
        debug_log.api(f"Graph built: {self.graph.number_of_nodes()} nodes, "
                     f"{self.graph.number_of_edges()} edges", level="INFO")
        
        return self.graph
    
    async def _resolve_import_to_file(self, import_path: str, from_file: str) -> Optional[str]:
        """Resolve an import path to an actual file path"""
        # Handle different import styles
        if import_path.startswith('.'):
            # Relative import
            return self._resolve_relative_import(import_path, from_file)
        elif import_path.startswith('@/'):
            # Alias import
            return self._resolve_alias_import(import_path)
        elif not import_path.startswith('.') and '/' in import_path:
            # Package import
            return self._resolve_package_import(import_path)
        
        return None
    
    def _resolve_relative_import(self, import_path: str, from_file: str) -> Optional[str]:
        """Resolve relative import path"""
        from_dir = Path(from_file).parent
        
        # Navigate relative path
        parts = import_path.split('/')
        current = from_dir
        
        for part in parts:
            if part == '.':
                continue
            elif part == '..':
                current = current.parent
            else:
                current = current / part
        
        # Try different extensions
        for ext in ['.tsx', '.ts', '.jsx', '.js', '/index.tsx', '/index.ts']:
            full_path = Path(str(current) + ext)
            if full_path.exists():
                return str(full_path)
        
        return None
    
    def _resolve_alias_import(self, import_path: str) -> Optional[str]:
        """Resolve alias import (e.g., @/components)"""
        # Remove @ prefix
        path = import_path[2:] if import_path.startswith('@/') else import_path[1:]
        
        # Try common alias mappings
        base_dirs = [
            '/app/client/src',
            '/Users/pregenie/Development/arkyvus_project/client/src',
            './client/src'
        ]
        
        for base in base_dirs:
            for ext in ['', '.tsx', '.ts', '.jsx', '.js', '/index.tsx', '/index.ts']:
                full_path = Path(base) / path
                if ext:
                    full_path = Path(str(full_path) + ext)
                if full_path.exists():
                    return str(full_path)
        
        return None
    
    def _resolve_package_import(self, import_path: str) -> Optional[str]:
        """Resolve package import"""
        # For external packages, return None (not part of our codebase)
        if import_path.startswith('node_modules/') or not import_path.startswith('.'):
            return None
        
        # For internal packages, try to resolve
        return self._resolve_alias_import('@/' + import_path)
    
    def _is_type_import(self, import_path: str) -> bool:
        """Check if import is type-only"""
        # This is simplified - in real implementation would check AST
        return 'types' in import_path or 'interface' in import_path
    
    def validate_current_state(self) -> ValidationReport:
        """
        Validate current state of the dependency graph
        """
        debug_log.api("Validating current dependency state", level="INFO")
        
        domain_violations = self._check_domain_boundaries()
        cycles = self._detect_cycles()
        public_violations = self._check_public_surface()
        orphans = self._find_orphaned_files()
        
        # Calculate statistics
        stats = self._calculate_statistics()
        
        # Determine if valid
        error_violations = [v for v in domain_violations if v.severity == 'error']
        error_cycles = [c for c in cycles if c.severity == 'error']
        is_valid = len(error_violations) == 0 and len(error_cycles) == 0
        
        # Can proceed with warnings?
        warning_count = len([v for v in domain_violations if v.severity == 'warning'])
        can_proceed = is_valid or (warning_count < 10 and len(error_violations) < 5)
        
        return ValidationReport(
            is_valid=is_valid,
            total_files=self.graph.number_of_nodes(),
            total_dependencies=self.graph.number_of_edges(),
            domain_violations=domain_violations,
            cyclic_dependencies=cycles,
            public_surface_violations=public_violations,
            orphaned_files=orphans,
            statistics=stats,
            can_proceed_with_warnings=can_proceed,
            timestamp=datetime.now().isoformat()
        )
    
    def _check_domain_boundaries(self) -> List[DomainBoundaryViolation]:
        """Check for domain boundary violations"""
        violations = []
        
        for source, target in self.graph.edges():
            source_domain = self.domain_map.get(source, 'unknown')
            target_domain = self.domain_map.get(target, 'unknown')
            
            # Get edge data
            edge_data = self.graph[source][target]
            is_type_only = edge_data.get('is_type_only', False)
            
            # Check if allowed
            violation = self._check_domain_import_allowed(
                source, target, source_domain, target_domain, is_type_only
            )
            
            if violation:
                violations.append(violation)
        
        return violations
    
    def _check_domain_import_allowed(self, source: str, target: str,
                                    source_domain: str, target_domain: str,
                                    is_type_only: bool) -> Optional[DomainBoundaryViolation]:
        """
        Check if import from source domain to target domain is allowed
        Fixed implementation addressing v3.1 critique
        """
        # Same domain is always allowed
        if source_domain == target_domain:
            return None
        
        # Shared and platform are always allowed targets
        if target_domain in ['shared', 'platform']:
            return None
        
        # Get source domain configuration
        source_config = self.ontology.domains.get(source_domain, {})
        allowed_deps = source_config.get('allowed_dependencies', {})
        
        # Check allowed domains
        allowed_domains = allowed_deps.get('domains', [])
        
        # Type-only imports have special rules
        if is_type_only:
            type_only_domains = allowed_deps.get('type_only_domains', [])
            # Type imports allowed to shared, platform, and specified type_only_domains
            if target_domain in ['shared', 'platform'] or target_domain in type_only_domains:
                return None
            else:
                # Type import to non-allowed domain is a warning
                return DomainBoundaryViolation(
                    source_file=source,
                    target_file=target,
                    source_domain=source_domain,
                    target_domain=target_domain,
                    violation_type='not_allowed',
                    severity='warning',
                    description=f"Type-only import from {source_domain} to {target_domain} should be reviewed",
                    suggested_fix=f"Consider moving type definitions to 'shared' domain"
                )
        
        # Regular imports
        if target_domain not in allowed_domains:
            # Check for capability-based exemptions
            # Fixed: Check if the SOURCE has the capability, not the target
            source_capabilities = self._get_file_capabilities(source)
            allowed_capabilities = allowed_deps.get('capabilities', [])
            
            for capability in source_capabilities:
                if capability in allowed_capabilities:
                    return None  # Capability exemption applies
            
            # Check forbidden imports
            forbidden = allowed_deps.get('forbidden_imports', [])
            if target_domain in forbidden:
                return DomainBoundaryViolation(
                    source_file=source,
                    target_file=target,
                    source_domain=source_domain,
                    target_domain=target_domain,
                    violation_type='forbidden',
                    severity='error',
                    description=f"Import from {source_domain} to {target_domain} is forbidden",
                    suggested_fix=f"Remove dependency or refactor to use allowed domains: {allowed_domains}"
                )
            
            # Not explicitly forbidden but not allowed
            return DomainBoundaryViolation(
                source_file=source,
                target_file=target,
                source_domain=source_domain,
                target_domain=target_domain,
                violation_type='not_allowed',
                severity='warning' if target_domain == 'misc' else 'error',
                description=f"Import from {source_domain} to {target_domain} violates domain boundaries",
                suggested_fix=f"Consider using one of allowed domains: {allowed_domains}"
            )
        
        return None
    
    def _get_file_capabilities(self, file_path: str) -> List[str]:
        """Get capabilities of a file based on its imports and content"""
        capabilities = []
        
        # Check what the file imports/uses
        for _, target in self.graph.edges(file_path):
            target_domain = self.domain_map.get(target, '')
            
            # Map domains to capabilities
            if target_domain == 'analytics' or 'analytics' in target:
                capabilities.append('analytics')
            elif target_domain == 'messaging' or 'message' in target:
                capabilities.append('messaging')
            elif target_domain == 'storage' or 'storage' in target:
                capabilities.append('storage')
            elif 'realtime' in target or 'websocket' in target:
                capabilities.append('realtime')
        
        return capabilities
    
    def _detect_cycles(self) -> List[CyclicDependency]:
        """Detect circular dependencies in the graph"""
        cycles = []
        
        try:
            # Find all simple cycles
            all_cycles = list(nx.simple_cycles(self.graph))
            
            for cycle in all_cycles:
                # Get involved domains
                domains = set()
                for node in cycle:
                    domain = self.domain_map.get(node, 'unknown')
                    domains.add(domain)
                
                # Determine severity
                # Cycles within same domain are warnings
                # Cross-domain cycles are errors
                severity = 'warning' if len(domains) == 1 else 'error'
                
                cycles.append(CyclicDependency(
                    cycle_path=cycle,
                    involves_domains=domains,
                    severity=severity,
                    description=f"Circular dependency involving {len(cycle)} files across {len(domains)} domain(s)"
                ))
                
        except Exception as e:
            debug_log.error_trace("Error detecting cycles", exception=e)
        
        return cycles
    
    def _check_public_surface(self) -> List[PublicSurfaceViolation]:
        """Check public API surface for violations"""
        violations = []
        
        # Identify public surface files
        public_patterns = [
            'index.ts', 'index.tsx',
            'public.ts', 'public.tsx',
            'api.ts', 'api.tsx'
        ]
        
        for node in self.graph.nodes():
            file_name = Path(node).name
            
            # Check if this is a public surface file
            is_public = any(pattern in file_name for pattern in public_patterns)
            
            # Also check if in a public directory
            if '/public/' in node or '/api/' in node:
                is_public = True
            
            if is_public:
                # Check for stable exports
                violation = self._check_stable_exports(node)
                if violation:
                    violations.append(violation)
        
        return violations
    
    def _check_stable_exports(self, file_path: str) -> Optional[PublicSurfaceViolation]:
        """Check if public file has stable exports"""
        # Get files that import from this public file
        importers = list(self.graph.predecessors(file_path))
        
        if len(importers) > 5:  # Widely used public API
            # Check if file has proper type exports
            # This is simplified - real implementation would check actual exports
            if 'types' not in file_path and '.d.ts' not in file_path:
                return PublicSurfaceViolation(
                    file_path=file_path,
                    violation_type='missing_type',
                    current_export='unknown',
                    expected_export='typed exports',
                    consumers=importers[:5],  # Show first 5
                    description=f"Public API used by {len(importers)} files lacks type definitions"
                )
        
        return None
    
    def _find_orphaned_files(self) -> List[str]:
        """Find files with no incoming or outgoing dependencies"""
        orphans = []
        
        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            
            # True orphans have no connections
            if in_degree == 0 and out_degree == 0:
                orphans.append(node)
        
        return orphans
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate graph statistics"""
        stats = {}
        
        # Basic metrics
        stats['total_nodes'] = self.graph.number_of_nodes()
        stats['total_edges'] = self.graph.number_of_edges()
        stats['average_degree'] = sum(dict(self.graph.degree()).values()) / max(stats['total_nodes'], 1)
        
        # Domain distribution
        domain_counts = defaultdict(int)
        for node, domain in self.domain_map.items():
            domain_counts[domain] += 1
        stats['domain_distribution'] = dict(domain_counts)
        
        # Connectivity metrics
        if stats['total_nodes'] > 0:
            largest_component = max(nx.weakly_connected_components(self.graph), key=len)
            stats['largest_component_size'] = len(largest_component)
            stats['component_count'] = nx.number_weakly_connected_components(self.graph)
        else:
            stats['largest_component_size'] = 0
            stats['component_count'] = 0
        
        # Find most connected nodes (hubs)
        degree_dict = dict(self.graph.degree())
        top_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        stats['hub_files'] = [{'file': node, 'connections': degree} for node, degree in top_nodes]
        
        return stats
    
    def validate_migration_plan(self, moves: List[MigrationMove]) -> ValidationReport:
        """
        Validate that a migration plan won't break dependencies
        """
        debug_log.api(f"Validating migration plan with {len(moves)} moves", level="INFO")
        
        # Clone graph for simulation
        temp_graph = self.graph.copy()
        temp_domain_map = self.domain_map.copy()
        
        violations = []
        
        for move in moves:
            # Simulate the move
            if move.from_path in temp_graph:
                # Update node
                old_data = temp_graph.nodes[move.from_path]
                temp_graph.remove_node(move.from_path)
                temp_graph.add_node(move.to_path, **old_data, domain=move.to_domain)
                
                # Update edges
                # Update incoming edges
                for pred in list(temp_graph.predecessors(move.from_path)):
                    edge_data = temp_graph[pred][move.from_path]
                    temp_graph.remove_edge(pred, move.from_path)
                    temp_graph.add_edge(pred, move.to_path, **edge_data)
                
                # Update outgoing edges
                for succ in list(temp_graph.successors(move.from_path)):
                    edge_data = temp_graph[move.from_path][succ]
                    temp_graph.remove_edge(move.from_path, succ)
                    temp_graph.add_edge(move.to_path, succ, **edge_data)
                
                # Update domain map
                temp_domain_map[move.to_path] = move.to_domain
                del temp_domain_map[move.from_path]
            
            # Check for violations after this move
            move_violations = self._check_move_violations(move, temp_graph, temp_domain_map)
            violations.extend(move_violations)
        
        # Check for cycles after all moves
        cycles = self._detect_cycles_in_graph(temp_graph, temp_domain_map)
        
        # Prepare report
        is_valid = len([v for v in violations if v.severity == 'error']) == 0
        
        return ValidationReport(
            is_valid=is_valid,
            total_files=temp_graph.number_of_nodes(),
            total_dependencies=temp_graph.number_of_edges(),
            domain_violations=violations,
            cyclic_dependencies=cycles,
            public_surface_violations=[],  # Not checking public surface for plan
            orphaned_files=[],
            statistics=self._calculate_statistics_for_graph(temp_graph),
            can_proceed_with_warnings=is_valid or len(violations) < 10,
            timestamp=datetime.now().isoformat()
        )
    
    def _check_move_violations(self, move: MigrationMove, graph: nx.DiGraph,
                              domain_map: Dict[str, str]) -> List[DomainBoundaryViolation]:
        """Check for violations introduced by a single move"""
        violations = []
        
        # Check all edges from/to the moved file
        moved_file = move.to_path
        
        # Check incoming dependencies
        for source in graph.predecessors(moved_file):
            source_domain = domain_map.get(source, 'unknown')
            violation = self._check_domain_import_allowed(
                source, moved_file, source_domain, move.to_domain, False
            )
            if violation:
                violations.append(violation)
        
        # Check outgoing dependencies
        for target in graph.successors(moved_file):
            target_domain = domain_map.get(target, 'unknown')
            violation = self._check_domain_import_allowed(
                moved_file, target, move.to_domain, target_domain, False
            )
            if violation:
                violations.append(violation)
        
        return violations
    
    def _detect_cycles_in_graph(self, graph: nx.DiGraph, 
                               domain_map: Dict[str, str]) -> List[CyclicDependency]:
        """Detect cycles in a specific graph"""
        cycles = []
        
        try:
            all_cycles = list(nx.simple_cycles(graph))
            
            for cycle in all_cycles:
                domains = set()
                for node in cycle:
                    domain = domain_map.get(node, 'unknown')
                    domains.add(domain)
                
                severity = 'warning' if len(domains) == 1 else 'error'
                
                cycles.append(CyclicDependency(
                    cycle_path=cycle,
                    involves_domains=domains,
                    severity=severity,
                    description=f"Circular dependency: {len(cycle)} files, {len(domains)} domains"
                ))
                
        except Exception as e:
            debug_log.error_trace("Error detecting cycles", exception=e)
        
        return cycles
    
    def _calculate_statistics_for_graph(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Calculate statistics for a specific graph"""
        return {
            'total_nodes': graph.number_of_nodes(),
            'total_edges': graph.number_of_edges(),
            'average_degree': sum(dict(graph.degree()).values()) / max(graph.number_of_nodes(), 1)
        }
    
    def suggest_fixes(self, violations: List[DomainBoundaryViolation]) -> List[Dict[str, Any]]:
        """Suggest fixes for violations"""
        fixes = []
        
        for violation in violations:
            if violation.violation_type == 'forbidden':
                fixes.append({
                    'violation': violation,
                    'fix_type': 'remove_dependency',
                    'description': f"Remove import from {violation.source_file} to {violation.target_file}",
                    'alternative': f"Use service from allowed domains: {self.ontology.domains[violation.source_domain].get('allowed_dependencies', {}).get('domains', [])}"
                })
            elif violation.violation_type == 'not_allowed':
                fixes.append({
                    'violation': violation,
                    'fix_type': 'refactor',
                    'description': f"Refactor {violation.source_file} to remove dependency on {violation.target_domain}",
                    'alternative': f"Consider moving shared code to 'shared' domain"
                })
            elif violation.violation_type == 'circular':
                fixes.append({
                    'violation': violation,
                    'fix_type': 'break_cycle',
                    'description': f"Break circular dependency between {violation.source_file} and {violation.target_file}",
                    'alternative': "Extract common code to a third module or use dependency injection"
                })
        
        return fixes


# Test functionality
if __name__ == "__main__":
    async def test_validator():
        validator = FrontendDependencyValidator()
        
        # Create mock classifications for testing
        mock_classifications = [
            type('Classification', (), {
                'file_path': '/app/client/src/components/auth/Login.tsx',
                'primary_domain': 'auth',
                'confidence': 0.9,
                'requires_review': False,
                'dependencies': ['@/services/auth', '@/components/ui/Button']
            })(),
            type('Classification', (), {
                'file_path': '/app/client/src/components/ui/Button.tsx',
                'primary_domain': 'ui',
                'confidence': 0.95,
                'requires_review': False,
                'dependencies': []
            })(),
            type('Classification', (), {
                'file_path': '/app/client/src/services/auth.ts',
                'primary_domain': 'auth',
                'confidence': 0.85,
                'requires_review': False,
                'dependencies': ['@/services/api']
            })()
        ]
        
        # Build graph
        graph = await validator.build_dependency_graph(mock_classifications)
        
        # Validate
        report = validator.validate_current_state()
        
        print(f"Validation Report")
        print(f"================")
        print(f"Valid: {report.is_valid}")
        print(f"Files: {report.total_files}")
        print(f"Dependencies: {report.total_dependencies}")
        print(f"Domain Violations: {len(report.domain_violations)}")
        print(f"Cycles: {len(report.cyclic_dependencies)}")
        print(f"Orphaned Files: {len(report.orphaned_files)}")
        print(f"Can Proceed: {report.can_proceed_with_warnings}")
        
        if report.domain_violations:
            print("\nDomain Violations:")
            for v in report.domain_violations[:3]:
                print(f"  - {v.description}")
        
        print(f"\nStatistics:")
        for key, value in report.statistics.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
    
    # Run test
    asyncio.run(test_validator())