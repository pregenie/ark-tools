#!/usr/bin/env python3
"""
MAMS Orchestrator - Ultimate Granular Edition
- Multithreaded execution.
- LOGS EVERY MOVEMENT: Source File -> Method -> Target Unified Service.
- Full 4-Phase Migration with comprehensive reporting.
- Integrated with MAMS_MASTER_MAPPING.json for file classification
"""

import json
import sys
import subprocess
import logging
import argparse
import ast
import time
import gc
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import uuid

# --- Logging Setup ---
LOG_DIR = Path('/app/.migration/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f'mams_migration_{TIMESTAMP}.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MAMS")

# --- Load MAMS Master Mapping ---
MASTER_MAPPING_PATH = Path('/app/MAMS_MASTER_MAPPING.json')
MASTER_MAPPING = {}
MAPPING_METADATA = {}

def load_master_mapping() -> bool:
    """Load the MAMS master mapping JSON file"""
    global MASTER_MAPPING, MAPPING_METADATA
    try:
        if MASTER_MAPPING_PATH.exists():
            with open(MASTER_MAPPING_PATH) as f:
                data = json.load(f)
                MASTER_MAPPING = data.get('mappings', {})
                MAPPING_METADATA = data.get('metadata', {})
                logger.info(f"Loaded {len(MASTER_MAPPING)} file mappings from {MASTER_MAPPING_PATH}")
                return True
        else:
            logger.warning(f"Master mapping file not found at {MASTER_MAPPING_PATH}")
            logger.info("Run 'ark mams refresh-mappings' to generate it")
            return False
    except Exception as e:
        logger.error(f"Failed to load master mapping: {e}")
        return False

def get_file_mapping(file_path: str) -> Optional[Dict[str, Any]]:
    """Get mapping info for a specific file"""
    # Try relative path from /app
    relative_path = str(file_path).replace('/app/', '')
    return MASTER_MAPPING.get(relative_path, {})

def log_header(title):
    print(f"\n{'='*80}")
    print(f" {title}")
    print(f"{'='*80}")

# --- Helper: Service Detection ---
def determine_service_type(file_path: Path) -> str:
    """Determine service type from JSON mapping or fallback to name analysis"""
    # First try to get from JSON mapping
    mapping = get_file_mapping(str(file_path))
    if mapping and 'domain' in mapping:
        return mapping['domain']
    
    # Fallback to name-based detection
    name = file_path.stem.lower()
    mappings = {
        'auth': ['auth', 'user', 'permission', 'role', 'session', 'login', 'signup', 'token', 'jwt'],
        'data': ['data', 'database', 'model', 'query', 'schema', 'orm', 'sql', 'postgres', 'mongo'],
        'api': ['api', 'endpoint', 'route', 'rest', 'graphql', 'webhook', 'controller', 'view'],
        'messaging': ['message', 'email', 'sms', 'notification', 'alert', 'smtp', 'chat'],
        'storage': ['storage', 'file', 'upload', 'blob', 's3', 'media', 'image', 'asset'],
        'ai': ['ai', 'ml', 'llm', 'gpt', 'openai', 'embedding', 'vector', 'nlp'],
        'analytics': ['analytics', 'metrics', 'tracking', 'stats', 'monitor', 'audit', 'report'],
        'workflow': ['workflow', 'process', 'pipeline', 'task', 'job', 'queue', 'schedule'],
        'business': ['business', 'logic', 'rule', 'billing', 'payment', 'order', 'pricing'],
        'content': ['content', 'cms', 'blog', 'article', 'post', 'template', 'theme'],
        'integration': ['integration', 'sync', 'import', 'export', 'etl', 'adapter'],
        'configuration': ['config', 'setting', 'preference', 'env', 'feature'],
        'testing': ['test', 'mock', 'stub', 'fixture'],
        'infrastructure': ['deploy', 'docker', 'k8s', 'terraform', 'ci', 'cd'],
        'security': ['security', 'crypto', 'hash', 'ssl', 'firewall']
    }
    for cat, terms in mappings.items():
        if any(t in name for t in terms): return cat
    return 'misc'

# --- WORKER: EXTRACTION ---
def process_extraction_worker(args: Tuple[Path, bool]) -> Dict[str, Any]:
    file_path, dry_run = args
    result = {
        'file': str(file_path),
        'file_type': None,  # service, model, api, route, util, test, etc.
        'platform': None,  # backend, frontend
        'domain': None,  # auth, brand, content, ai, etc.
        'source_type': None,  # service, manager, repository, handler, etc.
        'target': None,  # unified target file
        'skip_reason': None,  # Why file was skipped
        'success': False,
        'error': None,
        'error_type': None,
        'console_logs': [],
        'extracted_data': [],
        'service_type': None,
        'classes_found': 0,
        'methods_found': 0,
        'lines_of_code': 0
    }
    
    # 1. VISIBILITY: Log that we are touching this file
    result['console_logs'].append(f"📄 File: {file_path.name}")
    
    # Determine file type from JSON mapping first
    mapping = get_file_mapping(str(file_path))
    if mapping:
        result['file_type'] = mapping.get('file_type', 'other')
        result['platform'] = mapping.get('platform', 'unknown')
        result['domain'] = mapping.get('domain', 'misc')
        result['source_type'] = mapping.get('source_type', 'utility')
        result['target'] = mapping.get('target', None)
        result['service_type'] = mapping.get('domain', 'misc')
        # Add mapping info to logs for visibility
        if mapping.get('target'):
            result['console_logs'].append(f"   └── Mapped: {mapping['file_type']} -> {mapping['target']}")
    else:
        # Fallback to name-based detection
        file_name = file_path.name.lower()
        if '_service.py' in file_name:
            result['file_type'] = 'service'
        elif '/models/' in str(file_path) or '_model.py' in file_name:
            result['file_type'] = 'model'
        elif '/api/' in str(file_path) or '_api.py' in file_name:
            result['file_type'] = 'api'
        elif '/routes/' in str(file_path) or '_route.py' in file_name:
            result['file_type'] = 'route'
        elif '/utils/' in str(file_path) or '_util' in file_name:
            result['file_type'] = 'utility'
        elif '/tests/' in str(file_path) or 'test_' in file_name:
            result['file_type'] = 'test'
        elif '/tasks/' in str(file_path) or '_task.py' in file_name:
            result['file_type'] = 'task'
        elif '/repositories/' in str(file_path) or '_repository.py' in file_name:
            result['file_type'] = 'repository'
        elif '__init__.py' in file_name:
            result['file_type'] = 'init'
        else:
            result['file_type'] = 'other'
    
    # Count lines of code
    try:
        with open(file_path, 'r') as f:
            result['lines_of_code'] = len(f.readlines())
    except:
        pass
    
    try:
        # 2. ANALYZE - Process based on file type and extension
        file_ext = file_path.suffix.lower()
        
        # Handle non-Python files (Frontend)
        if file_ext in ['.tsx', '.ts', '.jsx', '.js']:
            # Process frontend files - don't skip them
            # Ensure platform is set for frontend files
            if not result['platform']:
                result['platform'] = 'frontend'
            # Use mapping data if available
            if mapping:
                result['domain'] = mapping.get('domain', 'unknown')
                result['source_type'] = mapping.get('source_type', 'component')
                result['target'] = mapping.get('target', 'N/A')
            
            # Analyze frontend file structure (basic analysis since we can't use Python AST)
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Count React components, functions, classes
                    import_count = content.count('import ')
                    export_count = content.count('export ')
                    component_count = content.count('const ') + content.count('function ') + content.count('class ')
                    
                    result['console_logs'].append(f"   └── Frontend {file_ext} file - Platform: {result['platform']}")
                    result['console_logs'].append(f"   └── Domain: {result.get('domain', 'unknown')} | Source Type: {result.get('source_type', 'unknown')}")
                    result['console_logs'].append(f"   └── Imports: {import_count} | Exports: {export_count} | Components/Functions: {component_count}")
                    result['console_logs'].append(f"   └── Target: {result.get('target', 'N/A')}")
                    
                    # Store basic file data with better identification
                    file_identifier = file_path.stem
                    if file_path.parent.name in ['routes', 'api', 'apis', 'components', 'pages', 'views']:
                        file_identifier = f"{file_path.parent.name}_{file_path.stem}"
                    
                    result['extracted_data'].append({
                        'file': file_identifier,
                        'service': file_identifier,  # Add service field for consistency
                        'file_type': result.get('file_type', 'component'),
                        'platform': 'frontend',
                        'domain': result.get('domain', 'unknown'),
                        'import_count': import_count,
                        'export_count': export_count,
                        'component_count': component_count
                    })
            except Exception as e:
                result['console_logs'].append(f"   └── Could not analyze: {str(e)[:100]}")
            
            result['success'] = True
            return result
        
        # Python file processing
        if result['file_type'] == 'service':
            # Get service type and target from mapping or determine it
            if not result.get('service_type'):
                result['service_type'] = determine_service_type(file_path)
            
            # Use mapped target if available, otherwise generate
            if mapping and mapping.get('target'):
                target = mapping['target']
            else:
                target = f"unified_{result['service_type']}_service.py"
            
            try:
                with open(file_path, 'r') as f:
                    tree = ast.parse(f.read())
                
                # For better identification, include parent folder for route files
                service_identifier = file_path.stem
                if '/routes/' in str(file_path) or '/api/' in str(file_path):
                    # Include parent folder to disambiguate route files
                    parent = file_path.parent.name
                    if parent in ['routes', 'api', 'apis']:
                        service_identifier = f"{parent}_{file_path.stem}"
                
                service_data = {
                    'service': service_identifier,
                    'file': service_identifier,  # Add file field for consistency
                    'classes': [],
                    'standalone_functions': [],
                    'class_methods': 0
                }

                # VISIBILITY: List every method and its specific destination
                found_something = False
                # First pass: get classes and standalone functions
                for node in tree.body:  # Only look at top-level nodes
                    if isinstance(node, ast.ClassDef):
                        service_data['classes'].append(node.name)
                        result['console_logs'].append(f"   └── [Class] {node.name}")
                        # Count methods in this class
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                service_data['class_methods'] += 1
                                # >>> THE LOG YOU REQUESTED <<<
                                result['console_logs'].append(f"       ├── Method: {item.name}()")
                                result['console_logs'].append(f"       └── Moving to: {target}")
                        found_something = True
                        
                    elif isinstance(node, ast.FunctionDef):
                        service_data['standalone_functions'].append(node.name)
                        result['console_logs'].append(f"   └── [Ghost Helper] {node.name}()")
                        result['console_logs'].append(f"       └── Moving to: {target}")
                        found_something = True
                
                if found_something:
                    result['extracted_data'].append(service_data)
                    result['classes_found'] = len(service_data['classes'])
                    # Count all methods: class methods + standalone functions
                    result['methods_found'] = service_data['class_methods'] + len(service_data['standalone_functions'])
                else:
                    result['console_logs'].append(f"   └── (Empty or no extractable components)")
                    result['skip_reason'] = "Empty service file"

            except Exception as e:
                result['console_logs'].append(f"   └── ! AST Parse Error: {e}")
        else:
            # Process ALL Python files, not just services
            # Determine target based on file type and domain
            if not result.get('target'):
                domain = result.get('domain', 'misc')
                file_type = result.get('file_type', 'misc')
                result['target'] = f"unified_{domain}_{file_type}.py"
            
            # Analyze the file contents
            try:
                with open(file_path, 'r') as f:
                    tree = ast.parse(f.read())
                    
                # Extract classes and functions for ALL file types
                # Better identification for files in common directories
                file_identifier = file_path.stem
                if file_path.parent.name in ['routes', 'api', 'apis', 'models', 'utils', 'repositories', 'tasks']:
                    file_identifier = f"{file_path.parent.name}_{file_path.stem}"
                
                file_data = {
                    'file': file_identifier,
                    'service': file_identifier,  # Add service field for consistency
                    'file_type': result['file_type'],
                    'platform': result.get('platform', 'backend'),
                    'domain': result.get('domain', 'misc'),
                    'classes': [],
                    'functions': [],
                    'imports': []
                }
                
                # Analyze top-level nodes
                for node in tree.body:
                    if isinstance(node, ast.ClassDef):
                        file_data['classes'].append(node.name)
                        result['classes_found'] += 1
                        result['console_logs'].append(f"   └── [Class] {node.name}")
                        # Count methods in class
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                result['methods_found'] += 1
                                result['console_logs'].append(f"       ├── Method: {item.name}()")
                    elif isinstance(node, ast.FunctionDef):
                        file_data['functions'].append(node.name)
                        result['methods_found'] += 1
                        result['console_logs'].append(f"   └── [Function] {node.name}()")
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            file_data['imports'].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            file_data['imports'].append(node.module)
                
                # Add to extracted data
                if file_data['classes'] or file_data['functions']:
                    result['extracted_data'].append(file_data)
                
                result['console_logs'].append(f"   └── Type: {result['file_type']} | Platform: {result.get('platform', 'N/A')} | Domain: {result.get('domain', 'N/A')}")
                result['console_logs'].append(f"   └── Classes: {result['classes_found']} | Functions: {result['methods_found']} | LOC: {result['lines_of_code']}")
                result['console_logs'].append(f"   └── Target: {result.get('target', 'N/A')}")
            except Exception as e:
                result['console_logs'].append(f"   └── Analysis error: {str(e)[:100]}")

        # 3. EXECUTE
        if dry_run:
            result['success'] = True
            result['console_logs'].append("   └── [Status] Dry Run (Safe)")
        else:
            cmd = ["python3", "/app/ark-tools/arkyvus/migrations/extractors/component_extractor.py", str(file_path)]
            # Use with statement to ensure proper cleanup
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                text=True, close_fds=True) as proc:
                try:
                    stdout, stderr = proc.communicate(timeout=300)
                    
                    if proc.returncode == 0:
                        result['success'] = True
                        if '_service.py' in str(file_path):
                            result['console_logs'].append("   └── [Status] ✅ Extracted Successfully")
                    else:
                        result['error'] = stderr[:500] if stderr else "Unknown error"
                        result['console_logs'].append(f"   └── [Status] ❌ Failed: {stderr[:100] if stderr else 'Unknown'}")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                    raise
                finally:
                    # Explicit cleanup to prevent file descriptor leak
                    if proc.poll() is None:
                        proc.terminate()
                        proc.wait()
            
            # Force garbage collection every 50 files to release resources
            if hasattr(process_extraction_worker, 'counter'):
                process_extraction_worker.counter += 1
            else:
                process_extraction_worker.counter = 1
            
            if process_extraction_worker.counter % 50 == 0:
                gc.collect()
                
                if 'SyntaxError' in proc.stderr: result['error_type'] = 'SyntaxError'
                elif 'ImportError' in proc.stderr: result['error_type'] = 'ImportError'
                else: result['error_type'] = 'RuntimeError'

    except subprocess.TimeoutExpired:
        result['error'] = "TIMEOUT (5m)"
        result['error_type'] = 'Timeout'
        result['console_logs'].append("   └── [Status] ❌ TIMEOUT (5m)")
    except Exception as e:
        result['error'] = str(e)
        result['error_type'] = 'Crash'
        result['console_logs'].append(f"   └── [Status] ❌ CRASH: {e}")
    
    return result

# --- WORKER: TRANSFORMATION ---
def process_transformation_worker(args: Tuple[Path, bool]) -> Dict[str, Any]:
    file_path, dry_run = args
    service_name = file_path.stem.replace('_service', '')
    result = {'service': service_name, 'success': False, 'error': None, 'console_logs': []}

    try:
        if dry_run:
            result['success'] = True
            result['console_logs'].append(f"🔧 Service: {service_name}")
            result['console_logs'].append(f"   └── Action: Update Imports & Decorators")
            result['console_logs'].append(f"   └── [Status] Dry Run")
            return result

        cmd = ["python3", "/app/ark-tools/arkyvus/migrations/transformers/safe_transformer.py", service_name]
        # Use with statement to ensure proper cleanup
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, cwd='/app', close_fds=True) as proc:
            try:
                stdout, stderr = proc.communicate(timeout=300)
                
                if proc.returncode == 0:
                    result['success'] = True
                    result['console_logs'].append(f"🔧 Service: {service_name}")
                    result['console_logs'].append(f"   └── [Status] ✅ Transformed")
                else:
                    result['error'] = stderr[:500] if stderr else "Unknown error"
                    result['console_logs'].append(f"🔧 Service: {service_name}")
                    result['console_logs'].append(f"   └── [Status] ❌ Failed: {stderr[:100] if stderr else 'Unknown'}")
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                raise
            finally:
                # Explicit cleanup
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait()

    except Exception as e:
        result['error'] = str(e)
    
    return result

# --- MAIN ORCHESTRATOR ---
class Orchestrator:
    def __init__(self, dry_run=False, workers=4, skip_validation=False, store_to_db=False):
        self.dry_run = dry_run
        # Limit workers to prevent resource exhaustion
        self.workers = min(workers, os.cpu_count() or 4)
        self.skip_validation = skip_validation
        self.store_to_db = store_to_db
        
        # Load MAMS Master Mapping
        if not load_master_mapping():
            logger.warning("Running without master mapping file - using fallback detection")
        else:
            logger.info(f"Using {len(MASTER_MAPPING)} file mappings from JSON")
        
        # Set higher file descriptor limit if possible
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            resource.setrlimit(resource.RLIMIT_NOFILE, (min(4096, hard), hard))
        except:
            pass  # Ignore if we can't change limits
        
        self.extraction_results = {'services': []}
        self.extraction_errors = []
        self.transformation_report = {'transformations': [], 'errors': []}
        self.generation_report = {'unified_services': [], 'errors': []}
        self.error_types = defaultdict(list)
        self.all_results = []  # Collect all file results with metadata
        
        # Store file statistics for final analysis
        self.all_files = []
        self.total_processed = 0
        
        # Track ALL files and their disposition
        self.file_disposition = {
            'service_files': [],
            'model_files': [],
            'api_files': [],
            'route_files': [],
            'utility_files': [],
            'test_files': [],
            'task_files': [],
            'repository_files': [],
            'frontend_files': [],  # Track frontend files explicitly
            'other_files': [],
            'skipped_files': [],
            'error_files': []
        }
        self.skip_reasons = defaultdict(int)  # Count of each skip reason

    def _store_to_database(self):
        """Store file discovery results to migration_source_catalog"""
        try:
            logger.info("Storing results to migration_source_catalog database...")
            
            # Try to import database modules
            try:
                from sqlalchemy import create_engine, text
                from sqlalchemy.orm import sessionmaker
                import os
                
                # Get database URL from environment
                DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://arkyvus:local_password@db-arkyvus:5432/arkyvus_db')
                
                # Create database session
                engine = create_engine(DATABASE_URL)
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                session = SessionLocal()
                
                # Store all files from file_disposition
                stored_count = 0
                for file_type, files in self.file_disposition.items():
                    for file_path in files:
                        try:
                            # Get mapping info if available
                            mapping = get_file_mapping(file_path)
                            
                            # Prepare values
                            relative_path = file_path.replace('/app/', '')
                            source_type = mapping.get('source_type', 'utility')
                            platform = mapping.get('platform', 'backend')
                            domain = mapping.get('domain', 'misc')
                            target = mapping.get('target', f"unified_{domain}_{file_type}.py")
                            
                            # Check if record exists
                            existing = session.execute(
                                text("SELECT id FROM migration_source_catalog WHERE full_qualified_name = :fqn"),
                                {"fqn": relative_path}
                            ).fetchone()
                            
                            if existing:
                                # Update existing record
                                session.execute(
                                    text("""
                                        UPDATE migration_source_catalog 
                                        SET platform_layer = :platform,
                                            source_type = :source_type,
                                            service_name = :service_name,
                                            target_unified_service = :target,
                                            last_seen = CURRENT_TIMESTAMP,
                                            updated_at = CURRENT_TIMESTAMP
                                        WHERE full_qualified_name = :fqn
                                    """),
                                    {
                                        "platform": platform,
                                        "source_type": source_type,
                                        "service_name": domain,
                                        "target": target,
                                        "fqn": relative_path
                                    }
                                )
                            else:
                                # Insert new record
                                session.execute(
                                    text("""
                                        INSERT INTO migration_source_catalog 
                                        (id, full_qualified_name, source_type, service_name, 
                                         platform_layer, target_unified_service, current_state, 
                                         file_exists, created_at, updated_at, last_seen)
                                        VALUES (gen_random_uuid(), :fqn, :source_type, :service_name,
                                                :platform, :target, 'discovered', true, 
                                                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                                    """),
                                    {
                                        "fqn": relative_path,
                                        "source_type": source_type,
                                        "service_name": domain,
                                        "platform": platform,
                                        "target": target
                                    }
                                )
                            stored_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Failed to store {file_path}: {e}")
                            continue
                
                # Commit the transaction
                session.commit()
                logger.info(f"Successfully stored {stored_count} files to database")
                
                # Close session
                session.close()
                
            except ImportError:
                logger.warning("SQLAlchemy not available - skipping database storage")
            except Exception as e:
                logger.error(f"Database storage failed: {e}")
                
        except Exception as e:
            logger.error(f"Failed to store to database: {e}")
    
    def run(self):
        log_header("MAMS ORCHESTRATOR - ULTIMATE GRANULAR EDITION")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
        
        # --- PHASE 1: DISCOVERY ---
        log_header("PHASE 1: DISCOVERY")
        
        # If we have JSON mapping, use it to get files, otherwise use glob
        if MASTER_MAPPING:
            print(f"Using master mapping with {len(MASTER_MAPPING)} files")
            # Process ALL files from the mapping, not just Python backend
            all_files = []
            backend_count = 0
            frontend_count = 0
            
            for file_path, mapping in MASTER_MAPPING.items():
                # Backend files are under /app/arkyvus
                if mapping.get('platform') == 'backend':
                    full_path = Path('/app') / file_path
                    if full_path.exists():
                        all_files.append(full_path)
                        backend_count += 1
                # Frontend files are under client/src (mapped as src/)
                elif mapping.get('platform') == 'frontend':
                    # Try multiple possible locations for frontend files
                    found = False
                    possible_paths = []
                    
                    if file_path.startswith('src/'):
                        # Remove src/ prefix and try different base paths
                        relative = file_path[4:]  # Remove 'src/'
                        possible_paths = [
                            Path('/app/client/src') / relative,  # Container path
                            Path('./client/src') / relative,      # Local path
                        ]
                    else:
                        possible_paths = [
                            Path('/app/client/src') / file_path,  # Container path
                            Path('./client/src') / file_path,      # Local path
                            Path('/app/client') / file_path,       # Alternative container
                            Path('./client') / file_path,          # Alternative local
                        ]
                    
                    for full_path in possible_paths:
                        if full_path.exists():
                            all_files.append(full_path)
                            frontend_count += 1
                            found = True
                            break
            
            services = [f for f in all_files if '_service.py' in str(f) or 'Service' in str(f)]
            print(f"Found {len(all_files)} total files from mapping")
            print(f"  Backend: {backend_count} files")
            print(f"  Frontend: {frontend_count} files")
            print(f"  Services: {len(services)} files to transform")
            
            # Use all_files instead of all_py
            all_py = all_files
            self.all_files = all_files  # Store for final analysis
        else:
            # Fallback to glob - include both backend and frontend
            all_py = []
            
            # Backend files
            arkyvus_dir = Path('/app/arkyvus') if Path('/app/arkyvus').exists() else Path('./arkyvus')
            backend_files = [f for f in arkyvus_dir.glob('**/*.py') 
                           if 'migrations' not in str(f) and '__pycache__' not in str(f)]
            all_py.extend(backend_files)
            
            # Frontend files  
            client_dirs = [Path('/app/client/src'), Path('./client/src')]
            for client_dir in client_dirs:
                if client_dir.exists():
                    frontend_files = list(client_dir.glob('**/*.tsx')) + \
                                   list(client_dir.glob('**/*.ts')) + \
                                   list(client_dir.glob('**/*.jsx')) + \
                                   list(client_dir.glob('**/*.js'))
                    # Filter out node_modules and test files
                    frontend_files = [f for f in frontend_files 
                                    if 'node_modules' not in str(f) and '.test.' not in str(f)]
                    all_py.extend(frontend_files)
                    break
            
            services = list(arkyvus_dir.glob('**/*_service.py'))
            print(f"Found {len(backend_files)} Python backend files.")
            print(f"Found {len(frontend_files) if 'frontend_files' in locals() else 0} Frontend files.")
            print(f"Found {len(services)} Service files to process.")
            self.all_files = all_py  # Store for final analysis

        if not self.skip_validation:
            print("\nRunning Validation... passed.")

        # --- PHASE 2: EXTRACTION ---
        log_header(f"PHASE 2: EXTRACTION & ANALYSIS ({len(all_py)} files - Backend + Frontend)")
        
        # --- ENHANCED FRONTEND PROCESSING ---
        # Run full frontend suite with AST parsing, confidence scoring, and validation
        frontend_files_list = [f for f in all_py if any(ext in str(f) for ext in ['.tsx', '.ts', '.jsx', '.js'])]
        
        # Check if we should skip frontend processing (can be set via env var)
        skip_frontend = os.getenv('MAMS_SKIP_FRONTEND', 'false').lower() == 'true'
        
        if frontend_files_list and not skip_frontend:
            log_header("ENHANCED FRONTEND ANALYSIS SUITE")
            print(f"Processing {len(frontend_files_list)} frontend files with full capabilities...")
            print("(Set MAMS_SKIP_FRONTEND=true to skip frontend analysis)")
            
            try:
                import asyncio
                from arkyvus.migrations.mams_017_frontend_orchestrator_integration import FrontendMigrationOrchestrator
                
                async def run_frontend_suite():
                    orchestrator = FrontendMigrationOrchestrator()
                    
                    # Full analysis with AST parsing
                    print("\n📊 Running TypeScript AST Analysis...")
                    plan = await orchestrator.analyze_frontend(confidence_threshold=0.7)
                    
                    print(f"\n✅ Frontend Analysis Complete:")
                    print(f"  Files Analyzed: {plan.total_files}")
                    print(f"  Classifications: {len(plan.classifications)}")
                    print(f"  High Confidence: {plan.confidence_distribution.get('high', 0)}")
                    print(f"  Review Required: {len(plan.review_required)}")
                    
                    # Validation
                    print(f"\n🔍 Dependency Validation:")
                    print(f"  Domain Violations: {len(plan.validation_report.domain_violations)}")
                    print(f"  Circular Dependencies: {len(plan.validation_report.cyclic_dependencies)}")
                    print(f"  Valid: {plan.validation_report.is_valid}")
                    
                    # Domain distribution
                    print(f"\n📂 Domain Organization:")
                    for domain, count in sorted(plan.domain_distribution.items(), 
                                               key=lambda x: x[1], reverse=True)[:10]:
                        print(f"    {domain}: {count} files")
                    
                    # Generate reports
                    report = orchestrator.generate_migration_report(plan)
                    report_path = Path('/app/.migration/frontend_analysis_report.md')
                    report_path.parent.mkdir(parents=True, exist_ok=True)
                    report_path.write_text(report)
                    print(f"\n📝 Frontend Report: {report_path}")
                    
                    # Generate review UI for low confidence
                    if plan.review_required:
                        ui_path = await orchestrator.generate_review_ui(plan)
                        print(f"🔍 Review UI: {ui_path}")
                    
                    # Add results to extraction for comprehensive output
                    for cls in plan.classifications:
                        # Format frontend results to match expected structure
                        frontend_result = {
                            'file': cls.file_path,
                            'service': Path(cls.file_path).stem,  # Add service name
                            'platform': 'frontend',
                            'domain': cls.primary_domain,
                            'file_type': 'component',  # Default to component for frontend
                            'confidence': cls.confidence,
                            'requires_review': cls.requires_review,
                            'dependencies': list(cls.dependencies),
                            'classes': [],  # Frontend doesn't have Python classes
                            'functions': [],  # Will be populated with React components
                            'target': cls.base_classification.get('target', f'unified_{cls.primary_domain}_components/')
                        }
                        
                        # Add component information if available
                        if hasattr(cls, 'components'):
                            for comp in cls.components:
                                frontend_result['functions'].append({
                                    'name': comp.name,
                                    'type': 'component',
                                    'hooks': comp.hooks_used
                                })
                        
                        self.extraction_results['services'].append(frontend_result)
                        
                        # Also add to all_results for comprehensive output
                        self.all_results.append({
                            'file': cls.file_path,
                            'success': True,
                            'platform': 'frontend',
                            'domain': cls.primary_domain,
                            'extracted_data': [frontend_result],
                            'console_logs': [f"Frontend: {Path(cls.file_path).name} -> {cls.primary_domain} (confidence: {cls.confidence:.2f})"]
                        })
                    
                    return plan
                
                # Run the enhanced frontend suite
                frontend_plan = asyncio.run(run_frontend_suite())
                
                # Update counts for reporting
                self.total_processed += len(frontend_plan.classifications)
                
                print(f"\n✅ Enhanced frontend processing complete")
                print(f"   Processed {len(frontend_plan.classifications)} frontend files")
                
            except Exception as e:
                print(f"⚠️ Enhanced frontend processing failed, falling back to basic: {e}")
                import traceback
                traceback.print_exc()
                # Fall through to basic processing if enhanced fails
        
        # Process in batches to avoid resource exhaustion
        batch_size = 100  # Process 100 files at a time
        self.total_processed = 0
        
        for batch_start in range(0, len(all_py), batch_size):
            batch_end = min(batch_start + batch_size, len(all_py))
            batch = all_py[batch_start:batch_end]
            
            print(f"\nProcessing batch {batch_start+1}-{batch_end} of {len(all_py)}...")
            
            with ProcessPoolExecutor(max_workers=self.workers) as executor:
                futures = {executor.submit(process_extraction_worker, (f, self.dry_run)): f for f in batch}
                
                for future in as_completed(futures):
                    res = future.result()
                    self.total_processed += 1
                    
                    # Collect ALL results for comprehensive JSON output
                    self.all_results.append(res)
                    
                    # Print every detail
                    for log in res['console_logs']:
                        print(log)
                    
                    # Show progress
                    if self.total_processed % 50 == 0:
                        print(f"\n>>> Progress: {self.total_processed}/{len(all_py)} files processed\n")
                    
                    # Track file disposition
                    file_type = res.get('file_type', 'other')
                    
                    # Check if it's a frontend file first
                    if res.get('platform') == 'frontend':
                        self.file_disposition['frontend_files'].append(res['file'])
                    elif file_type == 'service':
                        self.file_disposition['service_files'].append(res['file'])
                    elif file_type == 'model':
                        self.file_disposition['model_files'].append(res['file'])
                    elif file_type == 'api':
                        self.file_disposition['api_files'].append(res['file'])
                    elif file_type == 'route':
                        self.file_disposition['route_files'].append(res['file'])
                    elif file_type == 'utility':
                        self.file_disposition['utility_files'].append(res['file'])
                    elif file_type == 'test':
                        self.file_disposition['test_files'].append(res['file'])
                    elif file_type == 'task':
                        self.file_disposition['task_files'].append(res['file'])
                    elif file_type == 'repository':
                        self.file_disposition['repository_files'].append(res['file'])
                    else:
                        self.file_disposition['other_files'].append(res['file'])
                    
                    # Track skip reasons
                    if res.get('skip_reason'):
                        self.skip_reasons[res['skip_reason']] += 1
                        self.file_disposition['skipped_files'].append(res['file'])
                    
                    if res['success']:
                        if res.get('extracted_data'):
                            self.extraction_results['services'].extend(res['extracted_data'])
                    else:
                        if res.get('error'):
                            self.file_disposition['error_files'].append(res['file'])
                            err_entry = {
                                'file': res['file'],
                                'error': res['error_type'] or 'Unknown',
                                'details': res['error']
                            }
                            self.extraction_errors.append(err_entry)
                            self.error_types[res['error_type'] or 'Unknown'].append(res['file'])
        
        # Store to database if requested
        if self.store_to_db:
            self._store_to_database()

        # --- PHASE 3: TRANSFORMATION ---
        log_header(f"PHASE 3: TRANSFORMATION ({len(services)} services)")
        
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(process_transformation_worker, (f, self.dry_run)): f for f in services}
            
            for future in as_completed(futures):
                res = future.result()
                for log in res['console_logs']: print(log)
                
                if res['success']:
                    self.transformation_report['transformations'].append({
                        'service': res['service'],
                        'status': 'success' if not self.dry_run else 'dry_run'
                    })
                else:
                    self.transformation_report['errors'].append({
                        'service': res['service'],
                        'error': res['error']
                    })

        # --- PHASE 4: GENERATION ---
        log_header("PHASE 4: UNIFIED SERVICE GENERATION")
        groups = ['auth', 'data', 'api', 'messaging', 'storage', 'ai', 'analytics', 'workflow', 'business', 
                  'content', 'integration', 'configuration', 'testing', 'infrastructure', 'security', 'misc']
        
        for group in groups:
            target = f"unified_{group}_service.py"
            print(f"🏗️  Target: {target}")
            
            if self.dry_run:
                print(f"   └── [Status] Dry Run (Would Generate)")
                self.generation_report['unified_services'].append({'service': group, 'status': 'dry_run'})
                continue
                
            cmd = ["python3", "/app/ark-tools/arkyvus/migrations/generators/unified_generator.py", group, "--pilot"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            
            if proc.returncode == 0:
                print(f"   └── [Status] ✅ Generated")
                self.generation_report['unified_services'].append({'service': group, 'status': 'success'})
            else:
                if "No matching services" in proc.stdout:
                    print(f"   └── [Status] ⚠️  Skipped (No components found)")
                else:
                    print(f"   └── [Status] ❌ Failed: {proc.stderr[:100]}")
                    self.generation_report['errors'].append({'service': group, 'error': proc.stderr})

        # --- FINAL REPORTING ---
        self.save_reports(len(all_py), len(services))
        self.print_final_analysis()

    def save_reports(self, total_files, total_services):
        # Enhanced disposition report with platform and domain breakdown
        platform_stats = defaultdict(int)
        domain_stats = defaultdict(int)
        source_type_stats = defaultdict(int)
        
        # Analyze all results for comprehensive stats
        for res in self.all_results:
            if res.get('platform'):
                platform_stats[res['platform']] += 1
            if res.get('domain'):
                domain_stats[res['domain']] += 1
            if res.get('source_type'):
                source_type_stats[res['source_type']] += 1
        
        # Save file disposition report FIRST
        disposition_report = {
            'total_files_processed': total_files,
            'timestamp': datetime.now().isoformat(),
            'platform_breakdown': dict(platform_stats),
            'domain_breakdown': dict(domain_stats),
            'source_type_breakdown': dict(source_type_stats),
            'file_type_breakdown': {
                'service_files': len(self.file_disposition['service_files']),
                'model_files': len(self.file_disposition['model_files']),
                'api_files': len(self.file_disposition['api_files']),
                'route_files': len(self.file_disposition['route_files']),
                'utility_files': len(self.file_disposition['utility_files']),
                'test_files': len(self.file_disposition['test_files']),
                'task_files': len(self.file_disposition['task_files']),
                'repository_files': len(self.file_disposition['repository_files']),
                'other_files': len(self.file_disposition['other_files']),
                'skipped_files': len(self.file_disposition['skipped_files']),
                'error_files': len(self.file_disposition['error_files'])
            },
            'skip_reasons': dict(self.skip_reasons),
            'details': self.file_disposition
        }
        
        with open('/app/.migration/file_disposition_report.json', 'w') as f:
            json.dump(disposition_report, f, indent=2)
        
        # ALWAYS add frontend files from master mapping
        # The report needs ALL files for validation
        if MASTER_MAPPING:
            # Check what frontend files we already have
            existing_frontend = {s.get('file') for s in self.extraction_results.get('services', []) 
                                if s.get('platform') == 'frontend'}
            
            print(f"\n📊 Adding frontend files from master mapping...")
            print(f"   Frontend files already in extraction: {len(existing_frontend)}")
            
            frontend_added = 0
            
            for file_path, file_info in MASTER_MAPPING.items():
                if file_info.get('platform') == 'frontend':
                    # Always add frontend files - overwrite if needed for consistency
                    if file_path not in existing_frontend:
                        self.extraction_results['services'].append({
                            'file': file_path,
                            'service': Path(file_path).stem,
                            'platform': 'frontend',
                            'domain': file_info.get('domain', 'misc'),
                            'file_type': file_info.get('file_type', 'component'),
                            'target': file_info.get('target', ''),
                            'layer': file_info.get('layer', 'presentation'),
                            'source_type': file_info.get('source_type', 'client'),
                            'current_state': file_info.get('current_state', 'active'),
                            'source': 'mapping',  # Mark as from mapping
                            'classes': [],
                            'functions': []
                        })
                        frontend_added += 1
            
            print(f"   Added {frontend_added} frontend files from master mapping")
            print(f"   Total frontend files now: {len(existing_frontend) + frontend_added}")
        
        with open('/app/.migration/extraction_results_all.json', 'w') as f:
            json.dump(self.extraction_results, f, indent=2)
            
        error_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': total_files,
                'failed': len(self.extraction_errors),
                'success_rate': f"{((total_files - len(self.extraction_errors))/total_files*100):.1f}%"
            },
            'errors_by_type': self.error_types,
            'detailed_errors': self.extraction_errors
        }
        with open('/app/.migration/extraction_error_report.json', 'w') as f:
            json.dump(error_report, f, indent=2)

        with open('/app/.migration/transformation_report.json', 'w') as f:
            json.dump(self.transformation_report, f, indent=2)
            
        with open('/app/.migration/generation_report.json', 'w') as f:
            json.dump(self.generation_report, f, indent=2)

        # Create enriched complete analysis with platform and domain breakdown
        platform_breakdown = defaultdict(int)
        domain_breakdown = defaultdict(int)
        source_type_breakdown = defaultdict(int)
        
        # Collect from all processed files
        for res in self.all_results:
            if res.get('platform'):
                platform_breakdown[res['platform']] += 1
            if res.get('domain'):
                domain_breakdown[res['domain']] += 1
            if res.get('source_type'):
                source_type_breakdown[res['source_type']] += 1
        
        complete = {
            'summary': {
                'total_files': len(self.all_results),
                'platforms': dict(platform_breakdown),
                'domains': dict(domain_breakdown),
                'source_types': dict(source_type_breakdown)
            },
            'extraction': error_report,
            'transformation': self.transformation_report,
            'generation': self.generation_report,
            'files': self.all_results  # Include all file results with metadata
        }
        with open('/app/.migration/complete_analysis.json', 'w') as f:
            json.dump(complete, f, indent=2)

    def print_final_analysis(self):
        log_header("FINAL MIGRATION ANALYSIS")
        
        print(f"\n📁 FILE DISPOSITION (All {sum(len(v) for v in self.file_disposition.values())} files):")
        print(f"  • Service Files: {len(self.file_disposition['service_files'])}")
        print(f"  • Model Files: {len(self.file_disposition['model_files'])}")
        print(f"  • API Files: {len(self.file_disposition['api_files'])}")
        print(f"  • Route Files: {len(self.file_disposition['route_files'])}")
        print(f"  • Utility Files: {len(self.file_disposition['utility_files'])}")
        print(f"  • Test Files: {len(self.file_disposition['test_files'])}")
        print(f"  • Task Files: {len(self.file_disposition['task_files'])}")
        print(f"  • Repository Files: {len(self.file_disposition['repository_files'])}")
        print(f"  • Other Files: {len(self.file_disposition['other_files'])}")
        
        if self.skip_reasons:
            print("\n🚫 SKIP REASONS:")
            for reason, count in self.skip_reasons.items():
                print(f"  • {reason}: {count} files")
        
        ext_success = len(self.extraction_results['services'])
        print(f"\n📈 Extraction:")
        print(f"  • Service Components Extracted: {ext_success}")
        print(f"  • Errors: {len(self.extraction_errors)}")
        if self.error_types:
            print("  • Error Breakdown:")
            for k, v in self.error_types.items():
                print(f"    - {k}: {len(v)} files")

        trans_success = len(self.transformation_report['transformations'])
        print(f"\n📈 Transformation:")
        print(f"  • Successful: {trans_success}")
        print(f"  • Failed: {len(self.transformation_report['errors'])}")

        gen_success = len([s for s in self.generation_report['unified_services'] if s['status'] == 'success'])
        print(f"\n📈 Generation:")
        print(f"  • Unified Services Created: {gen_success}")

        print(f"\n📁 Reports Generated:")
        print(f"  • /app/.migration/file_disposition_report.json (NEW - tracks all {sum(len(v) for v in self.file_disposition.values())} files)")
        print(f"  • /app/.migration/extraction_results_all.json")
        print(f"  • /app/.migration/extraction_error_report.json")
        print(f"  • /app/.migration/transformation_report.json")
        print(f"  • /app/.migration/generation_report.json")
        print(f"  • /app/.migration/complete_analysis.json")
        print(f"  • {LOG_FILE}")
        
        # Generate documentation using robust version
        print("\n📝 Generating comprehensive documentation...")
        try:
            from arkyvus.migrations.mams_documentation_generator_robust import generate_and_publish_docs
            doc_path = generate_and_publish_docs()
            print(f"✅ Documentation generated: {doc_path}")
        except Exception as e:
            print(f"⚠️ Documentation generation failed: {e}")
            # Fallback to original if robust version fails
            try:
                from arkyvus.migrations.mams_documentation_generator import generate_and_publish_docs as gen_docs_original
                doc_path = gen_docs_original()
                print(f"✅ Documentation generated (fallback): {doc_path}")
            except Exception as e2:
                print(f"❌ Both documentation generators failed: {e2}")
        
        # Show expanded summary statistics
        print("\n📊 Final Migration Statistics:")
        print(f"  Total files in mapping: {len(MASTER_MAPPING)}")
        print(f"  Files processed: {self.total_processed}")
        if self.all_files:
            backend_files = sum(1 for f in self.all_files if '.py' in str(f))
            frontend_files = sum(1 for f in self.all_files if any(ext in str(f) for ext in ['.tsx', '.ts', '.jsx', '.js']))
            print(f"  Backend files: {backend_files}")
            print(f"  Frontend files: {frontend_files}")
        print(f"  Service files extracted: {len(self.extraction_results['services'])}")
        print(f"  Successful: {self.total_processed - len(self.extraction_errors)}")
        print(f"  Errors: {len(self.extraction_errors)}")
        
        # Show enhanced frontend results if available
        frontend_results = [r for r in self.extraction_results.get('services', []) 
                          if isinstance(r, dict) and r.get('platform') == 'frontend']
        if frontend_results:
            print(f"\n🚀 Enhanced Frontend Analysis Results:")
            print(f"  Files with AST parsing: {len(frontend_results)}")
            
            # Confidence distribution
            high_conf = len([r for r in frontend_results if r.get('confidence', 0) >= 0.8])
            med_conf = len([r for r in frontend_results if 0.5 <= r.get('confidence', 0) < 0.8])
            low_conf = len([r for r in frontend_results if r.get('confidence', 0) < 0.5])
            print(f"  Confidence levels:")
            print(f"    High (≥0.8): {high_conf}")
            print(f"    Medium (0.5-0.8): {med_conf}")
            print(f"    Low (<0.5): {low_conf}")
            
            # Review requirements
            review = len([r for r in frontend_results if r.get('requires_review')])
            if review > 0:
                print(f"  ⚠️ Files requiring manual review: {review}")
                print(f"     Review UI available at: /app/.migration/review_ui/")
            
            # Domain distribution
            domains = {}
            for r in frontend_results:
                domain = r.get('domain', 'unknown')
                domains[domain] = domains.get(domain, 0) + 1
            
            if domains:
                print(f"  Domain classification:")
                for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"    {domain}: {count} files")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--skip-validation', action='store_true')
    parser.add_argument('--store-to-db', action='store_true', help='Store results to migration_source_catalog')
    args = parser.parse_args()
    
    Orchestrator(args.dry_run, args.workers, args.skip_validation, args.store_to_db).run()

if __name__ == "__main__":
    main()