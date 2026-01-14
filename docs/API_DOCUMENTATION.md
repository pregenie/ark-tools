# ARK-TOOLS API Documentation

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Request/Response Format](#requestresponse-format)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [WebSocket API](#websocket-api)
8. [SDK Usage](#sdk-usage)
9. [Examples](#examples)

## API Overview

ARK-TOOLS provides a RESTful API for programmatic access to code analysis capabilities.

### Base URL
```
http://localhost:8100/api/v1
```

### API Versioning
- Current version: `v1`
- Version specified in URL path
- Backward compatibility maintained within major versions

### Content Types
- Request: `application/json`
- Response: `application/json`
- File uploads: `multipart/form-data`

## Authentication

### API Key Authentication

Include API key in request headers:

```http
Authorization: Bearer YOUR_API_KEY
```

### Generating API Keys

```bash
# Generate via CLI
ark-tools generate-api-key --name "production"

# Or via API
POST /api/v1/auth/generate-key
{
  "name": "production",
  "expires_in": 365
}
```

### API Key Management

```http
# List API keys
GET /api/v1/auth/keys

# Revoke API key
DELETE /api/v1/auth/keys/{key_id}

# Rotate API key
POST /api/v1/auth/keys/{key_id}/rotate
```

## Endpoints

### Analysis Endpoints

#### POST /api/v1/hybrid/analyze

Perform hybrid MAMS/LLM analysis on a codebase.

**Request:**
```json
{
  "directory": "/path/to/code",
  "strategy": "hybrid",
  "max_files": 50,
  "include_suggestions": true,
  "exclude_patterns": ["*.test.js", "node_modules"]
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| directory | string | Yes | Path to codebase |
| strategy | string | No | Analysis strategy: hybrid, fast, deep, compress_only |
| max_files | integer | No | Maximum files to analyze (default: 50) |
| include_suggestions | boolean | No | Include code organization suggestions |
| exclude_patterns | array | No | File patterns to exclude |

**Response:**
```json
{
  "success": true,
  "operation_id": "op_abc123",
  "analysis": {
    "structure": {
      "total_files": 142,
      "total_components": 456,
      "components": {
        "classes": 78,
        "functions": 234,
        "constants": 144
      }
    },
    "domains": [
      {
        "name": "Authentication",
        "description": "User authentication and authorization",
        "primary_components": ["auth.py", "jwt.py"],
        "confidence": 0.92
      }
    ],
    "timing": {
      "mams_ms": 1234,
      "compression_ms": 456,
      "llm_ms": 2345,
      "total_ms": 4035
    },
    "suggestions": [
      {
        "type": "refactor",
        "description": "Extract authentication logic into separate module",
        "impact": "high"
      }
    ]
  }
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid parameters
- `404`: Directory not found
- `500`: Analysis failed

---

#### POST /api/v1/hybrid/analyze/domains

Analyze semantic domains in code using LLM.

**Request:**
```json
{
  "directory": "/path/to/code",
  "context": "E-commerce platform",
  "include_intent": true
}
```

**Alternative Request (with pre-compressed code):**
```json
{
  "code_skeleton": "class UserService:\n    def get_user(): pass\n    def create_user(): pass",
  "context": "User management service",
  "include_intent": true
}
```

**Response:**
```json
{
  "success": true,
  "operation_id": "op_xyz789",
  "domains": [
    {
      "name": "User Management",
      "description": "Handles user CRUD operations",
      "primary_components": ["UserService"],
      "relationships": [
        {
          "source": "UserService",
          "target": "Database",
          "type": "depends_on"
        }
      ],
      "confidence": 0.88
    }
  ],
  "intent": {
    "primary_purpose": "User data management",
    "architectural_pattern": "Service layer",
    "design_patterns": ["Repository", "DTO"]
  }
}
```

---

#### POST /api/v1/hybrid/compress

Compress code to AST skeleton for LLM analysis.

**Request:**
```json
{
  "directory": "/path/to/code",
  "max_files": 50,
  "exclude_patterns": ["test_*", "__pycache__"]
}
```

**Response:**
```json
{
  "success": true,
  "compressed_files": {
    "main.py": "class App:\n    def __init__(): pass\n    def run(): pass",
    "utils.py": "def helper_function(): pass\nclass Utility:\n    def process(): pass"
  },
  "statistics": {
    "files_compressed": 45,
    "total_characters": 12543,
    "estimated_tokens": 3135,
    "compression_ratio": 0.82
  }
}
```

### Report Endpoints

#### POST /api/v1/hybrid/reports/generate

Generate reports from analysis results.

**Request:**
```json
{
  "analysis_data": {
    "structure": {...},
    "domains": [...],
    "timing": {...}
  },
  "format": ["json", "markdown", "html"],
  "output_dir": "/path/to/reports"
}
```

**Response:**
```json
{
  "success": true,
  "reports": {
    "json": "/path/to/reports/latest/master.json",
    "markdown": "/path/to/reports/latest/presentation/report.md",
    "html": "/path/to/reports/latest/presentation/report.html"
  },
  "report_dir": "/path/to/reports/latest"
}
```

---

#### GET /api/v1/hybrid/reports/latest

Get the latest report summary.

**Response:**
```json
{
  "success": true,
  "summary": {
    "metadata": {
      "timestamp": "2024-01-14T12:00:00Z",
      "run_id": "run_abc123",
      "directory": "/analyzed/code"
    },
    "statistics": {
      "total_files": 150,
      "total_components": 450,
      "total_domains": 6
    },
    "key_insights": [
      "Well-structured authentication domain",
      "Database layer could benefit from abstraction"
    ]
  },
  "report_dir": "/path/to/reports/latest"
}
```

---

#### GET /api/v1/hybrid/reports/history

Get history of all analysis reports.

**Response:**
```json
{
  "success": true,
  "history": {
    "runs": [
      {
        "run_id": "run_abc123",
        "timestamp": "2024-01-14T12:00:00Z",
        "directory": "/analyzed/code",
        "files_analyzed": 150,
        "strategy": "hybrid"
      }
    ]
  }
}
```

---

#### GET /api/v1/hybrid/reports/{report_id}

Get a specific report by ID or timestamp.

**Response:**
```json
{
  "success": true,
  "report_id": "run_abc123",
  "data": {
    "metadata": {...},
    "structure": {...},
    "domains": [...],
    "suggestions": [...]
  },
  "available_files": {
    "master": "/path/to/master.json",
    "summary": "/path/to/summary.json",
    "report.md": "/path/to/report.md",
    "report.html": "/path/to/report.html"
  }
}
```

### Model Endpoints

#### GET /api/v1/hybrid/model/info

Get information about the loaded LLM model.

**Response:**
```json
{
  "success": true,
  "model": {
    "path": "/home/user/.ark_tools/models/codellama-7b.gguf",
    "size_mb": 4321,
    "loaded": true,
    "config": {
      "context_size": 8192,
      "max_tokens": 2048,
      "threads": 4,
      "temperature": 0.1,
      "gpu_enabled": false
    }
  }
}
```

---

#### POST /api/v1/hybrid/model/download

Download a specific LLM model (placeholder - not yet implemented).

**Request:**
```json
{
  "model_name": "codellama-7b-instruct",
  "model_url": "https://huggingface.co/..."
}
```

**Response:**
```json
{
  "success": false,
  "message": "Model download not yet implemented",
  "instructions": [
    "To download models manually:",
    "1. Visit https://huggingface.co/models?library=gguf",
    "2. Download the desired GGUF model",
    "3. Save to ~/.ark_tools/models/",
    "4. Update ARK_LLM_MODEL_PATH in .env"
  ]
}
```

### Health Check Endpoints

#### GET /health

Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-14T12:00:00Z"
}
```

---

#### GET /ready

Readiness check with component status.

**Response:**
```json
{
  "ready": true,
  "components": {
    "database": "ready",
    "redis": "ready",
    "llm": "ready"
  }
}
```

---

#### GET /metrics

Prometheus-format metrics.

**Response:**
```
# HELP ark_tools_analysis_total Total number of analyses performed
# TYPE ark_tools_analysis_total counter
ark_tools_analysis_total 142

# HELP ark_tools_analysis_duration_seconds Analysis duration in seconds
# TYPE ark_tools_analysis_duration_seconds histogram
ark_tools_analysis_duration_seconds_bucket{le="1"} 10
ark_tools_analysis_duration_seconds_bucket{le="5"} 35
ark_tools_analysis_duration_seconds_bucket{le="10"} 40
```

## Request/Response Format

### Standard Request Headers

```http
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY
X-Request-ID: unique-request-id
```

### Standard Response Format

```json
{
  "success": true|false,
  "data": {...} | null,
  "error": "error message" | null,
  "metadata": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-14T12:00:00Z",
    "duration_ms": 1234
  }
}
```

### Pagination

For endpoints returning lists:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

Query parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_DIRECTORY",
    "message": "The specified directory does not exist",
    "details": {
      "directory": "/invalid/path"
    }
  },
  "metadata": {
    "request_id": "req_xyz789",
    "timestamp": "2024-01-14T12:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Invalid request parameters |
| UNAUTHORIZED | 401 | Missing or invalid API key |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

### Error Handling Best Practices

```python
import requests

def analyze_code(directory):
    try:
        response = requests.post(
            "http://localhost:8100/api/v1/hybrid/analyze",
            json={"directory": directory},
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            # Handle rate limiting
            retry_after = e.response.headers.get('Retry-After', 60)
            time.sleep(int(retry_after))
            return analyze_code(directory)  # Retry
        else:
            # Handle other errors
            error_data = e.response.json()
            print(f"Error: {error_data['error']['message']}")
            raise
```

## Rate Limiting

### Rate Limits

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| /analyze | 10 requests | 1 minute |
| /compress | 20 requests | 1 minute |
| /reports | 100 requests | 1 minute |
| /model | 50 requests | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1673700000
Retry-After: 45
```

### Handling Rate Limits

```javascript
async function makeRequest(url, options) {
  const response = await fetch(url, options);
  
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After') || 60;
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    return makeRequest(url, options);
  }
  
  return response;
}
```

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8100/ws');

ws.on('open', () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'YOUR_API_KEY'
  }));
});
```

### Real-Time Analysis Updates

```javascript
// Start analysis
ws.send(JSON.stringify({
  type: 'analyze',
  data: {
    directory: '/path/to/code',
    strategy: 'hybrid'
  }
}));

// Receive updates
ws.on('message', (data) => {
  const message = JSON.parse(data);
  
  switch(message.type) {
    case 'progress':
      console.log(`Progress: ${message.data.percentage}%`);
      break;
    case 'phase_complete':
      console.log(`Completed: ${message.data.phase}`);
      break;
    case 'result':
      console.log('Analysis complete:', message.data);
      break;
    case 'error':
      console.error('Error:', message.data.error);
      break;
  }
});
```

### WebSocket Events

| Event | Description | Data |
|-------|-------------|------|
| progress | Analysis progress update | `{percentage: 50, phase: "compression"}` |
| phase_complete | Phase completed | `{phase: "mams", duration_ms: 1234}` |
| result | Final result | Full analysis data |
| error | Error occurred | `{error: "message", code: "ERROR_CODE"}` |

## SDK Usage

### Python SDK

```python
from ark_tools.sdk import ArkToolsClient

# Initialize client
client = ArkToolsClient(
    base_url="http://localhost:8100",
    api_key="YOUR_API_KEY"
)

# Perform analysis
result = client.analyze(
    directory="/path/to/code",
    strategy="hybrid",
    max_files=50
)

# Generate report
report = client.generate_report(
    analysis_data=result,
    formats=["markdown", "html"]
)

# View domains
for domain in result.domains:
    print(f"{domain.name}: {domain.confidence}")
```

### JavaScript SDK

```javascript
import { ArkToolsClient } from 'ark-tools-sdk';

// Initialize client
const client = new ArkToolsClient({
  baseUrl: 'http://localhost:8100',
  apiKey: 'YOUR_API_KEY'
});

// Perform analysis
const result = await client.analyze({
  directory: '/path/to/code',
  strategy: 'hybrid',
  maxFiles: 50
});

// Generate report
const report = await client.generateReport({
  analysisData: result,
  formats: ['markdown', 'html']
});

// View domains
result.domains.forEach(domain => {
  console.log(`${domain.name}: ${domain.confidence}`);
});
```

### Go SDK

```go
package main

import (
    "github.com/ark-tools/ark-tools-go"
)

func main() {
    // Initialize client
    client := arktools.NewClient(
        "http://localhost:8100",
        "YOUR_API_KEY",
    )
    
    // Perform analysis
    result, err := client.Analyze(arktools.AnalyzeOptions{
        Directory: "/path/to/code",
        Strategy:  "hybrid",
        MaxFiles:  50,
    })
    
    if err != nil {
        panic(err)
    }
    
    // View domains
    for _, domain := range result.Domains {
        fmt.Printf("%s: %f\n", domain.Name, domain.Confidence)
    }
}
```

## Examples

### Complete Analysis Workflow

```python
import requests
import json
import time

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8100/api/v1"

def complete_analysis(directory):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # Step 1: Run analysis
    print("Starting analysis...")
    analysis_response = requests.post(
        f"{BASE_URL}/hybrid/analyze",
        json={
            "directory": directory,
            "strategy": "hybrid",
            "max_files": 75,
            "include_suggestions": True
        },
        headers=headers
    )
    analysis_response.raise_for_status()
    analysis_data = analysis_response.json()["analysis"]
    
    print(f"Found {len(analysis_data['domains'])} domains")
    
    # Step 2: Generate reports
    print("Generating reports...")
    report_response = requests.post(
        f"{BASE_URL}/hybrid/reports/generate",
        json={
            "analysis_data": analysis_data,
            "format": ["json", "markdown", "html"]
        },
        headers=headers
    )
    report_response.raise_for_status()
    report_paths = report_response.json()["reports"]
    
    print(f"Reports generated: {report_paths}")
    
    # Step 3: Get summary
    summary_response = requests.get(
        f"{BASE_URL}/hybrid/reports/latest",
        headers=headers
    )
    summary_response.raise_for_status()
    summary = summary_response.json()["summary"]
    
    return {
        "analysis": analysis_data,
        "reports": report_paths,
        "summary": summary
    }

# Run analysis
result = complete_analysis("/path/to/your/code")
print(json.dumps(result["summary"], indent=2))
```

### Streaming Analysis with WebSocket

```javascript
class ArkToolsAnalyzer {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.ws = null;
  }
  
  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket('ws://localhost:8100/ws');
      
      this.ws.on('open', () => {
        this.ws.send(JSON.stringify({
          type: 'auth',
          token: this.apiKey
        }));
        resolve();
      });
      
      this.ws.on('error', reject);
    });
  }
  
  async analyzeWithProgress(directory, onProgress) {
    await this.connect();
    
    return new Promise((resolve, reject) => {
      this.ws.send(JSON.stringify({
        type: 'analyze',
        data: {
          directory: directory,
          strategy: 'hybrid'
        }
      }));
      
      this.ws.on('message', (data) => {
        const message = JSON.parse(data);
        
        if (message.type === 'progress') {
          onProgress(message.data);
        } else if (message.type === 'result') {
          resolve(message.data);
          this.ws.close();
        } else if (message.type === 'error') {
          reject(new Error(message.data.error));
          this.ws.close();
        }
      });
    });
  }
}

// Usage
const analyzer = new ArkToolsAnalyzer('YOUR_API_KEY');

analyzer.analyzeWithProgress(
  '/path/to/code',
  (progress) => {
    console.log(`${progress.percentage}% - ${progress.phase}`);
  }
).then(result => {
  console.log('Analysis complete:', result);
});
```

### Batch Analysis

```bash
#!/bin/bash

# Batch analyze multiple projects

API_KEY="your_api_key"
BASE_URL="http://localhost:8100/api/v1"

projects=(
  "/path/to/project1"
  "/path/to/project2"
  "/path/to/project3"
)

for project in "${projects[@]}"; do
  echo "Analyzing $project..."
  
  curl -X POST "$BASE_URL/hybrid/analyze" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"directory\": \"$project\",
      \"strategy\": \"hybrid\",
      \"max_files\": 50
    }" \
    -o "$(basename $project)_analysis.json"
  
  echo "Completed $project"
  sleep 5  # Rate limiting
done
```