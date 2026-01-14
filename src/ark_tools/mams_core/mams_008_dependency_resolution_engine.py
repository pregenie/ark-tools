#!/usr/bin/env python3
"""
MAMS-008: Dependency Resolution Engine with Auto-Discovery
Auto-discovering dependency resolution with continuous monitoring
"""

import asyncio
import ast
import json
import re
import sys
import uuid
import networkx as nx
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class DependencyType(Enum):
    IMPORT = "import"
    CALL = "call" 
    INHERIT = "inherit"
    COMPOSE = "compose"
    INJECT = "inject"
    CONFIG = "config"
    EVENT = "event"
    DATABASE = "database"

class ServiceEvolution(Enum):
    CREATED = "created"
    RENAMED = "renamed"
    MOVED = "moved"
    SPLIT = "split"
    MERGED = "merged"
    DELETED = "deleted"

class DetectionMethod(Enum):
    AST = "ast"
    RUNTIME = "runtime"
    ANNOTATION = "annotation"
    CONFIG_FILE = "config_file"
    PATTERN_MATCH = "pattern_match"

@dataclass
class DiscoveryPattern:
    """Pattern for discovering services automatically"""
    pattern_id: str
    pattern_type: str  # service, method, dependency
    language: str  # python, typescript, sql
    pattern: str  # regex or glob pattern
    classification: str
    confidence_weight: float = 1.0
    active: bool = True
    auto_learned: bool = False
    match_count: int = 0
    last_matched: Optional[datetime] = None

@dataclass
class DiscoveredService:
    """A service discovered through auto-discovery"""
    service_id: str
    service_identifier: str
    discovery_timestamp: datetime
    discovery_source: str  # scan, watch, manual, import
    file_path: str
    service_type: str
    confidence_score: float
    auto_classified: bool = True
    manual_override: Optional[Dict] = None
    registered: bool = False
    contract_id: Optional[str] = None
    migration_status: str = "new"
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    is_active: bool = True

@dataclass
class DynamicDependency:
    """A dependency relationship between services"""
    dependency_id: str
    source_service_id: str
    target_service_id: str
    dependency_type: DependencyType
    detection_method: DetectionMethod
    metadata: Dict[str, Any] = field(default_factory=dict)
    first_detected: datetime = field(default_factory=datetime.now)
    last_confirmed: Optional[datetime] = None
    confidence: float = 1.0
    is_active: bool = True

class PatternLearner:
    """Learns new patterns from successful discoveries"""
    
    def __init__(self):
        self.patterns: List[DiscoveryPattern] = []
        self.pattern_history: List[Dict] = []
    
    def add_default_patterns(self):
        """Add default discovery patterns"""
        default_patterns = [
            # Python service patterns
            DiscoveryPattern("PY_SERVICE_1", "service", "python", r"class\s+\w*Service\s*\(", "service"),
            DiscoveryPattern("PY_SERVICE_2", "service", "python", r"class\s+\w*Manager\s*\(", "manager"),
            DiscoveryPattern("PY_SERVICE_3", "service", "python", r"class\s+\w*Handler\s*\(", "handler"),
            DiscoveryPattern("PY_SERVICE_4", "service", "python", r"class\s+\w*Repository\s*\(", "repository"),
            DiscoveryPattern("PY_SERVICE_5", "service", "python", r"class\s+\w*Client\s*\(", "client"),
            DiscoveryPattern("PY_SERVICE_6", "service", "python", r"@service_registry\.register", "service"),
            DiscoveryPattern("PY_SERVICE_7", "service", "python", r"@injectable", "injectable"),
            
            # TypeScript service patterns
            DiscoveryPattern("TS_SERVICE_1", "service", "typescript", r"export\s+class\s+\w*Service", "service"),
            DiscoveryPattern("TS_SERVICE_2", "service", "typescript", r"export\s+const\s+use\w+", "hook"),
            DiscoveryPattern("TS_SERVICE_3", "service", "typescript", r"@Injectable\(\)", "injectable"),
            DiscoveryPattern("TS_SERVICE_4", "service", "typescript", r"export\s+function\s+\w*API", "api_function"),
            
            # Dependency patterns
            DiscoveryPattern("DEP_IMPORT_1", "dependency", "python", r"from\s+[\w\.]+\s+import\s+\w+", "import"),
            DiscoveryPattern("DEP_IMPORT_2", "dependency", "python", r"import\s+[\w\.]+", "import"),
            DiscoveryPattern("DEP_CALL_1", "dependency", "python", r"\w+\.\w+\s*\(", "call"),
            DiscoveryPattern("DEP_INHERIT_1", "dependency", "python", r"class\s+\w+\s*\(\s*\w+", "inherit")
        ]
        
        self.patterns.extend(default_patterns)
    
    def learn_from_discovery(self, file_content: str, discovered_services: List[DiscoveredService]):
        """Learn patterns from successful discoveries"""
        lines = file_content.split('\n')
        
        for service in discovered_services:
            if service.confidence_score > 0.8:  # Only learn from high-confidence discoveries
                # Find the line containing the service definition
                for line_num, line in enumerate(lines):
                    if service.service_identifier.split('.')[-1] in line:
                        # Extract potential pattern
                        pattern = self._extract_pattern(line)
                        if pattern and not self._pattern_exists(pattern):
                            new_pattern = DiscoveryPattern(
                                pattern_id=str(uuid.uuid4()),
                                pattern_type="service",
                                language="python",
                                pattern=pattern,
                                classification=service.service_type,
                                confidence_weight=service.confidence_score,
                                auto_learned=True
                            )
                            self.patterns.append(new_pattern)
                        break
    
    def _extract_pattern(self, line: str) -> Optional[str]:
        """Extract a regex pattern from a line of code"""
        # Simple pattern extraction - could be made more sophisticated
        if 'class' in line:
            return r"class\s+" + re.escape(line.split('class')[1].split('(')[0].strip()) + r"\s*\("
        return None
    
    def _pattern_exists(self, pattern: str) -> bool:
        """Check if pattern already exists"""
        return any(p.pattern == pattern for p in self.patterns)

class ServiceDiscoverer:
    """Discovers services using patterns"""
    
    def __init__(self, pattern_learner: PatternLearner):
        self.pattern_learner = pattern_learner
        self.discovered_services: Dict[str, DiscoveredService] = {}
    
    def discover_in_file(self, file_path: str, content: str) -> List[DiscoveredService]:
        """Discover services in a single file"""
        discoveries = []
        
        # Try AST parsing first
        try:
            tree = ast.parse(content)
            ast_discoveries = self._discover_with_ast(file_path, tree, content)
            discoveries.extend(ast_discoveries)
        except SyntaxError:
            # Fall back to pattern matching
            pattern_discoveries = self._discover_with_patterns(file_path, content)
            discoveries.extend(pattern_discoveries)
        
        return discoveries
    
    def _discover_with_ast(self, file_path: str, tree: ast.AST, content: str) -> List[DiscoveredService]:
        """Discover services using AST analysis"""
        discoveries = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Analyze class to determine if it's a service
                service_type = self._classify_class(node)
                if service_type:
                    service = DiscoveredService(
                        service_id=str(uuid.uuid4()),
                        service_identifier=f"{file_path}.{node.name}",
                        discovery_timestamp=datetime.now(),
                        discovery_source="scan",
                        file_path=file_path,
                        service_type=service_type,
                        confidence_score=0.9
                    )
                    discoveries.append(service)
                    self.discovered_services[service.service_identifier] = service
        
        return discoveries
    
    def _discover_with_patterns(self, file_path: str, content: str) -> List[DiscoveredService]:
        """Discover services using pattern matching"""
        discoveries = []
        
        for pattern in self.pattern_learner.patterns:
            if not pattern.active or pattern.pattern_type != "service":
                continue
                
            matches = re.finditer(pattern.pattern, content, re.MULTILINE)
            for match in matches:
                # Extract service name from match
                service_name = self._extract_service_name(match.group(), pattern)
                if service_name:
                    service = DiscoveredService(
                        service_id=str(uuid.uuid4()),
                        service_identifier=f"{file_path}.{service_name}",
                        discovery_timestamp=datetime.now(),
                        discovery_source="scan",
                        file_path=file_path,
                        service_type=pattern.classification,
                        confidence_score=pattern.confidence_weight * 0.8  # Pattern-based has lower confidence
                    )
                    discoveries.append(service)
                    self.discovered_services[service.service_identifier] = service
                    
                    # Update pattern statistics
                    pattern.match_count += 1
                    pattern.last_matched = datetime.now()
        
        return discoveries
    
    def _classify_class(self, node: ast.ClassDef) -> Optional[str]:
        """Classify a class as a service type"""
        name = node.name.lower()
        
        # Check name patterns
        if 'service' in name:
            return 'service'
        elif 'manager' in name:
            return 'manager'
        elif 'handler' in name:
            return 'handler'
        elif 'repository' in name:
            return 'repository'
        elif 'client' in name:
            return 'client'
        elif 'controller' in name:
            return 'controller'
        
        # Check base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id.lower()
                if any(keyword in base_name for keyword in ['service', 'base', 'abstract']):
                    return 'service'
        
        # Check decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in ['injectable', 'service']:
                return 'service'
        
        return None
    
    def _extract_service_name(self, match_text: str, pattern: DiscoveryPattern) -> Optional[str]:
        """Extract service name from matched text"""
        if 'class' in match_text:
            # Extract class name
            parts = match_text.split()
            for i, part in enumerate(parts):
                if part == 'class' and i + 1 < len(parts):
                    class_name = parts[i + 1].split('(')[0]
                    return class_name
        
        return None

class DependencyAnalyzer:
    """Analyzes dependencies between services"""
    
    def __init__(self):
        self.dependencies: Dict[str, DynamicDependency] = {}
        self.dependency_graph = nx.DiGraph()
    
    def analyze_dependencies(self, services: Dict[str, DiscoveredService]) -> List[DynamicDependency]:
        """Analyze dependencies between services"""
        dependencies = []
        
        for service in services.values():
            try:
                with open(service.file_path, 'r') as f:
                    content = f.read()
                    
                # Analyze imports
                import_deps = self._analyze_imports(service, content)
                dependencies.extend(import_deps)
                
                # Analyze method calls
                call_deps = self._analyze_calls(service, content)
                dependencies.extend(call_deps)
                
                # Analyze inheritance
                inherit_deps = self._analyze_inheritance(service, content)
                dependencies.extend(inherit_deps)
                
            except Exception as e:
                print(f"Error analyzing dependencies for {service.service_identifier}: {e}")
        
        # Build dependency graph
        self._build_dependency_graph(dependencies)
        
        return dependencies
    
    def _analyze_imports(self, service: DiscoveredService, content: str) -> List[DynamicDependency]:
        """Analyze import dependencies"""
        dependencies = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    # Check if import is from another service
                    imported_service = self._resolve_import_to_service(node.module, node.names)
                    if imported_service:
                        dependency = DynamicDependency(
                            dependency_id=str(uuid.uuid4()),
                            source_service_id=service.service_id,
                            target_service_id=imported_service,
                            dependency_type=DependencyType.IMPORT,
                            detection_method=DetectionMethod.AST,
                            metadata={
                                'module': node.module,
                                'names': [alias.name for alias in node.names],
                                'line': node.lineno
                            }
                        )
                        dependencies.append(dependency)
                        
        except SyntaxError:
            # Fall back to text parsing
            import_deps = self._analyze_imports_text(service, content)
            dependencies.extend(import_deps)
        
        return dependencies
    
    def _analyze_calls(self, service: DiscoveredService, content: str) -> List[DynamicDependency]:
        """Analyze method call dependencies"""
        dependencies = []
        
        # Simple pattern matching for method calls
        call_pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.finditer(call_pattern, content)
        
        for match in matches:
            obj_name = match.group(1)
            method_name = match.group(2)
            
            # Try to resolve to a service
            target_service = self._resolve_call_to_service(obj_name, method_name)
            if target_service:
                dependency = DynamicDependency(
                    dependency_id=str(uuid.uuid4()),
                    source_service_id=service.service_id,
                    target_service_id=target_service,
                    dependency_type=DependencyType.CALL,
                    detection_method=DetectionMethod.PATTERN_MATCH,
                    metadata={
                        'object': obj_name,
                        'method': method_name,
                        'line': content[:match.start()].count('\n') + 1
                    }
                )
                dependencies.append(dependency)
        
        return dependencies
    
    def _analyze_inheritance(self, service: DiscoveredService, content: str) -> List[DynamicDependency]:
        """Analyze inheritance dependencies"""
        dependencies = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            # Try to resolve base class to a service
                            base_service = self._resolve_class_to_service(base.id)
                            if base_service:
                                dependency = DynamicDependency(
                                    dependency_id=str(uuid.uuid4()),
                                    source_service_id=service.service_id,
                                    target_service_id=base_service,
                                    dependency_type=DependencyType.INHERIT,
                                    detection_method=DetectionMethod.AST,
                                    metadata={
                                        'base_class': base.id,
                                        'child_class': node.name,
                                        'line': node.lineno
                                    }
                                )
                                dependencies.append(dependency)
        except SyntaxError:
            pass
        
        return dependencies
    
    def _analyze_imports_text(self, service: DiscoveredService, content: str) -> List[DynamicDependency]:
        """Analyze imports using text parsing"""
        dependencies = []
        
        import_patterns = [
            r'from\s+([\w\.]+)\s+import\s+([\w,\s]+)',
            r'import\s+([\w\.]+)'
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                module = match.group(1)
                target_service = self._resolve_module_to_service(module)
                if target_service:
                    dependency = DynamicDependency(
                        dependency_id=str(uuid.uuid4()),
                        source_service_id=service.service_id,
                        target_service_id=target_service,
                        dependency_type=DependencyType.IMPORT,
                        detection_method=DetectionMethod.PATTERN_MATCH,
                        metadata={'module': module, 'line': content[:match.start()].count('\n') + 1}
                    )
                    dependencies.append(dependency)
        
        return dependencies
    
    def _build_dependency_graph(self, dependencies: List[DynamicDependency]):
        """Build NetworkX dependency graph"""
        self.dependency_graph.clear()
        
        for dep in dependencies:
            if dep.is_active:
                self.dependency_graph.add_edge(
                    dep.source_service_id,
                    dep.target_service_id,
                    dependency_type=dep.dependency_type.value,
                    confidence=dep.confidence
                )
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the graph"""
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            return cycles
        except nx.NetworkXError:
            return []
    
    def calculate_dependency_depth(self, service_id: str) -> int:
        """Calculate the dependency depth of a service"""
        try:
            # Find shortest path from service to all leaf nodes
            if service_id not in self.dependency_graph:
                return 0
            
            # Calculate depths using BFS
            depths = nx.single_source_shortest_path_length(self.dependency_graph, service_id)
            return max(depths.values()) if depths else 0
        except nx.NetworkXError:
            return 0
    
    def get_service_dependencies(self, service_id: str, depth: int = None) -> Set[str]:
        """Get all dependencies of a service up to specified depth"""
        if service_id not in self.dependency_graph:
            return set()
        
        dependencies = set()
        visited = set()
        queue = deque([(service_id, 0)])
        
        while queue:
            current, current_depth = queue.popleft()
            
            if current in visited or (depth is not None and current_depth >= depth):
                continue
                
            visited.add(current)
            
            for neighbor in self.dependency_graph.successors(current):
                dependencies.add(neighbor)
                queue.append((neighbor, current_depth + 1))
        
        return dependencies
    
    def get_service_dependents(self, service_id: str) -> Set[str]:
        """Get all services that depend on this service"""
        if service_id not in self.dependency_graph:
            return set()
        
        return set(self.dependency_graph.predecessors(service_id))
    
    # Helper methods for service resolution
    def _resolve_import_to_service(self, module: str, names: List[ast.alias]) -> Optional[str]:
        """Resolve an import to a service ID"""
        # This would need to be implemented with actual service registry lookup
        # For now, return None
        return None
    
    def _resolve_call_to_service(self, obj_name: str, method_name: str) -> Optional[str]:
        """Resolve a method call to a service ID"""
        # This would need to be implemented with actual service registry lookup
        return None
    
    def _resolve_class_to_service(self, class_name: str) -> Optional[str]:
        """Resolve a class name to a service ID"""
        # This would need to be implemented with actual service registry lookup
        return None
    
    def _resolve_module_to_service(self, module: str) -> Optional[str]:
        """Resolve a module path to a service ID"""
        # This would need to be implemented with actual service registry lookup
        return None

class DependencyResolutionEngine:
    """
    MAMS-008: Dependency Resolution Engine with Auto-Discovery
    
    Continuously monitors codebase for new services and automatically
    builds and maintains dependency graphs
    """
    
    def __init__(self, root_path: str = None):
        self.root_path = Path(root_path or "/app")
        self.pattern_learner = PatternLearner()
        self.service_discoverer = ServiceDiscoverer(self.pattern_learner)
        self.dependency_analyzer = DependencyAnalyzer()
        
        # Initialize with default patterns
        self.pattern_learner.add_default_patterns()
        
        # State
        self.discovered_services: Dict[str, DiscoveredService] = {}
        self.dependencies: Dict[str, DynamicDependency] = {}
        self.auto_discovery_enabled = False
    
    def start_auto_discovery(self, interval: int = 60):
        """Start continuous auto-discovery"""
        self.auto_discovery_enabled = True
        asyncio.create_task(self._auto_discovery_loop(interval))
    
    def stop_auto_discovery(self):
        """Stop continuous auto-discovery"""
        self.auto_discovery_enabled = False
    
    async def _auto_discovery_loop(self, interval: int):
        """Continuous auto-discovery loop"""
        while self.auto_discovery_enabled:
            try:
                await self.discover_services()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"Error in auto-discovery loop: {e}")
                await asyncio.sleep(interval)
    
    async def discover_services(self, scan_paths: List[str] = None) -> Dict[str, DiscoveredService]:
        """Discover all services in specified paths"""
        if scan_paths is None:
            scan_paths = [
                "arkyvus/services/**/*.py",
                "arkyvus/api/**/*.py", 
                "arkyvus/managers/**/*.py",
                "arkyvus/handlers/**/*.py",
                "arkyvus/core/**/*.py",
                "arkyvus/utils/**/*.py"
            ]
        
        discovered_count = 0
        
        for pattern in scan_paths:
            for file_path in self.root_path.glob(pattern):
                if file_path.is_file() and file_path.suffix == '.py':
                    try:
                        content = file_path.read_text()
                        file_discoveries = self.service_discoverer.discover_in_file(
                            str(file_path), content
                        )
                        
                        for service in file_discoveries:
                            if service.service_identifier not in self.discovered_services:
                                self.discovered_services[service.service_identifier] = service
                                discovered_count += 1
                        
                        # Learn patterns from discoveries
                        if file_discoveries:
                            self.pattern_learner.learn_from_discovery(content, file_discoveries)
                            
                    except Exception as e:
                        print(f"Error discovering services in {file_path}: {e}")
        
        print(f"Discovered {discovered_count} new services")
        return self.discovered_services
    
    async def analyze_all_dependencies(self) -> Dict[str, DynamicDependency]:
        """Analyze dependencies for all discovered services"""
        dependencies = self.dependency_analyzer.analyze_dependencies(self.discovered_services)
        
        for dep in dependencies:
            self.dependencies[dep.dependency_id] = dep
        
        return self.dependencies
    
    def get_dependency_graph(self) -> nx.DiGraph:
        """Get the dependency graph"""
        return self.dependency_analyzer.dependency_graph
    
    def find_migration_order(self) -> List[str]:
        """Find optimal migration order based on dependencies"""
        graph = self.dependency_analyzer.dependency_graph
        
        try:
            # Topological sort for migration order
            return list(nx.topological_sort(graph))
        except nx.NetworkXError:
            # Handle cycles by breaking them
            return self._resolve_cycles_and_sort(graph)
    
    def _resolve_cycles_and_sort(self, graph: nx.DiGraph) -> List[str]:
        """Resolve cycles and return a valid topological order"""
        # Find strongly connected components
        sccs = list(nx.strongly_connected_components(graph))
        
        # Create condensation graph (DAG of SCCs)
        condensation = nx.condensation(graph)
        
        # Topologically sort the condensation
        scc_order = list(nx.topological_sort(condensation))
        
        # Expand SCCs back to original nodes
        result = []
        for scc_index in scc_order:
            scc_nodes = sccs[scc_index]
            # Within an SCC, order by dependency count
            scc_sorted = sorted(
                scc_nodes,
                key=lambda x: graph.in_degree(x)
            )
            result.extend(scc_sorted)
        
        return result
    
    def analyze_migration_impact(self, service_ids: List[str]) -> Dict[str, Any]:
        """Analyze the impact of migrating specific services"""
        impact_analysis = {
            'services_to_migrate': service_ids,
            'direct_dependencies': set(),
            'transitive_dependencies': set(),
            'dependent_services': set(),
            'potential_conflicts': [],
            'migration_complexity': 0
        }
        
        for service_id in service_ids:
            # Find dependencies
            deps = self.dependency_analyzer.get_service_dependencies(service_id)
            impact_analysis['direct_dependencies'].update(deps)
            
            # Find dependents
            dependents = self.dependency_analyzer.get_service_dependents(service_id)
            impact_analysis['dependent_services'].update(dependents)
            
            # Calculate complexity
            complexity = self.dependency_analyzer.calculate_dependency_depth(service_id)
            impact_analysis['migration_complexity'] += complexity
        
        # Find cycles
        cycles = self.dependency_analyzer.find_circular_dependencies()
        for cycle in cycles:
            if any(service_id in cycle for service_id in service_ids):
                impact_analysis['potential_conflicts'].append({
                    'type': 'circular_dependency',
                    'cycle': cycle
                })
        
        return impact_analysis
    
    def get_discovery_statistics(self) -> Dict[str, Any]:
        """Get statistics about the discovery process"""
        stats = {
            'total_services': len(self.discovered_services),
            'services_by_type': defaultdict(int),
            'dependencies_by_type': defaultdict(int),
            'patterns_learned': 0,
            'auto_classified': 0,
            'manually_classified': 0
        }
        
        # Count services by type
        for service in self.discovered_services.values():
            stats['services_by_type'][service.service_type] += 1
            if service.auto_classified:
                stats['auto_classified'] += 1
            else:
                stats['manually_classified'] += 1
        
        # Count dependencies by type
        for dep in self.dependencies.values():
            stats['dependencies_by_type'][dep.dependency_type.value] += 1
        
        # Count learned patterns
        stats['patterns_learned'] = len([
            p for p in self.pattern_learner.patterns if p.auto_learned
        ])
        
        return dict(stats)


def test_dependency_resolution_engine():
    """Test the dependency resolution engine"""
    print("=" * 60)
    print("MAMS-008: Dependency Resolution Engine Test")
    print("=" * 60)
    
    # Initialize engine
    engine = DependencyResolutionEngine()
    
    # Create mock services for testing
    mock_services = {
        'AuthService': DiscoveredService(
            service_id="SVC_001",
            service_identifier="arkyvus.services.auth.AuthService",
            discovery_timestamp=datetime.now(),
            discovery_source="scan",
            file_path="arkyvus/services/auth_service.py",
            service_type="service",
            confidence_score=0.95
        ),
        'UserManager': DiscoveredService(
            service_id="SVC_002", 
            service_identifier="arkyvus.services.user.UserManager",
            discovery_timestamp=datetime.now(),
            discovery_source="scan", 
            file_path="arkyvus/services/user_manager.py",
            service_type="manager",
            confidence_score=0.90
        ),
        'PaymentHandler': DiscoveredService(
            service_id="SVC_003",
            service_identifier="arkyvus.handlers.payment.PaymentHandler",
            discovery_timestamp=datetime.now(),
            discovery_source="scan",
            file_path="arkyvus/handlers/payment_handler.py", 
            service_type="handler",
            confidence_score=0.85
        )
    }
    
    engine.discovered_services.update({s.service_identifier: s for s in mock_services.values()})
    
    # Create mock dependencies
    mock_dependencies = [
        DynamicDependency(
            dependency_id="DEP_001",
            source_service_id="SVC_002",  # UserManager
            target_service_id="SVC_001",  # AuthService
            dependency_type=DependencyType.IMPORT,
            detection_method=DetectionMethod.AST,
            metadata={'module': 'arkyvus.services.auth', 'line': 5}
        ),
        DynamicDependency(
            dependency_id="DEP_002",
            source_service_id="SVC_003",  # PaymentHandler
            target_service_id="SVC_002",  # UserManager
            dependency_type=DependencyType.CALL,
            detection_method=DetectionMethod.AST,
            metadata={'method': 'get_user', 'line': 25}
        )
    ]
    
    engine.dependencies.update({d.dependency_id: d for d in mock_dependencies})
    
    # Build dependency graph
    engine.dependency_analyzer._build_dependency_graph(mock_dependencies)
    
    async def run_test():
        print(f"Testing with {len(mock_services)} mock services...")
        
        # Test discovery statistics
        stats = engine.get_discovery_statistics()
        print(f"\n📊 Discovery Statistics:")
        print(f"   Total Services: {stats['total_services']}")
        print(f"   Auto-classified: {stats['auto_classified']}")
        print(f"   Services by Type:")
        for service_type, count in stats['services_by_type'].items():
            print(f"     {service_type}: {count}")
        
        # Test dependency analysis
        print(f"\n🔗 Dependency Analysis:")
        print(f"   Total Dependencies: {len(engine.dependencies)}")
        print(f"   Dependencies by Type:")
        for dep_type, count in stats['dependencies_by_type'].items():
            print(f"     {dep_type}: {count}")
        
        # Test migration order
        migration_order = engine.find_migration_order()
        print(f"\n📋 Migration Order:")
        for i, service_id in enumerate(migration_order, 1):
            service = next((s for s in mock_services.values() if s.service_id == service_id), None)
            if service:
                print(f"   {i}. {service.service_identifier} ({service.service_type})")
        
        # Test circular dependency detection
        cycles = engine.dependency_analyzer.find_circular_dependencies()
        print(f"\n🔄 Circular Dependencies: {len(cycles)}")
        for cycle in cycles:
            print(f"   Cycle: {' → '.join(cycle)} → {cycle[0]}")
        
        # Test migration impact analysis
        test_services = ["SVC_002"]  # UserManager
        impact = engine.analyze_migration_impact(test_services)
        print(f"\n🎯 Migration Impact Analysis for {test_services}:")
        print(f"   Direct Dependencies: {len(impact['direct_dependencies'])}")
        print(f"   Dependent Services: {len(impact['dependent_services'])}")
        print(f"   Migration Complexity: {impact['migration_complexity']}")
        print(f"   Potential Conflicts: {len(impact['potential_conflicts'])}")
        
        # Test pattern learning
        print(f"\n🧠 Pattern Learning:")
        print(f"   Total Patterns: {len(engine.pattern_learner.patterns)}")
        print(f"   Default Patterns: {len([p for p in engine.pattern_learner.patterns if not p.auto_learned])}")
        print(f"   Learned Patterns: {len([p for p in engine.pattern_learner.patterns if p.auto_learned])}")
        
        print(f"\n✅ Dependency Resolution Engine Test Complete!")
        return True
    
    # Run async test
    success = asyncio.run(run_test())
    return success


if __name__ == "__main__":
    success = test_dependency_resolution_engine()
    sys.exit(0 if success else 1)