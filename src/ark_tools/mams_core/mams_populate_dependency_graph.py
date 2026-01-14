#!/usr/bin/env python3
"""
MAMS Migration Dependency Graph Population
Populates the migration_dependency_graph table by analyzing code dependencies
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import ast
import logging

logger = logging.getLogger(__name__)

class DependencyGraphPopulator:
    def __init__(self):
        self.migration_dir = Path('/app/.migration')
        self.extraction_results_path = self.migration_dir / 'extraction_results_all.json'
        self.dependencies = []
        
    def load_extraction_results(self) -> Dict:
        """Load the extraction results from MAMS run"""
        if self.extraction_results_path.exists():
            with open(self.extraction_results_path, 'r') as f:
                return json.load(f)
        return {'services': []}
    
    def resolve_file_path(self, file_path: str) -> str:
        """Resolve relative paths to absolute paths based on project structure"""
        # If already absolute, return as is
        if file_path.startswith('/'):
            return file_path
            
        # From arkyvus_project directory:
        # - Frontend: /client/src/...
        # - Backend: /arkyvus/...
        
        # Handle frontend files (src/...)
        if file_path.startswith('src/'):
            # Frontend files are in client/src
            possible_paths = [
                Path('/app/client') / file_path,  # Container: /app/client/src/...
                Path('/Users/pregenie/Development/arkyvus_project/client') / file_path,  # Local
                Path('./client') / file_path,  # Relative local
            ]
        # Handle backend files (arkyvus/...)
        elif file_path.startswith('arkyvus/'):
            possible_paths = [
                Path('/app') / file_path,  # Container: /app/arkyvus/...
                Path('/Users/pregenie/Development/arkyvus_project') / file_path,  # Local
                Path('.') / file_path,  # Relative local
            ]
        else:
            # Try both frontend and backend locations
            possible_paths = [
                Path('/app/client/src') / file_path,  # Frontend in container
                Path('/app/arkyvus') / file_path,  # Backend in container
                Path('/Users/pregenie/Development/arkyvus_project/client/src') / file_path,  # Frontend local
                Path('/Users/pregenie/Development/arkyvus_project/arkyvus') / file_path,  # Backend local
                Path('./client/src') / file_path,  # Frontend relative
                Path('./arkyvus') / file_path,  # Backend relative
            ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        # If not found, return the original (will fail gracefully later)
        return file_path
    
    def extract_python_imports(self, file_path: str) -> List[Tuple[str, str]]:
        """Extract import dependencies from Python files"""
        dependencies = []
        
        # Resolve the actual file path
        actual_path = self.resolve_file_path(file_path)
        
        try:
            with open(actual_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(('import', alias.name))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        full_import = f"{module}.{alias.name}" if module else alias.name
                        dependencies.append(('from_import', full_import))
                        
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path} (tried: {actual_path})")
        except Exception as e:
            logger.warning(f"Could not parse {file_path}: {e}")
            
        return dependencies
    
    def extract_typescript_imports(self, file_path: str) -> List[Tuple[str, str]]:
        """Extract import dependencies from TypeScript/JavaScript files"""
        dependencies = []
        
        # Resolve the actual file path
        actual_path = self.resolve_file_path(file_path)
        
        try:
            with open(actual_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regular expressions for different import patterns
            patterns = [
                r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",  # ES6 imports
                r"require\s*\(['\"]([^'\"]+)['\"]\)",  # CommonJS require
                r"import\s*\(['\"]([^'\"]+)['\"]\)",  # Dynamic imports
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    dependencies.append(('import', match))
                    
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path} (tried: {actual_path})")
        except Exception as e:
            logger.warning(f"Could not parse {file_path}: {e}")
            
        return dependencies
    
    def resolve_import_to_file(self, import_path: str, from_file: str, platform: str) -> Optional[str]:
        """Resolve an import path to an actual file in the catalog
        Returns paths in extraction format: src/... for frontend, arkyvus/... for backend
        """
        
        if platform == 'backend':
            # Python import resolution
            if import_path.startswith('arkyvus'):
                # Internal arkyvus imports - already in correct format
                module_parts = import_path.split('.')
                # Could be importing a module or specific item from module
                # Try as direct module first
                potential_path = '/'.join(module_parts) + '.py'
                if potential_path.startswith('arkyvus/'):
                    return potential_path
                return 'arkyvus/' + potential_path
            elif not import_path.startswith('.'):
                # External package - not tracked in our migration
                return None
            else:
                # Relative import
                from_dir = Path(from_file).parent
                import_parts = import_path.lstrip('.').split('.')
                # Count leading dots for relative levels
                level = len(import_path) - len(import_path.lstrip('.'))
                
                # Go up directories based on relative level
                current_dir = from_dir
                for _ in range(level - 1):
                    current_dir = current_dir.parent
                    
                # Build the target path
                target_parts = list(current_dir.parts) + import_parts
                # Ensure it starts with arkyvus/ for backend
                if 'arkyvus' in target_parts:
                    idx = target_parts.index('arkyvus')
                    result_path = '/'.join(target_parts[idx:]) + '.py'
                    return result_path
                    
                return str(current_dir / '/'.join(import_parts)) + '.py'
                
        elif platform == 'frontend':
            # TypeScript/JavaScript import resolution
            if import_path.startswith('@/'):
                # Alias import (@/ maps to src/)
                # Remove @/ and add src/ prefix
                base_path = 'src/' + import_path[2:]
                # Don't add extension yet - will check what exists
                return base_path
            elif import_path.startswith('./') or import_path.startswith('../'):
                # Relative import - resolve from current file location
                from_dir = Path(from_file).parent
                
                # Normalize the path
                resolved_parts = []
                from_parts = list(from_dir.parts)
                import_parts = import_path.split('/')
                
                # Start with directory of importing file
                resolved_parts = from_parts[:]
                
                # Process the relative path
                for part in import_parts:
                    if part == '.':
                        continue  # Current directory
                    elif part == '..':
                        if resolved_parts:
                            resolved_parts.pop()  # Go up one level
                    else:
                        resolved_parts.append(part)
                
                # Ensure it starts with src/ for frontend
                if 'src' in resolved_parts:
                    idx = resolved_parts.index('src')
                    result_path = '/'.join(resolved_parts[idx:])
                    # Don't add extension - let caller handle that
                    return result_path
                    
                return '/'.join(resolved_parts)
            else:
                # Node module import - not tracked
                return None
                
        return None
    
    def analyze_dependencies(self):
        """Analyze all files and build dependency relationships"""
        results = self.load_extraction_results()
        
        # Build a map of file paths to their IDs for quick lookup
        # IMPORTANT: The catalog stores ABSOLUTE paths like /app/client/src/...
        # while extraction results use RELATIVE paths like src/...
        file_to_metadata = {}
        processed_count = 0
        frontend_count = 0
        backend_count = 0
        
        print("\n🔍 Starting deep dependency analysis...")
        print("This will analyze ALL files for import statements - may take several minutes")
        
        services = results.get('services', [])
        total_services = len(services)
        
        # Process all services (backend and frontend)
        for idx, service in enumerate(services):
            file_path = service.get('file')
            
            # Show progress every 100 files
            if idx % 100 == 0:
                print(f"  Progress: {idx}/{total_services} files analyzed ({(idx/total_services)*100:.1f}%)")
            
            if file_path:
                # CRITICAL: Convert to absolute path format used in migration_source_catalog
                if file_path.startswith('src/'):
                    # Frontend files need /app/client/ prefix
                    absolute_path = '/app/client/' + file_path
                elif file_path.startswith('arkyvus/'):
                    # Backend files need /app/ prefix
                    absolute_path = '/app/' + file_path
                else:
                    absolute_path = file_path
                
                # Store both relative and absolute for lookup
                metadata = {
                    'platform': service.get('platform', 'backend'),
                    'domain': service.get('domain'),
                    'service': service.get('service'),
                    'absolute_path': absolute_path,
                    'relative_path': file_path
                }
                
                # Index by both paths
                file_to_metadata[file_path] = metadata
                file_to_metadata[absolute_path] = metadata
                
                # Extract dependencies based on file type
                platform = service.get('platform', 'backend')
                
                if platform == 'backend' and file_path.endswith('.py'):
                    imports = self.extract_python_imports(file_path)
                    backend_count += 1
                elif platform == 'frontend' and any(file_path.endswith(ext) for ext in ['.tsx', '.ts', '.jsx', '.js']):
                    imports = self.extract_typescript_imports(file_path)
                    frontend_count += 1
                else:
                    imports = []
                
                processed_count += 1
                
                # Resolve imports to actual files
                for import_type, import_path in imports:
                    target_file = self.resolve_import_to_file(import_path, file_path, platform)
                    
                    if target_file:
                        # Convert target to absolute path for catalog lookup
                        if target_file.startswith('src/'):
                            target_absolute = '/app/client/' + target_file
                        elif target_file.startswith('arkyvus/'):
                            target_absolute = '/app/' + target_file
                        else:
                            target_absolute = target_file
                        
                        # For frontend files, try with different extensions
                        resolved_target = None
                        if platform == 'frontend' and not target_file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                            # Try to find the actual file with extension
                            for ext in ['.tsx', '.ts', '.jsx', '.js', '/index.tsx', '/index.ts', '/index.jsx', '/index.js']:
                                potential = target_file + ext
                                potential_absolute = '/app/client/' + potential if potential.startswith('src/') else potential
                                
                                if potential in file_to_metadata or potential_absolute in file_to_metadata:
                                    resolved_target = potential_absolute if potential_absolute in file_to_metadata else potential
                                    break
                        else:
                            # Check if target exists in our metadata
                            if target_absolute in file_to_metadata or target_file in file_to_metadata:
                                resolved_target = target_absolute if target_absolute in file_to_metadata else target_file
                        
                        if resolved_target and resolved_target in file_to_metadata:
                            # We have a dependency between two tracked files
                            # Store using ABSOLUTE paths to match migration_source_catalog
                            source_absolute = absolute_path  # Already computed above
                            target_meta = file_to_metadata[resolved_target]
                            target_final = target_meta.get('absolute_path', resolved_target)
                            
                            self.dependencies.append({
                                'source_file': source_absolute,  # Use absolute path
                                'target_file': target_final,     # Use absolute path
                                'dependency_type': 'import',
                                'import_statement': import_path,
                                'source_relative': file_path,    # Keep relative for debugging
                                'target_relative': target_meta.get('relative_path', target_file)
                            })
        
        print(f"📊 Analyzed {processed_count} files ({backend_count} backend, {frontend_count} frontend)")
        print(f"🔗 Found {len(self.dependencies)} dependencies between tracked files")
        
        # Show sample dependencies for verification
        if self.dependencies:
            print("\nSample dependencies found (showing relative paths):")
            for dep in self.dependencies[:5]:
                source = dep.get('source_relative', dep['source_file'])
                target = dep.get('target_relative', dep['target_file'])
                print(f"  {source} → {target}")
            print(f"\nDependencies use absolute paths like: {self.dependencies[0]['source_file']}")
                
        return self.dependencies
    
    def populate_database(self):
        """Populate the migration_dependency_graph table"""
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker
            import os
            
            # Get database connection
            db_url = os.getenv('DATABASE_URL', 'postgresql://arkyvus:arkyvus@localhost:5432/arkyvus')
            engine = create_engine(db_url)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # First, get all files from migration_source_catalog to get their IDs
            result = session.execute(text("""
                SELECT id, full_qualified_name 
                FROM migration_source_catalog
            """))
            
            file_to_id = {}
            frontend_samples = []
            backend_samples = []
            
            for row in result:
                path = row.full_qualified_name
                file_to_id[path] = row.id
                
                # Collect samples for debugging
                if path.startswith('src/') and len(frontend_samples) < 5:
                    frontend_samples.append(path)
                elif path.startswith('arkyvus/') and len(backend_samples) < 5:
                    backend_samples.append(path)
            
            print(f"Found {len(file_to_id)} files in migration_source_catalog")
            
            # Show sample paths to understand the format
            print("\n📁 Sample paths in migration_source_catalog:")
            if frontend_samples:
                print("  Frontend paths:")
                for p in frontend_samples:
                    print(f"    - {p}")
            if backend_samples:
                print("  Backend paths:")
                for p in backend_samples:
                    print(f"    - {p}")
            
            # Also try alternate path formats
            # Some systems might store paths differently
            alt_file_to_id = {}
            for path, id_val in file_to_id.items():
                # Try without client/ prefix for frontend
                if path.startswith('client/src/'):
                    alt_path = path[7:]  # Remove 'client/'
                    alt_file_to_id[alt_path] = id_val
                # Try with client/ prefix for frontend
                elif path.startswith('src/'):
                    alt_path = 'client/' + path
                    alt_file_to_id[alt_path] = id_val
            
            # Merge alternative mappings
            file_to_id.update(alt_file_to_id)
            print(f"After adding alternate paths: {len(file_to_id)} total mappings")
            
            # Analyze dependencies
            self.analyze_dependencies()
            
            # Insert dependencies into the database
            inserted_count = 0
            skipped_count = 0
            not_found_count = 0
            
            # Debug output is already shown above, skip this duplicate
            
            for dep in self.dependencies:
                source_file = dep['source_file']
                target_file = dep['target_file']
                
                # Try multiple normalization strategies
                # The extraction results use paths like "src/..." for frontend
                # and "arkyvus/..." for backend, matching what's in the catalog
                
                # First try as-is (extraction results should already match)
                source_id = file_to_id.get(source_file)
                target_id = file_to_id.get(target_file)
                
                # If not found, try without leading slashes
                if not source_id:
                    source_normalized = source_file.lstrip('/')
                    source_id = file_to_id.get(source_normalized)
                    
                if not target_id:
                    target_normalized = target_file.lstrip('/')
                    target_id = file_to_id.get(target_normalized)
                
                # If still not found, try removing common prefixes
                if not source_id:
                    for prefix in ['/app/', '/Users/pregenie/Development/arkyvus_project/', './']:
                        if source_file.startswith(prefix):
                            source_normalized = source_file[len(prefix):]
                            source_id = file_to_id.get(source_normalized)
                            if source_id:
                                break
                
                if not target_id:
                    for prefix in ['/app/', '/Users/pregenie/Development/arkyvus_project/', './']:
                        if target_file.startswith(prefix):
                            target_normalized = target_file[len(prefix):]
                            target_id = file_to_id.get(target_normalized)
                            if target_id:
                                break
                
                if not source_id or not target_id:
                    not_found_count += 1
                    if not_found_count <= 5:  # Show first few misses for debugging
                        print(f"⚠️  Could not find IDs for dependency:")
                        print(f"    Source: {source_file} -> ID: {source_id}")
                        print(f"    Target: {target_file} -> ID: {target_id}")
                        
                        # Show what similar paths exist in the catalog
                        if not source_id:
                            source_name = Path(source_file).name
                            similar = [p for p in file_to_id.keys() if source_name in p]
                            if similar:
                                print(f"    Similar source paths in catalog: {similar[:3]}")
                        if not target_id:
                            target_name = Path(target_file).name
                            similar = [p for p in file_to_id.keys() if target_name in p]
                            if similar:
                                print(f"    Similar target paths in catalog: {similar[:3]}")
                    continue
                
                if source_id and target_id and source_id != target_id:
                    try:
                        # Check if this dependency already exists
                        existing = session.execute(text("""
                            SELECT 1 FROM migration_dependency_graph 
                            WHERE source_method_id = :source_id 
                            AND depends_on_method_id = :target_id
                            AND dependency_type = :dep_type
                        """), {
                            'source_id': source_id,
                            'target_id': target_id,
                            'dep_type': dep['dependency_type']
                        }).first()
                        
                        if not existing:
                            # Insert the dependency
                            session.execute(text("""
                                INSERT INTO migration_dependency_graph 
                                (source_method_id, depends_on_method_id, dependency_type, 
                                 is_circular, can_migrate_independently, created_at)
                                VALUES (:source_id, :target_id, :dep_type, 
                                        false, false, CURRENT_TIMESTAMP)
                            """), {
                                'source_id': source_id,
                                'target_id': target_id,
                                'dep_type': dep['dependency_type']
                            })
                            inserted_count += 1
                        else:
                            skipped_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to insert dependency: {e}")
                        
            # Commit all changes
            session.commit()
            
            print(f"✅ Successfully inserted {inserted_count} dependencies")
            print(f"⏩ Skipped {skipped_count} existing dependencies")
            
            # Detect circular dependencies
            print("\n🔄 Detecting circular dependencies...")
            session.execute(text("""
                WITH RECURSIVE dep_chain AS (
                    -- Base case: all dependencies
                    SELECT 
                        source_method_id,
                        depends_on_method_id,
                        ARRAY[source_method_id, depends_on_method_id] as path,
                        1 as depth
                    FROM migration_dependency_graph
                    
                    UNION ALL
                    
                    -- Recursive case
                    SELECT 
                        dc.source_method_id,
                        mdg.depends_on_method_id,
                        dc.path || mdg.depends_on_method_id,
                        dc.depth + 1
                    FROM dep_chain dc
                    JOIN migration_dependency_graph mdg 
                        ON dc.depends_on_method_id = mdg.source_method_id
                    WHERE NOT (mdg.depends_on_method_id = ANY(dc.path))
                        AND dc.depth < 10  -- Limit recursion depth
                )
                UPDATE migration_dependency_graph mdg
                SET is_circular = true
                FROM dep_chain dc
                WHERE dc.depends_on_method_id = dc.source_method_id
                    AND (mdg.source_method_id = ANY(dc.path) 
                         OR mdg.depends_on_method_id = ANY(dc.path))
            """))
            
            # Check for circular dependencies
            result = session.execute(text("""
                SELECT COUNT(*) as circular_count
                FROM migration_dependency_graph
                WHERE is_circular = true
            """)).first()
            
            if result and result.circular_count > 0:
                print(f"⚠️  Found {result.circular_count} circular dependencies")
            else:
                print("✅ No circular dependencies detected")
            
            # Set migration order based on dependency depth
            print("\n📊 Calculating migration order using topological sort...")
            
            # First, build a proper dependency graph for topological sorting
            print("  Building dependency graph...")
            dep_graph = {}  # file_id -> list of files it depends on
            reverse_graph = {}  # file_id -> list of files that depend on it
            all_file_ids = set()
            
            # Get all dependencies
            deps_result = session.execute(text("""
                SELECT source_method_id, depends_on_method_id 
                FROM migration_dependency_graph
            """))
            
            for row in deps_result:
                source_id = row.source_method_id
                target_id = row.depends_on_method_id
                
                all_file_ids.add(source_id)
                all_file_ids.add(target_id)
                
                # source depends on target (source imports target)
                if source_id not in dep_graph:
                    dep_graph[source_id] = []
                dep_graph[source_id].append(target_id)
                
                # target is depended upon by source
                if target_id not in reverse_graph:
                    reverse_graph[target_id] = []
                reverse_graph[target_id].append(source_id)
            
            print(f"  Found {len(all_file_ids)} files involved in dependencies")
            
            # Topological sort using Kahn's algorithm to determine migration order
            # Files with no dependencies should be migrated first (order 0)
            # Files that depend on them next (order 1), etc.
            
            # Find all nodes with no incoming edges (no dependencies)
            in_degree = {}
            for file_id in all_file_ids:
                in_degree[file_id] = len(dep_graph.get(file_id, []))
            
            # Queue of files with no dependencies
            queue = [fid for fid in all_file_ids if in_degree[fid] == 0]
            migration_orders = {}
            current_level = 0
            
            print(f"  Starting with {len(queue)} root files (no dependencies)")
            
            while queue:
                next_queue = []
                
                for file_id in queue:
                    migration_orders[file_id] = current_level
                    
                    # For each file that depends on this one
                    for dependent in reverse_graph.get(file_id, []):
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            next_queue.append(dependent)
                
                queue = next_queue
                if queue:
                    current_level += 1
            
            print(f"  Calculated {len(migration_orders)} migration orders with max depth {current_level}")
            
            # Update migration_order for all dependencies
            for file_id, order in migration_orders.items():
                session.execute(text("""
                    UPDATE migration_dependency_graph 
                    SET migration_order = :order
                    WHERE source_method_id = :file_id OR depends_on_method_id = :file_id
                """), {'order': order, 'file_id': file_id})
            
            # Also add migration order to a new column in migration_source_catalog for easier querying
            # First check if column exists
            try:
                session.execute(text("""
                    ALTER TABLE migration_source_catalog 
                    ADD COLUMN IF NOT EXISTS migration_order INTEGER DEFAULT NULL
                """))
                session.commit()
                
                # Update migration order in source catalog
                for file_id, order in migration_orders.items():
                    session.execute(text("""
                        UPDATE migration_source_catalog 
                        SET migration_order = :order
                        WHERE id = :file_id
                    """), {'order': order, 'file_id': file_id})
                
                print("  Updated migration_source_catalog with migration orders")
            except Exception as e:
                print(f"  Note: Could not add migration_order to catalog: {e}")
            
            session.commit()
            print(f"✅ Migration order calculated: {current_level + 1} levels of dependencies")
            
            # Summary statistics
            result = session.execute(text("""
                SELECT 
                    COUNT(*) as total_dependencies,
                    COUNT(DISTINCT source_method_id) as files_with_dependencies,
                    COUNT(DISTINCT depends_on_method_id) as files_depended_upon,
                    COUNT(CASE WHEN is_circular THEN 1 END) as circular_deps,
                    MAX(migration_order) as max_depth,
                    MIN(migration_order) as min_depth
                FROM migration_dependency_graph
            """)).first()
            
            if result:
                print("\n📈 Dependency Graph Statistics:")
                print(f"  Total dependencies: {result.total_dependencies}")
                print(f"  Files with outgoing dependencies: {result.files_with_dependencies}")
                print(f"  Files with incoming dependencies: {result.files_depended_upon}")
                print(f"  Circular dependencies: {result.circular_deps}")
                print(f"  Migration order range: {result.min_depth} to {result.max_depth}")
                
                # Show migration order distribution
                order_dist = session.execute(text("""
                    SELECT migration_order, COUNT(*) as count
                    FROM (
                        SELECT DISTINCT source_method_id as file_id, migration_order
                        FROM migration_dependency_graph
                        WHERE migration_order IS NOT NULL
                        UNION
                        SELECT DISTINCT depends_on_method_id as file_id, migration_order  
                        FROM migration_dependency_graph
                        WHERE migration_order IS NOT NULL
                    ) t
                    GROUP BY migration_order
                    ORDER BY migration_order
                    LIMIT 10
                """))
                
                print("\n📊 Migration Order Distribution (first 10 levels):")
                for row in order_dist:
                    if row.migration_order is not None:
                        print(f"  Level {row.migration_order}: {row.count} files")
                
                # Show example files at each level
                print("\n🔍 Example files at each migration level:")
                examples = session.execute(text("""
                    WITH file_orders AS (
                        SELECT DISTINCT mdg.source_method_id as file_id, 
                               mdg.migration_order,
                               msc.full_qualified_name
                        FROM migration_dependency_graph mdg
                        JOIN migration_source_catalog msc ON msc.id = mdg.source_method_id
                        WHERE mdg.migration_order IS NOT NULL
                    )
                    SELECT migration_order, 
                           STRING_AGG(
                               CASE 
                                   WHEN full_qualified_name LIKE '%/%' 
                                   THEN SUBSTRING(full_qualified_name FROM '[^/]+$')
                                   ELSE full_qualified_name
                               END, ', '
                           ) as examples
                    FROM (
                        SELECT migration_order, full_qualified_name,
                               ROW_NUMBER() OVER (PARTITION BY migration_order ORDER BY full_qualified_name) as rn
                        FROM file_orders
                    ) t
                    WHERE rn <= 3
                    GROUP BY migration_order
                    ORDER BY migration_order
                    LIMIT 5
                """))
                
                for row in examples:
                    if row.migration_order is not None:
                        print(f"  Level {row.migration_order}: {row.examples}")
            
            session.close()
            
        except ImportError:
            print("❌ SQLAlchemy not available - cannot populate database")
        except Exception as e:
            print(f"❌ Failed to populate dependency graph: {e}")
            import traceback
            traceback.print_exc()

def populate_dependency_graph():
    """Main entry point"""
    populator = DependencyGraphPopulator()
    populator.populate_database()

if __name__ == "__main__":
    populate_dependency_graph()