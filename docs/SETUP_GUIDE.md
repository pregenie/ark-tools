# ARK-TOOLS Setup Guide

## Overview

ARK-TOOLS features an intelligent setup system that can:
- Automatically detect existing services (PostgreSQL, Redis) in your environment
- Inherit credentials from existing `.env` files
- Interrogate Docker containers to find compatible services
- Create new services if needed
- Validate connections before committing configuration

## Installation

```bash
# Install ARK-TOOLS
pip install ark-tools

# Or from source
git clone https://github.com/your-org/ark-tools.git
cd ark-tools
pip install -e .
```

## Setup Modes

### 1. Web UI Setup (Easiest - Recommended!)

The simplest way to get started:

```bash
./ark-setup web
```

This command:
- ✅ Automatically finds an available port
- ✅ Shows you the exact URL to open (e.g., http://localhost:8082)
- ✅ Provides a visual, guided setup experience
- ✅ No need to remember command-line options!

### 2. Quick Setup (Command-line)

For automatic setup without a UI:

```bash
./ark-setup --mode quick
```

This will:
- Scan for existing `.env` files in parent directories
- Detect running Docker containers
- Find system services (PostgreSQL, Redis)
- Automatically configure using the best available options
- Generate secure secrets
- Test all connections

### 2. Interactive Setup

For full control over configuration:

```bash
ark-setup
```

Choose from three interactive modes:
- **Quick**: Automated with confirmation prompts
- **Custom**: Step-by-step configuration
- **Minimal**: No external dependencies (SQLite fallback)

### 3. Interactive CLI Setup

For step-by-step command-line setup:

```bash
./ark-setup
```

Choose from quick, custom, or minimal modes interactively.

### 4. Terminal UI Setup

For a rich terminal interface:

```bash
ark-setup tui
```

Navigate through configuration steps with keyboard controls.

## Command-Line Options

### Non-Interactive Quick Setup

```bash
# Use specific parent environment file
ark-setup --mode quick --parent-env /path/to/parent/.env --output-dir ./config

# Minimal setup (no external dependencies)
ark-setup --mode minimal --output-dir ./config
```

### Validate Existing Configuration

```bash
# Test connections in existing .env
ark-setup validate
```

## Service Detection

### Docker Container Detection

ARK-TOOLS automatically detects services running in Docker:

```yaml
# Detected containers
- PostgreSQL (postgres:14)
- Redis (redis:7-alpine)
- MongoDB (mongo:latest)
```

The system will:
1. List all running containers
2. Identify compatible services
3. Extract connection details
4. Test connectivity

### Environment File Inheritance

If you have existing projects with `.env` files:

```bash
# Parent project .env
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-xxx
```

ARK-TOOLS can inherit these credentials to avoid re-entry.

### System Service Detection

Native services are also detected:

```bash
# PostgreSQL running on port 5432
# Redis running on port 6379
# Detected via port scanning and process inspection
```

## Configuration Options

### Service Modes

When configuring services, choose from:

1. **Use Existing**: Connect to existing database/service
2. **Share Existing**: Use existing service with separate database/keyspace
3. **Create New**: Generate Docker Compose configuration for new service
4. **Skip**: Don't configure this service

### PostgreSQL Configuration

```python
# Mode: Use Existing
- Uses existing database
- Requires credentials

# Mode: Create New
- Generates docker-compose.yml
- Creates new PostgreSQL container
- Sets up ark_tools database
```

### Redis Configuration

```python
# Mode: Share Existing
- Uses existing Redis instance
- Separate database number (0-15)

# Mode: Create New
- New Redis container
- Dedicated instance for ARK-TOOLS
```

## Generated Files

After setup, you'll have:

```
./
├── .env                    # Environment configuration
├── docker-compose.yml      # Service definitions (if needed)
├── .env.example           # Template for others
└── setup.log              # Setup process log
```

### Sample .env File

```bash
# ARK-TOOLS Configuration
# Generated: 2024-01-11

# Deployment
ARK_DEPLOYMENT_MODE=development

# Database
DATABASE_URL=postgresql://arkuser:pass@localhost:5432/ark_tools
ARK_USE_SQLITE_FALLBACK=false

# Redis
REDIS_URL=redis://localhost:6379/2

# Security
ARK_SECRET_KEY=<generated-secret>
ARK_CSRF_SECRET_KEY=<generated-secret>

# AI Providers (inherited)
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Features
ARK_ENABLE_WEBSOCKETS=true
ARK_ENABLE_MONITORING=true
ARK_ENABLE_SECURITY_SCAN=false

# MAMS Integration
ARK_MAMS_BASE_PATH=/path/to/mams
```

## Testing Connections

After configuration, test your setup:

```bash
# Validate all connections
ark-setup validate

# Output:
✅ PostgreSQL: Connected to PostgreSQL 14.5
✅ Redis: Connected to Redis 7.0.5
✅ MAMS: Found at /path/to/mams
```

## Docker Compose Integration

If you choose to create new services:

```yaml
# Generated docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: ark_tools
      POSTGRES_USER: arkuser
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - ark_postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ark_redis_data:/data

volumes:
  ark_postgres_data:
  ark_redis_data:
```

Start services with:

```bash
docker-compose up -d
```

## Troubleshooting

### Connection Issues

```bash
# Check if services are running
docker ps

# Test PostgreSQL connection
psql -h localhost -U arkuser -d ark_tools -c '\l'

# Test Redis connection
redis-cli -h localhost ping
```

### Permission Errors

```bash
# Ensure Docker daemon is accessible
sudo usermod -aG docker $USER

# Logout and login again
```

### Port Conflicts

If default ports are in use:

1. Run custom setup
2. Specify alternative ports
3. Update generated configuration

### Missing Dependencies

```bash
# Install optional dependencies for full functionality
pip install ark-tools[full]

# Or specific features
pip install asyncpg aioredis
```

## Environment Variables

### Core Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ARK_DEPLOYMENT_MODE` | development/production | development |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `ARK_SECRET_KEY` | Application secret key | (generated) |

### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `ARK_ENABLE_WEBSOCKETS` | Enable WebSocket support | true |
| `ARK_ENABLE_MONITORING` | Enable Prometheus/Grafana | false |
| `ARK_ENABLE_SECURITY_SCAN` | Enable security scanning | false |
| `ARK_USE_SQLITE_FALLBACK` | Use SQLite if PostgreSQL unavailable | false |

### AI Providers

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | No |
| `ANTHROPIC_API_KEY` | Anthropic API key | No |

## Next Steps

After successful setup:

1. **Verify Configuration**
   ```bash
   cat .env  # Review generated configuration
   ```

2. **Start Services** (if using Docker)
   ```bash
   docker-compose up -d
   ```

3. **Run Health Check**
   ```bash
   curl http://localhost:5000/health/detailed
   ```

4. **Perform First Analysis**
   ```bash
   ark-analyze directory=/path/to/code
   ```

## Advanced Configuration

### Using Existing Databases

To use an existing PostgreSQL database:

1. Choose "Custom Setup"
2. Select "Use Existing" for PostgreSQL
3. Provide connection details
4. ARK-TOOLS will test the connection

### Multiple Environments

Create environment-specific configurations:

```bash
# Development
ark-setup --output-dir ./config/dev

# Staging
ark-setup --output-dir ./config/staging

# Production
ark-setup --output-dir ./config/prod
```

### CI/CD Integration

For automated deployments:

```bash
# Non-interactive setup with environment file
ark-setup --mode quick \
  --parent-env /secrets/.env \
  --output-dir /app/config \
  --no-interactive
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/ark-tools/issues
- Documentation: https://ark-tools.readthedocs.io
- Discord: https://discord.gg/ark-tools