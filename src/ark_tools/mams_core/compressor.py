"""
Context Compression Module
==========================

Compresses code to semantic skeletons using AST parsing.
Reduces token usage by ~80% while preserving meaning for LLM analysis.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ark_tools.utils.debug_logger import debug_log


class CodeCompressor:
    """
    Compresses code to semantic skeleton using AST parsing.
    Reduces token usage by ~80% while preserving meaning.
    """
    
    def __init__(self, max_docstring_length: int = 50, max_methods_per_class: int = 10):
        """
        Initialize the code compressor.
        
        Args:
            max_docstring_length: Maximum characters to keep from docstrings
            max_methods_per_class: Maximum methods to show per class
        """
        self.max_docstring_length = max_docstring_length
        self.max_methods_per_class = max_methods_per_class
        self.supported_extensions = {'.py', '.pyx', '.pyi'}
        
    def compress_file(self, file_path: Path) -> str:
        """
        Extract semantic skeleton from Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Compressed code skeleton as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            skeleton = self._extract_skeleton(tree, file_path.name)
            
            debug_log.mams(f"Compressed {file_path.name}: {len(content)} -> {len(skeleton)} chars", level="DEBUG")
            return skeleton
            
        except SyntaxError as e:
            debug_log.error_trace(f"Syntax error in {file_path}", exception=e)
            return f"# Syntax error in {file_path.name}: {str(e)}"
        except Exception as e:
            debug_log.error_trace(f"Compression failed for {file_path}", exception=e)
            return f"# Error processing {file_path.name}"
    
    def _extract_skeleton(self, tree: ast.AST, filename: str) -> str:
        """Extract skeleton from AST."""
        skeleton_parts = []
        
        # Add file-level docstring if exists
        if ast.get_docstring(tree):
            doc = ast.get_docstring(tree)
            skeleton_parts.append(f'"""{doc[:self.max_docstring_length]}..."""' if len(doc) > self.max_docstring_length else f'"""{doc}"""')
        
        # Process imports
        imports = self._extract_imports(tree)
        if imports:
            skeleton_parts.extend(imports)
            skeleton_parts.append("")  # Empty line after imports
        
        # Process top-level elements
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.col_offset == 0:
                skeleton_parts.append(self._compress_class(node))
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                skeleton_parts.append(self._compress_function(node))
            elif isinstance(node, ast.AsyncFunctionDef) and node.col_offset == 0:
                skeleton_parts.append(self._compress_function(node, is_async=True))
        
        return "\n".join(skeleton_parts)
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")
        return imports[:10]  # Limit to first 10 imports
    
    def _compress_class(self, node: ast.ClassDef) -> str:
        """Compress class definition."""
        parts = []
        
        # Class declaration with bases
        bases = ", ".join([self._get_name(base) for base in node.bases])
        class_def = f"class {node.name}({bases}):" if bases else f"class {node.name}:"
        parts.append(class_def)
        
        # Add docstring
        docstring = ast.get_docstring(node)
        if docstring:
            doc_summary = docstring.split('\n')[0][:self.max_docstring_length]
            parts.append(f'    """{doc_summary}"""')
        
        # Extract method signatures
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_async = isinstance(item, ast.AsyncFunctionDef)
                method_sig = self._get_method_signature(item, is_async)
                methods.append(f"    {method_sig}")
        
        # Limit methods shown
        if methods:
            parts.extend(methods[:self.max_methods_per_class])
            if len(methods) > self.max_methods_per_class:
                parts.append(f"    # ... +{len(methods) - self.max_methods_per_class} more methods")
        else:
            parts.append("    pass")
        
        return "\n".join(parts)
    
    def _compress_function(self, node: ast.FunctionDef, is_async: bool = False) -> str:
        """Compress function definition."""
        sig = self._get_method_signature(node, is_async)
        docstring = ast.get_docstring(node)
        
        if docstring:
            doc_summary = docstring.split('\n')[0][:self.max_docstring_length]
            return f"{sig}\n    '''{doc_summary}'''"
        else:
            return sig
    
    def _get_method_signature(self, node: ast.FunctionDef, is_async: bool = False) -> str:
        """Extract method signature."""
        # Get arguments
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            if arg.annotation:
                arg_type = self._get_annotation(arg.annotation)
                args.append(f"{arg_name}: {arg_type}")
            else:
                args.append(arg_name)
        
        # Limit arguments shown
        if len(args) > 5:
            args = args[:3] + ["..."] + args[-1:]
        
        # Get return type
        returns = ""
        if node.returns:
            returns = f" -> {self._get_annotation(node.returns)}"
        
        # Build signature
        prefix = "async def" if is_async else "def"
        return f"{prefix} {node.name}({', '.join(args)}){returns}:"
    
    def _get_annotation(self, annotation) -> str:
        """Extract type annotation as string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return repr(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            return f"{self._get_name(annotation.value)}[...]"
        else:
            return "Any"
    
    def _get_name(self, node) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return "object"
    
    def compress_directory(
        self, 
        directory: Path, 
        max_files: int = 50,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Compress top N most complex files in directory.
        
        Args:
            directory: Directory to analyze
            max_files: Maximum number of files to compress
            exclude_patterns: Patterns to exclude (e.g., ['test_', '__pycache__'])
            
        Returns:
            Dictionary mapping file paths to compressed skeletons
        """
        exclude_patterns = exclude_patterns or ['test_', '__pycache__', '.git', 'node_modules']
        results = {}
        
        # Find Python files
        py_files = []
        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    if not any(p in file for p in exclude_patterns):
                        py_files.append(Path(root) / file)
        
        # Sort by size (proxy for complexity)
        py_files.sort(key=lambda f: f.stat().st_size, reverse=True)
        
        # Compress top N files
        for file_path in py_files[:max_files]:
            try:
                compressed = self.compress_file(file_path)
                if compressed and not compressed.startswith("# Error"):
                    relative_path = file_path.relative_to(directory)
                    results[str(relative_path)] = compressed
            except Exception as e:
                debug_log.error_trace(f"Failed to compress {file_path}", exception=e)
                continue
        
        # Log statistics
        total_chars = sum(len(v) for v in results.values())
        debug_log.agent(
            f"Compressed {len(results)} files from {directory.name}, "
            f"~{total_chars // 4} tokens (estimated)"
        )
        
        return results
    
    def create_analysis_prompt(self, compressed_code: Dict[str, str]) -> str:
        """
        Create a formatted prompt for LLM analysis.
        
        Args:
            compressed_code: Dictionary of file paths to compressed skeletons
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for file_path, skeleton in compressed_code.items():
            prompt_parts.append(f"# File: {file_path}")
            prompt_parts.append(skeleton)
            prompt_parts.append("")  # Empty line between files
        
        return "\n".join(prompt_parts)