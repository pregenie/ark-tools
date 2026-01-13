# Getting Started with ARK-TOOLS

## The Simplest Way to Start (1 Minute!)

### Step 1: Navigate to ARK-TOOLS
```bash
cd ark-tools
```

### Step 2: Run the Setup Command
```bash
./ark-setup web
```

### Step 3: Open Your Browser
The command will show you something like:
```
✅ Found available port: 8082
🌐 Starting ARK-TOOLS Web UI at http://localhost:8082
   Press Ctrl+C to stop the server
```

**Just open that URL in your browser!** (In this example: http://localhost:8082)

## That's It! 🎉

The Web UI will:
- ✅ Automatically detect your existing PostgreSQL/Redis services
- ✅ Find any `.env` files from parent projects 
- ✅ Offer to inherit credentials (no retyping!)
- ✅ Test all connections before saving
- ✅ Generate your configuration

## What Makes This So Easy?

1. **No Port Conflicts** - Automatically finds an available port
2. **No Dependencies to Install** - Script auto-installs what's needed
3. **No Manual Configuration** - Visual interface guides you
4. **No Guessing** - Tells you exactly where to go

## Alternative Methods

If you prefer command-line:
```bash
# Quick automatic setup
./ark-setup --mode quick

# Interactive CLI
./ark-setup

# Terminal UI
./ark-setup tui
```

But seriously, just use `./ark-setup web` - it's the easiest way!

## Troubleshooting

### Can't access the URL?
- Make sure you're using the exact URL shown (port may vary)
- Check your firewall isn't blocking local connections
- Try `curl http://localhost:PORT` to test connectivity

### Port detection failing?
```bash
# Manually specify a port
./ark-setup web --port 9000
```

### Dependencies not installing?
```bash
# Install manually
pip install click rich python-dotenv pydantic fastapi uvicorn
```

## Next Steps

After setup completes:
1. Your configuration is saved to `.env`
2. Services are configured and tested
3. You're ready to use ARK-TOOLS!

Start analyzing code:
```bash
/ark-analyze directory=/path/to/your/code
```