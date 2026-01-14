#!/usr/bin/env python3
"""
MAMS Migration Documentation Generator - Robust Version
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
                        'domain': service.get('domain', 'misc'),
                        'type': service.get('file_type', 'component'),
                        'target': service.get('target', ''),
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
                        'domain': info.get('domain', 'misc'),
                        'type': info.get('file_type', 'component'),
                        'target': info.get('target', ''),
                        'source': 'mapping'
                    }

        # Source 3: File Disposition (Last resort)
        # Often file_disposition just has strings, so we infer metadata
        if self.file_disposition:
            # Try to find lists that look like files
            for category, files in self.file_disposition.items():
                if isinstance(files, list):
                    for file_path in files:
                        if any(str(file_path).endswith(ext) for ext in ['.tsx', '.ts', '.jsx', '.js']):
                            if file_path not in frontend_files:
                                frontend_files[file_path] = {
                                    'file': file_path,
                                    'name': Path(file_path).name,
                                    'domain': 'misc', # Unknown
                                    'type': 'component',
                                    'target': '',
                                    'source': 'disposition'
                                }

        print(f"📊 Aggregated {len(frontend_files)} frontend files from all sources.")
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

        # Detailed Mapping - Shows ALL files
        doc.append("\n## Detailed Component Mapping")
        doc.append(self._generate_detailed_mapping())
        
        return '\n'.join(doc)
    
    def _generate_summary(self) -> str:
        # Calculate stats
        backend_files = sum(1 for s in self.extraction_results.get('services', []) if s.get('platform') != 'frontend')
        frontend_files = len(self.all_frontend_files)
        
        summary = []
        summary.append("| Metric | Value |")
        summary.append("|--------|-------|")
        summary.append(f"| **Backend Files** | {backend_files} |")
        summary.append(f"| **Frontend Files** | {frontend_files} |")
        summary.append(f"| **Total Processed** | {backend_files + frontend_files} |")
        return '\n'.join(summary)

    def _generate_frontend_section(self) -> str:
        if not self.all_frontend_files:
            return "\n> ⚠️ No frontend files were detected in the analysis output.\n"

        section = []
        
        # Domain Breakdown
        domain_counts = defaultdict(int)
        for f in self.all_frontend_files:
            domain_counts[f['domain']] += 1
            
        section.append("\n### Domain Breakdown")
        section.append("| Domain | Count |")
        section.append("|--------|-------|")
        for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
            section.append(f"| {domain} | {count} |")
            
        # Type Breakdown
        type_counts = defaultdict(int)
        for f in self.all_frontend_files:
            type_counts[f['type']] += 1
            
        section.append("\n### Component Type Breakdown")
        section.append("| Type | Count |")
        section.append("|------|-------|")
        for ftype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            section.append(f"| {ftype} | {count} |")
            
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
        
        return '\n'.join(section)

    def _generate_detailed_mapping(self) -> str:
        section = []
        
        if not self.all_frontend_files:
            return "No frontend mapping data available."

        # Group by Domain
        by_domain = defaultdict(list)
        for f in self.all_frontend_files:
            by_domain[f['domain']].append(f)
            
        for domain, files in sorted(by_domain.items()):
            section.append(f"\n### Domain: {domain.upper()} ({len(files)} files)")
            section.append("| File Path | File Name | Target Path | Source |")
            section.append("|-----------|-----------|-------------|--------|")
            
            # Show ALL files - no truncation for validation
            for f in sorted(files, key=lambda x: x['name']):
                path = f['file']
                name = f['name']
                target = f['target'] if f['target'] else '-'
                src = f['source']
                section.append(f"| {path} | {name} | {target} | {src} |")
                
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
            print(f"   path: {main_report}")
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