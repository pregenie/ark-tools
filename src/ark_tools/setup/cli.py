"""
Command-Line Interface for ARK-TOOLS Setup
==========================================

Provides both interactive and non-interactive CLI for setup configuration.
"""

import sys
import os
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich import print as rprint

from ark_tools.setup.orchestrator import SetupOrchestrator
from ark_tools.setup.configurator import ServiceMode

console = Console()

class SetupCLI:
    """
    Command-line interface for ARK-TOOLS setup
    """
    
    def __init__(self):
        self.orchestrator = SetupOrchestrator()
        self.console = console
    
    def print_banner(self) -> None:
        """Print welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════╗
║       🚀 ARK-TOOLS Setup Assistant 🚀                ║
║                                                       ║
║  Intelligent Configuration for Code Consolidation    ║
╚═══════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")
    
    async def run_interactive(self) -> None:
        """Run interactive setup"""
        self.print_banner()
        
        # Choose setup mode
        setup_mode = Prompt.ask(
            "\nSetup Mode",
            choices=["quick", "custom", "minimal"],
            default="quick"
        )
        
        if setup_mode == "quick":
            await self.quick_setup()
        elif setup_mode == "custom":
            await self.custom_setup()
        else:
            await self.minimal_setup()
    
    async def quick_setup(self) -> None:
        """Run quick setup with intelligent defaults"""
        self.console.print("\n[bold]Quick Setup[/bold] - Detecting environment...\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            # Detect environment
            task = progress.add_task("Scanning for environment files...", total=None)
            envs = await self.orchestrator.detect_environment_async()
            progress.update(task, completed=True)
            
            # Show detected environments
            if envs:
                self.display_environments(envs)
                
                # Select parent environment
                parent_env = self.orchestrator.env_detector.get_parent_project_env()
                if parent_env:
                    use_parent = Confirm.ask(
                        f"\nUse [cyan]{parent_env.project_name}[/cyan] as parent project?",
                        default=True
                    )
                    if use_parent:
                        self.orchestrator.selected_env = parent_env
            
            # Detect services
            task = progress.add_task("Detecting services...", total=None)
            services = await self.orchestrator.detect_services_async()
            progress.update(task, completed=True)
        
        # Show detected services
        if services:
            self.display_services(services)
        
        # Run quick setup
        self.console.print("\n[bold]Configuring ARK-TOOLS...[/bold]\n")
        
        success, message = self.orchestrator.quick_setup(
            self.orchestrator.selected_env.path if self.orchestrator.selected_env else None
        )
        
        if success:
            self.console.print(f"[green]✅ {message}[/green]\n")
            
            # Show configuration preview
            self.show_configuration_preview()
            
            # Test connections
            if Confirm.ask("\nTest service connections?", default=True):
                await self.test_connections()
            
            # Save configuration
            if Confirm.ask("\nSave configuration?", default=True):
                self.save_configuration()
        else:
            self.console.print(f"[red]❌ {message}[/red]")
    
    async def custom_setup(self) -> None:
        """Run custom setup with user choices"""
        self.console.print("\n[bold]Custom Setup[/bold]\n")
        
        # Detect environment
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Scanning for environment files...", total=None)
            envs = await self.orchestrator.detect_environment_async()
            progress.update(task, completed=True)
        
        # Select environment to inherit from
        if envs:
            self.display_environments(envs)
            
            env_choices = [f"{i+1}. {env.project_name or env.path}" for i, env in enumerate(envs)]
            env_choices.append(f"{len(envs)+1}. None (start fresh)")
            
            choice = IntPrompt.ask(
                "\nSelect environment to inherit from",
                default=len(envs)+1,
                choices=[str(i) for i in range(1, len(envs)+2)]
            )
            
            if choice <= len(envs):
                selected_env = envs[choice-1]
                
                # Choose what to inherit
                inherit_options = []
                if selected_env.has_database:
                    if Confirm.ask("Inherit database credentials?", default=True):
                        inherit_options.extend(['DATABASE_URL', 'POSTGRES_URL'])
                
                if selected_env.has_redis:
                    if Confirm.ask("Inherit Redis configuration?", default=True):
                        inherit_options.extend(['REDIS_URL', 'REDIS_HOST'])
                
                if selected_env.has_ai_keys:
                    if Confirm.ask("Inherit AI API keys?", default=True):
                        inherit_options.extend(['OPENAI_API_KEY', 'ANTHROPIC_API_KEY'])
                
                if inherit_options:
                    self.orchestrator.configurator.inherit_from_env(selected_env, inherit_options)
        
        # Detect and configure services
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Detecting services...", total=None)
            services = await self.orchestrator.detect_services_async()
            progress.update(task, completed=True)
        
        if services:
            self.display_services(services)
            
            # Check system resources first
            self.console.print("\n[bold]System Resource Check[/bold]")
            from ark_tools.setup.system_checker import SystemChecker
            checker = SystemChecker()
            resources = checker.check_system_resources()
            
            if not resources.can_run_ark_tools:
                self.console.print("[red]⚠️ System resource warnings detected:[/red]")
                for warning in resources.warnings:
                    self.console.print(f"  {warning}")
                for rec in resources.recommendations:
                    self.console.print(f"  {rec}")
                
                if not Confirm.ask("\nContinue despite warnings?", default=False):
                    return
            else:
                self.console.print("[green]✅ System resources adequate[/green]")
                self.console.print(f"  CPU: {resources.cpu_count} cores")
                self.console.print(f"  RAM: {resources.memory_available_gb:.1f}GB available")
                self.console.print(f"  Disk: {resources.disk_available_gb:.1f}GB available")
                if resources.docker_available:
                    self.console.print(f"  Docker: Available ({resources.docker_running_containers} containers running)")
                else:
                    self.console.print("  Docker: [yellow]Not available[/yellow]")
            
            # Configure ARK-TOOLS Container
            ark_services = [s for s in services if s.service_type == 'ark-tools']
            ark_configured = False
            
            if ark_services:
                self.console.print("\n[bold]ARK-TOOLS Container Configuration[/bold]")
                self.console.print("[green]Found existing ARK-TOOLS container![/green]")
                ark_service = ark_services[0]
                self.console.print(f"  Container: {ark_service.container_name}")
                self.console.print(f"  Status: {'Running' if ark_service.is_running else 'Stopped'}")
                
                mode = Prompt.ask(
                    "How to proceed?",
                    choices=["use_existing", "create_new", "skip"],
                    default="use_existing"
                )
                
                if mode == "use_existing":
                    self.console.print("[green]✅ Will use existing ARK-TOOLS container[/green]")
                    ark_configured = True
                elif mode == "create_new":
                    self.console.print("[yellow]Will create new ARK-TOOLS container[/yellow]")
                    ark_configured = True
            else:
                self.console.print("\n[bold]ARK-TOOLS Container Setup[/bold]")
                self.console.print("[yellow]No ARK-TOOLS container detected[/yellow]")
                
                if resources.docker_available:
                    if Confirm.ask("Create ARK-TOOLS container for optimized execution?", default=True):
                        self.console.print("[green]✅ Will create ARK-TOOLS container[/green]")
                        ark_configured = True
                    else:
                        self.console.print("[yellow]⚠️ Running on host (less isolated)[/yellow]")
                else:
                    self.console.print("[yellow]Docker not available - will run on host[/yellow]")
            
            # Store ARK-TOOLS configuration
            self.orchestrator.configurator.config.use_ark_tools_container = ark_configured
            
            # Configure PostgreSQL
            pg_services = [s for s in services if s.service_type == 'postgresql']
            if pg_services:
                self.console.print("\n[bold]PostgreSQL Configuration[/bold]")
                pg_service = self.select_service(pg_services, "PostgreSQL")
                
                if pg_service:
                    mode = Prompt.ask(
                        "Configuration mode",
                        choices=["use_existing", "create_new", "skip"],
                        default="use_existing"
                    )
                    
                    if mode != "skip":
                        database_name = Prompt.ask("Database name", default="ark_tools")
                        
                        config = self.orchestrator.configurator.configure_from_detected_service(
                            pg_service,
                            ServiceMode(mode),
                            database_name=database_name
                        )
                        self.orchestrator.configurator.config.postgresql = config
            
            # Configure Redis
            redis_services = [s for s in services if s.service_type == 'redis']
            if redis_services:
                self.console.print("\n[bold]Redis Configuration[/bold]")
                redis_service = self.select_service(redis_services, "Redis")
                
                if redis_service:
                    mode = Prompt.ask(
                        "Configuration mode",
                        choices=["share_existing", "create_new", "skip"],
                        default="share_existing"
                    )
                    
                    if mode != "skip":
                        if mode == "share_existing":
                            db_number = IntPrompt.ask("Database number", default=2, choices=list(range(16)))
                        else:
                            db_number = 0
                        
                        config = self.orchestrator.configurator.configure_from_detected_service(
                            redis_service,
                            ServiceMode(mode),
                            database_number=db_number
                        )
                        self.orchestrator.configurator.config.redis = config
        
        # Feature configuration
        self.console.print("\n[bold]Feature Configuration[/bold]")
        self.orchestrator.configurator.config.enable_websockets = Confirm.ask(
            "Enable WebSocket support?", default=True
        )
        self.orchestrator.configurator.config.enable_monitoring = Confirm.ask(
            "Enable monitoring (Prometheus/Grafana)?", default=True
        )
        self.orchestrator.configurator.config.enable_security_scan = Confirm.ask(
            "Enable security scanning?", default=True
        )
        
        # Generate secrets
        self.orchestrator.configurator.generate_secrets()
        
        # Detect MAMS
        self.orchestrator.configurator.detect_mams_path()
        
        # Show configuration
        self.show_configuration_preview()
        
        # Test connections
        if Confirm.ask("\nTest service connections?", default=True):
            await self.test_connections()
        
        # Save configuration
        if Confirm.ask("\nSave configuration?", default=True):
            self.save_configuration()
    
    async def minimal_setup(self) -> None:
        """Run minimal setup without external dependencies"""
        self.console.print("\n[bold]Minimal Setup[/bold] - No external dependencies\n")
        
        self.orchestrator.configurator.create_minimal_config()
        
        self.console.print("[green]✅ Minimal configuration created[/green]")
        self.console.print("  • Using SQLite for database (fallback mode)")
        self.console.print("  • No Redis caching")
        self.console.print("  • No monitoring stack")
        
        # Show configuration
        self.show_configuration_preview()
        
        # Save configuration
        if Confirm.ask("\nSave configuration?", default=True):
            self.save_configuration()
    
    def display_environments(self, envs: List[Any]) -> None:
        """Display detected environments in a table"""
        table = Table(title="Detected Environment Files")
        table.add_column("Project", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Services", style="yellow")
        
        for env in envs:
            services = []
            if env.has_database:
                services.append("🗄️ DB")
            if env.has_redis:
                services.append("📦 Redis")
            if env.has_ai_keys:
                services.append("🤖 AI")
            
            table.add_row(
                env.project_name or "Unknown",
                env.path,
                " ".join(services)
            )
        
        self.console.print(table)
    
    def display_services(self, services: List[Any]) -> None:
        """Display detected services in a table"""
        table = Table(title="Detected Services")
        table.add_column("Service", style="cyan")
        table.add_column("Source", style="green")
        table.add_column("Host:Port", style="yellow")
        table.add_column("Status", style="magenta")
        
        for service in services:
            status = "🟢 Running" if service.is_running else "🔴 Stopped"
            source_emoji = {
                'docker': "🐳",
                'native': "💻",
                'env_file': "📄"
            }.get(service.source, "")
            
            table.add_row(
                service.service_type.upper(),
                f"{source_emoji} {service.source}",
                f"{service.host}:{service.port}",
                status
            )
        
        self.console.print(table)
    
    def select_service(self, services: List[Any], service_type: str) -> Optional[Any]:
        """Let user select a service from list"""
        if len(services) == 1:
            return services[0]
        
        choices = []
        for i, service in enumerate(services):
            status = "Running" if service.is_running else "Stopped"
            choices.append(f"{i+1}. {service.host}:{service.port} ({status})")
        choices.append(f"{len(services)+1}. None")
        
        choice = IntPrompt.ask(
            f"\nSelect {service_type} service",
            default=1,
            choices=[str(i) for i in range(1, len(services)+2)]
        )
        
        if choice <= len(services):
            return services[choice-1]
        return None
    
    def show_configuration_preview(self) -> None:
        """Show configuration preview"""
        self.console.print("\n[bold]Configuration Preview[/bold]\n")
        
        # Generate configuration content
        env_content = self.orchestrator.configurator.config.to_env_content()
        
        # Display with syntax highlighting
        syntax = Syntax(env_content, "bash", theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=".env", border_style="green"))
    
    async def test_connections(self) -> None:
        """Test service connections"""
        self.console.print("\n[bold]Testing Connections...[/bold]\n")
        
        results = await self.orchestrator.test_all_connections()
        
        for service, result in results.items():
            if result['connected']:
                self.console.print(f"[green]✅ {service}: {result['message']}[/green]")
            else:
                self.console.print(f"[red]❌ {service}: {result['message']}[/red]")
    
    def save_configuration(self) -> None:
        """Save configuration to files"""
        output_dir = Prompt.ask("\nOutput directory", default=".")
        
        success, files = self.orchestrator.save_configuration(output_dir)
        
        if success:
            self.console.print(f"\n[green]✅ Configuration saved successfully![/green]")
            self.console.print("\nCreated files:")
            for file in files:
                self.console.print(f"  • {file}")
            
            # Show next steps
            self.console.print("\n[bold]Next Steps:[/bold]")
            for step in self.orchestrator.get_next_steps():
                self.console.print(f"  {step}")
        else:
            self.console.print("[red]❌ Failed to save configuration[/red]")

@click.group()
def cli():
    """ARK-TOOLS Setup Assistant"""
    pass

@cli.command()
@click.option('--mode', type=click.Choice(['quick', 'custom', 'minimal']), default='quick',
              help='Setup mode')
@click.option('--parent-env', type=click.Path(exists=True), 
              help='Parent environment file to inherit from')
@click.option('--output-dir', type=click.Path(), default='.',
              help='Output directory for configuration files')
def setup(mode, parent_env, output_dir):
    """Run ARK-TOOLS setup"""
    setup_cli = SetupCLI()
    
    if mode == 'quick' and parent_env:
        # Non-interactive quick setup
        orchestrator = setup_cli.orchestrator
        success, message = orchestrator.quick_setup(parent_env)
        
        if success:
            click.echo(click.style(f"✅ {message}", fg='green'))
            success, files = orchestrator.save_configuration(output_dir)
            if success:
                click.echo(f"Configuration saved to: {', '.join(files)}")
            else:
                click.echo(click.style("Failed to save configuration", fg='red'))
        else:
            click.echo(click.style(f"❌ {message}", fg='red'))
    else:
        # Interactive setup
        asyncio.run(setup_cli.run_interactive())

@cli.command()
@click.option('--port', type=int, default=None, help='Port to run web UI on (auto-detect if not specified)')
def web(port):
    """Launch web-based setup UI"""
    from ark_tools.setup.web import run_web_ui
    # run_web_ui will handle port detection and display the URL
    run_web_ui(port=port)

@cli.command()
def tui():
    """Launch terminal UI for setup"""
    from ark_tools.setup.tui import run_tui
    run_tui()

@cli.command()
@click.option('--build', is_flag=True, help='Build containers before starting')
@click.option('--detach', is_flag=True, default=True, help='Run containers in detached mode')
def start(build, detach):
    """Start ARK-TOOLS containers"""
    import subprocess
    from pathlib import Path
    
    # Check if docker-compose.yml exists
    if not Path('docker-compose.yml').exists():
        click.echo(click.style("No docker-compose.yml found. Run 'ark-setup' first.", fg='red'))
        return
    
    click.echo(click.style("Starting ARK-TOOLS containers...", fg='cyan'))
    
    try:
        # Build if requested
        if build:
            click.echo("Building containers...")
            result = subprocess.run(['docker-compose', 'build'], capture_output=True, text=True)
            if result.returncode != 0:
                click.echo(click.style(f"Build failed: {result.stderr}", fg='red'))
                return
        
        # Start containers
        cmd = ['docker-compose', 'up']
        if detach:
            cmd.append('-d')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            if detach:
                click.echo(click.style("✅ Containers started successfully!", fg='green'))
                click.echo("\nRunning containers:")
                subprocess.run(['docker-compose', 'ps'])
                
                # Show access URLs
                click.echo("\n📍 Access URLs:")
                if Path('.env').exists():
                    import re
                    with open('.env') as f:
                        content = f.read()
                        port_match = re.search(r'ARK_TOOLS_PORT=(\d+)', content)
                        port = port_match.group(1) if port_match else '8100'
                        click.echo(f"  ARK-TOOLS: http://localhost:{port}")
            else:
                click.echo(click.style("Containers running in foreground mode...", fg='cyan'))
        else:
            click.echo(click.style(f"Failed to start containers: {result.stderr}", fg='red'))
    except FileNotFoundError:
        click.echo(click.style("Docker Compose not installed. Please install it first.", fg='red'))
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))

@cli.command()
def stop():
    """Stop ARK-TOOLS containers"""
    import subprocess
    from pathlib import Path
    
    if not Path('docker-compose.yml').exists():
        click.echo(click.style("No docker-compose.yml found.", fg='red'))
        return
    
    click.echo(click.style("Stopping ARK-TOOLS containers...", fg='cyan'))
    
    try:
        result = subprocess.run(['docker-compose', 'down'], capture_output=True, text=True)
        
        if result.returncode == 0:
            click.echo(click.style("✅ Containers stopped successfully!", fg='green'))
        else:
            click.echo(click.style(f"Failed to stop containers: {result.stderr}", fg='red'))
    except FileNotFoundError:
        click.echo(click.style("Docker Compose not installed.", fg='red'))
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))

@cli.command()
def logs():
    """View ARK-TOOLS container logs"""
    import subprocess
    from pathlib import Path
    
    if not Path('docker-compose.yml').exists():
        click.echo(click.style("No docker-compose.yml found.", fg='red'))
        return
    
    try:
        subprocess.run(['docker-compose', 'logs', '-f'])
    except FileNotFoundError:
        click.echo(click.style("Docker Compose not installed.", fg='red'))
    except KeyboardInterrupt:
        click.echo("\nStopped viewing logs.")

@cli.command()
def validate():
    """Validate existing configuration"""
    setup_cli = SetupCLI()
    orchestrator = setup_cli.orchestrator
    
    # Try to load existing .env
    env_path = Path('.env')
    if not env_path.exists():
        click.echo(click.style("No .env file found", fg='red'))
        return
    
    click.echo("Validating configuration...")
    
    # Run connection tests
    async def run_tests():
        results = await orchestrator.test_all_connections()
        for service, result in results.items():
            if result['connected']:
                click.echo(click.style(f"✅ {service}: {result['message']}", fg='green'))
            else:
                click.echo(click.style(f"❌ {service}: {result['message']}", fg='red'))
    
    asyncio.run(run_tests())

if __name__ == '__main__':
    cli()