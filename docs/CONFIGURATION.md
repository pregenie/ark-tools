# ARK-TOOLS Configuration Reference

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Environment Variables](#environment-variables)
3. [Configuration Files](#configuration-files)
4. [Core Settings](#core-settings)
5. [LLM Configuration](#llm-configuration)
6. [Database Configuration](#database-configuration)
7. [Cache Configuration](#cache-configuration)
8. [API Configuration](#api-configuration)
9. [Analysis Settings](#analysis-settings)
10. [Security Settings](#security-settings)
11. [Performance Tuning](#performance-tuning)
12. [Advanced Configuration](#advanced-configuration)

## Configuration Overview

ARK-TOOLS uses a hierarchical configuration system:

1. **Default Values** - Built-in defaults
2. **Configuration Files** - `config.yaml`, `settings.json`
3. **Environment Variables** - `.env` file or system environment
4. **Command-Line Arguments** - Runtime overrides

Priority order (highest to lowest):
```
CLI Arguments > Environment Variables > Config Files > Defaults
```

## Environment Variables

### Creating .env File

```bash
# Copy template
cp .env.example .env

# Edit configuration
vim .env
```

### Complete .env Reference

```bash
# ============================================
# ARK-TOOLS CONFIGURATION
# ============================================

# --------------------------------------------
# Core Settings
# --------------------------------------------
# Environment: development, staging, production
ARK_TOOLS_ENV=production

# Debug mode
ARK_DEBUG=false

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
ARK_LOG_LEVEL=INFO

# Log output: console, file, both
ARK_LOG_OUTPUT=both

# Log directory
ARK_LOG_DIR=~/.ark_tools/logs

# --------------------------------------------
# LLM Configuration
# --------------------------------------------
# Model file path (GGUF format)
ARK_LLM_MODEL_PATH=~/.ark_tools/models/codellama-7b-instruct.Q4_K_M.gguf

# Context window size (tokens)
ARK_LLM_CONTEXT_SIZE=8192

# Maximum generation tokens
ARK_LLM_MAX_TOKENS=2048

# CPU threads for inference
ARK_LLM_THREADS=4

# Temperature (0.0 = deterministic, 1.0 = creative)
ARK_LLM_TEMPERATURE=0.1

# Top-p sampling
ARK_LLM_TOP_P=0.95

# Top-k sampling
ARK_LLM_TOP_K=40

# Repeat penalty
ARK_LLM_REPEAT_PENALTY=1.1

# Enable GPU acceleration
ARK_LLM_ENABLE_GPU=false

# GPU layers to offload (0 = CPU only)
ARK_LLM_GPU_LAYERS=32

# GPU device ID (for multi-GPU systems)
ARK_LLM_GPU_DEVICE=0

# --------------------------------------------
# Database Configuration
# --------------------------------------------
# Database URL (PostgreSQL)
DATABASE_URL=postgresql://ark:password@localhost:5432/ark_tools

# Database pool size
DATABASE_POOL_SIZE=20

# Max overflow connections
DATABASE_MAX_OVERFLOW=40

# Connection timeout (seconds)
DATABASE_TIMEOUT=30

# Enable SQL logging
DATABASE_LOG_SQL=false

# --------------------------------------------
# Redis Cache Configuration
# --------------------------------------------
# Redis URL
REDIS_URL=redis://localhost:6379/0

# Max connections
REDIS_MAX_CONNECTIONS=50

# Connection timeout (seconds)
REDIS_TIMEOUT=5

# Cache TTL (seconds)
REDIS_CACHE_TTL=3600

# Enable cache
REDIS_ENABLED=true

# --------------------------------------------
# API Configuration
# --------------------------------------------
# API host
ARK_API_HOST=0.0.0.0

# API port
ARK_API_PORT=8100

# API base path
ARK_API_BASE_PATH=/api/v1

# Enable API documentation
ARK_API_DOCS=true

# API key (for authentication)
ARK_API_KEY=your-secret-api-key-here

# Enable CORS
ARK_API_CORS=true

# CORS origins (comma-separated)
ARK_API_CORS_ORIGINS=http://localhost:3000,https://app.example.com

# Rate limiting
ARK_API_RATE_LIMIT=100

# Rate limit window (seconds)
ARK_API_RATE_LIMIT_WINDOW=60

# --------------------------------------------
# Analysis Settings
# --------------------------------------------
# Default strategy: hybrid, fast, deep, compress_only
ARK_ANALYSIS_STRATEGY=hybrid

# Maximum files to analyze
ARK_ANALYSIS_MAX_FILES=50

# Maximum file size (bytes)
ARK_ANALYSIS_MAX_FILE_SIZE=10485760

# Exclude patterns (comma-separated)
ARK_ANALYSIS_EXCLUDE=*.pyc,__pycache__,node_modules,.git

# Include hidden files
ARK_ANALYSIS_INCLUDE_HIDDEN=false

# Compression ratio target
ARK_ANALYSIS_COMPRESSION_TARGET=0.8

# --------------------------------------------
# Security Settings
# --------------------------------------------
# Secret key for sessions
ARK_SECRET_KEY=change-this-to-random-secret-key

# Enable authentication
ARK_ENABLE_AUTH=true

# JWT expiration (seconds)
ARK_JWT_EXPIRATION=86400

# Password hash rounds
ARK_PASSWORD_ROUNDS=12

# Allowed file extensions
ARK_ALLOWED_EXTENSIONS=.py,.js,.ts,.jsx,.tsx,.java,.go,.rs,.cpp,.c,.h

# Maximum upload size (bytes)
ARK_MAX_UPLOAD_SIZE=104857600

# --------------------------------------------
# Performance Settings
# --------------------------------------------
# Worker processes
ARK_WORKER_PROCESSES=4

# Thread pool size
ARK_THREAD_POOL_SIZE=10

# Async timeout (seconds)
ARK_ASYNC_TIMEOUT=300

# Batch processing size
ARK_BATCH_SIZE=50

# Enable profiling
ARK_ENABLE_PROFILING=false

# --------------------------------------------
# Monitoring Settings
# --------------------------------------------
# Enable monitoring
ARK_ENABLE_MONITORING=true

# Metrics port
ARK_METRICS_PORT=9090

# Health check interval (seconds)
ARK_HEALTH_CHECK_INTERVAL=30

# Enable distributed tracing
ARK_ENABLE_TRACING=false

# Tracing endpoint
ARK_TRACING_ENDPOINT=http://localhost:14268/api/traces

# --------------------------------------------
# Report Settings
# --------------------------------------------
# Report output directory
ARK_REPORT_DIR=.ark_reports

# Generate markdown reports
ARK_REPORT_MARKDOWN=true

# Generate HTML reports
ARK_REPORT_HTML=true

# Generate JSON reports
ARK_REPORT_JSON=true

# Report retention days
ARK_REPORT_RETENTION_DAYS=30

# --------------------------------------------
# Feature Flags
# --------------------------------------------
# Enable WebSocket support
ARK_ENABLE_WEBSOCKETS=true

# Enable real-time updates
ARK_ENABLE_REALTIME=true

# Enable experimental features
ARK_ENABLE_EXPERIMENTAL=false

# Enable beta features
ARK_ENABLE_BETA=false
```

## Configuration Files

### config.yaml

```yaml
# ~/.ark_tools/config.yaml

ark_tools:
  # Core configuration
  core:
    environment: production
    debug: false
    log_level: INFO
    
  # Analysis configuration  
  analysis:
    default_strategy: hybrid
    max_files: 50
    max_file_size: 10485760  # 10MB
    excluded_patterns:
      - "*.pyc"
      - "__pycache__"
      - "node_modules"
      - ".git"
      - ".venv"
      - "*.log"
    supported_languages:
      - python
      - javascript
      - typescript
      - java
      - go
      - rust
    
  # LLM configuration
  llm:
    model_path: ~/.ark_tools/models/codellama-7b-instruct.gguf
    context_size: 8192
    max_tokens: 2048
    temperature: 0.1
    threads: 4
    gpu_enabled: false
    gpu_layers: 32
    
  # Performance settings
  performance:
    worker_processes: 4
    thread_pool_size: 10
    cache_enabled: true
    cache_ttl: 3600
    batch_size: 50
    
  # Security settings
  security:
    enable_auth: true
    jwt_expiration: 86400
    allowed_origins:
      - http://localhost:3000
      - https://app.example.com
    rate_limit:
      requests: 100
      window: 60
      
  # Feature flags
  features:
    websockets: true
    realtime_updates: true
    experimental: false
    beta: false
```

### settings.json

```json
{
  "arkTools": {
    "version": "0.1.0",
    "core": {
      "environment": "production",
      "debug": false,
      "logLevel": "INFO"
    },
    "analysis": {
      "strategies": {
        "hybrid": {
          "enabled": true,
          "priority": 1,
          "maxFiles": 75,
          "compressionTarget": 0.8
        },
        "fast": {
          "enabled": true,
          "priority": 2,
          "maxFiles": 150,
          "skipLLM": true
        },
        "deep": {
          "enabled": true,
          "priority": 3,
          "maxFiles": 30,
          "enhancedContext": true
        }
      }
    },
    "models": {
      "available": [
        {
          "name": "CodeLlama-7B-Instruct",
          "path": "~/.ark_tools/models/codellama-7b-instruct.gguf",
          "contextSize": 8192,
          "recommended": true
        },
        {
          "name": "Mistral-7B-Instruct",
          "path": "~/.ark_tools/models/mistral-7b-instruct.gguf",
          "contextSize": 8192
        },
        {
          "name": "Phi-2",
          "path": "~/.ark_tools/models/phi-2.gguf",
          "contextSize": 2048
        }
      ]
    }
  }
}
```

## Core Settings

### Environment Modes

| Mode | Debug | Logging | Caching | Performance |
|------|-------|---------|---------|-------------|
| development | ON | DEBUG | OFF | Profiling ON |
| staging | OFF | INFO | ON | Monitoring ON |
| production | OFF | WARNING | ON | Optimized |

### Logging Configuration

```python
# Python configuration
import logging

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'ark_tools.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}
```

## LLM Configuration

### Model Selection

```bash
# CodeLlama (Best for code analysis)
ARK_LLM_MODEL_PATH=~/.ark_tools/models/codellama-7b-instruct.Q4_K_M.gguf
ARK_LLM_CONTEXT_SIZE=8192

# Mistral (General purpose)
ARK_LLM_MODEL_PATH=~/.ark_tools/models/mistral-7b-instruct.Q4_K_M.gguf
ARK_LLM_CONTEXT_SIZE=8192

# Phi-2 (Fastest, smallest)
ARK_LLM_MODEL_PATH=~/.ark_tools/models/phi-2.Q4_K_M.gguf
ARK_LLM_CONTEXT_SIZE=2048
```

### Optimization Settings

```bash
# CPU Optimization
ARK_LLM_THREADS=8           # Set to number of CPU cores
ARK_LLM_BATCH_SIZE=512      # Larger = faster but more memory

# GPU Optimization
ARK_LLM_ENABLE_GPU=true
ARK_LLM_GPU_LAYERS=32       # Layers to offload to GPU
ARK_LLM_GPU_BATCH_SIZE=1024 # GPU batch size

# Memory Optimization
ARK_LLM_USE_MMAP=true       # Memory-mapped model loading
ARK_LLM_USE_MLOCK=false     # Lock model in RAM
```

## Database Configuration

### PostgreSQL

```bash
# Standard connection
DATABASE_URL=postgresql://user:password@localhost:5432/ark_tools

# With SSL
DATABASE_URL=postgresql://user:password@localhost:5432/ark_tools?sslmode=require

# Connection pool settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
```

### SQLite (Fallback)

```bash
# SQLite for development/testing
DATABASE_URL=sqlite:///~/.ark_tools/ark_tools.db

# In-memory database
DATABASE_URL=sqlite:///:memory:
```

## Cache Configuration

### Redis Settings

```bash
# Standard Redis
REDIS_URL=redis://localhost:6379/0

# Redis with password
REDIS_URL=redis://:password@localhost:6379/0

# Redis Sentinel
REDIS_SENTINELS=localhost:26379,localhost:26380
REDIS_MASTER_NAME=mymaster

# Cache strategies
REDIS_CACHE_STRATEGY=lru       # lru, lfu, ttl
REDIS_CACHE_MAX_ENTRIES=10000
REDIS_CACHE_TTL=3600
```

### In-Memory Cache

```python
# Python configuration
CACHE_CONFIG = {
    'type': 'memory',
    'max_size': 1000,
    'ttl': 3600,
    'strategy': 'lru'
}
```

## API Configuration

### CORS Settings

```python
# Python configuration
CORS_CONFIG = {
    'origins': ['http://localhost:3000', 'https://app.example.com'],
    'methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'headers': ['Content-Type', 'Authorization'],
    'credentials': True,
    'max_age': 3600
}
```

### Rate Limiting

```python
# Per-endpoint configuration
RATE_LIMITS = {
    '/api/v1/analyze': '10/minute',
    '/api/v1/compress': '20/minute',
    '/api/v1/reports': '100/minute',
    'default': '60/minute'
}
```

## Analysis Settings

### File Filtering

```yaml
# .arkignore file
# Exclude patterns
*.pyc
__pycache__/
node_modules/
.git/
.venv/
*.log
*.tmp
build/
dist/
*.egg-info/

# Include specific files even if matched above
!important.log
!config.tmp
```

### Language-Specific Settings

```yaml
languages:
  python:
    extensions: [.py]
    max_file_size: 10485760
    ast_parser: true
    
  javascript:
    extensions: [.js, .jsx]
    max_file_size: 5242880
    ast_parser: true
    
  typescript:
    extensions: [.ts, .tsx]
    max_file_size: 5242880
    ast_parser: true
```

## Security Settings

### Authentication

```python
# JWT Configuration
JWT_CONFIG = {
    'algorithm': 'HS256',
    'expiration': 86400,  # 24 hours
    'refresh_expiration': 604800,  # 7 days
    'issuer': 'ark-tools',
    'audience': 'ark-tools-api'
}
```

### Input Validation

```python
# Validation rules
VALIDATION_RULES = {
    'max_path_length': 4096,
    'max_file_size': 10485760,  # 10MB
    'allowed_schemes': ['file', 'http', 'https'],
    'forbidden_paths': ['/etc', '/sys', '/proc'],
    'sanitize_paths': True
}
```

## Performance Tuning

### Memory Management

```bash
# Memory limits
ARK_MAX_MEMORY=4GB
ARK_MEMORY_LIMIT_POLICY=strict  # strict, soft, none

# Garbage collection
ARK_GC_THRESHOLD=1000
ARK_GC_COLLECT_INTERVAL=300
```

### Concurrency Settings

```python
# Thread pool configuration
THREAD_POOL_CONFIG = {
    'core_threads': 4,
    'max_threads': 16,
    'keepalive_seconds': 60,
    'queue_size': 100
}

# Async configuration
ASYNC_CONFIG = {
    'max_workers': 10,
    'timeout': 300,
    'retry_count': 3,
    'retry_delay': 1
}
```

## Advanced Configuration

### Custom Strategies

```python
# ~/.ark_tools/custom_strategies.py

CUSTOM_STRATEGIES = {
    'security_focus': {
        'base_strategy': 'deep',
        'max_files': 100,
        'focus_patterns': ['auth*.py', 'security*.py', '*crypt*.py'],
        'enhanced_analysis': True,
        'llm_prompts': {
            'system': 'Focus on security vulnerabilities and best practices'
        }
    },
    'performance_audit': {
        'base_strategy': 'hybrid',
        'max_files': 75,
        'focus_patterns': ['*loop*.py', '*query*.py', '*cache*.py'],
        'metrics': ['complexity', 'performance', 'memory']
    }
}
```

### Plugin Configuration

```yaml
# ~/.ark_tools/plugins.yaml

plugins:
  enabled: true
  directory: ~/.ark_tools/plugins
  
  installed:
    - name: security-scanner
      version: 1.0.0
      enabled: true
      config:
        scan_level: high
        
    - name: dependency-analyzer
      version: 2.1.0
      enabled: true
      config:
        check_vulnerabilities: true
```

### Monitoring Configuration

```yaml
# Prometheus metrics
metrics:
  enabled: true
  port: 9090
  path: /metrics
  
  collectors:
    - analysis_duration
    - files_processed
    - tokens_used
    - cache_hits
    - error_rate
    
# Distributed tracing
tracing:
  enabled: false
  provider: jaeger
  endpoint: http://localhost:14268/api/traces
  sample_rate: 0.1
```

## Configuration Validation

### Validate Configuration

```bash
# Validate all settings
ark-setup validate

# Validate specific section
ark-setup validate --section llm
ark-setup validate --section database

# Test configuration
ark-tools test-config
```

### Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["ark_tools"],
  "properties": {
    "ark_tools": {
      "type": "object",
      "properties": {
        "core": {
          "type": "object",
          "properties": {
            "environment": {
              "type": "string",
              "enum": ["development", "staging", "production"]
            },
            "debug": {
              "type": "boolean"
            }
          }
        }
      }
    }
  }
}
```

## Configuration Best Practices

### Security
- Never commit `.env` files to version control
- Use strong, unique API keys
- Rotate secrets regularly
- Use environment-specific configurations

### Performance
- Tune thread count to CPU cores
- Adjust batch sizes based on memory
- Enable caching in production
- Use GPU acceleration when available

### Maintainability
- Document custom configurations
- Use descriptive variable names
- Keep development and production configs separate
- Regular configuration audits