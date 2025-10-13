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
from utils.database import get_database

logger = logging.getLogger(__name__)

class UBOTraceService:
    """Service for managing UBO trace operations"""
    
    def __init__(self):
        self.lyzr_service = LyzrAgentService()
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
        
        # Update status to in progress
        await self.db.ubo_traces.update_one(
            {"trace_id": trace_id},
            {"$set": {"status": TraceStatus.IN_PROGRESS, "updated_at": datetime.utcnow()}}
        )
        
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
    
    async def _execute_stage(self, trace_id: str, stage: TraceStage, entity: str, 
                           ubo_name: str, location: str, domain: Optional[str] = None) -> TraceStageResult:
        """Execute a single stage of the UBO trace"""
        
        start_time = datetime.utcnow()
        
        # Get agent configuration
        config = self.lyzr_service.agent_configs.get(stage)
        if not config:
            raise ValueError(f"Unknown stage: {stage}")
        
        stage_result = TraceStageResult(
            trace_id=trace_id,
            stage=stage,
            status=TraceStatus.IN_PROGRESS,
            agent_id=config["agent_id"],
            session_id=config["session_id"],
            request_message=self.lyzr_service._build_prompt(stage, entity, ubo_name, location, domain)
        )
        
        try:
            # Call Lyzr agent
            response = await self.lyzr_service.call_agent(stage, entity, ubo_name, location, domain)
            
            if response.success:
                stage_result.response_content = response.content
                stage_result.processing_time_ms = response.processing_time_ms
                
                # Parse results
                parsed_results = self.lyzr_service.parse_results(response.content, ubo_name)
                stage_result.parsed_results = parsed_results
                stage_result.urls_found = parsed_results["urls"]
                stage_result.direct_connections = parsed_results["direct"]
                stage_result.indirect_connections = parsed_results["indirect"]
                stage_result.has_direct = parsed_results["has_direct"]
                stage_result.has_indirect = parsed_results["has_indirect"]
                stage_result.status = TraceStatus.COMPLETED
                
            else:
                stage_result.error_message = response.error
                stage_result.status = TraceStatus.FAILED
            
            stage_result.completed_at = datetime.utcnow()
            
        except Exception as e:
            stage_result.error_message = str(e)
            stage_result.status = TraceStatus.FAILED
            stage_result.completed_at = datetime.utcnow()
            logger.error(f"Stage {stage} failed for trace {trace_id}: {str(e)}")
        
        return stage_result
    
    async def _generate_summary(self, trace_id: str, stage_results: List[TraceStageResult], 
                              start_time: datetime) -> TraceSummary:
        """Generate a summary of the trace results"""
        
        # Get trace details
        trace = await self.db.ubo_traces.find_one({"trace_id": trace_id})
        
        # Aggregate results
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
            trace_ids=[]
        )
        
        # Create all traces first
        for trace_request in request.traces:
            trace_response = await self.create_trace(trace_request)
            batch_response.trace_ids.append(trace_response.trace_id)
        
        # Execute traces with concurrency limit
        semaphore = asyncio.Semaphore(request.max_concurrent or 3)
        
        async def execute_single_trace(trace_id: str):
            async with semaphore:
                try:
                    await self.execute_trace(trace_id)
                    batch_response.completed_traces += 1
                except Exception as e:
                    batch_response.failed_traces += 1
                    logger.error(f"Batch trace {trace_id} failed: {str(e)}")
        
        # Execute all traces concurrently
        await asyncio.gather(*[execute_single_trace(trace_id) for trace_id in batch_response.trace_ids])
        
        # Update batch status
        if batch_response.completed_traces == batch_response.total_traces:
            batch_response.status = TraceStatus.COMPLETED
        elif batch_response.completed_traces > 0:
            batch_response.status = TraceStatus.PARTIAL
        else:
            batch_response.status = TraceStatus.FAILED
        
        return batch_response
