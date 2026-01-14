#!/usr/bin/env python3
"""
Phase 2: Component Extractor
The "Ghost Hunter" - Finds ALL code components including standalone helpers
Ensures nothing gets left behind during migration
"""

import libcst as cst
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

class ComponentExtractor(cst.CSTVisitor):
    """
    Extracts ALL code components from a Python file.
    Critical: Captures "Ghost Helpers" (standalone functions) that usually get lost.
    """
    
    def __init__(self):
        self.components = {
            'module_docstring': None,
            'imports': [],
            'classes': [],
            'standalone_functions': [],  # The Ghost Helpers!
            'global_constants': [],
            'global_variables': [],
            'type_aliases': [],
            'statistics': {
                'total_lines': 0,
                'comment_lines': 0,
                'docstring_count': 0
            }
        }
        self.in_class = False
        self.current_class = None
    
    def visit_Module(self, node: cst.Module) -> bool:
        """Extract module-level docstring if present"""
        if node.body and isinstance(node.body[0], cst.SimpleStatementLine):
            first_stmt = node.body[0]
            if len(first_stmt.body) == 1 and isinstance(first_stmt.body[0], cst.Expr):
                expr = first_stmt.body[0]
                if isinstance(expr.value, (cst.SimpleString, cst.ConcatenatedString)):
                    self.components['module_docstring'] = self._extract_string_value(expr.value)
        return True
    
    def visit_Import(self, node: cst.Import) -> bool:
        """Capture import statements"""
        self.components['imports'].append({
            'type': 'import',
            'node': node,
            'code': node.__class__.__name__
        })
        return False
    
    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        """Capture from...import statements"""
        module = self._get_module_string(node.module) if node.module else ''
        names = []
        if isinstance(node.names, cst.ImportStar):
            names = ['*']
        else:
            for name in node.names:
                if isinstance(name, cst.ImportAlias):
                    names.append(name.name.value if isinstance(name.name, cst.Name) else str(name.name))
        
        self.components['imports'].append({
            'type': 'import_from',
            'module': module,
            'names': names,
            'node': node
        })
        return False
    
    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        """Track when we enter a class definition"""
        self.in_class = True
        self.current_class = node.name.value
        
        # Extract class information
        bases = []
        for base in node.bases:
            if isinstance(base.value, cst.Name):
                bases.append(base.value.value)
        
        self.components['classes'].append({
            'name': node.name.value,
            'bases': bases,
            'decorators': [self._decorator_to_string(d) for d in node.decorators],
            'node': node,
            'methods': []  # Will be populated by visit_FunctionDef
        })
        return True
    
    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        """Track when we leave a class"""
        self.in_class = False
        self.current_class = None
    
    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        """
        Extract functions - both class methods AND standalone helpers.
        This is critical for catching "Ghost Helpers"!
        """
        func_info = {
            'name': node.name.value,
            'is_async': isinstance(node.asynchronous, cst.Asynchronous),
            'decorators': [self._decorator_to_string(d) for d in node.decorators],
            'params': self._extract_params(node.params),
            'returns': self._get_annotation_string(node.returns) if node.returns else None,
            'docstring': self._extract_docstring(node),
            'node': node
        }
        
        if self.in_class:
            # This is a method inside a class
            func_info['class'] = self.current_class
            # Add to the last class's methods
            if self.components['classes']:
                self.components['classes'][-1]['methods'].append(func_info)
        else:
            # This is a STANDALONE HELPER FUNCTION - Ghost Hunter catches it!
            self.components['standalone_functions'].append(func_info)
            print(f"  🎯 Found standalone function: {func_info['name']}")
        
        return False  # Don't visit nested functions
    
    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool:
        """Capture type aliases and annotated globals"""
        if not self.in_class and isinstance(node.target, cst.Name):
            self.components['type_aliases'].append({
                'name': node.target.value,
                'type': self._get_annotation_string(node.annotation),
                'value': node.value,
                'node': node
            })
        return False
    
    def visit_Assign(self, node: cst.Assign) -> bool:
        """
        Capture global constants and variables.
        Critical for DEFAULT_TIMEOUT, MAX_RETRIES, etc.
        """
        if not self.in_class and len(node.targets) == 1:
            target = node.targets[0].target
            if isinstance(target, cst.Name):
                var_name = target.value
                
                # Determine if it's a constant (UPPERCASE or starts with DEFAULT_)
                is_constant = (var_name.isupper() or 
                             var_name.startswith('DEFAULT_') or
                             var_name.endswith('_CONFIG'))
                
                var_info = {
                    'name': var_name,
                    'value': self._get_value_string(node.value),
                    'is_constant': is_constant,
                    'node': node
                }
                
                if is_constant:
                    self.components['global_constants'].append(var_info)
                    print(f"  📌 Found global constant: {var_name}")
                else:
                    self.components['global_variables'].append(var_info)
        
        return False
    
    def _extract_params(self, params: cst.Parameters) -> List[Dict]:
        """Extract parameter information"""
        param_list = []
        
        for param in params.params:
            param_info = {
                'name': param.name.value if isinstance(param.name, cst.Name) else str(param.name),
                'annotation': self._get_annotation_string(param.annotation) if param.annotation else None,
                'default': self._get_value_string(param.default) if param.default else None
            }
            param_list.append(param_info)
        
        return param_list
    
    def _extract_docstring(self, node: cst.FunctionDef) -> Optional[str]:
        """Extract docstring from function"""
        if node.body and node.body.body:
            first_stmt = node.body.body[0]
            if isinstance(first_stmt, cst.SimpleStatementLine):
                if len(first_stmt.body) == 1 and isinstance(first_stmt.body[0], cst.Expr):
                    expr = first_stmt.body[0]
                    if isinstance(expr.value, (cst.SimpleString, cst.ConcatenatedString)):
                        self.components['statistics']['docstring_count'] += 1
                        return self._extract_string_value(expr.value)
        return None
    
    def _extract_string_value(self, node) -> str:
        """Extract string value from various string nodes"""
        if isinstance(node, cst.SimpleString):
            return node.value.strip('"\'')
        elif isinstance(node, cst.ConcatenatedString):
            parts = []
            for part in node.left, node.right:
                parts.append(self._extract_string_value(part))
            return ''.join(parts)
        return str(node)
    
    def _decorator_to_string(self, decorator: cst.Decorator) -> str:
        """Convert decorator to string representation"""
        return decorator.decorator.value if isinstance(decorator.decorator, cst.Name) else str(decorator.decorator)
    
    def _get_module_string(self, module) -> str:
        """Convert module node to string"""
        if isinstance(module, cst.Name):
            return module.value
        elif isinstance(module, cst.Attribute):
            return f"{self._get_module_string(module.value)}.{module.attr.value}"
        return str(module)
    
    def _get_annotation_string(self, annotation) -> str:
        """Convert annotation to string"""
        if annotation and annotation.annotation:
            return str(annotation.annotation)
        return ""
    
    def _get_value_string(self, value) -> str:
        """Convert value node to string representation"""
        if isinstance(value, cst.Integer):
            return value.value
        elif isinstance(value, cst.SimpleString):
            return value.value
        elif isinstance(value, cst.Name):
            return value.value
        return str(value) if value else ""
    
    def extract(self, source_code: str) -> Dict[str, Any]:
        """
        Extract all components from source code.
        
        Returns:
            Dictionary containing all extracted components
        """
        try:
            # Parse the module
            module = cst.parse_module(source_code)
            
            # Count lines for statistics
            self.components['statistics']['total_lines'] = len(source_code.splitlines())
            
            # Visit the tree to extract components
            tree = module.visit(self)
            
            return self.components
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return self.components


def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Python file and extract all components"""
    print(f"\nAnalyzing: {file_path}")
    print("=" * 60)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        extractor = ComponentExtractor()
        components = extractor.extract(source_code)
        
        # Print summary
        print(f"\n📊 Component Summary:")
        print(f"  - Module docstring: {'Yes' if components['module_docstring'] else 'No'}")
        print(f"  - Imports: {len(components['imports'])}")
        print(f"  - Classes: {len(components['classes'])}")
        print(f"  - Standalone functions: {len(components['standalone_functions'])} {'⚠️' if components['standalone_functions'] else ''}")
        print(f"  - Global constants: {len(components['global_constants'])} {'⚠️' if components['global_constants'] else ''}")
        print(f"  - Global variables: {len(components['global_variables'])}")
        print(f"  - Type aliases: {len(components['type_aliases'])}")
        
        if components['classes']:
            print(f"\n📦 Classes found:")
            for cls in components['classes']:
                print(f"  - {cls['name']} ({len(cls['methods'])} methods)")
        
        if components['standalone_functions']:
            print(f"\n🎯 Standalone functions (Ghost Helpers):")
            for func in components['standalone_functions']:
                print(f"  - {func['name']}() {'async' if func['is_async'] else ''}")
        
        if components['global_constants']:
            print(f"\n📌 Global constants:")
            for const in components['global_constants']:
                print(f"  - {const['name']} = {const['value'][:30]}...")
        
        return components
        
    except Exception as e:
        print(f"❌ Failed to analyze file: {e}")
        return {}


def main():
    """Main entry point for testing the extractor"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="MAMS Phase 2: Component Extractor")
    parser.add_argument('file_path', nargs='?', help='Specific file to analyze')
    parser.add_argument('--output', type=str, default='/app/.migration/extraction_results.json', 
                      help='Output JSON file path')
    args = parser.parse_args()
    
    # Create output directory
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if args.file_path:
        # Analyze specific file
        file_path = Path(args.file_path)
        if file_path.exists():
            components = analyze_file(file_path)
            
            # Save results to JSON for inspection
            with open(output_file, 'w') as f:
                # Convert non-serializable nodes to strings
                json_safe = {
                    k: v for k, v in components.items() 
                    if k != 'node'
                }
                json.dump({'services': [json_safe]}, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {output_file}")
            
            # Mark phase 2 complete
            (output_file.parent / 'mams_phase2.complete').touch()
        else:
            print(f"File not found: {file_path}")
            sys.exit(1)
    else:
        # Test on a sample file
        print("Phase 2: Component Extraction Test")
        print("=" * 60)
        print("\nUsage: python component_extractor.py <path_to_file.py>")
        print("\nTesting on sample code...")
        
        sample_code = '''"""Module docstring"""
import os
from typing import Dict, List

DEFAULT_TIMEOUT = 30  # Global constant
db_connection = None  # Global variable

def helper_function(x: int) -> int:
    """A standalone helper function - Ghost Helper!"""
    return x * 2

class MyService:
    """Main service class"""
    
    def __init__(self):
        self.timeout = DEFAULT_TIMEOUT
    
    def process(self, data: List[str]) -> Dict:
        """Process some data"""
        result = helper_function(len(data))
        return {"count": result}

def another_helper():
    """Another Ghost Helper"""
    pass
'''
        
        extractor = ComponentExtractor()
        components = extractor.extract(sample_code)
        
        print(f"\n✅ Extraction successful!")
        print(f"Found {len(components['standalone_functions'])} Ghost Helpers")
        print(f"Found {len(components['global_constants'])} Global Constants")

if __name__ == "__main__":
    main()