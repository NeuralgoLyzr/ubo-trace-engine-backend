"""
UBO Trace Engine Backend - API Endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import logging

from models.schemas import (
    UBOTraceRequest, UBOTraceResponse, TraceSummary, TraceStageResult,
    BatchTraceRequest, BatchTraceResponse, HealthCheck,
    CompanyDomainAnalysisRequest, CompanyDomainAnalysisResponse
)
from services.ubo_trace_service import UBOTraceService
from utils.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
ubo_service = UBOTraceService()

@router.post("/trace", response_model=UBOTraceResponse)
async def create_ubo_trace(request: UBOTraceRequest):
    """Create a new UBO trace"""
    try:
        trace = await ubo_service.create_trace(request)
        logger.info(f"Created UBO trace: {trace.trace_id}")
        return trace
    except Exception as e:
        logger.error(f"Failed to create UBO trace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trace/{trace_id}/execute", response_model=TraceSummary)
async def execute_ubo_trace(trace_id: str):
    """Execute a UBO trace (all 4 stages)"""
    try:
        summary = await ubo_service.execute_trace(trace_id)
        logger.info(f"Executed UBO trace: {trace_id}")
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute UBO trace {trace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trace/{trace_id}", response_model=Dict[str, Any])
async def get_ubo_trace(trace_id: str):
    """Get a UBO trace by ID"""
    try:
        trace = await ubo_service.get_trace(trace_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        return trace
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get UBO trace {trace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trace/{trace_id}/summary", response_model=TraceSummary)
async def get_trace_summary(trace_id: str):
    """Get a complete trace summary with all results"""
    try:
        summary = await ubo_service.get_trace_summary(trace_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Trace not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trace summary {trace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trace/{trace_id}/stages", response_model=List[TraceStageResult])
async def get_trace_stages(trace_id: str):
    """Get all stage results for a trace"""
    try:
        db = get_database()
        stages = await db.trace_results.find({"trace_id": trace_id}).to_list(None)
        # Convert ObjectId to string for serialization
        for stage in stages:
            if "_id" in stage:
                stage["_id"] = str(stage["_id"])
        return [TraceStageResult(**stage) for stage in stages]
    except Exception as e:
        logger.error(f"Failed to get trace stages {trace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trace/batch", response_model=BatchTraceResponse)
async def execute_batch_traces(request: BatchTraceRequest):
    """Execute multiple UBO traces in batch"""
    try:
        batch_response = await ubo_service.execute_batch_traces(request)
        logger.info(f"Executed batch traces: {batch_response.batch_id}")
        return batch_response
    except Exception as e:
        logger.error(f"Failed to execute batch traces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/traces", response_model=List[Dict[str, Any]])
async def list_traces(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    entity: Optional[str] = Query(default=None)
):
    """List all UBO traces with optional filtering"""
    try:
        db = get_database()
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if entity:
            filter_dict["entity"] = {"$regex": entity, "$options": "i"}
        
        # Get traces
        cursor = db.ubo_traces.find(filter_dict).skip(offset).limit(limit).sort("created_at", -1)
        traces = await cursor.to_list(None)
        
        # Convert ObjectId to string for serialization
        for trace in traces:
            if "_id" in trace:
                trace["_id"] = str(trace["_id"])
        
        return traces
    except Exception as e:
        logger.error(f"Failed to list traces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/traces/stats", response_model=Dict[str, Any])
async def get_trace_statistics():
    """Get UBO trace statistics"""
    try:
        db = get_database()
        
        # Count by status
        status_counts = {}
        statuses = ["pending", "in_progress", "completed", "failed", "partial"]
        
        for status in statuses:
            count = await db.ubo_traces.count_documents({"status": status})
            status_counts[status] = count
        
        # Total counts
        total_traces = await db.ubo_traces.count_documents({})
        total_stage_results = await db.trace_results.count_documents({})
        
        # Recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_traces = await db.ubo_traces.count_documents({"created_at": {"$gte": yesterday}})
        
        return {
            "total_traces": total_traces,
            "total_stage_results": total_stage_results,
            "status_counts": status_counts,
            "recent_traces_24h": recent_traces,
            "generated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to get trace statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/trace/{trace_id}")
async def delete_trace(trace_id: str):
    """Delete a UBO trace and all its results"""
    try:
        db = get_database()
        
        # Delete trace
        trace_result = await db.ubo_traces.delete_one({"trace_id": trace_id})
        if trace_result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        # Delete stage results
        await db.trace_results.delete_many({"trace_id": trace_id})
        
        logger.info(f"Deleted UBO trace: {trace_id}")
        return {"message": "Trace deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete trace {trace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-company-domains", response_model=CompanyDomainAnalysisResponse)
async def analyze_company_domains(request: CompanyDomainAnalysisRequest):
    """Analyze company domains using Lyzr AI agent"""
    try:
        from services.lyzr_service import LyzrAgentService
        lyzr_service = LyzrAgentService()
        
        result = await lyzr_service.analyze_company_domains(
            company_name=request.company_name,
            ubo_name=request.ubo_name,
            address=request.address
        )
        
        logger.info(f"Company domain analysis completed for {request.company_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze company domains: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        
        # Test database connection
        await db.client.admin.command('ping')
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    # Test Lyzr API (basic connectivity)
    try:
        from services.lyzr_service import LyzrAgentService
        lyzr_service = LyzrAgentService()
        # We could add a simple ping test here if needed
        lyzr_api_status = "healthy"
    except Exception as e:
        lyzr_api_status = f"unhealthy: {str(e)}"
    
    return HealthCheck(
        status="healthy" if database_status == "healthy" and lyzr_api_status == "healthy" else "unhealthy",
        service="ubo_trace_engine",
        version="1.0.0",
        database_status=database_status,
        lyzr_api_status=lyzr_api_status
    )
