"""
UBO Trace Engine Backend - Data Models
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid
from bson import ObjectId

# Simple ObjectId handling without custom class
def objectid_validator(v):
    """Simple ObjectId validator"""
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str):
        if ObjectId.is_valid(v):
            return v
    raise ValueError("Invalid ObjectId")

class TraceStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class TraceStage(str, Enum):
    STAGE_1A = "stage_1a"  # Direct Evidence (General)
    STAGE_1B = "stage_1b"  # Direct Evidence (Time-filtered)
    STAGE_2A = "stage_2a"  # Indirect Evidence (General)
    STAGE_2B = "stage_2b"  # Indirect Evidence (Time-filtered)

class UBOTraceRequest(BaseModel):
    """Request model for UBO trace"""
    entity: str = Field(..., description="Entity name to trace")
    ubo_name: str = Field(..., description="Ultimate Beneficial Owner name")
    location: str = Field(..., description="Location/jurisdiction")
    domain_name: Optional[str] = Field(None, description="Optional domain name for context")

class UBOTraceResponse(BaseModel):
    """Response model for UBO trace"""
    id: Optional[str] = Field(default=None, alias="_id")
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity: str
    ubo_name: str
    location: str
    domain_name: Optional[str] = None
    status: TraceStatus = TraceStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    stages_completed: List[TraceStage] = Field(default_factory=list)
    total_stages: int = 4
    results_summary: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class FactItem(BaseModel):
    """Individual fact with URL"""
    fact: str
    url: str

class TraceStageResult(BaseModel):
    """Result model for individual trace stage"""
    id: Optional[str] = Field(default=None, alias="_id")
    trace_id: str
    stage: TraceStage
    status: TraceStatus
    agent_id: str
    session_id: str
    request_message: str
    response_content: Optional[str] = None
    parsed_results: Optional[Dict[str, Any]] = None
    facts: List[FactItem] = Field(default_factory=list)  # Structured facts from Lyzr response
    summary: Optional[str] = None  # Summary from Lyzr response
    apollo_enrichment: Optional[Dict[str, Any]] = None  # Apollo.io enrichment data
    apollo_insights: Optional[Dict[str, Any]] = None  # Apollo.io insights and verification
    searchapi_domain_search: Optional[Dict[str, Any]] = None  # SearchAPI domain search results
    searchapi_domain_ownership: Optional[Dict[str, Any]] = None  # SearchAPI domain ownership results
    searchapi_related_domains: Optional[Dict[str, Any]] = None  # SearchAPI related domains results
    expert_domain_analysis: Optional[Dict[str, Any]] = None  # Expert AI domain analysis with confidence scores
    urls_found: List[str] = Field(default_factory=list)
    direct_connections: List[str] = Field(default_factory=list)
    indirect_connections: List[str] = Field(default_factory=list)
    has_direct: bool = False
    has_indirect: bool = False
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TraceSummary(BaseModel):
    """Summary model for complete trace results"""
    trace_id: str
    entity: str
    ubo_name: str
    location: str
    domain_name: Optional[str] = None
    overall_status: TraceStatus
    stages_completed: int
    total_stages: int
    has_direct_evidence: bool
    has_indirect_evidence: bool
    total_urls: int
    total_direct_facts: int
    total_indirect_facts: int
    connection_status: str  # "DIRECT CONNECTION", "INDIRECT CONNECTION ONLY", "NO CONNECTION"
    stage_results: List[TraceStageResult]
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_processing_time_ms: Optional[int] = None

class LyzrAgentRequest(BaseModel):
    """Request model for Lyzr AI agent"""
    user_id: str
    agent_id: str
    session_id: str
    message: str

class PerplexityResponse(BaseModel):
    """Response model from Perplexity AI API"""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None

class LyzrAgentResponse(BaseModel):
    """Response model from Lyzr AI agent"""
    success: bool
    content: Optional[str] = None
    facts: List[FactItem] = Field(default_factory=list)  # Structured facts from JSON response
    summary: Optional[str] = None  # Summary from JSON response
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None

class BatchTraceRequest(BaseModel):
    """Request model for batch UBO traces"""
    traces: List[UBOTraceRequest]
    max_concurrent: Optional[int] = Field(default=3, description="Maximum concurrent traces")

class BatchTraceResponse(BaseModel):
    """Response model for batch UBO traces"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_traces: int
    completed_traces: int
    failed_traces: int
    trace_ids: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: TraceStatus = TraceStatus.PENDING

class CompanyDomainAnalysisRequest(BaseModel):
    """Request model for company domain analysis"""
    company_name: str = Field(..., description="Company name to analyze")
    ubo_name: str = Field(..., description="Ultimate Beneficial Owner name")
    address: str = Field(..., description="Company address")

class CompanyDomain(BaseModel):
    """Individual company domain result"""
    rank: int = Field(..., description="Ranking of the domain")
    domain: str = Field(..., description="Domain name")
    short_summary: str = Field(..., description="Short summary of the domain")
    relation: str = Field(..., description="Relation to the company")

class CompanyDomainAnalysisResponse(BaseModel):
    """Response model for company domain analysis"""
    success: bool
    companies: List[CompanyDomain] = Field(default_factory=list)
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database_status: str
    lyzr_api_status: str
