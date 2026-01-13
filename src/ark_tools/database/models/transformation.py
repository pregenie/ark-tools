"""
Transformation Database Models  
==============================

Models for storing transformation plans, operations, and generation results.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ark_tools.database.base import Base

class TransformationPlan(Base):
    """
    Represents a transformation plan for code consolidation
    """
    __tablename__ = 'transformation_plans'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # Plan metadata
    analysis_id = Column(String(64), nullable=False, index=True)
    strategy = Column(String(32), nullable=False)  # conservative, moderate, aggressive
    status = Column(String(32), nullable=False, default='draft')  # draft, approved, executing, completed, failed
    
    # Timing information
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    started_execution_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Plan configuration
    strategy_config = Column(JSON, nullable=False)
    parameters = Column(JSON, nullable=True)
    
    # Impact estimation
    estimated_files_affected = Column(Integer, nullable=True)
    estimated_components_consolidated = Column(Integer, nullable=True)
    estimated_code_reduction_percent = Column(Float, nullable=True)
    risk_level = Column(String(32), nullable=True)  # low, medium, high
    complexity_score = Column(Integer, nullable=True)
    
    # Plan details
    description = Column(Text, nullable=True)
    consolidation_goals = Column(JSON, nullable=True)
    
    # Validation and safety
    validation_rules = Column(JSON, nullable=False)
    safety_checks = Column(JSON, nullable=True)
    rollback_plan = Column(JSON, nullable=False)
    
    # Execution tracking
    total_operations = Column(Integer, nullable=True)
    completed_operations = Column(Integer, nullable=False, default=0)
    failed_operations = Column(Integer, nullable=False, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    warnings = Column(JSON, nullable=True)
    
    # Relationships
    groups = relationship("TransformationGroup", back_populates="plan", cascade="all, delete-orphan")
    operations = relationship("TransformationOperation", back_populates="plan", cascade="all, delete-orphan")
    generation_results = relationship("GenerationResult", back_populates="plan", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("strategy IN ('conservative', 'moderate', 'aggressive')", name='valid_strategy'),
        CheckConstraint("status IN ('draft', 'approved', 'executing', 'completed', 'failed', 'cancelled')", 
                       name='valid_status'),
        CheckConstraint("risk_level IN ('low', 'medium', 'high') OR risk_level IS NULL", name='valid_risk_level'),
        CheckConstraint("estimated_code_reduction_percent >= 0 AND estimated_code_reduction_percent <= 100 OR estimated_code_reduction_percent IS NULL",
                       name='valid_reduction_percent'),
        CheckConstraint("completed_operations >= 0", name='non_negative_completed'),
        CheckConstraint("failed_operations >= 0", name='non_negative_failed'),
        Index('ix_plan_status_created', 'status', 'created_at'),
        Index('ix_plan_strategy', 'strategy'),
        Index('ix_plan_analysis', 'analysis_id'),
    )
    
    def __repr__(self) -> str:
        return f"<TransformationPlan(id='{self.plan_id}', strategy='{self.strategy}', status='{self.status}')>"

class TransformationGroup(Base):
    """
    Represents a group of related transformations within a plan
    """
    __tablename__ = 'transformation_groups'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(String(64), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('transformation_plans.id'), nullable=False)
    
    # Group metadata
    name = Column(String(128), nullable=False)
    group_type = Column(String(32), nullable=False)  # duplicate_consolidation, pattern_consolidation
    description = Column(Text, nullable=True)
    priority = Column(String(32), nullable=False)  # low, medium, high, critical
    
    # Components involved
    source_components = Column(JSON, nullable=False)  # List of source component IDs
    target_component = Column(String(128), nullable=True)  # Target consolidated component
    
    # Consolidation details
    consolidation_strategy = Column(String(64), nullable=False)
    estimated_effort = Column(String(32), nullable=True)  # trivial, low, medium, high
    estimated_reduction = Column(Float, nullable=True)  # Percentage reduction expected
    
    # Pattern-specific fields
    pattern_type = Column(String(64), nullable=True)
    frequency = Column(Integer, nullable=True)
    similarity_score = Column(Float, nullable=True)
    
    # Status tracking
    status = Column(String(32), nullable=False, default='pending')  # pending, in_progress, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    operations_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    
    # Metadata
    group_metadata = Column(JSON, nullable=True)
    
    # Relationships
    plan = relationship("TransformationPlan", back_populates="groups")
    operations = relationship("TransformationOperation", back_populates="group", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("group_type IN ('duplicate_consolidation', 'pattern_consolidation', 'custom')", 
                       name='valid_group_type'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name='valid_priority'),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')",
                       name='valid_status'),
        CheckConstraint("estimated_effort IN ('trivial', 'low', 'medium', 'high') OR estimated_effort IS NULL",
                       name='valid_effort'),
        CheckConstraint("similarity_score >= 0 AND similarity_score <= 1 OR similarity_score IS NULL",
                       name='valid_similarity'),
        Index('ix_group_plan_priority', 'plan_id', 'priority'),
        Index('ix_group_type_status', 'group_type', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<TransformationGroup(id='{self.group_id}', type='{self.group_type}', status='{self.status}')>"

class TransformationOperation(Base):
    """
    Represents a single transformation operation
    """
    __tablename__ = 'transformation_operations'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id = Column(String(64), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('transformation_plans.id'), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey('transformation_groups.id'), nullable=True)
    
    # Operation details
    operation_type = Column(String(32), nullable=False)  # merge_duplicates, extract_pattern, refactor
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    
    # Input/Output
    input_components = Column(JSON, nullable=False)  # List of input component paths/IDs
    output_file = Column(String(512), nullable=True)  # Generated output file path
    transformation_type = Column(String(32), nullable=False)  # libcst_merge, text_merge, etc.
    
    # Configuration
    operation_config = Column(JSON, nullable=True)
    safety_checks = Column(JSON, nullable=False)
    
    # Status and timing
    status = Column(String(32), nullable=False, default='pending')
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Results
    success = Column(Boolean, nullable=True)
    generated_file_path = Column(String(512), nullable=True)
    generated_file_size = Column(Integer, nullable=True)
    lines_generated = Column(Integer, nullable=True)
    
    # Validation results
    syntax_valid = Column(Boolean, nullable=True)
    imports_valid = Column(Boolean, nullable=True)
    tests_generated = Column(Boolean, nullable=False, default=False)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Preview/dry-run data
    preview_content = Column(Text, nullable=True)
    dry_run_result = Column(JSON, nullable=True)
    
    # Relationships
    plan = relationship("TransformationPlan", back_populates="operations")
    group = relationship("TransformationGroup", back_populates="operations")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("operation_type IN ('merge_duplicates', 'extract_pattern', 'refactor', 'custom')",
                       name='valid_operation_type'),
        CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'skipped')",
                       name='valid_status'),
        CheckConstraint("execution_time_ms >= 0 OR execution_time_ms IS NULL", name='positive_execution_time'),
        CheckConstraint("retry_count >= 0", name='non_negative_retries'),
        Index('ix_operation_plan_status', 'plan_id', 'status'),
        Index('ix_operation_group_type', 'group_id', 'operation_type'),
        Index('ix_operation_execution_time', 'started_at', 'completed_at'),
    )
    
    def __repr__(self) -> str:
        return f"<TransformationOperation(id='{self.operation_id}', type='{self.operation_type}', status='{self.status}')>"

class GenerationResult(Base):
    """
    Stores the results of code generation operations
    """
    __tablename__ = 'generation_results'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generation_id = Column(String(64), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('transformation_plans.id'), nullable=False)
    
    # Generation metadata
    dry_run = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    
    # Generation statistics
    files_generated = Column(Integer, nullable=False, default=0)
    total_lines_generated = Column(Integer, nullable=False, default=0)
    total_size_bytes = Column(Integer, nullable=False, default=0)
    operations_executed = Column(Integer, nullable=False, default=0)
    operations_successful = Column(Integer, nullable=False, default=0)
    operations_failed = Column(Integer, nullable=False, default=0)
    
    # Quality metrics
    syntax_validation_passed = Column(Boolean, nullable=True)
    import_validation_passed = Column(Boolean, nullable=True)
    test_coverage_percent = Column(Float, nullable=True)
    
    # Output information
    output_directory = Column(String(512), nullable=True)
    generated_files_list = Column(JSON, nullable=True)  # List of generated files with metadata
    
    # Code quality metrics
    estimated_code_reduction_percent = Column(Float, nullable=True)
    complexity_reduction = Column(Float, nullable=True)
    maintainability_improvement = Column(Float, nullable=True)
    
    # Validation results
    validation_results = Column(JSON, nullable=True)
    safety_check_results = Column(JSON, nullable=True)
    
    # Error tracking
    errors_encountered = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    
    # Success metrics
    overall_success = Column(Boolean, nullable=True)
    success_rate = Column(Float, nullable=True)  # Percentage of successful operations
    
    # Generation configuration
    generation_config = Column(JSON, nullable=True)
    strategy_used = Column(String(32), nullable=True)
    
    # Additional metadata
    generation_metadata = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)
    
    # Relationships
    plan = relationship("TransformationPlan", back_populates="generation_results")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("files_generated >= 0", name='non_negative_files'),
        CheckConstraint("total_lines_generated >= 0", name='non_negative_lines'),
        CheckConstraint("total_size_bytes >= 0", name='non_negative_size'),
        CheckConstraint("operations_executed >= 0", name='non_negative_operations'),
        CheckConstraint("operations_successful >= 0", name='non_negative_successful'),
        CheckConstraint("operations_failed >= 0", name='non_negative_failed'),
        CheckConstraint("operations_successful + operations_failed <= operations_executed", 
                       name='valid_operation_counts'),
        CheckConstraint("success_rate >= 0 AND success_rate <= 100 OR success_rate IS NULL",
                       name='valid_success_rate'),
        CheckConstraint("test_coverage_percent >= 0 AND test_coverage_percent <= 100 OR test_coverage_percent IS NULL",
                       name='valid_coverage'),
        Index('ix_generation_plan_success', 'plan_id', 'overall_success'),
        Index('ix_generation_dry_run', 'dry_run'),
        Index('ix_generation_completed', 'completed_at'),
    )
    
    def __repr__(self) -> str:
        return f"<GenerationResult(id='{self.generation_id}', files={self.files_generated}, success={self.overall_success})>"