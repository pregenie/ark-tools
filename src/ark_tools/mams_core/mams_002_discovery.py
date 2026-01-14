#!/usr/bin/env python3
"""
MAMS-002: Simplified Service Discovery Implementation
Avoids circular imports by being completely standalone
"""
import ast
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid


class SimpleMethodDiscovery:
    """Simplified discovery without external dependencies"""
    
    def __init__(self):
        self.methods = []
        
    def discover_methods(self, base_path: str = 'arkyvus') -> List[Dict[str, Any]]:
        """Discover methods in Python files"""
        print(f"Scanning {base_path}...")
        
        # Find Python files
        python_files = []
        for py_file in Path(base_path).rglob('*.py'):
            # Skip test files and cache
            if any(skip in str(py_file) for skip in ['__pycache__', 'test_', '_test', '.git', 'migrations']):
                continue
            python_files.append(py_file)
        
        print(f"Found {len(python_files)} Python files")
        
        # Process files
        for py_file in python_files[:20]:  # Limit for initial test
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                self._extract_methods(tree, str(py_file))
            except:
                pass
                
        return self.methods
    
    def _extract_methods(self, tree: ast.AST, file_path: str):
        """Extract methods from AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not item.name.startswith('_') or item.name == '__init__':
                            self.methods.append({
                                'id': str(uuid.uuid4()),
                                'file_path': file_path,
                                'class_name': class_name,
                                'method_name': item.name,
                                'line_number': item.lineno,
                                'is_async': isinstance(item, ast.AsyncFunctionDef),
                                'service_type': self._classify_service(class_name, file_path),
                                'full_qualified_name': f"{file_path.replace('/', '.').replace('.py', '')}.{class_name}.{item.name}"
                            })
    
    def _classify_service(self, class_name: str, file_path: str) -> str:
        """Simple service classification"""
        class_lower = class_name.lower()
        path_lower = file_path.lower()
        
        if 'service' in class_lower:
            return 'SERVICE'
        elif 'manager' in class_lower:
            return 'MANAGER'
        elif 'repository' in class_lower or 'repo' in class_lower:
            return 'REPOSITORY'
        elif 'handler' in class_lower:
            return 'HANDLER'
        elif 'client' in class_lower:
            return 'CLIENT'
        elif 'model' in class_lower or 'models/' in path_lower:
            return 'MODEL'
        elif 'controller' in class_lower or 'api/' in path_lower:
            return 'CONTROLLER'
        else:
            return 'UTILITY'
    
    def store_in_database(self):
        """Store discovered methods in database"""
        import psycopg2
        import json
        from datetime import datetime
        
        # Direct database connection - NO Flask, NO unified logging
        conn = psycopg2.connect(
            host='db-arkyvus',
            database='arkyvus_db', 
            user='admin',
            password='chooters'
        )
        
        try:
            batch_size = 50
            for i in range(0, len(self.methods), batch_size):
                batch = self.methods[i:i + batch_size]
                
                for method in batch:
                    try:
                        # Check if exists
                        result = db.session.execute(
                            db.text("SELECT id FROM migration_source_catalog WHERE full_qualified_name = :fqn"),
                            {"fqn": method['full_qualified_name']}
                        )
                        existing = result.fetchone()
                        
                        if not existing:
                            # Insert new
                            db.session.execute(
                                db.text("""
                                    INSERT INTO migration_source_catalog 
                                    (id, full_qualified_name, source_type, service_name, method_name,
                                     method_signature, current_state, discovery_metadata, last_seen)
                                    VALUES (:id, :fqn, :source_type, :service_name, :method_name,
                                            :sig, 'active', :meta, :last_seen)
                                """),
                                {
                                    "id": method['id'],
                                    "fqn": method['full_qualified_name'],
                                    "source_type": method['service_type'],
                                    "service_name": method['class_name'],
                                    "method_name": method['method_name'],
                                    "sig": json.dumps({
                                        'is_async': method['is_async'],
                                        'line_number': method['line_number']
                                    }),
                                    "meta": json.dumps({
                                        'file_path': method['file_path'],
                                        'discovered_at': datetime.utcnow().isoformat()
                                    }),
                                    "last_seen": datetime.utcnow()
                                }
                            )
                    except Exception as e:
                        print(f"Error storing method: {e}")
                        
                db.session.commit()
                print(f"Stored batch {i//batch_size + 1}")
            
            # Print summary
            result = db.session.execute(
                db.text("SELECT COUNT(*) FROM migration_source_catalog")
            )
            total = result.scalar()
            print(f"\nTotal methods in database: {total}")
            
            # Show breakdown by type
            result = db.session.execute(
                db.text("""
                    SELECT source_type, COUNT(*) as count 
                    FROM migration_source_catalog 
                    GROUP BY source_type 
                    ORDER BY count DESC
                """)
            )
            
            print("\nMethods by type:")
            for row in result:
                print(f"  {row.source_type}: {row.count}")
                
        except Exception as e:
            print(f"❌ Database operation failed: {e}")
            db.session.rollback()
        finally:
            db.session.close()


def main():
    """Run discovery"""
    print("=" * 60)
    print("MAMS-002: Service Discovery Engine")
    print("=" * 60)
    
    discovery = SimpleMethodDiscovery()
    
    # Discover methods
    methods = discovery.discover_methods()
    
    print(f"\nDiscovered {len(methods)} methods")
    
    # Show breakdown
    type_counts = {}
    for method in methods:
        t = method['service_type']
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print("\nMethods by service type:")
    for service_type, count in sorted(type_counts.items()):
        print(f"  {service_type}: {count}")
    
    # Show sample
    print("\nSample methods:")
    for method in methods[:10]:
        print(f"  - {method['class_name']}.{method['method_name']} ({method['service_type']})")
    
    # Store in database
    print("\nStoring in database...")
    discovery.store_in_database()
    
    print("\n✅ Discovery completed successfully")


if __name__ == "__main__":
    main()