"""
UBO Trace Engine Backend - API Endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import logging

from models.schemas import (
    UBOTraceRequest, UBOTraceResponse, TraceSummary, TraceStageResult,
    BatchTraceRequest, BatchTraceResponse, HealthCheck,
    CompanyDomainAnalysisRequest, CompanyDomainAnalysisResponse,
    UBOSearchRequest, UBOSearchResponse, ApolloPeopleSearchRequest,
    CandidateUBOAnalysisRequest, CandidateUBOAnalysisResponse,
    UBOVerificationRequest, UBOVerificationResponse
)
from services.ubo_trace_service import UBOTraceService
from utils.database import get_database, is_database_available

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service
ubo_service = UBOTraceService()

@router.post("/trace", response_model=UBOTraceResponse)
async def create_ubo_trace(request: UBOTraceRequest):
    """Create a new UBO trace"""
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. MongoDB connection is not available."
        )
    try:
        trace = await ubo_service.create_trace(request)
        logger.info(f"Created UBO trace: {trace.trace_id}")
        return trace
    except HTTPException:
        raise
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
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. MongoDB connection is not available."
        )
    try:
        db = get_database()
        stages = await db.trace_results.find({"trace_id": trace_id}).to_list(None)
        # Convert ObjectId to string for serialization
        for stage in stages:
            if "_id" in stage:
                stage["_id"] = str(stage["_id"])
        return [TraceStageResult(**stage) for stage in stages]
    except HTTPException:
        raise
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
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. MongoDB connection is not available."
        )
    
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
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Check for MongoDB connection errors
        if "timed out" in error_msg.lower() or "mongodb" in error_msg.lower() or "database" in error_msg.lower():
            logger.error(f"Database connection error: {error_msg}")
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable. MongoDB connection is not available."
            )
        logger.error(f"Failed to list traces: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/traces/stats", response_model=Dict[str, Any])
async def get_trace_statistics():
    """Get UBO trace statistics"""
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. MongoDB connection is not available."
        )
    
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
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Check for MongoDB connection errors
        if "timed out" in error_msg.lower() or "mongodb" in error_msg.lower() or "database" in error_msg.lower():
            logger.error(f"Database connection error: {error_msg}")
            raise HTTPException(
                status_code=503,
                detail="Database service unavailable. MongoDB connection is not available."
            )
        logger.error(f"Failed to get trace statistics: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.delete("/trace/{trace_id}")
async def delete_trace(trace_id: str):
    """Delete a UBO trace and all its results"""
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. MongoDB connection is not available."
        )
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

@router.post("/domain-analysis")
async def analyze_domains_with_expert(
    company_name: str,
    ubo_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Analyze domains using Expert AI agent and return confidence scores and rankings"""
    try:
        from services.searchapi_service import SearchAPIService
        
        searchapi_service = SearchAPIService()
        
        logger.info(f"Starting domain analysis for: {company_name} - {ubo_name} - {location}")
        
        # Call the domain analysis method
        result = await searchapi_service.analyze_domains_for_api(
            company_name, ubo_name, location
        )
        
        if result.get("success"):
            logger.info(f"Domain analysis completed: {len(result.get('results', []))} domains analyzed")
            return result
        else:
            logger.error(f"Domain analysis failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Domain analysis failed"))
        
    except Exception as e:
        logger.error(f"Failed to analyze domains: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-ubo-ownership")
async def search_ubo_ownership(
    company_name: str,
    location: Optional[str] = None
):
    """Search for UBO ownership information using Google Search API and analyze with Lyzr agent"""
    try:
        from services.searchapi_service import SearchAPIService
        
        searchapi_service = SearchAPIService()
        
        logger.info(f"Starting UBO ownership search for: {company_name} - {location}")
        
        # Call the UBO ownership search method
        result = await searchapi_service.search_ubo_ownership(
            company_name, location
        )
        
        if result.get("success"):
            logger.info(f"UBO ownership search completed: {result.get('total_organic_results', 0)} organic results, {result.get('total_related_questions', 0)} related questions")
            return result
        else:
            error_code = result.get("error_code")
            error_message = result.get("error", "UBO ownership search failed")
            
            # Handle rate limiting with 429 status
            if error_code == "RATE_LIMIT_EXCEEDED":
                logger.warning(f"UBO ownership search rate limited: {error_message}")
                raise HTTPException(status_code=429, detail=error_message)
            
            logger.error(f"UBO ownership search failed: {error_message}")
            raise HTTPException(status_code=500, detail=error_message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search UBO ownership: {str(e)}")
        
        # Check if it's a rate limit error
        error_str = str(e)
        if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
            raise HTTPException(status_code=429, detail="SearchAPI rate limit exceeded. Please try again later.")
        
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apollo-people-search")
async def apollo_people_search_by_organization(request: ApolloPeopleSearchRequest):
    """Search for people by organization using Apollo API with advanced filters"""
    try:
        from services.apollo_service import ApolloService
        
        apollo_service = ApolloService()
        
        logger.info(f"Starting Apollo people search for organization: {request.organization_name}")
        
        # Call the Apollo people search method
        result = await apollo_service.search_people_by_organization(
            organization_name=request.organization_name,
            person_titles=request.person_titles,
            domains=request.domains,
            locations=request.locations
        )
        
        if result.get("success"):
            logger.info(f"Apollo people search completed: {result.get('total_results', 0)} people found")
            return result
        else:
            error_message = result.get("error", "Apollo people search failed")
            logger.error(f"Apollo people search failed: {error_message}")
            
            # Check if it's a connection/SSL/timeout error - return 503 (Service Unavailable)
            error_lower = error_message.lower()
            if any(keyword in error_lower for keyword in ["connection", "ssl", "timeout", "unable to connect", "interrupted", "disconnected"]):
                raise HTTPException(status_code=503, detail=error_message)
            # For other errors, return 500
            else:
                raise HTTPException(status_code=500, detail=error_message)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Apollo service not configured: {str(e)}")
        raise HTTPException(status_code=503, detail="Apollo API key not configured")
    except Exception as e:
        error_str = str(e)
        logger.error(f"Failed to search Apollo people: {error_str}")
        
        # Check if it's a connection/SSL/timeout error
        error_lower = error_str.lower()
        if any(keyword in error_lower for keyword in ["connection", "ssl", "timeout", "unable to connect", "interrupted", "disconnected"]):
            raise HTTPException(status_code=503, detail="Apollo API connection error. Please try again later.")
        else:
            raise HTTPException(status_code=500, detail=error_str)

@router.post("/search-ubo", response_model=UBOSearchResponse)
async def search_ubo(request: UBOSearchRequest):
    """Search for Ultimate Beneficial Owners using Lyzr agents"""
    try:
        from services.ubo_search_service import UBOSearchService
        ubo_search_service = UBOSearchService()
        
        result = await ubo_search_service.search_ubo(request)
        
        logger.info(f"UBO search completed for {request.company_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to search UBO: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-domain-standalone")
async def search_domain_standalone(
    company_name: str = Query(...),
    location: Optional[str] = Query(None)
):
    """Standalone domain search endpoint"""
    try:
        from services.ubo_search_service import UBOSearchService
        ubo_search_service = UBOSearchService()
        
        result = await ubo_search_service.search_domain(company_name, location)
        
        logger.info(f"Domain search completed for {company_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to search domain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-csuite-standalone")
async def search_csuite_standalone(
    company_name: str = Query(...),
    domain: Optional[str] = Query(None),
    location: Optional[str] = Query(None)
):
    """Standalone C-suite search endpoint"""
    try:
        from services.ubo_search_service import UBOSearchService
        ubo_search_service = UBOSearchService()
        
        result = await ubo_search_service.search_csuite(company_name, domain, location)
        
        logger.info(f"C-suite search completed for {company_name}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to search C-suite: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-candidate-ubo", response_model=CandidateUBOAnalysisResponse)
async def analyze_candidate_ubo(request: CandidateUBOAnalysisRequest):
    """Analyze a candidate to find Ultimate Beneficial Owners with retry mechanism"""
    import json
    import asyncio
    import time
    from services.lyzr_service import LyzrAgentService
    from utils.settings import settings
    
    # Retry configuration
    max_retries = 2  # Reduced from 3 to 2 (3 total attempts instead of 4)
    retry_delay = 3  # Reduced from 5 to 3 seconds
    start_time = time.time()
    
    try:
        # Initialize Lyzr service
        lyzr_service = LyzrAgentService()
        
        # Get agent configuration from settings
        agent_id = settings.agent_candidate_ubo_analysis
        session_id = settings.session_candidate_ubo_analysis
        
        if not agent_id or not session_id:
            raise HTTPException(
                status_code=500,
                detail="Candidate UBO analysis agent not configured. Please set AGENT_CANDIDATE_UBO_ANALYSIS and SESSION_CANDIDATE_UBO_ANALYSIS in .env"
            )
        
        # Format message as JSON string as shown in the example
        message = f'{{"candidate": "{request.candidate}"}}'
        
        logger.info(f"Analyzing candidate UBO for: {request.candidate}")
        
        # Retry loop
        last_error = None
        for attempt in range(max_retries + 1):  # 0, 1, 2, 3 (total 4 attempts)
            is_retry = attempt > 0
            
            try:
                if is_retry:
                    logger.info(f"Retry attempt {attempt} for candidate UBO analysis (candidate: {request.candidate})")
                    await asyncio.sleep(retry_delay)
                
                # Call the Lyzr agent with longer timeout for candidate analysis
                # Use 120 seconds timeout to allow for complex analysis
                response = await lyzr_service.call_custom_agent(
                    agent_id=agent_id,
                    session_id=session_id,
                    message=message,
                    timeout=120  # 2 minutes per attempt
                )
                
                if not response.success:
                    error_msg = response.error or "Unknown error from Lyzr agent"
                    logger.warning(f"Lyzr agent call failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg}")
                    last_error = error_msg
                    
                    # Retry if not the last attempt
                    if attempt < max_retries:
                        continue
                    else:
                        processing_time = int((time.time() - start_time) * 1000)
                        return CandidateUBOAnalysisResponse(
                            success=False,
                            error=error_msg,
                            processing_time_ms=processing_time
                        )
                
                if not response.content:
                    logger.warning(f"Empty response content from Lyzr agent (attempt {attempt + 1}/{max_retries + 1})")
                    last_error = "Empty response from Lyzr agent"
                    
                    # Retry if not the last attempt
                    if attempt < max_retries:
                        continue
                    else:
                        processing_time = int((time.time() - start_time) * 1000)
                        return CandidateUBOAnalysisResponse(
                            success=False,
                            error="Empty response from Lyzr agent",
                            processing_time_ms=processing_time
                        )
                
                # Parse the response content
                ubos = []
                unresolved_candidates = []
                
                try:
                    # Try to parse JSON response
                    # First, try to extract JSON from markdown code blocks if present
                    content = response.content.strip()
                    if content.startswith("```"):
                        # Extract JSON from markdown code block
                        lines = content.split("\n")
                        json_start = None
                        json_end = None
                        for i, line in enumerate(lines):
                            if line.strip().startswith("```") and json_start is None:
                                json_start = i + 1
                            elif line.strip().startswith("```") and json_start is not None:
                                json_end = i
                                break
                        if json_start is not None and json_end is not None:
                            content = "\n".join(lines[json_start:json_end])
                    
                    parsed_content = json.loads(content)
                    
                    # Extract UBOs
                    if isinstance(parsed_content, dict):
                        ubos_data = parsed_content.get("ubos", [])
                        for ubo_data in ubos_data:
                            if isinstance(ubo_data, dict):
                                from models.schemas import UBOAnalysisResult, ResolutionChainItem
                                
                                # Parse resolution chain
                                resolution_chain = []
                                chain_data = ubo_data.get("resolution_chain", [])
                                for chain_item in chain_data:
                                    if isinstance(chain_item, dict):
                                        resolution_chain.append(ResolutionChainItem(
                                            entity_name=chain_item.get("entity_name", ""),
                                            entity_type=chain_item.get("entity_type", ""),
                                            relation=chain_item.get("relation", ""),
                                            level=chain_item.get("level", 0)
                                        ))
                                
                                # Create UBO analysis result
                                ubo_result = UBOAnalysisResult(
                                    ubo_name=ubo_data.get("ubo_name", ""),
                                    ubo_type=ubo_data.get("ubo_type", ""),
                                    control_mechanism=ubo_data.get("control_mechanism", ""),
                                    resolution_chain=resolution_chain,
                                    rationale=ubo_data.get("rationale", ""),
                                    source_url=ubo_data.get("source_url", []),
                                    confidence=ubo_data.get("confidence", "Medium")
                                )
                                ubos.append(ubo_result)
                        
                        # Extract unresolved candidates
                        unresolved_candidates = parsed_content.get("unresolved_candidates", [])
                        
                        # Successfully parsed the response
                        processing_time = int((time.time() - start_time) * 1000)
                        logger.info(f"Candidate UBO analysis completed (attempt {attempt + 1}): found {len(ubos)} UBOs, {len(unresolved_candidates)} unresolved candidates")
                        
                        return CandidateUBOAnalysisResponse(
                            success=True,
                            ubos=ubos,
                            unresolved_candidates=unresolved_candidates,
                            processing_time_ms=processing_time
                        )
                    else:
                        logger.warning(f"Parsed content is not a dict: {type(parsed_content)}")
                        last_error = f"Unexpected response format: {type(parsed_content)}"
                        
                        # Retry if not the last attempt
                        if attempt < max_retries:
                            continue
                        else:
                            processing_time = int((time.time() - start_time) * 1000)
                            return CandidateUBOAnalysisResponse(
                                success=False,
                                error=f"Unexpected response format: {type(parsed_content)}",
                                processing_time_ms=processing_time
                            )
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                    logger.warning(f"Raw content (first 500 chars): {response.content[:500]}")
                    last_error = f"Failed to parse JSON response: {str(e)}"
                    
                    # Retry if not the last attempt
                    if attempt < max_retries:
                        continue
                    else:
                        processing_time = int((time.time() - start_time) * 1000)
                        return CandidateUBOAnalysisResponse(
                            success=False,
                            error=f"Failed to parse JSON response after {max_retries + 1} attempts: {str(e)}. Response may not be in expected format.",
                            processing_time_ms=processing_time
                        )
                except (KeyError, TypeError) as e:
                    logger.warning(f"Failed to extract data from response (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                    last_error = f"Failed to extract data from response: {str(e)}"
                    
                    # Retry if not the last attempt
                    if attempt < max_retries:
                        continue
                    else:
                        processing_time = int((time.time() - start_time) * 1000)
                        return CandidateUBOAnalysisResponse(
                            success=False,
                            error=f"Failed to extract data from response after {max_retries + 1} attempts: {str(e)}",
                            processing_time_ms=processing_time
                        )
                    
            except Exception as e:
                logger.error(f"Candidate UBO analysis failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                last_error = str(e)
                
                # Retry if not the last attempt
                if attempt < max_retries:
                    logger.info(f"Retrying candidate UBO analysis in {retry_delay} seconds due to error...")
                    continue
                else:
                    # Final attempt failed
                    processing_time = int((time.time() - start_time) * 1000)
                    return CandidateUBOAnalysisResponse(
                        success=False,
                        error=f"Failed after {max_retries + 1} attempts: {str(e)}",
                        processing_time_ms=processing_time
                    )
        
        # This should never be reached, but just in case
        processing_time = int((time.time() - start_time) * 1000)
        return CandidateUBOAnalysisResponse(
            success=False,
            error=last_error or "Unexpected error in retry loop",
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze candidate UBO: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-ubo", response_model=UBOVerificationResponse)
async def verify_ubo(request: UBOVerificationRequest):
    """Verify UBO details including shareholding, age, nationality, evidence, and source URL"""
    import json
    import asyncio
    import time
    from services.lyzr_service import LyzrAgentService
    from utils.settings import settings
    from models.schemas import UBOType
    
    # Retry configuration
    max_retries = 2
    retry_delay = 3
    start_time = time.time()
    
    try:
        # Initialize Lyzr service
        lyzr_service = LyzrAgentService()
        
        # Get agent configuration from settings
        agent_id = settings.agent_ubo_verification
        session_id = settings.session_ubo_verification
        
        if not agent_id or not session_id:
            raise HTTPException(
                status_code=500,
                detail="UBO verification agent not configured. Please set AGENT_UBO_VERIFICATION and SESSION_UBO_VERIFICATION in .env"
            )
        
        # Format message as JSON string with all parameters
        message_parts = {
            "ubo_name": request.ubo_name,
            "company_name": request.company_name
        }
        if request.location:
            message_parts["location"] = request.location
        if request.context:
            message_parts["context"] = request.context
        
        message = json.dumps(message_parts)
        
        logger.info(f"Verifying UBO: {request.ubo_name} for company: {request.company_name}")
        
        # Retry loop
        last_error = None
        for attempt in range(max_retries + 1):
            is_retry = attempt > 0
            
            try:
                if is_retry:
                    logger.info(f"Retry attempt {attempt} for UBO verification (UBO: {request.ubo_name}, Company: {request.company_name})")
                    await asyncio.sleep(retry_delay)
                
                # Call the Lyzr agent with longer timeout for verification
                response = await lyzr_service.call_custom_agent(
                    agent_id=agent_id,
                    session_id=session_id,
                    message=message,
                    timeout=120  # 2 minutes per attempt
                )
                
                if not response.success:
                    error_msg = response.error or "Unknown error from Lyzr agent"
                    logger.warning(f"Lyzr agent call failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg}")
                    last_error = error_msg
                    
                    # Retry if not the last attempt
                    if attempt < max_retries:
                        continue
                    else:
                        processing_time = int((time.time() - start_time) * 1000)
                        return UBOVerificationResponse(
                            success=False,
                            error=error_msg,
                            processing_time_ms=processing_time
                        )
                
                if not response.content:
                    logger.warning(f"Empty response content from Lyzr agent (attempt {attempt + 1}/{max_retries + 1})")
                    last_error = "Empty response from Lyzr agent"
                    
                    # Retry if not the last attempt
                    if attempt < max_retries:
                        continue
                    else:
                        processing_time = int((time.time() - start_time) * 1000)
                        return UBOVerificationResponse(
                            success=False,
                            error="Empty response from Lyzr agent",
                            processing_time_ms=processing_time
                        )
                
                # Parse the response content
                try:
                    # Try to parse JSON response
                    # First, try to extract JSON from markdown code blocks if present
                    content = response.content.strip()
                    if content.startswith("```"):
                        # Extract JSON from markdown code block
                        lines = content.split("\n")
                        json_start = None
                        json_end = None
                        for i, line in enumerate(lines):
                            if line.strip().startswith("```") and json_start is None:
                                json_start = i + 1
                            elif line.strip().startswith("```") and json_start is not None:
                                json_end = i
                                break
                        if json_start is not None and json_end is not None:
                            content = "\n".join(lines[json_start:json_end])
                    
                    parsed_content = json.loads(content)
                    
                    # Extract verification data
                    if isinstance(parsed_content, dict):
                        # Handle new response format with results array
                        results_data = parsed_content.get("results", [])
                        if not results_data and isinstance(parsed_content.get("results"), list):
                            results_data = parsed_content["results"]
                        
                        # If results is not an array, try to extract from root level
                        if not isinstance(results_data, list):
                            # Check if the data itself is a result object
                            if isinstance(parsed_content, dict) and any(key in parsed_content for key in ["holding", "ubo_type", "evidence"]):
                                results_data = [parsed_content]
                            else:
                                results_data = []
                        
                        from models.schemas import UBOVerificationResult
                        verification_results = []
                        
                        for result_item in results_data:
                            if isinstance(result_item, dict):
                                # Parse ubo_type enum if present
                                ubo_type_value = result_item.get("ubo_type")
                                ubo_type = None
                                if ubo_type_value:
                                    try:
                                        if isinstance(ubo_type_value, str):
                                            ubo_type = UBOType(ubo_type_value)
                                        else:
                                            ubo_type = ubo_type_value
                                    except (ValueError, TypeError):
                                        logger.warning(f"Invalid ubo_type value: {ubo_type_value}, expected 'Control' or 'Ownership'")
                                
                                verification_results.append(UBOVerificationResult(
                                    holding=result_item.get("Holding") or result_item.get("holding"),
                                    ubo_type=ubo_type,
                                    evidence=result_item.get("evidence"),
                                    source_url=result_item.get("source_url"),
                                    confidence=result_item.get("confidence"),
                                    age=result_item.get("age"),
                                    nationality=result_item.get("nationality")
                                ))
                        
                        # Successfully parsed the response
                        processing_time = int((time.time() - start_time) * 1000)
                        logger.info(f"UBO verification completed (attempt {attempt + 1}): {request.ubo_name} for {request.company_name}, found {len(verification_results)} results")
                        
                        return UBOVerificationResponse(
                            success=True,
                            results=verification_results,
                            processing_time_ms=processing_time
                        )
                    else:
                        logger.warning(f"Parsed content is not a dict: {type(parsed_content)}")
                        last_error = f"Unexpected response format: {type(parsed_content)}"
                        
                        # Retry if not the last attempt
                        if attempt < max_retries:
                            continue
                        else:
                            processing_time = int((time.time() - start_time) * 1000)
                            return UBOVerificationResponse(
                                success=False,
                                error=f"Unexpected response format: {type(parsed_content)}",
                                processing_time_ms=processing_time
                            )
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                    logger.warning(f"Raw content (first 500 chars): {response.content[:500]}")
                    last_error = f"Failed to parse JSON response: {str(e)}"
                    
                    # Retry if not the last attempt
                    if attempt < max_retries:
                        continue
                    else:
                        processing_time = int((time.time() - start_time) * 1000)
                        return UBOVerificationResponse(
                            success=False,
                            error=f"Failed to parse JSON response after {max_retries + 1} attempts: {str(e)}. Response may not be in expected format.",
                            processing_time_ms=processing_time
                        )
                except (KeyError, TypeError) as e:
                    logger.warning(f"Failed to extract data from response (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                    last_error = f"Failed to extract data from response: {str(e)}"
                    
                    # Retry if not the last attempt
                    if attempt < max_retries:
                        continue
                    else:
                        processing_time = int((time.time() - start_time) * 1000)
                        return UBOVerificationResponse(
                            success=False,
                            error=f"Failed to extract data from response after {max_retries + 1} attempts: {str(e)}",
                            processing_time_ms=processing_time
                        )
                    
            except Exception as e:
                logger.error(f"UBO verification failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                last_error = str(e)
                
                # Retry if not the last attempt
                if attempt < max_retries:
                    logger.info(f"Retrying UBO verification in {retry_delay} seconds due to error...")
                    continue
                else:
                    # Final attempt failed
                    processing_time = int((time.time() - start_time) * 1000)
                    return UBOVerificationResponse(
                        success=False,
                        error=f"Failed after {max_retries + 1} attempts: {str(e)}",
                        processing_time_ms=processing_time
                    )
        
        # This should never be reached, but just in case
        processing_time = int((time.time() - start_time) * 1000)
        return UBOVerificationResponse(
            success=False,
            error=last_error or "Unexpected error in retry loop",
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify UBO: {str(e)}")
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
