#!/bin/bash
# ARK-TOOLS Installation Script
# =============================

set -e

echo "🚀 ARK-TOOLS Setup Installer"
echo "============================"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ is required. Found: Python $python_version"
    exit 1
fi
echo "✅ Python $python_version found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install --quiet click rich python-dotenv pydantic fastapi uvicorn aiofiles

# Optional dependencies (don't fail if not available)
echo "📦 Installing optional dependencies..."
pip3 install --quiet textual 2>/dev/null || echo "⚠️  Terminal UI (textual) not available"
pip3 install --quiet asyncpg 2>/dev/null || echo "⚠️  PostgreSQL async support not available"
pip3 install --quiet redis 2>/dev/null || echo "⚠️  Redis support not available"
echo ""

# Make setup script executable
chmod +x ark-setup

# Add to PATH if not already there
if ! command -v ark-setup &> /dev/null; then
    echo "📝 Adding ark-setup to PATH..."
    current_dir=$(pwd)
    echo "export PATH=\"$current_dir:\$PATH\"" >> ~/.bashrc 2>/dev/null || true
    echo "export PATH=\"$current_dir:\$PATH\"" >> ~/.zshrc 2>/dev/null || true
    export PATH="$current_dir:$PATH"
    echo "✅ Added to PATH (restart shell to make permanent)"
else
    echo "✅ ark-setup already in PATH"
fi
echo ""

echo "✨ Installation complete!"
echo ""
echo "🎯 Quick Start Options:"
echo "======================="
echo ""
echo "1. 🚀 Automatic Setup (Recommended):"
echo "   ./ark-setup --mode quick"
echo ""
echo "2. 🖥️  Web UI Setup (Visual):"
echo "   ./ark-setup web"
echo "   Then open: http://localhost:8080"
echo ""
echo "3. 📺 Terminal UI Setup (Interactive):"
echo "   ./ark-setup tui"
echo ""
echo "4. 💻 CLI Setup (Step-by-step):"
echo "   ./ark-setup"
echo ""
echo "5. ✅ Validate Existing Config:"
echo "   ./ark-setup validate"
echo ""
echo "Choose the option that best fits your needs!"