"""
Web UI for ARK-TOOLS Setup
===========================

FastAPI-based web interface with embedded Vue.js frontend.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ark_tools.setup.detector import EnvironmentDetector, ServiceDetector
from ark_tools.setup.configurator import SetupConfigurator, ServiceMode, ServiceConfig
from ark_tools.setup.validator import ConnectionValidator
from ark_tools.setup.orchestrator import SetupOrchestrator

# Pydantic models for API
class DetectionRequest(BaseModel):
    search_paths: Optional[List[str]] = None

class ServiceConfigRequest(BaseModel):
    service_id: str
    mode: str
    options: Dict[str, Any] = {}

class InheritanceRequest(BaseModel):
    env_path: str
    keys: List[str]

class SaveConfigRequest(BaseModel):
    output_dir: str = "."
    
class TestConnectionRequest(BaseModel):
    service_type: str
    host: str
    port: int
    credentials: Optional[Dict[str, str]] = None

# Create FastAPI app
def create_setup_app() -> FastAPI:
    """Create the FastAPI setup application"""
    app = FastAPI(title="ARK-TOOLS Setup Assistant")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # State management
    app.state.orchestrator = SetupOrchestrator()
    app.state.connected_clients = set()
    
    return app

app = create_setup_app()

# HTML template with embedded Vue.js application
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARK-TOOLS Setup Assistant</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='80' font-size='80'>🚀</text></svg>">
    <script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js"></script>
    <style>
        [v-cloak] { display: none; }
        
        /* Reset and base styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #f9fafb;
            color: #111827;
            line-height: 1.5;
        }
        
        /* Layout utilities */
        .container {
            max-width: 80rem;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        .min-h-screen {
            min-height: 100vh;
        }
        
        /* Typography */
        h1 { font-size: 1.875rem; font-weight: 700; }
        h2 { font-size: 1.25rem; font-weight: 600; }
        h3 { font-size: 1rem; font-weight: 500; }
        
        .text-sm { font-size: 0.875rem; }
        .text-xs { font-size: 0.75rem; }
        
        /* Colors */
        .bg-white { background-color: white; }
        .bg-gray-50 { background-color: #f9fafb; }
        .bg-gray-100 { background-color: #f3f4f6; }
        .bg-gray-200 { background-color: #e5e7eb; }
        .bg-indigo-50 { background-color: #eef2ff; }
        .bg-indigo-600 { background-color: #4f46e5; }
        .bg-indigo-700 { background-color: #4338ca; }
        .bg-green-50 { background-color: #f0fdf4; }
        .bg-green-100 { background-color: #dcfce7; }
        .bg-green-600 { background-color: #16a34a; }
        .bg-amber-50 { background-color: #fffbeb; }
        .bg-amber-100 { background-color: #fef3c7; }
        .bg-amber-600 { background-color: #d97706; }
        .bg-red-100 { background-color: #fee2e2; }
        .bg-blue-50 { background-color: #eff6ff; }
        
        .text-gray-500 { color: #6b7280; }
        .text-gray-600 { color: #4b5563; }
        .text-gray-700 { color: #374151; }
        .text-gray-900 { color: #111827; }
        .text-white { color: white; }
        .text-indigo-500 { color: #6366f1; }
        .text-green-500 { color: #10b981; }
        .text-green-600 { color: #16a34a; }
        .text-green-800 { color: #166534; }
        .text-amber-600 { color: #d97706; }
        .text-amber-700 { color: #b45309; }
        .text-amber-800 { color: #92400e; }
        .text-amber-900 { color: #78350f; }
        .text-red-500 { color: #ef4444; }
        .text-red-600 { color: #dc2626; }
        .text-red-800 { color: #991b1b; }
        .text-blue-700 { color: #1d4ed8; }
        .text-blue-900 { color: #1e3a8a; }
        .text-yellow-600 { color: #ca8a04; }
        
        .border-gray-200 { border-color: #e5e7eb; }
        .border-gray-300 { border-color: #d1d5db; }
        .border-indigo-500 { border-color: #6366f1; }
        .border-amber-400 { border-color: #fbbf24; }
        
        /* Spacing */
        .p-2 { padding: 0.5rem; }
        .p-3 { padding: 0.75rem; }
        .p-4 { padding: 1rem; }
        .p-6 { padding: 1.5rem; }
        .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
        .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
        .py-6 { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        .py-8 { padding-top: 2rem; padding-bottom: 2rem; }
        .px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
        .px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .pb-8 { padding-bottom: 2rem; }
        .mt-1 { margin-top: 0.25rem; }
        .mt-2 { margin-top: 0.5rem; }
        .mt-3 { margin-top: 0.75rem; }
        .mt-4 { margin-top: 1rem; }
        .mt-6 { margin-top: 1.5rem; }
        .mt-8 { margin-top: 2rem; }
        .mb-1 { margin-bottom: 0.25rem; }
        .mb-2 { margin-bottom: 0.5rem; }
        .mb-3 { margin-bottom: 0.75rem; }
        .mb-4 { margin-bottom: 1rem; }
        .mb-6 { margin-bottom: 1.5rem; }
        .ml-2 { margin-left: 0.5rem; }
        .ml-3 { margin-left: 0.75rem; }
        .ml-4 { margin-left: 1rem; }
        .space-x-2 > * + * { margin-left: 0.5rem; }
        .space-x-3 > * + * { margin-left: 0.75rem; }
        .space-x-4 > * + * { margin-left: 1rem; }
        .space-y-2 > * + * { margin-top: 0.5rem; }
        .space-y-4 > * + * { margin-top: 1rem; }
        
        /* Borders and shadows */
        .border { border-width: 1px; border-style: solid; }
        .border-2 { border-width: 2px; border-style: solid; }
        .border-dashed { border-style: dashed; }
        .rounded { border-radius: 0.25rem; }
        .rounded-lg { border-radius: 0.5rem; }
        .rounded-full { border-radius: 9999px; }
        .shadow { box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        
        /* Flexbox */
        .flex { display: flex; }
        .items-start { align-items: flex-start; }
        .items-center { align-items: center; }
        .justify-between { justify-content: space-between; }
        .justify-center { justify-content: center; }
        .justify-end { justify-content: flex-end; }
        
        /* Forms */
        input[type="text"],
        input[type="number"] {
            width: 100%;
            padding: 0.5rem 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 0.25rem;
            font-size: 0.875rem;
        }
        
        input[type="radio"] {
            margin-top: 0.25rem;
        }
        
        /* Buttons */
        button {
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
            border: none;
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        button:hover:not(:disabled) {
            filter: brightness(0.9);
        }
        
        /* Progress steps */
        .progress-step {
            position: relative;
            display: flex;
            align-items: center;
        }
        
        .progress-line {
            position: absolute;
            height: 2px;
            width: 100%;
        }
        
        /* Hover states */
        .hover-bg-gray-50:hover { background-color: #f9fafb; }
        .hover-bg-indigo-700:hover { background-color: #4338ca; }
        .hover-bg-green-700:hover { background-color: #15803d; }
        .hover-bg-amber-700:hover { background-color: #b45309; }
        .hover-bg-yellow-700:hover { background-color: #a16207; }
        .hover-border-gray-300:hover { border-color: #d1d5db; }
        
        /* Modal */
        .modal-backdrop {
            position: fixed;
            inset: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 50;
        }
        
        .modal-content {
            background-color: white;
            border-radius: 0.5rem;
            padding: 1.5rem;
            max-width: 32rem;
            width: 100%;
        }
        
        /* Utilities */
        .relative { position: relative; }
        .block { display: block; }
        .inset-0 { inset: 0; }
        .w-full { width: 100%; }
        .w-8 { width: 2rem; }
        .h-8 { height: 2rem; }
        .h-0-5 { height: 0.125rem; }
        .font-medium { font-weight: 500; }
        .font-semibold { font-weight: 600; }
        .font-bold { font-weight: 700; }
        .cursor-pointer { cursor: pointer; }
        .transition { transition: all 0.15s; }
        .overflow-x-auto { overflow-x: auto; }
        
        /* Responsive utilities */
        @media (min-width: 640px) {
            .sm-px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
            .sm-pr-20 { padding-right: 5rem; }
        }
        
        @media (min-width: 1024px) {
            .lg-px-8 { padding-left: 2rem; padding-right: 2rem; }
        }
        
        /* Animations */
        .fade-enter-active, .fade-leave-active {
            transition: opacity 0.5s;
        }
        .fade-enter-from, .fade-leave-to {
            opacity: 0;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div id="app" v-cloak class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow">
            <div class="container px-4 sm-px-6 lg-px-8 py-6">
                <h1 class="font-bold text-gray-900">🚀 ARK-TOOLS Setup Assistant</h1>
                <p class="mt-2 text-sm text-gray-600">Intelligent configuration for your code consolidation platform</p>
            </div>
        </header>

        <!-- Progress Steps -->
        <div class="container px-4 sm-px-6 lg-px-8 py-8">
            <nav aria-label="Progress">
                <ol class="flex items-center">
                    <li v-for="(step, index) in steps" :key="index"
                        :class="['relative', index !== steps.length - 1 ? 'pr-8 sm-pr-20' : '']">
                        <div class="absolute inset-0 flex items-center" v-if="index !== steps.length - 1">
                            <div class="h-0-5 w-full" 
                                :class="currentStep > index ? 'bg-indigo-600' : 'bg-gray-200'"></div>
                        </div>
                        <div class="relative flex h-8 w-8 items-center justify-center rounded-full"
                            :class="currentStep === index ? 'bg-indigo-600 text-white' : 
                                    currentStep > index ? 'bg-indigo-600 text-white' : 
                                    'bg-white border-2 border-gray-300 text-gray-500'">
                            <span class="text-sm">{{ index + 1 }}</span>
                        </div>
                        <span class="ml-2 text-sm font-medium"
                            :class="currentStep >= index ? 'text-gray-900' : 'text-gray-500'">
                            {{ step }}
                        </span>
                    </li>
                </ol>
            </nav>
        </div>

        <!-- Main Content -->
        <main class="container px-4 sm-px-6 lg-px-8 pb-8">
            <div class="bg-white shadow rounded-lg">
                <div class="p-6">
                    <!-- Step 1: Environment Detection -->
                    <div v-show="currentStep === 0">
                        <h2 class="text-xl font-semibold mb-4">🔍 Environment & System Check</h2>
                        
                        <!-- System Resources Check -->
                        <div class="mb-6 p-4 bg-blue-50 rounded-lg">
                            <h3 class="font-medium text-blue-900 mb-2">💻 System Resources</h3>
                            <div v-if="!systemResources" class="text-sm text-blue-700">
                                <button @click="checkSystemResources" 
                                        :disabled="checkingResources"
                                        class="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50">
                                    {{ checkingResources ? 'Checking...' : 'Check System Capacity' }}
                                </button>
                            </div>
                            <div v-else class="space-y-2">
                                <div class="text-sm">
                                    <span class="font-medium">CPU:</span> {{ systemResources.cpu_count }} cores
                                    <span :class="systemResources.cpu_count >= 4 ? 'text-green-600' : 'text-amber-600'">
                                        ({{ systemResources.cpu_count >= 4 ? '✓ Good' : '⚠️ Limited' }})
                                    </span>
                                </div>
                                <div class="text-sm">
                                    <span class="font-medium">RAM:</span> {{ systemResources.memory_available_gb.toFixed(1) }}GB available
                                    <span :class="systemResources.memory_available_gb >= 4 ? 'text-green-600' : 'text-amber-600'">
                                        ({{ systemResources.memory_available_gb >= 4 ? '✓ Good' : '⚠️ Limited' }})
                                    </span>
                                </div>
                                <div class="text-sm">
                                    <span class="font-medium">Disk:</span> {{ systemResources.disk_available_gb.toFixed(1) }}GB available
                                    <span :class="systemResources.disk_available_gb >= 10 ? 'text-green-600' : 'text-amber-600'">
                                        ({{ systemResources.disk_available_gb >= 10 ? '✓ Good' : '⚠️ Limited' }})
                                    </span>
                                </div>
                                <div class="text-sm">
                                    <span class="font-medium">Docker:</span> 
                                    <span :class="systemResources.docker_available ? 'text-green-600' : 'text-red-600'">
                                        {{ systemResources.docker_available ? '✓ Available' : '✗ Not Available' }}
                                    </span>
                                    <span v-if="systemResources.docker_available">
                                        ({{ systemResources.docker_running_containers }} containers running)
                                    </span>
                                </div>
                                
                                <div v-if="systemResources.warnings && systemResources.warnings.length > 0" 
                                     class="mt-3 p-2 bg-amber-100 rounded">
                                    <div v-for="warning in systemResources.warnings" :key="warning" class="text-sm text-amber-800">
                                        {{ warning }}
                                    </div>
                                </div>
                                
                                <div v-if="systemResources.recommendations && systemResources.recommendations.length > 0" 
                                     class="mt-2">
                                    <div v-for="rec in systemResources.recommendations" :key="rec" class="text-sm text-blue-700">
                                        {{ rec }}
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <h3 class="font-medium text-gray-900 mb-2">📁 Environment Files</h3>
                        <button @click="scanEnvironment" 
                                :disabled="scanning"
                                class="mb-4 px-4 py-2 bg-indigo-600 text-white rounded hover-bg-indigo-700 disabled:opacity-50">
                            {{ scanning ? 'Scanning...' : 'Scan for Environment Files' }}
                        </button>

                        <div v-if="detectedEnvs.length > 0" class="space-y-4">
                            <div v-for="env in detectedEnvs" :key="env.path"
                                 @click="selectEnvironment(env)"
                                 :class="['border rounded-lg p-4 cursor-pointer transition',
                                         selectedEnv?.path === env.path ? 
                                         'border-indigo-500 bg-indigo-50' : 
                                         'border-gray-200 hover-border-gray-300']">
                                <div class="flex items-start justify-between">
                                    <div>
                                        <h3 class="font-medium">📁 {{ env.project_name || 'Unknown Project' }}</h3>
                                        <p class="text-sm text-gray-600">{{ env.path }}</p>
                                        <div class="mt-2 flex space-x-4">
                                            <span v-if="env.has_database" class="text-sm">🗄️ Database</span>
                                            <span v-if="env.has_redis" class="text-sm">📦 Redis</span>
                                            <span v-if="env.has_ai_keys" class="text-sm">🤖 AI Keys</span>
                                        </div>
                                    </div>
                                    <div v-if="selectedEnv?.path === env.path" 
                                         class="text-green-500">
                                        ✓
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div v-else-if="!scanning" class="text-gray-500">
                            No environment files detected yet. Click scan to search.
                        </div>
                    </div>

                    <!-- Step 2: Service Discovery -->
                    <div v-show="currentStep === 1">
                        <h2 class="text-xl font-semibold mb-4">🔍 Service Discovery</h2>
                        <p class="text-sm text-gray-600 mb-4">
                            ARK-TOOLS needs an execution container, PostgreSQL for data storage, and Redis for caching (optional).
                            We'll check what you have running, or help you create new services.
                        </p>
                        
                        <button @click="detectServices"
                                :disabled="detectingServices"
                                class="mb-4 px-4 py-2 bg-indigo-600 text-white rounded hover-bg-indigo-700 disabled:opacity-50">
                            {{ detectingServices ? 'Detecting...' : 'Detect Services' }}
                        </button>

                        <div v-if="detectedServices.length > 0" class="space-y-4">
                            <!-- ARK-TOOLS Container -->
                            <div v-if="arkToolsServices.length > 0">
                                <h3 class="font-medium text-gray-900 mb-2">🚀 ARK-TOOLS Execution Container</h3>
                                <p class="text-sm text-gray-600 mb-3">
                                    Found existing ARK-TOOLS container. You can use this to run your system efficiently.
                                </p>
                                <div class="space-y-2">
                                    <div v-for="service in arkToolsServices" :key="service.id"
                                         class="border rounded-lg p-4 bg-green-50">
                                        <div class="flex items-start justify-between">
                                            <div>
                                                <div class="flex items-center space-x-2">
                                                    <span :class="service.is_running ? 'text-green-500' : 'text-red-500'">
                                                        {{ service.is_running ? '🟢' : '🔴' }}
                                                    </span>
                                                    <span class="font-medium">ARK-TOOLS Container</span>
                                                    <span>🐳</span>
                                                </div>
                                                <p class="text-sm text-gray-600">Container: {{ service.container_name }}</p>
                                                <p class="text-sm text-gray-500">
                                                    Version: {{ service.version || 'latest' }}
                                                </p>
                                            </div>
                                            <button @click="configureService(service)"
                                                    class="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover-bg-indigo-700">
                                                Configure
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="border-2 border-dashed border-amber-400 rounded-lg p-4 bg-amber-50">
                                <h3 class="font-medium text-amber-900 mb-2">⚠️ No ARK-TOOLS Container Found</h3>
                                <p class="text-sm text-amber-700 mb-3">
                                    ARK-TOOLS runs best in its own optimized container. We'll help you create one.
                                </p>
                                <button @click="createArkToolsContainer"
                                        class="px-4 py-2 bg-amber-600 text-white rounded hover-bg-amber-700">
                                    Create ARK-TOOLS Container
                                </button>
                            </div>

                            <!-- PostgreSQL Services -->
                            <div v-if="postgresServices.length > 0">
                                <h3 class="font-medium text-gray-900 mb-2">PostgreSQL Services</h3>
                                <div class="space-y-2">
                                    <div v-for="service in postgresServices" :key="service.id"
                                         class="border rounded-lg p-4">
                                        <div class="flex items-start justify-between">
                                            <div>
                                                <div class="flex items-center space-x-2">
                                                    <span :class="service.is_running ? 'text-green-500' : 'text-red-500'">
                                                        {{ service.is_running ? '🟢' : '🔴' }}
                                                    </span>
                                                    <span class="font-medium">PostgreSQL</span>
                                                    <span v-if="service.source === 'docker'">🐳</span>
                                                    <span v-else-if="service.source === 'native'">💻</span>
                                                </div>
                                                <p class="text-sm text-gray-600">{{ service.host }}:{{ service.port }}</p>
                                                <p v-if="service.container_name" class="text-sm text-gray-500">
                                                    Container: {{ service.container_name }}
                                                </p>
                                            </div>
                                            <button @click="configureService(service)"
                                                    class="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover-bg-indigo-700">
                                                Use This Service
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Redis Services -->
                            <div v-if="redisServices.length > 0">
                                <h3 class="font-medium text-gray-900 mb-2">Redis Services</h3>
                                <div class="space-y-2">
                                    <div v-for="service in redisServices" :key="service.id"
                                         class="border rounded-lg p-4">
                                        <div class="flex items-start justify-between">
                                            <div>
                                                <div class="flex items-center space-x-2">
                                                    <span :class="service.is_running ? 'text-green-500' : 'text-red-500'">
                                                        {{ service.is_running ? '🟢' : '🔴' }}
                                                    </span>
                                                    <span class="font-medium">Redis</span>
                                                    <span v-if="service.source === 'docker'">🐳</span>
                                                    <span v-else-if="service.source === 'native'">💻</span>
                                                </div>
                                                <p class="text-sm text-gray-600">{{ service.host }}:{{ service.port }}</p>
                                                <p v-if="service.container_name" class="text-sm text-gray-500">
                                                    Container: {{ service.container_name }}
                                                </p>
                                            </div>
                                            <button @click="configureService(service)"
                                                    class="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover-bg-indigo-700">
                                                Use This Service
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div v-else-if="!detectingServices" class="text-gray-500">
                            <p>No services detected yet. Click "Detect Services" to scan.</p>
                            <div class="mt-4 p-4 bg-blue-50 rounded-lg">
                                <p class="text-sm font-medium text-blue-900">💡 {{ noServicesHintTitle }}</p>
                                <p class="text-sm text-blue-700 mt-1">No problem! After detection, ARK-TOOLS can:</p>
                                <ul class="text-sm text-blue-700 mt-2 ml-4">
                                    <li>• Create new Docker containers for you</li>
                                    <li>• Generate docker-compose.yml configuration</li>
                                    <li>• Use SQLite as a fallback (if needed)</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    <!-- Step 3: Configuration -->
                    <div v-show="currentStep === 2">
                        <h2 class="text-xl font-semibold mb-4">⚙️ Service Configuration</h2>
                        
                        <div class="space-y-4">
                            <div v-for="(config, service) in serviceConfigs" :key="service"
                                 class="border rounded-lg p-4">
                                <h3 class="font-medium mb-2">{{ service }}</h3>
                                <p class="text-sm text-gray-600">Mode: {{ config.mode }}</p>
                                <div v-if="config.warnings.length > 0" class="mt-2">
                                    <p v-for="warning in config.warnings" :key="warning"
                                       class="text-sm text-yellow-600">⚠️ {{ warning }}</p>
                                </div>
                            </div>
                        </div>

                        <div v-if="Object.keys(serviceConfigs).length === 0" class="text-gray-500">
                            No services configured yet. Go back and configure detected services.
                        </div>
                    </div>

                    <!-- Step 4: Review & Save -->
                    <div v-show="currentStep === 3">
                        <h2 class="text-xl font-semibold mb-4">📋 Review Configuration</h2>
                        
                        <div class="mb-4">
                            <h3 class="font-medium mb-2">Environment Preview</h3>
                            <pre class="bg-gray-100 p-4 rounded overflow-x-auto text-sm">{{ configPreview }}</pre>
                        </div>

                        <div class="flex space-x-4">
                            <button @click="testConnections"
                                    :disabled="testing"
                                    class="px-4 py-2 bg-yellow-600 text-white rounded hover-bg-yellow-700 disabled:opacity-50">
                                {{ testing ? 'Testing...' : 'Test Connections' }}
                            </button>

                            <button @click="saveConfiguration"
                                    :disabled="saving"
                                    class="px-4 py-2 bg-green-600 text-white rounded hover-bg-green-700 disabled:opacity-50">
                                {{ saving ? 'Saving...' : 'Save Configuration' }}
                            </button>
                        </div>

                        <div v-if="testResults" class="mt-4 p-4 bg-gray-100 rounded">
                            <h3 class="font-medium mb-2">Connection Test Results</h3>
                            <div v-for="(result, service) in testResults" :key="service">
                                <span :class="result.connected ? 'text-green-600' : 'text-red-600'">
                                    {{ result.connected ? '✅' : '❌' }} {{ service }}: {{ result.message }}
                                </span>
                            </div>
                        </div>

                        <div v-if="saveStatus" class="mt-4 p-4 rounded"
                             :class="saveStatus.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">
                            {{ saveStatus.message }}
                        </div>
                    </div>

                    <!-- Navigation Buttons -->
                    <div class="mt-8 flex justify-between">
                        <button @click="previousStep"
                                v-if="currentStep > 0"
                                class="px-4 py-2 border border-gray-300 rounded hover-bg-gray-50">
                            Previous
                        </button>
                        <div v-else></div>
                        
                        <button @click="nextStep"
                                v-if="currentStep < steps.length - 1"
                                class="px-4 py-2 bg-indigo-600 text-white rounded hover-bg-indigo-700">
                            Next
                        </button>
                    </div>
                </div>
            </div>
        </main>

        <!-- Service Configuration Modal -->
        <div v-if="configuringService" 
             class="modal-backdrop">
            <div class="modal-content">
                <h3 class="text-lg font-medium mb-2">
                    {{ arkToolsModalTitle }}
                </h3>
                <p class="text-sm text-gray-600 mb-4">
                    {{ arkToolsModalDescription }}
                </p>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Choose an option:
                        </label>
                        <div class="space-y-2">
                            <!-- ARK-TOOLS Container Options -->
                            <template v-if="configuringService.service_type === 'ark-tools'">
                                <label class="flex items-start p-3 border rounded-lg cursor-pointer hover-bg-gray-50"
                                       :class="serviceConfigForm.mode === 'use_existing' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'"
                                       v-if="configuringService.source !== 'create_new'">
                                    <input type="radio" v-model="serviceConfigForm.mode" value="use_existing" class="mt-1">
                                    <div class="ml-3">
                                        <div class="font-medium">Use This Container (Recommended)</div>
                                        <div class="text-sm text-gray-600">Run ARK-TOOLS in this existing optimized container</div>
                                    </div>
                                </label>
                                
                                <label class="flex items-start p-3 border rounded-lg cursor-pointer hover-bg-gray-50"
                                       :class="serviceConfigForm.mode === 'create_new' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
                                    <input type="radio" v-model="serviceConfigForm.mode" value="create_new" class="mt-1">
                                    <div class="ml-3">
                                        <div class="font-medium">{{ configuringService.source === 'create_new' ? 'Create New Container' : 'Replace with New Container' }}</div>
                                        <div class="text-sm text-gray-600">Create a fresh Docker container optimized for ARK-TOOLS</div>
                                    </div>
                                </label>
                                
                                <label class="flex items-start p-3 border rounded-lg cursor-pointer hover-bg-gray-50"
                                       :class="serviceConfigForm.mode === 'skip' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
                                    <input type="radio" v-model="serviceConfigForm.mode" value="skip" class="mt-1">
                                    <div class="ml-3">
                                        <div class="font-medium">Run on Host (Advanced)</div>
                                        <div class="text-sm text-gray-600">Run ARK-TOOLS directly on your machine without containerization</div>
                                    </div>
                                </label>
                            </template>
                            
                            <!-- PostgreSQL/Redis Options -->
                            <template v-else>
                                <label class="flex items-start p-3 border rounded-lg cursor-pointer hover-bg-gray-50"
                                       :class="serviceConfigForm.mode === 'use_existing' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
                                    <input type="radio" v-model="serviceConfigForm.mode" value="use_existing" class="mt-1">
                                    <div class="ml-3">
                                        <div class="font-medium">Use This Service (Recommended)</div>
                                        <div class="text-sm text-gray-600">Connect ARK-TOOLS directly to this existing {{ configuringService.service_type }}</div>
                                    </div>
                                </label>
                                
                                <label class="flex items-start p-3 border rounded-lg cursor-pointer hover-bg-gray-50"
                                       :class="serviceConfigForm.mode === 'share_existing' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
                                    <input type="radio" v-model="serviceConfigForm.mode" value="share_existing" class="mt-1">
                                    <div class="ml-3">
                                        <div class="font-medium">Share With Other Apps</div>
                                        <div class="text-sm text-gray-600">Use this service but with separate database/keyspace to avoid conflicts</div>
                                    </div>
                                </label>
                                
                                <label class="flex items-start p-3 border rounded-lg cursor-pointer hover-bg-gray-50"
                                       :class="serviceConfigForm.mode === 'create_new' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
                                    <input type="radio" v-model="serviceConfigForm.mode" value="create_new" class="mt-1">
                                    <div class="ml-3">
                                        <div class="font-medium">Create New Container</div>
                                        <div class="text-sm text-gray-600">Ignore this service and create a fresh Docker container for ARK-TOOLS only</div>
                                    </div>
                                </label>
                                
                                <label class="flex items-start p-3 border rounded-lg cursor-pointer hover-bg-gray-50"
                                       :class="serviceConfigForm.mode === 'skip' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'">
                                    <input type="radio" v-model="serviceConfigForm.mode" value="skip" class="mt-1">
                                    <div class="ml-3">
                                        <div class="font-medium">{{ skipServiceLabel }}</div>
                                        <div class="text-sm text-gray-600">Skip this service ({{ configuringService.service_type === 'postgresql' ? 'will use SQLite fallback' : 'no caching' }})</div>
                                    </div>
                                </label>
                            </template>
                        </div>
                    </div>

                    <div v-if="configuringService.service_type === 'postgresql' && serviceConfigForm.mode !== 'skip'">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Database Name for ARK-TOOLS
                        </label>
                        <input v-model="serviceConfigForm.database_name" 
                               type="text"
                               placeholder="ark_tools"
                               class="w-full border rounded px-3 py-2">
                        <p class="text-xs text-gray-500 mt-1">
                            {{ serviceConfigForm.mode === 'create_new' ? 'Will be created in the new container' : 'Will be created if it doesn\'t exist' }}
                        </p>
                    </div>

                    <div v-if="configuringService.service_type === 'redis' && serviceConfigForm.mode === 'share_existing'">
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Redis Database Number (0-15)
                        </label>
                        <input v-model.number="serviceConfigForm.database_number" 
                               type="number" min="0" max="15"
                               placeholder="2"
                               class="w-full border rounded px-3 py-2">
                        <p class="text-xs text-gray-500 mt-1">
                            Use a different number than your other apps to avoid key conflicts
                        </p>
                    </div>
                </div>

                <div class="mt-6 flex justify-end space-x-3">
                    <button @click="configuringService = null"
                            class="px-4 py-2 border border-gray-300 rounded hover-bg-gray-50">
                        Cancel
                    </button>
                    <button @click="saveServiceConfig"
                            class="px-4 py-2 bg-indigo-600 text-white rounded hover-bg-indigo-700">
                        Save
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const { createApp } = Vue;

        createApp({
            data() {
                return {
                    currentStep: 0,
                    steps: [
                        'Environment Detection',
                        'Service Discovery', 
                        'Configuration',
                        'Review & Save'
                    ],
                    
                    // Environment detection
                    scanning: false,
                    detectedEnvs: [],
                    selectedEnv: null,
                    
                    // Service discovery
                    detectingServices: false,
                    detectedServices: [],
                    
                    // Service configuration
                    serviceConfigs: {},
                    configuringService: null,
                    serviceConfigForm: {
                        mode: 'use_existing',
                        database_name: 'ark_tools',
                        database_number: 2
                    },
                    
                    // Configuration preview
                    configPreview: '',
                    
                    // Testing and saving
                    testing: false,
                    testResults: null,
                    saving: false,
                    saveStatus: null,
                    
                    // System resources
                    systemResources: null,
                    checkingResources: false,
                    
                    // WebSocket
                    ws: null
                };
            },
            
            computed: {
                postgresServices() {
                    return this.detectedServices.filter(s => s.service_type === 'postgresql');
                },
                redisServices() {
                    return this.detectedServices.filter(s => s.service_type === 'redis');
                },
                arkToolsServices() {
                    return this.detectedServices.filter(s => s.service_type === 'ark-tools');
                },
                // Computed properties for strings with apostrophes
                noServicesHintTitle() {
                    return "Don't have PostgreSQL or Redis?";
                },
                arkToolsModalTitle() {
                    if (!this.configuringService) return '';
                    if (this.configuringService.service_type === 'ark-tools') {
                        return 'Configure ARK-TOOLS Execution Container';
                    }
                    return 'How should ARK-TOOLS use ' + this.configuringService.service_type + '?';
                },
                arkToolsModalDescription() {
                    if (!this.configuringService) return '';
                    if (this.configuringService.service_type === 'ark-tools') {
                        if (this.configuringService.source === 'create_new') {
                            return 'Create a new ARK-TOOLS container optimized for your system';
                        }
                        return 'Found ARK-TOOLS container: ' + this.configuringService.container_name;
                    }
                    return 'Found ' + this.configuringService.service_type + ' at ' + this.configuringService.host + ':' + this.configuringService.port;
                },
                createNewServiceTitle() {
                    return "Don't worry! ARK-TOOLS will create this for you.";
                },
                skipServiceTitle() {
                    return "I'll configure this manually later.";
                },
                skipServiceLabel() {
                    if (!this.configuringService) return '';
                    return "Don't Use " + this.configuringService.service_type;
                }
            },
            
            mounted() {
                this.connectWebSocket();
                this.scanEnvironment();
            },
            
            methods: {
                connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                    
                    this.ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        console.log('WebSocket message:', data);
                    };
                },
                
                async scanEnvironment() {
                    this.scanning = true;
                    try {
                        const response = await fetch('/api/detect/environment', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({})
                        });
                        const data = await response.json();
                        this.detectedEnvs = data.environments;
                        
                        // Auto-select parent project
                        if (data.parent_env) {
                            this.selectedEnv = data.parent_env;
                        }
                    } catch (error) {
                        console.error('Failed to scan environment:', error);
                    } finally {
                        this.scanning = false;
                    }
                },
                
                async detectServices() {
                    this.detectingServices = true;
                    try {
                        const response = await fetch('/api/detect/services', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({})
                        });
                        const data = await response.json();
                        this.detectedServices = data.services;
                    } catch (error) {
                        console.error('Failed to detect services:', error);
                    } finally {
                        this.detectingServices = false;
                    }
                },
                
                selectEnvironment(env) {
                    this.selectedEnv = env;
                },
                
                configureService(service) {
                    this.configuringService = service;
                    this.serviceConfigForm = {
                        mode: 'use_existing',
                        database_name: 'ark_tools',
                        database_number: 2
                    };
                },
                
                async saveServiceConfig() {
                    try {
                        const response = await fetch('/api/configure/service', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                service_id: this.configuringService.id || 
                                          `${this.configuringService.service_type}_${this.configuringService.port}`,
                                mode: this.serviceConfigForm.mode,
                                options: this.serviceConfigForm
                            })
                        });
                        const data = await response.json();
                        this.serviceConfigs[this.configuringService.service_type] = data.config;
                        this.configuringService = null;
                        
                        // Update preview
                        await this.updatePreview();
                    } catch (error) {
                        console.error('Failed to configure service:', error);
                    }
                },
                
                async updatePreview() {
                    try {
                        const response = await fetch('/api/preview');
                        const data = await response.json();
                        this.configPreview = data.env_content;
                    } catch (error) {
                        console.error('Failed to update preview:', error);
                    }
                },
                
                async checkSystemResources() {
                    this.checkingResources = true;
                    try {
                        const response = await fetch('/api/check-resources', {
                            method: 'POST'
                        });
                        const data = await response.json();
                        this.systemResources = data.resources;
                    } catch (error) {
                        console.error('Failed to check system resources:', error);
                    } finally {
                        this.checkingResources = false;
                    }
                },
                
                async createArkToolsContainer() {
                    // This will create a new ARK-TOOLS container
                    const newService = {
                        service_type: 'ark-tools',
                        source: 'create_new',
                        host: 'localhost',
                        port: 0,
                        is_running: false,
                        container_name: 'ark_tools_new'
                    };
                    
                    // Set configuration mode to create new
                    this.serviceConfigForm.mode = 'create_new';
                    this.configuringService = newService;
                },
                
                async testConnections() {
                    this.testing = true;
                    this.testResults = null;
                    try {
                        const response = await fetch('/api/test-connections', {
                            method: 'POST'
                        });
                        const data = await response.json();
                        this.testResults = data.results;
                    } catch (error) {
                        console.error('Failed to test connections:', error);
                    } finally {
                        this.testing = false;
                    }
                },
                
                async saveConfiguration() {
                    this.saving = true;
                    this.saveStatus = null;
                    try {
                        const response = await fetch('/api/save', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                output_dir: '.'
                            })
                        });
                        const data = await response.json();
                        this.saveStatus = {
                            success: data.success,
                            message: data.success ? 
                                `Configuration saved! Files: ${data.files.join(', ')}` :
                                'Failed to save configuration'
                        };
                    } catch (error) {
                        console.error('Failed to save configuration:', error);
                        this.saveStatus = {
                            success: false,
                            message: 'Error saving configuration'
                        };
                    } finally {
                        this.saving = false;
                    }
                },
                
                nextStep() {
                    if (this.currentStep < this.steps.length - 1) {
                        this.currentStep++;
                        if (this.currentStep === 1 && this.detectedServices.length === 0) {
                            this.detectServices();
                        }
                        if (this.currentStep === 3) {
                            this.updatePreview();
                        }
                    }
                },
                
                previousStep() {
                    if (this.currentStep > 0) {
                        this.currentStep--;
                    }
                }
            }
        }).mount('#app');
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI"""
    return HTML_TEMPLATE

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    app.state.connected_clients.add(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        app.state.connected_clients.remove(websocket)

@app.post("/api/detect/environment")
async def detect_environment(request: DetectionRequest):
    """Detect environment files"""
    orchestrator = app.state.orchestrator
    environments = await orchestrator.detect_environment_async(request.search_paths)
    parent_env = orchestrator.env_detector.get_parent_project_env()
    
    return {
        "environments": [env.__dict__ for env in environments],
        "parent_env": parent_env.__dict__ if parent_env else None
    }

@app.post("/api/check-resources")
async def check_resources():
    """Check system resources"""
    from ark_tools.setup.system_checker import SystemChecker
    
    checker = SystemChecker()
    resources = checker.check_system_resources()
    
    return {
        "resources": {
            "cpu_count": resources.cpu_count,
            "cpu_percent": resources.cpu_percent,
            "memory_total_gb": resources.memory_total_gb,
            "memory_available_gb": resources.memory_available_gb,
            "memory_percent": resources.memory_percent,
            "disk_total_gb": resources.disk_total_gb,
            "disk_available_gb": resources.disk_available_gb,
            "disk_percent": resources.disk_percent,
            "docker_available": resources.docker_available,
            "docker_running_containers": resources.docker_running_containers,
            "docker_images_size_gb": resources.docker_images_size_gb,
            "docker_containers_size_gb": resources.docker_containers_size_gb,
            "platform": resources.platform,
            "python_version": resources.python_version,
            "can_run_ark_tools": resources.can_run_ark_tools,
            "warnings": resources.warnings,
            "recommendations": resources.recommendations
        }
    }

@app.post("/api/detect/services")
async def detect_services(request: DetectionRequest):
    """Detect available services"""
    orchestrator = app.state.orchestrator
    services = await orchestrator.detect_services_async()
    
    # Convert services to dict format
    services_data = []
    for service in services:
        service_dict = {
            'id': f"{service.service_type}_{service.port}",
            'service_type': service.service_type,
            'source': service.source,
            'host': service.host,
            'port': service.port,
            'container_name': service.container_name,
            'container_id': service.container_id,
            'version': service.version,
            'is_running': service.is_running,
            'compatible': service.compatible,
            'warnings': service.warnings or []
        }
        services_data.append(service_dict)
    
    return {"services": services_data}

@app.post("/api/configure/service")
async def configure_service(request: ServiceConfigRequest):
    """Configure a service"""
    orchestrator = app.state.orchestrator
    
    # Find the service
    service = None
    for s in orchestrator.detected_services:
        service_id = f"{s.service_type}_{s.port}"
        if service_id == request.service_id:
            service = s
            break
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Configure the service
    mode = ServiceMode(request.mode)
    config = orchestrator.configurator.configure_from_detected_service(
        service, mode, **request.options
    )
    
    # Store configuration
    if service.service_type == 'postgresql':
        orchestrator.configurator.config.postgresql = config
    elif service.service_type == 'redis':
        orchestrator.configurator.config.redis = config
    
    return {"config": config.to_dict()}

@app.post("/api/configure/inherit")
async def configure_inheritance(request: InheritanceRequest):
    """Configure credential inheritance"""
    orchestrator = app.state.orchestrator
    
    # Find the environment
    env = None
    for e in orchestrator.detected_envs:
        if e.path == request.env_path:
            env = e
            break
    
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    
    # Inherit configuration
    orchestrator.configurator.inherit_from_env(env, request.keys)
    
    return {"success": True}

@app.get("/api/preview")
async def get_preview():
    """Get configuration preview"""
    orchestrator = app.state.orchestrator
    
    # Generate secrets if needed
    if not orchestrator.configurator.config.ark_secret_key:
        orchestrator.configurator.generate_secrets()
    
    # Detect MAMS
    orchestrator.configurator.detect_mams_path()
    
    # Generate preview
    env_content = orchestrator.configurator.config.to_env_content()
    
    return {
        "env_content": env_content,
        "config": orchestrator.configurator.config.to_dict()
    }

@app.post("/api/test-connections")
async def test_connections():
    """Test service connections"""
    orchestrator = app.state.orchestrator
    results = await orchestrator.test_all_connections()
    
    return {"results": results}

@app.post("/api/save")
async def save_configuration(request: SaveConfigRequest):
    """Save configuration to files"""
    orchestrator = app.state.orchestrator
    
    # Validate configuration
    is_valid, issues = orchestrator.configurator.config.validate_config()
    if not is_valid and issues:
        return {
            "success": False,
            "message": f"Configuration issues: {', '.join(issues)}",
            "issues": issues
        }
    
    # Save configuration
    output_dir = Path(request.output_dir)
    success, files = orchestrator.configurator.config.save(output_dir)
    
    return {
        "success": success,
        "files": files,
        "message": "Configuration saved successfully" if success else "Failed to save configuration"
    }

def find_available_port(start_port: int = 8080, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            # Try to bind to the port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                s.close()
                return port
        except OSError:
            # Port is in use, try next one
            continue
    
    # If no ports available in range, raise error
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts}")

def run_web_ui(host: str = "0.0.0.0", port: int = None):
    """Run the web UI server with automatic port detection."""
    import os
    
    # Check for environment variable first
    if port is None:
        port = int(os.environ.get('ARK_SETUP_PORT', 0))
    
    # If still no port specified, find an available one
    if port == 0 or port is None:
        try:
            port = find_available_port(8080)
            print(f"✅ Found available port: {port}")
        except RuntimeError as e:
            print(f"❌ {e}")
            print("   Try setting ARK_SETUP_PORT environment variable")
            return
    
    print(f"🌐 Starting ARK-TOOLS Web UI at http://localhost:{port}")
    print(f"   Press Ctrl+C to stop the server\n")
    
    try:
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        print("\n👋 Web UI server stopped")