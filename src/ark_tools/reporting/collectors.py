"""
Report Data Collectors
======================

Collectors for gathering data from various analysis components.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import time

from ark_tools.utils.debug_logger import debug_log


class DataCollector:
    """Base class for data collectors."""
    
    def collect(self) -> Dict[str, Any]:
        """Collect data from source."""
        raise NotImplementedError


class HybridAnalysisCollector(DataCollector):
    """
    Collects data from hybrid MAMS/LLM analysis results.
    Transforms raw analysis data into report-ready format.
    """
    
    def __init__(self, analysis_result: Dict[str, Any]):
        """
        Initialize collector with analysis results.
        
        Args:
            analysis_result: Raw results from hybrid analysis
        """
        self.analysis_result = analysis_result
        self.start_time = time.time()
        
    def collect(self) -> Dict[str, Any]:
        """
        Collect and transform analysis data for reporting.
        
        Returns:
            Report-ready data dictionary
        """
        debug_log.agent("Collecting hybrid analysis data for report")
        
        return {
            "metadata": self._collect_metadata(),
            "structure": self._collect_structure_data(),
            "domains": self._collect_domain_data(),
            "compression_stats": self._collect_compression_stats(),
            "timing": self._collect_timing_data(),
            "suggestions": self._collect_suggestions(),
            "model_info": self._collect_model_info(),
            "confidence": self._collect_confidence_scores(),
            "strategy": self.analysis_result.get("strategy", "unknown"),
            "analysis_complete": self.analysis_result.get("analysis_complete", False),
            "error": self.analysis_result.get("error")
        }
    
    def _collect_metadata(self) -> Dict[str, Any]:
        """Collect analysis metadata."""
        return {
            "collection_time": datetime.now().isoformat(),
            "analysis_type": "hybrid",
            "data_source": "HybridAnalysisCollector"
        }
    
    def _collect_structure_data(self) -> Dict[str, Any]:
        """Collect structural analysis data from MAMS."""
        structure = self.analysis_result.get("structure", {})
        return {
            "total_files": structure.get("total_files", 0),
            "total_components": structure.get("total_components", 0),
            "mams_available": structure.get("mams_available", False),
            "fallback_analysis": structure.get("fallback_analysis", False),
            "components": structure.get("components", {})
        }
    
    def _collect_domain_data(self) -> List[Dict[str, Any]]:
        """Collect domain discovery data from LLM analysis."""
        domains = self.analysis_result.get("domains", [])
        domain_relationships = self.analysis_result.get("domain_relationships", [])
        
        # Enhance domains with additional metrics
        enhanced_domains = []
        for domain in domains:
            enhanced = dict(domain)
            enhanced["metrics"] = self._calculate_domain_metrics(domain)
            enhanced["health_score"] = self._calculate_domain_health(domain)
            enhanced_domains.append(enhanced)
        
        return enhanced_domains
    
    def _collect_compression_stats(self) -> Dict[str, Any]:
        """Collect compression statistics."""
        stats = self.analysis_result.get("compression_stats", {})
        return {
            "files_analyzed": stats.get("files_analyzed", 0),
            "total_tokens": stats.get("total_tokens", 0),
            "compression_ratio": stats.get("compression_ratio", 0),
            "average_tokens_per_file": (
                stats.get("total_tokens", 0) / max(stats.get("files_analyzed", 1), 1)
            )
        }
    
    def _collect_timing_data(self) -> Dict[str, Any]:
        """Collect performance timing data."""
        timing = self.analysis_result.get("timing", {})
        return {
            "mams_ms": timing.get("mams_ms", 0),
            "compression_ms": timing.get("compression_ms", 0),
            "llm_ms": timing.get("llm_ms", 0),
            "total_ms": timing.get("total_ms", 0),
            "collection_ms": int((time.time() - self.start_time) * 1000)
        }
    
    def _collect_suggestions(self) -> Dict[str, Any]:
        """Collect code organization suggestions."""
        suggestions = self.analysis_result.get("suggestions", {})
        return {
            "suggestions": suggestions.get("suggestions", []),
            "total_count": suggestions.get("total_suggestions", 0),
            "estimated_impact": suggestions.get("estimated_impact", 0)
        }
    
    def _collect_model_info(self) -> Dict[str, Any]:
        """Collect LLM model information."""
        # This would be populated from actual model info
        return {
            "model_path": "codellama-7b-instruct.gguf",
            "context_size": 8192,
            "max_tokens": 2048,
            "temperature": 0.1
        }
    
    def _collect_confidence_scores(self) -> float:
        """Collect overall confidence score."""
        return self.analysis_result.get("confidence", 0.0)
    
    def _calculate_domain_metrics(self, domain: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional metrics for a domain."""
        components = domain.get("primary_components", [])
        relationships = domain.get("relationships", [])
        
        return {
            "component_count": len(components),
            "relationship_count": len(relationships),
            "complexity_score": self._calculate_complexity(components, relationships),
            "cohesion_score": domain.get("confidence", 0)
        }
    
    def _calculate_domain_health(self, domain: Dict[str, Any]) -> float:
        """Calculate health score for a domain."""
        confidence = domain.get("confidence", 0)
        components = len(domain.get("primary_components", []))
        relationships = len(domain.get("relationships", []))
        
        # Simple health calculation
        health = confidence * 0.5
        if 3 <= components <= 10:
            health += 0.3
        if relationships < 5:
            health += 0.2
            
        return min(health, 1.0)
    
    def _calculate_complexity(self, components: List, relationships: List) -> float:
        """Calculate complexity score based on components and relationships."""
        if not components:
            return 0.0
            
        # Simple complexity heuristic
        complexity = len(relationships) / max(len(components), 1)
        return min(complexity, 1.0)


class MAMSCollector(DataCollector):
    """Collector for MAMS-specific analysis data."""
    
    def __init__(self, mams_result: Dict[str, Any]):
        self.mams_result = mams_result
    
    def collect(self) -> Dict[str, Any]:
        """Collect MAMS analysis data."""
        return {
            "discovery": self._collect_discovery_data(),
            "validation": self._collect_validation_data(),
            "extraction": self._collect_extraction_data(),
            "file_tracking": self._collect_file_tracking()
        }
    
    def _collect_discovery_data(self) -> Dict[str, Any]:
        """Collect file discovery data."""
        return {
            "total_files": self.mams_result.get("total_files", 0),
            "file_types": self._categorize_files(),
            "exclusions": self.mams_result.get("exclusions", {})
        }
    
    def _collect_validation_data(self) -> Dict[str, Any]:
        """Collect validation results."""
        return {
            "compatibility": self.mams_result.get("compatibility", {}),
            "dependencies": self.mams_result.get("dependencies", {}),
            "readiness": self.mams_result.get("readiness", {})
        }
    
    def _collect_extraction_data(self) -> Dict[str, Any]:
        """Collect component extraction data."""
        components = self.mams_result.get("components", {})
        return {
            "total_extracted": len(components),
            "by_type": self._categorize_components(components),
            "errors": self.mams_result.get("extraction_errors", [])
        }
    
    def _collect_file_tracking(self) -> Dict[str, Any]:
        """Collect file processing tracking."""
        return {
            "processed": self.mams_result.get("processed_files", []),
            "skipped": self.mams_result.get("skipped_files", []),
            "failed": self.mams_result.get("failed_files", [])
        }
    
    def _categorize_files(self) -> Dict[str, int]:
        """Categorize files by type."""
        # Would implement actual categorization
        return {
            ".py": 0,
            ".js": 0,
            ".ts": 0,
            ".jsx": 0,
            ".tsx": 0
        }
    
    def _categorize_components(self, components: Dict) -> Dict[str, int]:
        """Categorize components by type."""
        # Would implement actual categorization
        return {
            "classes": 0,
            "functions": 0,
            "constants": 0,
            "types": 0
        }


class LLMCollector(DataCollector):
    """Collector for LLM-specific analysis data."""
    
    def __init__(self, llm_result: Dict[str, Any]):
        self.llm_result = llm_result
    
    def collect(self) -> Dict[str, Any]:
        """Collect LLM analysis data."""
        return {
            "domains": self._collect_domains(),
            "intent_analysis": self._collect_intent(),
            "semantic_relationships": self._collect_relationships(),
            "confidence_scores": self._collect_confidence(),
            "model_metrics": self._collect_model_metrics()
        }
    
    def _collect_domains(self) -> List[Dict[str, Any]]:
        """Collect discovered domains."""
        return self.llm_result.get("domains", [])
    
    def _collect_intent(self) -> Optional[Dict[str, Any]]:
        """Collect code intent analysis."""
        return self.llm_result.get("intent")
    
    def _collect_relationships(self) -> List[Dict[str, Any]]:
        """Collect domain relationships."""
        return self.llm_result.get("domain_relationships", [])
    
    def _collect_confidence(self) -> Dict[str, float]:
        """Collect confidence scores."""
        return {
            "overall": self.llm_result.get("overall_confidence", 0),
            "by_domain": self._get_domain_confidence()
        }
    
    def _collect_model_metrics(self) -> Dict[str, Any]:
        """Collect model performance metrics."""
        return {
            "inference_time_ms": self.llm_result.get("inference_time", 0),
            "tokens_processed": self.llm_result.get("tokens", 0),
            "cache_hit": self.llm_result.get("cache_hit", False)
        }
    
    def _get_domain_confidence(self) -> Dict[str, float]:
        """Get confidence scores by domain."""
        domains = self.llm_result.get("domains", [])
        return {
            d["name"]: d.get("confidence", 0) 
            for d in domains
        }


class PerformanceCollector(DataCollector):
    """Collector for performance metrics."""
    
    def __init__(self):
        self.metrics = {}
        
    def start_timer(self, name: str):
        """Start a named timer."""
        self.metrics[f"{name}_start"] = time.time()
    
    def stop_timer(self, name: str):
        """Stop a named timer and record duration."""
        start_key = f"{name}_start"
        if start_key in self.metrics:
            duration = time.time() - self.metrics[start_key]
            self.metrics[f"{name}_duration_ms"] = int(duration * 1000)
            del self.metrics[start_key]
    
    def add_metric(self, name: str, value: Any):
        """Add a custom metric."""
        self.metrics[name] = value
    
    def collect(self) -> Dict[str, Any]:
        """Collect all performance metrics."""
        return dict(self.metrics)