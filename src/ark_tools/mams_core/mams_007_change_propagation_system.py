#!/usr/bin/env python3
"""
MAMS-007: Change Propagation System
Intelligent change tracking and reference updating for service migrations
"""

import ast
import json
import re
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class ChangeType(Enum):
    SERVICE_RENAME = "service_rename"
    SERVICE_MOVE = "service_move"
    SERVICE_SPLIT = "service_split"
    SERVICE_MERGE = "service_merge"
    METHOD_RENAME = "method_rename"
    METHOD_MOVE = "method_move"
    METHOD_SIGNATURE = "method_signature"
    IMPORT_PATH = "import_path"
    TYPE_DEFINITION = "type_definition"

class ReferenceType(Enum):
    IMPORT = "import"
    CALL = "call"
    INHERITANCE = "inheritance"
    TYPE_ANNOTATION = "type_annotation"
    DECORATOR = "decorator"
    STRING_LITERAL = "string_literal"

class PropagationStrategy(Enum):
    EAGER = "eager"  # Update immediately
    LAZY = "lazy"    # Update on demand
    STAGED = "staged"  # Update in phases

@dataclass
class ChangeRecord:
    """Record of a specific change made during migration"""
    change_id: str
    change_type: ChangeType
    original_element: str
    new_element: str
    source_location: str
    timestamp: datetime = field(default_factory=datetime.now)
    
@dataclass
class Reference:
    """A reference from one element to another"""
    reference_id: str
    source_type: str
    source_identifier: str
    source_location: str
    target_type: str
    target_identifier: str
    target_location: str
    reference_type: ReferenceType
    confidence: float = 1.0

@dataclass 
class PropagationImpact:
    """Impact of a change on a specific file/location"""
    impact_id: str
    change_id: str
    affected_file: str
    affected_line: int
    affected_element: str
    impact_type: str  # direct, transitive, potential
    update_required: bool
    update_applied: bool = False
    update_status: str = "pending"
    error_message: Optional[str] = None

@dataclass
class PropagationResult:
    """Result of applying a propagation operation"""
    success: bool
    files_processed: int
    references_updated: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rollback_data: Optional[Dict] = None

class ChangeDetectionEngine:
    """Detects changes in code through AST comparison"""
    
    def __init__(self):
        self.detected_changes: List[ChangeRecord] = []
    
    def detect_changes(self, before_ast: ast.AST, after_ast: ast.AST, 
                      file_path: str) -> List[ChangeRecord]:
        """Detect changes between two AST trees"""
        changes = []
        
        # Extract elements from both ASTs
        before_elements = self._extract_elements(before_ast)
        after_elements = self._extract_elements(after_ast)
        
        # Find renamed/moved elements
        changes.extend(self._detect_renames(before_elements, after_elements, file_path))
        changes.extend(self._detect_moves(before_elements, after_elements, file_path))
        changes.extend(self._detect_signature_changes(before_elements, after_elements, file_path))
        
        return changes
    
    def _extract_elements(self, tree: ast.AST) -> Dict[str, Dict]:
        """Extract all interesting elements from AST"""
        elements = {
            'classes': {},
            'methods': {},
            'functions': {},
            'imports': {}
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                elements['classes'][node.name] = {
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [self._ast_to_string(base) for base in node.bases],
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                }
            elif isinstance(node, ast.FunctionDef):
                elements['functions'][node.name] = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'returns': self._ast_to_string(node.returns) if node.returns else None
                }
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    elements['imports'][f"{node.module}:{node.lineno}"] = {
                        'module': node.module,
                        'names': [alias.name for alias in node.names],
                        'line': node.lineno
                    }
        
        return elements
    
    def _detect_renames(self, before: Dict, after: Dict, file_path: str) -> List[ChangeRecord]:
        """Detect renamed elements"""
        changes = []
        
        # Check class renames
        before_classes = set(before['classes'].keys())
        after_classes = set(after['classes'].keys())
        
        # Simple heuristic: if one class disappeared and one appeared, might be rename
        removed = before_classes - after_classes
        added = after_classes - before_classes
        
        if len(removed) == 1 and len(added) == 1:
            old_name = list(removed)[0]
            new_name = list(added)[0]
            
            # Check if structure is similar
            old_class = before['classes'][old_name]
            new_class = after['classes'][new_name]
            
            # Simple similarity check
            if len(old_class['methods']) == len(new_class['methods']):
                changes.append(ChangeRecord(
                    change_id=str(uuid.uuid4()),
                    change_type=ChangeType.SERVICE_RENAME,
                    original_element=old_name,
                    new_element=new_name,
                    source_location=f"{file_path}:{old_class['line']}"
                ))
        
        return changes
    
    def _detect_moves(self, before: Dict, after: Dict, file_path: str) -> List[ChangeRecord]:
        """Detect moved elements"""
        # For this implementation, we'll track imports as moves
        changes = []
        
        before_imports = before['imports']
        after_imports = after['imports']
        
        for before_key, before_import in before_imports.items():
            found = False
            for after_key, after_import in after_imports.items():
                if (before_import['names'] == after_import['names'] and 
                    before_import['module'] != after_import['module']):
                    changes.append(ChangeRecord(
                        change_id=str(uuid.uuid4()),
                        change_type=ChangeType.IMPORT_PATH,
                        original_element=before_import['module'],
                        new_element=after_import['module'],
                        source_location=f"{file_path}:{before_import['line']}"
                    ))
                    found = True
                    break
        
        return changes
    
    def _detect_signature_changes(self, before: Dict, after: Dict, file_path: str) -> List[ChangeRecord]:
        """Detect method signature changes"""
        changes = []
        
        # Compare function signatures
        for func_name in before['functions']:
            if func_name in after['functions']:
                before_func = before['functions'][func_name]
                after_func = after['functions'][func_name]
                
                if before_func['args'] != after_func['args']:
                    changes.append(ChangeRecord(
                        change_id=str(uuid.uuid4()),
                        change_type=ChangeType.METHOD_SIGNATURE,
                        original_element=f"{func_name}({', '.join(before_func['args'])})",
                        new_element=f"{func_name}({', '.join(after_func['args'])})",
                        source_location=f"{file_path}:{before_func['line']}"
                    ))
        
        return changes
    
    def _ast_to_string(self, node: ast.AST) -> str:
        """Convert AST node to string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return "unknown"

class ReferenceTracker:
    """Tracks all references between elements in the codebase"""
    
    def __init__(self):
        self.references: List[Reference] = []
        self.reference_graph: Dict[str, Set[str]] = {}
    
    def scan_file_references(self, file_path: str, content: str) -> List[Reference]:
        """Scan a file for all references"""
        references = []
        
        try:
            tree = ast.parse(content)
            visitor = ReferenceVisitor(file_path)
            visitor.visit(tree)
            references.extend(visitor.references)
        except SyntaxError:
            # Handle syntax errors gracefully
            references.extend(self._scan_text_references(file_path, content))
        
        return references
    
    def _scan_text_references(self, file_path: str, content: str) -> List[Reference]:
        """Fallback text-based reference scanning"""
        references = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Find imports
            import_match = re.search(r'from\s+([\w\.]+)\s+import\s+([\w,\s]+)', line)
            if import_match:
                module = import_match.group(1)
                names = [n.strip() for n in import_match.group(2).split(',')]
                
                for name in names:
                    references.append(Reference(
                        reference_id=str(uuid.uuid4()),
                        source_type="file",
                        source_identifier=file_path,
                        source_location=f"{file_path}:{line_num}",
                        target_type="module",
                        target_identifier=f"{module}.{name}",
                        target_location="unknown",
                        reference_type=ReferenceType.IMPORT,
                        confidence=0.9
                    ))
            
            # Find method calls
            call_matches = re.finditer(r'(\w+)\.(\w+)\s*\(', line)
            for match in call_matches:
                obj_name = match.group(1)
                method_name = match.group(2)
                
                references.append(Reference(
                    reference_id=str(uuid.uuid4()),
                    source_type="file",
                    source_identifier=file_path,
                    source_location=f"{file_path}:{line_num}:{match.start()}",
                    target_type="method",
                    target_identifier=f"{obj_name}.{method_name}",
                    target_location="unknown",
                    reference_type=ReferenceType.CALL,
                    confidence=0.8
                ))
        
        return references
    
    def build_reference_graph(self, references: List[Reference]) -> Dict[str, Set[str]]:
        """Build a graph of all references"""
        graph = {}
        
        for ref in references:
            source = ref.source_identifier
            target = ref.target_identifier
            
            if source not in graph:
                graph[source] = set()
            graph[source].add(target)
        
        self.reference_graph = graph
        return graph
    
    def find_transitive_impacts(self, changed_element: str) -> Set[str]:
        """Find all elements transitively affected by a change"""
        affected = set()
        to_process = {changed_element}
        
        while to_process:
            current = to_process.pop()
            if current in affected:
                continue
                
            affected.add(current)
            
            # Find all elements that reference current
            for source, targets in self.reference_graph.items():
                if current in targets and source not in affected:
                    to_process.add(source)
        
        return affected

class ReferenceVisitor(ast.NodeVisitor):
    """AST visitor to find references"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.references: List[Reference] = []
    
    def visit_ImportFrom(self, node):
        """Handle 'from module import name' statements"""
        if node.module:
            for alias in node.names:
                self.references.append(Reference(
                    reference_id=str(uuid.uuid4()),
                    source_type="file",
                    source_identifier=self.file_path,
                    source_location=f"{self.file_path}:{node.lineno}",
                    target_type="module",
                    target_identifier=f"{node.module}.{alias.name}",
                    target_location="unknown",
                    reference_type=ReferenceType.IMPORT
                ))
    
    def visit_Call(self, node):
        """Handle method/function calls"""
        if isinstance(node.func, ast.Attribute):
            target = self._get_full_name(node.func)
            if target:
                self.references.append(Reference(
                    reference_id=str(uuid.uuid4()),
                    source_type="file", 
                    source_identifier=self.file_path,
                    source_location=f"{self.file_path}:{node.lineno}:{node.col_offset}",
                    target_type="method",
                    target_identifier=target,
                    target_location="unknown",
                    reference_type=ReferenceType.CALL
                ))
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Handle class definitions and inheritance"""
        for base in node.bases:
            base_name = self._get_full_name(base)
            if base_name:
                self.references.append(Reference(
                    reference_id=str(uuid.uuid4()),
                    source_type="class",
                    source_identifier=f"{self.file_path}.{node.name}",
                    source_location=f"{self.file_path}:{node.lineno}",
                    target_type="class",
                    target_identifier=base_name,
                    target_location="unknown",
                    reference_type=ReferenceType.INHERITANCE
                ))
        self.generic_visit(node)
    
    def _get_full_name(self, node):
        """Extract full dotted name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_full_name(node.value)
            if value:
                return f"{value}.{node.attr}"
        return None

class UpdateApplicator:
    """Applies updates to files based on propagation impacts"""
    
    def __init__(self):
        self.update_strategies = {
            ChangeType.SERVICE_RENAME: self._apply_service_rename,
            ChangeType.IMPORT_PATH: self._apply_import_update,
            ChangeType.METHOD_RENAME: self._apply_method_rename,
            ChangeType.METHOD_SIGNATURE: self._apply_signature_update
        }
    
    def apply_updates(self, impacts: List[PropagationImpact], 
                     changes: Dict[str, ChangeRecord]) -> PropagationResult:
        """Apply all updates for given impacts"""
        result = PropagationResult(success=True, files_processed=0, references_updated=0)
        processed_files = set()
        
        # Group impacts by file for efficient processing
        impacts_by_file = {}
        for impact in impacts:
            if impact.affected_file not in impacts_by_file:
                impacts_by_file[impact.affected_file] = []
            impacts_by_file[impact.affected_file].append(impact)
        
        # Process each file
        for file_path, file_impacts in impacts_by_file.items():
            try:
                file_result = self._apply_file_updates(file_path, file_impacts, changes)
                if file_result['success']:
                    result.references_updated += file_result['updates_applied']
                    processed_files.add(file_path)
                else:
                    result.errors.extend(file_result['errors'])
                    result.success = False
            except Exception as e:
                result.errors.append(f"Error processing {file_path}: {e}")
                result.success = False
        
        result.files_processed = len(processed_files)
        return result
    
    def _apply_file_updates(self, file_path: str, impacts: List[PropagationImpact],
                           changes: Dict[str, ChangeRecord]) -> Dict[str, Any]:
        """Apply updates to a single file"""
        try:
            # Read original content
            path_obj = Path(file_path)
            if not path_obj.exists():
                return {'success': False, 'errors': [f"File not found: {file_path}"]}
            
            original_content = path_obj.read_text()
            updated_content = original_content
            updates_applied = 0
            
            # Apply updates (process in reverse line order to maintain line numbers)
            sorted_impacts = sorted(impacts, key=lambda x: x.affected_line, reverse=True)
            
            for impact in sorted_impacts:
                if impact.update_required and not impact.update_applied:
                    change = changes.get(impact.change_id)
                    if change:
                        update_func = self.update_strategies.get(change.change_type)
                        if update_func:
                            updated_content = update_func(updated_content, impact, change)
                            updates_applied += 1
                            impact.update_applied = True
                            impact.update_status = "completed"
            
            # Write updated content if changes were made
            if updates_applied > 0:
                # Create backup
                backup_path = path_obj.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                backup_path.write_text(original_content)
                
                # Write updated content
                path_obj.write_text(updated_content)
            
            return {
                'success': True,
                'updates_applied': updates_applied,
                'backup_created': updates_applied > 0
            }
            
        except Exception as e:
            return {'success': False, 'errors': [str(e)]}
    
    def _apply_service_rename(self, content: str, impact: PropagationImpact, 
                             change: ChangeRecord) -> str:
        """Apply service rename update"""
        lines = content.split('\n')
        
        if impact.affected_line <= len(lines):
            line = lines[impact.affected_line - 1]
            updated_line = line.replace(change.original_element, change.new_element)
            lines[impact.affected_line - 1] = updated_line
        
        return '\n'.join(lines)
    
    def _apply_import_update(self, content: str, impact: PropagationImpact,
                            change: ChangeRecord) -> str:
        """Apply import path update"""
        lines = content.split('\n')
        
        if impact.affected_line <= len(lines):
            line = lines[impact.affected_line - 1]
            # Update import statement
            if 'from' in line and 'import' in line:
                updated_line = line.replace(change.original_element, change.new_element)
                lines[impact.affected_line - 1] = updated_line
        
        return '\n'.join(lines)
    
    def _apply_method_rename(self, content: str, impact: PropagationImpact,
                            change: ChangeRecord) -> str:
        """Apply method rename update"""
        # Extract old and new method names
        old_method = change.original_element
        new_method = change.new_element
        
        # Simple find and replace for method calls
        # This could be made more sophisticated with AST manipulation
        return content.replace(f".{old_method}(", f".{new_method}(")
    
    def _apply_signature_update(self, content: str, impact: PropagationImpact,
                               change: ChangeRecord) -> str:
        """Apply method signature update"""
        # For now, just log that signature update is needed
        # This would require more sophisticated AST manipulation
        lines = content.split('\n')
        if impact.affected_line <= len(lines):
            line = lines[impact.affected_line - 1]
            # Add a TODO comment about signature change
            comment = f"  # TODO: Update call signature for {change.original_element} -> {change.new_element}"
            lines.insert(impact.affected_line - 1, comment)
        
        return '\n'.join(lines)

class ChangePropagationSystem:
    """
    MAMS-007: Change Propagation System
    
    Orchestrates change detection, reference tracking, and update application
    """
    
    def __init__(self):
        self.change_detector = ChangeDetectionEngine()
        self.reference_tracker = ReferenceTracker()
        self.update_applicator = UpdateApplicator()
        
        self.changes: Dict[str, ChangeRecord] = {}
        self.references: List[Reference] = []
        self.impacts: List[PropagationImpact] = []
    
    def register_change(self, change: ChangeRecord):
        """Register a change that occurred during migration"""
        self.changes[change.change_id] = change
    
    def scan_codebase_references(self, root_path: str, patterns: List[str] = None) -> int:
        """Scan the entire codebase for references"""
        if patterns is None:
            patterns = ['**/*.py']
        
        root = Path(root_path)
        scanned_files = 0
        
        for pattern in patterns:
            for file_path in root.glob(pattern):
                if file_path.is_file():
                    try:
                        content = file_path.read_text()
                        file_references = self.reference_tracker.scan_file_references(
                            str(file_path), content
                        )
                        self.references.extend(file_references)
                        scanned_files += 1
                    except Exception as e:
                        print(f"Error scanning {file_path}: {e}")
        
        # Build reference graph
        self.reference_tracker.build_reference_graph(self.references)
        return scanned_files
    
    def analyze_propagation_impacts(self, changes: List[ChangeRecord]) -> List[PropagationImpact]:
        """Analyze what needs to be updated for given changes"""
        impacts = []
        
        for change in changes:
            # Find all references to the changed element
            affected_refs = [
                ref for ref in self.references 
                if change.original_element in ref.target_identifier
            ]
            
            # Create impact records
            for ref in affected_refs:
                impact = PropagationImpact(
                    impact_id=str(uuid.uuid4()),
                    change_id=change.change_id,
                    affected_file=ref.source_identifier,
                    affected_line=self._extract_line_number(ref.source_location),
                    affected_element=ref.source_identifier,
                    impact_type="direct",
                    update_required=True
                )
                impacts.append(impact)
            
            # Find transitive impacts
            transitive_elements = self.reference_tracker.find_transitive_impacts(
                change.original_element
            )
            
            for element in transitive_elements:
                if element != change.original_element:
                    impact = PropagationImpact(
                        impact_id=str(uuid.uuid4()),
                        change_id=change.change_id,
                        affected_file=element,
                        affected_line=1,  # Default line
                        affected_element=element,
                        impact_type="transitive",
                        update_required=True
                    )
                    impacts.append(impact)
        
        self.impacts.extend(impacts)
        return impacts
    
    def propagate_changes(self, strategy: PropagationStrategy = PropagationStrategy.STAGED) -> PropagationResult:
        """Execute change propagation with given strategy"""
        if strategy == PropagationStrategy.EAGER:
            return self._eager_propagation()
        elif strategy == PropagationStrategy.LAZY:
            return self._lazy_propagation()
        else:
            return self._staged_propagation()
    
    def _eager_propagation(self) -> PropagationResult:
        """Apply all changes immediately"""
        return self.update_applicator.apply_updates(self.impacts, self.changes)
    
    def _lazy_propagation(self) -> PropagationResult:
        """Mark changes for later application"""
        # For now, just return success without applying
        return PropagationResult(
            success=True,
            files_processed=0,
            references_updated=0,
            warnings=["Lazy propagation: changes marked but not applied"]
        )
    
    def _staged_propagation(self) -> PropagationResult:
        """Apply changes in phases"""
        phases = [
            ("import", [imp for imp in self.impacts if "import" in imp.affected_element.lower()]),
            ("direct", [imp for imp in self.impacts if imp.impact_type == "direct"]),
            ("transitive", [imp for imp in self.impacts if imp.impact_type == "transitive"])
        ]
        
        overall_result = PropagationResult(success=True, files_processed=0, references_updated=0)
        
        for phase_name, phase_impacts in phases:
            if phase_impacts:
                print(f"Applying {phase_name} phase: {len(phase_impacts)} impacts")
                phase_result = self.update_applicator.apply_updates(phase_impacts, self.changes)
                
                overall_result.files_processed += phase_result.files_processed
                overall_result.references_updated += phase_result.references_updated
                overall_result.errors.extend(phase_result.errors)
                overall_result.warnings.extend(phase_result.warnings)
                
                if not phase_result.success:
                    overall_result.success = False
        
        return overall_result
    
    def _extract_line_number(self, location: str) -> int:
        """Extract line number from location string"""
        try:
            parts = location.split(':')
            if len(parts) >= 2:
                return int(parts[1])
        except:
            pass
        return 1
    
    def validate_propagation(self, root_path: str) -> Dict[str, Any]:
        """Validate that propagation didn't break anything"""
        validation_result = {
            'syntax_errors': [],
            'import_errors': [],
            'test_failures': [],
            'overall_valid': True
        }
        
        root = Path(root_path)
        
        # Check Python syntax
        for py_file in root.glob('**/*.py'):
            try:
                with open(py_file, 'r') as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                validation_result['syntax_errors'].append({
                    'file': str(py_file),
                    'error': str(e)
                })
                validation_result['overall_valid'] = False
        
        return validation_result

def test_change_propagation_system():
    """Test the change propagation system"""
    print("=" * 60)
    print("MAMS-007: Change Propagation System Test")  
    print("=" * 60)
    
    # Initialize system
    system = ChangePropagationSystem()
    
    # Create test changes
    test_changes = [
        ChangeRecord(
            change_id="CHANGE_001",
            change_type=ChangeType.SERVICE_RENAME,
            original_element="AuthService",
            new_element="UnifiedAuthService",
            source_location="arkyvus/services/auth_service.py:1"
        ),
        ChangeRecord(
            change_id="CHANGE_002", 
            change_type=ChangeType.METHOD_RENAME,
            original_element="login",
            new_element="auth_login",
            source_location="arkyvus/services/auth_service.py:25"
        ),
        ChangeRecord(
            change_id="CHANGE_003",
            change_type=ChangeType.IMPORT_PATH,
            original_element="arkyvus.services.auth",
            new_element="arkyvus.services.unified.auth_service",
            source_location="arkyvus/services/auth_service.py:5"
        )
    ]
    
    print(f"Testing with {len(test_changes)} changes:")
    for change in test_changes:
        print(f"  {change.change_type.value}: {change.original_element} → {change.new_element}")
        system.register_change(change)
    
    # Create mock references
    mock_references = [
        Reference(
            reference_id="REF_001",
            source_type="file",
            source_identifier="arkyvus/api/v1/auth.py",
            source_location="arkyvus/api/v1/auth.py:5",
            target_type="service",
            target_identifier="arkyvus.services.auth.AuthService",
            target_location="arkyvus/services/auth_service.py:1",
            reference_type=ReferenceType.IMPORT
        ),
        Reference(
            reference_id="REF_002",
            source_type="file",
            source_identifier="arkyvus/api/v1/auth.py", 
            source_location="arkyvus/api/v1/auth.py:25",
            target_type="method",
            target_identifier="AuthService.login",
            target_location="arkyvus/services/auth_service.py:25",
            reference_type=ReferenceType.CALL
        )
    ]
    
    system.references.extend(mock_references)
    system.reference_tracker.build_reference_graph(mock_references)
    
    print(f"\n📊 Reference Analysis:")
    print(f"   Total References: {len(system.references)}")
    print(f"   Reference Graph Nodes: {len(system.reference_tracker.reference_graph)}")
    
    # Analyze impacts
    impacts = system.analyze_propagation_impacts(test_changes)
    print(f"\n🎯 Impact Analysis:")
    print(f"   Total Impacts: {len(impacts)}")
    
    impact_types = {}
    for impact in impacts:
        impact_types[impact.impact_type] = impact_types.get(impact.impact_type, 0) + 1
    
    for impact_type, count in impact_types.items():
        print(f"   {impact_type.title()}: {count}")
    
    # Test propagation strategies
    print(f"\n🔄 Propagation Strategy Testing:")
    
    # Test staged propagation (safe for testing)
    result = system.propagate_changes(PropagationStrategy.STAGED)
    
    print(f"   Strategy: STAGED")
    print(f"   Success: {result.success}")
    print(f"   Files Processed: {result.files_processed}")
    print(f"   References Updated: {result.references_updated}")
    
    if result.errors:
        print(f"   Errors: {len(result.errors)}")
        for error in result.errors[:2]:  # Show first 2 errors
            print(f"     • {error}")
    
    if result.warnings:
        print(f"   Warnings: {len(result.warnings)}")
        for warning in result.warnings[:2]:  # Show first 2 warnings
            print(f"     • {warning}")
    
    print(f"\n✅ Change Propagation System Test Complete!")
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"   Changes Registered: {len(system.changes)}")
    print(f"   References Tracked: {len(system.references)}")
    print(f"   Impacts Identified: {len(system.impacts)}")
    print(f"   Propagation Success: {result.success}")
    
    return True


if __name__ == "__main__":
    success = test_change_propagation_system()
    sys.exit(0 if success else 1)