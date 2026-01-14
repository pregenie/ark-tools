# ARK-TOOLS Installation Guide

## Table of Contents

1. [Requirements](#requirements)
2. [Quick Install](#quick-install)
3. [Installation Methods](#installation-methods)
4. [Platform-Specific Instructions](#platform-specific-instructions)
5. [Model Installation](#model-installation)
6. [Verification](#verification)
7. [Upgrading](#upgrading)
8. [Uninstallation](#uninstallation)
9. [Troubleshooting](#troubleshooting)

## Requirements

### System Requirements

#### Minimum
- **CPU**: 4 cores (x86_64 or ARM64)
- **RAM**: 8GB
- **Storage**: 10GB free space
- **Python**: 3.9 or higher
- **OS**: Linux, macOS 12+, Windows 10/11 (with WSL2)

#### Recommended
- **CPU**: 8+ cores
- **RAM**: 16GB or more
- **Storage**: 20GB SSD
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional)
- **Python**: 3.10 or 3.11

### Software Dependencies

```bash
# Check Python version
python --version  # Should be 3.9+

# Check pip
pip --version

# Check git (optional)
git --version
```

## Quick Install

### One-Line Installation

```bash
# Install with all features
pip install ark-tools[full] && ark-setup
```

### Basic Installation

```bash
# Install core package
pip install ark-tools

# Run setup wizard
ark-setup
```

## Installation Methods

### Method 1: pip (Recommended)

#### Basic Installation
```bash
pip install ark-tools
```

#### With Optional Features
```bash
# Full installation (all features)
pip install ark-tools[full]

# With PostgreSQL support
pip install ark-tools[postgresql]

# With Redis support
pip install ark-tools[redis]

# With AI features
pip install ark-tools[ai]

# With monitoring
pip install ark-tools[monitoring]

# Multiple features
pip install ark-tools[postgresql,redis,ai]
```

### Method 2: From Source

```bash
# Clone repository
git clone https://github.com/ark-tools/ark-tools.git
cd ark-tools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run setup
ark-setup
```

### Method 3: Docker

```bash
# Pull official image
docker pull arktools/ark-tools:latest

# Run container
docker run -it \
  -v $(pwd):/workspace \
  -v ~/.ark_tools:/root/.ark_tools \
  arktools/ark-tools:latest
```

### Method 4: Docker Compose

```bash
# Clone repository
git clone https://github.com/ark-tools/ark-tools.git
cd ark-tools

# Configure environment
cp .env.example .env
vim .env  # Edit configuration

# Start services
docker-compose up -d
```

## Platform-Specific Instructions

### Linux (Ubuntu/Debian)

```bash
# Install system dependencies
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-dev \
  build-essential \
  libssl-dev \
  libffi-dev \
  python3-venv

# Install ARK-TOOLS
pip install ark-tools[full]

# Run setup
ark-setup
```

### Linux (RHEL/CentOS/Fedora)

```bash
# Install system dependencies
sudo dnf install -y \
  python3-pip \
  python3-devel \
  gcc \
  openssl-devel \
  python3-virtualenv

# Install ARK-TOOLS
pip install ark-tools[full]

# Run setup
ark-setup
```

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install ARK-TOOLS
pip3 install ark-tools[full]

# Run setup
ark-setup
```

#### macOS ARM64 (Apple Silicon)

```bash
# Install Rosetta 2 (if needed)
softwareupdate --install-rosetta

# Install dependencies
brew install cmake

# Install with Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
pip install ark-tools[full]
```

### Windows

#### Option 1: WSL2 (Recommended)

```bash
# Install WSL2
wsl --install

# Inside WSL2 Ubuntu
sudo apt update
sudo apt install python3-pip

# Install ARK-TOOLS
pip install ark-tools[full]

# Run setup
ark-setup
```

#### Option 2: Native Windows

```powershell
# Install Python from python.org
# Open PowerShell as Administrator

# Install ARK-TOOLS
pip install ark-tools[full]

# Run setup
ark-setup
```

## Model Installation

### Automatic Model Download

```bash
# Run model setup wizard
ark-tools download-model

# Select model:
# 1. CodeLlama-7B-Instruct (Recommended for code)
# 2. Mistral-7B-Instruct
# 3. Phi-2 (Smallest, fastest)
# 4. DeepSeek-Coder-6.7B
```

### Manual Model Download

```bash
# Create models directory
mkdir -p ~/.ark_tools/models
cd ~/.ark_tools/models

# Download CodeLlama-7B-Instruct (Recommended)
wget https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf

# Or download Mistral-7B
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Or download Phi-2 (Smallest)
wget https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```

### GPU Acceleration Setup

#### NVIDIA CUDA

```bash
# Install CUDA toolkit
# Visit: https://developer.nvidia.com/cuda-downloads

# Install llama-cpp-python with CUDA
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Enable GPU in configuration
export ARK_LLM_ENABLE_GPU=true
export ARK_LLM_GPU_LAYERS=32
```

#### AMD ROCm

```bash
# Install ROCm
# Visit: https://rocm.docs.amd.com/en/latest/

# Install with ROCm support
CMAKE_ARGS="-DLLAMA_HIPBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Enable GPU
export ARK_LLM_ENABLE_GPU=true
```

#### Apple Metal (macOS)

```bash
# Install with Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Enable Metal acceleration
export ARK_LLM_ENABLE_GPU=true
```

## Verification

### Verify Installation

```bash
# Check ARK-TOOLS version
ark-analyze --version

# Run system check
ark-tools diagnose

# Output should show:
# ✅ Python: 3.11.5
# ✅ ARK-TOOLS: 0.1.0
# ✅ Configuration: Valid
# ✅ Model: Found
```

### Test Basic Functionality

```bash
# Create test directory
mkdir test_project
echo "def hello(): pass" > test_project/main.py

# Run analysis
ark-analyze analyze hybrid test_project --strategy fast

# Check for success message
# ✅ Analysis Complete!
```

### Verify Components

```bash
# Check CLI tools
which ark-analyze
which ark-setup
which ark-server

# Check Python imports
python -c "import ark_tools; print(ark_tools.__version__)"

# Check model
ark-analyze model
```

## Configuration

### Initial Configuration

```bash
# Run interactive setup
ark-setup

# Or use quick setup with defaults
ark-setup --mode quick

# Or minimal setup (no external services)
ark-setup --mode minimal
```

### Environment Variables

Create `.env` file:

```bash
# Core settings
ARK_TOOLS_ENV=production
ARK_DEBUG=false

# Model configuration
ARK_LLM_MODEL_PATH=~/.ark_tools/models/codellama-7b-instruct.Q4_K_M.gguf
ARK_LLM_CONTEXT_SIZE=8192
ARK_LLM_MAX_TOKENS=2048
ARK_LLM_THREADS=4
ARK_LLM_TEMPERATURE=0.1

# Optional services
DATABASE_URL=postgresql://user:pass@localhost:5432/ark_tools
REDIS_URL=redis://localhost:6379/0

# API settings
ARK_API_HOST=0.0.0.0
ARK_API_PORT=8100
```

### Validate Configuration

```bash
# Validate setup
ark-setup validate

# Test connections
ark-tools test-connections

# Expected output:
# ✅ Configuration: Valid
# ✅ Model: Loaded
# ✅ Database: Connected (optional)
# ✅ Redis: Connected (optional)
```

## Upgrading

### Upgrade to Latest Version

```bash
# Upgrade package
pip install --upgrade ark-tools

# Upgrade with all features
pip install --upgrade ark-tools[full]

# Run migration if needed
ark-tools migrate
```

### Upgrade from Source

```bash
cd ark-tools
git pull origin main
pip install --upgrade -e .[dev]
```

### Upgrade Docker

```bash
# Pull latest image
docker pull arktools/ark-tools:latest

# Recreate containers
docker-compose down
docker-compose up -d
```

### Check for Updates

```bash
# Check current version
ark-analyze --version

# Check for updates
pip list --outdated | grep ark-tools

# View changelog
ark-tools changelog
```

## Uninstallation

### Complete Uninstallation

```bash
# Uninstall package
pip uninstall ark-tools

# Remove configuration
rm -rf ~/.ark_tools
rm .env

# Remove reports
rm -rf .ark_reports

# Remove Docker containers/images
docker-compose down --rmi all --volumes
```

### Partial Uninstallation

```bash
# Keep configuration and models
pip uninstall ark-tools

# Or keep only models
rm -rf ~/.ark_tools/config
rm -rf ~/.ark_tools/cache
# Keep ~/.ark_tools/models
```

## Troubleshooting

### Common Installation Issues

#### Python Version Error

```bash
# Error: Python 3.9+ required

# Solution: Install Python 3.9+
# Ubuntu/Debian
sudo apt install python3.9

# macOS
brew install python@3.9

# Or use pyenv
pyenv install 3.9.16
pyenv local 3.9.16
```

#### pip Installation Fails

```bash
# Error: pip install fails

# Solution 1: Upgrade pip
python -m pip install --upgrade pip

# Solution 2: Use virtual environment
python -m venv venv
source venv/bin/activate
pip install ark-tools

# Solution 3: Install from wheels
pip install --only-binary :all: ark-tools
```

#### Model Download Fails

```bash
# Error: Model download timeout

# Solution 1: Manual download with resume
wget -c https://huggingface.co/[model-url]

# Solution 2: Use different mirror
export HF_ENDPOINT=https://hf-mirror.com

# Solution 3: Download via git-lfs
git lfs install
git clone https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF
```

#### GPU Support Issues

```bash
# Error: GPU not detected

# Solution 1: Check CUDA installation
nvidia-smi

# Solution 2: Reinstall with CUDA
pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --no-cache-dir

# Solution 3: Fallback to CPU
export ARK_LLM_ENABLE_GPU=false
```

#### Permission Denied

```bash
# Error: Permission denied

# Solution 1: Use user installation
pip install --user ark-tools

# Solution 2: Fix permissions
sudo chown -R $USER:$USER ~/.ark_tools

# Solution 3: Use virtual environment
python -m venv venv
source venv/bin/activate
pip install ark-tools
```

### Platform-Specific Issues

#### macOS: SSL Certificate Error

```bash
# Install certificates
pip install --upgrade certifi

# Or manually
/Applications/Python\ 3.9/Install\ Certificates.command
```

#### Windows: Long Path Error

```powershell
# Enable long paths (Run as Administrator)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
  -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

#### Linux: Missing Libraries

```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev

# RHEL/CentOS
sudo yum install gcc python3-devel

# Arch
sudo pacman -S base-devel python
```

### Getting Help

```bash
# Built-in help
ark-analyze --help
ark-setup --help

# System diagnostics
ark-tools diagnose --verbose

# Generate support bundle
ark-tools support-bundle --output support.zip

# Community support
# Visit: https://github.com/ark-tools/ark-tools/discussions
```