"""
Report Format Generators
========================

Generators for various report output formats (Markdown, HTML, JSON).
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ark_tools.utils.debug_logger import debug_log


class MarkdownGenerator:
    """Generates Markdown-formatted reports."""
    
    def generate(self, master_data: Dict[str, Any], output_path: Path) -> Path:
        """
        Generate Markdown report from master data.
        
        Args:
            master_data: Complete analysis data
            output_path: Path to save markdown file
            
        Returns:
            Path to generated markdown file
        """
        debug_log.agent(f"Generating Markdown report: {output_path}")
        
        sections = [
            self._generate_header(master_data),
            self._generate_executive_summary(master_data),
            self._generate_scorecard(master_data),
            self._generate_analysis_results(master_data),
            self._generate_domain_section(master_data),
            self._generate_recommendations(master_data),
            self._generate_performance_metrics(master_data),
            self._generate_next_steps(master_data),
            self._generate_appendix(master_data)
        ]
        
        # Combine all sections
        content = "\n\n".join(filter(None, sections))
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        
        return output_path
    
    def _generate_header(self, data: Dict[str, Any]) -> str:
        """Generate report header."""
        metadata = data.get("metadata", {})
        return f"""# ARK-TOOLS Hybrid Analysis Report

**Run ID:** {metadata.get("run_id", "unknown")}  
**Date:** {metadata.get("timestamp", "unknown")}  
**Version:** {metadata.get("ark_tools_version", "2.0.0")}  
**Status:** ✅ Analysis Complete"""
    
    def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary section."""
        summary = data.get("summary", {})
        domains = data.get("domains", [])
        
        return f"""## Executive Summary

Successfully analyzed **{summary.get('total_files_analyzed', 0):,}** files containing **{summary.get('total_components', 0):,}** components. 
The analysis discovered **{len(domains)}** distinct business domains using a {summary.get('analysis_strategy', 'hybrid')} analysis strategy.

**Key Findings:**
- MAMS structural analysis: {'✅ Available' if summary.get('mams_available') else '⚠️ Fallback mode'}
- LLM semantic analysis confidence: {summary.get('llm_confidence', 0):.1%}
- Total analysis time: {summary.get('total_time_ms', 0):,}ms"""
    
    def _generate_scorecard(self, data: Dict[str, Any]) -> str:
        """Generate scorecard section."""
        summary = data.get("summary", {})
        recommendations = data.get("recommendations", {})
        
        # Calculate scores
        analysis_score = min(summary.get('llm_confidence', 0) * 100, 100)
        quality_score = 100 - (len(recommendations.get('critical', [])) * 10)
        completeness = 100 if summary.get('total_files_analyzed', 0) > 0 else 0
        
        return f"""## 📊 Analysis Scorecard

| Metric | Score | Status |
|--------|-------|--------|
| Analysis Confidence | {analysis_score:.1f}% | {self._get_status_emoji(analysis_score)} |
| Code Quality | {quality_score:.1f}% | {self._get_status_emoji(quality_score)} |
| Analysis Completeness | {completeness:.1f}% | {self._get_status_emoji(completeness)} |
| Domain Discovery | {len(data.get('domains', []))} domains | ✅ |"""
    
    def _generate_analysis_results(self, data: Dict[str, Any]) -> str:
        """Generate analysis results section."""
        hybrid = data.get("hybrid_analysis", {})
        mams = data.get("mams_analysis", {})
        llm = data.get("llm_analysis", {})
        
        phases = hybrid.get("phases_completed", [])
        timing = hybrid.get("timing_breakdown", {})
        
        return f"""## 📈 Analysis Results

### Completed Phases
{self._format_phase_list(phases)}

### Analysis Timing
- **MAMS Structural Analysis:** {timing.get('mams_ms', 0):,}ms
- **Context Compression:** {timing.get('compression_ms', 0):,}ms  
- **LLM Semantic Analysis:** {timing.get('llm_ms', 0):,}ms
- **Total Time:** {timing.get('total_ms', 0):,}ms

### MAMS Analysis
- Files Analyzed: {mams.get('file_count', 0):,}
- Components Found: {mams.get('component_count', 0):,}
- Analysis Mode: {'Native MAMS' if mams.get('available') else 'Fallback Analysis'}

### LLM Analysis
- Tokens Processed: {llm.get('tokens_processed', 0):,}
- Context Size Used: {llm.get('context_size', 0):,}
- Inference Time: {llm.get('inference_time_ms', 0):,}ms
- Confidence Level: {llm.get('confidence', 0):.1%}"""
    
    def _generate_domain_section(self, data: Dict[str, Any]) -> str:
        """Generate domain discovery section."""
        domains = data.get("domains", [])
        
        if not domains:
            return "## 🏗️ Domain Discovery\n\nNo domains discovered in this analysis."
        
        sections = ["## 🏗️ Domain Discovery\n"]
        
        for i, domain in enumerate(domains[:10], 1):  # Limit to top 10
            name = domain.get("name", "Unknown")
            desc = domain.get("description", "No description")
            confidence = domain.get("confidence", 0)
            components = domain.get("primary_components", [])
            relationships = domain.get("relationships", [])
            
            sections.append(f"""### {i}. {name}

**Description:** {desc}  
**Confidence:** {confidence:.1%}  
**Components:** {len(components)} ({', '.join(components[:5])}{'...' if len(components) > 5 else ''})  
**Relationships:** {len(relationships)} connections to other domains""")
        
        return "\n\n".join(sections)
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> str:
        """Generate recommendations section."""
        recommendations = data.get("recommendations", {})
        
        critical = recommendations.get("critical", [])
        warnings = recommendations.get("warnings", [])
        improvements = recommendations.get("improvements", [])
        
        if not any([critical, warnings, improvements]):
            return "## 💡 Recommendations\n\nNo specific recommendations at this time."
        
        sections = ["## 💡 Recommendations"]
        
        if critical:
            sections.append("### 🔴 Critical Issues")
            for rec in critical:
                sections.append(f"- **{rec.get('suggestion', 'N/A')}**")
                if rec.get('impact'):
                    sections.append(f"  - Impact: {rec['impact']}")
                if rec.get('effort'):
                    sections.append(f"  - Effort: {rec['effort']}")
        
        if warnings:
            sections.append("\n### 🟡 Warnings")
            for rec in warnings:
                sections.append(f"- {rec.get('suggestion', 'N/A')}")
        
        if improvements:
            sections.append("\n### 🟢 Improvements")
            for rec in improvements:
                sections.append(f"- {rec.get('suggestion', 'N/A')}")
        
        return "\n".join(sections)
    
    def _generate_performance_metrics(self, data: Dict[str, Any]) -> str:
        """Generate performance metrics section."""
        metrics = data.get("performance_metrics", {})
        speed = metrics.get("processing_speed", {})
        efficiency = metrics.get("compression_efficiency", {})
        
        return f"""## ⚡ Performance Metrics

### Processing Speed
- MAMS Analysis: {speed.get('mams_ms', 0):,}ms
- Compression: {speed.get('compression_ms', 0):,}ms
- LLM Inference: {speed.get('llm_ms', 0):,}ms
- **Total:** {speed.get('total_ms', 0):,}ms

### Compression Efficiency
- Files Compressed: {efficiency.get('files_compressed', 0)}
- Tokens Generated: {efficiency.get('tokens_generated', 0):,}
- Compression Ratio: {efficiency.get('compression_ratio', 0):.1%}"""
    
    def _generate_next_steps(self, data: Dict[str, Any]) -> str:
        """Generate next steps section."""
        next_steps = data.get("next_steps", {})
        
        immediate = next_steps.get("immediate", [])
        testing = next_steps.get("testing", [])
        deployment = next_steps.get("deployment", [])
        
        sections = ["## 🎯 Next Steps"]
        
        if immediate:
            sections.append("\n### Immediate Actions")
            for step in immediate:
                sections.append(f"1. {step}")
        
        if testing:
            sections.append("\n### Testing Phase")
            for step in testing:
                sections.append(f"- {step}")
        
        if deployment:
            sections.append("\n### Deployment Preparation")
            for step in deployment:
                sections.append(f"- {step}")
        
        return "\n".join(sections)
    
    def _generate_appendix(self, data: Dict[str, Any]) -> str:
        """Generate appendix section."""
        metadata = data.get("metadata", {})
        
        return f"""## Appendix

### Report Metadata
- **Run ID:** `{metadata.get('run_id', 'unknown')}`
- **Timestamp:** {metadata.get('timestamp', 'unknown')}
- **Platform:** {metadata.get('environment', {}).get('platform', 'unknown')}
- **Python Version:** {metadata.get('environment', {}).get('python_version', 'unknown')}

### Related Files
- Full Report: `master.json`
- Summary: `summary.json`
- Errors: `errors.json` (if applicable)

---

*Generated by ARK-TOOLS v2.0.0*"""
    
    def _format_phase_list(self, phases: List[str]) -> str:
        """Format phase list with checkmarks."""
        if not phases:
            return "- No phases completed"
        
        return "\n".join([f"- ✅ {phase.replace('_', ' ').title()}" for phase in phases])
    
    def _get_status_emoji(self, score: float) -> str:
        """Get status emoji based on score."""
        if score >= 90:
            return "✅"
        elif score >= 70:
            return "🟡"
        else:
            return "🔴"


class HTMLGenerator:
    """Generates HTML-formatted reports with interactive elements."""
    
    def generate(self, master_data: Dict[str, Any], output_path: Path) -> Path:
        """
        Generate HTML report from master data.
        
        Args:
            master_data: Complete analysis data
            output_path: Path to save HTML file
            
        Returns:
            Path to generated HTML file
        """
        debug_log.agent(f"Generating HTML report: {output_path}")
        
        html_content = self._generate_html(master_data)
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content)
        
        return output_path
    
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """Generate complete HTML document."""
        metadata = data.get("metadata", {})
        summary = data.get("summary", {})
        domains = data.get("domains", [])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARK-TOOLS Analysis Report - {metadata.get('run_id', 'unknown')}</title>
    {self._generate_styles()}
    {self._generate_scripts()}
</head>
<body>
    <div class="container">
        {self._generate_header_html(metadata)}
        {self._generate_summary_cards(summary)}
        {self._generate_analysis_charts(data)}
        {self._generate_domain_cards(domains)}
        {self._generate_recommendations_html(data.get('recommendations', {}))}
        {self._generate_footer_html(metadata)}
    </div>
</body>
</html>"""
    
    def _generate_styles(self) -> str:
        """Generate CSS styles."""
        return """<style>
        :root {
            --primary-color: #4a90e2;
            --success-color: #5cb85c;
            --warning-color: #f0ad4e;
            --danger-color: #d9534f;
            --dark-bg: #2c3e50;
            --light-bg: #ecf0f1;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background: var(--light-bg);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary-color), var(--dark-bg));
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        
        .metadata {
            display: flex;
            gap: 20px;
            margin-top: 15px;
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .card-title {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .card-value {
            font-size: 2em;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        .card-subtitle {
            font-size: 0.9em;
            color: #999;
            margin-top: 5px;
        }
        
        .domain-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid var(--primary-color);
        }
        
        .domain-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .domain-name {
            font-size: 1.3em;
            font-weight: bold;
        }
        
        .confidence-badge {
            background: var(--success-color);
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .recommendations {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .rec-critical {
            border-left: 4px solid var(--danger-color);
            padding-left: 15px;
            margin-bottom: 15px;
        }
        
        .rec-warning {
            border-left: 4px solid var(--warning-color);
            padding-left: 15px;
            margin-bottom: 15px;
        }
        
        .rec-info {
            border-left: 4px solid var(--success-color);
            padding-left: 15px;
            margin-bottom: 15px;
        }
        
        .footer {
            text-align: center;
            color: #666;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
    </style>"""
    
    def _generate_scripts(self) -> str:
        """Generate JavaScript for interactivity."""
        return """<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        // Add interactive charts here
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize charts
            console.log('ARK-TOOLS Report Loaded');
        });
    </script>"""
    
    def _generate_header_html(self, metadata: Dict[str, Any]) -> str:
        """Generate header HTML."""
        return f"""<div class="header">
        <h1>🔬 ARK-TOOLS Hybrid Analysis Report</h1>
        <div class="metadata">
            <div>📅 {metadata.get('timestamp', 'unknown')}</div>
            <div>🔖 Run ID: {metadata.get('run_id', 'unknown')[:8]}...</div>
            <div>⚡ Version: {metadata.get('ark_tools_version', '2.0.0')}</div>
        </div>
    </div>"""
    
    def _generate_summary_cards(self, summary: Dict[str, Any]) -> str:
        """Generate summary statistics cards."""
        cards_html = []
        
        cards_data = [
            ("Files Analyzed", summary.get('total_files_analyzed', 0), "📁"),
            ("Components", summary.get('total_components', 0), "🧩"),
            ("Domains", summary.get('domains_discovered', 0), "🏗️"),
            ("Analysis Time", f"{summary.get('total_time_ms', 0):,}ms", "⏱️"),
        ]
        
        for title, value, icon in cards_data:
            cards_html.append(f"""<div class="card">
            <div class="card-title">{icon} {title}</div>
            <div class="card-value">{value}</div>
        </div>""")
        
        return f"""<div class="cards">
        {''.join(cards_html)}
    </div>"""
    
    def _generate_analysis_charts(self, data: Dict[str, Any]) -> str:
        """Generate analysis charts section."""
        # Placeholder for charts
        return """<div class="chart-container">
        <h2>📊 Analysis Breakdown</h2>
        <div id="timing-chart"></div>
        <div id="domain-chart"></div>
    </div>"""
    
    def _generate_domain_cards(self, domains: List[Dict[str, Any]]) -> str:
        """Generate domain cards."""
        if not domains:
            return "<p>No domains discovered.</p>"
        
        cards = []
        for domain in domains[:10]:  # Limit to 10
            name = domain.get("name", "Unknown")
            desc = domain.get("description", "No description")
            confidence = domain.get("confidence", 0)
            components = domain.get("primary_components", [])
            
            cards.append(f"""<div class="domain-card">
            <div class="domain-header">
                <div class="domain-name">{name}</div>
                <div class="confidence-badge">{confidence:.0%}</div>
            </div>
            <p>{desc}</p>
            <p><strong>Components:</strong> {', '.join(components[:5])}{'...' if len(components) > 5 else ''}</p>
        </div>""")
        
        return f"""<div class="domains">
        <h2>🏗️ Discovered Domains</h2>
        {''.join(cards)}
    </div>"""
    
    def _generate_recommendations_html(self, recommendations: Dict[str, Any]) -> str:
        """Generate recommendations HTML."""
        sections = ['<div class="recommendations"><h2>💡 Recommendations</h2>']
        
        critical = recommendations.get("critical", [])
        warnings = recommendations.get("warnings", [])
        improvements = recommendations.get("improvements", [])
        
        for rec in critical:
            sections.append(f"""<div class="rec-critical">
            <strong>⚠️ Critical:</strong> {rec.get('suggestion', 'N/A')}
        </div>""")
        
        for rec in warnings:
            sections.append(f"""<div class="rec-warning">
            <strong>⚡ Warning:</strong> {rec.get('suggestion', 'N/A')}
        </div>""")
        
        for rec in improvements:
            sections.append(f"""<div class="rec-info">
            <strong>💡 Improvement:</strong> {rec.get('suggestion', 'N/A')}
        </div>""")
        
        sections.append('</div>')
        return ''.join(sections)
    
    def _generate_footer_html(self, metadata: Dict[str, Any]) -> str:
        """Generate footer HTML."""
        return f"""<div class="footer">
        <p>Generated by ARK-TOOLS v{metadata.get('ark_tools_version', '2.0.0')} on {metadata.get('timestamp', 'unknown')}</p>
        <p>Run ID: {metadata.get('run_id', 'unknown')}</p>
    </div>"""


class JSONReportGenerator:
    """Generates structured JSON reports."""
    
    def generate(self, data: Dict[str, Any], output_path: Path) -> Path:
        """
        Generate JSON report.
        
        Args:
            data: Report data
            output_path: Path to save JSON file
            
        Returns:
            Path to generated JSON file
        """
        debug_log.agent(f"Generating JSON report: {output_path}")
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON with pretty formatting
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return output_path