#!/usr/bin/env python3
"""
MAMS Orchestrator Enhanced Integration
Patches the existing orchestrator to use enhanced frontend processing
"""

import asyncio
from pathlib import Path
from typing import Dict, Any

def integrate_enhanced_frontend():
    """
    Integration function to be imported by mams_orchestrator_enhanced_fixed.py
    Adds enhanced frontend processing to the existing MAMS run-all command
    """
    
    async def process_frontend_enhanced(files_list, dry_run=False):
        """
        Enhanced frontend processing to replace basic extraction
        Called by the main orchestrator
        """
        from arkyvus.migrations.mams_017_frontend_orchestrator_integration import FrontendMigrationOrchestrator
        
        print("\n" + "="*80)
        print("ENHANCED FRONTEND PROCESSING")
        print("="*80)
        
        orchestrator = FrontendMigrationOrchestrator()
        
        # Phase 1: Deep Analysis with AST parsing
        print("\n📊 Phase 1: Enhanced Frontend Analysis with AST Parsing")
        print("  - TypeScript AST parsing for accurate analysis")
        print("  - Confidence scoring with evidence tracking")
        print("  - Dependency graph construction")
        
        plan = await orchestrator.analyze_frontend(confidence_threshold=0.7)
        
        print(f"\n✅ Frontend Analysis Complete:")
        print(f"  Total Files: {plan.total_files}")
        print(f"  High Confidence: {plan.confidence_distribution.get('high', 0)}")
        print(f"  Medium Confidence: {plan.confidence_distribution.get('medium', 0)}")
        print(f"  Low Confidence: {plan.confidence_distribution.get('low', 0)}")
        print(f"  Review Required: {len(plan.review_required)}")
        
        # Phase 2: Validation
        print(f"\n📋 Phase 2: Dependency Validation")
        print(f"  Domain Violations: {len(plan.validation_report.domain_violations)}")
        print(f"  Circular Dependencies: {len(plan.validation_report.cyclic_dependencies)}")
        print(f"  Orphaned Files: {len(plan.validation_report.orphaned_files)}")
        print(f"  Can Proceed: {plan.validation_report.can_proceed_with_warnings}")
        
        # Phase 3: Migration Planning
        print(f"\n🗺️ Phase 3: Migration Planning")
        print(f"  Files to Move: {len(plan.file_moves)}")
        print(f"  Import Updates Required: {plan.import_rewrite_plan.total_updates}")
        print(f"  Affected Files: {len(plan.import_rewrite_plan.affected_files)}")
        
        # Show domain distribution
        print(f"\n📊 Domain Distribution:")
        for domain, count in sorted(plan.domain_distribution.items(), 
                                   key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {domain}: {count} files")
        
        # Generate reports
        report = orchestrator.generate_migration_report(plan)
        report_path = Path('/app/.migration/frontend_enhanced_report.md')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report)
        print(f"\n📝 Enhanced Frontend Report: {report_path}")
        
        # Generate review UI if needed
        if plan.review_required:
            ui_path = await orchestrator.generate_review_ui(plan)
            print(f"🔍 Review UI Generated: {ui_path}")
            print(f"   Open this file in a browser to review low-confidence classifications")
        
        # Prepare results for orchestrator
        results = {
            'platform': 'frontend',
            'files_analyzed': plan.total_files,
            'classifications': len(plan.classifications),
            'confidence_high': plan.confidence_distribution.get('high', 0),
            'confidence_low': plan.confidence_distribution.get('low', 0),
            'review_required': len(plan.review_required),
            'domain_violations': len(plan.validation_report.domain_violations),
            'migration_ready': plan.validation_report.can_proceed_with_warnings,
            'report_path': str(report_path),
            'review_ui_path': ui_path if plan.review_required else None
        }
        
        if not dry_run and plan.validation_report.can_proceed_with_warnings:
            print(f"\n⚡ Phase 4: Migration Execution")
            if input("Execute frontend migration? (y/n): ").lower() == 'y':
                migration_results = await orchestrator.execute_migration(plan, dry_run=False)
                results['migration_executed'] = True
                results['files_moved'] = migration_results['files_moved']
                results['imports_updated'] = migration_results['imports_updated']
                print(f"✅ Migration Complete: {migration_results['files_moved']} files moved")
            else:
                print("Migration skipped - run 'ark mams migrate-frontend' to execute later")
        elif dry_run:
            print(f"\n[DRY RUN] Would migrate {len(plan.file_moves)} files")
        
        return results
    
    return process_frontend_enhanced


# Monkey patch function to inject into existing orchestrator
def patch_orchestrator():
    """
    Patches the existing orchestrator to use enhanced frontend processing
    Call this from mams_orchestrator_enhanced_fixed.py
    """
    
    # This would be imported and called in the orchestrator
    # Right before the frontend processing section
    
    enhanced_processor = integrate_enhanced_frontend()
    return enhanced_processor