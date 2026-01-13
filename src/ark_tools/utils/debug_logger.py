"""
Structured Debug Logger for ARK-TOOLS
=====================================

Provides scoped debug logging with structured output for better debugging
and monitoring throughout the ARK-TOOLS system.
"""

import logging
import sys
import json
import traceback
import uuid
from typing import Any, Dict, Optional
from datetime import datetime

class StructuredDebugLogger:
    """Structured debug logger with scoped categories"""
    
    def __init__(self):
        self.logger = logging.getLogger('ark_tools')
        self._setup_formatter()
    
    def _setup_formatter(self) -> None:
        """Setup structured log formatter"""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
    
    def _log_structured(
        self, 
        message: str, 
        level: str = "INFO",
        category: str = "general",
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log structured message with category"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'message': message,
            'level': level
        }
        
        if extra:
            log_entry['extra'] = extra
        
        # Convert to proper logging level
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Create formatted message
        formatted_message = f"[{category.upper()}] {message}"
        if extra:
            formatted_message += f" | Extra: {json.dumps(extra, default=str)}"
        
        self.logger.log(log_level, formatted_message)
    
    def jwt(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log JWT-related operations"""
        self._log_structured(message, level, "jwt", extra)
    
    def auth(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log authentication operations"""
        self._log_structured(message, level, "auth", extra)
    
    def api(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log API operations"""
        self._log_structured(message, level, "api", extra)
    
    def analysis(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log code analysis operations"""
        self._log_structured(message, level, "analysis", extra)
    
    def transformation(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log code transformation operations"""
        self._log_structured(message, level, "transformation", extra)
    
    def agent(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log agent operations"""
        self._log_structured(message, level, "agent", extra)
    
    def safety(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log safety and security operations"""
        self._log_structured(message, level, "safety", extra)
    
    def database(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log database operations"""
        self._log_structured(message, level, "database", extra)
    
    def mams(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log MAMS integration operations"""
        self._log_structured(message, level, "mams", extra)
    
    def websocket(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log WebSocket operations"""
        self._log_structured(message, level, "websocket", extra)
    
    def performance(self, message: str, level: str = "DEBUG", extra: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics"""
        self._log_structured(message, level, "performance", extra)
    
    def error_trace(
        self, 
        message: str, 
        exception: Optional[Exception] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log error with full traceback"""
        error_id = str(uuid.uuid4())
        
        error_data = {
            'error_id': error_id,
            'message': message
        }
        
        if extra:
            error_data.update(extra)
        
        if exception:
            error_data.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            })
        
        self._log_structured(
            f"{message} (Error ID: {error_id})",
            level="ERROR",
            category="error",
            extra=error_data
        )
        
        return error_id

# Global debug logger instance
debug_log = StructuredDebugLogger()