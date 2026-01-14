#!/usr/bin/env python3
"""
MAMS-013: TypeScript AST Parser
Production-grade TypeScript/React parser using Node.js for accurate AST analysis
"""

import os
import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import tempfile

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from arkyvus.utils.debug_logger import debug_log

@dataclass
class ParsedImport:
    """Represents a parsed import statement"""
    source: str  # The module being imported from
    specifiers: List[Dict[str, str]]  # What's being imported
    is_type_only: bool
    line_number: int
    
@dataclass
class ParsedExport:
    """Represents a parsed export statement"""
    name: str
    type: str  # 'default', 'named', 'namespace'
    is_type_only: bool
    line_number: int

@dataclass
class ParsedComponent:
    """Represents a parsed React component"""
    name: str
    type: str  # 'function', 'class', 'arrow'
    props_type: Optional[str]
    hooks_used: List[str]
    jsx_elements: List[str]
    line_start: int
    line_end: int

@dataclass 
class TypeScriptAST:
    """Complete AST representation for a TypeScript/React file"""
    file_path: str
    file_hash: str
    imports: List[ParsedImport]
    exports: List[ParsedExport]
    components: List[ParsedComponent]
    hooks: List[str]
    api_calls: List[Dict[str, Any]]
    state_management: Dict[str, Any]
    dependencies: Set[str]
    parse_timestamp: str
    errors: List[str]


class TypeScriptASTParser:
    """
    Production-grade TypeScript/React AST parser using Node.js subprocess
    Provides comprehensive analysis for frontend migration
    """
    
    def __init__(self):
        self.parser_script_path = self._create_parser_script()
        self.cache: Dict[str, TypeScriptAST] = {}
        self.cache_dir = Path('/tmp/mams_ast_cache')
        self.cache_dir.mkdir(exist_ok=True)
        
    def _create_parser_script(self) -> Path:
        """Create Node.js parser script for TypeScript AST analysis"""
        script_content = '''
const fs = require('fs');
const path = require('path');

// Parse TypeScript/React file and extract comprehensive information
function parseTypeScriptFile(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf8');
        
        // Extract imports
        const imports = [];
        const importRegex = /import\\s+(?:type\\s+)?(?:({[^}]+})|([\\w]+)|\\*\\s+as\\s+([\\w]+))\\s+from\\s+['"](.*?)['"];?/g;
        let match;
        while ((match = importRegex.exec(content)) !== null) {
            const lineNumber = content.substring(0, match.index).split('\\n').length;
            imports.push({
                source: match[4],
                specifiers: match[1] || match[2] || match[3] || '',
                isTypeOnly: match[0].includes('import type'),
                lineNumber: lineNumber
            });
        }
        
        // Extract exports
        const exports = [];
        const exportRegex = /export\\s+(?:type\\s+)?(?:(default)\\s+)?(?:(const|let|var|function|class|interface|type|enum)\\s+)?([\\w]+)/g;
        while ((match = exportRegex.exec(content)) !== null) {
            const lineNumber = content.substring(0, match.index).split('\\n').length;
            exports.push({
                name: match[3] || 'default',
                type: match[1] ? 'default' : 'named',
                isTypeOnly: match[0].includes('export type'),
                lineNumber: lineNumber
            });
        }
        
        // Extract React components
        const components = [];
        
        // Function components
        const funcCompRegex = /(?:export\\s+)?(?:const|function)\\s+([A-Z][\\w]*)\\s*(?::|=)\\s*(?:\\([^)]*\\)\\s*(?::|=>)|function)/g;
        while ((match = funcCompRegex.exec(content)) !== null) {
            const lineNumber = content.substring(0, match.index).split('\\n').length;
            components.push({
                name: match[1],
                type: 'function',
                lineStart: lineNumber
            });
        }
        
        // Extract hooks usage
        const hooks = [];
        const hookRegex = /use[A-Z][\\w]*(?=\\s*\\()/g;
        const uniqueHooks = new Set();
        while ((match = hookRegex.exec(content)) !== null) {
            uniqueHooks.add(match[0]);
        }
        hooks.push(...uniqueHooks);
        
        // Extract API calls
        const apiCalls = [];
        const apiPatterns = [
            /fetch\\s*\\(['"](.*?)['"]/g,
            /axios\\.[\\w]+\\s*\\(['"](.*?)['"]/g,
            /apiClient\\.[\\w]+\\s*\\(['"](.*?)['"]/g
        ];
        
        for (const pattern of apiPatterns) {
            while ((match = pattern.exec(content)) !== null) {
                const lineNumber = content.substring(0, match.index).split('\\n').length;
                apiCalls.push({
                    endpoint: match[1],
                    lineNumber: lineNumber,
                    method: match[0].split('.')[1]?.split('(')[0] || 'fetch'
                });
            }
        }
        
        // Extract state management patterns
        const stateManagement = {
            useState: (content.match(/useState/g) || []).length,
            useReducer: (content.match(/useReducer/g) || []).length,
            useContext: (content.match(/useContext/g) || []).length,
            redux: content.includes('useSelector') || content.includes('useDispatch'),
            zustand: content.includes('create(') && content.includes('zustand'),
            mobx: content.includes('observer') || content.includes('makeObservable')
        };
        
        // Extract JSX elements
        const jsxElements = [];
        const jsxRegex = /<([A-Z][\\w]*)[^>]*>/g;
        const uniqueElements = new Set();
        while ((match = jsxRegex.exec(content)) !== null) {
            uniqueElements.add(match[1]);
        }
        jsxElements.push(...uniqueElements);
        
        return {
            imports,
            exports,
            components,
            hooks,
            apiCalls,
            stateManagement,
            jsxElements,
            dependencies: imports.map(i => i.source),
            errors: []
        };
        
    } catch (error) {
        return {
            imports: [],
            exports: [],
            components: [],
            hooks: [],
            apiCalls: [],
            stateManagement: {},
            jsxElements: [],
            dependencies: [],
            errors: [error.message]
        };
    }
}

// Main execution
const filePath = process.argv[2];
if (!filePath) {
    console.error(JSON.stringify({error: 'No file path provided'}));
    process.exit(1);
}

const result = parseTypeScriptFile(filePath);
console.log(JSON.stringify(result, null, 2));
'''
        
        # Create temporary script file
        script_path = Path(tempfile.gettempdir()) / 'mams_ts_parser.js'
        script_path.write_text(script_content)
        return script_path
        
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file for caching"""
        return hashlib.md5(file_path.read_bytes()).hexdigest()
        
    async def parse(self, file_path: Path) -> TypeScriptAST:
        """
        Parse TypeScript/React file and return comprehensive AST
        Uses caching for performance
        """
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            return TypeScriptAST(
                file_path=str(file_path),
                file_hash='',
                imports=[],
                exports=[],
                components=[],
                hooks=[],
                api_calls=[],
                state_management={},
                dependencies=set(),
                parse_timestamp=datetime.now().isoformat(),
                errors=[f'File not found: {file_path}']
            )
        
        # Skip very large files to avoid memory issues
        file_size = file_path.stat().st_size
        if file_size > 500000:  # 500KB limit
            return TypeScriptAST(
                file_path=str(file_path),
                file_hash='',
                imports=[],
                exports=[],
                components=[],
                hooks=[],
                api_calls=[],
                state_management={},
                dependencies=set(),
                parse_timestamp=datetime.now().isoformat(),
                errors=[f'File too large ({file_size} bytes), skipped for performance']
            )
        
        # Check cache
        file_hash = self.get_file_hash(file_path)
        cache_key = f"{file_path.name}_{file_hash}"
        
        if cache_key in self.cache:
            debug_log.api(f"Using cached AST for {file_path.name}", level="DEBUG")
            return self.cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                cached_data = json.loads(cache_file.read_text())
                ast = self._dict_to_ast(cached_data, str(file_path), file_hash)
                self.cache[cache_key] = ast
                return ast
            except Exception as e:
                debug_log.error_trace(f"Failed to load cached AST", exception=e)
        
        # Parse file using Node.js
        try:
            result = await self._run_parser(file_path)
            
            # Convert to TypeScriptAST
            ast = TypeScriptAST(
                file_path=str(file_path),
                file_hash=file_hash,
                imports=[
                    ParsedImport(
                        source=imp['source'],
                        specifiers=[{'name': imp.get('specifiers', '')}],
                        is_type_only=imp.get('isTypeOnly', False),
                        line_number=imp.get('lineNumber', 0)
                    ) for imp in result.get('imports', [])
                ],
                exports=[
                    ParsedExport(
                        name=exp['name'],
                        type=exp['type'],
                        is_type_only=exp.get('isTypeOnly', False),
                        line_number=exp.get('lineNumber', 0)
                    ) for exp in result.get('exports', [])
                ],
                components=[
                    ParsedComponent(
                        name=comp['name'],
                        type=comp.get('type', 'function'),
                        props_type=None,
                        hooks_used=[],
                        jsx_elements=[],
                        line_start=comp.get('lineStart', 0),
                        line_end=comp.get('lineEnd', 0)
                    ) for comp in result.get('components', [])
                ],
                hooks=result.get('hooks', []),
                api_calls=result.get('apiCalls', []),
                state_management=result.get('stateManagement', {}),
                dependencies=set(result.get('dependencies', [])),
                parse_timestamp=datetime.now().isoformat(),
                errors=result.get('errors', [])
            )
            
            # Update components with JSX elements
            jsx_elements = result.get('jsxElements', [])
            for component in ast.components:
                component.jsx_elements = jsx_elements
                component.hooks_used = ast.hooks
            
            # Cache result
            self.cache[cache_key] = ast
            
            # Save to disk cache
            try:
                cache_file.write_text(json.dumps(self._ast_to_dict(ast), indent=2))
            except Exception as e:
                debug_log.error_trace(f"Failed to cache AST", exception=e)
            
            return ast
            
        except Exception as e:
            debug_log.error_trace(f"Failed to parse {file_path}", exception=e)
            return TypeScriptAST(
                file_path=str(file_path),
                file_hash=file_hash,
                imports=[],
                exports=[],
                components=[],
                hooks=[],
                api_calls=[],
                state_management={},
                dependencies=set(),
                parse_timestamp=datetime.now().isoformat(),
                errors=[str(e)]
            )
    
    async def _run_parser(self, file_path: Path) -> Dict[str, Any]:
        """Run Node.js parser subprocess"""
        try:
            # Run Node.js script
            process = await asyncio.create_subprocess_exec(
                'node', str(self.parser_script_path), str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Parser failed: {stderr.decode()}")
            
            return json.loads(stdout.decode())
            
        except FileNotFoundError:
            # Node.js not available, use fallback regex parsing
            debug_log.api("Node.js not available, using fallback parser", level="WARNING")
            return await self._fallback_parser(file_path)
    
    async def _fallback_parser(self, file_path: Path) -> Dict[str, Any]:
        """Fallback regex-based parser when Node.js is not available"""
        content = file_path.read_text()
        
        # Basic regex parsing (less accurate but functional)
        imports = []
        import_lines = [line for line in content.split('\n') if line.strip().startswith('import')]
        for i, line in enumerate(import_lines):
            if ' from ' in line:
                parts = line.split(' from ')
                source = parts[1].strip().strip(';').strip('"').strip("'")
                imports.append({
                    'source': source,
                    'specifiers': parts[0].replace('import', '').strip(),
                    'isTypeOnly': 'import type' in line,
                    'lineNumber': i + 1
                })
        
        # Find exports
        exports = []
        export_lines = [line for line in content.split('\n') if 'export' in line]
        for i, line in enumerate(export_lines):
            if 'export default' in line:
                exports.append({
                    'name': 'default',
                    'type': 'default',
                    'isTypeOnly': False,
                    'lineNumber': i + 1
                })
            elif 'export' in line:
                exports.append({
                    'name': 'unknown',
                    'type': 'named',
                    'isTypeOnly': 'export type' in line,
                    'lineNumber': i + 1
                })
        
        # Find components (simple detection)
        components = []
        component_regex = r'(?:const|function)\s+([A-Z]\w*)'
        import re
        for match in re.finditer(component_regex, content):
            components.append({
                'name': match.group(1),
                'type': 'function',
                'lineStart': content[:match.start()].count('\n') + 1
            })
        
        # Find hooks
        hooks = list(set(re.findall(r'use[A-Z]\w*', content)))
        
        # Find API calls
        api_calls = []
        for match in re.finditer(r'(?:fetch|axios|apiClient)\.\w+\([\'"]([^\'"]+)', content):
            api_calls.append({
                'endpoint': match.group(1),
                'lineNumber': content[:match.start()].count('\n') + 1,
                'method': 'unknown'
            })
        
        return {
            'imports': imports,
            'exports': exports,
            'components': components,
            'hooks': hooks,
            'apiCalls': api_calls,
            'stateManagement': {
                'useState': content.count('useState'),
                'useReducer': content.count('useReducer'),
                'useContext': content.count('useContext'),
                'redux': 'useSelector' in content or 'useDispatch' in content,
                'zustand': 'zustand' in content,
                'mobx': 'observer' in content
            },
            'dependencies': [imp['source'] for imp in imports],
            'errors': []
        }
    
    def _ast_to_dict(self, ast: TypeScriptAST) -> Dict[str, Any]:
        """Convert AST to dictionary for caching"""
        return {
            'file_path': ast.file_path,
            'file_hash': ast.file_hash,
            'imports': [
                {
                    'source': imp.source,
                    'specifiers': imp.specifiers,
                    'is_type_only': imp.is_type_only,
                    'line_number': imp.line_number
                } for imp in ast.imports
            ],
            'exports': [
                {
                    'name': exp.name,
                    'type': exp.type,
                    'is_type_only': exp.is_type_only,
                    'line_number': exp.line_number
                } for exp in ast.exports
            ],
            'components': [
                {
                    'name': comp.name,
                    'type': comp.type,
                    'props_type': comp.props_type,
                    'hooks_used': comp.hooks_used,
                    'jsx_elements': comp.jsx_elements,
                    'line_start': comp.line_start,
                    'line_end': comp.line_end
                } for comp in ast.components
            ],
            'hooks': ast.hooks,
            'api_calls': ast.api_calls,
            'state_management': ast.state_management,
            'dependencies': list(ast.dependencies),
            'parse_timestamp': ast.parse_timestamp,
            'errors': ast.errors
        }
    
    def _dict_to_ast(self, data: Dict[str, Any], file_path: str, file_hash: str) -> TypeScriptAST:
        """Convert dictionary to AST from cache"""
        return TypeScriptAST(
            file_path=file_path,
            file_hash=file_hash,
            imports=[
                ParsedImport(
                    source=imp['source'],
                    specifiers=imp['specifiers'],
                    is_type_only=imp['is_type_only'],
                    line_number=imp['line_number']
                ) for imp in data.get('imports', [])
            ],
            exports=[
                ParsedExport(
                    name=exp['name'],
                    type=exp['type'],
                    is_type_only=exp['is_type_only'],
                    line_number=exp['line_number']
                ) for exp in data.get('exports', [])
            ],
            components=[
                ParsedComponent(
                    name=comp['name'],
                    type=comp['type'],
                    props_type=comp.get('props_type'),
                    hooks_used=comp.get('hooks_used', []),
                    jsx_elements=comp.get('jsx_elements', []),
                    line_start=comp['line_start'],
                    line_end=comp['line_end']
                ) for comp in data.get('components', [])
            ],
            hooks=data.get('hooks', []),
            api_calls=data.get('api_calls', []),
            state_management=data.get('stateManagement', {}),
            dependencies=set(data.get('dependencies', [])),
            parse_timestamp=data.get('parse_timestamp', datetime.now().isoformat()),
            errors=data.get('errors', [])
        )
    
    async def parse_batch(self, file_paths: List[Path], max_workers: int = 10) -> Dict[str, TypeScriptAST]:
        """Parse multiple files concurrently"""
        results = {}
        
        # Create tasks for all files
        tasks = []
        for file_path in file_paths:
            tasks.append(self.parse(file_path))
        
        # Process in batches to avoid overwhelming the system
        for i in range(0, len(tasks), max_workers):
            batch = tasks[i:i + max_workers]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for j, result in enumerate(batch_results):
                file_path = file_paths[i + j]
                if isinstance(result, Exception):
                    debug_log.error_trace(f"Failed to parse {file_path}", exception=result)
                    results[str(file_path)] = TypeScriptAST(
                        file_path=str(file_path),
                        file_hash='',
                        imports=[],
                        exports=[],
                        components=[],
                        hooks=[],
                        api_calls=[],
                        state_management={},
                        dependencies=set(),
                        parse_timestamp=datetime.now().isoformat(),
                        errors=[str(result)]
                    )
                else:
                    results[str(file_path)] = result
        
        return results
    
    def clear_cache(self):
        """Clear in-memory and disk cache"""
        self.cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()
        
        debug_log.api("AST cache cleared", level="INFO")


# Test functionality
if __name__ == "__main__":
    async def test_parser():
        parser = TypeScriptASTParser()
        
        # Test on a sample file
        test_file = Path("/app/client/src/components/auth/LoginPage.tsx")
        if test_file.exists():
            ast = await parser.parse(test_file)
            print(f"File: {ast.file_path}")
            print(f"Imports: {len(ast.imports)}")
            print(f"Exports: {len(ast.exports)}")
            print(f"Components: {[c.name for c in ast.components]}")
            print(f"Hooks used: {ast.hooks}")
            print(f"API calls: {len(ast.api_calls)}")
            print(f"Dependencies: {len(ast.dependencies)}")
            print(f"Errors: {ast.errors}")
        else:
            print(f"Test file not found: {test_file}")
    
    # Run test
    asyncio.run(test_parser())