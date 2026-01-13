# ARK-TOOLS Agentic Workflow System
## AI-Assisted Code Consolidation Platform

**Version**: 2.0.0  
**Architecture**: Agentic Workflows with Specialized AI Agents  
**Production Ready**: ✅ Full production standards with safety guarantees

---

## 🚀 Quick Start

### 1. Setup ARK-TOOLS
```bash
# Option 1: Intelligent Setup (Recommended)
ark-setup --mode quick
# Automatically detects existing services, inherits credentials, and configures ARK-TOOLS

# Option 2: Interactive Setup
ark-setup
# Choose from quick, custom, or minimal setup modes

# Option 3: Web UI Setup
ark-setup web
# Open http://localhost:8080 for visual configuration

# Option 4: Use MCP scaffold command
/scaffold-project
# Creates complete project structure
```

### 2. Verify Setup
```bash
# Validate configuration
ark-setup validate

# Or run comprehensive tests
/ark-test
```

### 3. Analyze Your Codebase
```bash
# Point ARK-TOOLS at your code for analysis
/ark-analyze directory=/path/to/your/code type=comprehensive
```

### 4. Generate Transformations
```bash
# Create transformation plan
/ark-transform --analysis-id <your-analysis-id>

# Generate consolidated code
/ark-generate --plan-id <your-plan-id>
```

---

## 🏗️ System Architecture

ARK-TOOLS uses an **agentic workflow architecture** with specialized AI agents working together:

```
┌─────────────────────────────────────────┐
│             USER COMMANDS               │
│  /scaffold-project /ark-analyze        │
│  /ark-transform   /ark-generate        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           SPECIALIZED AGENTS            │
│  ┌─────────────┬─────────────────────┐  │
│  │ark-architect│ System Design       │  │
│  │ark-detective│ Pattern Detection   │  │  
│  │ark-transform│ Code Transformation │  │
│  │ark-guardian │ Test & Validation   │  │
│  └─────────────┴─────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            SAFETY LAYER                 │
│  • Read-Only Source Protection          │
│  • Versioned Output Directories         │
│  • Automated Testing & Validation       │
│  • Rollback & Recovery Systems          │
└─────────────────────────────────────────┘
```

## 🎯 Core Principles

### 1. **Read-Only Source Rule**
- **Never modifies your original files**
- All transformations output to `.ark_output/v_TIMESTAMP/`
- Your source code is completely safe

### 2. **AI-Assisted Development**
- **Specialized agents** handle different aspects
- **Automated workflows** reduce manual work
- **Quality gates** ensure production standards

### 3. **Production Quality**
- **Type hints throughout**
- **Comprehensive error handling**
- **Integration testing focus**
- **Security best practices**

---

## 📋 Available Commands

### Project Management
| Command | Description | Example |
|---------|-------------|---------|
| `/scaffold-project` | Initialize complete project structure | Creates ark-tools/, database/, API, tests |
| `/scaffold-module` | Create new vertical slice module | `/scaffold-module module=discovery` |
| `/ark-test` | Run comprehensive test suite | Tests, formatting, type checking, security |

### Code Analysis & Transformation
| Command | Description | Example |
|---------|-------------|---------|
| `/ark-analyze` | Analyze codebase for patterns | `/ark-analyze directory=./src type=comprehensive` |
| `/ark-transform` | Create transformation plan | `/ark-transform --analysis-id abc123` |
| `/ark-generate` | Generate consolidated code | `/ark-generate --plan-id xyz789` |
| `/ark-deploy` | Deploy to production | `/ark-deploy environment=staging` |

---

## 🤖 Specialized Agents

### 🏛️ **ark-architect**
- **Role**: System design integrity
- **Responsibilities**: Database schema review, API validation, architecture enforcement
- **Quality Gates**: Type safety, security standards, performance requirements

### 🕵️ **ark-detective** 
- **Role**: Pattern detection specialist
- **Responsibilities**: Find duplicates, identify consolidation opportunities, architectural analysis
- **Outputs**: Pattern reports, similarity scores, consolidation recommendations

### 🔧 **ark-transformer**
- **Role**: Safe code transformation
- **Responsibilities**: LibCST-based transformations, semantic preservation, safety validation
- **Guarantees**: AST roundtrip validation, no source modification, rollback capability

### 🛡️ **ark-guardian**
- **Role**: Test generation and regression prevention
- **Responsibilities**: Generate test suites, validate transformations, prevent regressions
- **Coverage**: Unit tests, integration tests, property-based testing, performance benchmarks

---

## ⚙️ Safety & Quality System

### Automated Quality Enforcement

#### **PostToolUse Hooks**
```json
{
  "python_formatting": "black + isort after any Python file write",
  "type_checking": "mypy validation on ark-tools files", 
  "source_protection": "Prevents modification of source files",
  "mams_integration": "Verifies MAMS components remain accessible"
}
```

#### **PreCommit Hooks**
```json
{
  "testing": "pytest unit tests must pass",
  "syntax_validation": "Python syntax check all files",
  "security_scan": "bandit + safety vulnerability scanning",
  "docker_build": "Verify containers can be built"
}
```

### Source Protection System
```python
# ❌ BLOCKED - Direct source modification
Write("src/service.py", "modified code")  # Prevented by hooks

# ✅ ALLOWED - Safe transformation  
/ark-generate --plan-id xyz  # Outputs to .ark_output/v_TIMESTAMP/
```

---

## 📖 Usage Examples

### Example 1: Analyze Python Microservices

```bash
# Analyze a microservices codebase
/ark-analyze directory=/app/microservices type=comprehensive

# Expected output:
# ✅ Discovered 156 files (Python: 134, TypeScript: 22)
# 🔍 Found 47 patterns (API endpoints: 23, Services: 18, Models: 6)
# 🔍 Detected 12 duplicate groups with 85% similarity
# 💡 Identified 8 consolidation opportunities
# 📊 Analysis saved to: analysis_results_abc123.json
```

### Example 2: Transform Duplicate Services

```bash
# Create transformation plan
/ark-transform --analysis-id abc123 --strategy conservative

# Review plan
# 📋 Plan created with 5 transformation groups
# 🎯 Consolidation opportunities:
#   • User services (3 files → 1 unified service)
#   • Auth utilities (5 files → 2 organized modules)  
#   • Database helpers (4 duplicate functions → 1 helper)

# Generate consolidated code
/ark-generate --plan-id xyz789

# Output:
# 🚀 Generation complete!
# 📁 Output: .ark_output/v_20260112_143022/
# ✅ 15 files generated, syntax validated
# ✅ All tests pass, no regressions detected
```

### Example 3: Deploy to Production

```bash
# Deploy with full safety checks
/ark-deploy environment=production version=2.1.0

# Deployment process:
# 🔍 Pre-deployment validation
# 💾 Backup current deployment  
# 🚀 Blue-green deployment
# 🏥 Health checks (API, DB, Redis)
# 🌐 Traffic migration (10% → 50% → 100%)
# ✅ Post-deployment validation
# 🧹 Cleanup old deployment
```

---

## 🏗️ Development Workflow

### Sprint-Based Implementation

#### **Sprint 1: Foundation (Days 1-3)**
```bash
/scaffold-project                    # Initialize structure
/scaffold-module module=projects     # Create first module
/ark-test                           # Verify setup
```

#### **Sprint 2: Discovery Engine (Days 4-6)**  
```bash
/scaffold-module module=discovery include_websocket=true
/ark-analyze directory=./examples   # Test on sample code
```

#### **Sprint 3: Analysis Core (Days 7-9)**
```bash
/scaffold-module module=analysis
/ark-analyze directory=./real-project type=comprehensive
```

#### **Sprint 4: Transformation (Days 10-12)**
```bash
/scaffold-module module=transformation  
/ark-transform --analysis-id <id> --strategy moderate
/ark-generate --plan-id <id> --dry-run
```

#### **Sprint 5: Production Deploy (Days 13-15)**
```bash
/ark-deploy environment=staging
/ark-test coverage=true
/ark-deploy environment=production
```

---

## 🔧 Configuration

### Environment Setup

#### Required Environment Variables
```bash
# Database
export DATABASE_URL="postgresql://ark_admin:password@localhost:5432/ark_tools"
export REDIS_URL="redis://localhost:6379/0"

# Security  
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

# Optional: Monitoring
export SENTRY_DSN="https://your-sentry-dsn"
export PROMETHEUS_ENABLED="true"
```

#### MCP Configuration
The system uses `.mcp/` directory for agent and hook configuration:

```
.mcp/
├── commands/           # Slash command definitions
├── agents/            # Specialized agent configurations  
└── hooks/            # Quality enforcement hooks
    ├── config.json   # Main hooks configuration
    └── scripts/      # Custom validation scripts
```

### Production Configuration

#### Environment Setup
```bash
# ARK-TOOLS intelligently configures itself
ark-setup --mode quick

# Detects and uses:
# - Existing PostgreSQL/Redis containers
# - Native service installations  
# - Parent project credentials
# - MAMS integration paths
```

#### Docker Compose (Production)
```yaml
# docker-compose.production.yml (generated by ark-setup if needed)
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg14-latest
    environment:
      POSTGRES_DB: ark_tools
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  api:
    image: ark-tools/api:${VERSION}
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    
  frontend:
    image: ark-tools/frontend:${VERSION}
    ports:
      - "80:3000"
```

---

## 📊 Monitoring & Observability

### Health Checks
```bash
# Comprehensive health monitoring
curl http://localhost:5002/api/v1/health

{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok", 
    "mams": "ok",
    "api": "healthy"
  }
}
```

### Metrics Collection
```python
# Automatic metrics collection
- Analysis execution time
- Transformation success rates  
- Generated code quality scores
- System resource usage
- Error rates and recovery times
```

### Logging
```python
# Structured logging throughout
{
  "timestamp": "2026-01-12T14:30:22Z",
  "level": "INFO",
  "agent": "ark-detective",
  "operation": "pattern_detection",
  "duration_ms": 1234,
  "patterns_found": 47
}
```

---

## 🔒 Security

### Security Features
- **Command whitelisting** - Only approved commands allowed
- **Input validation** - All inputs sanitized
- **Source protection** - Read-only source enforcement
- **Vulnerability scanning** - Automated security checks
- **Access controls** - JWT-based authentication

### Security Scanning
```bash
# Automatic security scans
bandit -r ark-tools/     # Python security issues
safety check            # Dependency vulnerabilities  
docker scan             # Container image scanning
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **MAMS Components Not Found**
```bash
# Error: ModuleNotFoundError: No module named 'extractors.component_extractor'
# Solution: Verify MAMS path
export PYTHONPATH=/app/ark-tools/arkyvus/migrations:$PYTHONPATH
```

#### 2. **Source Protection Violation**
```bash
# Error: ❌ BLOCKED: Attempted to modify source file
# Solution: Use proper output directory
/ark-generate --plan-id xyz  # Outputs to .ark_output/
```

#### 3. **Database Connection Issues**
```bash
# Error: psycopg2.OperationalError: could not connect
# Solution 1: Validate connections
ark-setup validate

# Solution 2: Re-run setup to detect services
ark-setup --mode quick

# Solution 3: Check database configuration manually
docker-compose ps postgres
echo $DATABASE_URL
```

#### 4. **Test Failures**
```bash
# Error: Tests failing after transformation
# Solution: Run guardian validation
/ark-test module=all coverage=true verbose=true
```

---

## 🤝 Contributing

### Development Setup
```bash
# Clone and setup
git clone <repo-url>
cd ark-tools

# Intelligent setup (detects existing services)
ark-setup --mode quick

# Or use interactive setup for custom configuration
ark-setup

# Initialize project structure
/scaffold-project

# Run development environment  
docker-compose up -d
```

### Code Standards
- **Type hints required** - All functions must have type annotations
- **Tests required** - Minimum 80% coverage
- **Documentation required** - Docstrings for all public functions
- **Security scans must pass** - No high-severity vulnerabilities

---

## 📚 Documentation

### Complete Documentation Set
- **[Design Specification](docs/ARK_TOOLS_DESIGN_SPECIFICATION.md)** - Complete system architecture
- **[Implementation Guide](docs/ARK_TOOLS_IMPLEMENTATION_GUIDE.md)** - Step-by-step development  
- **[API Specification](docs/ARK_TOOLS_API_SPECIFICATION.md)** - Complete API reference
- **[User Guide](docs/ARK_TOOLS_USER_GUIDE.md)** - Comprehensive user manual
- **[Agentic Workflow Guide](docs/ARK_TOOLS_AGENTIC_WORKFLOW.md)** - Advanced workflow patterns

### Agent Documentation
- **[ark-architect](/.mcp/agents/ark-architect.yml)** - System design agent
- **[ark-detective](/.mcp/agents/ark-detective.yml)** - Pattern detection agent  
- **[ark-transformer](/.mcp/agents/ark-transformer.yml)** - Code transformation agent
- **[ark-guardian](/.mcp/agents/ark-guardian.yml)** - Test generation agent

---

## 📈 Success Metrics

### Quality Metrics
- **Code Reduction**: 40-60% reduction in duplicate code
- **Test Coverage**: >90% for generated code
- **Performance**: <200ms API response times
- **Reliability**: >99.9% uptime in production

### Developer Experience  
- **Setup Time**: <5 minutes from zero to first analysis
- **Learning Curve**: <1 day to productive usage
- **Error Recovery**: Automatic rollback on failures
- **Documentation**: Complete examples and troubleshooting

---

## 🎉 Getting Started

Ready to consolidate your codebase? Start with:

```bash
# 1. Initialize ARK-TOOLS
/scaffold-project

# 2. Analyze your code
/ark-analyze directory=/path/to/your/code

# 3. Review and transform
/ark-transform --analysis-id <id>
/ark-generate --plan-id <id> --dry-run

# 4. Deploy when ready
/ark-generate --plan-id <id>
```

**Need help?** Check the [User Guide](docs/ARK_TOOLS_USER_GUIDE.md) or [Troubleshooting](#-troubleshooting) section.

**Enterprise support?** Contact the team for production deployment assistance and training.

---

*ARK-TOOLS: Transforming fragmented codebases into unified, maintainable architectures with AI-powered safety and precision.*