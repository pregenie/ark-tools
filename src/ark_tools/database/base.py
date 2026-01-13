"""
ARK-TOOLS Database Base Configuration
====================================

Base database configuration, connection management, and SQLAlchemy setup.
"""

import os
from typing import Optional, Any, Dict
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from ark_tools import config
from ark_tools.utils.debug_logger import debug_log

logger = logging.getLogger(__name__)

# SQLAlchemy declarative base
Base = declarative_base()

# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

Base.metadata = MetaData(naming_convention=convention)

class DatabaseManager:
    """
    Manages database connections and session lifecycle for ARK-TOOLS
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection URL (defaults to config)
        """
        self.database_url = database_url or config.DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        
        debug_log.database("Database Manager initialized")
        
        # Initialize connection
        self._create_engine()
        self._create_session_factory()
    
    def _create_engine(self) -> None:
        """Create SQLAlchemy engine with production-ready configuration"""
        try:
            # Parse database URL to check if it's PostgreSQL
            is_postgres = 'postgresql' in self.database_url
            
            # Engine configuration for production
            engine_kwargs = {
                'echo': False,  # Set to True for SQL debugging
                'pool_pre_ping': True,  # Validate connections before use
                'pool_recycle': 3600,  # Recycle connections every hour
            }
            
            if is_postgres:
                # PostgreSQL-specific optimizations
                engine_kwargs.update({
                    'poolclass': QueuePool,
                    'pool_size': 10,
                    'max_overflow': 20,
                    'connect_args': {
                        'connect_timeout': 10,
                        'application_name': 'ark_tools'
                    }
                })
            
            self.engine = create_engine(self.database_url, **engine_kwargs)
            
            debug_log.database("Database engine created successfully")
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
                debug_log.database("Database connection test successful")
        
        except Exception as e:
            debug_log.error_trace("Failed to create database engine", exception=e)
            raise
    
    def _create_session_factory(self) -> None:
        """Create session factory"""
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        debug_log.database("Session factory created")
    
    @contextmanager
    def get_session(self):
        """
        Get database session with automatic cleanup
        
        Yields:
            SQLAlchemy Session object
        """
        session = self.SessionLocal()
        try:
            debug_log.database("Database session created")
            yield session
            session.commit()
            debug_log.database("Database session committed")
        except Exception as e:
            session.rollback()
            debug_log.database(f"Database session rolled back due to error: {e}", level="ERROR")
            raise
        finally:
            session.close()
            debug_log.database("Database session closed")
    
    def create_tables(self) -> None:
        """Create all tables defined in models"""
        try:
            # Import all models to ensure they're registered
            from ark_tools.database.models import (
                analysis, project, transformation, user_session
            )
            
            debug_log.database("Creating database tables")
            Base.metadata.create_all(bind=self.engine)
            debug_log.database("Database tables created successfully")
        
        except Exception as e:
            debug_log.error_trace("Failed to create database tables", exception=e)
            raise
    
    def drop_tables(self) -> None:
        """Drop all tables (use with caution!)"""
        try:
            debug_log.database("Dropping database tables", level="WARNING")
            Base.metadata.drop_all(bind=self.engine)
            debug_log.database("Database tables dropped")
        
        except Exception as e:
            debug_log.error_trace("Failed to drop database tables", exception=e)
            raise
    
    def check_connection(self) -> Dict[str, Any]:
        """
        Check database connection and return status
        
        Returns:
            Dict with connection status information
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT version() as version, now() as timestamp")
                row = result.fetchone()
                
                status = {
                    'connected': True,
                    'database_version': row[0] if row else 'unknown',
                    'server_time': str(row[1]) if row and len(row) > 1 else 'unknown',
                    'connection_url': self._mask_password(self.database_url)
                }
                
                debug_log.database("Database connection check successful")
                return status
        
        except Exception as e:
            debug_log.error_trace("Database connection check failed", exception=e)
            return {
                'connected': False,
                'error': str(e),
                'connection_url': self._mask_password(self.database_url)
            }
    
    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging"""
        if '@' in url and '://' in url:
            try:
                # Split URL to hide password
                protocol, rest = url.split('://', 1)
                if '@' in rest:
                    auth, host = rest.split('@', 1)
                    if ':' in auth:
                        user, _ = auth.split(':', 1)
                        return f"{protocol}://{user}:***@{host}"
                return url
            except:
                return url.replace(':', ':***', 1) if ':' in url else url
        return url
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about database tables"""
        try:
            with self.engine.connect() as conn:
                # Get table information
                inspector = conn.dialect.get_table_names(conn)
                
                tables_info = {}
                for table_name in inspector:
                    try:
                        result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = result.scalar()
                        tables_info[table_name] = {'row_count': count}
                    except Exception as e:
                        tables_info[table_name] = {'error': str(e)}
                
                return {
                    'total_tables': len(inspector),
                    'tables': tables_info
                }
        
        except Exception as e:
            debug_log.error_trace("Failed to get table information", exception=e)
            return {'error': str(e)}
    
    def execute_raw_sql(self, sql: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute raw SQL (use with caution!)
        
        Args:
            sql: SQL statement to execute
            parameters: Optional parameters for the SQL
            
        Returns:
            Query result
        """
        try:
            with self.get_session() as session:
                debug_log.database(f"Executing raw SQL: {sql[:100]}...")
                result = session.execute(sql, parameters or {})
                return result
        
        except Exception as e:
            debug_log.error_trace(f"Raw SQL execution failed: {sql}", exception=e)
            raise
    
    def cleanup_sessions(self) -> None:
        """Cleanup expired database sessions"""
        try:
            if self.engine:
                self.engine.dispose()
                debug_log.database("Database connection pool disposed")
        
        except Exception as e:
            debug_log.error_trace("Failed to cleanup database sessions", exception=e)

# Global database manager instance
db_manager = DatabaseManager()