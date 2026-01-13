"""
ARK-TOOLS Analysis Engine
=========================

Core analysis engine that integrates with MAMS components to analyze
codebases for patterns, duplicates, and consolidation opportunities.
"""

import os
import sys
import time
import importlib
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import ast
import logging

from ark_tools import config
from ark_tools.utils.debug_logger import debug_log

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """
    Core analysis engine integrating with MAMS components
    """
    
    def __init__(self):
        self.mams_components = {}
        self._load_mams_components()
        
        debug_log.analysis("Analysis Engine initialized with MAMS integration")
    
    def _load_mams_components(self) -> None:
        """Load MAMS components for code analysis"""
        try:
            # Ensure MAMS path is in Python path
            mams_path = config.MAMS_MIGRATIONS_PATH
            if os.path.exists(mams_path) and mams_path not in sys.path:
                sys.path.insert(0, mams_path)
            
            # Try to import MAMS components
            try:
                from extractors.component_extractor import ComponentExtractor
                self.mams_components['ComponentExtractor'] = ComponentExtractor
                debug_log.mams("Loaded ComponentExtractor from MAMS")
            except ImportError as e:
                debug_log.mams(f"Could not load ComponentExtractor: {e}", level="WARNING")
            
            try:
                from validators.dependency_validator import DependencyValidator  
                self.mams_components['DependencyValidator'] = DependencyValidator
                debug_log.mams("Loaded DependencyValidator from MAMS")
            except ImportError as e:
                debug_log.mams(f"Could not load DependencyValidator: {e}", level="WARNING")
            
            try:
                from analyzers.pattern_analyzer import PatternAnalyzer
                self.mams_components['PatternAnalyzer'] = PatternAnalyzer
                debug_log.mams("Loaded PatternAnalyzer from MAMS")
            except ImportError as e:
                debug_log.mams(f"Could not load PatternAnalyzer: {e}", level="WARNING")
            
        except Exception as e:
            debug_log.error_trace("Failed to load MAMS components", exception=e)
            # Continue without MAMS - use fallback analysis
    
    def analyze(
        self,
        directory: Union[str, Path],
        analysis_type: str = "comprehensive",
        analysis_id: str = None,
        output_dir: Optional[Path] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze codebase for patterns and consolidation opportunities
        
        Args:
            directory: Directory to analyze
            analysis_type: Type of analysis (quick, comprehensive, deep)
            analysis_id: Unique identifier for this analysis
            output_dir: Directory for analysis outputs
            **kwargs: Additional analysis parameters
            
        Returns:
            Dict containing comprehensive analysis results
        """
        start_time = time.time()
        directory = Path(directory)
        
        debug_log.analysis(f"Starting {analysis_type} analysis of {directory}")
        
        # Initialize results structure
        results = {
            'analysis_id': analysis_id,
            'analysis_type': analysis_type,
            'directory': str(directory),
            'timestamp': time.time(),
            'summary': {},
            'files_analyzed': [],
            'patterns_found': [],
            'duplicates_detected': [],
            'consolidation_opportunities': [],
            'recommendations': [],
            'metrics': {},
            'errors': []
        }
        
        try:
            # Phase 1: File Discovery
            debug_log.analysis("Phase 1: File Discovery")
            files_discovered = self._discover_files(directory, analysis_type)
            results['files_analyzed'] = files_discovered
            results['summary']['total_files'] = len(files_discovered)
            
            # Phase 2: Component Extraction
            debug_log.analysis("Phase 2: Component Extraction")
            if self.mams_components.get('ComponentExtractor'):
                components = self._extract_components_mams(files_discovered)
            else:
                components = self._extract_components_fallback(files_discovered)
            
            results['summary']['total_components'] = len(components)
            
            # Phase 3: Pattern Detection  
            debug_log.analysis("Phase 3: Pattern Detection")
            if self.mams_components.get('PatternAnalyzer'):
                patterns = self._detect_patterns_mams(components)
            else:
                patterns = self._detect_patterns_fallback(components)
            
            results['patterns_found'] = patterns
            results['summary']['patterns_found'] = len(patterns)
            
            # Phase 4: Duplicate Detection
            debug_log.analysis("Phase 4: Duplicate Detection")
            duplicates = self._detect_duplicates(components)
            results['duplicates_detected'] = duplicates
            results['summary']['duplicates_found'] = len(duplicates)
            
            # Phase 5: Consolidation Analysis
            debug_log.analysis("Phase 5: Consolidation Analysis") 
            opportunities = self._analyze_consolidation_opportunities(
                components, patterns, duplicates
            )
            results['consolidation_opportunities'] = opportunities
            
            # Phase 6: Generate Recommendations
            debug_log.analysis("Phase 6: Generate Recommendations")
            recommendations = self._generate_recommendations(results)
            results['recommendations'] = recommendations
            
            # Calculate metrics
            execution_time = time.time() - start_time
            results['metrics'] = {
                'execution_time_seconds': execution_time,
                'files_per_second': len(files_discovered) / execution_time if execution_time > 0 else 0,
                'components_per_file': len(components) / len(files_discovered) if files_discovered else 0,
                'duplicate_percentage': (len(duplicates) / len(components) * 100) if components else 0
            }
            
            debug_log.analysis(f"Analysis completed in {execution_time:.2f}s")
            
            return results
        
        except Exception as e:
            debug_log.error_trace(f"Analysis failed for {directory}", exception=e)
            results['errors'].append({
                'type': type(e).__name__,
                'message': str(e),
                'phase': 'analysis_execution'
            })
            return results
    
    def _discover_files(self, directory: Path, analysis_type: str) -> List[Dict[str, Any]]:
        """Discover files to analyze based on analysis type"""
        files_found = []
        
        # File extensions to analyze
        if analysis_type == "quick":
            extensions = ['.py']
            max_files = 50
        elif analysis_type == "comprehensive": 
            extensions = ['.py', '.js', '.ts', '.java', '.go']
            max_files = 500
        else:  # deep
            extensions = ['.py', '.js', '.ts', '.java', '.go', '.cpp', '.c', '.rb', '.php']
            max_files = None
        
        for ext in extensions:
            pattern = f"**/*{ext}"
            files = list(directory.rglob(pattern))
            
            for file_path in files:
                if max_files and len(files_found) >= max_files:
                    break
                
                try:
                    stat = file_path.stat()
                    files_found.append({
                        'path': str(file_path),
                        'size_bytes': stat.st_size,
                        'extension': ext,
                        'relative_path': str(file_path.relative_to(directory))
                    })
                except Exception as e:
                    debug_log.analysis(f"Error accessing file {file_path}: {e}", level="WARNING")
        
        return files_found
    
    def _extract_components_mams(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract components using MAMS ComponentExtractor"""
        components = []
        
        try:
            ComponentExtractor = self.mams_components['ComponentExtractor']
            extractor = ComponentExtractor()
            
            for file_info in files:
                file_path = file_info['path']
                
                try:
                    # Use MAMS component extraction
                    file_components = extractor.extract_from_file(file_path)
                    
                    for component in file_components:
                        components.append({
                            'id': f"{file_path}:{component.get('name', 'unknown')}",
                            'name': component.get('name'),
                            'type': component.get('type'),
                            'file_path': file_path,
                            'line_start': component.get('line_start'),
                            'line_end': component.get('line_end'),
                            'source_code': component.get('source_code'),
                            'dependencies': component.get('dependencies', []),
                            'complexity': component.get('complexity', 0),
                            'extracted_by': 'mams'
                        })
                
                except Exception as e:
                    debug_log.mams(f"MAMS extraction failed for {file_path}: {e}", level="WARNING")
        
        except Exception as e:
            debug_log.error_trace("MAMS component extraction failed", exception=e)
        
        return components
    
    def _extract_components_fallback(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback component extraction using AST"""
        components = []
        
        for file_info in files:
            file_path = file_info['path']
            
            if not file_path.endswith('.py'):
                continue  # Skip non-Python files in fallback mode
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        components.append({
                            'id': f"{file_path}:{node.name}",
                            'name': node.name,
                            'type': 'function',
                            'file_path': file_path,
                            'line_start': node.lineno,
                            'line_end': getattr(node, 'end_lineno', node.lineno),
                            'source_code': ast.unparse(node),
                            'dependencies': self._extract_dependencies_from_node(node),
                            'complexity': len(list(ast.walk(node))),
                            'extracted_by': 'fallback'
                        })
                    
                    elif isinstance(node, ast.ClassDef):
                        components.append({
                            'id': f"{file_path}:{node.name}",
                            'name': node.name,
                            'type': 'class',
                            'file_path': file_path,
                            'line_start': node.lineno,
                            'line_end': getattr(node, 'end_lineno', node.lineno),
                            'source_code': ast.unparse(node),
                            'dependencies': self._extract_dependencies_from_node(node),
                            'complexity': len(list(ast.walk(node))),
                            'extracted_by': 'fallback'
                        })
            
            except Exception as e:
                debug_log.analysis(f"Fallback extraction failed for {file_path}: {e}", level="WARNING")
        
        return components
    
    def _extract_dependencies_from_node(self, node: ast.AST) -> List[str]:
        """Extract dependencies from AST node"""
        dependencies = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                dependencies.append(child.id)
            elif isinstance(child, ast.Attribute):
                dependencies.append(ast.unparse(child))
        
        return list(set(dependencies))  # Remove duplicates
    
    def _detect_patterns_mams(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns using MAMS PatternAnalyzer"""
        patterns = []
        
        try:
            PatternAnalyzer = self.mams_components['PatternAnalyzer']
            analyzer = PatternAnalyzer()
            
            # Group components for pattern analysis
            detected_patterns = analyzer.analyze_patterns(components)
            
            for pattern in detected_patterns:
                patterns.append({
                    'id': pattern.get('id'),
                    'name': pattern.get('name'),
                    'type': pattern.get('type'),
                    'components': pattern.get('components', []),
                    'frequency': len(pattern.get('components', [])),
                    'confidence': pattern.get('confidence', 0.0),
                    'detected_by': 'mams'
                })
        
        except Exception as e:
            debug_log.error_trace("MAMS pattern detection failed", exception=e)
        
        return patterns
    
    def _detect_patterns_fallback(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback pattern detection"""
        patterns = []
        
        # Group by component type
        type_groups = {}
        for component in components:
            comp_type = component.get('type', 'unknown')
            if comp_type not in type_groups:
                type_groups[comp_type] = []
            type_groups[comp_type].append(component)
        
        # Create patterns for each type with multiple instances
        for comp_type, comps in type_groups.items():
            if len(comps) > 1:
                patterns.append({
                    'id': f"pattern_{comp_type}",
                    'name': f"{comp_type.title()} Pattern",
                    'type': comp_type,
                    'components': [c['id'] for c in comps],
                    'frequency': len(comps),
                    'confidence': min(0.8, len(comps) / 10),  # Higher confidence with more instances
                    'detected_by': 'fallback'
                })
        
        return patterns
    
    def _detect_duplicates(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect near-duplicate components"""
        duplicates = []
        
        # Simple similarity detection based on component names and types
        seen_components = {}
        
        for component in components:
            name = component.get('name', '')
            comp_type = component.get('type', '')
            source = component.get('source_code', '')
            
            # Create a simple signature
            signature = f"{comp_type}_{name}_{len(source)}"
            
            if signature in seen_components:
                # Found potential duplicate
                original = seen_components[signature]
                similarity = self._calculate_similarity(original, component)
                
                if similarity > 0.85:  # 85% similarity threshold
                    duplicates.append({
                        'id': f"dup_{len(duplicates)}",
                        'original_component': original['id'],
                        'duplicate_component': component['id'],
                        'similarity_score': similarity,
                        'type': 'near_duplicate',
                        'consolidation_potential': 'high' if similarity > 0.95 else 'medium'
                    })
            else:
                seen_components[signature] = component
        
        return duplicates
    
    def _calculate_similarity(self, comp1: Dict[str, Any], comp2: Dict[str, Any]) -> float:
        """Calculate similarity between two components"""
        # Simple similarity calculation
        name1 = comp1.get('name', '')
        name2 = comp2.get('name', '')
        
        # Name similarity
        name_sim = 1.0 if name1 == name2 else 0.5
        
        # Type similarity
        type_sim = 1.0 if comp1.get('type') == comp2.get('type') else 0.0
        
        # Size similarity (based on source code length)
        size1 = len(comp1.get('source_code', ''))
        size2 = len(comp2.get('source_code', ''))
        
        if size1 == 0 and size2 == 0:
            size_sim = 1.0
        elif size1 == 0 or size2 == 0:
            size_sim = 0.0
        else:
            size_ratio = min(size1, size2) / max(size1, size2)
            size_sim = size_ratio
        
        # Weighted average
        similarity = (name_sim * 0.4 + type_sim * 0.3 + size_sim * 0.3)
        return similarity
    
    def _analyze_consolidation_opportunities(
        self,
        components: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]], 
        duplicates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze consolidation opportunities"""
        opportunities = []
        
        # Opportunities from duplicates
        for duplicate in duplicates:
            if duplicate['consolidation_potential'] in ['high', 'medium']:
                opportunities.append({
                    'id': f"opp_dup_{len(opportunities)}",
                    'type': 'duplicate_consolidation',
                    'priority': 'high' if duplicate['similarity_score'] > 0.95 else 'medium',
                    'description': f"Consolidate near-duplicate components with {duplicate['similarity_score']:.1%} similarity",
                    'components_involved': [
                        duplicate['original_component'],
                        duplicate['duplicate_component']
                    ],
                    'estimated_reduction': f"{(duplicate['similarity_score'] * 100):.0f}%",
                    'effort_level': 'low' if duplicate['similarity_score'] > 0.95 else 'medium'
                })
        
        # Opportunities from patterns
        for pattern in patterns:
            if pattern['frequency'] > 3:  # Pattern appears more than 3 times
                opportunities.append({
                    'id': f"opp_pattern_{len(opportunities)}",
                    'type': 'pattern_consolidation',
                    'priority': 'medium',
                    'description': f"Consolidate {pattern['frequency']} instances of {pattern['name']}",
                    'components_involved': pattern['components'],
                    'estimated_reduction': f"{min(75, pattern['frequency'] * 10)}%",
                    'effort_level': 'medium'
                })
        
        return opportunities
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # High-level summary recommendations
        total_files = results['summary'].get('total_files', 0)
        total_duplicates = results['summary'].get('duplicates_found', 0)
        
        if total_duplicates > 0:
            duplicate_percentage = (total_duplicates / results['summary'].get('total_components', 1)) * 100
            
            if duplicate_percentage > 20:
                recommendations.append({
                    'priority': 'high',
                    'type': 'duplication',
                    'message': f"High duplication detected ({duplicate_percentage:.1f}%) - prioritize consolidation",
                    'action': 'Start with highest similarity duplicates first'
                })
            elif duplicate_percentage > 10:
                recommendations.append({
                    'priority': 'medium',
                    'type': 'duplication', 
                    'message': f"Moderate duplication found ({duplicate_percentage:.1f}%) - consider consolidation",
                    'action': 'Review duplicate pairs for consolidation opportunities'
                })
        
        # Pattern-based recommendations
        patterns_found = len(results.get('patterns_found', []))
        if patterns_found > 5:
            recommendations.append({
                'priority': 'medium',
                'type': 'patterns',
                'message': f"Multiple patterns detected ({patterns_found}) - opportunities for standardization",
                'action': 'Create reusable components for common patterns'
            })
        
        # File organization recommendations  
        if total_files > 100:
            recommendations.append({
                'priority': 'low',
                'type': 'organization',
                'message': f"Large codebase ({total_files} files) - consider modular organization",
                'action': 'Group related files into logical modules'
            })
        
        return recommendations