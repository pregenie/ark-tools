# ARK-TOOLS Development Standards

## 🎯 PROJECT OVERVIEW
ARK-TOOLS is a standalone intelligent code analysis system that combines MAMS static analysis with embedded LLM capabilities for semantic understanding of codebases.

## 🚀 QUICK START
```bash
# Analyze a codebase
ark-analyze /path/to/code --strategy hybrid

# Run tests
pytest tests/
npm test

# Check code quality
ark-tools check
```

## 🏗️ ARCHITECTURE OVERVIEW

### Core Components
- **MAMS Core**: Fast static analysis (milliseconds)
- **LLM Engine**: Semantic understanding (seconds)
- **Hybrid Analyzer**: Combines both approaches
- **Context Compressor**: Reduces code to AST skeletons for LLM

### Analysis Strategies
1. **Fast**: MAMS only - structural analysis in milliseconds
2. **Deep**: LLM only - semantic understanding in seconds
3. **Hybrid**: Both - complete analysis with reconciliation

## 🐳 DOCKER ENVIRONMENT

### Container Architecture
```
ark_tools_postgres      : PostgreSQL database (port 5432)
ark_tools_redis         : Redis cache (port 6379)
ark_tools_api           : FastAPI/Flask backend (port 8000)
ark_tools_websocket     : WebSocket service (port 8001)
ark_tools_nginx         : Nginx proxy (port 80)
ark_tools_prometheus    : Monitoring (port 9090)
ark_tools_grafana       : Dashboards (port 3000)
```

### Essential Commands
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f ark_tools_api

# Run analysis
docker-compose exec ark_tools_api ark-analyze /workspace

# Install Python dependencies
docker-compose exec ark_tools_api poetry add package

# Run tests
docker-compose exec ark_tools_api pytest
```

## 🤖 LLM INTEGRATION

### Supported Models
1. **CodeLlama-7B-Instruct** (Primary)
   - Best for code understanding
   - 3.8GB quantized

2. **Mistral-7B-Instruct** (Fallback)
   - General purpose
   - 4.1GB quantized

3. **Phi-2** (Lightweight)
   - Fast, small model
   - 1.5GB

### Model Management
```bash
# Download models
ark-tools models download codellama-7b-instruct

# List models
ark-tools models list

# Check status
ark-tools models status
```

## 📊 MAMS INTEGRATION

### Core Components from arkyvus_mams_tools
- `mams_002_backend_discovery_v2.py` - Service discovery
- `mams_008_dependency_resolution_engine.py` - Dependencies
- `MAMS_MASTER_MAPPING.json` - 2,876 file mappings

### Context Compression
- Reduces token usage by ~80%
- Preserves semantic meaning
- Enables full codebase analysis within LLM limits

## 🧪 TESTING STANDARDS

### Test Categories
1. **Unit Tests**: Individual components
2. **Integration Tests**: MAMS + LLM integration
3. **E2E Tests**: Full analysis pipeline

### Test Commands
```bash
# All tests
pytest

# Specific module
pytest tests/test_mams_core.py

# With coverage
pytest --cov=ark_tools

# Frontend tests
npm test
```

## 📝 CODING STANDARDS

### Python Standards
- Use type hints for all functions
- Follow PEP 8
- Use `debug_log` for structured logging
- Handle exceptions with context

### Frontend Standards
- TypeScript for all components
- React functional components with hooks
- TanStack Query for data fetching
- Proper error boundaries

### API Standards
- RESTful endpoints
- Consistent error responses
- OpenAPI documentation
- Rate limiting on expensive operations

## 🔍 DEBUGGING

### Debug Logging
```python
from ark_tools.utils.debug_logger import debug_log

# Category-specific logging
debug_log.mams("MAMS analysis starting", level="DEBUG")
debug_log.llm("LLM inference complete", level="INFO")
debug_log.agent("Architect agent activated", level="DEBUG")
debug_log.error_trace("Analysis failed", exception=e)
```

### Common Issues
1. **LLM Memory Error**: Reduce batch size or use smaller model
2. **MAMS Import Error**: Ensure MAMS_MASTER_MAPPING.json exists
3. **Token Limit Exceeded**: Increase compression or reduce file count

## 🚀 DEPLOYMENT

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/ark_tools
REDIS_URL=redis://localhost:6379

# Optional
ARK_LLM_MODEL_PATH=/models/codellama-7b.gguf
ARK_LLM_CONTEXT_SIZE=8192
ARK_LLM_THREADS=8
ARK_ENABLE_GPU=true
```

### Production Checklist
- [ ] Models downloaded and verified
- [ ] Database migrations applied
- [ ] Redis cache configured
- [ ] WebSocket service running
- [ ] Nginx configured for proxy
- [ ] Monitoring enabled

## 📊 PERFORMANCE BENCHMARKS

### Expected Performance
| Operation | Files | Time | Memory |
|-----------|-------|------|--------|
| MAMS Analysis | 1,000 | 150ms | 200MB |
| LLM Analysis | 1,000 | 4s | 4GB |
| Hybrid Analysis | 1,000 | 4.5s | 4.2GB |

### Optimization Tips
- Cache LLM results aggressively
- Use context compression for large codebases
- Batch similar files together
- Run MAMS and LLM in parallel when possible

## 🎯 DEVELOPMENT WORKFLOW

### Feature Development
1. Create feature branch: `git checkout -b feature/name`
2. Write tests first (TDD)
3. Implement feature
4. Run full test suite
5. Update documentation
6. Create pull request

### Code Review Checklist
- [ ] Tests pass
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] No hardcoded values
- [ ] Error handling complete
- [ ] Logging appropriate
- [ ] Performance acceptable

## 🔒 SECURITY

### Security Principles
- All analysis runs locally (no external API calls)
- LLM models stored locally
- Cache encrypted at rest
- No telemetry or tracking
- Read-only source analysis (never modifies original code)

### API Security
- JWT authentication for API endpoints
- Rate limiting on expensive operations
- Input validation on all endpoints
- SQL injection protection
- XSS prevention in web UI

## 📚 KEY CONCEPTS

### Domain Discovery
The process of identifying business domains in code:
1. MAMS extracts structural components
2. Context compressor creates AST skeletons
3. LLM analyzes skeletons for semantic meaning
4. User confirms discovered domains

### Three-Tier Analysis
1. **Fast Tier**: MAMS static analysis (milliseconds)
2. **Deep Tier**: LLM semantic analysis (seconds)
3. **Hybrid Tier**: Reconciled results with user confirmation

### Agent Architecture
- `ArchitectAgent`: Extended with hybrid analysis capability
- `BaseAgent`: Foundation for all agents
- Non-blocking async operations
- Integrated with existing ARK-TOOLS patterns

## 🆘 SUPPORT

### Getting Help
- GitHub Issues: https://github.com/ark-tools/ark-tools/issues
- Documentation: https://ark-tools.readthedocs.io
- Discord: https://discord.gg/ark-tools

### Common Commands Reference
```bash
# Analysis
ark-analyze /path --strategy hybrid
ark-transform --plan analysis_123

# Development
docker-compose up -d
pytest --cov=ark_tools
npm test

# Production
ark-tools check --production
ark-tools deploy --environment production

# Debugging
docker-compose logs -f ark_tools_api
ark-tools debug --verbose
```

---

**Last Updated**: January 2025
**Version**: 2.0
**Status**: Production Ready