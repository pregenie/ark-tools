#!/usr/bin/env python3
"""
MAMS Dedicated Logging System
Separate from unified logging - tracks MAMS operations, execution state, and audit trail
"""

import os
import sys
import json
import uuid
import asyncio
import asyncpg
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class MAMSLogger:
    """
    Dedicated MAMS logging system
    Separate from unified logging - focuses on MAMS operations and audit trail
    """
    
    def __init__(self, component: str, execution_scope: str = None):
        self.component = component  # e.g., 'MAMS-002'
        self.execution_scope = execution_scope  # e.g., 'backend', 'frontend'
        self.execution_id = None
        self.conn = None
        self.start_time = None
        
    @asynccontextmanager
    async def execution_context(self, execution_type: str, **kwargs):
        """Context manager for MAMS execution logging"""
        self.execution_id = str(uuid.uuid4())
        self.start_time = datetime.utcnow()
        
        self.conn = await asyncpg.connect("postgresql://admin:chooters@db:5432/arkyvus_db")
        
        try:
            # Start execution log
            await self._log_execution_start(execution_type, **kwargs)
            
            yield self
            
            # Complete execution log
            await self._log_execution_complete()
            
        except Exception as e:
            # Log execution failure
            await self._log_execution_failed(str(e))
            raise
        finally:
            if self.conn:
                await self.conn.close()
    
    async def _log_execution_start(self, execution_type: str, **kwargs):
        """Log start of MAMS execution"""
        await self.conn.execute("""
            INSERT INTO mams_execution_log 
            (id, mams_component, execution_type, execution_scope, start_time, status,
             executor_host, executor_container, command_executed, input_parameters)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        self.execution_id,
        self.component,
        execution_type,
        self.execution_scope,
        self.start_time,
        'running',
        os.uname().nodename,
        os.environ.get('HOSTNAME', 'unknown'),
        ' '.join(sys.argv),
        json.dumps(kwargs))
        
        print(f"🚀 {self.component} Execution Started - ID: {self.execution_id}")
    
    async def _log_execution_complete(self):
        """Log successful completion of MAMS execution"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        await self.conn.execute("""
            UPDATE mams_execution_log 
            SET end_time = $1,
                status = 'completed',
                performance_metrics = jsonb_set(
                    COALESCE(performance_metrics, '{}'),
                    '{execution_duration_seconds}',
                    to_jsonb($2::float)
                )
            WHERE id = $3
        """, end_time, duration, self.execution_id)
        
        print(f"✅ {self.component} Execution Completed - Duration: {duration:.2f}s")
    
    async def _log_execution_failed(self, error_message: str):
        """Log failed MAMS execution"""
        end_time = datetime.utcnow()
        
        await self.conn.execute("""
            UPDATE mams_execution_log 
            SET end_time = $1,
                status = 'failed',
                errors_count = errors_count + 1,
                error_details = jsonb_set(
                    COALESCE(error_details, '{}'),
                    '{error_message}',
                    to_jsonb($2)
                )
            WHERE id = $3
        """, end_time, error_message, self.execution_id)
        
        print(f"❌ {self.component} Execution Failed - Error: {error_message}")
    
    async def log_discovery_progress(self, 
                                   items_processed: int,
                                   items_created: int = 0,
                                   items_updated: int = 0,
                                   items_skipped: int = 0):
        """Log discovery progress"""
        await self.conn.execute("""
            UPDATE mams_execution_log 
            SET items_processed = $1,
                items_created = $2,
                items_updated = $3,
                items_skipped = $4
            WHERE id = $5
        """, items_processed, items_created, items_updated, items_skipped, self.execution_id)
    
    async def log_phase_completion(self, phase_name: str, results: Dict[str, Any]):
        """Log completion of a specific phase within MAMS execution"""
        await self.conn.execute("""
            UPDATE mams_execution_log 
            SET execution_results = jsonb_set(
                COALESCE(execution_results, '{}'),
                '{phase}',
                $1
            )
            WHERE id = $2
        """, json.dumps({phase_name: results}), self.execution_id)
        
        print(f"📋 {self.component} Phase '{phase_name}' completed")
    
    async def log_fingerprint(self, fingerprint: str):
        """Log source fingerprint for deduplication"""
        await self.conn.execute("""
            UPDATE mams_execution_log 
            SET source_fingerprint = $1
            WHERE id = $2
        """, fingerprint, self.execution_id)
    
    async def log_previous_execution_link(self, previous_execution_id: str):
        """Link to previous execution for incremental updates"""
        await self.conn.execute("""
            UPDATE mams_execution_log 
            SET previous_execution_id = $1
            WHERE id = $2
        """, previous_execution_id, self.execution_id)
    
    def info(self, message: str, **kwargs):
        """Log info message with MAMS context"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        context = f"[{self.component}:{self.execution_id[:8] if self.execution_id else 'init'}]"
        print(f"{timestamp} INFO {context} {message}")
        
        if kwargs:
            print(f"  └─ {json.dumps(kwargs, default=str)}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message with MAMS context"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        context = f"[{self.component}:{self.execution_id[:8] if self.execution_id else 'init'}]"
        print(f"{timestamp} WARN {context} ⚠️ {message}")
        
        if kwargs:
            print(f"  └─ {json.dumps(kwargs, default=str)}")
    
    def error(self, message: str, **kwargs):
        """Log error message with MAMS context"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        context = f"[{self.component}:{self.execution_id[:8] if self.execution_id else 'init'}]"
        print(f"{timestamp} ERROR {context} ❌ {message}")
        
        if kwargs:
            print(f"  └─ {json.dumps(kwargs, default=str)}")

class MAMSAuditLogger:
    """
    MAMS audit logging utilities
    Provides audit trail queries and analysis
    """
    
    @staticmethod
    async def get_execution_history(component: str = None, days: int = 30) -> List[Dict]:
        """Get MAMS execution history"""
        conn = await asyncpg.connect("postgresql://admin:chooters@db:5432/arkyvus_db")
        try:
            where_clause = ""
            params = [days]
            
            if component:
                where_clause = "AND mams_component = $2"
                params.append(component)
            
            records = await conn.fetch(f"""
                SELECT 
                    id,
                    mams_component,
                    execution_type,
                    execution_scope,
                    start_time,
                    end_time,
                    status,
                    items_processed,
                    items_created,
                    items_updated,
                    items_skipped,
                    errors_count,
                    executor_container
                FROM mams_execution_log 
                WHERE start_time > NOW() - INTERVAL '{days} days'
                {where_clause}
                ORDER BY start_time DESC
            """, *params)
            
            return [dict(record) for record in records]
        finally:
            await conn.close()
    
    @staticmethod
    async def get_component_summary() -> Dict[str, Any]:
        """Get summary of all MAMS component executions"""
        conn = await asyncpg.connect("postgresql://admin:chooters@db:5432/arkyvus_db")
        try:
            records = await conn.fetch("""
                SELECT 
                    mams_component,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(items_created) as total_items_created,
                    SUM(items_processed) as total_items_processed,
                    MAX(start_time) as last_execution,
                    AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration_seconds
                FROM mams_execution_log 
                GROUP BY mams_component
                ORDER BY last_execution DESC
            """)
            
            summary = {}
            for record in records:
                summary[record['mams_component']] = dict(record)
            
            return summary
        finally:
            await conn.close()

async def main():
    """Test the MAMS logging system"""
    async with MAMSLogger('MAMS-999', 'test').execution_context('test', test_param='value') as logger:
        logger.info("Testing MAMS logging system")
        await logger.log_discovery_progress(100, 50, 20, 30)
        await logger.log_phase_completion('test_phase', {'result': 'success'})
        logger.warning("Test warning message")
    
    # Test audit logging
    history = await MAMSAuditLogger.get_execution_history('MAMS-999', 1)
    print(f"Execution History: {json.dumps(history, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())