"""
ARK-TOOLS Command-Line Interface
================================

Main CLI entry point for ARK-TOOLS analysis and reporting.
"""

import click
import asyncio
import json
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from ark_tools.agents.architect import ArchitectAgent
from ark_tools import config
from ark_tools.utils.debug_logger import debug_log

console = Console()


@click.group()
def cli():
    """ARK-TOOLS Code Analysis and Reporting"""
    pass


@cli.group()
def analyze():
    """Code analysis commands"""
    pass


@cli.group()
def report():
    """Report generation and viewing commands"""
    pass


@analyze.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--strategy', '-s', 
              type=click.Choice(['hybrid', 'fast', 'deep', 'compress_only']),
              default='hybrid',
              help='Analysis strategy to use')
@click.option('--max-files', '-m', type=int, default=50,
              help='Maximum files to analyze')
@click.option('--output', '-o', type=click.Path(),
              help='Output directory for reports')
@click.option('--format', '-f', 
              type=click.Choice(['json', 'markdown', 'html', 'all']),
              default='all',
              help='Report format(s) to generate')
@click.option('--include-suggestions', is_flag=True,
              help='Include code organization suggestions')
def hybrid(directory, strategy, max_files, output, format, include_suggestions):
    """Perform hybrid MAMS/LLM analysis on a codebase"""
    console.print(f"\n[bold cyan]🚀 ARK-TOOLS Hybrid Analysis[/bold cyan]\n")
    console.print(f"Directory: [green]{directory}[/green]")
    console.print(f"Strategy: [yellow]{strategy}[/yellow]")
    console.print(f"Max files: [yellow]{max_files}[/yellow]\n")
    
    async def run_analysis():
        # Initialize architect agent
        architect_config = {
            'llm_model_path': config.LLM_MODEL_PATH,
            'context_size': config.LLM_CONTEXT_SIZE,
            'max_tokens': config.LLM_MAX_TOKENS,
            'threads': config.LLM_THREADS,
            'temperature': config.LLM_TEMPERATURE
        }
        
        architect = ArchitectAgent(config=architect_config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Run analysis
            task = progress.add_task("Running hybrid analysis...", total=None)
            
            result = await architect.execute_operation(
                'perform_hybrid_analysis',
                {
                    'directory': directory,
                    'strategy': strategy,
                    'max_files': max_files
                }
            )
            
            progress.update(task, completed=True)
            
            if not result.success:
                console.print(f"[red]❌ Analysis failed: {result.error}[/red]")
                return
            
            analysis_data = result.data
            
            # Add suggestions if requested
            if include_suggestions and analysis_data.get('domains'):
                task = progress.add_task("Generating suggestions...", total=None)
                
                suggestions_result = await architect.execute_operation(
                    'suggest_code_organization',
                    {
                        'domains': analysis_data['domains'],
                        'structure': analysis_data.get('structure', {})
                    }
                )
                
                if suggestions_result.success:
                    analysis_data['suggestions'] = suggestions_result.data
                
                progress.update(task, completed=True)
            
            # Display results summary
            console.print("\n[bold green]✅ Analysis Complete![/bold green]\n")
            
            # Show summary table
            table = Table(title="Analysis Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")
            
            structure = analysis_data.get('structure', {})
            table.add_row("Files Analyzed", str(structure.get('total_files', 0)))
            table.add_row("Components Found", str(structure.get('total_components', 0)))
            table.add_row("Domains Discovered", str(len(analysis_data.get('domains', []))))
            
            if 'timing' in analysis_data:
                timing = analysis_data['timing']
                total_ms = timing.get('total_ms', 0)
                table.add_row("Analysis Time", f"{total_ms / 1000:.2f}s")
            
            console.print(table)
            
            # Show domains
            domains = analysis_data.get('domains', [])
            if domains:
                console.print("\n[bold]Discovered Domains:[/bold]")
                for domain in domains:
                    confidence = domain.get('confidence', 0)
                    emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
                    console.print(f"  {emoji} [cyan]{domain['name']}[/cyan] - {domain.get('description', 'No description')}")
            
            # Generate reports if output specified
            if output:
                await generate_reports(analysis_data, output, format)
            
            return analysis_data
    
    # Run the async function
    asyncio.run(run_analysis())


@analyze.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--max-files', '-m', type=int, default=50,
              help='Maximum files to compress')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for compressed skeleton')
def compress(directory, max_files, output):
    """Compress code to AST skeleton for LLM analysis"""
    from ark_tools.mams_core.compressor import CodeCompressor
    
    console.print(f"\n[bold cyan]📦 Code Compression[/bold cyan]\n")
    console.print(f"Directory: [green]{directory}[/green]")
    console.print(f"Max files: [yellow]{max_files}[/yellow]\n")
    
    compressor = CodeCompressor()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Compressing code...", total=None)
        
        compressed = compressor.compress_directory(
            Path(directory),
            max_files=max_files
        )
        
        progress.update(task, completed=True)
    
    # Calculate statistics
    total_chars = sum(len(v) for v in compressed.values())
    estimated_tokens = total_chars // 4
    
    console.print(f"\n[bold green]✅ Compression Complete![/bold green]\n")
    console.print(f"Files compressed: [yellow]{len(compressed)}[/yellow]")
    console.print(f"Total characters: [yellow]{total_chars:,}[/yellow]")
    console.print(f"Estimated tokens: [yellow]{estimated_tokens:,}[/yellow]")
    console.print(f"Compression ratio: [green]~80%[/green]\n")
    
    # Save if output specified
    if output:
        output_path = Path(output)
        output_path.write_text(json.dumps(compressed, indent=2))
        console.print(f"Saved to: [green]{output_path}[/green]")
    
    # Show sample
    if compressed:
        first_file = list(compressed.keys())[0]
        sample = compressed[first_file][:500] + "..." if len(compressed[first_file]) > 500 else compressed[first_file]
        
        syntax = Syntax(sample, "python", theme="monokai")
        console.print(Panel(syntax, title=f"Sample: {first_file}", border_style="cyan"))


@report.command()
@click.argument('analysis-file', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--output', '-o', type=click.Path(), default='.ark_reports',
              help='Output directory for reports')
@click.option('--format', '-f',
              type=click.Choice(['json', 'markdown', 'html', 'all']),
              default='all',
              help='Report format(s) to generate')
def generate(analysis_file, output, format):
    """Generate reports from analysis results"""
    from ark_tools.reporting import ReportGenerator, HybridAnalysisCollector
    from ark_tools.reporting.base import ReportConfig
    
    console.print(f"\n[bold cyan]📊 Report Generation[/bold cyan]\n")
    
    # Load analysis data
    with open(analysis_file) as f:
        analysis_data = json.load(f)
    
    # Configure report generation
    formats_to_generate = []
    if format in ['markdown', 'all']:
        formats_to_generate.append('markdown')
    if format in ['html', 'all']:
        formats_to_generate.append('html')
    if format in ['json', 'all']:
        formats_to_generate.append('json')
    
    report_config = ReportConfig(
        output_dir=Path(output),
        generate_markdown='markdown' in formats_to_generate,
        generate_html='html' in formats_to_generate
    )
    
    # Generate reports
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating reports...", total=None)
        
        collector = HybridAnalysisCollector(analysis_data)
        report_data = collector.collect()
        
        generator = ReportGenerator(config=report_config)
        report_paths = generator.generate_reports(report_data)
        
        progress.update(task, completed=True)
    
    console.print(f"\n[bold green]✅ Reports Generated![/bold green]\n")
    
    # Show generated files
    table = Table(title="Generated Reports")
    table.add_column("Format", style="cyan")
    table.add_column("File", style="green")
    
    for format_name, path in report_paths.items():
        table.add_row(format_name.upper(), str(path))
    
    console.print(table)
    
    console.print(f"\nReport directory: [green]{report_config.output_dir / 'latest'}[/green]")


@report.command()
@click.option('--report-id', '-r', help='Specific report ID or timestamp')
@click.option('--format', '-f',
              type=click.Choice(['json', 'markdown', 'html', 'summary']),
              default='summary',
              help='Format to view')
def view(report_id, format):
    """View existing reports"""
    import json
    
    console.print(f"\n[bold cyan]📖 Report Viewer[/bold cyan]\n")
    
    report_base = Path('.ark_reports')
    
    if not report_base.exists():
        console.print("[red]No reports found. Run analysis first.[/red]")
        return
    
    # Determine which report to show
    if report_id:
        report_dir = report_base / report_id
    else:
        report_dir = report_base / 'latest'
    
    if not report_dir.exists():
        console.print(f"[red]Report not found: {report_dir}[/red]")
        return
    
    # Load and display based on format
    if format == 'summary':
        summary_file = report_dir / 'summary.json'
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
            
            # Display summary
            console.print(Panel(f"[bold]Report Summary[/bold]\n{report_dir}", border_style="cyan"))
            
            if 'metadata' in summary:
                meta = summary['metadata']
                console.print(f"\n[bold]Metadata:[/bold]")
                console.print(f"  Generated: [yellow]{meta.get('timestamp', 'Unknown')}[/yellow]")
                console.print(f"  Run ID: [yellow]{meta.get('run_id', 'Unknown')}[/yellow]")
            
            if 'statistics' in summary:
                stats = summary['statistics']
                console.print(f"\n[bold]Statistics:[/bold]")
                console.print(f"  Files: [yellow]{stats.get('total_files', 0)}[/yellow]")
                console.print(f"  Components: [yellow]{stats.get('total_components', 0)}[/yellow]")
                console.print(f"  Domains: [yellow]{stats.get('total_domains', 0)}[/yellow]")
            
            if 'key_insights' in summary:
                console.print(f"\n[bold]Key Insights:[/bold]")
                for insight in summary['key_insights']:
                    console.print(f"  • {insight}")
    
    elif format == 'json':
        master_file = report_dir / 'master.json'
        if master_file.exists():
            with open(master_file) as f:
                data = json.load(f)
            
            # Pretty print JSON
            syntax = Syntax(json.dumps(data, indent=2), "json", theme="monokai")
            console.print(syntax)
    
    elif format == 'markdown':
        md_file = report_dir / 'presentation' / 'report.md'
        if md_file.exists():
            content = md_file.read_text()
            # Display with syntax highlighting
            syntax = Syntax(content, "markdown", theme="monokai")
            console.print(syntax)
        else:
            console.print("[red]Markdown report not found[/red]")
    
    elif format == 'html':
        html_file = report_dir / 'presentation' / 'report.html'
        if html_file.exists():
            console.print(f"HTML report: [green]file://{html_file.resolve()}[/green]")
            console.print("\nOpen this URL in your browser to view the report.")
        else:
            console.print("[red]HTML report not found[/red]")


@report.command()
def history():
    """View report history"""
    import json
    
    console.print(f"\n[bold cyan]📜 Report History[/bold cyan]\n")
    
    history_file = Path('.ark_reports/history.json')
    
    if not history_file.exists():
        console.print("[yellow]No report history found[/yellow]")
        return
    
    with open(history_file) as f:
        history = json.load(f)
    
    runs = history.get('runs', [])
    
    if not runs:
        console.print("[yellow]No reports in history[/yellow]")
        return
    
    # Display history table
    table = Table(title="Report History")
    table.add_column("Run ID", style="cyan")
    table.add_column("Timestamp", style="green")
    table.add_column("Directory", style="yellow")
    table.add_column("Files", style="magenta")
    table.add_column("Strategy", style="blue")
    
    for run in runs[-10:]:  # Show last 10 runs
        table.add_row(
            run.get('run_id', 'Unknown'),
            run.get('timestamp', 'Unknown'),
            run.get('directory', 'Unknown'),
            str(run.get('files_analyzed', 0)),
            run.get('strategy', 'Unknown')
        )
    
    console.print(table)
    
    if len(runs) > 10:
        console.print(f"\n[dim]Showing last 10 of {len(runs)} total reports[/dim]")


@report.command()
@click.confirm("This will remove all generated reports. Continue?")
def clean():
    """Clean up report directory"""
    import shutil
    
    console.print(f"\n[bold cyan]🧹 Cleaning Reports[/bold cyan]\n")
    
    report_base = Path('.ark_reports')
    
    if report_base.exists():
        try:
            shutil.rmtree(report_base)
            console.print("[green]✅ Reports cleaned successfully[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to clean reports: {e}[/red]")
    else:
        console.print("[yellow]No reports to clean[/yellow]")


@cli.command()
def model():
    """Show LLM model information"""
    console.print(f"\n[bold cyan]🤖 LLM Model Information[/bold cyan]\n")
    
    model_path = Path(config.LLM_MODEL_PATH) if config.LLM_MODEL_PATH else None
    
    if model_path and model_path.exists():
        console.print(f"[bold]Model Path:[/bold] [green]{model_path}[/green]")
        
        # Get file size
        size_mb = model_path.stat().st_size / (1024 * 1024)
        console.print(f"[bold]Model Size:[/bold] [yellow]{size_mb:.1f} MB[/yellow]")
    else:
        console.print(f"[bold]Model Path:[/bold] [red]Not found[/red]")
        if config.LLM_MODEL_PATH:
            console.print(f"  Expected: {config.LLM_MODEL_PATH}")
    
    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Context Size: [yellow]{config.LLM_CONTEXT_SIZE}[/yellow]")
    console.print(f"  Max Tokens: [yellow]{config.LLM_MAX_TOKENS}[/yellow]")
    console.print(f"  Threads: [yellow]{config.LLM_THREADS}[/yellow]")
    console.print(f"  Temperature: [yellow]{config.LLM_TEMPERATURE}[/yellow]")
    console.print(f"  GPU Enabled: [yellow]{config.LLM_ENABLE_GPU}[/yellow]")
    
    if not model_path or not model_path.exists():
        console.print("\n[bold]To download a model:[/bold]")
        console.print("1. Visit https://huggingface.co/models?library=gguf")
        console.print("2. Download a model (e.g., CodeLlama-7B-Instruct GGUF)")
        console.print("3. Save to ~/.ark_tools/models/")
        console.print("4. Update ARK_LLM_MODEL_PATH in .env")


@cli.command()
def server():
    """Start the ARK-TOOLS API server"""
    import uvicorn
    
    console.print(f"\n[bold cyan]🚀 Starting ARK-TOOLS API Server[/bold cyan]\n")
    
    # Import the FastAPI app
    from ark_tools.api import create_app
    
    app = create_app()
    
    # Run server
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        log_level="info" if config.DEBUG else "warning"
    )


async def generate_reports(analysis_data, output_dir, format_choice):
    """Helper function to generate reports from analysis data"""
    from ark_tools.reporting import ReportGenerator, HybridAnalysisCollector
    from ark_tools.reporting.base import ReportConfig
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating reports...", total=None)
        
        # Configure report generation
        formats_to_generate = []
        if format_choice in ['markdown', 'all']:
            formats_to_generate.append('markdown')
        if format_choice in ['html', 'all']:
            formats_to_generate.append('html')
        if format_choice in ['json', 'all']:
            formats_to_generate.append('json')
        
        report_config = ReportConfig(
            output_dir=Path(output_dir),
            generate_markdown='markdown' in formats_to_generate,
            generate_html='html' in formats_to_generate
        )
        
        # Generate reports
        collector = HybridAnalysisCollector(analysis_data)
        report_data = collector.collect()
        
        generator = ReportGenerator(config=report_config)
        report_paths = generator.generate_reports(report_data)
        
        progress.update(task, completed=True)
    
    console.print(f"\n[bold]Reports saved to:[/bold] [green]{report_config.output_dir / 'latest'}[/green]")
    
    for format_name, path in report_paths.items():
        console.print(f"  • {format_name}: {path}")


def main():
    """Main entry point for ark-analyze command"""
    cli()


if __name__ == '__main__':
    main()