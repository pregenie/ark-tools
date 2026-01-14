# ARK-TOOLS Technical Reference

## Table of Contents

1. [Core APIs](#core-apis)
2. [Agent System](#agent-system)
3. [MAMS Core](#mams-core)
4. [LLM Engine](#llm-engine)
5. [Context Compression](#context-compression)
6. [Reporting System](#reporting-system)
7. [Data Models](#data-models)
8. [Error Handling](#error-handling)
9. [Performance Metrics](#performance-metrics)
10. [Extension Development](#extension-development)

## Core APIs

### ArchitectAgent API

The central orchestrator for hybrid analysis operations.

```python
from ark_tools.agents.architect import ArchitectAgent

# Initialize agent
agent = ArchitectAgent(config={
    'llm_model_path': '/path/to/model.gguf',
    'context_size': 8192,
    'max_tokens': 2048,
    'threads': 4,
    'temperature': 0.1
})

# Execute operations
result = await agent.execute_operation(
    operation_name='perform_hybrid_analysis',
    parameters={
        'directory': '/path/to/code',
        'strategy': 'hybrid',  # or 'fast', 'deep', 'compress_only'
        'max_files': 50
    }
)
```

#### Available Operations

##### perform_hybrid_analysis
Performs complete hybrid MAMS/LLM analysis.

**Parameters:**
- `directory` (str): Path to codebase
- `strategy` (str): Analysis strategy
- `max_files` (int): Maximum files to analyze

**Returns:**
```python
{
    'structure': Dict,      # MAMS structural data
    'domains': List[Dict],  # Discovered domains
    'timing': Dict,         # Performance metrics
    'confidence': float,    # Overall confidence
    'suggestions': List     # Optional suggestions
}
```

##### analyze_semantic_domains
Analyzes code for semantic domains using LLM.

**Parameters:**
- `directory` (str, optional): Path to code
- `code_skeleton` (str, optional): Pre-compressed code
- `context` (str): Additional context
- `include_intent` (bool): Include intent analysis

**Returns:**
```python
[
    {
        'name': str,
        'description': str,
        'primary_components': List[str],
        'relationships': List[Dict],
        'confidence': float
    }
]
```

##### suggest_code_organization
Generates code organization suggestions.

**Parameters:**
- `domains` (List[Dict]): Discovered domains
- `structure` (Dict): Structural analysis

**Returns:**
```python
{
    'suggestions': List[Dict],
    'total_suggestions': int,
    'estimated_impact': float
}
```

## Agent System

### BaseAgent Abstract Class

All agents inherit from this base class.

```python
from ark_tools.agents.base import BaseAgent, OperationResult

class CustomAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.register_operations()
    
    def register_operations(self):
        self.operations = {
            'custom_operation': self._custom_operation
        }
    
    async def _custom_operation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        return {'result': 'data'}
```

### OperationResult Class

Standard result format for all operations.

```python
@dataclass
class OperationResult:
    success: bool
    operation_id: str
    operation_name: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
```

## MAMS Core

### FileDiscoveryAgent

Discovers and categorizes files in a codebase.

```python
from ark_tools.mams_core.discovery import FileDiscoveryAgent

agent = FileDiscoveryAgent()
result = await agent.execute_operation(
    'discover_files',
    {
        'directory': '/path/to/code',
        'exclude_patterns': ['*.pyc', '__pycache__'],
        'max_files': 100
    }
)
```

### ValidationAgent

Validates code compatibility and dependencies.

```python
from ark_tools.mams_core.validation import ValidationAgent

agent = ValidationAgent()
result = await agent.execute_operation(
    'validate_codebase',
    {
        'files': discovered_files,
        'check_dependencies': True
    }
)
```

### ExtractionAgent

Extracts components from code files.

```python
from ark_tools.mams_core.extraction import ExtractionAgent

agent = ExtractionAgent()
result = await agent.execute_operation(
    'extract_components',
    {
        'files': validated_files,
        'extract_types': ['classes', 'functions', 'constants']
    }
)
```

### CodeCompressor

Compresses code to AST skeletons for LLM processing.

```python
from ark_tools.mams_core.compressor import CodeCompressor

compressor = CodeCompressor()

# Compress single file
compressed = compressor.compress_file(Path('file.py'))

# Compress directory
compressed_files = compressor.compress_directory(
    Path('/path/to/code'),
    max_files=50,
    exclude_patterns=['test_*']
)
```

#### Compression Algorithm

```python
def compress_python_file(self, file_path: Path) -> str:
    """
    Reduces Python code to semantic skeleton:
    1. Parse AST
    2. Extract signatures
    3. Remove implementation details
    4. Preserve structure
    """
    tree = ast.parse(content)
    skeleton = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Extract class signature
            skeleton.append(f"class {node.name}:")
            for method in node.body:
                if isinstance(method, ast.FunctionDef):
                    skeleton.append(f"    def {method.name}(...): pass")
        elif isinstance(node, ast.FunctionDef):
            # Extract function signature
            skeleton.append(f"def {node.name}(...): pass")
    
    return '\n'.join(skeleton)
```

## LLM Engine

### LLMAnalysisEngine

Manages LLM inference for semantic analysis.

```python
from ark_tools.llm_engine.engine import LLMAnalysisEngine

engine = LLMAnalysisEngine(config={
    'model_path': '/path/to/model.gguf',
    'context_size': 8192,
    'max_tokens': 2048,
    'threads': 4,
    'temperature': 0.1
})

# Analyze domains
domains = await engine.analyze_domain_semantics(
    code_skeleton="compressed code here",
    context="Optional context"
)

# Analyze intent
intent = await engine.analyze_code_intent(
    code_skeleton="compressed code here"
)
```

### Model Loading

```python
from llama_cpp import Llama

class LLMAnalysisEngine:
    def _initialize_model(self):
        self.model = Llama(
            model_path=self.config['model_path'],
            n_ctx=self.config['context_size'],
            n_threads=self.config['threads'],
            n_gpu_layers=32 if self.config.get('gpu_enabled') else 0,
            verbose=False
        )
```

### Non-Blocking Inference

```python
async def analyze_domain_semantics(self, code_skeleton: str) -> Dict[str, Any]:
    loop = asyncio.get_event_loop()
    
    def _run_inference():
        prompt = self._build_domain_prompt(code_skeleton)
        response = self.model(
            prompt,
            max_tokens=self.config['max_tokens'],
            temperature=self.config['temperature'],
            stop=["```", "\n\n"]
        )
        return response['choices'][0]['text']
    
    # Run in thread pool to avoid blocking
    result_text = await loop.run_in_executor(
        self._executor,
        _run_inference
    )
    
    return self._parse_llm_response(result_text)
```

## Context Compression

### Compression Strategies

#### AST-Based Compression
```python
class ASTCompressor:
    def compress(self, code: str) -> str:
        """
        Compression ratio: ~80%
        Preserves: Structure, signatures, relationships
        Removes: Implementation, comments, docstrings
        """
        tree = ast.parse(code)
        return self.extract_skeleton(tree)
```

#### Token Optimization
```python
class TokenOptimizer:
    def optimize(self, compressed: str) -> str:
        """
        Further reduces tokens:
        - Short variable names
        - Remove optional syntax
        - Compress whitespace
        """
        optimized = re.sub(r'\s+', ' ', compressed)
        return optimized.strip()
```

### File Complexity Scoring

```python
def calculate_complexity(file_path: Path) -> float:
    """
    Calculate file complexity for prioritization.
    Higher scores = more important for analysis.
    """
    content = file_path.read_text()
    
    # Count complexity indicators
    class_count = len(re.findall(r'^class\s+', content, re.MULTILINE))
    function_count = len(re.findall(r'^def\s+', content, re.MULTILINE))
    import_count = len(re.findall(r'^import\s+', content, re.MULTILINE))
    line_count = len(content.splitlines())
    
    # Calculate weighted score
    complexity = (
        class_count * 10 +
        function_count * 5 +
        import_count * 2 +
        line_count * 0.1
    )
    
    return complexity
```

## Reporting System

### ReportGenerator

Central report generation system.

```python
from ark_tools.reporting import ReportGenerator
from ark_tools.reporting.base import ReportConfig

config = ReportConfig(
    output_dir=Path('.ark_reports'),
    generate_markdown=True,
    generate_html=True,
    include_visualizations=True
)

generator = ReportGenerator(config)
report_paths = generator.generate_reports(analysis_data)
```

### Report Collectors

#### HybridAnalysisCollector
```python
from ark_tools.reporting.collectors import HybridAnalysisCollector

collector = HybridAnalysisCollector(analysis_result)
report_data = collector.collect()
# Returns standardized report data
```

#### Custom Collectors
```python
from ark_tools.reporting.collectors import DataCollector

class CustomCollector(DataCollector):
    def collect(self) -> Dict[str, Any]:
        return {
            'metadata': self._collect_metadata(),
            'metrics': self._collect_metrics(),
            'insights': self._collect_insights()
        }
```

### Report Generators

#### MarkdownGenerator
```python
from ark_tools.reporting.generators import MarkdownGenerator

generator = MarkdownGenerator()
markdown_content = generator.generate(report_data)
```

#### HTMLGenerator
```python
from ark_tools.reporting.generators import HTMLGenerator

generator = HTMLGenerator()
html_content = generator.generate(report_data)
```

## Data Models

### Analysis Result Schema

```python
from pydantic import BaseModel
from typing import List, Dict, Optional

class Component(BaseModel):
    name: str
    type: str  # 'class', 'function', 'constant'
    file: str
    line: int
    metadata: Dict[str, Any]

class Domain(BaseModel):
    name: str
    description: str
    primary_components: List[str]
    relationships: List[Dict[str, str]]
    confidence: float

class AnalysisResult(BaseModel):
    structure: Dict[str, Any]
    domains: List[Domain]
    compression_stats: Dict[str, int]
    timing: Dict[str, float]
    confidence: float
    suggestions: Optional[List[Dict]]
    error: Optional[str]
```

### Report Data Schema

```python
class ReportData(BaseModel):
    metadata: Dict[str, Any]
    structure: Dict[str, Any]
    domains: List[Domain]
    compression_stats: Dict[str, Any]
    timing: Dict[str, float]
    suggestions: Dict[str, Any]
    model_info: Dict[str, Any]
    confidence: float
    strategy: str
    analysis_complete: bool
```

## Error Handling

### Custom Exceptions

```python
class ArkToolsException(Exception):
    """Base exception for ARK-TOOLS"""
    pass

class AnalysisException(ArkToolsException):
    """Raised when analysis fails"""
    pass

class CompressionException(ArkToolsException):
    """Raised when compression fails"""
    pass

class LLMException(ArkToolsException):
    """Raised when LLM inference fails"""
    pass
```

### Error Recovery

```python
async def safe_analysis(directory: str) -> Dict[str, Any]:
    try:
        return await perform_analysis(directory)
    except LLMException as e:
        # Fall back to MAMS-only analysis
        logger.warning(f"LLM failed: {e}, using MAMS only")
        return await perform_mams_analysis(directory)
    except CompressionException as e:
        # Skip compression, use raw files
        logger.warning(f"Compression failed: {e}, using raw files")
        return await perform_raw_analysis(directory)
    except Exception as e:
        # Log and return error state
        logger.error(f"Analysis failed: {e}")
        return {'error': str(e), 'success': False}
```

## Performance Metrics

### Metric Collection

```python
from ark_tools.metrics import MetricsCollector

metrics = MetricsCollector()

# Start timer
metrics.start_timer('analysis')

# Record counter
metrics.increment('files_processed')

# Record gauge
metrics.set_gauge('memory_usage', memory_mb)

# Stop timer
duration = metrics.stop_timer('analysis')
```

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `analysis_total` | Counter | Total analyses performed |
| `analysis_duration_seconds` | Histogram | Analysis duration |
| `files_processed` | Counter | Files processed |
| `tokens_used` | Counter | LLM tokens consumed |
| `compression_ratio` | Gauge | Average compression ratio |
| `cache_hit_ratio` | Gauge | Cache hit percentage |
| `error_rate` | Gauge | Error rate per minute |
| `memory_usage_mb` | Gauge | Memory usage in MB |

## Extension Development

### Creating Custom Agents

```python
from ark_tools.agents.base import BaseAgent
from typing import Dict, Any

class SecurityAnalysisAgent(BaseAgent):
    """Agent for security vulnerability analysis"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.register_operations()
    
    def register_operations(self):
        self.operations = {
            'scan_vulnerabilities': self._scan_vulnerabilities,
            'check_dependencies': self._check_dependencies
        }
    
    async def _scan_vulnerabilities(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        directory = parameters['directory']
        
        # Custom security scanning logic
        vulnerabilities = []
        
        # Scan for common patterns
        for pattern in self.vulnerability_patterns:
            matches = self.scan_pattern(directory, pattern)
            vulnerabilities.extend(matches)
        
        return {
            'vulnerabilities': vulnerabilities,
            'severity_counts': self.count_severities(vulnerabilities),
            'scan_time': time.time()
        }
```

### Creating Custom Compressors

```python
from ark_tools.mams_core.compressor import BaseCompressor

class JavaScriptCompressor(BaseCompressor):
    """Compressor for JavaScript/TypeScript files"""
    
    def compress_file(self, file_path: Path) -> str:
        content = file_path.read_text()
        
        # Parse with JavaScript AST parser
        tree = parse_javascript(content)
        
        # Extract skeleton
        skeleton = []
        for node in walk_tree(tree):
            if node.type == 'ClassDeclaration':
                skeleton.append(f"class {node.name}")
            elif node.type == 'FunctionDeclaration':
                skeleton.append(f"function {node.name}()")
        
        return '\n'.join(skeleton)
```

### Creating Custom Report Formats

```python
from ark_tools.reporting.generators import BaseGenerator

class XMLReportGenerator(BaseGenerator):
    """Generate XML format reports"""
    
    def generate(self, data: Dict[str, Any]) -> str:
        root = ET.Element('analysis_report')
        
        # Add metadata
        metadata = ET.SubElement(root, 'metadata')
        for key, value in data['metadata'].items():
            elem = ET.SubElement(metadata, key)
            elem.text = str(value)
        
        # Add domains
        domains = ET.SubElement(root, 'domains')
        for domain in data['domains']:
            domain_elem = ET.SubElement(domains, 'domain')
            domain_elem.set('name', domain['name'])
            domain_elem.set('confidence', str(domain['confidence']))
        
        return ET.tostring(root, encoding='unicode')
```

### Plugin System

```python
from ark_tools.plugins import PluginManager

# Register plugin
plugin_manager = PluginManager()
plugin_manager.register('security', SecurityAnalysisAgent)

# Use plugin
agent = plugin_manager.get('security')
result = await agent.execute_operation('scan_vulnerabilities', params)
```

## Advanced Usage

### Batch Processing

```python
async def batch_analyze(directories: List[str]) -> List[Dict]:
    """Analyze multiple directories in parallel"""
    
    async def analyze_one(directory):
        try:
            return await architect_agent.execute_operation(
                'perform_hybrid_analysis',
                {'directory': directory}
            )
        except Exception as e:
            return {'directory': directory, 'error': str(e)}
    
    # Process in parallel with concurrency limit
    semaphore = asyncio.Semaphore(3)
    
    async def analyze_with_limit(directory):
        async with semaphore:
            return await analyze_one(directory)
    
    tasks = [analyze_with_limit(d) for d in directories]
    return await asyncio.gather(*tasks)
```

### Streaming Analysis

```python
async def stream_analysis(directory: str):
    """Stream analysis results as they become available"""
    
    async for result in architect_agent.stream_operation(
        'perform_hybrid_analysis',
        {'directory': directory}
    ):
        yield result
        # Process intermediate results
        if result.get('phase') == 'mams_complete':
            # MAMS analysis done, can show structural results
            pass
        elif result.get('phase') == 'compression_complete':
            # Compression done, show stats
            pass
        elif result.get('phase') == 'llm_complete':
            # LLM analysis done, show domains
            pass
```

### Custom Analysis Strategies

```python
class CustomStrategy:
    """Define custom analysis strategy"""
    
    def should_compress(self, file_path: Path) -> bool:
        # Custom logic for compression decision
        return file_path.stat().st_size > 1024
    
    def select_files(self, all_files: List[Path]) -> List[Path]:
        # Custom file selection logic
        return sorted(all_files, key=self.calculate_importance)[-50:]
    
    def configure_llm(self, default_config: Dict) -> Dict:
        # Custom LLM configuration
        config = default_config.copy()
        config['temperature'] = 0.05  # More deterministic
        return config
```