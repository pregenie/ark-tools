#!/usr/bin/env python3
"""
Enhanced Unified Service Generator with Merge Capabilities
Safely generates unified services with version control and merge support
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import difflib
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Service consolidation mapping
CONSOLIDATION_MAP = {
    'auth': ['user_service', 'permission_service', 'role_service', 'session_service'],
    'data': ['database_service', 'cache_service', 'query_service', 'orm_service'],
    'api': ['rest_service', 'graphql_service', 'websocket_service', 'grpc_service'],
    'messaging': ['email_service', 'sms_service', 'notification_service', 'chat_service'],
    'storage': ['file_service', 's3_service', 'blob_service', 'media_service'],
    'ai': ['ml_service', 'nlp_service', 'vision_service', 'recommendation_service'],
    'analytics': ['metrics_service', 'reporting_service', 'tracking_service', 'audit_service'],
    'workflow': ['orchestration_service', 'pipeline_service', 'task_service', 'scheduler_service']
}


class EnhancedUnifiedGenerator:
    """Enhanced generator with merge and versioning capabilities"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.base_output_dir = Path('/app/.mams_output')
        self.version = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = self.base_output_dir / f'v_{self.version}'
        self.metadata_file = self.base_output_dir / 'mams_metadata.json'
        self.metadata = self.load_metadata()
        
    def load_metadata(self) -> Dict[str, Any]:
        """Load MAMS metadata tracking file changes and versions"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            'versions': [],
            'file_hashes': {},
            'last_run': None,
            'merge_history': []
        }
    
    def save_metadata(self):
        """Save updated metadata"""
        if not self.dry_run:
            self.base_output_dir.mkdir(exist_ok=True)
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
    
    def get_file_hash(self, content: str) -> str:
        """Generate hash of file content for change detection"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def detect_changes(self, file_path: str, new_content: str) -> Dict[str, Any]:
        """Detect if file has changed since last generation"""
        new_hash = self.get_file_hash(new_content)
        old_hash = self.metadata['file_hashes'].get(file_path)
        
        existing_file = Path(file_path)
        has_manual_edits = False
        
        if existing_file.exists() and old_hash:
            current_content = existing_file.read_text()
            current_hash = self.get_file_hash(current_content)
            has_manual_edits = current_hash != old_hash
        
        return {
            'changed': new_hash != old_hash,
            'has_manual_edits': has_manual_edits,
            'old_hash': old_hash,
            'new_hash': new_hash
        }
    
    def merge_code(self, existing_content: str, new_content: str, file_path: str) -> str:
        """Intelligently merge existing code with new generated code"""
        # Parse existing code to find manual additions
        existing_lines = existing_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Look for MAMS markers
        start_marker = "# === MAMS GENERATED CODE START ==="
        end_marker = "# === MAMS GENERATED CODE END ==="
        manual_marker = "# === MANUAL CODE START ==="
        manual_end = "# === MANUAL CODE END ==="
        
        merged_lines = []
        
        # If markers exist, preserve manual sections
        if start_marker in existing_content:
            in_manual = False
            manual_sections = []
            
            for line in existing_lines:
                if manual_marker in line:
                    in_manual = True
                    manual_sections.append([])
                elif manual_end in line:
                    in_manual = False
                elif in_manual and manual_sections:
                    manual_sections[-1].append(line)
            
            # Build merged content with preserved manual sections
            merged_lines.append("# Enhanced by MAMS - Merged on " + datetime.now().isoformat())
            merged_lines.extend(new_lines)
            
            # Add preserved manual sections at the end
            if manual_sections:
                merged_lines.append("\n" + manual_marker)
                for section in manual_sections:
                    merged_lines.extend(section)
                merged_lines.append(manual_end)
        else:
            # No markers, use diff-based merge
            differ = difflib.unified_diff(
                new_lines, existing_lines,
                fromfile=f'{file_path}.generated',
                tofile=f'{file_path}.existing',
                lineterm=''
            )
            
            # If files are significantly different, create a merged version
            diff_lines = list(differ)
            if len(diff_lines) > len(new_lines) * 0.3:  # >30% different
                # Significant changes, keep both versions in the file
                merged_lines = [
                    f"# MAMS Merge - {datetime.now().isoformat()}",
                    "# Significant differences detected, manual review required",
                    "",
                    start_marker,
                ] + new_lines + [
                    end_marker,
                    "",
                    manual_marker,
                    "# Original code preserved below - merge manually",
                ] + existing_lines + [
                    manual_end
                ]
            else:
                # Minor changes, use the new version
                merged_lines = new_lines
        
        return '\n'.join(merged_lines)
    
    def generate_unified_service(self, group_name: str, legacy_services: List[str]) -> str:
        """Generate unified service code with proper structure"""
        class_name = f"Unified{group_name.capitalize()}Service"
        
        code = f'''#!/usr/bin/env python3
"""
Unified {group_name.capitalize()} Service
Generated by MAMS on {datetime.now().isoformat()}
Consolidates: {', '.join(legacy_services)}
"""

from typing import Optional, List, Dict, Any
import logging
from arkyvus.services.unified.base import UnifiedServiceBase

logger = logging.getLogger(__name__)

# === MAMS GENERATED CODE START ===

class {class_name}(UnifiedServiceBase):
    """
    Unified service consolidating all {group_name} functionality.
    This service replaces: {', '.join(legacy_services)}
    """
    
    def __init__(self):
        super().__init__(service_name="{group_name}")
        self.legacy_compatibility = True
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all consolidated components"""
'''
        
        # Add methods for each legacy service
        for service in legacy_services:
            service_base = service.replace('_service', '')
            code += f'''
    # === {service} functionality ===
    
    async def {service_base}_operation(self, *args, **kwargs) -> Any:
        """Legacy {service} operation - TO BE IMPLEMENTED"""
        # TODO: Migrate logic from {service}
        raise NotImplementedError(f"{{self.__class__.__name__}}.{service_base}_operation not yet migrated")
'''
        
        code += '''
    # === Common operations ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all consolidated services"""
        return {
            "service": self.service_name,
            "status": "healthy",
            "consolidated_services": ''' + str(legacy_services) + '''
        }

# === MAMS GENERATED CODE END ===

# === MANUAL CODE START ===
# Add your custom code here - it will be preserved during regeneration
# === MANUAL CODE END ===
'''
        return code
    
    def write_service_file(self, group_name: str, content: str, force: bool = False) -> Dict[str, Any]:
        """Write service file with proper versioning and backup"""
        # Determine paths
        service_filename = f"{group_name}_service.py"
        versioned_path = self.output_dir / service_filename
        current_path = Path(f'/app/arkyvus/services/unified/{service_filename}')
        
        result = {
            'group': group_name,
            'versioned_path': str(versioned_path),
            'current_path': str(current_path),
            'action': None,
            'backup_path': None
        }
        
        # Check for changes
        changes = self.detect_changes(str(current_path), content)
        
        if self.dry_run:
            result['action'] = 'dry_run'
            if current_path.exists():
                if changes['has_manual_edits']:
                    result['action'] = 'would_merge'
                elif changes['changed']:
                    result['action'] = 'would_update'
                else:
                    result['action'] = 'unchanged'
            else:
                result['action'] = 'would_create'
            
            print(f"  [DRY RUN] {result['action']}: {service_filename}")
            return result
        
        # Create versioned output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Always write to versioned directory
        with open(versioned_path, 'w') as f:
            f.write(content)
        result['action'] = 'generated_version'
        
        # Handle existing file
        if current_path.exists():
            existing_content = current_path.read_text()
            
            if changes['has_manual_edits'] and not force:
                # Merge required
                merged_content = self.merge_code(existing_content, content, str(current_path))
                merge_path = self.output_dir / f"{group_name}_service_merged.py"
                with open(merge_path, 'w') as f:
                    f.write(merged_content)
                result['action'] = 'merged'
                result['merge_path'] = str(merge_path)
                print(f"  ✓ Merged with manual edits: {merge_path}")
                
                # Create backup
                backup_path = self.output_dir / f"{group_name}_service_backup.py"
                shutil.copy2(current_path, backup_path)
                result['backup_path'] = str(backup_path)
                
            elif changes['changed']:
                # Create backup before updating
                backup_path = self.output_dir / f"{group_name}_service_backup.py"
                shutil.copy2(current_path, backup_path)
                result['backup_path'] = str(backup_path)
                result['action'] = 'updated'
                print(f"  ✓ Updated (backup at {backup_path})")
            else:
                result['action'] = 'unchanged'
                print(f"  - Unchanged: {service_filename}")
        else:
            result['action'] = 'created'
            print(f"  ✓ Created new: {service_filename}")
        
        # Update metadata
        self.metadata['file_hashes'][str(current_path)] = self.get_file_hash(content)
        
        return result
    
    def generate_all(self, groups: List[str] = None, force: bool = False) -> List[Dict[str, Any]]:
        """Generate all unified services with proper tracking"""
        if groups is None:
            groups = list(CONSOLIDATION_MAP.keys())
        
        results = []
        
        print(f"\n{'='*60}")
        print(f"MAMS Enhanced Generator - Version {self.version}")
        print(f"Output Directory: {self.output_dir}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'ACTIVE'}")
        print(f"{'='*60}\n")
        
        for group_name in groups:
            if group_name not in CONSOLIDATION_MAP:
                print(f"⚠️  Unknown group: {group_name}")
                continue
            
            legacy_services = CONSOLIDATION_MAP[group_name]
            print(f"\n[{group_name.upper()}] Processing {len(legacy_services)} services...")
            
            # Generate code
            service_code = self.generate_unified_service(group_name, legacy_services)
            
            # Write file with versioning
            result = self.write_service_file(group_name, service_code, force)
            results.append(result)
        
        # Update metadata
        self.metadata['last_run'] = datetime.now().isoformat()
        self.metadata['versions'].append({
            'version': self.version,
            'timestamp': datetime.now().isoformat(),
            'groups': groups,
            'results': results
        })
        self.save_metadata()
        
        # Generate summary report
        self.generate_summary(results)
        
        return results
    
    def generate_summary(self, results: List[Dict[str, Any]]):
        """Generate summary report of the generation run"""
        summary_path = self.output_dir / 'MAMS_SUMMARY.md'
        
        if self.dry_run:
            return
        
        with open(summary_path, 'w') as f:
            f.write(f"# MAMS Generation Summary\n\n")
            f.write(f"**Version:** {self.version}\n")
            f.write(f"**Date:** {datetime.now().isoformat()}\n")
            f.write(f"**Output Directory:** `{self.output_dir}`\n\n")
            
            f.write("## Results\n\n")
            
            created = [r for r in results if r['action'] == 'created']
            updated = [r for r in results if r['action'] == 'updated']
            merged = [r for r in results if r['action'] == 'merged']
            unchanged = [r for r in results if r['action'] == 'unchanged']
            
            f.write(f"- **Created:** {len(created)} new services\n")
            f.write(f"- **Updated:** {len(updated)} services\n")
            f.write(f"- **Merged:** {len(merged)} services (manual review required)\n")
            f.write(f"- **Unchanged:** {len(unchanged)} services\n\n")
            
            if merged:
                f.write("## ⚠️ Manual Review Required\n\n")
                f.write("The following services have manual edits and require review:\n\n")
                for r in merged:
                    f.write(f"- `{r['group']}_service.py`\n")
                    f.write(f"  - Merged file: `{r.get('merge_path', 'N/A')}`\n")
                    f.write(f"  - Backup: `{r.get('backup_path', 'N/A')}`\n\n")
            
            f.write("## Next Steps\n\n")
            f.write("1. Review generated services in the versioned output directory\n")
            f.write("2. For merged files, manually review and integrate changes\n")
            f.write("3. Copy reviewed files to the main service directory\n")
            f.write("4. Run tests to ensure compatibility\n")
            f.write("5. Commit changes with reference to this version\n")
        
        print(f"\n📄 Summary report: {summary_path}")


def main():
    """Main entry point for enhanced generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced MAMS Unified Service Generator")
    parser.add_argument('--group', '-g', dest='groups', action='append',
                       help='Specific group to generate (can be used multiple times)')
    parser.add_argument('--all', action='store_true',
                       help='Generate all groups')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without writing files')
    parser.add_argument('--force', action='store_true',
                       help='Force overwrite even with manual edits')
    
    args = parser.parse_args()
    
    # Determine which groups to generate
    if args.all or not args.groups:
        groups = None  # Generate all
    else:
        groups = args.groups
    
    # Create generator
    generator = EnhancedUnifiedGenerator(dry_run=args.dry_run)
    
    # Generate services
    results = generator.generate_all(groups=groups, force=args.force)
    
    # Print summary
    print("\n" + "="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    
    if not args.dry_run:
        print(f"✅ Generated {len(results)} services")
        print(f"📁 Output directory: {generator.output_dir}")
        print("\nRun with --dry-run to preview changes without writing files")
    else:
        print("DRY RUN COMPLETE - No files were modified")
        print("Remove --dry-run to apply changes")


if __name__ == "__main__":
    main()