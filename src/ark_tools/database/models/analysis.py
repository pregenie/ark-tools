"""
Analysis Database Models
========================

Models for storing code analysis results, pattern detection,
and duplicate identification.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

from ark_tools.database.base import Base

class Analysis(Base):
    """
    Represents a code analysis session
    """
    __tablename__ = 'analyses'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(String(64), unique=True, nullable=False, index=True)
    
    # Analysis metadata
    directory_path = Column(String(512), nullable=False)
    analysis_type = Column(String(32), nullable=False)  # quick, comprehensive, deep
    status = Column(String(32), nullable=False, default='running')  # running, completed, failed
    
    # Timing information
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Float, nullable=True)
    
    # Analysis configuration
    strategy_config = Column(JSON, nullable=True)
    parameters = Column(JSON, nullable=True)
    
    # Summary statistics
    total_files = Column(Integer, nullable=True)
    total_components = Column(Integer, nullable=True) 
    patterns_found = Column(Integer, nullable=True)
    duplicates_found = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    warnings = Column(JSON, nullable=True)
    
    # Relationships
    results = relationship("AnalysisResult", back_populates="analysis", cascade="all, delete-orphan")
    patterns = relationship("PatternDetection", back_populates="analysis", cascade="all, delete-orphan") 
    duplicates = relationship("DuplicateDetection", back_populates="analysis", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("analysis_type IN ('quick', 'comprehensive', 'deep')", name='valid_analysis_type'),
        CheckConstraint("status IN ('running', 'completed', 'failed', 'cancelled')", name='valid_status'),
        CheckConstraint("execution_time_seconds >= 0", name='positive_execution_time'),
        Index('ix_analysis_status_started', 'status', 'started_at'),
        Index('ix_analysis_directory', 'directory_path'),
    )
    
    def __repr__(self) -> str:
        return f"<Analysis(id='{self.analysis_id}', type='{self.analysis_type}', status='{self.status}')>"

class AnalysisResult(Base):
    """
    Stores detailed analysis results and metrics
    """
    __tablename__ = 'analysis_results'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id'), nullable=False)
    
    # Result data
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(32), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    components_extracted = Column(Integer, nullable=False, default=0)
    
    # Analysis metrics
    complexity_score = Column(Float, nullable=True)
    maintainability_index = Column(Float, nullable=True)
    cyclomatic_complexity = Column(Integer, nullable=True)
    lines_of_code = Column(Integer, nullable=True)
    
    # Component details
    functions_count = Column(Integer, nullable=False, default=0)
    classes_count = Column(Integer, nullable=False, default=0)
    imports_count = Column(Integer, nullable=False, default=0)
    
    # Detailed results (JSON)
    components_detail = Column(JSON, nullable=True)
    dependencies = Column(JSON, nullable=True)
    metrics_detail = Column(JSON, nullable=True)
    
    # Processing metadata
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Error handling
    processing_errors = Column(JSON, nullable=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="results")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("file_size_bytes >= 0", name='positive_file_size'),
        CheckConstraint("components_extracted >= 0", name='non_negative_components'),
        CheckConstraint("lines_of_code >= 0", name='non_negative_lines'),
        Index('ix_result_analysis_file', 'analysis_id', 'file_path'),
        Index('ix_result_file_type', 'file_type'),
    )
    
    def __repr__(self) -> str:
        return f"<AnalysisResult(file='{self.file_path}', components={self.components_extracted})>"

class PatternDetection(Base):
    """
    Stores detected code patterns and their metadata
    """
    __tablename__ = 'pattern_detections'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id'), nullable=False)
    pattern_id = Column(String(64), nullable=False)
    
    # Pattern information
    pattern_name = Column(String(128), nullable=False)
    pattern_type = Column(String(64), nullable=False)  # function, class, api_endpoint, etc.
    frequency = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Pattern details
    description = Column(Text, nullable=True)
    components_involved = Column(JSON, nullable=False)  # List of component IDs
    example_code = Column(Text, nullable=True)
    
    # Classification
    complexity_level = Column(String(32), nullable=True)  # low, medium, high
    consolidation_potential = Column(String(32), nullable=True)  # low, medium, high
    estimated_effort = Column(String(32), nullable=True)  # low, medium, high
    
    # Metrics
    total_lines_involved = Column(Integer, nullable=True)
    average_similarity = Column(Float, nullable=True)
    
    # Detection metadata
    detected_by = Column(String(32), nullable=False)  # mams, fallback, etc.
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    detection_method = Column(String(64), nullable=True)
    
    # Additional data
    pattern_metadata = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="patterns")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("frequency > 0", name='positive_frequency'),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name='valid_confidence'),
        CheckConstraint("complexity_level IN ('low', 'medium', 'high') OR complexity_level IS NULL", 
                       name='valid_complexity_level'),
        CheckConstraint("consolidation_potential IN ('low', 'medium', 'high') OR consolidation_potential IS NULL",
                       name='valid_consolidation_potential'),
        Index('ix_pattern_analysis_type', 'analysis_id', 'pattern_type'),
        Index('ix_pattern_frequency', 'frequency'),
        Index('ix_pattern_confidence', 'confidence_score'),
    )
    
    def __repr__(self) -> str:
        return f"<PatternDetection(name='{self.pattern_name}', freq={self.frequency}, confidence={self.confidence_score:.2f})>"

class DuplicateDetection(Base):
    """
    Stores detected code duplicates and similarity information
    """
    __tablename__ = 'duplicate_detections'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id'), nullable=False)
    duplicate_id = Column(String(64), nullable=False)
    
    # Duplicate pair information
    original_component_id = Column(String(128), nullable=False)
    duplicate_component_id = Column(String(128), nullable=False)
    original_file_path = Column(String(512), nullable=False)
    duplicate_file_path = Column(String(512), nullable=False)
    
    # Similarity metrics
    similarity_score = Column(Float, nullable=False)
    structural_similarity = Column(Float, nullable=True)
    semantic_similarity = Column(Float, nullable=True)
    lexical_similarity = Column(Float, nullable=True)
    
    # Content comparison
    common_lines = Column(Integer, nullable=True)
    total_lines_original = Column(Integer, nullable=True)
    total_lines_duplicate = Column(Integer, nullable=True)
    
    # Classification
    duplicate_type = Column(String(32), nullable=False)  # exact, near, structural
    consolidation_strategy = Column(String(32), nullable=True)  # merge, extract, refactor
    priority = Column(String(32), nullable=True)  # low, medium, high, critical
    
    # Effort estimation
    estimated_effort = Column(String(32), nullable=True)  # trivial, low, medium, high
    risk_level = Column(String(32), nullable=True)  # low, medium, high
    
    # Detection details
    detected_by = Column(String(32), nullable=False)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    detection_method = Column(String(64), nullable=True)
    
    # Analysis data
    differences = Column(JSON, nullable=True)  # Detailed differences
    consolidation_suggestions = Column(JSON, nullable=True)
    
    # Validation status
    manually_reviewed = Column(Boolean, nullable=False, default=False)
    review_notes = Column(Text, nullable=True)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="duplicates")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("similarity_score >= 0 AND similarity_score <= 1", name='valid_similarity'),
        CheckConstraint("original_component_id != duplicate_component_id", name='different_components'),
        CheckConstraint("duplicate_type IN ('exact', 'near', 'structural')", name='valid_duplicate_type'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'critical') OR priority IS NULL",
                       name='valid_priority'),
        CheckConstraint("risk_level IN ('low', 'medium', 'high') OR risk_level IS NULL",
                       name='valid_risk_level'),
        Index('ix_duplicate_analysis_similarity', 'analysis_id', 'similarity_score'),
        Index('ix_duplicate_components', 'original_component_id', 'duplicate_component_id'),
        Index('ix_duplicate_priority', 'priority'),
    )
    
    def __repr__(self) -> str:
        return f"<DuplicateDetection(similarity={self.similarity_score:.2f}, type='{self.duplicate_type}', priority='{self.priority}')>"