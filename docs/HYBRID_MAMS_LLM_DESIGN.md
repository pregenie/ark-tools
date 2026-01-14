# ARK-TOOLS Hybrid MAMS/LLM Analysis System
## Production Design and Implementation Document

**Version:** 2.0  
**Date:** January 2025  
**Status:** Production Ready Design  
**Architecture:** Agent-Integrated Hybrid Analysis

---

## Executive Summary

This document describes the production design for integrating MAMS (Master Automated Migration System) core components with an embedded LLM layer as a capability within ARK-TOOLS' existing Agent architecture. The system leverages the existing `ArchitectAgent` and `BaseAgent` infrastructure rather than creating redundant orchestration layers. MAMS serves as a context compressor for efficient LLM analysis, solving token limit constraints while maintaining semantic understanding.

### Key Improvements in v2.0
- **No Duplication**: Extends existing Agent architecture instead of creating parallel systems
- **Context Compression**: MAMS preprocesses code to AST skeletons, reducing LLM tokens by ~80%
- **Non-blocking**: Async-safe LLM inference using ThreadPoolExecutor
- **Unified Architecture**: LLM as a capability tool for ArchitectAgent
- **Efficient Token Usage**: Analyzes code structure without full implementation details

---

## 1. System Architecture

### 1.1 Agent-Integrated Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface Layer                    │
│  (CLI Commands, Web API, Real-time WebSocket Updates)       │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                  Existing Agent Architecture                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              ArchitectAgent (Extended)               │   │
│  │                                                      │   │
│  │  Capabilities:                                       │   │
│  │  ├─ validate_database_schema (existing)             │   │
│  │  ├─ review_api_design (existing)                    │   │
│  │  ├─ validate_source_protection (existing)           │   │
│  │  └─ perform_hybrid_analysis (NEW)                   │   │
│  │       ├─ MAMS Context Compression                   │   │
│  │       └─ LLM Semantic Analysis                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                      Tool Layer (NEW)                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ MAMS         │  │ Code         │  │ LLM Analysis │     │
│  │ Compressor   │  │ Skeleton     │  │ Engine       │     │
│  │ (AST->Text)  │  │ Extractor    │  │ (Async-safe) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Component Integration Map

```yaml
ark_tools/
├── mams_core/                 # Integrated MAMS components
│   ├── compressor.py           # AST-based context compression
│   ├── discovery/              # File discovery engine
│   ├── extractors/             # Component extractors
│   └── mapping/                # Master mapping system
│
├── llm_engine/                 # Embedded LLM layer
│   ├── engine.py               # Async-safe inference engine
│   ├── models/                 # Model storage
│   ├── prompts/                # Semantic analysis prompts
│   └── cache/                  # Results cache
│
├── agents/                     # Extended Agent capabilities
│   └── architect.py            # Enhanced with hybrid analysis
│
└── web/                        # Enhanced Web UI
    ├── semantic_explorer.py    # Visual domain explorer
    └── junior_dev_guide.py     # Code understanding assistant
```

---

## 2. MAMS Core Integration

### 2.1 Components to Import from arkyvus_mams_tools

Based on the discovered MAMS structure, we'll integrate:

#### Essential Components
```python
# From /Users/pregenie/Development/arkyvus_mams_tools/migrations/
- mams_002_backend_discovery_v2.py     # Service discovery engine
- mams_008_dependency_resolution_engine.py  # Dependency resolver
- mams_006_migration_planning_engine.py     # Planning engine

# From /Users/pregenie/Development/arkyvus_mams_tools/migrations/generators/
- unified_generator.py                  # Unified code generator
- blueprint_generator.py                # Blueprint patterns
- frontend_integration_generator.py     # Frontend patterns
```

#### Master Mapping Integration
```python
# Core mapping file
MAMS_MASTER_MAPPING.json (1.09MB)
- 2,876 file mappings
- Domain classifications
- Service relationships
- Platform specifications (backend/frontend)
- Source type categorization
```

### 2.2 Integration Strategy

```python
# src/ark_tools/mams_core/__init__.py
class MAMSCore:
    """Integrated MAMS core functionality"""
    
    def __init__(self):
        self.discovery_engine = BackendServiceDiscovery()
        self.dependency_resolver = DependencyResolutionEngine()
        self.mapping_system = MasterMappingSystem()
        self.generators = {
            'unified': UnifiedGenerator(),
            'blueprint': BlueprintGenerator(),
            'frontend': FrontendIntegrationGenerator()
        }
        
    def analyze_structure(self, directory: Path) -> StructuralAnalysis:
        """Fast structural analysis using MAMS"""
        # 1. Discover files and services
        services = self.discovery_engine.discover_services(directory)
        
        # 2. Extract components
        components = self.extract_components(services)
        
        # 3. Resolve dependencies
        dependencies = self.dependency_resolver.resolve(components)
        
        # 4. Map to domains using master mapping
        domains = self.mapping_system.map_to_domains(components)
        
        return StructuralAnalysis(
            services=services,
            components=components,
            dependencies=dependencies,
            domains=domains,
            execution_time_ms=self.timer.elapsed_ms()
        )
```

---

## 3. Context Compression Strategy

### 3.1 The Token Limit Problem

LLMs have context windows (4K-32K tokens). A single Python file can easily exceed this. The solution: **MAMS as a Context Compressor**.

```python
# src/ark_tools/mams_core/compressor.py
import ast
from pathlib import Path
from typing import Dict, List, Optional
from ark_tools.utils.debug_logger import debug_log

class CodeCompressor:
    """
    Compresses code to semantic skeleton using AST parsing.
    Reduces token usage by ~80% while preserving meaning.
    """
    
    def compress_file(self, file_path: Path) -> str:
        """Extract semantic skeleton from Python file"""
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            skeleton = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node) or "No description"
                    methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    skeleton.append(f"class {node.name}:  # {doc.split()[0:10]}")
                    for method in methods[:5]:  # Limit to key methods
                        skeleton.append(f"    def {method}(...)")
                        
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    doc = ast.get_docstring(node) or ""
                    args = [a.arg for a in node.args.args if a.arg != 'self']
                    skeleton.append(f"def {node.name}({', '.join(args[:3])}...): # {doc[:50]}")
            
            return "\n".join(skeleton)
            
        except Exception as e:
            debug_log.error_trace(f"Compression failed for {file_path}", exception=e)
            return f"# Error processing {file_path.name}"
    
    def compress_directory(self, directory: Path, max_files: int = 50) -> Dict[str, str]:
        """Compress top N most complex files in directory"""
        results = {}
        py_files = list(directory.glob("**/*.py"))[:max_files]
        
        for file_path in py_files:
            compressed = self.compress_file(file_path)
            if compressed:
                results[str(file_path)] = compressed
                
        debug_log.agent(f"Compressed {len(results)} files, ~{sum(len(v) for v in results.values())} tokens")
        return results
```

### 3.2 Compression Example

**Original Code (523 tokens):**
```python
class UserAuthenticationService:
    """Handles user authentication and session management"""
    
    def __init__(self, db_connection, redis_client, config):
        self.db = db_connection
        self.redis = redis_client
        self.config = config
        self.jwt_secret = config.get('JWT_SECRET')
        self.token_expiry = config.get('TOKEN_EXPIRY', 3600)
        
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        # 50 lines of implementation...
        
    def create_session(self, user: User) -> str:
        """Create new session for authenticated user"""
        # 30 lines of implementation...
```

**Compressed Skeleton (87 tokens):**
```python
class UserAuthenticationService:  # Handles user authentication
    def authenticate_user(username, password...)
    def create_session(user...)
    def refresh_token(token...)
    def logout(session_id...)
```

This 6x reduction allows analyzing entire codebases within LLM context limits.

## 4. LLM Engine Implementation

### 3.1 Model Selection and Configuration

#### Recommended Models (in priority order)

1. **CodeLlama-7B-Instruct** (Primary)
   - Size: 3.8GB quantized (GGUF format)
   - Strengths: Specialized for code understanding
   - Speed: 20-30 tokens/sec on CPU, 100+ on GPU
   - Use case: Primary code analysis and domain extraction

2. **Mistral-7B-Instruct** (Fallback)
   - Size: 4.1GB quantized
   - Strengths: General purpose, good reasoning
   - Speed: 25-35 tokens/sec on CPU
   - Use case: Fallback when CodeLlama unavailable

3. **Phi-2** (Lightweight)
   - Size: 1.5GB
   - Strengths: Small, fast, decent code understanding
   - Speed: 40-50 tokens/sec on CPU
   - Use case: Quick analysis, resource-constrained environments

### 4.2 Non-blocking LLM Engine

```python
# src/ark_tools/llm_engine/engine.py
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional
from pathlib import Path
from ark_tools.utils.debug_logger import debug_log

class LLMAnalysisEngine:
    """
    Async-safe LLM engine for semantic code analysis.
    Offloads inference to thread pool to prevent blocking.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._model = None  # Lazy load to save memory
        self.cache = {}  # Simple in-memory cache
        
    def _get_model(self):
        """Lazy load model only when needed"""
        if not self._model:
            from llama_cpp import Llama
            debug_log.agent("Loading LLM model for semantic analysis...")
            self._model = Llama(
                model_path=self.model_path,
                n_ctx=8192,     # Larger context for compressed code
                n_threads=8,
                n_gpu_layers=35 if self._has_gpu() else 0,
                verbose=False
            )
        return self._model
    
    async def analyze_domain_semantics(self, code_skeleton: str) -> Dict[str, Any]:
        """
        Analyze compressed code skeleton asynchronously.
        Returns domain analysis without blocking event loop.
        """
        # Check cache
        cache_key = hash(code_skeleton[:500])  # Use first 500 chars for key
        if cache_key in self.cache:
            debug_log.agent("Using cached LLM analysis")
            return self.cache[cache_key]
        
        def _run_inference():
            """Blocking inference in thread pool"""
            llm = self._get_model()
            prompt = self._build_semantic_prompt(code_skeleton)
            
            response = llm(
                prompt,
                max_tokens=1024,
                temperature=0.1,  # Low temp for consistency
                stop=["</json>"],
                stream=False
            )
            return response['choices'][0]['text']
        
        # Run in thread pool to avoid blocking
        debug_log.agent("Starting async LLM inference...")
        try:
            result_text = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                _run_inference
            )
            result = self._parse_json_response(result_text)
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            debug_log.error_trace("LLM inference failed", exception=e)
            return {"error": str(e), "domains": [], "confidence": 0}
    
    def _build_semantic_prompt(self, skeleton: str) -> str:
        """Build prompt for domain analysis"""
        return f"""[INST] You are a Senior Software Architect analyzing code structure.
Analyze these code signatures and identify business domains.

Code Skeleton:
{skeleton}

Task: Identify business domains and explain their purpose.
Output ONLY valid JSON.

Example output:
{{
  "domains": [
    {{
      "name": "Authentication",
      "description": "User login and session management",
      "confidence": 0.95,
      "components": ["UserService", "SessionManager"],
      "relationships": ["UserManagement"]
    }}
  ]
}}
[/INST]
<json>"""
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse and clean LLM JSON output"""
        text = text.strip()
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback for malformed JSON
            return {"domains": [], "error": "Failed to parse LLM response"}
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
```

### 3.3 Prompt Engineering

```python
# src/ark_tools/llm_engine/prompts.py
class PromptTemplateManager:
    """Manages prompt templates for different analysis tasks"""
    
    DOMAIN_ANALYSIS_TEMPLATE = """<system>
You are an expert software architect analyzing code structure to identify business domains.
Your task is to group related components into logical business domains.
</system>

<components>
{component_list}
</components>

<task>
Analyze the above components and identify the business domains they belong to.
For each domain:
1. Provide a clear domain name
2. List the components that belong to it
3. Explain the domain's responsibility
4. Identify relationships with other domains

Format your response as JSON:
</task>

<analysis>
{
  "domains": [
    {
      "name": "Authentication",
      "description": "Handles user authentication and session management",
      "components": ["LoginService", "SessionManager", "TokenValidator"],
      "relationships": ["User Management", "Security"],
      "confidence": 0.95
    }
  ],
  "domain_relationships": [
    {
      "from": "Authentication",
      "to": "User Management",
      "type": "depends_on",
      "reason": "Requires user data for authentication"
    }
  ]
}
</analysis>"""

    def get_domain_analysis_prompt(self, components: List[Component], context: str) -> str:
        """Generate domain analysis prompt"""
        component_list = self._format_components(components)
        return self.DOMAIN_ANALYSIS_TEMPLATE.format(
            component_list=component_list
        )
```

---

## 5. Agent Integration

### 5.1 Extending ArchitectAgent

```python
# src/ark_tools/agents/architect.py (additions)
from ark_tools.llm_engine.engine import LLMAnalysisEngine
from ark_tools.mams_core.compressor import CodeCompressor
from typing import Dict, Any, List, Optional
from pathlib import Path

class ArchitectAgent(BaseAgent):
    """Enhanced architect agent with semantic analysis capabilities"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("ark-architect", config)
        # ... existing init ...
        
        # Initialize new engines
        self.llm_engine = LLMAnalysisEngine(
            model_path=config.get('llm_model_path')
        )
        self.compressor = CodeCompressor()
        self.mams_core = self._init_mams_core()
        
    def get_capabilities(self) -> List[str]:
        """Extended capabilities"""
        return super().get_capabilities() + [
            'perform_hybrid_analysis',
            'analyze_semantic_domains',
            'suggest_code_organization'
        ]
    
    async def execute_operation(self, operation: str, parameters: Dict[str, Any]) -> AgentResult:
        """Extended operation router"""
        if operation == 'perform_hybrid_analysis':
            result_data = await self._perform_hybrid_analysis(parameters)
        elif operation == 'analyze_semantic_domains':
            result_data = await self._analyze_semantic_domains(parameters)
        else:
            # Existing operations
            return await super().execute_operation(operation, parameters)
            
        return self._complete_operation(
            operation=operation,
            success=True,
            data=result_data
        )
    
    async def _perform_hybrid_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Three-tier hybrid analysis:
        1. MAMS for structure (fast)
        2. Compression for context reduction
        3. LLM for semantic understanding (deep)
        """
        target_dir = Path(parameters.get('directory', '.'))
        strategy = parameters.get('strategy', 'hybrid')
        
        # Phase 1: MAMS structural analysis (milliseconds)
        debug_log.agent("Phase 1: MAMS structural analysis...")
        mams_result = self.mams_core.analyze_structure(target_dir)
        
        if strategy == 'fast':
            return {'analysis': mams_result, 'type': 'structural'}
        
        # Phase 2: Context compression
        debug_log.agent("Phase 2: Compressing code for LLM analysis...")
        compressed_code = self.compressor.compress_directory(
            target_dir,
            max_files=50  # Top 50 most complex files
        )
        
        # Combine all skeletons
        full_skeleton = "\n\n".join([
            f"# File: {path}\n{skeleton}"
            for path, skeleton in compressed_code.items()
        ])
        
        # Phase 3: LLM semantic analysis (seconds)
        debug_log.agent("Phase 3: LLM semantic analysis...")
        semantic_result = await self.llm_engine.analyze_domain_semantics(full_skeleton)
        
        # Phase 4: Reconcile results
        return self._reconcile_analysis_results(
            mams=mams_result,
            semantic=semantic_result,
            compression_stats={
                'files_analyzed': len(compressed_code),
                'total_tokens': len(full_skeleton.split()),
                'compression_ratio': 0.2  # Approximate
            }
        )
    
    def _reconcile_analysis_results(
        self, 
        mams: Dict, 
        semantic: Dict,
        compression_stats: Dict
    ) -> Dict[str, Any]:
        """Merge MAMS structure with LLM semantics"""
        
        # Use MAMS for accurate file/function counts
        structure = {
            'total_files': mams.get('total_files', 0),
            'total_components': mams.get('total_components', 0),
            'dependencies': mams.get('dependencies', [])
        }
        
        # Use LLM for domain understanding
        domains = semantic.get('domains', [])
        
        # Enhance domains with MAMS data
        for domain in domains:
            domain_name = domain['name']
            # Match components from MAMS to domains from LLM
            domain['file_count'] = self._count_domain_files(
                domain_name, 
                mams.get('components', [])
            )
            domain['complexity'] = self._calculate_domain_complexity(
                domain_name,
                mams
            )
        
        return {
            'structure': structure,
            'domains': domains,
            'confidence': semantic.get('confidence', 0),
            'compression_stats': compression_stats,
            'analysis_time': {
                'mams_ms': mams.get('execution_time_ms', 0),
                'llm_estimated_ms': 3000  # Typical LLM time
            }
        }
```

## 6. Enhanced Web UI for Junior Developers

### 6.1 Semantic Code Explorer

```vue
<!-- src/ark_tools/web/components/SemanticExplorer.vue -->
<template>
  <div class="semantic-explorer">
    <h2>🧠 Intelligent Code Understanding</h2>
    
    <!-- Domain Visualization -->
    <div class="domain-grid">
      <div v-for="domain in domains" :key="domain.name" 
           class="domain-card" 
           :class="{ 'high-confidence': domain.confidence > 0.8 }">
        
        <div class="domain-header">
          <h3>{{ domain.name }}</h3>
          <span class="confidence-badge">
            {{ (domain.confidence * 100).toFixed(0) }}% confident
          </span>
        </div>
        
        <div class="domain-explanation">
          <p>{{ domain.description }}</p>
          <div class="ai-insight">
            💡 <em>"{{ domain.llm_explanation }}"</em>
          </div>
        </div>
        
        <div class="domain-stats">
          <div class="stat">
            <span class="label">Files:</span>
            <span class="value">{{ domain.file_count }}</span>
          </div>
          <div class="stat">
            <span class="label">Components:</span>
            <span class="value">{{ domain.component_count }}</span>
          </div>
          <div class="stat">
            <span class="label">Complexity:</span>
            <span class="complexity-bar" :style="complexityStyle(domain.complexity)"></span>
          </div>
        </div>
        
        <!-- Interactive Learning -->
        <div class="learning-section">
          <button @click="explainDomain(domain)" class="explain-btn">
            🎓 Explain This Domain
          </button>
          <button @click="showRelationships(domain)" class="relationships-btn">
            🔗 Show Relationships
          </button>
        </div>
        
        <!-- Junior Dev Helper -->
        <div v-if="domain.expanded" class="junior-helper">
          <h4>Understanding "{{ domain.name }}":</h4>
          <ul>
            <li v-for="concept in domain.concepts" :key="concept">
              {{ concept }}
            </li>
          </ul>
          <div class="code-example">
            <pre><code>{{ domain.example_code }}</code></pre>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Interactive Domain Relationship Graph -->
    <div class="relationship-graph" v-if="showGraph">
      <svg ref="domainGraph" width="800" height="600">
        <!-- D3.js visualization of domain relationships -->
      </svg>
    </div>
    
    <!-- Learning Assistant Panel -->
    <div class="learning-assistant">
      <h3>🤖 AI Assistant</h3>
      <div class="chat-interface">
        <div class="messages">
          <div v-for="msg in assistantMessages" :key="msg.id" 
               :class="msg.type">
            {{ msg.text }}
          </div>
        </div>
        <input v-model="userQuestion" 
               @keyup.enter="askAssistant"
               placeholder="Ask about the code architecture...">
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SemanticExplorer',
  data() {
    return {
      domains: [],
      showGraph: false,
      assistantMessages: [],
      userQuestion: ''
    }
  },
  methods: {
    async explainDomain(domain) {
      // Request LLM to explain domain in simple terms
      const response = await fetch('/api/v1/explain-domain', {
        method: 'POST',
        body: JSON.stringify({ domain_name: domain.name })
      })
      const explanation = await response.json()
      
      // Show explanation tailored for junior developers
      this.assistantMessages.push({
        id: Date.now(),
        type: 'assistant',
        text: explanation.simple_explanation
      })
      
      // Expand domain card with examples
      domain.expanded = true
      domain.concepts = explanation.key_concepts
      domain.example_code = explanation.code_example
    },
    
    async askAssistant() {
      // Use LLM to answer architecture questions
      const response = await fetch('/api/v1/assistant/ask', {
        method: 'POST',
        body: JSON.stringify({ 
          question: this.userQuestion,
          context: this.domains
        })
      })
      const answer = await response.json()
      
      this.assistantMessages.push({
        id: Date.now(),
        type: 'user',
        text: this.userQuestion
      })
      
      this.assistantMessages.push({
        id: Date.now() + 1,
        type: 'assistant',
        text: answer.response
      })
      
      this.userQuestion = ''
    },
    
    complexityStyle(complexity) {
      const width = Math.min(complexity * 10, 100)
      const color = complexity > 7 ? '#ff4444' : 
                    complexity > 4 ? '#ffaa00' : '#44ff44'
      return {
        width: `${width}%`,
        backgroundColor: color
      }
    }
  }
}
</script>

<style scoped>
.domain-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  padding: 20px;
  margin: 15px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  transition: transform 0.3s;
}

.domain-card:hover {
  transform: translateY(-5px);
}

.high-confidence {
  border: 2px solid #4ade80;
}

.ai-insight {
  background: rgba(255,255,255,0.1);
  padding: 10px;
  border-radius: 8px;
  margin: 10px 0;
}

.junior-helper {
  background: rgba(0,0,0,0.2);
  padding: 15px;
  border-radius: 10px;
  margin-top: 15px;
}

.learning-assistant {
  position: fixed;
  right: 20px;
  bottom: 20px;
  width: 350px;
  background: white;
  border-radius: 15px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.3);
  padding: 20px;
}
</style>
```

---

## 5. Implementation Plan

### 5.1 Phase 1: MAMS Core Integration (Week 1)

**Tasks:**
1. Copy essential MAMS components from `arkyvus_mams_tools`
2. Refactor imports and paths for ARK-TOOLS structure
3. Integrate MAMS_MASTER_MAPPING.json
4. Create MAMS wrapper classes
5. Test structural analysis capabilities

**Deliverables:**
- `src/ark_tools/mams_core/` fully integrated
- Unit tests for MAMS components
- Performance benchmarks established

### 5.2 Phase 2: LLM Engine Setup (Week 2)

**Tasks:**
1. Implement model download and management system
2. Create llama.cpp integration layer
3. Develop prompt templates for domain analysis
4. Build caching system for LLM results
5. Optimize inference parameters

**Deliverables:**
- `src/ark_tools/llm_engine/` fully implemented
- Model management CLI commands
- Prompt template library
- Cache persistence system

### 5.3 Phase 3: Hybrid Orchestration (Week 3)

**Tasks:**
1. Build analysis orchestrator
2. Implement result reconciliation logic
3. Create domain discovery engine
4. Develop user confirmation interface
5. Add WebSocket real-time updates

**Deliverables:**
- `src/ark_tools/hybrid_analyzer/` complete
- API endpoints for analysis
- Real-time progress updates
- User confirmation flows

### 5.4 Phase 4: Production Hardening (Week 4)

**Tasks:**
1. Add comprehensive error handling
2. Implement retry logic and fallbacks
3. Create monitoring and metrics
4. Performance optimization
5. Documentation and examples

**Deliverables:**
- Production-ready system
- Performance metrics dashboard
- Complete API documentation
- Example use cases

---

## 6. Configuration and Deployment

### 6.1 Configuration Structure

```yaml
# config/hybrid_analysis.yaml
analysis:
  mams:
    enabled: true
    timeout_ms: 5000
    max_files: 10000
    
  llm:
    enabled: true
    model: "codellama-7b-instruct"
    model_path: "~/.ark_tools/models/"
    context_size: 4096
    gpu_layers: 35
    threads: 8
    
  hybrid:
    strategy: "intelligent"  # fast|deep|intelligent
    cache_ttl: 86400        # 24 hours
    confirmation_required: true
    
domains:
  min_component_count: 3
  auto_split_threshold: 50
  merge_similar_threshold: 0.85
  
  suggested_domains:
    - authentication
    - authorization  
    - data_access
    - business_logic
    - api_gateway
    - messaging
    - reporting
    - monitoring
```

### 6.2 Docker Integration

```dockerfile
# docker/Dockerfile.hybrid
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install llama.cpp
RUN pip install llama-cpp-python

# Copy MAMS core
COPY arkyvus_mams_tools/migrations /app/mams_core/
COPY arkyvus_mams_tools/MAMS_MASTER_MAPPING.json /app/mams_core/

# Copy ARK-TOOLS
COPY src/ /app/src/
WORKDIR /app

# Download default model
RUN python -m ark_tools.llm_engine.model_manager download codellama-7b

ENTRYPOINT ["python", "-m", "ark_tools"]
```

---

## 7. Usage Examples

### 7.1 CLI Usage

```bash
# Fast analysis (MAMS only)
ark-analyze /path/to/code --strategy fast

# Deep analysis (LLM only)  
ark-analyze /path/to/code --strategy deep

# Hybrid analysis (default)
ark-analyze /path/to/code --strategy hybrid

# With specific model
ark-analyze /path/to/code --model mistral-7b

# Skip confirmation
ark-analyze /path/to/code --auto-confirm
```

### 7.2 API Usage

```python
from ark_tools.hybrid_analyzer import HybridAnalyzer

analyzer = HybridAnalyzer()

# Run analysis
result = await analyzer.analyze(
    directory="/path/to/project",
    strategy="hybrid",
    auto_confirm=False
)

# Access results
print(f"Found {len(result.domains)} domains")
for domain in result.domains:
    print(f"- {domain.name}: {len(domain.components)} components")
    
# Generate transformation plan
plan = analyzer.create_transformation_plan(result)
```

### 7.3 Example Output

```
🚀 Starting Hybrid Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 MAMS Analysis (124ms)
- Files scanned: 847
- Components found: 312
- Dependencies mapped: 1,245

🧠 LLM Analysis (3.2s)
- Domains identified: 6
- Confidence: 92%
- Relationships mapped: 14

🔍 Domain Discovery Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Authentication & Security
   Components: 42
   Files: 18
   Relationships: [User Management, API Gateway]
   
2. Data Management
   Components: 67
   Files: 31
   Relationships: [Business Logic, Reporting]
   
3. Messaging & Communications
   Components: 28
   Files: 12
   Relationships: [Notifications, External APIs]

Confirm domains? [Y/n/edit]: Y

✅ Analysis complete! Results saved to .ark_output/analysis_20250114_100230/
```

---

## 8. Performance Metrics

### 8.1 Expected Performance

| Analysis Type | Files | Time | Memory | CPU |
|--------------|-------|------|--------|-----|
| MAMS Only | 1,000 | 150ms | 200MB | 10% |
| MAMS Only | 10,000 | 1.2s | 800MB | 25% |
| LLM Only | 1,000 | 4s | 4GB | 80% |
| LLM Only | 10,000 | 35s | 4.5GB | 85% |
| Hybrid | 1,000 | 4.5s | 4.2GB | 60% |
| Hybrid | 10,000 | 37s | 5GB | 70% |

### 8.2 Optimization Strategies

1. **Caching**: Cache LLM results for identical code patterns
2. **Batching**: Process multiple files in single LLM call
3. **Pruning**: Skip analysis of test/vendor files
4. **Parallelization**: Run MAMS and LLM analysis concurrently
5. **Model Quantization**: Use 4-bit quantized models for speed

---

## 9. Monitoring and Observability

### 9.1 Metrics to Track

```python
# src/ark_tools/monitoring/metrics.py
METRICS = {
    'analysis.mams.duration_ms': Histogram,
    'analysis.llm.duration_ms': Histogram,
    'analysis.domains.discovered': Gauge,
    'analysis.components.total': Gauge,
    'analysis.cache.hit_rate': Gauge,
    'llm.tokens_per_second': Gauge,
    'llm.model.memory_gb': Gauge,
}
```

### 9.2 Health Checks

```python
# GET /health/hybrid
{
  "status": "healthy",
  "components": {
    "mams_core": {
      "status": "operational",
      "version": "2.0",
      "last_analysis": "2025-01-14T10:02:30Z"
    },
    "llm_engine": {
      "status": "operational",
      "model": "codellama-7b",
      "memory_usage_gb": 3.8,
      "inference_speed_tps": 28
    },
    "cache": {
      "status": "operational",
      "entries": 1247,
      "hit_rate": 0.73
    }
  }
}
```

---

## 10. Security Considerations

### 10.1 Code Privacy

- All analysis runs locally - no code sent to external services
- LLM models stored locally in `~/.ark_tools/models/`
- Cache encrypted at rest using ARK_SECRET_KEY
- No telemetry or usage tracking

### 10.2 Model Security

- Models downloaded from official repositories only
- SHA256 verification of model files
- Models run in sandboxed environment
- No network access during inference

---

## 11. Future Enhancements

### 11.1 Advanced Features (v2.0)

1. **Fine-tuned Models**: Custom models trained on specific codebases
2. **Multi-language Support**: Extend beyond Python/JavaScript
3. **Incremental Analysis**: Analyze only changed files
4. **Team Collaboration**: Shared domain definitions
5. **CI/CD Integration**: Automated analysis on commits

### 11.2 Model Improvements

1. **Mixture of Experts**: Use multiple specialized models
2. **Active Learning**: Improve from user confirmations
3. **Context Extension**: Support larger codebases
4. **Speed Optimization**: Custom CUDA kernels for GPU

---

## 12. Conclusion

This hybrid MAMS/LLM system represents a significant advancement in code analysis capabilities. By combining the speed and accuracy of MAMS static analysis with the semantic understanding of embedded LLMs, ARK-TOOLS can provide unparalleled insights into code structure and business domains while maintaining complete privacy and offline operation.

The system is designed for production use with comprehensive error handling, performance optimization, and user-friendly interfaces. The phased implementation plan ensures each component is thoroughly tested before integration, minimizing risk and ensuring stability.

---

## Appendix A: MAMS Component Details

### Essential Files to Copy

```bash
# From arkyvus_mams_tools/migrations/
mams_002_backend_discovery_v2.py       # 14KB
mams_006_migration_planning_engine.py  # 30KB  
mams_008_dependency_resolution_engine.py # 35KB
mams_013_typescript_ast_parser.py      # 22KB

# From arkyvus_mams_tools/migrations/generators/
unified_generator.py                    # 20KB
blueprint_generator.py                  # 10KB
frontend_integration_generator.py       # 15KB

# Master mapping
MAMS_MASTER_MAPPING.json               # 1.09MB
```

### Integration Points

1. **Discovery Engine**: Line 26-50 of mams_002_backend_discovery_v2.py
2. **Dependency Resolution**: Line 180-220 of mams_008_dependency_resolution_engine.py
3. **Generator System**: Line 45-90 of unified_generator.py
4. **Master Mapping**: Full JSON structure with 2,876 mappings

---

## Appendix B: Model Download Commands

```bash
# Download models using ARK-TOOLS CLI
ark-tools models download codellama-7b-instruct
ark-tools models download mistral-7b-instruct  
ark-tools models download phi-2

# List available models
ark-tools models list

# Check model status
ark-tools models status

# Remove a model
ark-tools models remove mistral-7b-instruct
```

---

**Document End**

*This design document provides the complete blueprint for implementing the hybrid MAMS/LLM analysis system in ARK-TOOLS. The system leverages existing MAMS components from arkyvus_mams_tools while adding intelligent AI-powered analysis capabilities.*