# ARK-TOOLS User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Quick Start Tutorial](#quick-start-tutorial)
3. [Analyzing Codebases](#analyzing-codebases)
4. [Understanding Reports](#understanding-reports)
5. [Command-Line Usage](#command-line-usage)
6. [Web Interface](#web-interface)
7. [Best Practices](#best-practices)
8. [Use Cases](#use-cases)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

## Getting Started

### What is ARK-TOOLS?

ARK-TOOLS is an intelligent code analysis framework that helps you understand complex codebases through:

- **Structural Analysis**: Fast scanning of code structure using MAMS
- **Semantic Understanding**: Deep comprehension using embedded LLMs
- **Domain Discovery**: Automatic identification of functional domains
- **Smart Compression**: 80% token reduction while preserving meaning
- **Rich Reports**: Multi-format reports with actionable insights

### Prerequisites

Before starting, ensure you have:

1. Python 3.9 or higher installed
2. At least 8GB of RAM
3. 10GB of free disk space
4. (Optional) Docker for containerized deployment

## Quick Start Tutorial

### Step 1: Installation

```bash
# Install ARK-TOOLS with all features
pip install ark-tools[full]
```

### Step 2: Initial Setup

Run the interactive setup wizard:

```bash
ark-setup
```

Choose your setup mode:
- **Quick**: Automatic configuration with smart defaults
- **Custom**: Manual configuration with full control
- **Minimal**: Basic setup without external dependencies

### Step 3: Download an LLM Model

ARK-TOOLS needs a local LLM model for semantic analysis:

```bash
# Create models directory
mkdir -p ~/.ark_tools/models
cd ~/.ark_tools/models

# Download CodeLlama (recommended for code analysis)
wget https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf
```

### Step 4: Your First Analysis

Analyze a Python project:

```bash
ark-analyze analyze hybrid /path/to/your/project
```

View the results:

```bash
ark-analyze report view
```

## Analyzing Codebases

### Analysis Strategies

ARK-TOOLS offers different analysis strategies for various needs:

#### 1. Hybrid Analysis (Recommended)
Combines MAMS and LLM for comprehensive insights.

```bash
ark-analyze analyze hybrid /path/to/code --strategy hybrid
```

**Best for**: Complete understanding of new codebases

#### 2. Fast Analysis
MAMS-only structural analysis without LLM.

```bash
ark-analyze analyze hybrid /path/to/code --strategy fast
```

**Best for**: Quick structural overview, large codebases

#### 3. Deep Analysis
Enhanced LLM analysis with more context.

```bash
ark-analyze analyze hybrid /path/to/code --strategy deep
```

**Best for**: Detailed semantic understanding, smaller codebases

#### 4. Compression Only
Just compress code without analysis.

```bash
ark-analyze analyze hybrid /path/to/code --strategy compress_only
```

**Best for**: Preparing code for manual LLM analysis

### Analysis Options

```bash
ark-analyze analyze hybrid /path/to/code \
  --strategy hybrid \
  --max-files 100 \
  --output ./reports \
  --format all \
  --include-suggestions
```

**Options:**
- `--strategy`: Analysis strategy (hybrid/fast/deep/compress_only)
- `--max-files`: Maximum files to analyze (default: 50)
- `--output`: Output directory for reports
- `--format`: Report formats (json/markdown/html/all)
- `--include-suggestions`: Include code organization suggestions

### Analyzing Different Languages

ARK-TOOLS supports multiple programming languages:

#### Python Projects
```bash
ark-analyze analyze hybrid ./python_project
```

#### JavaScript/TypeScript
```bash
ark-analyze analyze hybrid ./js_project --max-files 75
```

#### Mixed Language Projects
```bash
ark-analyze analyze hybrid ./full_stack_app --strategy hybrid
```

## Understanding Reports

### Report Structure

After analysis, ARK-TOOLS generates comprehensive reports:

```
.ark_reports/
├── latest/                    # Most recent report
│   ├── master.json           # Complete analysis data
│   ├── summary.json          # Executive summary
│   ├── errors.json           # Any errors encountered
│   ├── manifest.json         # File inventory
│   └── presentation/
│       ├── report.md         # Markdown report
│       └── report.html       # Interactive HTML report
```

### Reading the Summary

The summary provides quick insights:

```json
{
  "metadata": {
    "timestamp": "2024-01-14T12:00:00Z",
    "directory": "/path/to/code",
    "strategy": "hybrid"
  },
  "statistics": {
    "total_files": 150,
    "total_components": 450,
    "total_domains": 6,
    "compression_ratio": 0.82
  },
  "key_insights": [
    "Well-structured authentication domain",
    "Database layer could benefit from abstraction",
    "Strong separation of concerns in API layer"
  ]
}
```

### Domain Discovery Results

Domains represent functional areas of your codebase:

```json
{
  "domains": [
    {
      "name": "Authentication",
      "description": "User authentication and authorization",
      "primary_components": [
        "auth_service.py",
        "jwt_handler.py",
        "permissions.py"
      ],
      "confidence": 0.92
    },
    {
      "name": "Data Processing",
      "description": "ETL and data transformation logic",
      "primary_components": [
        "etl_pipeline.py",
        "transformers.py",
        "validators.py"
      ],
      "confidence": 0.87
    }
  ]
}
```

### Viewing Reports

#### View Summary
```bash
ark-analyze report view --format summary
```

#### View Full JSON
```bash
ark-analyze report view --format json
```

#### View Markdown
```bash
ark-analyze report view --format markdown
```

#### Open HTML in Browser
```bash
ark-analyze report view --format html
# Opens: file:///path/to/report.html
```

## Command-Line Usage

### Main Commands

#### Analysis Commands
```bash
# Run hybrid analysis
ark-analyze analyze hybrid /path/to/code

# Compress code only
ark-analyze analyze compress /path/to/code

# With custom options
ark-analyze analyze hybrid ./myproject \
  --max-files 100 \
  --output ./analysis \
  --include-suggestions
```

#### Report Commands
```bash
# Generate report from existing analysis
ark-analyze report generate analysis.json --format all

# View latest report
ark-analyze report view

# View specific report
ark-analyze report view --report-id 2024-01-14_120000

# View report history
ark-analyze report history

# Clean up old reports
ark-analyze report clean
```

#### Utility Commands
```bash
# Check model status
ark-analyze model

# Start API server
ark-analyze server
```

### Using the API Server

Start the server:
```bash
ark-server
# Server starts at http://localhost:8100
```

Make API requests:
```bash
# Run analysis
curl -X POST http://localhost:8100/api/v1/hybrid/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "directory": "/path/to/code",
    "strategy": "hybrid",
    "max_files": 50
  }'

# Get model info
curl http://localhost:8100/api/v1/hybrid/model/info
```

## Web Interface

### Starting the Web UI

```bash
ark-setup web --port 8080
# Opens http://localhost:8080
```

### Web UI Features

1. **Visual Analysis**
   - Directory browser
   - Drag-and-drop support
   - Real-time progress

2. **Interactive Reports**
   - Domain visualization
   - Component relationships
   - Code metrics charts

3. **Configuration**
   - Model selection
   - Strategy tuning
   - Output preferences

## Best Practices

### 1. Choosing the Right Strategy

| Codebase Size | Recommended Strategy | Max Files |
|---------------|---------------------|-----------|
| Small (<100 files) | Deep | 50 |
| Medium (100-500) | Hybrid | 75 |
| Large (500-2000) | Hybrid | 100 |
| Very Large (2000+) | Fast | 150 |

### 2. Optimizing Analysis

#### Pre-Analysis Cleanup
```bash
# Remove build artifacts
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove node_modules for JS projects
find . -type d -name "node_modules" -exec rm -rf {} +
```

#### Exclude Patterns
Create `.arkignore` file:
```
*.pyc
__pycache__
node_modules/
.git/
*.log
build/
dist/
```

### 3. Iterative Analysis

Start broad, then focus:

```bash
# Step 1: Quick overview
ark-analyze analyze hybrid ./project --strategy fast

# Step 2: Focus on core
ark-analyze analyze hybrid ./project/src --strategy hybrid

# Step 3: Deep dive into complex areas
ark-analyze analyze hybrid ./project/src/core --strategy deep
```

### 4. Report Management

```bash
# Keep reports organized
ark-analyze analyze hybrid ./project --output ./reports/$(date +%Y%m%d)

# Compare analyses over time
diff .ark_reports/latest/summary.json .ark_reports/previous/summary.json

# Archive important reports
tar czf analysis_backup.tar.gz .ark_reports/
```

## Use Cases

### 1. Code Review and Onboarding

**Scenario**: New developer joining the team

```bash
# Generate comprehensive analysis
ark-analyze analyze hybrid ./codebase --include-suggestions

# Create onboarding report
ark-analyze report generate analysis.json --format html

# Share report
cp .ark_reports/latest/presentation/report.html ./onboarding/
```

### 2. Architecture Documentation

**Scenario**: Document system architecture

```bash
# Analyze with focus on structure
ark-analyze analyze hybrid ./system --strategy hybrid

# Extract architecture insights
jq '.domains' .ark_reports/latest/master.json > architecture.json

# Generate architecture document
ark-analyze report generate analysis.json --format markdown
```

### 3. Technical Debt Assessment

**Scenario**: Identify areas needing refactoring

```bash
# Deep analysis with suggestions
ark-analyze analyze hybrid ./legacy_code \
  --strategy deep \
  --include-suggestions

# Review suggestions
jq '.suggestions' .ark_reports/latest/master.json
```

### 4. Pre-Migration Analysis

**Scenario**: Preparing for framework migration

```bash
# Comprehensive analysis
ark-analyze analyze hybrid ./old_framework \
  --max-files 200 \
  --strategy hybrid

# Focus on dependencies
grep -r "import\|require" .ark_reports/latest/manifest.json
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Model not found"
```bash
# Check model path
ark-analyze model

# Download model if missing
cd ~/.ark_tools/models
wget [model_url]

# Update configuration
export ARK_LLM_MODEL_PATH=~/.ark_tools/models/model.gguf
```

#### Issue: "Out of memory"
```bash
# Reduce batch size
ark-analyze analyze hybrid ./code --max-files 25

# Use fast strategy
ark-analyze analyze hybrid ./code --strategy fast

# Increase swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Issue: "Analysis takes too long"
```bash
# Use fewer files
ark-analyze analyze hybrid ./code --max-files 30

# Use faster model
export ARK_LLM_MODEL_PATH=~/.ark_tools/models/phi-2.gguf

# Enable GPU acceleration
export ARK_LLM_ENABLE_GPU=true
```

#### Issue: "Permission denied"
```bash
# Check file permissions
ls -la /path/to/code

# Run with proper permissions
sudo ark-analyze analyze hybrid ./code

# Or change ownership
sudo chown -R $USER:$USER ./code
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Set debug environment
export ARK_DEBUG=true
export ARK_LOG_LEVEL=DEBUG

# Run with verbose flag
ark-analyze --verbose analyze hybrid ./code

# Check logs
tail -f ~/.ark_tools/logs/ark-tools.log
```

## FAQ

### General Questions

**Q: How long does analysis take?**
A: Typically 30 seconds to 5 minutes depending on codebase size and strategy.

**Q: Can I analyze private code?**
A: Yes, all analysis is performed locally. No code leaves your machine.

**Q: What languages are supported?**
A: Python, JavaScript, TypeScript, Java, Go, C++, and more.

**Q: How accurate is domain discovery?**
A: Typically 80-95% accurate with proper model and sufficient context.

### Technical Questions

**Q: Can I use my own LLM model?**
A: Yes, any GGUF format model can be used. Update ARK_LLM_MODEL_PATH.

**Q: How much memory do I need?**
A: Minimum 8GB RAM, recommended 16GB for large codebases.

**Q: Can I run without Docker?**
A: Yes, ARK-TOOLS can run directly on the host system.

**Q: Is GPU required?**
A: No, GPU is optional but speeds up LLM inference significantly.

### Best Practices Questions

**Q: How many files should I analyze?**
A: Start with 50, increase if needed. Quality over quantity.

**Q: Should I include tests in analysis?**
A: Usually no, unless analyzing test architecture specifically.

**Q: How often should I run analysis?**
A: After major changes, before refactoring, or monthly for tracking.

**Q: Can I customize the analysis?**
A: Yes, through configuration files and custom strategies.

## Getting Help

### Resources

- **Documentation**: `/docs` folder in installation
- **Examples**: `/examples` folder with sample analyses
- **API Docs**: `http://localhost:8100/docs` when server is running

### Support Channels

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Community forum for questions
- **Email**: support@ark-tools.io

### Diagnostic Commands

```bash
# System check
ark-tools diagnose

# Version info
ark-analyze --version

# Configuration check
ark-setup validate

# Generate support bundle
ark-tools support-bundle
```