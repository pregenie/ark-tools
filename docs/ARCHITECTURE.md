# ARK-TOOLS Architecture Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Architecture Patterns](#architecture-patterns)
4. [Data Flow](#data-flow)
5. [Integration Points](#integration-points)
6. [Deployment Architecture](#deployment-architecture)

## System Overview

ARK-TOOLS employs a hybrid architecture combining fast structural analysis with semantic understanding through embedded LLMs. The system is designed for scalability, modularity, and privacy-preserving operation.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│         (CLI / Web UI / API)                            │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                   API Gateway                            │
│              (FastAPI + Auth Middleware)                 │
└─────────────────┬───────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────┐
│                  Agent Orchestration                     │
│                  (ArchitectAgent)                        │
└──────┬──────────────────────┬──────────────────────────┘
       │                      │
┌──────▼────────┐     ┌──────▼────────┐
│     MAMS      │     │   LLM Engine   │
│   Analyzer    │     │  (Embedded)    │
└───────────────┘     └────────────────┘
       │                      │
┌──────▼──────────────────────▼──────────┐
│         Context Compressor              │
│        (AST-based reduction)            │
└─────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────┐
│          Report Generator                │
│     (Multi-format output system)         │
└──────────────────────────────────────────┘
```

## Core Components

### 1. Agent System (`ark_tools.agents`)

The agent system provides the orchestration layer for all analysis operations.

#### ArchitectAgent
- **Purpose**: Central orchestrator for hybrid analysis
- **Responsibilities**:
  - Coordinate MAMS and LLM analysis phases
  - Manage context compression
  - Generate reports
  - Handle operation routing

```python
# Key Operations
- perform_hybrid_analysis()
- analyze_semantic_domains()
- suggest_code_organization()
```

### 2. MAMS Core (`ark_tools.mams_core`)

Master Automated Migration System for fast structural analysis.

#### Components
- **FileDiscoveryAgent**: Scans and categorizes source files
- **ValidationAgent**: Validates compatibility and dependencies
- **ExtractionAgent**: Extracts components and relationships
- **CodeCompressor**: Reduces code to AST skeletons

#### Key Features
- Language-agnostic file discovery
- Dependency graph construction
- Component extraction (classes, functions, constants)
- ~80% token reduction through AST compression

### 3. LLM Engine (`ark_tools.llm_engine`)

Embedded LLM integration for semantic analysis.

#### Architecture
```python
class LLMAnalysisEngine:
    def __init__(self, config):
        # Initialize with GGUF model
        self.model = Llama(model_path=config['llm_model_path'])
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    async def analyze_domain_semantics(self, code_skeleton):
        # Non-blocking async inference
        return await loop.run_in_executor(self._executor, self._run_inference)
```

#### Supported Models
- CodeLlama-7B-Instruct (recommended)
- Mistral-7B-Instruct
- Phi-2
- DeepSeek-Coder-6.7B

### 4. Reporting System (`ark_tools.reporting`)

Multi-format report generation with progressive disclosure.

#### Components
- **ReportGenerator**: Main report generation orchestrator
- **HybridAnalysisCollector**: Collects and transforms analysis data
- **MarkdownGenerator**: Creates human-readable markdown reports
- **HTMLGenerator**: Generates interactive HTML reports

#### Report Structure
```
.ark_reports/
├── latest/                 # Symlink to most recent
├── 2024-01-14_120000/     # Timestamped report
│   ├── master.json        # Complete analysis data
│   ├── summary.json       # Executive summary
│   ├── errors.json        # Error tracking
│   ├── manifest.json      # File inventory
│   └── presentation/
│       ├── report.md      # Markdown report
│       └── report.html    # HTML report
└── history.json           # Report history
```

### 5. API Layer (`ark_tools.api`)

RESTful API for programmatic access.

#### Endpoints
- `/api/v1/hybrid/analyze` - Run hybrid analysis
- `/api/v1/hybrid/compress` - Compress code
- `/api/v1/hybrid/reports/generate` - Generate reports
- `/api/v1/hybrid/model/info` - Get model information

### 6. Setup System (`ark_tools.setup`)

Intelligent configuration and environment detection.

#### Components
- **SetupOrchestrator**: Manages setup workflow
- **ServiceDetector**: Detects existing services
- **EnvironmentDetector**: Scans for environment files
- **SystemChecker**: Validates system resources

## Architecture Patterns

### 1. Agent-Based Architecture

Each major capability is encapsulated in an agent with defined operations:

```python
class BaseAgent:
    async def execute_operation(self, operation_name, parameters):
        # Standard operation interface
        pass
```

Benefits:
- Modular capability addition
- Clear responsibility boundaries
- Testable units
- Extensible design

### 2. Context Compression Pattern

Reduces token usage while preserving semantic meaning:

```python
# Original: ~1000 tokens
class UserService:
    def __init__(self, db, cache):
        self.db = db
        self.cache = cache
    
    def get_user(self, user_id):
        # Check cache first
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        # Query database
        user = self.db.query(User).filter_by(id=user_id).first()
        if user:
            self.cache.set(f"user:{user_id}", user)
        return user

# Compressed: ~200 tokens
class UserService:
    def __init__(self, db, cache): pass
    def get_user(self, user_id): pass
```

### 3. Non-Blocking Async Pattern

LLM inference wrapped in thread pool to prevent blocking:

```python
async def analyze_with_llm(self, content):
    loop = asyncio.get_event_loop()
    # Run blocking LLM inference in thread pool
    result = await loop.run_in_executor(
        self._executor,
        self._run_llm_inference,
        content
    )
    return result
```

### 4. Single Source of Truth

Report data follows master-derived pattern:

```
master.json (complete data)
    ├── summary.json (derived)
    ├── errors.json (filtered)
    └── manifest.json (metadata)
```

## Data Flow

### Analysis Pipeline

1. **Input Phase**
   - User provides directory path
   - Strategy selection (hybrid/fast/deep)
   - Configuration parameters

2. **Discovery Phase**
   - File system scanning
   - Language detection
   - Exclusion filtering

3. **Structural Analysis (MAMS)**
   - Component extraction
   - Dependency mapping
   - Relationship discovery

4. **Compression Phase**
   - AST parsing
   - Skeleton generation
   - Token optimization

5. **Semantic Analysis (LLM)**
   - Domain discovery
   - Intent analysis
   - Relationship inference

6. **Reconciliation Phase**
   - Merge MAMS and LLM results
   - Resolve conflicts
   - Calculate confidence scores

7. **Report Generation**
   - Data collection
   - Format transformation
   - Multi-format output

### Data Models

#### Analysis Result
```python
{
    "structure": {
        "total_files": int,
        "total_components": int,
        "components": Dict[str, List[Component]]
    },
    "domains": [
        {
            "name": str,
            "description": str,
            "primary_components": List[str],
            "confidence": float
        }
    ],
    "timing": {
        "mams_ms": int,
        "compression_ms": int,
        "llm_ms": int,
        "total_ms": int
    },
    "suggestions": List[Dict],
    "confidence": float
}
```

## Integration Points

### 1. External Services

#### PostgreSQL
- Configuration storage
- Analysis history
- Report metadata

#### Redis
- Result caching
- Session management
- Queue for async tasks

### 2. Model Integration

#### GGUF Models
- Local file system storage
- Memory-mapped loading
- GPU acceleration (optional)

### 3. Container Integration

#### Docker Support
- Isolated execution environment
- Resource management
- Service orchestration

## Deployment Architecture

### Standalone Deployment

```
┌─────────────────────┐
│    Host Machine     │
│                     │
│  ┌───────────────┐  │
│  │  ARK-TOOLS    │  │
│  │   Process     │  │
│  └───────────────┘  │
│                     │
│  ┌───────────────┐  │
│  │  LLM Model    │  │
│  │   (GGUF)      │  │
│  └───────────────┘  │
└─────────────────────┘
```

### Container Deployment

```
┌──────────────────────────────────────┐
│         Docker Host                   │
│                                       │
│  ┌─────────────┐  ┌────────────┐    │
│  │ ark-tools   │  │ postgresql │    │
│  │ container   │  │ container  │    │
│  └─────────────┘  └────────────┘    │
│                                       │
│  ┌─────────────┐  ┌────────────┐    │
│  │   redis     │  │ monitoring │    │
│  │ container   │  │ container  │    │
│  └─────────────┘  └────────────┘    │
└──────────────────────────────────────┘
```

### Distributed Deployment

```
┌─────────────────┐     ┌─────────────────┐
│   API Gateway   │────▶│  Load Balancer  │
└─────────────────┘     └─────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────▼──────┐      ┌─────▼──────┐      ┌─────▼──────┐
    │  Worker 1  │      │  Worker 2  │      │  Worker 3  │
    └────────────┘      └────────────┘      └────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                      ┌────────▼────────┐
                      │  Shared Cache   │
                      │    (Redis)      │
                      └─────────────────┘
```

## Performance Considerations

### Memory Management
- LLM models use memory mapping for efficient loading
- Context compression reduces memory footprint
- Streaming processing for large codebases

### Scalability
- Horizontal scaling through worker distribution
- Caching layer for repeated analyses
- Async processing for non-blocking operations

### Resource Requirements

#### Minimum
- CPU: 4 cores
- RAM: 8GB
- Disk: 10GB (including model)

#### Recommended
- CPU: 8+ cores
- RAM: 16GB
- Disk: 20GB
- GPU: Optional (8GB+ VRAM)

## Security Considerations

### Data Privacy
- All analysis performed locally
- No external API calls for core functionality
- Embedded LLMs ensure data doesn't leave premises

### Access Control
- API key authentication
- Role-based access control
- Audit logging

### Input Validation
- Path traversal prevention
- File type validation
- Size limits enforcement

## Extension Points

### Custom Agents
```python
from ark_tools.agents.base import BaseAgent

class CustomAgent(BaseAgent):
    async def execute_operation(self, op_name, params):
        # Custom analysis logic
        pass
```

### Custom Collectors
```python
from ark_tools.reporting.collectors import DataCollector

class CustomCollector(DataCollector):
    def collect(self):
        # Custom data collection
        pass
```

### Custom Generators
```python
from ark_tools.reporting.generators import BaseGenerator

class CustomGenerator(BaseGenerator):
    def generate(self, data):
        # Custom report format
        pass
```

## Monitoring and Observability

### Metrics
- Analysis duration
- Token usage
- Cache hit rates
- Error rates

### Logging
- Structured logging with levels
- Operation tracing
- Error tracking

### Health Checks
- `/health` - System health
- `/ready` - Readiness probe
- `/metrics` - Prometheus metrics

## Future Architecture Considerations

### Planned Enhancements
1. Distributed analysis for large codebases
2. Real-time collaboration features
3. Cloud-native deployment options
4. Multi-model ensemble analysis
5. Incremental analysis capabilities

### Extension Areas
1. Additional language support
2. Custom domain ontologies
3. Integration with CI/CD pipelines
4. IDE plugins
5. GraphQL API layer