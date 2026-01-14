#!/usr/bin/env python3
"""
MAMS Migration Documentation Generator
Generates comprehensive documentation from migration JSON outputs.
Robustly handles missing data by cross-referencing multiple JSON sources.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict

class DocumentationGenerator:
    def __init__(self):
        self.migration_dir = Path('/app/.migration')
        self.docs_dir = Path('/app/docs/migration')
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all JSON reports with fallbacks
        self.extraction_results = self._load_json('extraction_results_all.json')
        self.extraction_errors = self._load_json('extraction_error_report.json')
        self.transformation_report = self._load_json('transformation_report.json')
        self.generation_report = self._load_json('generation_report.json')
        self.complete_analysis = self._load_json('complete_analysis.json')
        self.file_disposition = self._load_json('file_disposition_report.json')
        
        # Load Master Mapping
        self.master_mapping = self._load_master_mapping()
        
        # Pre-process frontend files from ALL sources to ensure we have data
        self.all_frontend_files = self._aggregate_frontend_files()

    def _load_json(self, filename: str) -> Dict:
        """Robust JSON loader"""
        filepath = self.migration_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ Warning: Could not decode {filename}")
                return {}
        return {}
    
    def _load_master_mapping(self) -> Dict:
        """Load the MAMS Master Mapping with multiple path checks"""
        possible_paths = [
            Path('/app/MAMS_MASTER_MAPPING.json'),
            Path('./MAMS_MASTER_MAPPING.json'),
            Path('../MAMS_MASTER_MAPPING.json'),
            Path('/Users/pregenie/Development/arkyvus_project/MAMS_MASTER_MAPPING.json')
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r') as f:
                        print(f"✅ Loaded Master Mapping from {path}")
                        return json.load(f)
                except:
                    continue
        print("⚠️ Warning: Master Mapping not found.")
        return {'mappings': {}}

    def _infer_domain_from_path(self, file_path: str) -> str:
        """
        Intelligently infer domain from file path patterns.
        Based on common React/TypeScript project structures.
        """
        path_lower = file_path.lower()
        path_parts = Path(file_path).parts
        
        # Check for explicit domain folders
        domain_folders = {
            'auth': ['auth', 'authentication', 'login', 'signup', 'session'],
            'user': ['user', 'users', 'profile', 'account', 'settings'],
            'dashboard': ['dashboard', 'home', 'overview', 'analytics'],
            'admin': ['admin', 'administration', 'management', 'superuser'],
            'api': ['api', 'services', 'endpoints', 'client'],
            'content': ['content', 'articles', 'posts', 'blog', 'media'],
            'commerce': ['commerce', 'shop', 'cart', 'checkout', 'payment', 'order'],
            'messaging': ['message', 'messaging', 'chat', 'notification', 'email'],
            'search': ['search', 'filter', 'query', 'find'],
            'report': ['report', 'reports', 'analytics', 'metrics', 'statistics'],
            'security': ['security', 'permission', 'role', 'access', 'guard'],
            'workflow': ['workflow', 'process', 'task', 'job', 'queue'],
            'integration': ['integration', 'webhook', 'sync', 'import', 'export'],
            'ui': ['components', 'ui', 'ux', 'design', 'layout', 'theme'],
            'shared': ['shared', 'common', 'utils', 'helpers', 'lib'],
            'test': ['test', 'tests', 'spec', 'testing', '__test__', '__tests__']
        }
        
        # Check path parts for domain indicators
        for domain, patterns in domain_folders.items():
            for pattern in patterns:
                # Check if pattern appears in any path component
                for part in path_parts:
                    if pattern in part.lower():
                        return domain
                # Check if pattern appears in the full path
                if pattern in path_lower:
                    return domain
        
        # Check file name patterns
        filename = Path(file_path).name.lower()
        
        # Specific file pattern checks
        if 'auth' in filename or 'login' in filename or 'signup' in filename:
            return 'auth'
        elif 'user' in filename or 'profile' in filename:
            return 'user'
        elif 'admin' in filename:
            return 'admin'
        elif 'dashboard' in filename or 'home' in filename:
            return 'dashboard'
        elif 'api' in filename or 'service' in filename or 'client' in filename:
            return 'api'
        elif 'report' in filename or 'analytic' in filename:
            return 'report'
        elif 'test' in filename or 'spec' in filename:
            return 'test'
        
        # Check parent directories for context
        if len(path_parts) > 2:
            parent_dir = path_parts[-2].lower()
            for domain, patterns in domain_folders.items():
                if any(pattern in parent_dir for pattern in patterns):
                    return domain
        
        # Check for page/route patterns
        if '/pages/' in path_lower or '/routes/' in path_lower or '/views/' in path_lower:
            # Try to extract domain from page path
            for i, part in enumerate(path_parts):
                if part in ['pages', 'routes', 'views'] and i + 1 < len(path_parts):
                    next_part = path_parts[i + 1].lower()
                    # Map common page names to domains
                    if next_part in domain_folders:
                        return next_part
                    for domain, patterns in domain_folders.items():
                        if next_part in patterns:
                            return domain
        
        # If still no match, check for feature modules
        if '/features/' in path_lower or '/modules/' in path_lower:
            for i, part in enumerate(path_parts):
                if part in ['features', 'modules'] and i + 1 < len(path_parts):
                    feature_name = path_parts[i + 1].lower()
                    # Try to map feature to domain
                    for domain, patterns in domain_folders.items():
                        if feature_name in patterns or any(p in feature_name for p in patterns):
                            return domain
                    # Use feature name as domain if it's reasonable
                    if len(feature_name) > 2 and feature_name.isalpha():
                        return feature_name
        
        # Default to 'ui' for component files, 'shared' for utilities
        if any(path_lower.endswith(ext) for ext in ['.tsx', '.jsx']):
            if 'component' in path_lower or 'view' in path_lower:
                return 'ui'
            elif 'util' in path_lower or 'helper' in path_lower or 'hook' in path_lower:
                return 'shared'
        
        # Last resort - try to use the most specific directory
        for part in reversed(path_parts[:-1]):  # Exclude filename
            if part.lower() not in ['src', 'client', 'app', 'lib', 'dist', 'build', 'node_modules']:
                if len(part) > 2 and not part.startswith('.'):
                    return part.lower()
        
        return 'misc'  # Only if no pattern matches

    def _aggregate_frontend_files(self) -> List[Dict]:
        """
        Crucial Fix: Aggregate frontend files from all possible sources.
        Prioritizes Extraction Results (real-time), then Master Mapping (static).
        """
        frontend_files = {} # Key by file path to deduplicate

        # Source 1: Extraction Results (The most accurate source of what was processed)
        services = self.extraction_results.get('services', [])
        for service in services:
            # Check explicit platform flag or file extension
            is_frontend = service.get('platform') == 'frontend'
            if not is_frontend:
                fname = str(service.get('file', '')).lower()
                if any(fname.endswith(ext) for ext in ['.tsx', '.ts', '.jsx', '.js']) and '_service.py' not in fname:
                    is_frontend = True
            
            if is_frontend:
                file_path = service.get('file')
                if file_path:
                    frontend_files[file_path] = {
                        'file': file_path,
                        'name': Path(file_path).name,
                        'domain': service.get('domain') or self._infer_domain_from_path(file_path),
                        'type': service.get('file_type') or 'component',
                        'target': service.get('target') or '',
                        'source': 'extraction'
                    }

        # Source 2: Master Mapping (Fill in gaps)
        mapping = self.master_mapping.get('mappings', {})
        for file_path, info in mapping.items():
            if info.get('platform') == 'frontend':
                # Normalize path
                if file_path not in frontend_files:
                    frontend_files[file_path] = {
                        'file': file_path,
                        'name': Path(file_path).name,
                        'domain': info.get('domain') or self._infer_domain_from_path(file_path),
                        'type': info.get('file_type') or 'component',
                        'target': info.get('target') or '',
                        'source': 'mapping'
                    }

        # Source 3: File Disposition (Restored with intelligent domain assignment)
        # Process files that were discovered but not yet categorized
        if self.file_disposition:
            # Try to find lists that look like files
            for category, files in self.file_disposition.items():
                if isinstance(files, list):
                    for file_path in files:
                        if any(str(file_path).endswith(ext) for ext in ['.tsx', '.ts', '.jsx', '.js']):
                            if file_path not in frontend_files:
                                # Intelligently assign domain based on path patterns
                                inferred_domain = self._infer_domain_from_path(str(file_path))
                                frontend_files[file_path] = {
                                    'file': file_path,
                                    'name': Path(file_path).name,
                                    'domain': inferred_domain,
                                    'type': 'component',
                                    'target': '',
                                    'source': 'disposition'
                                }

        print(f"📊 Aggregated {len(frontend_files)} frontend files from all sources.")
        
        # Report domain distribution for validation
        domain_counts = defaultdict(int)
        for f in frontend_files.values():
            domain_counts[f['domain']] += 1
        
        print("Domain distribution:")
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(frontend_files)) * 100 if frontend_files else 0
            print(f"  {domain}: {count} files ({percentage:.1f}%)")
        
        # Warn if too many files in misc
        misc_count = domain_counts.get('misc', 0)
        if misc_count > 0:
            misc_percentage = (misc_count / len(frontend_files)) * 100 if frontend_files else 0
            if misc_percentage > 20:
                print(f"⚠️  Warning: {misc_percentage:.1f}% of files in 'misc' domain - review domain assignment logic")
        
        return list(frontend_files.values())
    
    def generate_documentation(self) -> str:
        """Generate comprehensive migration documentation"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        doc = []
        doc.append("# MAMS Comprehensive Platform Migration Report")
        doc.append(f"\n**Generated:** {timestamp}")
        doc.append(f"**Total Frontend Files Detected:** {len(self.all_frontend_files)}")
        doc.append("---\n")
        
        # Navigation
        doc.append("## Index")
        doc.append("- [Executive Summary](#executive-summary)")
        doc.append("- [Frontend Migration Status](#frontend-migration-status)")
        doc.append("- [Backend Migration Status](#backend-migration-status)")
        doc.append("- [Detailed Component Mapping](#detailed-component-mapping)")
        doc.append("---\n")
        
        # Executive Summary
        doc.append("## Executive Summary")
        doc.append(self._generate_summary())
        
        # Frontend Section (The Priority)
        doc.append("\n## Frontend Migration Status")
        doc.append(self._generate_frontend_section())
        
        # Backend Section
        doc.append("\n## Backend Migration Status")
        doc.append(self._generate_backend_section())

        # Detailed Mapping
        doc.append("\n## Detailed Component Mapping")
        doc.append(self._generate_detailed_mapping())
        
        return '\n'.join(doc)
    
    def _generate_summary(self) -> str:
        # Calculate stats
        backend_files = sum(1 for s in self.extraction_results.get('services', []) if s.get('platform') != 'frontend')
        frontend_files = len(self.all_frontend_files)
        
        # Check for errors
        total_errors = len(self.extraction_errors.get('errors', []))
        
        summary = []
        summary.append("| Metric | Value |")
        summary.append("|--------|-------|")
        summary.append(f"| **Backend Files** | {backend_files} |")
        summary.append(f"| **Frontend Files** | {frontend_files} |")
        summary.append(f"| **Total Processed** | {backend_files + frontend_files} |")
        summary.append(f"| **Extraction Errors** | {total_errors} |")
        
        # Add completion percentage if we have mapping data
        if self.master_mapping.get('mappings'):
            total_mapped = len(self.master_mapping['mappings'])
            if total_mapped > 0:
                completion = round(((backend_files + frontend_files) / total_mapped) * 100, 2)
                summary.append(f"| **Migration Progress** | {completion}% |")
        
        return '\n'.join(summary)

    def _generate_frontend_section(self) -> str:
        if not self.all_frontend_files:
            return "\n> ⚠️ No frontend files were detected in the analysis output.\n"

        section = []
        
        # Domain Breakdown
        domain_counts = defaultdict(int)
        for f in self.all_frontend_files:
            domain = f.get('domain') or 'unknown'
            domain_counts[domain] += 1
            
        section.append("\n### Domain Breakdown")
        section.append("| Domain | Count |")
        section.append("|--------|-------|")
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
            section.append(f"| {domain} | {count} |")
            
        # Type Breakdown
        type_counts = defaultdict(int)
        for f in self.all_frontend_files:
            file_type = f.get('type') or 'unknown'
            type_counts[file_type] += 1
            
        section.append("\n### Component Type Breakdown")
        section.append("| Type | Count |")
        section.append("|------|-------|")
        for ftype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            section.append(f"| {ftype} | {count} |")
            
        # Source Breakdown to show data quality
        source_counts = defaultdict(int)
        for f in self.all_frontend_files:
            source_counts[f.get('source', 'unknown')] += 1
            
        section.append("\n### Data Source Breakdown")
        section.append("| Source | Count | Description |")
        section.append("|--------|-------|-------------|")
        for source, count in sorted(source_counts.items()):
            desc = {
                'extraction': 'Actively processed files',
                'mapping': 'From master mapping (not yet processed)',
                'disposition': 'Discovered but uncategorized'
            }.get(source, 'Unknown source')
            section.append(f"| {source} | {count} | {desc} |")
            
        return '\n'.join(section)

    def _generate_backend_section(self) -> str:
        section = []
        services = [s for s in self.extraction_results.get('services', []) if s.get('platform') != 'frontend']
        
        if not services:
            return "\n> No backend services found in extraction results.\n"
            
        section.append(f"\nFound {len(services)} backend service candidates.")
        
        # Group by extracted classes
        total_classes = sum(len(s.get('classes', [])) for s in services)
        section.append(f"- **Classes Extracted:** {total_classes}")
        
        # Domain breakdown for backend
        backend_domains = defaultdict(int)
        for s in services:
            backend_domains[s.get('domain', 'unknown')] += 1
            
        section.append("\n### Backend Domain Distribution")
        section.append("| Domain | Count |")
        section.append("|--------|-------|")
        for domain, count in sorted(backend_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
            section.append(f"| {domain} | {count} |")
            
        return '\n'.join(section)

    def _generate_detailed_mapping(self) -> str:
        section = []
        
        # BACKEND Detailed Mapping
        section.append("\n## Backend Service Mapping\n")
        backend_services = [s for s in self.extraction_results.get('services', []) 
                           if s.get('platform') != 'frontend']
        
        if backend_services:
            # Group backend by domain
            backend_by_domain = defaultdict(list)
            for service in backend_services:
                domain = service.get('domain') or 'unknown'
                backend_by_domain[domain].append(service)
            
            for domain, services in sorted(backend_by_domain.items(), 
                                          key=lambda x: (-len(x[1]), x[0])):  # Sort by count desc, then name
                section.append(f"\n### Backend Domain: {domain.upper()} ({len(services)} files)")
                section.append("| File Path | Service | Classes | Functions | Target |")
                section.append("|-----------|---------|---------|-----------|--------|")
                
                # Show ALL backend files - no truncation for validation
                for service in sorted(services, key=lambda x: x.get('file', '')):
                    file_path = service.get('file', '-')
                    service_name = service.get('service', Path(file_path).stem)
                    num_classes = len(service.get('classes', []))
                    num_functions = len(service.get('standalone_functions', []))
                    target = service.get('target', f'unified_{domain}_service')
                    
                    # Shorten path for readability
                    if len(file_path) > 60:
                        file_path = "..." + file_path[-57:]
                    
                    section.append(f"| {file_path} | {service_name} | {num_classes} | {num_functions} | {target} |")
        else:
            section.append("No backend services found in extraction results.")
        
        # FRONTEND Detailed Mapping
        section.append("\n## Frontend Component Mapping\n")
        
        if not self.all_frontend_files:
            section.append("No frontend mapping data available.")
        else:
            # Group by Domain
            by_domain = defaultdict(list)
            for f in self.all_frontend_files:
                # Handle None or missing domains
                domain = f.get('domain') or 'unknown'
                by_domain[domain].append(f)
                
            # Sort domains, handling any edge cases
            for domain, files in sorted(by_domain.items(), 
                                       key=lambda x: (-len(x[1]), x[0] or '')):  # Sort by count desc, then name
                section.append(f"\n### Frontend Domain: {domain.upper()} ({len(files)} files)")
                section.append("| File Name | Type | Target Path | Source |")
                section.append("|-----------|------|-------------|--------|")
                
                # Show ALL files - no truncation for validation
                for f in sorted(files, key=lambda x: x['name']):
                    name = f['name']
                    ftype = f['type']
                    target = f['target'] if f['target'] else '-'
                    src = f['source']
                    section.append(f"| {name} | {ftype} | {target} | {src} |")
                
        return '\n'.join(section)

    def publish(self):
        """Generate and save documentation"""
        try:
            doc_content = self.generate_documentation()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            main_report = self.docs_dir / f"MAMS_Migration_Report_{timestamp}.md"
            
            with open(main_report, 'w') as f:
                f.write(doc_content)
            
            # Create latest link
            latest = self.docs_dir / "MAMS_Migration_Report_Latest.md"
            if latest.exists():
                latest.unlink()
            try:
                latest.symlink_to(main_report.name)
            except OSError:
                # Fallback if symlinks aren't supported
                with open(latest, 'w') as f:
                    f.write(doc_content)
            
            print(f"\n✅ Documentation generated successfully!")
            print(f"   Path: {main_report}")
            print(f"   Frontend Files Found: {len(self.all_frontend_files)}")
            return str(main_report)
            
        except Exception as e:
            print(f"❌ Error generating documentation: {e}")
            import traceback
            traceback.print_exc()
            return None

def generate_and_publish_docs():
    generator = DocumentationGenerator()
    return generator.publish()

if __name__ == "__main__":
    generate_and_publish_docs()