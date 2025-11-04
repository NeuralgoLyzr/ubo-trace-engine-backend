"""
UBO Trace Engine Backend - UBO Trace Service
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from models.schemas import (
    UBOTraceRequest, UBOTraceResponse, TraceStageResult, TraceSummary,
    TraceStatus, TraceStage, BatchTraceRequest, BatchTraceResponse
)
from services.lyzr_service import LyzrAgentService
from services.apollo_service import ApolloService
from services.searchapi_service import SearchAPIService
from utils.database import get_database

logger = logging.getLogger(__name__)

class UBOTraceService:
    """Service for managing UBO trace operations"""
    
    def __init__(self):
        self.lyzr_service = LyzrAgentService()
        self.apollo_service = ApolloService()
        self.searchapi_service = SearchAPIService()
        self._db = None
    
    @property
    def db(self):
        """Get database connection lazily"""
        if self._db is None:
            self._db = get_database()
        return self._db
    
    async def create_trace(self, request: UBOTraceRequest) -> UBOTraceResponse:
        """Create a new UBO trace"""
        
        trace_response = UBOTraceResponse(
            entity=request.entity,
            ubo_name=request.ubo_name,
            location=request.location,
            domain_name=request.domain_name,
            status=TraceStatus.PENDING
        )
        
        # Save to database
        await self.db.ubo_traces.insert_one(trace_response.dict())
        
        logger.info(f"Created UBO trace: {trace_response.trace_id}")
        return trace_response
    
    async def execute_trace(self, trace_id: str) -> TraceSummary:
        """Execute the complete 4-stage UBO trace"""
        
        # Get trace from database
        trace = await self.db.ubo_traces.find_one({"trace_id": trace_id})
        if not trace:
            raise ValueError(f"Trace not found: {trace_id}")
        
        # Update status to in progress and clear previous results
        await self.db.ubo_traces.update_one(
            {"trace_id": trace_id},
            {
                "$set": {
                    "status": TraceStatus.IN_PROGRESS, 
                    "stages_completed": [],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Clear previous stage results for this trace
        await self.db.trace_results.delete_many({"trace_id": trace_id})
        
        start_time = datetime.utcnow()
        stage_results = []
        
        try:
            # Execute all 4 stages
            stages = [TraceStage.STAGE_1A, TraceStage.STAGE_1B, TraceStage.STAGE_2A, TraceStage.STAGE_2B]
            
            for stage in stages:
                logger.info(f"Executing stage {stage} for trace {trace_id}")
                
                stage_result = await self._execute_stage(
                    trace_id, stage, trace["entity"], trace["ubo_name"], 
                    trace["location"], trace.get("domain_name")
                )
                
                stage_results.append(stage_result)
                
                # Save stage result to database
                await self.db.trace_results.insert_one(stage_result.dict())
                
                # Update trace with completed stage
                await self.db.ubo_traces.update_one(
                    {"trace_id": trace_id},
                    {
                        "$push": {"stages_completed": stage},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
                
                # Add delay between stages to respect rate limits
                await asyncio.sleep(5)
            
            # Generate summary
            summary = await self._generate_summary(trace_id, stage_results, start_time)
            
            # Update trace status
            await self.db.ubo_traces.update_one(
                {"trace_id": trace_id},
                {
                    "$set": {
                        "status": TraceStatus.COMPLETED,
                        "results_summary": summary.dict(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Completed UBO trace: {trace_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to execute trace {trace_id}: {str(e)}")
            
            # Update trace status to failed
            await self.db.ubo_traces.update_one(
                {"trace_id": trace_id},
                {
                    "$set": {
                        "status": TraceStatus.FAILED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            raise
    
    def _has_zero_results(self, stage_result: TraceStageResult) -> bool:
        """Check if a stage result has zero findings"""
        if not stage_result.parsed_results:
            return True
        
        direct_count = len(stage_result.parsed_results.get("direct", []))
        indirect_count = len(stage_result.parsed_results.get("indirect", []))
        urls_count = len(stage_result.parsed_results.get("urls", []))
        
        # Consider it zero results if no direct connections, no indirect connections, and no URLs
        return direct_count == 0 and indirect_count == 0 and urls_count == 0

    async def _execute_stage(self, trace_id: str, stage: TraceStage, entity: str, 
                           ubo_name: Optional[str] = None, location: Optional[str] = None, domain: Optional[str] = None) -> TraceStageResult:
        """Execute a single stage of the UBO trace with retry logic for zero results"""
        
        start_time = datetime.utcnow()
        max_retries = 3
        retry_delay = 5  # seconds
        
        # Get agent configuration
        config = self.lyzr_service.agent_configs.get(stage)
        if not config:
            raise ValueError(f"Unknown stage: {stage}")
        
        for attempt in range(max_retries + 1):  # 0, 1, 2, 3 (total 4 attempts)
            is_retry = attempt > 0
            
            # Build request message with available parameters
            message_parts = [f"Entity: {entity}"]
            if ubo_name:
                message_parts.append(f"UBO: {ubo_name}")
            if location:
                message_parts.append(f"Location: {location}")
            if domain:
                message_parts.append(f"Domain: {domain}")
            request_message = ", ".join(message_parts) if message_parts else f"Entity: {entity}"
            
            stage_result = TraceStageResult(
                trace_id=trace_id,
                stage=stage,
                status=TraceStatus.IN_PROGRESS,
                agent_id=config["agent_id"],
                session_id=config["session_id"],
                request_message=request_message
            )
            
            try:
                if is_retry:
                    logger.info(f"Retry attempt {attempt} for stage {stage} (trace {trace_id})")
                
                # Call Lyzr agent
                response = await self.lyzr_service.call_agent(stage, entity, ubo_name, location, domain)
                
                if response.success:
                    stage_result.response_content = response.content
                    stage_result.processing_time_ms = response.processing_time_ms
                    
                    # Set structured facts and summary from Lyzr response
                    stage_result.facts = response.facts
                    stage_result.summary = response.summary
                    
                    # Add Apollo enrichment data
                    try:
                        logger.info(f"Starting Apollo enrichment for stage {stage}")
                        apollo_enrichment = await self.apollo_service.enrich_ubo_trace_data(
                            entity, ubo_name, location, domain
                        )
                        stage_result.apollo_enrichment = apollo_enrichment
                        
                        # Extract insights from Apollo data
                        apollo_insights = self.apollo_service.extract_key_insights(apollo_enrichment)
                        stage_result.apollo_insights = apollo_insights
                        
                        logger.info(f"Apollo enrichment completed for stage {stage}")
                        logger.info(f"Apollo insights: {apollo_insights.get('overall_confidence', 0)}% confidence")
                        
                    except Exception as apollo_error:
                        logger.warning(f"Apollo enrichment failed for stage {stage}: {str(apollo_error)}")
                        stage_result.apollo_enrichment = {"error": str(apollo_error)}
                        stage_result.apollo_insights = {"error": str(apollo_error)}
                    
                    # Add SearchAPI domain search
                    try:
                        logger.info(f"Starting SearchAPI domain search for stage {stage}")
                        
                        # Search for domains using available parameters
                        domain_search = await self.searchapi_service.search_domains(
                            entity, ubo_name, location
                        )
                        stage_result.searchapi_domain_search = domain_search
                        
                        # If domain is provided, search for ownership information
                        if domain:
                            domain_ownership = await self.searchapi_service.search_domain_ownership(
                                entity, ubo_name, location, domain
                            )
                            stage_result.searchapi_domain_ownership = domain_ownership
                        
                        # Search for related domains
                        related_domains = await self.searchapi_service.search_related_domains(
                            entity, ubo_name, location
                        )
                        stage_result.searchapi_related_domains = related_domains
                        
                        logger.info(f"SearchAPI domain search completed for stage {stage}")
                        logger.info(f"Found {domain_search.get('total_results', 0)} domains")
                        logger.info(f"Found {related_domains.get('total_results', 0)} related domains")
                        
                    except Exception as searchapi_error:
                        logger.warning(f"SearchAPI domain search failed for stage {stage}: {str(searchapi_error)}")
                        stage_result.searchapi_domain_search = {"error": str(searchapi_error)}
                        stage_result.searchapi_domain_ownership = {"error": str(searchapi_error)}
                        stage_result.searchapi_related_domains = {"error": str(searchapi_error)}
                    
                    # Add Expert domain analysis
                    try:
                        logger.info(f"Starting Expert domain analysis for stage {stage}")
                        
                        # Get Lyzr domain analysis results (requires address, so we'll skip if not available)
                        lyzr_domains = []
                        # Note: analyze_company_domains requires address parameter, so we skip it here
                        # as we don't have address in the trace context
                        
                        # Get Google SERP domains from SearchAPI
                        google_serp_domains = []
                        if stage_result.searchapi_domain_search and stage_result.searchapi_domain_search.get("success"):
                            google_serp_domains = stage_result.searchapi_domain_search.get("domains", [])
                        
                        # Call Expert agent for analysis
                        if lyzr_domains or google_serp_domains:
                            expert_analysis = await self.searchapi_service.analyze_domains_with_expert(
                                entity, ubo_name, location, lyzr_domains, google_serp_domains
                            )
                            stage_result.expert_domain_analysis = expert_analysis
                            
                            logger.info(f"Expert domain analysis completed for stage {stage}")
                            logger.info(f"Expert confidence: {expert_analysis.get('expert_analysis', {}).get('overall_confidence', 0)}%")
                        else:
                            logger.warning(f"No domain data available for Expert analysis in stage {stage}")
                            stage_result.expert_domain_analysis = {"error": "No domain data available"}
                        
                    except Exception as expert_error:
                        logger.warning(f"Expert domain analysis failed for stage {stage}: {str(expert_error)}")
                        stage_result.expert_domain_analysis = {"error": str(expert_error)}
                    
                    # Parse results for backward compatibility
                    parsed_results = self.lyzr_service.parse_results(response.content, ubo_name)
                    stage_result.parsed_results = parsed_results
                    stage_result.urls_found = parsed_results["urls"]
                    stage_result.direct_connections = parsed_results["direct"]
                    stage_result.indirect_connections = parsed_results["indirect"]
                    stage_result.has_direct = parsed_results["has_direct"]
                    stage_result.has_indirect = parsed_results["has_indirect"]
                    stage_result.status = TraceStatus.COMPLETED
                    
                    # Check if we have zero results and should retry
                    if self._has_zero_results(stage_result) and attempt < max_retries:
                        logger.warning(f"Stage {stage} returned zero results (attempt {attempt + 1}/{max_retries + 1}). Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        # Either we have results or we've exhausted retries
                        if self._has_zero_results(stage_result):
                            logger.warning(f"Stage {stage} still has zero results after {max_retries + 1} attempts")
                        else:
                            logger.info(f"Stage {stage} completed successfully with results")
                        break
                    
                else:
                    stage_result.error_message = response.error
                    stage_result.status = TraceStatus.FAILED
                    break
                
            except Exception as e:
                stage_result.error_message = str(e)
                stage_result.status = TraceStatus.FAILED
                logger.error(f"Stage {stage} failed for trace {trace_id} (attempt {attempt + 1}): {str(e)}")
                
                # If this is not the last attempt, wait before retrying
                if attempt < max_retries:
                    logger.info(f"Retrying stage {stage} in {retry_delay} seconds due to error...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    break
            
            stage_result.completed_at = datetime.utcnow()
        
        return stage_result
    
    async def _generate_summary(self, trace_id: str, stage_results: List[TraceStageResult], 
                              start_time: datetime) -> TraceSummary:
        """Generate a summary of the trace results"""
        
        # Get trace details
        trace = await self.db.ubo_traces.find_one({"trace_id": trace_id})
        
        # Aggregate resultsk
        all_direct = []
        all_indirect = []
        all_urls = []
        has_direct = False
        has_indirect = False
        
        for result in stage_results:
            if result.parsed_results:
                all_direct.extend(result.parsed_results.get("direct", []))
                all_indirect.extend(result.parsed_results.get("indirect", []))
                all_urls.extend(result.parsed_results.get("urls", []))
                
                if result.parsed_results.get("has_direct"):
                    has_direct = True
                if result.parsed_results.get("has_indirect"):
                    has_indirect = True
        
        # Remove duplicates
        all_direct = list(set(all_direct))
        all_indirect = list(set(all_indirect))
        all_urls = list(set(all_urls))
        
        # Determine connection status
        if has_direct:
            connection_status = "DIRECT CONNECTION"
        elif has_indirect:
            connection_status = "INDIRECT CONNECTION ONLY"
        else:
            connection_status = "NO CONNECTION"
        
        # Calculate processing time
        end_time = datetime.utcnow()
        total_processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        summary = TraceSummary(
            trace_id=trace_id,
            entity=trace["entity"],
            ubo_name=trace["ubo_name"],
            location=trace["location"],
            domain_name=trace.get("domain_name"),
            overall_status=TraceStatus.COMPLETED,
            stages_completed=len(stage_results),
            total_stages=4,
            has_direct_evidence=has_direct,
            has_indirect_evidence=has_indirect,
            total_urls=len(all_urls),
            total_direct_facts=len(all_direct),
            total_indirect_facts=len(all_indirect),
            connection_status=connection_status,
            stage_results=stage_results,
            created_at=start_time,
            completed_at=end_time,
            total_processing_time_ms=total_processing_time
        )
        
        return summary
    
    async def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get a trace by ID"""
        trace = await self.db.ubo_traces.find_one({"trace_id": trace_id})
        if trace and "_id" in trace:
            trace["_id"] = str(trace["_id"])
        return trace
    
    async def get_trace_summary(self, trace_id: str) -> Optional[TraceSummary]:
        """Get a complete trace summary"""
        trace = await self.get_trace(trace_id)
        if not trace:
            return None
        
        # Get stage results
        stage_results = await self.db.trace_results.find({"trace_id": trace_id}).to_list(None)
        # Convert ObjectId to string for serialization
        for result in stage_results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        stage_results = [TraceStageResult(**result) for result in stage_results]
        
        # Generate summary
        return await self._generate_summary(trace_id, stage_results, trace["created_at"])
    
    async def execute_batch_traces(self, request: BatchTraceRequest) -> BatchTraceResponse:
        """Execute multiple UBO traces in batch"""
        
        batch_response = BatchTraceResponse(
            total_traces=len(request.traces),
            completed_traces=0,
            failed_traces=0,
            trace_ids=[]
        )
        
        # Create all traces (batch only creates, does not execute)
        for trace_request in request.traces:
            try:
                trace_response = await self.create_trace(trace_request)
                batch_response.trace_ids.append(trace_response.trace_id)
                batch_response.completed_traces += 1
            except Exception as e:
                batch_response.failed_traces += 1
                logger.error(f"Failed to create trace: {str(e)}")
        
        # Update batch status based on creation results
        if batch_response.completed_traces == batch_response.total_traces:
            batch_response.status = TraceStatus.COMPLETED
        elif batch_response.completed_traces > 0:
            batch_response.status = TraceStatus.PARTIAL
        else:
            batch_response.status = TraceStatus.FAILED
        
        return batch_response
