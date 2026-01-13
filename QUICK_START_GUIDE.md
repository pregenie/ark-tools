# ARK-TOOLS Quick Start Guide
## Get Running in 5 Minutes

🚀 **From Zero to Code Consolidation in Minutes**

---

## ⚡ 30-Second Overview

ARK-TOOLS is an AI-powered system that finds duplicate code in your projects and safely consolidates it. It **never modifies your original files** - everything is output to safe directories.

**What it does:**
- 🔍 Scans your code for patterns and duplicates
- 🧠 Uses AI to plan safe consolidations  
- ⚙️ Generates clean, unified code
- 🛡️ Protects your original files completely

---

## 🏃‍♂️ Quick Start (5 Minutes)

### Step 1: Setup ARK-TOOLS (30 seconds)
```bash
# Just run this simple command:
./ark-setup web

# You'll see:
# ✅ Found available port: 8082
# 🌐 Starting ARK-TOOLS Web UI at http://localhost:8082
#    Press Ctrl+C to stop the server

# Then open the URL it shows you in your browser!
```
**What this does:** Automatically finds an available port, starts the web UI, and tells you exactly where to go. The visual interface guides you through the entire setup.

### Step 2: Test Your Setup (30 seconds)
```bash
/ark-test
```
**What this does:** Verifies everything is working correctly.

### Step 3: Analyze Your Code (2 minutes)
```bash
/ark-analyze directory=/path/to/your/code type=comprehensive
```
**What this does:** Scans your codebase and finds patterns, duplicates, and consolidation opportunities.

### Step 4: Create Transformation Plan (1 minute)
```bash
/ark-transform --analysis-id <your-analysis-id> --strategy conservative
```
**What this does:** Creates a safe plan for consolidating your code.

### Step 5: Generate Consolidated Code (1 minute)
```bash
/ark-generate --plan-id <your-plan-id>
```
**What this does:** Generates the consolidated code in a safe output directory.

**🎉 Done!** Your consolidated code is in `.ark_output/v_TIMESTAMP/`

---

## 📋 Pre-Requirements Checklist

Before starting, ensure you have:

- [ ] **Python 3.9+** available (3.11+ recommended)
- [ ] **Docker & Docker Compose** (optional - ARK-TOOLS can use existing services)
- [ ] **Git** for version control
- [ ] **4GB+ RAM** available
- [ ] **Read access** to your source code

**Check your setup:**
```bash
python3 --version         # Should show Python 3.9+
docker --version          # Optional: Docker 24+ if using containers
docker-compose --version  # Optional: v2.20+ if using containers
```

**Quick Setup will automatically detect:**
- Running PostgreSQL/Redis in Docker containers
- Native PostgreSQL/Redis installations
- Existing `.env` files with credentials
- MAMS integration if available

---

## 🎯 Your First Analysis (Step-by-Step)

### Example: Analyze a Python Project

```bash
# 1. Point ARK-TOOLS at your Python project
/ark-analyze directory=/home/user/my-python-app type=comprehensive

# Expected output:
# 🔍 Starting Analysis
# 📂 Discovery Phase: Found 87 Python files
# 🔧 Extraction Phase: Extracted 234 components  
# 🎯 Pattern Detection: Found 23 API endpoints, 18 services
# 🔍 Duplicate Detection: Found 12 near-duplicates (>85% similarity)
# ✅ Analysis complete! ID: abc123def456
```

### Example: Review What Was Found

```bash
# The analysis creates a report file
cat analysis_results_abc123def456.json

# Key sections to look for:
# - "summary": Overview of files and components found
# - "patterns": Types of code patterns detected
# - "duplicates": Similar code that could be merged
# - "consolidation_opportunities": Specific recommendations
```

### Example: Create Transformation Plan

```bash
# Create a conservative transformation plan
/ark-transform --analysis-id abc123def456 --strategy conservative

# Expected output:
# 🔧 Creating Transformation Plan
# 🎯 Grouping Components (conservative strategy)
# ✅ Created 3 transformation groups:
#   1. user_management (4 files → 1 unified service) 
#   2. auth_utilities (3 files → 1 utility module)
#   3. duplicate_elimination (5 duplicate functions → 1 shared)
# 📋 Plan ID: xyz789abc123
```

---

## 🔍 Understanding the Output

### Analysis Results
```json
{
  "summary": {
    "total_files": 87,
    "total_components": 234,
    "patterns_found": 4,
    "duplicates_found": 12
  },
  "recommendations": [
    {
      "priority": "high", 
      "type": "duplication",
      "message": "High duplication in user services - consider consolidation"
    }
  ]
}
```

### Transformation Plan
```json
{
  "groups": [
    {
      "name": "user_management",
      "type": "consolidation", 
      "source_files": ["user_service.py", "customer_service.py"],
      "operations": [
        {
          "type": "merge",
          "target": "unified_user_service.py"
        }
      ],
      "estimated_reduction": "67%"
    }
  ]
}
```

### Generated Output Structure
```
.ark_output/v_20260112_143022/
├── user_management/
│   └── unified_user_service.py    # Consolidated user functions
├── auth_utilities/  
│   └── auth_helpers.py           # Consolidated auth utilities
├── tests/
│   ├── test_user_management.py   # Generated tests
│   └── test_auth_utilities.py
└── GENERATION_REPORT.md          # Summary of what was done
```

---

## 🎚️ Strategy Levels

Choose the right strategy for your comfort level:

### **Conservative** (Recommended for first time)
- Only merges code that's >90% similar
- Preserves all existing functionality  
- Lower code reduction, higher safety
```bash
/ark-transform --analysis-id <id> --strategy conservative
```

### **Moderate** (Good for experienced users)
- Merges code that's >80% similar
- Some restructuring for better organization
- Balanced reduction vs. risk
```bash
/ark-transform --analysis-id <id> --strategy moderate
```

### **Aggressive** (For major refactoring)
- Merges code that's >70% similar  
- Significant restructuring
- Maximum consolidation, higher risk
```bash
/ark-transform --analysis-id <id> --strategy aggressive
```

---

## 🛡️ Safety Guarantees

### Your Original Code is 100% Safe
- ✅ **Never modifies** your source files
- ✅ **Only reads** from your original code
- ✅ **Outputs everything** to `.ark_output/` directories
- ✅ **Creates backups** before any operations
- ✅ **Validates syntax** of all generated code

### Quality Guarantees  
- ✅ **Type checking** - All generated code has proper type hints
- ✅ **Syntax validation** - Generated code compiles correctly
- ✅ **Test generation** - Automatic test creation for consolidated code
- ✅ **Import resolution** - All imports work correctly
- ✅ **Rollback capability** - Can undo any transformation

### What If Something Goes Wrong?
```bash
# All operations are logged and reversible
# Check the generation report
cat .ark_output/v_TIMESTAMP/GENERATION_REPORT.md

# If needed, simply delete the output directory
rm -rf .ark_output/v_TIMESTAMP/

# Your original code is unchanged!
```

---

## 💡 Pro Tips

### 1. Start Small
```bash
# Analyze just one directory first
/ark-analyze directory=/path/to/small-module type=quick

# Then expand to full project
/ark-analyze directory=/path/to/full-project type=comprehensive
```

### 2. Use Dry Runs
```bash
# Preview what would be generated without creating files
/ark-generate --plan-id <id> --dry-run=true

# Review the preview, then generate for real
/ark-generate --plan-id <id> --dry-run=false
```

### 3. Check Generated Tests
```bash
# Generated code includes tests - run them!
cd .ark_output/v_TIMESTAMP/
python -m pytest tests/ -v

# Make sure everything works before using the code
```

### 4. Review Before Using
```bash
# Always review generated code before integration
# Use a diff tool to compare original vs consolidated
diff -u original/user_service.py .ark_output/v_TIMESTAMP/unified_user_service.py
```

---

## 🔧 Common Commands Quick Reference

### Setup Commands
```bash
/scaffold-project                    # Initialize ARK-TOOLS
/scaffold-module module=discovery    # Add new module
/ark-test                           # Verify setup
```

### Analysis Commands
```bash
/ark-analyze directory=./src         # Analyze src directory
/ark-analyze directory=./app type=quick    # Quick analysis
```

### Transformation Commands  
```bash
/ark-transform --analysis-id <id>    # Create plan (conservative)
/ark-transform --analysis-id <id> --strategy moderate   # Moderate plan
```

### Generation Commands
```bash
/ark-generate --plan-id <id> --dry-run    # Preview only
/ark-generate --plan-id <id>              # Generate code
```

---

## 📞 Getting Help

### Built-in Help
```bash
/ark-analyze --help        # Command-specific help
/ark-test --verbose=true   # Detailed test output
```

### Check Logs
```bash
# View detailed logs
tail -f logs/ark-tools.log

# Check hook execution
tail -f logs/mcp-hooks.log
```

### Documentation
- **[Complete User Guide](docs/ARK_TOOLS_USER_GUIDE.md)** - Comprehensive documentation
- **[API Reference](docs/ARK_TOOLS_API_SPECIFICATION.md)** - API details
- **[Troubleshooting](README_ARK_TOOLS_AGENTIC.md#-troubleshooting)** - Common issues

### Support
- **GitHub Issues** - Report bugs and feature requests
- **Community Forum** - Ask questions and share experiences
- **Enterprise Support** - Production deployment assistance

---

## 🎉 Success Stories

### "Reduced 500 lines to 150 lines in 10 minutes"
```bash
# Before: 5 similar user service files, lots of duplication
# After: 1 unified service with all functionality preserved
# Result: 70% code reduction, easier maintenance
```

### "Found 12 copy-paste bugs automatically"
```bash
# ARK-TOOLS detected near-duplicate functions with subtle bugs
# Consolidation used the correct implementation
# Result: Bug fixes + code cleanup in one step
```

### "Safely refactored legacy codebase"
```bash
# 10-year-old codebase with scattered utility functions  
# ARK-TOOLS identified and organized into logical modules
# Result: Modern architecture with zero functionality lost
```

---

## 🚀 Next Steps

### Ready to Start?
```bash
# 1. Initialize (30 seconds)
/scaffold-project

# 2. Analyze your code (2 minutes)  
/ark-analyze directory=/your/code/path

# 3. Transform safely (3 minutes)
/ark-transform --analysis-id <id>
/ark-generate --plan-id <id>
```

### Want to Learn More?
- **[Complete Documentation](docs/)** - Deep dive into all features
- **[Advanced Workflows](docs/ARK_TOOLS_AGENTIC_WORKFLOW.md)** - Power user techniques  
- **[Production Deployment](docs/ARK_TOOLS_IMPLEMENTATION_GUIDE.md)** - Enterprise setup

### Ready for Production?
- **[Deployment Guide](/ark-deploy)** - Production-ready deployment
- **[Monitoring Setup](README_ARK_TOOLS_AGENTIC.md#-monitoring--observability)** - Observability configuration
- **[Team Workflows](docs/ARK_TOOLS_USER_GUIDE.md#team-collaboration)** - Multi-developer usage

---

**🎯 Remember: ARK-TOOLS makes code consolidation safe, automatic, and reversible. Your original code is never touched!**

*Happy consolidating! 🚀*