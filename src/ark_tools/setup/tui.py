"""
Terminal User Interface for ARK-TOOLS Setup
============================================

Beautiful terminal UI using Textual for interactive configuration.
"""

from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
import asyncio
from datetime import datetime

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header, Footer, Static, Button, Label, Select, Input,
    RadioButton, RadioSet, Checkbox, DataTable, ProgressBar,
    TabbedContent, TabPane, TextArea, Tree
)
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from ark_tools.setup.detector import (
    EnvironmentDetector, ServiceDetector, 
    DetectedService, DetectedEnvironment
)
from ark_tools.setup.configurator import (
    SetupConfigurator, ServiceMode, ServiceConfig, ARKToolsConfig
)
from ark_tools.setup.validator import ConnectionValidator

class ServiceCard(Static):
    """Widget displaying a detected service"""
    
    def __init__(self, service: DetectedService, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        
    def compose(self) -> ComposeResult:
        """Compose the service card"""
        status_emoji = "🟢" if self.service.is_running else "🔴"
        source_emoji = {
            'docker': "🐳",
            'native': "💻",
            'env_file': "📄"
        }.get(self.service.source, "❓")
        
        yield Static(
            f"{status_emoji} {self.service.service_type.upper()} {source_emoji}",
            classes="service-title"
        )
        yield Static(f"Host: {self.service.host}:{self.service.port}")
        
        if self.service.container_name:
            yield Static(f"Container: {self.service.container_name}")
        
        if self.service.version:
            yield Static(f"Version: {self.service.version}")
        
        if self.service.warnings:
            for warning in self.service.warnings:
                yield Static(f"⚠️  {warning}", classes="warning")

class EnvironmentCard(Static):
    """Widget displaying a detected environment file"""
    
    def __init__(self, env: DetectedEnvironment, **kwargs):
        super().__init__(**kwargs)
        self.env = env
        
    def compose(self) -> ComposeResult:
        """Compose the environment card"""
        yield Static(f"📁 {self.env.project_name or 'Unknown Project'}", classes="env-title")
        yield Static(f"Path: {self.env.path}")
        
        services = []
        if self.env.has_database:
            services.append("🗄️ Database")
        if self.env.has_redis:
            services.append("📦 Redis")
        if self.env.has_ai_keys:
            services.append("🤖 AI Keys")
        
        if services:
            yield Static(f"Services: {', '.join(services)}")
        
        yield Static(f"Variables: {len(self.env.variables)}")

class ServiceConfigScreen(ModalScreen):
    """Modal screen for configuring a service"""
    
    def __init__(self, service: DetectedService, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.result = None
        
    def compose(self) -> ComposeResult:
        """Compose the configuration screen"""
        with Container(id="service-config-modal"):
            yield Static(f"Configure {self.service.service_type.upper()}", classes="modal-title")
            
            yield Static("How would you like to use this service?")
            
            with RadioSet(id="service-mode"):
                yield RadioButton("Use existing (recommended)", value=True)
                yield RadioButton("Share existing (different database/schema)")
                yield RadioButton("Create new instance")
                yield RadioButton("Skip this service")
            
            if self.service.service_type == 'postgresql':
                yield Label("Database name:")
                yield Input(value="ark_tools", id="database-name")
                
                yield Checkbox("Install pgvector extension", value=True, id="install-pgvector")
            
            elif self.service.service_type == 'redis':
                yield Label("Database number (0-15):")
                yield Input(value="2", id="database-number")
            
            with Horizontal(classes="modal-buttons"):
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", id="cancel")
    
    @on(Button.Pressed, "#ok")
    def handle_ok(self) -> None:
        """Handle OK button"""
        mode_widget = self.query_one("#service-mode", RadioSet)
        selected_index = mode_widget._selected
        
        modes = [
            ServiceMode.USE_EXISTING,
            ServiceMode.SHARE_EXISTING,
            ServiceMode.CREATE_NEW,
            ServiceMode.SKIP
        ]
        
        self.result = {
            'mode': modes[selected_index] if selected_index >= 0 else ServiceMode.USE_EXISTING
        }
        
        # Add service-specific options
        if self.service.service_type == 'postgresql':
            self.result['database_name'] = self.query_one("#database-name", Input).value
            self.result['install_pgvector'] = self.query_one("#install-pgvector", Checkbox).value
        elif self.service.service_type == 'redis':
            self.result['database_number'] = int(self.query_one("#database-number", Input).value)
        
        self.dismiss(self.result)
    
    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        """Handle cancel button"""
        self.dismiss(None)

class SetupTUI(App):
    """Main TUI application for ARK-TOOLS setup"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .service-title {
        text-style: bold;
        color: $primary;
    }
    
    .env-title {
        text-style: bold;
        color: $secondary;
    }
    
    .warning {
        color: $warning;
    }
    
    .success {
        color: $success;
    }
    
    .error {
        color: $error;
    }
    
    ServiceCard {
        border: solid $primary;
        padding: 1;
        margin: 1;
        height: auto;
    }
    
    EnvironmentCard {
        border: solid $secondary;
        padding: 1;
        margin: 1;
        height: auto;
    }
    
    #service-config-modal {
        border: thick $primary;
        background: $surface;
        padding: 2;
        width: 60;
        height: auto;
    }
    
    .modal-title {
        text-style: bold;
        text-align: center;
        padding: 1;
    }
    
    .modal-buttons {
        margin-top: 1;
        align: center middle;
    }
    
    .step-container {
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    .step-title {
        text-style: bold;
        color: $primary;
        padding: 1;
    }
    
    ProgressBar {
        margin: 1;
    }
    
    #config-preview {
        border: solid $secondary;
        padding: 1;
        margin: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("n", "next_step", "Next"),
        Binding("p", "prev_step", "Previous"),
        Binding("s", "save", "Save Config"),
    ]
    
    def __init__(self):
        super().__init__()
        self.env_detector = EnvironmentDetector()
        self.service_detector = ServiceDetector()
        self.configurator = SetupConfigurator()
        self.validator = ConnectionValidator()
        
        self.detected_envs: List[DetectedEnvironment] = []
        self.detected_services: List[DetectedService] = []
        self.selected_env: Optional[DetectedEnvironment] = None
        self.service_configs: Dict[str, ServiceConfig] = {}
        
        self.current_step = 0
        self.steps = [
            "Environment Detection",
            "Service Discovery",
            "Service Configuration",
            "Credential Inheritance",
            "Review & Save"
        ]
    
    def compose(self) -> ComposeResult:
        """Compose the main application"""
        yield Header(show_clock=True)
        yield Footer()
        
        with TabbedContent(*[f"Step {i+1}: {step}" for i, step in enumerate(self.steps)]):
            # Step 1: Environment Detection
            with TabPane("Step 1: Environment Detection"):
                yield Static("🔍 Scanning for environment files...", classes="step-title")
                yield ScrollableContainer(id="env-container")
                yield Button("Select Parent Environment", id="select-env", variant="primary")
            
            # Step 2: Service Discovery
            with TabPane("Step 2: Service Discovery"):
                yield Static("🔍 Detecting services...", classes="step-title")
                yield ScrollableContainer(id="service-container")
                yield Button("Refresh Services", id="refresh-services")
            
            # Step 3: Service Configuration
            with TabPane("Step 3: Service Configuration"):
                yield Static("⚙️ Configure Services", classes="step-title")
                yield ScrollableContainer(id="config-container")
            
            # Step 4: Credential Inheritance
            with TabPane("Step 4: Credential Inheritance"):
                yield Static("🔑 Select credentials to inherit", classes="step-title")
                yield ScrollableContainer(id="credential-container")
            
            # Step 5: Review & Save
            with TabPane("Step 5: Review & Save"):
                yield Static("📋 Configuration Preview", classes="step-title")
                yield TextArea(id="config-preview", read_only=True)
                with Horizontal():
                    yield Button("Test Connections", id="test-connections")
                    yield Button("Save Configuration", id="save-config", variant="success")
                yield Static(id="save-status")
    
    def on_mount(self) -> None:
        """Called when app starts"""
        self.scan_environment()
        self.detect_services()
    
    @work(thread=True)
    def scan_environment(self) -> None:
        """Scan for environment files"""
        self.detected_envs = self.env_detector.scan_for_env_files()
        self.call_from_thread(self.update_env_display)
    
    @work(thread=True)
    def detect_services(self) -> None:
        """Detect available services"""
        self.detected_services = []
        
        # Scan Docker containers
        docker_services = self.service_detector.scan_docker_containers()
        self.detected_services.extend(docker_services)
        
        # Scan system services
        system_services = self.service_detector.scan_system_services()
        self.detected_services.extend(system_services)
        
        # Merge with environment information
        self.detected_services = self.service_detector.merge_with_env_services(self.env_detector)
        
        self.call_from_thread(self.update_service_display)
    
    def update_env_display(self) -> None:
        """Update environment display"""
        container = self.query_one("#env-container", ScrollableContainer)
        
        # Clear existing content
        for child in list(container.children):
            child.remove()
        
        if not self.detected_envs:
            container.mount(Static("No environment files found", classes="warning"))
        else:
            for env in self.detected_envs:
                card = EnvironmentCard(env)
                container.mount(card)
        
        # Auto-select parent project if found
        parent_env = self.env_detector.get_parent_project_env()
        if parent_env:
            self.selected_env = parent_env
            container.mount(Static(f"✅ Selected: {parent_env.path}", classes="success"))
    
    def update_service_display(self) -> None:
        """Update service display"""
        container = self.query_one("#service-container", ScrollableContainer)
        
        # Clear existing content
        for child in list(container.children):
            child.remove()
        
        if not self.detected_services:
            container.mount(Static("No services detected", classes="warning"))
        else:
            # Group services by type
            postgres_services = [s for s in self.detected_services if s.service_type == 'postgresql']
            redis_services = [s for s in self.detected_services if s.service_type == 'redis']
            
            if postgres_services:
                container.mount(Static("PostgreSQL Services:", classes="step-title"))
                for service in postgres_services:
                    card = ServiceCard(service)
                    card.on_click = lambda s=service: self.configure_service(s)
                    container.mount(card)
            
            if redis_services:
                container.mount(Static("Redis Services:", classes="step-title"))
                for service in redis_services:
                    card = ServiceCard(service)
                    card.on_click = lambda s=service: self.configure_service(s)
                    container.mount(card)
        
        self.update_config_display()
    
    def update_config_display(self) -> None:
        """Update configuration display"""
        container = self.query_one("#config-container", ScrollableContainer)
        
        # Clear existing content
        for child in list(container.children):
            child.remove()
        
        # Show current configuration
        for service_type, config in self.service_configs.items():
            container.mount(Static(f"{service_type}: {config.mode.value}", classes="success"))
    
    async def configure_service(self, service: DetectedService) -> None:
        """Open configuration modal for a service"""
        screen = ServiceConfigScreen(service)
        result = await self.push_screen_wait(screen)
        
        if result:
            # Apply configuration
            config = self.configurator.configure_from_detected_service(
                service, 
                result['mode'],
                **result
            )
            
            if service.service_type == 'postgresql':
                self.configurator.config.postgresql = config
            elif service.service_type == 'redis':
                self.configurator.config.redis = config
            
            self.service_configs[service.service_type] = config
            self.update_config_display()
            self.update_preview()
    
    def update_preview(self) -> None:
        """Update configuration preview"""
        preview = self.query_one("#config-preview", TextArea)
        
        # Generate configuration preview
        self.configurator.generate_secrets()
        
        if self.selected_env:
            # Inherit from selected environment
            inherit_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
            self.configurator.inherit_from_env(self.selected_env, inherit_keys)
        
        # Detect MAMS
        self.configurator.detect_mams_path()
        
        # Generate preview
        env_content = self.configurator.config.to_env_content()
        preview.load_text(env_content)
    
    @on(Button.Pressed, "#select-env")
    def handle_select_env(self) -> None:
        """Handle environment selection"""
        # TODO: Implement environment selection dialog
        pass
    
    @on(Button.Pressed, "#refresh-services")
    def handle_refresh_services(self) -> None:
        """Handle service refresh"""
        self.detect_services()
    
    @on(Button.Pressed, "#test-connections")
    @work(thread=True)
    async def handle_test_connections(self) -> None:
        """Test service connections"""
        status_widget = self.query_one("#save-status", Static)
        
        # Test PostgreSQL
        if self.configurator.config.postgresql:
            pg_config = self.configurator.config.postgresql
            pg_result = await self.validator.test_postgresql(
                pg_config.host,
                pg_config.port,
                pg_config.credentials.get('username'),
                pg_config.credentials.get('password'),
                pg_config.credentials.get('database')
            )
            
            if pg_result['connected']:
                self.call_from_thread(
                    lambda: status_widget.update("✅ PostgreSQL connection successful")
                )
            else:
                self.call_from_thread(
                    lambda: status_widget.update(f"❌ PostgreSQL: {pg_result['error']}")
                )
        
        # Test Redis
        if self.configurator.config.redis:
            redis_config = self.configurator.config.redis
            redis_result = await self.validator.test_redis(
                redis_config.host,
                redis_config.port,
                redis_config.credentials.get('password'),
                redis_config.database_number or 0
            )
            
            if redis_result['connected']:
                self.call_from_thread(
                    lambda: status_widget.update("✅ Redis connection successful")
                )
            else:
                self.call_from_thread(
                    lambda: status_widget.update(f"❌ Redis: {redis_result['error']}")
                )
    
    @on(Button.Pressed, "#save-config")
    def handle_save_config(self) -> None:
        """Handle configuration save"""
        status_widget = self.query_one("#save-status", Static)
        
        # Validate configuration
        is_valid, issues = self.configurator.config.validate_config()
        
        if not is_valid and issues:
            status_widget.update(f"⚠️ Configuration issues: {', '.join(issues)}")
            return
        
        # Save configuration
        output_dir = Path.cwd()
        success, files = self.configurator.config.save(output_dir)
        
        if success:
            status_widget.update(f"✅ Configuration saved: {', '.join(files)}")
            self.notify("Configuration saved successfully!", severity="success")
        else:
            status_widget.update("❌ Failed to save configuration")
            self.notify("Failed to save configuration", severity="error")
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()
    
    def action_refresh(self) -> None:
        """Refresh detection"""
        self.scan_environment()
        self.detect_services()
    
    def action_next_step(self) -> None:
        """Go to next step"""
        tabs = self.query_one(TabbedContent)
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            tabs.active = f"tab-{self.current_step}"
    
    def action_prev_step(self) -> None:
        """Go to previous step"""
        tabs = self.query_one(TabbedContent)
        if self.current_step > 0:
            self.current_step -= 1
            tabs.active = f"tab-{self.current_step}"
    
    def action_save(self) -> None:
        """Save configuration"""
        self.handle_save_config()

def run_tui():
    """Run the TUI application"""
    app = SetupTUI()
    app.run()