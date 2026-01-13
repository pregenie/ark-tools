# ARK-TOOLS Setup UI Launch Guide

## 🚀 How to Initialize and Use the Setup UIs

ARK-TOOLS includes **three different UI options** for setup configuration. Here's how to use each one:

---

## 1. 🌐 Web UI (Browser-based)

The Web UI provides a visual, browser-based interface for configuring ARK-TOOLS.

### Launch the Web UI:
```bash
# From the ark-tools directory:
./ark-setup web

# Or if ark-setup is in your PATH:
ark-setup web
```

### What happens:
1. Starts a FastAPI server on port 8080
2. Serves an embedded Vue.js application
3. Provides real-time WebSocket updates

### Access the UI:
Open your browser and navigate to:
```
http://localhost:8080
```

### Features:
- Visual service detection display
- Drag-and-drop configuration
- Real-time connection testing
- Progress indicators for each step
- Export configuration when complete

### Screenshot Preview:
```
┌──────────────────────────────────────────────┐
│  🚀 ARK-TOOLS Setup Assistant                │
├──────────────────────────────────────────────┤
│  [Quick Setup] [Custom] [Minimal]            │
│                                               │
│  Detected Services:                          │
│  ✅ PostgreSQL (Docker) - localhost:5432     │
│  ✅ Redis (Native) - localhost:6379          │
│                                               │
│  Detected Environments:                      │
│  📁 /Users/you/project/.env                  │
│     └── Has: Database, Redis, AI Keys        │
│                                               │
│  [Test Connections] [Generate Config]        │
└──────────────────────────────────────────────┘
```

---

## 2. 📺 Terminal UI (TUI)

The Terminal UI provides a rich, interactive terminal interface using Textual.

### Launch the Terminal UI:
```bash
# From the ark-tools directory:
./ark-setup tui

# Or if ark-setup is in your PATH:
ark-setup tui
```

### What happens:
1. Launches a Textual application in your terminal
2. Provides keyboard navigation
3. Shows real-time updates

### Navigation:
- **Arrow Keys**: Navigate between options
- **Tab**: Move to next field
- **Enter**: Select/confirm
- **Escape**: Go back/cancel
- **Space**: Toggle checkboxes

### Features:
- Step-by-step wizard interface
- Service configuration modals
- Real-time validation
- Progress indicators
- Keyboard shortcuts

### Terminal Preview:
```
╔══════════════════════════════════════════════╗
║     ARK-TOOLS Setup - Terminal Interface    ║
╠══════════════════════════════════════════════╣
║                                              ║
║  Setup Mode:                                 ║
║  ○ Quick (Automatic with defaults)          ║
║  ● Custom (Full control)                    ║
║  ○ Minimal (No external dependencies)       ║
║                                              ║
║  [Next →]  [Cancel]                          ║
║                                              ║
╚══════════════════════════════════════════════╝
 Keyboard: ↑↓ Navigate | Enter Select | Esc Back
```

---

## 3. 💻 CLI (Command Line Interface)

The CLI provides an interactive command-line setup with rich formatting.

### Launch the CLI:
```bash
# Interactive mode (default):
./ark-setup

# Quick setup mode:
./ark-setup --mode quick

# Custom setup mode:
./ark-setup --mode custom

# Minimal setup mode:
./ark-setup --mode minimal
```

### What happens:
1. Uses Rich library for beautiful terminal output
2. Provides interactive prompts
3. Shows tables and progress bars

### Features:
- Colored output and tables
- Interactive prompts with defaults
- Progress spinners
- Confirmation prompts
- Syntax-highlighted config preview

### CLI Preview:
```bash
╔═══════════════════════════════════════════════════════╗
║       🚀 ARK-TOOLS Setup Assistant 🚀                ║
║                                                       ║
║  Intelligent Configuration for Code Consolidation    ║
╚═══════════════════════════════════════════════════════╝

Setup Mode [quick/custom/minimal] (quick): custom

[bold]Custom Setup[/bold]

⠋ Scanning for environment files...
✅ Found 3 environment files

┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Project     ┃ Path             ┃ Services    ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ arkyvus     │ ../arkyvus/.env  │ 🗄️ DB 📦 Redis │
│ project-2   │ ../proj2/.env    │ 🗄️ DB 🤖 AI   │
│ local       │ ./.env           │ 📦 Redis     │
└─────────────┴──────────────────┴─────────────┘

Select environment to inherit from (1-3, 4 for none): 1
```

---

## 4. 🔧 Non-Interactive Mode

For CI/CD or automated setups:

```bash
# Quick setup with specific parent env:
./ark-setup --mode quick --parent-env /path/to/.env --output-dir ./config

# Validate existing configuration:
./ark-setup validate
```

---

## 🎯 Which UI Should You Use?

### Use **Web UI** if you:
- Prefer visual interfaces
- Want to see everything at once
- Like drag-and-drop configuration
- Need to share setup with team members

### Use **Terminal UI** if you:
- Work primarily in the terminal
- Want keyboard-only navigation
- Prefer step-by-step wizards
- Like modal dialogs

### Use **CLI** if you:
- Want quick interactive setup
- Prefer command-line prompts
- Like seeing configuration as tables
- Need scriptable but interactive setup

### Use **Non-Interactive** if you:
- Setting up in CI/CD pipelines
- Automating deployments
- Have all configuration ready
- Need reproducible setups

---

## 🚦 Quick Test

After setup with any UI, validate your configuration:

```bash
./ark-setup validate

# Expected output:
✅ PostgreSQL: Connected to PostgreSQL 14.5
✅ Redis: Connected to Redis 7.0.5
✅ MAMS: Found at /path/to/mams
✅ Configuration valid and ready!
```

---

## 💡 Tips

1. **First Time Users**: Start with Web UI for the most visual experience
2. **Terminal Users**: Use TUI for full-featured terminal experience
3. **Quick Setup**: Use CLI with `--mode quick` for fastest setup
4. **Automation**: Use non-interactive mode with pre-configured values

---

## 🆘 Troubleshooting

### Web UI won't start:
```bash
# Check if port 8080 is in use:
lsof -i :8080

# Use different port:
ARK_SETUP_PORT=8081 ./ark-setup web
```

### Terminal UI not available:
```bash
# Install Textual:
pip install textual

# Then retry:
./ark-setup tui
```

### CLI colors not showing:
```bash
# Force color output:
FORCE_COLOR=1 ./ark-setup
```

---

## 📚 Next Steps

After successful setup:

1. Review generated `.env` file
2. Start services if using Docker: `docker-compose up -d`
3. Run health check: `curl http://localhost:5000/health/detailed`
4. Begin using ARK-TOOLS: `/ark-analyze directory=/your/code`