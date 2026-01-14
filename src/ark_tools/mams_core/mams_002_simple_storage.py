#!/usr/bin/env python3
"""
MAMS-002: Simple Backend Discovery and Storage
NO unified logging, NO RabbitMQ, just direct database storage
"""

import ast
import json
import uuid
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class SimpleBackendDiscovery:
    """Simple backend discovery without any logging complexity"""
    
    def __init__(self):
        self.methods = []
        
    def discover_methods(self) -> List[Dict[str, Any]]:
        """Discover methods in Python files"""
        print("🔍 MAMS-002: Simple Backend Discovery")
        print("Scanning arkyvus...")
        
        # Find Python files
        python_files = []
        for py_file in Path('arkyvus').rglob('*.py'):
            # Skip test files and cache
            if any(skip in str(py_file) for skip in ['__pycache__', 'test_', '_test', '.git', 'migrations']):
                continue
            python_files.append(py_file)
        
        print(f"Found {len(python_files)} Python files")
        
        # Process all files
        for py_file in python_files:
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                self._extract_methods(tree, str(py_file))
            except:
                pass
                
        print(f"Discovered {len(self.methods)} methods")
        return self.methods
    
    def _extract_methods(self, tree: ast.AST, file_path: str):
        """Extract methods from AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        method_info = {
                            'id': str(uuid.uuid4()),
                            'file_path': file_path,
                            'class_name': class_name,
                            'method_name': method.name,
                            'line_number': method.lineno,
                            'is_async': isinstance(method, ast.AsyncFunctionDef),
                            'service_type': self._classify_service_type(class_name, method.name),
                            'full_qualified_name': f"{file_path.replace('/', '.').replace('.py', '')}.{class_name}.{method.name}"
                        }
                        self.methods.append(method_info)
    
    def _classify_service_type(self, class_name: str, method_name: str) -> str:
        """Simple service type classification - only returns constraint-allowed values"""
        class_lower = class_name.lower()
        if 'manager' in class_lower:
            return 'manager'
        elif 'service' in class_lower:
            return 'service'
        elif 'repository' in class_lower or 'repo' in class_lower:
            return 'repository'
        elif 'handler' in class_lower:
            return 'handler'
        elif 'client' in class_lower:
            return 'client'
        elif 'controller' in class_lower:
            return 'controller'
        elif 'model' in class_lower:
            return 'utility'  # Map models to utility since 'model' not allowed
        else:
            return 'utility'
    
    def store_in_database(self):
        """Store discovered methods directly in database - NO UNIFIED LOGGING"""
        print("💾 Storing in database...")
        
        # Direct database connection
        conn = psycopg2.connect(
            host='db-arkyvus',
            database='arkyvus_db',
            user='admin', 
            password='chooters'
        )
        
        try:
            cur = conn.cursor()
            created_count = 0
            
            for method in self.methods:
                try:
                    # Check if exists
                    cur.execute(
                        "SELECT id FROM migration_source_catalog WHERE full_qualified_name = %s",
                        (method['full_qualified_name'],)
                    )
                    existing = cur.fetchone()
                    
                    if not existing:
                        # Insert new record
                        cur.execute("""
                            INSERT INTO migration_source_catalog 
                            (id, full_qualified_name, source_type, service_name, method_name,
                             method_signature, current_state, discovery_metadata, last_seen)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            method['id'],
                            method['full_qualified_name'],
                            method['service_type'],
                            method['class_name'],
                            method['method_name'],
                            json.dumps({
                                "method_name": method['method_name'],
                                "is_async": method['is_async'],
                                "line_number": method['line_number']
                            }),
                            "active",
                            json.dumps({
                                "file_path": method['file_path'],
                                "discovered_at": datetime.utcnow().isoformat()
                            }),
                            datetime.utcnow()
                        ))
                        created_count += 1
                        print(f"✅ Added: {method['full_qualified_name']}")
                    else:
                        print(f"⏭️ Exists: {method['full_qualified_name']}")
                        
                except Exception as e:
                    print(f"❌ Error with {method.get('full_qualified_name', 'unknown')}: {e}")
                    continue
            
            conn.commit()
            print(f"✅ Database storage complete: {created_count} new records")
            
        finally:
            conn.close()

def main():
    """Main execution"""
    discovery = SimpleBackendDiscovery()
    
    # Discover methods
    methods = discovery.discover_methods()
    print(f"\nMethods by service type:")
    types = {}
    for method in methods:
        t = method['service_type'].upper()
        types[t] = types.get(t, 0) + 1
    
    for t, count in sorted(types.items()):
        print(f"  {t}: {count}")
    
    # Store in database
    discovery.store_in_database()
    
    print(f"\n🎯 MAMS-002 Complete: {len(methods)} backend methods processed")

if __name__ == "__main__":
    main()