#!/usr/bin/env python3
"""
MAMS-017: Frontend Orchestrator Integration
Integrates all frontend alignment components with existing MAMS orchestrator
"""

import os
import json
import asyncio
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

# Add parent paths for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from arkyvus.utils.debug_logger import debug_log
from arkyvus.migrations.mams_013_typescript_ast_parser import TypeScriptASTParser
from arkyvus.migrations.mams_014_enhanced_frontend_analyzer import EnhancedFrontendAnalyzer
from arkyvus.migrations.mams_015_dependency_validator import (
    FrontendDependencyValidator, MigrationMove
)
from arkyvus.migrations.mams_016_import_rewriter import ImportRewriter, FileMove

@dataclass
class FrontendMigrationPlan:
    """Complete frontend migration plan"""
    timestamp: str
    total_files: int
    classifications: List[Any]
    file_moves: List[FileMove]
    domain_distribution: Dict[str, int]
    confidence_distribution: Dict[str, int]
    review_required: List[str]
    validation_report: Any
    import_rewrite_plan: Any
    state_file: str = '.migration/frontend_migration_state.json'

@dataclass
class MigrationState:
    """Track migration state for idempotency"""
    completed_moves: List[str]
    failed_moves: List[str]  
    import_updates_applied: List[str]
    rollback_data: Dict[str, str]  # new_path -> original_path
    last_checkpoint: str
    

class FrontendMigrationOrchestrator:
    """
    Complete orchestrator for frontend migration
    Integrates with existing MAMS system
    """
    
    def __init__(self):
        self.ts_parser = TypeScriptASTParser()
        self.analyzer = EnhancedFrontendAnalyzer()
        self.validator = FrontendDependencyValidator()
        self.rewriter = ImportRewriter()
        self.state = self._load_state()
        self.migration_dir = Path('/app/.migration')
        self.migration_dir.mkdir(exist_ok=True)
        
    def _load_state(self) -> MigrationState:
        """Load migration state for idempotency"""
        state_file = Path('.migration/frontend_migration_state.json')
        
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                return MigrationState(**data)
            except Exception as e:
                debug_log.error_trace("Failed to load migration state", exception=e)
        
        return MigrationState(
            completed_moves=[],
            failed_moves=[],
            import_updates_applied=[],
            rollback_data={},
            last_checkpoint=datetime.now().isoformat()
        )
    
    def _save_state(self):
        """Save migration state"""
        state_file = Path('.migration/frontend_migration_state.json')
        state_file.parent.mkdir(exist_ok=True)
        
        state_data = {
            'completed_moves': self.state.completed_moves,
            'failed_moves': self.state.failed_moves,
            'import_updates_applied': self.state.import_updates_applied,
            'rollback_data': self.state.rollback_data,
            'last_checkpoint': self.state.last_checkpoint
        }
        
        state_file.write_text(json.dumps(state_data, indent=2))
    
    async def analyze_frontend(self, confidence_threshold: float = 0.7) -> FrontendMigrationPlan:
        """
        Complete frontend analysis with all enhancements
        """
        # Suppress AMQP/RabbitMQ errors that aren't relevant
        import logging
        logging.getLogger('pika').setLevel(logging.WARNING)
        logging.getLogger('pika.adapters').setLevel(logging.WARNING)
        logging.getLogger('pika.connection').setLevel(logging.WARNING)
        
        debug_log.api("Starting enhanced frontend analysis", level="INFO")
        
        # Get all frontend files
        frontend_files = self._get_frontend_files()
        debug_log.api(f"Found {len(frontend_files)} frontend files", level="INFO")
        
        # Analyze files with progress tracking and batching
        classifications = []
        review_required = []
        
        total = len(frontend_files)
        batch_size = 50  # Process in smaller batches to avoid overwhelming system
        
        print(f"\nAnalyzing {total} frontend files in batches of {batch_size}...")
        
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch = frontend_files[batch_start:batch_end]
            
            # Show progress
            progress = (batch_start / total) * 100
            print(f"  Progress: {batch_start}/{total} files ({progress:.1f}%)", end='\r')
            
            # Process batch
            for file_path in batch:
                try:
                    result = await self.analyzer.analyze_file(file_path)
                    classifications.append(result)
                    
                    if result.requires_review:
                        review_required.append(str(file_path))
                        
                except Exception as e:
                    # Don't stop on individual file errors
                    debug_log.api(f"Skipped {file_path.name}: {str(e)}", level="WARNING")
                    continue
        
        print(f"  Progress: {total}/{total} files (100.0%)  ")
        
        # Build dependency graph
        graph = await self.validator.build_dependency_graph(classifications)
        
        # Validate current state
        validation_report = self.validator.validate_current_state()
        
        # Generate file moves based on classifications
        file_moves = self._generate_file_moves(classifications)
        
        # Create import rewrite plan
        import_rewrite_plan = await self.rewriter.create_rewrite_plan(file_moves)
        
        # Calculate statistics
        domain_dist = {}
        confidence_dist = {'high': 0, 'medium': 0, 'low': 0}
        
        for cls in classifications:
            domain_dist[cls.primary_domain] = domain_dist.get(cls.primary_domain, 0) + 1
            
            if cls.confidence >= 0.8:
                confidence_dist['high'] += 1
            elif cls.confidence >= 0.6:
                confidence_dist['medium'] += 1
            else:
                confidence_dist['low'] += 1
        
        return FrontendMigrationPlan(
            timestamp=datetime.now().isoformat(),
            total_files=len(frontend_files),
            classifications=classifications,
            file_moves=file_moves,
            domain_distribution=domain_dist,
            confidence_distribution=confidence_dist,
            review_required=review_required,
            validation_report=validation_report,
            import_rewrite_plan=import_rewrite_plan
        )
    
    def _get_frontend_files(self) -> List[Path]:
        """Get all frontend TypeScript/React files"""
        frontend_dirs = [
            Path('/app/client/src'),
            Path('/Users/pregenie/Development/arkyvus_project/client/src'),
            Path('./client/src')  # Add relative path option
        ]
        
        files = []
        for frontend_dir in frontend_dirs:
            if frontend_dir.exists():
                print(f"Found frontend directory: {frontend_dir}")
                for ext in ['*.tsx', '*.ts']:
                    matching = list(frontend_dir.rglob(ext))
                    files.extend(matching)
                    print(f"  Found {len(matching)} {ext} files")
                break
        else:
            print("WARNING: No frontend directory found!")
            print(f"  Checked: {[str(d) for d in frontend_dirs]}")
        
        # Filter out test files and node_modules
        filtered = []
        for f in files:
            path_str = str(f)
            if 'node_modules' not in path_str and '.test.' not in path_str and '.spec.' not in path_str:
                filtered.append(f)
        
        return filtered
    
    def _generate_file_moves(self, classifications: List[Any]) -> List[FileMove]:
        """Generate file moves based on domain classifications"""
        moves = []
        
        for cls in classifications:
            # Only move files with high confidence
            if cls.confidence < 0.7:
                continue
            
            # Skip files already in correct location
            current_path = Path(cls.file_path)
            if f'/domains/{cls.primary_domain}/' in str(current_path):
                continue
            
            # Generate target path
            target_path = self._calculate_target_path(current_path, cls.primary_domain)
            
            if target_path and target_path != current_path:
                moves.append(FileMove(
                    from_path=str(current_path),
                    to_path=str(target_path),
                    from_domain=cls.base_classification.get('domain', 'unknown'),
                    to_domain=cls.primary_domain
                ))
        
        return moves
    
    def _calculate_target_path(self, current_path: Path, domain: str) -> Optional[Path]:
        """Calculate target path for domain organization"""
        # Get base client directory
        path_str = str(current_path)
        
        if '/client/src/' in path_str:
            base_dir = path_str.split('/client/src/')[0] + '/client/src'
        else:
            return None
        
        # Get relative path from src
        rel_path = current_path.relative_to(Path(base_dir))
        
        # Determine subdirectory based on file type
        file_name = current_path.name
        
        if 'component' in file_name.lower() or current_path.suffix == '.tsx':
            subdir = 'components'
        elif 'service' in file_name.lower() or 'api' in file_name.lower():
            subdir = 'services'  
        elif 'hook' in file_name.lower() or file_name.startswith('use'):
            subdir = 'hooks'
        elif 'context' in file_name.lower():
            subdir = 'contexts'
        elif 'util' in file_name.lower() or 'helper' in file_name.lower():
            subdir = 'utils'
        elif 'type' in file_name.lower() or '.d.ts' in file_name:
            subdir = 'types'
        else:
            subdir = 'misc'
        
        # Build target path
        target = Path(base_dir) / 'domains' / domain / subdir / file_name
        
        return target
    
    async def execute_migration(self, plan: FrontendMigrationPlan, 
                              dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute the frontend migration plan
        """
        debug_log.api(f"Executing migration plan (dry_run={dry_run})", level="INFO")
        
        results = {
            'files_moved': 0,
            'imports_updated': 0,
            'errors': [],
            'rollback_data': {}
        }
        
        if dry_run:
            debug_log.api("DRY RUN MODE - No files will be modified", level="INFO")
            return self._simulate_migration(plan)
        
        # Create checkpoint
        checkpoint_id = self._create_checkpoint()
        
        try:
            # Phase 1: Move files
            debug_log.api("Phase 1: Moving files", level="INFO")
            for move in plan.file_moves:
                # Skip if already completed (idempotency)
                move_id = f"{move.from_path}->{move.to_path}"
                if move_id in self.state.completed_moves:
                    continue
                
                try:
                    self._move_file(move)
                    results['files_moved'] += 1
                    results['rollback_data'][move.to_path] = move.from_path
                    self.state.completed_moves.append(move_id)
                    self.state.rollback_data[move.to_path] = move.from_path
                    
                except Exception as e:
                    debug_log.error_trace(f"Failed to move {move.from_path}", exception=e)
                    results['errors'].append(str(e))
                    self.state.failed_moves.append(move_id)
            
            # Save state after moves
            self._save_state()
            
            # Phase 2: Update imports
            debug_log.api("Phase 2: Updating imports", level="INFO")
            import_results = await self.rewriter.apply_updates(plan.import_rewrite_plan)
            results['imports_updated'] = import_results['imports_updated']
            results['errors'].extend(import_results.get('errors', []))
            
            # Phase 3: Validate
            debug_log.api("Phase 3: Validating migration", level="INFO")
            validation = await self._validate_migration(plan)
            
            if not validation['is_valid']:
                raise Exception(f"Migration validation failed: {validation['errors']}")
            
            debug_log.api("Migration completed successfully", level="INFO")
            
        except Exception as e:
            debug_log.error_trace("Migration failed, initiating rollback", exception=e)
            await self.rollback(checkpoint_id)
            raise
        
        return results
    
    def _create_checkpoint(self) -> str:
        """Create a checkpoint for rollback"""
        checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_dir = self.migration_dir / f'checkpoint_{checkpoint_id}'
        checkpoint_dir.mkdir(exist_ok=True)
        
        # Save current state
        state_file = checkpoint_dir / 'state.json'
        state_file.write_text(json.dumps({
            'checkpoint_id': checkpoint_id,
            'timestamp': datetime.now().isoformat(),
            'state': {
                'completed_moves': self.state.completed_moves,
                'rollback_data': self.state.rollback_data
            }
        }, indent=2))
        
        self.state.last_checkpoint = checkpoint_id
        self._save_state()
        
        return checkpoint_id
    
    def _move_file(self, move: FileMove):
        """Execute a single file move"""
        source = Path(move.from_path)
        target = Path(move.to_path)
        
        # Create target directory
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(source), str(target))
        
        # Move associated files (tests, styles, etc.)
        self._move_associated_files(source, target)
    
    def _move_associated_files(self, source: Path, target: Path):
        """Move associated test files, styles, etc."""
        source_dir = source.parent
        source_stem = source.stem
        
        # Patterns for associated files
        patterns = [
            f"{source_stem}.test.*",
            f"{source_stem}.spec.*",
            f"{source_stem}.module.*",
            f"{source_stem}.css",
            f"{source_stem}.scss",
            f"{source_stem}.styles.*"
        ]
        
        for pattern in patterns:
            for associated in source_dir.glob(pattern):
                target_file = target.parent / associated.name
                try:
                    shutil.move(str(associated), str(target_file))
                    debug_log.api(f"Moved associated file: {associated.name}", level="DEBUG")
                except Exception as e:
                    debug_log.error_trace(f"Failed to move associated file {associated}", exception=e)
    
    def _simulate_migration(self, plan: FrontendMigrationPlan) -> Dict[str, Any]:
        """Simulate migration without making changes"""
        results = {
            'files_to_move': len(plan.file_moves),
            'imports_to_update': plan.import_rewrite_plan.total_updates,
            'domains': plan.domain_distribution,
            'review_required': len(plan.review_required),
            'validation': {
                'is_valid': plan.validation_report.is_valid,
                'violations': len(plan.validation_report.domain_violations),
                'cycles': len(plan.validation_report.cyclic_dependencies)
            }
        }
        
        # Show sample moves
        results['sample_moves'] = []
        for move in plan.file_moves[:5]:
            results['sample_moves'].append({
                'from': move.from_path,
                'to': move.to_path,
                'domain': move.to_domain
            })
        
        return results
    
    async def _validate_migration(self, plan: FrontendMigrationPlan) -> Dict[str, Any]:
        """Validate migration was successful"""
        validation = {
            'is_valid': True,
            'errors': []
        }
        
        # Check all files exist in new locations
        for move in plan.file_moves:
            if not Path(move.to_path).exists():
                validation['is_valid'] = False
                validation['errors'].append(f"File not found: {move.to_path}")
        
        # Validate imports
        affected_files = list(plan.import_rewrite_plan.affected_files)
        import_errors = await self.rewriter.validate_imports(affected_files)
        
        if import_errors:
            validation['is_valid'] = False
            validation['errors'].extend([f"Import error in {f}: {e}" 
                                        for f, errors in import_errors.items() 
                                        for e in errors])
        
        return validation
    
    async def rollback(self, checkpoint_id: str):
        """Rollback migration to checkpoint"""
        debug_log.api(f"Rolling back to checkpoint {checkpoint_id}", level="WARNING")
        
        # Load checkpoint
        checkpoint_dir = self.migration_dir / f'checkpoint_{checkpoint_id}'
        if not checkpoint_dir.exists():
            raise Exception(f"Checkpoint {checkpoint_id} not found")
        
        state_file = checkpoint_dir / 'state.json'
        checkpoint_data = json.loads(state_file.read_text())
        
        # Restore files
        rollback_data = checkpoint_data['state']['rollback_data']
        for new_path, original_path in rollback_data.items():
            if Path(new_path).exists():
                try:
                    # Move back to original location
                    Path(original_path).parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(new_path, original_path)
                    debug_log.api(f"Rolled back: {new_path} -> {original_path}", level="INFO")
                except Exception as e:
                    debug_log.error_trace(f"Failed to rollback {new_path}", exception=e)
        
        # Reset state
        self.state.completed_moves = checkpoint_data['state']['completed_moves']
        self.state.rollback_data = {}
        self._save_state()
        
        debug_log.api("Rollback completed", level="INFO")
    
    async def generate_review_ui(self, plan: FrontendMigrationPlan) -> str:
        """Generate interactive review UI for low-confidence classifications"""
        from arkyvus.migrations.mams_018_review_ui_generator import ReviewUIGenerator
        
        generator = ReviewUIGenerator()
        ui_path = await generator.generate_review_interface(
            plan.classifications,
            plan.validation_report
        )
        
        return ui_path
    
    def generate_migration_report(self, plan: FrontendMigrationPlan) -> str:
        """Generate comprehensive migration report"""
        report = []
        report.append("# Frontend Migration Report")
        report.append(f"Generated: {plan.timestamp}\n")
        
        report.append("## Summary")
        report.append(f"- Total Files: {plan.total_files}")
        report.append(f"- Files to Move: {len(plan.file_moves)}")
        report.append(f"- Review Required: {len(plan.review_required)}")
        report.append(f"- Import Updates: {plan.import_rewrite_plan.total_updates}\n")
        
        report.append("## Domain Distribution")
        for domain, count in sorted(plan.domain_distribution.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {domain}: {count} files")
        
        report.append("\n## Confidence Distribution")
        for level, count in plan.confidence_distribution.items():
            report.append(f"- {level}: {count} files")
        
        report.append("\n## Validation Results")
        report.append(f"- Valid: {plan.validation_report.is_valid}")
        report.append(f"- Domain Violations: {len(plan.validation_report.domain_violations)}")
        report.append(f"- Circular Dependencies: {len(plan.validation_report.cyclic_dependencies)}")
        report.append(f"- Can Proceed: {plan.validation_report.can_proceed_with_warnings}")
        
        if plan.validation_report.domain_violations:
            report.append("\n### Domain Violations (Top 10)")
            for v in plan.validation_report.domain_violations[:10]:
                report.append(f"- [{v.severity}] {v.description}")
        
        if plan.validation_report.cyclic_dependencies:
            report.append("\n### Circular Dependencies")
            for c in plan.validation_report.cyclic_dependencies[:5]:
                report.append(f"- {c.description}")
        
        report.append("\n## Files Requiring Review")
        for file in plan.review_required[:20]:
            report.append(f"- {file}")
        
        if len(plan.review_required) > 20:
            report.append(f"... and {len(plan.review_required) - 20} more")
        
        return '\n'.join(report)


# Integration with existing MAMS orchestrator
def integrate_with_mams_orchestrator():
    """
    Function to be called from existing MAMS orchestrator
    """
    async def process_frontend_enhanced():
        orchestrator = FrontendMigrationOrchestrator()
        
        # Analyze
        plan = await orchestrator.analyze_frontend()
        
        # Generate report
        report = orchestrator.generate_migration_report(plan)
        report_path = Path('/app/.migration/frontend_migration_report.md')
        report_path.write_text(report)
        
        # Generate review UI if needed
        if plan.review_required:
            ui_path = await orchestrator.generate_review_ui(plan)
            debug_log.api(f"Review UI generated: {ui_path}", level="INFO")
        
        return {
            'plan': plan,
            'report_path': str(report_path),
            'statistics': {
                'total_files': plan.total_files,
                'moves_planned': len(plan.file_moves),
                'review_required': len(plan.review_required),
                'is_valid': plan.validation_report.is_valid
            }
        }
    
    return process_frontend_enhanced


if __name__ == "__main__":
    async def test_orchestrator():
        orchestrator = FrontendMigrationOrchestrator()
        
        # Analyze frontend
        print("Analyzing frontend files...")
        plan = await orchestrator.analyze_frontend()
        
        print(f"\nAnalysis Complete:")
        print(f"  Total Files: {plan.total_files}")
        print(f"  Files to Move: {len(plan.file_moves)}")
        print(f"  Review Required: {len(plan.review_required)}")
        
        print(f"\nDomain Distribution:")
        for domain, count in sorted(plan.domain_distribution.items(), 
                                   key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {domain}: {count}")
        
        print(f"\nConfidence Distribution:")
        for level, count in plan.confidence_distribution.items():
            print(f"  {level}: {count}")
        
        print(f"\nValidation Results:")
        print(f"  Valid: {plan.validation_report.is_valid}")
        print(f"  Can Proceed: {plan.validation_report.can_proceed_with_warnings}")
        
        # Generate report
        report = orchestrator.generate_migration_report(plan)
        print(f"\nReport generated ({len(report)} characters)")
        
        # Simulate migration
        print(f"\nSimulating migration...")
        results = await orchestrator.execute_migration(plan, dry_run=True)
        print(f"Simulation Results:")
        for key, value in results.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
    
    # Run test
    asyncio.run(test_orchestrator())