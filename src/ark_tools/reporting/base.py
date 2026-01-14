"""
Base Report Generator
=====================

Core reporting functionality for ARK-TOOLS analysis results.
"""

import json
import uuid
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from ark_tools.utils.debug_logger import debug_log


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    output_dir: Path = field(default_factory=lambda: Path(".ark_reports"))
    keep_history: int = 10
    generate_markdown: bool = True
    generate_html: bool = True
    generate_summary: bool = True
    compress_large_reports: bool = True
    compression_threshold_mb: int = 10
    sync_to_host: bool = True
    host_dir: Optional[Path] = None


class ReportGenerator:
    """
    Base class for generating comprehensive analysis reports.
    Implements single source of truth pattern with master.json.
    """
    
    def __init__(self, config: Optional[ReportConfig] = None):
        """Initialize report generator with configuration."""
        self.config = config or ReportConfig()
        self.timestamp = datetime.now()
        self.run_id = str(uuid.uuid4())
        self.report_dir = self._setup_report_directory()
        self.master_data = {}
        
    def _setup_report_directory(self) -> Path:
        """Setup directory structure for this report run."""
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        run_dir = self.config.output_dir / timestamp_str
        
        # Create directory structure
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "presentation").mkdir(exist_ok=True)
        
        # Update latest symlink
        latest_link = self.config.output_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(run_dir.name)
        
        debug_log.agent(f"Report directory created: {run_dir}")
        return run_dir
    
    def generate_reports(self, analysis_data: Dict[str, Any]) -> Dict[str, Path]:
        """
        Generate all report formats from analysis data.
        
        Args:
            analysis_data: Complete analysis results
            
        Returns:
            Dictionary mapping report types to file paths
        """
        debug_log.agent(f"Generating reports for run {self.run_id}")
        
        # Phase 1: Create master report (source of truth)
        self.master_data = self._create_master_report(analysis_data)
        master_path = self._save_json_report("master.json", self.master_data)
        
        report_paths = {"master": master_path}
        
        # Phase 2: Generate derived reports
        if self.config.generate_summary:
            summary_data = self._create_summary_report(self.master_data)
            report_paths["summary"] = self._save_json_report("summary.json", summary_data)
        
        # Phase 3: Generate error report if errors exist
        if self._has_errors(self.master_data):
            error_data = self._create_error_report(self.master_data)
            report_paths["errors"] = self._save_json_report("errors.json", error_data)
        
        # Phase 4: Generate manifest
        manifest_data = self._create_manifest(report_paths)
        report_paths["manifest"] = self._save_json_report("manifest.json", manifest_data)
        
        # Phase 5: Generate presentations
        if self.config.generate_markdown:
            from ark_tools.reporting.generators import MarkdownGenerator
            md_gen = MarkdownGenerator()
            report_paths["markdown"] = md_gen.generate(
                self.master_data, 
                self.report_dir / "presentation" / "report.md"
            )
        
        if self.config.generate_html:
            from ark_tools.reporting.generators import HTMLGenerator
            html_gen = HTMLGenerator()
            report_paths["html"] = html_gen.generate(
                self.master_data,
                self.report_dir / "presentation" / "report.html"
            )
        
        # Phase 6: Update history
        self._update_history(self.master_data)
        
        # Phase 7: Sync to host if configured
        if self.config.sync_to_host and self.config.host_dir:
            self._sync_to_host()
        
        # Phase 8: Cleanup old reports
        self._cleanup_old_reports()
        
        debug_log.agent(f"Report generation complete: {len(report_paths)} reports created")
        return report_paths
    
    def _create_master_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive master report with all data."""
        return {
            "$schema": "https://ark-tools.dev/schemas/master-v1.json",
            "version": "1.0.0",
            "metadata": self._create_metadata(),
            "summary": self._create_summary_section(analysis_data),
            "hybrid_analysis": self._create_hybrid_section(analysis_data),
            "mams_analysis": self._create_mams_section(analysis_data),
            "llm_analysis": self._create_llm_section(analysis_data),
            "domains": self._create_domains_section(analysis_data),
            "file_tracking": self._create_file_tracking(analysis_data),
            "recommendations": self._create_recommendations(analysis_data),
            "next_steps": self._create_next_steps(analysis_data),
            "performance_metrics": self._create_performance_metrics(analysis_data)
        }
    
    def _create_metadata(self) -> Dict[str, Any]:
        """Create metadata section."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "ark_tools_version": "2.0.0",
            "environment": {
                "platform": os.uname().sysname.lower(),
                "python_version": ".".join(map(str, os.sys.version_info[:3])),
                "hostname": os.uname().nodename
            },
            "configuration": {
                "report_dir": str(self.report_dir),
                "generate_markdown": self.config.generate_markdown,
                "generate_html": self.config.generate_html
            }
        }
    
    def _create_summary_section(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary statistics."""
        structure = analysis_data.get("structure", {})
        domains = analysis_data.get("domains", [])
        timing = analysis_data.get("timing", {})
        
        return {
            "total_files_analyzed": structure.get("total_files", 0),
            "total_components": structure.get("total_components", 0),
            "domains_discovered": len(domains),
            "analysis_strategy": analysis_data.get("strategy", "hybrid"),
            "total_time_ms": timing.get("total_ms", 0),
            "mams_available": structure.get("mams_available", False),
            "llm_confidence": analysis_data.get("confidence", 0)
        }
    
    def _create_hybrid_section(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create hybrid analysis section."""
        return {
            "strategy": analysis_data.get("strategy", "unknown"),
            "phases_completed": self._get_completed_phases(analysis_data),
            "compression_stats": analysis_data.get("compression_stats", {}),
            "timing_breakdown": analysis_data.get("timing", {}),
            "analysis_complete": analysis_data.get("analysis_complete", False)
        }
    
    def _create_mams_section(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create MAMS analysis section."""
        structure = analysis_data.get("structure", {})
        return {
            "available": structure.get("mams_available", False),
            "fallback_used": structure.get("fallback_analysis", False),
            "components": structure.get("components", {}),
            "file_count": structure.get("total_files", 0),
            "component_count": structure.get("total_components", 0)
        }
    
    def _create_llm_section(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create LLM analysis section."""
        return {
            "model_used": analysis_data.get("model_info", {}).get("model_path", "unknown"),
            "context_size": analysis_data.get("model_info", {}).get("context_size", 0),
            "tokens_processed": analysis_data.get("compression_stats", {}).get("total_tokens", 0),
            "inference_time_ms": analysis_data.get("timing", {}).get("llm_ms", 0),
            "confidence": analysis_data.get("confidence", 0),
            "error": analysis_data.get("error")
        }
    
    def _create_domains_section(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create domains section."""
        domains = analysis_data.get("domains", [])
        domain_relationships = analysis_data.get("domain_relationships", [])
        
        # Enhance domains with relationships
        for domain in domains:
            domain_name = domain.get("name")
            domain["relationships"] = [
                rel for rel in domain_relationships 
                if rel.get("from") == domain_name or rel.get("to") == domain_name
            ]
            
        return domains
    
    def _create_file_tracking(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create file tracking section."""
        compression_stats = analysis_data.get("compression_stats", {})
        return {
            "processed": {
                "count": compression_stats.get("files_analyzed", 0),
                "files": []  # Would include file list in production
            },
            "skipped": {
                "count": 0,
                "reasons": {},
                "files": []
            },
            "failed": {
                "count": 0,
                "files": []
            }
        }
    
    def _create_recommendations(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create recommendations section."""
        suggestions = analysis_data.get("suggestions", {}).get("suggestions", [])
        
        critical = [s for s in suggestions if s.get("impact") == "high"]
        warnings = [s for s in suggestions if s.get("impact") == "medium"]
        improvements = [s for s in suggestions if s.get("impact") == "low"]
        
        return {
            "critical": critical,
            "warnings": warnings,
            "improvements": improvements,
            "total_count": len(suggestions)
        }
    
    def _create_next_steps(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create next steps section."""
        suggestions = analysis_data.get("suggestions", {}).get("suggestions", [])
        domains = analysis_data.get("domains", [])
        
        immediate = []
        if len(domains) > 5:
            immediate.append("Review discovered domains for accuracy")
        if suggestions:
            immediate.append(f"Review {len(suggestions)} code organization suggestions")
            
        testing = [
            "Validate domain boundaries",
            "Test component relationships",
            "Review generated documentation"
        ]
        
        deployment = [
            "Refactor based on domain analysis",
            "Implement suggested improvements",
            "Monitor code metrics"
        ]
        
        return {
            "immediate": immediate,
            "testing": testing,
            "deployment": deployment
        }
    
    def _create_performance_metrics(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance metrics section."""
        timing = analysis_data.get("timing", {})
        compression = analysis_data.get("compression_stats", {})
        
        return {
            "processing_speed": {
                "mams_ms": timing.get("mams_ms", 0),
                "compression_ms": timing.get("compression_ms", 0),
                "llm_ms": timing.get("llm_ms", 0),
                "total_ms": timing.get("total_ms", 0)
            },
            "compression_efficiency": {
                "files_compressed": compression.get("files_analyzed", 0),
                "tokens_generated": compression.get("total_tokens", 0),
                "compression_ratio": compression.get("compression_ratio", 0)
            }
        }
    
    def _get_completed_phases(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Determine which phases were completed."""
        phases = []
        
        if analysis_data.get("structure"):
            phases.append("structural_analysis")
        if analysis_data.get("compression_stats"):
            phases.append("context_compression")
        if analysis_data.get("domains"):
            phases.append("domain_discovery")
        if analysis_data.get("suggestions"):
            phases.append("recommendations")
            
        return phases
    
    def _create_summary_report(self, master_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create concise summary report from master data."""
        summary = master_data.get("summary", {})
        domains = master_data.get("domains", [])
        recommendations = master_data.get("recommendations", {})
        
        return {
            "$schema": "https://ark-tools.dev/schemas/summary-v1.json",
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "success": True,
            
            "scorecard": {
                "files_analyzed": summary.get("total_files_analyzed", 0),
                "domains_discovered": len(domains),
                "components_found": summary.get("total_components", 0),
                "analysis_confidence": summary.get("llm_confidence", 0)
            },
            
            "key_metrics": {
                "analysis_time_ms": summary.get("total_time_ms", 0),
                "mams_available": summary.get("mams_available", False),
                "recommendations_count": recommendations.get("total_count", 0)
            },
            
            "top_domains": [
                {
                    "name": d.get("name"),
                    "confidence": d.get("confidence", 0),
                    "component_count": len(d.get("primary_components", []))
                }
                for d in domains[:5]
            ],
            
            "recommended_actions": [
                r.get("suggestion") for r in recommendations.get("critical", [])[:3]
            ],
            
            "links": {
                "full_report": "master.json",
                "errors": "errors.json" if self._has_errors(master_data) else None,
                "markdown": "presentation/report.md",
                "html": "presentation/report.html"
            }
        }
    
    def _create_error_report(self, master_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed error report."""
        return {
            "$schema": "https://ark-tools.dev/schemas/errors-v1.json",
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            
            "summary": {
                "total_errors": 0,  # Would be populated from actual errors
                "critical": 0,
                "warnings": 0
            },
            
            "errors": [],  # Would contain actual errors
            "warnings": []  # Would contain warnings
        }
    
    def _create_manifest(self, report_paths: Dict[str, Path]) -> Dict[str, Any]:
        """Create manifest with metadata about generated reports."""
        file_info = {}
        
        for report_type, path in report_paths.items():
            if path and path.exists():
                stat = path.stat()
                file_info[report_type] = {
                    "path": str(path.relative_to(self.report_dir)),
                    "size_bytes": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                }
        
        return {
            "$schema": "https://ark-tools.dev/schemas/manifest-v1.json",
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "ark_tools_version": "2.0.0",
            "files": file_info,
            "report_directory": str(self.report_dir)
        }
    
    def _save_json_report(self, filename: str, data: Dict[str, Any]) -> Path:
        """Save JSON report to file."""
        filepath = self.report_dir / filename
        
        # Check if compression needed
        json_str = json.dumps(data, indent=2)
        size_mb = len(json_str.encode()) / (1024 * 1024)
        
        if self.config.compress_large_reports and size_mb > self.config.compression_threshold_mb:
            # Compress large files
            import gzip
            filepath = filepath.with_suffix(".json.gz")
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        else:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        
        debug_log.agent(f"Saved report: {filepath} ({size_mb:.2f} MB)")
        return filepath
    
    def _has_errors(self, master_data: Dict[str, Any]) -> bool:
        """Check if there are errors in the analysis."""
        # Check various sections for errors
        if master_data.get("llm_analysis", {}).get("error"):
            return True
        if master_data.get("recommendations", {}).get("critical"):
            return True
        return False
    
    def _update_history(self, master_data: Dict[str, Any]):
        """Update historical tracking of report runs."""
        history_file = self.config.output_dir / "history.json"
        
        # Load existing history
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)
        else:
            history = {"runs": []}
        
        # Add current run
        summary = master_data.get("summary", {})
        history["runs"].append({
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "directory": self.report_dir.name,
            "summary": {
                "files_analyzed": summary.get("total_files_analyzed", 0),
                "domains_found": summary.get("domains_discovered", 0),
                "analysis_time_ms": summary.get("total_time_ms", 0)
            }
        })
        
        # Keep only last N runs
        history["runs"] = history["runs"][-self.config.keep_history:]
        
        # Calculate trends
        if len(history["runs"]) > 1:
            current = history["runs"][-1]["summary"]
            previous = history["runs"][-2]["summary"]
            history["trends"] = {
                "files_change": current["files_analyzed"] - previous["files_analyzed"],
                "domains_change": current["domains_found"] - previous["domains_found"],
                "performance_change": current["analysis_time_ms"] - previous["analysis_time_ms"]
            }
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _sync_to_host(self):
        """Sync reports to host directory if configured."""
        if not self.config.host_dir:
            return
            
        host_dir = self.config.host_dir / self.report_dir.name
        host_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all files
        for item in self.report_dir.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(self.report_dir)
                dest = host_dir / relative_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
        
        # Update latest symlink on host
        latest_link = self.config.host_dir / "latest"
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(host_dir.name)
        
        debug_log.agent(f"Reports synced to host: {host_dir}")
    
    def _cleanup_old_reports(self):
        """Remove old report directories beyond retention limit."""
        if not self.config.output_dir.exists():
            return
            
        # Get all report directories (exclude latest symlink and history.json)
        report_dirs = [
            d for d in self.config.output_dir.iterdir()
            if d.is_dir() and d.name != "latest"
        ]
        
        # Sort by creation time
        report_dirs.sort(key=lambda d: d.stat().st_ctime)
        
        # Remove oldest if exceeding limit
        while len(report_dirs) > self.config.keep_history:
            old_dir = report_dirs.pop(0)
            shutil.rmtree(old_dir)
            debug_log.agent(f"Removed old report: {old_dir}")