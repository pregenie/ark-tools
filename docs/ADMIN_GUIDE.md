# ARK-TOOLS Administration Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration Management](#configuration-management)
4. [Service Management](#service-management)
5. [Model Management](#model-management)
6. [Database Administration](#database-administration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [Security Administration](#security-administration)
10. [Performance Tuning](#performance-tuning)
11. [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements

#### Minimum
- **CPU**: 4 cores (x86_64 or ARM64)
- **RAM**: 8GB
- **Storage**: 10GB free space
- **Network**: 100 Mbps

#### Recommended
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Storage**: 20GB+ SSD
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional)
- **Network**: 1 Gbps

### Software Requirements

#### Operating Systems
- Ubuntu 20.04/22.04 LTS
- macOS 12+ (Monterey or later)
- Windows 10/11 with WSL2
- RHEL/CentOS 8+

#### Dependencies
- Python 3.9+
- Docker 20.10+ (optional)
- PostgreSQL 14+ (optional)
- Redis 6+ (optional)

## Installation

### Quick Installation

```bash
# Install with all features
pip install ark-tools[full]

# Run interactive setup
ark-setup

# Start services
ark-server
```

### Docker Installation

```bash
# Clone repository
git clone https://github.com/ark-tools/ark-tools.git
cd ark-tools

# Run setup
ark-setup --mode docker

# Start containers
docker-compose up -d
```

### Manual Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install ARK-TOOLS
pip install -e .

# Download LLM model
mkdir -p ~/.ark_tools/models
cd ~/.ark_tools/models
wget https://huggingface.co/codellama-7b-instruct.gguf

# Configure environment
cp .env.example .env
vim .env  # Edit configuration

# Initialize database
python -m ark_tools.setup.db_init
```

## Configuration Management

### Configuration Files

#### Primary Configuration (`.env`)
```bash
# Core Settings
ARK_TOOLS_ENV=production
ARK_TOOLS_PORT=8100
ARK_TOOLS_HOST=0.0.0.0

# Database
DATABASE_URL=postgresql://ark:password@localhost:5432/ark_tools
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# LLM Settings
ARK_LLM_MODEL_PATH=/home/ark/.ark_tools/models/codellama-7b-instruct.gguf
ARK_LLM_CONTEXT_SIZE=8192
ARK_LLM_MAX_TOKENS=2048
ARK_LLM_THREADS=4
ARK_LLM_TEMPERATURE=0.1
ARK_LLM_ENABLE_GPU=false

# Security
ARK_SECRET_KEY=your-secret-key-here
ARK_API_KEY=your-api-key-here
ARK_ENABLE_AUTH=true

# Monitoring
ARK_ENABLE_MONITORING=true
ARK_METRICS_PORT=9090
```

#### Advanced Configuration (`config.yaml`)
```yaml
ark_tools:
  # Analysis settings
  analysis:
    max_file_size: 10485760  # 10MB
    excluded_patterns:
      - "*.pyc"
      - "__pycache__"
      - "node_modules"
      - ".git"
    supported_languages:
      - python
      - javascript
      - typescript
      - java
      - go
  
  # Performance settings
  performance:
    worker_processes: 4
    thread_pool_size: 10
    cache_ttl: 3600
    batch_size: 50
  
  # Security settings
  security:
    allowed_origins:
      - "http://localhost:3000"
      - "https://app.example.com"
    rate_limit: 100
    rate_limit_period: 60
```

### Environment-Specific Configuration

```bash
# Development
export ARK_TOOLS_ENV=development
export ARK_DEBUG=true

# Staging
export ARK_TOOLS_ENV=staging
export ARK_DEBUG=false

# Production
export ARK_TOOLS_ENV=production
export ARK_DEBUG=false
export ARK_ENABLE_MONITORING=true
```

## Service Management

### Starting Services

#### Systemd Service
```bash
# Create service file
sudo tee /etc/systemd/system/ark-tools.service << EOF
[Unit]
Description=ARK-TOOLS Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ark
WorkingDirectory=/opt/ark-tools
Environment="PATH=/opt/ark-tools/venv/bin"
ExecStart=/opt/ark-tools/venv/bin/ark-server
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable ark-tools
sudo systemctl start ark-tools
sudo systemctl status ark-tools
```

#### Docker Compose
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d ark-tools

# View logs
docker-compose logs -f ark-tools

# Stop services
docker-compose down
```

### Health Checks

```bash
# Check service health
curl http://localhost:8100/health

# Check readiness
curl http://localhost:8100/ready

# Check specific components
curl http://localhost:8100/health/database
curl http://localhost:8100/health/redis
curl http://localhost:8100/health/llm
```

## Model Management

### Downloading Models

```bash
# Create models directory
mkdir -p ~/.ark_tools/models
cd ~/.ark_tools/models

# Download CodeLlama-7B-Instruct (recommended)
wget https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf

# Download Mistral-7B-Instruct
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Download Phi-2
wget https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf
```

### Model Configuration

```bash
# Update model path in .env
ARK_LLM_MODEL_PATH=/home/ark/.ark_tools/models/codellama-7b-instruct.Q4_K_M.gguf

# Configure model parameters
ARK_LLM_CONTEXT_SIZE=8192    # Max context window
ARK_LLM_MAX_TOKENS=2048       # Max generation tokens
ARK_LLM_TEMPERATURE=0.1       # Lower = more deterministic
ARK_LLM_THREADS=4             # CPU threads to use
```

### GPU Acceleration

```bash
# Install CUDA support
pip install llama-cpp-python --force-reinstall --no-cache-dir \
    --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121

# Enable GPU in configuration
ARK_LLM_ENABLE_GPU=true
ARK_LLM_GPU_LAYERS=32  # Number of layers to offload
```

## Database Administration

### PostgreSQL Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE USER ark WITH PASSWORD 'secure_password';
CREATE DATABASE ark_tools OWNER ark;
GRANT ALL PRIVILEGES ON DATABASE ark_tools TO ark;
EOF

# Initialize schema
python -m ark_tools.setup.db_init

# Run migrations
alembic upgrade head
```

### Database Maintenance

```bash
# Backup database
pg_dump -U ark -h localhost ark_tools > backup_$(date +%Y%m%d).sql

# Restore database
psql -U ark -h localhost ark_tools < backup_20240114.sql

# Vacuum and analyze
psql -U ark -h localhost ark_tools -c "VACUUM ANALYZE;"

# Check database size
psql -U ark -h localhost ark_tools -c "
SELECT pg_database_size('ark_tools') / 1024 / 1024 AS size_mb;
"
```

### Redis Administration

```bash
# Connect to Redis
redis-cli

# Check memory usage
127.0.0.1:6379> INFO memory

# Clear cache
127.0.0.1:6379> FLUSHDB

# Set memory limit
127.0.0.1:6379> CONFIG SET maxmemory 2gb
127.0.0.1:6379> CONFIG SET maxmemory-policy allkeys-lru
```

## Monitoring and Logging

### Log Management

```bash
# Log locations
/var/log/ark-tools/ark-tools.log     # Application logs
/var/log/ark-tools/access.log        # Access logs
/var/log/ark-tools/error.log         # Error logs

# Configure log rotation
sudo tee /etc/logrotate.d/ark-tools << EOF
/var/log/ark-tools/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ark ark
    sharedscripts
    postrotate
        systemctl reload ark-tools
    endscript
}
EOF
```

### Monitoring with Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ark-tools'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "ARK-TOOLS Metrics",
    "panels": [
      {
        "title": "Analysis Rate",
        "targets": [
          {
            "expr": "rate(ark_tools_analysis_total[5m])"
          }
        ]
      },
      {
        "title": "LLM Inference Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, ark_tools_llm_inference_duration_seconds)"
          }
        ]
      }
    ]
  }
}
```

## Backup and Recovery

### Automated Backup Script

```bash
#!/bin/bash
# /opt/ark-tools/scripts/backup.sh

BACKUP_DIR="/backups/ark-tools"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup database
pg_dump -U ark -h localhost ark_tools > $BACKUP_DIR/$DATE/database.sql

# Backup configuration
cp /opt/ark-tools/.env $BACKUP_DIR/$DATE/
cp -r /opt/ark-tools/config $BACKUP_DIR/$DATE/

# Backup reports
tar czf $BACKUP_DIR/$DATE/reports.tar.gz /opt/ark-tools/.ark_reports

# Backup models
tar czf $BACKUP_DIR/$DATE/models.tar.gz ~/.ark_tools/models

# Remove old backups (keep 30 days)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR/$DATE"
```

### Recovery Procedure

```bash
# Stop services
systemctl stop ark-tools

# Restore database
psql -U ark -h localhost ark_tools < /backups/ark-tools/20240114_120000/database.sql

# Restore configuration
cp /backups/ark-tools/20240114_120000/.env /opt/ark-tools/

# Restore reports
tar xzf /backups/ark-tools/20240114_120000/reports.tar.gz -C /

# Restart services
systemctl start ark-tools
```

## Security Administration

### API Key Management

```python
# Generate API key
import secrets
api_key = secrets.token_urlsafe(32)
print(f"API Key: {api_key}")

# Store in database
INSERT INTO api_keys (key, name, created_at, expires_at) 
VALUES ('api_key_here', 'production_key', NOW(), NOW() + INTERVAL '1 year');
```

### SSL/TLS Configuration

```nginx
# /etc/nginx/sites-available/ark-tools
server {
    listen 443 ssl http2;
    server_name ark-tools.example.com;
    
    ssl_certificate /etc/letsencrypt/live/ark-tools.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ark-tools.example.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 443/tcp
sudo ufw allow 8100/tcp from 10.0.0.0/8
sudo ufw enable
```

## Performance Tuning

### System Optimization

```bash
# Increase file descriptors
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize kernel parameters
sudo tee -a /etc/sysctl.conf << EOF
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
vm.swappiness = 10
EOF

sudo sysctl -p
```

### Application Tuning

```python
# config.py optimization settings
WORKER_PROCESSES = os.cpu_count()
THREAD_POOL_SIZE = WORKER_PROCESSES * 2
CONNECTION_POOL_SIZE = 50
CACHE_SIZE = "2GB"
BATCH_PROCESSING_SIZE = 100
```

### Database Optimization

```sql
-- Index optimization
CREATE INDEX idx_analysis_created ON analyses(created_at);
CREATE INDEX idx_analysis_directory ON analyses(directory);
CREATE INDEX idx_reports_run_id ON reports(run_id);

-- Query optimization
EXPLAIN ANALYZE SELECT * FROM analyses WHERE created_at > NOW() - INTERVAL '7 days';
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
journalctl -u ark-tools -f

# Verify configuration
ark-setup validate

# Test database connection
python -c "from ark_tools.db import test_connection; test_connection()"
```

#### High Memory Usage
```bash
# Check memory usage
ps aux | grep ark-tools
free -h

# Limit memory usage
systemctl edit ark-tools
# Add: MemoryLimit=4G
```

#### Slow Analysis
```bash
# Check resource usage
htop
iotop

# Profile analysis
ARK_PROFILE=true ark-analyze analyze hybrid /path/to/code

# Review profile results
python -m pstats profile_results.prof
```

### Debug Mode

```bash
# Enable debug logging
export ARK_DEBUG=true
export ARK_LOG_LEVEL=DEBUG

# Run with verbose output
ark-analyze --verbose analyze hybrid /path/to/code

# Enable SQL query logging
export ARK_LOG_SQL=true
```

### Getting Help

```bash
# Check system status
ark-tools status --detailed

# Run diagnostics
ark-tools diagnose

# Generate support bundle
ark-tools support-bundle --output support.tar.gz
```

## Maintenance Schedule

### Daily Tasks
- Check service health
- Review error logs
- Monitor disk space

### Weekly Tasks
- Database vacuum
- Cache cleanup
- Log rotation verification

### Monthly Tasks
- Security updates
- Performance review
- Backup verification

### Quarterly Tasks
- Capacity planning
- Security audit
- Disaster recovery test