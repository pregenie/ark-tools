# ARK-TOOLS Documentation

## Overview

ARK-TOOLS is an intelligent code consolidation and analysis framework that combines fast structural analysis (MAMS) with semantic understanding (embedded LLM) to provide comprehensive insights into codebases.

## Documentation Structure

### Core Documentation

- **[Architecture Guide](ARCHITECTURE.md)** - System design, components, and integration patterns
- **[Installation Guide](INSTALLATION.md)** - Setup instructions and requirements
- **[User Guide](USER_GUIDE.md)** - How to use ARK-TOOLS for code analysis
- **[Administration Guide](ADMIN_GUIDE.md)** - System administration and maintenance
- **[Technical Reference](TECHNICAL_REFERENCE.md)** - API documentation and technical details
- **[Configuration Reference](CONFIGURATION.md)** - Complete configuration options

### Specialized Guides

- **[CLI Reference](CLI_REFERENCE.md)** - Command-line interface documentation
- **[API Documentation](API_DOCUMENTATION.md)** - REST API endpoints and usage
- **[Report Formats](REPORT_FORMATS.md)** - Understanding analysis reports
- **[LLM Integration](LLM_INTEGRATION.md)** - Setting up and using embedded LLMs

### Development

- **[Development Guide](DEVELOPMENT.md)** - Contributing to ARK-TOOLS
- **[Testing Guide](TESTING.md)** - Running and writing tests
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## Quick Start

1. **Install ARK-TOOLS**
   ```bash
   pip install ark-tools[full]
   ```

2. **Run Setup**
   ```bash
   ark-setup
   ```

3. **Analyze a Codebase**
   ```bash
   ark-analyze analyze hybrid /path/to/code --output reports
   ```

4. **View Reports**
   ```bash
   ark-analyze report view
   ```

## Key Features

### Hybrid Analysis
Combines MAMS structural analysis with LLM semantic understanding for comprehensive code insights.

### Context Compression
Reduces code to AST skeletons, achieving ~80% token reduction while preserving semantic meaning.

### Multi-Format Reporting
Generates reports in JSON, Markdown, and HTML formats with progressive disclosure.

### Embedded LLM Support
Works with local LLMs (CodeLlama, Mistral, Phi-2) for privacy-preserving analysis.

### Agent Architecture
Extensible agent-based system for modular analysis capabilities.

## Getting Help

- **Issues**: Report bugs on [GitHub Issues](https://github.com/ark-tools/ark-tools/issues)
- **Discussions**: Join our [community forum](https://github.com/ark-tools/ark-tools/discussions)
- **Support**: Contact support@ark-tools.io

## License

ARK-TOOLS is released under the MIT License. See [LICENSE](../LICENSE) for details.