"""
Base Agent Class for ARK-TOOLS Specialized Agents
=================================================

Provides the foundation for all specialized agents in the ARK-TOOLS
agentic workflow system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime
import logging

from ark_tools.utils.debug_logger import debug_log

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentResult:
    """Standardized agent result structure"""
    agent_name: str
    operation: str
    status: AgentStatus
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    operation_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.operation_id:
            self.operation_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class BaseAgent(ABC):
    """
    Base class for all ARK-TOOLS specialized agents
    
    Provides common functionality for:
    - Operation tracking and logging
    - Result standardization  
    - Error handling and recovery
    - Inter-agent communication
    """
    
    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base agent
        
        Args:
            agent_name: Unique name for this agent
            config: Optional configuration parameters
        """
        self.agent_name = agent_name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.current_operation: Optional[str] = None
        self.operation_history: List[AgentResult] = []
        
        debug_log.agent(f"Initialized agent: {agent_name}")
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides
        
        Returns:
            List of capability names
        """
        pass
    
    @abstractmethod  
    def execute_operation(self, operation: str, parameters: Dict[str, Any]) -> AgentResult:
        """
        Execute a specific operation
        
        Args:
            operation: Name of operation to execute
            parameters: Operation parameters
            
        Returns:
            AgentResult with execution results
        """
        pass
    
    def can_handle_operation(self, operation: str) -> bool:
        """
        Check if this agent can handle the given operation
        
        Args:
            operation: Operation name to check
            
        Returns:
            True if agent can handle the operation
        """
        return operation in self.get_capabilities()
    
    def _start_operation(self, operation: str) -> str:
        """
        Start an operation and update agent status
        
        Args:
            operation: Name of operation starting
            
        Returns:
            Operation ID for tracking
        """
        operation_id = str(uuid.uuid4())
        self.status = AgentStatus.RUNNING
        self.current_operation = operation
        
        debug_log.agent(
            f"Starting operation: {operation}",
            extra={'agent': self.agent_name, 'operation_id': operation_id}
        )
        
        return operation_id
    
    def _complete_operation(
        self, 
        operation: str, 
        operation_id: str,
        success: bool,
        data: Dict[str, Any],
        error: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> AgentResult:
        """
        Complete an operation and update agent status
        
        Args:
            operation: Name of completed operation
            operation_id: ID of the operation
            success: Whether operation succeeded
            data: Operation result data
            error: Error message if operation failed
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            AgentResult with complete operation results
        """
        self.status = AgentStatus.COMPLETED if success else AgentStatus.FAILED
        self.current_operation = None
        
        result = AgentResult(
            agent_name=self.agent_name,
            operation=operation,
            status=self.status,
            success=success,
            data=data,
            error=error,
            execution_time_ms=execution_time_ms,
            operation_id=operation_id
        )
        
        # Add to operation history
        self.operation_history.append(result)
        
        debug_log.agent(
            f"Completed operation: {operation} ({'SUCCESS' if success else 'FAILED'})",
            extra={
                'agent': self.agent_name,
                'operation_id': operation_id,
                'success': success,
                'execution_time_ms': execution_time_ms
            }
        )
        
        return result
    
    def _handle_operation_error(
        self,
        operation: str,
        operation_id: str, 
        exception: Exception,
        execution_time_ms: Optional[int] = None
    ) -> AgentResult:
        """
        Handle operation error and create error result
        
        Args:
            operation: Name of failed operation
            operation_id: ID of the operation
            exception: Exception that occurred
            execution_time_ms: Execution time before failure
            
        Returns:
            AgentResult with error information
        """
        error_id = debug_log.error_trace(
            f"Operation failed in {self.agent_name}: {operation}",
            exception=exception,
            extra={'agent': self.agent_name, 'operation_id': operation_id}
        )
        
        return self._complete_operation(
            operation=operation,
            operation_id=operation_id,
            success=False,
            data={'error_id': error_id},
            error=str(exception),
            execution_time_ms=execution_time_ms
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'agent_name': self.agent_name,
            'status': self.status.value,
            'current_operation': self.current_operation,
            'capabilities': self.get_capabilities(),
            'operations_completed': len([r for r in self.operation_history if r.success]),
            'operations_failed': len([r for r in self.operation_history if not r.success]),
            'last_operation': self.operation_history[-1].operation if self.operation_history else None
        }
    
    def get_operation_history(self, limit: Optional[int] = None) -> List[AgentResult]:
        """
        Get operation history
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of AgentResult objects
        """
        history = self.operation_history
        if limit:
            history = history[-limit:]
        return history
    
    def reset_agent(self) -> None:
        """Reset agent to initial state"""
        self.status = AgentStatus.IDLE
        self.current_operation = None
        self.operation_history.clear()
        
        debug_log.agent(f"Reset agent: {self.agent_name}")