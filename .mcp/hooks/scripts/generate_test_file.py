#!/usr/bin/env python3
"""
ARK-TOOLS Test File Generator
Automatically generates test files for new service modules
"""

import sys
import os
import json
import re
import ast
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestFileGenerator:
    """Generates comprehensive test files for service modules"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.template_dir = Path(config.get('template_dir', 'templates/tests'))
        self.output_dir = Path(config.get('output_dir', 'ark-tools/tests/unit'))
        self.naming_pattern = config.get('naming_pattern', 'test_{module_name}.py')
    
    def generate_test_file(self, service_file: str) -> Dict[str, Any]:
        """
        Generate test file for a service module
        
        Args:
            service_file: Path to the service file
            
        Returns:
            Dict with generation result
        """
        
        result = {
            'success': False,
            'test_file': None,
            'error': None,
            'tests_generated': 0
        }
        
        try:
            # Extract service information
            service_info = self._analyze_service_file(service_file)
            
            if not service_info:
                result['error'] = f"Could not analyze service file: {service_file}"
                return result
            
            # Generate test content
            test_content = self._generate_test_content(service_info)
            
            # Determine output file path
            module_name = service_info['module_name']
            test_filename = self.naming_pattern.format(module_name=module_name)
            test_file_path = self.output_dir / test_filename
            
            # Ensure output directory exists
            test_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write test file
            with open(test_file_path, 'w') as f:
                f.write(test_content)
            
            result.update({
                'success': True,
                'test_file': str(test_file_path),
                'tests_generated': len(service_info['methods']),
                'service_analyzed': service_info
            })
            
            logger.info(f"Generated test file: {test_file_path}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error generating test file for {service_file}: {e}")
        
        return result
    
    def _analyze_service_file(self, service_file: str) -> Optional[Dict[str, Any]]:
        """Analyze service file to extract testable components"""
        
        try:
            with open(service_file, 'r') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract module information
            module_name = Path(service_file).stem
            
            service_info = {
                'module_name': module_name,
                'file_path': service_file,
                'classes': [],
                'methods': [],
                'functions': [],
                'imports': []
            }
            
            # Visit AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node)
                    service_info['classes'].append(class_info)
                    service_info['methods'].extend(class_info['methods'])
                
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    # Top-level function
                    func_info = self._extract_function_info(node)
                    service_info['functions'].append(func_info)
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_info = self._extract_import_info(node)
                    service_info['imports'].append(import_info)
            
            return service_info
            
        except Exception as e:
            logger.error(f"Error analyzing service file {service_file}: {e}")
            return None
    
    def _extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract class information from AST node"""
        
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'methods': [],
            'is_service': 'Service' in node.name
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_function_info(item, is_method=True)
                class_info['methods'].append(method_info)
        
        return class_info
    
    def _extract_function_info(self, node: ast.FunctionDef, is_method: bool = False) -> Dict[str, Any]:
        """Extract function/method information from AST node"""
        
        func_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'args': [arg.arg for arg in node.args.args],
            'returns': None,
            'is_method': is_method,
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
            'raises_exceptions': self._extract_exceptions(node)
        }
        
        # Extract return type annotation
        if node.returns:
            func_info['returns'] = ast.unparse(node.returns)
        
        return func_info
    
    def _extract_import_info(self, node) -> Dict[str, Any]:
        """Extract import information"""
        
        if isinstance(node, ast.Import):
            return {
                'type': 'import',
                'modules': [alias.name for alias in node.names]
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                'type': 'from_import',
                'module': node.module,
                'names': [alias.name for alias in node.names]
            }
    
    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name from AST node"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{ast.unparse(decorator.value)}.{decorator.attr}"
        else:
            return ast.unparse(decorator)
    
    def _extract_exceptions(self, node: ast.FunctionDef) -> List[str]:
        """Extract exceptions that function might raise"""
        
        exceptions = []
        
        for item in ast.walk(node):
            if isinstance(item, ast.Raise):
                if item.exc:
                    if isinstance(item.exc, ast.Name):
                        exceptions.append(item.exc.id)
                    elif isinstance(item.exc, ast.Call) and isinstance(item.exc.func, ast.Name):
                        exceptions.append(item.exc.func.id)
        
        return list(set(exceptions))
    
    def _generate_test_content(self, service_info: Dict[str, Any]) -> str:
        """Generate comprehensive test content"""
        
        lines = []
        
        # Header
        lines.extend([
            f'"""Unit tests for {service_info["module_name"]} module"""',
            '',
            '# Generated automatically by ARK-TOOLS',
            f'# Source: {service_info["file_path"]}',
            f'# Generated: {datetime.now().isoformat()}',
            '',
            'import pytest',
            'from unittest.mock import Mock, patch, MagicMock',
            'from uuid import uuid4',
            'from datetime import datetime',
            '',
        ])
        
        # Add specific imports based on service analysis
        lines.extend(self._generate_imports(service_info))
        lines.append('')
        
        # Generate test classes for each service class
        for class_info in service_info['classes']:
            if class_info['is_service']:
                lines.extend(self._generate_service_test_class(class_info, service_info))
                lines.append('')
        
        # Generate tests for standalone functions
        if service_info['functions']:
            lines.extend(self._generate_function_tests(service_info['functions'], service_info))
        
        return '\n'.join(lines)
    
    def _generate_imports(self, service_info: Dict[str, Any]) -> List[str]:
        """Generate import statements for tests"""
        
        lines = []
        module_name = service_info['module_name']
        
        # Import the module under test
        if service_info['classes']:
            class_names = [cls['name'] for cls in service_info['classes']]
            lines.append(f'from ark_tools.core.{module_name} import {", ".join(class_names)}')
        
        # Import database models if used
        if any('session' in method['args'] for cls in service_info['classes'] for method in cls['methods']):
            lines.append('from ark_tools.database.models.base import DatabaseManager')
        
        # Import specific models based on service name
        if 'project' in module_name.lower():
            lines.append('from ark_tools.database.models.project import Project')
        
        return lines
    
    def _generate_service_test_class(self, class_info: Dict[str, Any], service_info: Dict[str, Any]) -> List[str]:
        """Generate test class for a service class"""
        
        lines = []
        class_name = class_info['name']
        test_class_name = f'Test{class_name}'
        
        lines.extend([
            f'class {test_class_name}:',
            f'    """Test suite for {class_name}"""',
            '',
            '    @pytest.fixture',
            '    def mock_session(self):',
            '        """Create mock database session"""',
            '        return Mock()',
            '',
            '    @pytest.fixture',
            f'    def service(self, mock_session):',
            f'        """Create {class_name} instance with mock session"""',
            f'        return {class_name}(mock_session)',
            ''
        ])
        
        # Generate test methods
        for method in class_info['methods']:
            if not method['name'].startswith('_'):  # Skip private methods
                lines.extend(self._generate_method_test(method, class_info, service_info))
                lines.append('')
        
        return lines
    
    def _generate_method_test(self, method: Dict[str, Any], class_info: Dict[str, Any], service_info: Dict[str, Any]) -> List[str]:
        """Generate test for a service method"""
        
        lines = []
        method_name = method['name']
        test_name = f'test_{method_name}'
        
        # Happy path test
        lines.extend([
            f'    def {test_name}_success(self, service, mock_session):',
            f'        """Test successful {method_name}"""',
            '        # Arrange',
        ])
        
        # Generate test data based on method name and args
        test_data = self._generate_test_data(method)
        lines.extend([f'        {line}' for line in test_data])
        
        lines.extend([
            '',
            '        # Act',
            f'        result = service.{method_name}({self._generate_method_call_args(method)})',
            '',
            '        # Assert',
            '        assert result is not None',
        ])
        
        # Add specific assertions based on method type
        if 'create' in method_name.lower():
            lines.append('        mock_session.add.assert_called_once()')
            lines.append('        mock_session.commit.assert_called_once()')
        elif 'delete' in method_name.lower():
            lines.append('        mock_session.delete.assert_called_once()')
            lines.append('        mock_session.commit.assert_called_once()')
        elif 'update' in method_name.lower():
            lines.append('        mock_session.commit.assert_called_once()')
        
        # Error case test
        if method['raises_exceptions']:
            lines.extend([
                '',
                f'    def {test_name}_error(self, service, mock_session):',
                f'        """Test {method_name} error handling"""',
                '        # Arrange',
                '        mock_session.query.side_effect = Exception("Database error")',
                '',
                '        # Act & Assert',
                f'        with pytest.raises(Exception):',
                f'            service.{method_name}({self._generate_method_call_args(method)})'
            ])
        
        return lines
    
    def _generate_test_data(self, method: Dict[str, Any]) -> List[str]:
        """Generate test data for method arguments"""
        
        lines = []
        
        for arg in method['args']:
            if arg == 'self':
                continue
            elif 'id' in arg.lower():
                lines.append(f'{arg} = uuid4()')
            elif arg == 'data':
                lines.append(f'{arg} = {{"test_key": "test_value"}}')
            elif arg in ['name', 'description']:
                lines.append(f'{arg} = "test_{arg}"')
            elif arg == 'session':
                continue  # Handled by fixture
            else:
                lines.append(f'{arg} = Mock()')
        
        return lines
    
    def _generate_method_call_args(self, method: Dict[str, Any]) -> str:
        """Generate method call arguments for tests"""
        
        args = []
        
        for arg in method['args']:
            if arg not in ['self', 'session']:
                args.append(arg)
        
        return ', '.join(args)
    
    def _generate_function_tests(self, functions: List[Dict[str, Any]], service_info: Dict[str, Any]) -> List[str]:
        """Generate tests for standalone functions"""
        
        lines = []
        
        for function in functions:
            if not function['name'].startswith('_'):  # Skip private functions
                lines.extend([
                    f'def test_{function["name"]}():',
                    f'    """Test {function["name"]} function"""',
                    '    # TODO: Implement test for standalone function',
                    '    pass',
                    ''
                ])
        
        return lines

def main():
    """Main function called by MCP hooks"""
    
    if len(sys.argv) < 2:
        logger.error("Usage: generate_test_file.py <service_file>")
        sys.exit(1)
    
    service_file = sys.argv[1]
    
    # Load configuration
    config_file = Path(__file__).parent.parent / 'config.json'
    try:
        with open(config_file, 'r') as f:
            full_config = json.load(f)
            config = full_config.get('custom_handlers', {}).get('generate_test_file', {}).get('config', {})
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        config = {
            'template_dir': 'templates/tests',
            'output_dir': 'ark-tools/tests/unit',
            'naming_pattern': 'test_{module_name}.py'
        }
    
    # Check if test file already exists
    module_name = Path(service_file).stem
    test_filename = config.get('naming_pattern', 'test_{module_name}.py').format(module_name=module_name)
    test_file_path = Path(config.get('output_dir', 'ark-tools/tests/unit')) / test_filename
    
    if test_file_path.exists():
        logger.info(f"Test file already exists: {test_file_path}")
        print(f"✅ Test file already exists: {test_file_path}")
        sys.exit(0)
    
    # Generate test file
    generator = TestFileGenerator(config)
    result = generator.generate_test_file(service_file)
    
    if result['success']:
        print(f"✅ Generated test file: {result['test_file']}")
        print(f"📊 Tests generated: {result['tests_generated']}")
        sys.exit(0)
    else:
        print(f"❌ Failed to generate test file: {result['error']}")
        sys.exit(1)

if __name__ == '__main__':
    main()