# ARK-TOOLS Container Setup Guide

## Overview
ARK-TOOLS now supports running in its own optimized Docker container, providing better isolation, resource management, and deployment consistency. This guide explains how to set up and manage ARK-TOOLS containers.

## Key Features

### 🚀 Automatic Container Detection
- Detects existing ARK-TOOLS containers
- Identifies compatible containers (ark-tool, ark_tool, arktools)
- Shows container status and version

### 💻 System Resource Checking
- Validates CPU cores (min 2, recommended 4)
- Checks available RAM (min 2GB, recommended 4GB)
- Verifies disk space (min 5GB, recommended 10GB)
- Confirms Docker availability
- Provides alternatives for constrained systems

### 🎯 Smart Configuration
- **Use Existing**: Leverage detected ARK-TOOLS containers
- **Create New**: Build optimized container from scratch
- **Run on Host**: Fallback for systems without Docker

## Setup Methods

### 1. Web UI (Recommended)
```bash
./ark-setup web
```
The web interface provides:
- Visual system resource assessment
- Step-by-step container configuration
- Real-time validation
- Clear guidance for each decision

Access at: http://localhost:8082 (auto-detects available port)

### 2. Command Line Interface
```bash
./ark-setup
```
Interactive CLI that:
- Checks system resources first
- Detects existing containers
- Guides through configuration options
- Generates Docker Compose files

### 3. Quick Setup (Non-interactive)
```bash
./ark-setup --mode quick --parent-env /path/to/.env
```
Automatically configures based on detected environment.

## Container Management

### Starting Containers
```bash
# Start all containers
./ark-setup start

# Build and start
./ark-setup start --build

# Start in foreground (see logs)
./ark-setup start --no-detach
```

### Stopping Containers
```bash
./ark-setup stop
```

### Viewing Logs
```bash
./ark-setup logs
```

### Validating Configuration
```bash
./ark-setup validate
```

## Generated Files

### docker-compose.yml
When you choose to use containers, ARK-TOOLS generates:
- ARK-TOOLS container configuration
- PostgreSQL container (if needed)
- Redis container (if needed)
- Proper networking and volumes
- Resource limits and health checks

### Dockerfile.ark-tools
Custom Dockerfile with:
- Python 3.11 slim base
- All required dependencies
- Non-root user for security
- Health check endpoint
- Optimized layer caching

### .env
Environment configuration with:
- Database credentials
- Redis connection
- Secret keys
- Port mappings
- Feature flags

## Container Architecture

### ARK-TOOLS Container
- **Image**: ark-tools:latest
- **Port**: 8100 (configurable)
- **Memory**: 512MB-2GB
- **CPU**: 0.5-2.0 cores
- **Volumes**: 
  - ./config:/app/config
  - ./data:/app/data
  - ./logs:/app/logs
  - Docker socket (for container operations)

### Resource Allocation
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: '2G'
    reservations:
      cpus: '0.5'
      memory: '512M'
```

## System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 2GB available
- **Disk**: 5GB free
- **Docker**: Installed (or run on host)

### Recommended
- **CPU**: 4+ cores
- **RAM**: 4GB+ available
- **Disk**: 10GB+ free
- **Docker**: Latest version

## Workflow Example

1. **Check System Resources**
   ```bash
   ./ark-setup web
   ```
   - View CPU, RAM, Disk availability
   - Confirm Docker is installed

2. **Configure ARK-TOOLS Container**
   - If found: Choose "Use Existing" or "Create New"
   - If not found: Create new container

3. **Configure Services**
   - PostgreSQL: Use existing, share, or create new
   - Redis: Use existing, share, or create new

4. **Save Configuration**
   - Generates .env, docker-compose.yml, Dockerfile

5. **Start Containers**
   ```bash
   ./ark-setup start --build
   ```

6. **Access ARK-TOOLS**
   - Default: http://localhost:8100
   - Check .env for custom port

## Troubleshooting

### Docker Not Available
- **Option 1**: Install Docker Desktop/Engine
- **Option 2**: Run ARK-TOOLS on host (less isolated)
- **Option 3**: Use cloud deployment

### Insufficient Resources
- **Low RAM**: Use SQLite instead of PostgreSQL
- **Low CPU**: Disable monitoring features
- **Low Disk**: Clean up Docker images/containers

### Container Won't Start
1. Check logs: `./ark-setup logs`
2. Verify ports: `docker ps`
3. Check resources: `docker stats`
4. Rebuild: `./ark-setup start --build`

## Advanced Configuration

### Custom Resource Limits
Edit docker-compose.yml:
```yaml
ark-tools:
  deploy:
    resources:
      limits:
        cpus: '4.0'  # Increase CPU
        memory: '4G'  # Increase RAM
```

### Multiple Environments
```bash
# Development
ARK_ENV=dev ./ark-setup start

# Production
ARK_ENV=prod ./ark-setup start
```

### Volume Persistence
Data persists in Docker volumes:
- postgres-data
- redis-data
- ./data (host mount)

## Security Considerations

### Container Isolation
- Runs as non-root user (arkuser)
- Limited resource access
- Network isolation via Docker networks

### Secrets Management
- Generated automatically
- Stored in .env (gitignored)
- Passed as environment variables

### Docker Socket Access
- Read-only mount for container operations
- Required for detecting other containers
- Can be removed if not needed

## Migration Guide

### From Host to Container
1. Backup existing data
2. Run setup: `./ark-setup`
3. Choose "Create New Container"
4. Start containers: `./ark-setup start`
5. Restore data if needed

### From Container to Host
1. Stop containers: `./ark-setup stop`
2. Export data from volumes
3. Run setup: `./ark-setup`
4. Choose "Run on Host"
5. Import data to host locations

## Best Practices

1. **Always Check Resources First**
   - Prevents deployment failures
   - Identifies constraints early

2. **Use Containers When Possible**
   - Better isolation
   - Easier deployment
   - Consistent environment

3. **Configure Services Appropriately**
   - Share existing for development
   - Create new for production
   - Skip Redis if not needed

4. **Monitor Container Health**
   - Check logs regularly
   - Monitor resource usage
   - Set up alerts for failures

5. **Keep Configuration Versioned**
   - Commit docker-compose.yml
   - Document .env structure
   - Track Dockerfile changes

## Support

For issues or questions:
- Check logs: `./ark-setup logs`
- Validate setup: `./ark-setup validate`
- Review this guide
- Open an issue on GitHub