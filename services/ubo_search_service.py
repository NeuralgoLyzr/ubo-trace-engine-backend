"""
UBO Trace Engine Backend - UBO Search Service
Service for searching Ultimate Beneficial Owners using Lyzr agents
"""

import httpx
import time
import re
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from utils.settings import settings
from models.schemas import (
    UBOSearchRequest, UBOSearchResponse, DomainInfo, Executive, 
    UBOCandidate, CrossVerifyCandidate, RegistryPage, HierarchyLayer,
    LyzrAgentRequest, StepResult
)

logger = logging.getLogger(__name__)

class UBOSearchService:
    """Service for UBO search using Lyzr AI agents"""
    
    def __init__(self):
        self.api_url = settings.lyzr_api_url
        self.api_key = settings.lyzr_api_key
        self.user_id = settings.lyzr_user_id
        self.timeout = settings.api_timeout
    
    async def call_lyzr_agent(self, agent_id: str, session_id: str, message: str) -> Dict[str, Any]:
        """Call a Lyzr agent with the given parameters"""
        start_time = time.time()
        
        try:
            request_data = LyzrAgentRequest(
                user_id=self.user_id,
                agent_id=agent_id,
                session_id=session_id,
                message=message
            )
            
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=request_data.dict()
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract content from response
                content = result.get("response", "")
                if not content:
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    content = result.get("content", "")
                
                processing_time = int((time.time() - start_time) * 1000)
                
                return {
                    "success": True,
                    "content": content,
                    "processing_time_ms": processing_time
                }
                
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Lyzr agent call failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": processing_time
            }
    
    def parse_json_block(self, text: str) -> Dict[str, Any]:
        """Parse JSON from text response"""
        try:
            # Try to find JSON block in response
            json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', text)
            if json_match:
                block = json_match.group(0)
                return json.loads(block)
            # If no JSON block found, try parsing entire text
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Could not parse JSON from response: {str(e)}")
            return {"raw_text": text[:800]}
    
    def _is_empty_result(self, data: Any) -> bool:
        """Check if parsed result data is empty"""
        if data is None:
            return True
        if isinstance(data, dict):
            # Check if it only has raw_text or is essentially empty
            if "raw_text" in data and len(data) == 1:
                return True
            # Check if it's an empty dict or has no meaningful fields
            if not data or (len(data) == 0):
                return True
            # For domain info, check if domain is missing/empty
            if "domain" in data and not data.get("domain"):
                return True
        if isinstance(data, list):
            return len(data) == 0
        return False
    
    async def search_domain(self, company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Search for company domain with retry logic"""
        message = f"company_name: {company_name}"
        if location:
            message += f", location: {location}"
        
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries + 1):
            is_retry = attempt > 0
            
            if is_retry:
                logger.info(f"Retry attempt {attempt} for domain search (company: {company_name})")
            
            result = await self.call_lyzr_agent(
                settings.agent_ubo_domain,
                settings.session_ubo_domain,
                message
            )
            
            if result.get("success"):
                parsed = self.parse_json_block(result["content"])
                
                # Check if result is empty
                if not self._is_empty_result(parsed):
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
                elif attempt < max_retries:
                    logger.warning(f"Domain search returned empty results (attempt {attempt + 1}/{max_retries + 1}). Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Last attempt returned empty, return it anyway
                    logger.warning(f"Domain search returned empty results after {max_retries + 1} attempts")
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
            
            # If call failed and not last attempt, retry
            if attempt < max_retries:
                logger.warning(f"Domain search failed (attempt {attempt + 1}/{max_retries + 1}). Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                continue
        
        return result
    
    async def search_csuite(self, company_name: str, domain: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """Search for C-suite executives with retry logic"""
        message = f"company_name: {company_name}"
        if domain:
            message += f", domain: {domain}"
        if location:
            message += f", location: {location}"
        
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} for C-suite search (company: {company_name})")
            
            result = await self.call_lyzr_agent(
                settings.agent_ubo_csuite,
                settings.session_ubo_csuite,
                message
            )
            
            if result.get("success"):
                parsed = self.parse_json_block(result["content"])
                
                if not self._is_empty_result(parsed):
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
                elif attempt < max_retries:
                    logger.warning(f"C-suite search returned empty results (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.warning(f"C-suite search returned empty results after {max_retries + 1} attempts")
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
            
            if attempt < max_retries:
                logger.warning(f"C-suite search failed (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                await asyncio.sleep(retry_delay)
                continue
        
        return result
    
    async def search_ubos(self, company_name: str, domain: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """Search for Ultimate Beneficial Owners with retry logic"""
        message = f"company_name: {company_name}"
        if domain:
            message += f", domain: {domain}"
        if location:
            message += f", location: {location}"
        
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} for UBOs search (company: {company_name})")
            
            result = await self.call_lyzr_agent(
                settings.agent_ubo_ubos,
                settings.session_ubo_ubos,
                message
            )
            
            if result.get("success"):
                parsed = self.parse_json_block(result["content"])
                
                if not self._is_empty_result(parsed):
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
                elif attempt < max_retries:
                    logger.warning(f"UBOs search returned empty results (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.warning(f"UBOs search returned empty results after {max_retries + 1} attempts")
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
            
            if attempt < max_retries:
                logger.warning(f"UBOs search failed (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                await asyncio.sleep(retry_delay)
                continue
        
        return result
    
    async def cross_verify_ubos(self, company_name: str, domain: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """Cross-verify UBO candidates with retry logic"""
        message = f"company_name: {company_name}"
        if domain:
            message += f", domain: {domain}"
        if location:
            message += f", location: {location}"
        
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} for cross-verify (company: {company_name})")
            
            result = await self.call_lyzr_agent(
                settings.agent_ubo_crossverify,
                settings.session_ubo_crossverify,
                message
            )
            
            if result.get("success"):
                parsed = self.parse_json_block(result["content"])
                
                if not self._is_empty_result(parsed):
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
                elif attempt < max_retries:
                    logger.warning(f"Cross-verify returned empty results (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.warning(f"Cross-verify returned empty results after {max_retries + 1} attempts")
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
            
            if attempt < max_retries:
                logger.warning(f"Cross-verify failed (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                await asyncio.sleep(retry_delay)
                continue
        
        return result
    
    async def search_registries(self, company_name: str, domain: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """Search for registry/verification pages with retry logic"""
        message = f"company_name: {company_name}"
        if domain:
            message += f", domain: {domain}"
        if location:
            message += f", location: {location}"
        
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} for registries search (company: {company_name})")
            
            result = await self.call_lyzr_agent(
                settings.agent_ubo_registries,
                settings.session_ubo_registries,
                message
            )
            
            if result.get("success"):
                parsed = self.parse_json_block(result["content"])
                
                if not self._is_empty_result(parsed):
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
                elif attempt < max_retries:
                    logger.warning(f"Registries search returned empty results (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.warning(f"Registries search returned empty results after {max_retries + 1} attempts")
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
            
            if attempt < max_retries:
                logger.warning(f"Registries search failed (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                await asyncio.sleep(retry_delay)
                continue
        
        return result
    
    async def search_hierarchy(self, company_name: str, domain: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """Search for ownership hierarchy with retry logic"""
        message = f"company_name: {company_name}"
        if domain:
            message += f", domain: {domain}"
        if location:
            message += f", location: {location}"
        
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} for hierarchy search (company: {company_name})")
            
            result = await self.call_lyzr_agent(
                settings.agent_ubo_hierarchy,
                settings.session_ubo_hierarchy,
                message
            )
            
            if result.get("success"):
                parsed = self.parse_json_block(result["content"])
                
                if not self._is_empty_result(parsed):
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
                elif attempt < max_retries:
                    logger.warning(f"Hierarchy search returned empty results (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.warning(f"Hierarchy search returned empty results after {max_retries + 1} attempts")
                    return {"success": True, "data": parsed, "raw_content": result["content"]}
            
            if attempt < max_retries:
                logger.warning(f"Hierarchy search failed (attempt {attempt + 1}/{max_retries + 1}). Retrying...")
                await asyncio.sleep(retry_delay)
                continue
        
        return result
    
    def parse_domain_info(self, data: Dict[str, Any]) -> Optional[DomainInfo]:
        """Parse domain information from response"""
        try:
            if isinstance(data, dict):
                return DomainInfo(
                    entity=data.get("entity", ""),
                    domain=data.get("domain"),
                    evidence=data.get("evidence")
                )
        except Exception as e:
            logger.warning(f"Could not parse domain info: {str(e)}")
        return None
    
    def parse_executives(self, data: Any) -> List[Executive]:
        """Parse executives list from response"""
        executives = []
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        executives.append(Executive(
                            name=item.get("name", ""),
                            role=item.get("role"),
                            nationality=item.get("nationality"),
                            source_url=item.get("source_url")
                        ))
        except Exception as e:
            logger.warning(f"Could not parse executives: {str(e)}")
        return executives
    
    def parse_ubos(self, data: Any) -> List[UBOCandidate]:
        """Parse UBO candidates from response"""
        ubos = []
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        ubos.append(UBOCandidate(
                            name=item.get("name", ""),
                            relation=item.get("relation"),
                            ubo_type=item.get("ubo_type"),
                            rationale=item.get("rationale"),
                            source_url=item.get("source_url")
                        ))
        except Exception as e:
            logger.warning(f"Could not parse UBOs: {str(e)}")
        return ubos
    
    def parse_cross_verify(self, data: Any) -> List[CrossVerifyCandidate]:
        """Parse cross-verified candidates from response"""
        candidates = []
        try:
            # Handle different data structures
            if isinstance(data, dict):
                # If data is a dict with a "candidates" key
                if "candidates" in data and isinstance(data["candidates"], list):
                    data = data["candidates"]
                # If data is a dict with other keys, try to extract candidates
                elif "candidate" in data or "evidence" in data:
                    # Single candidate as dict
                    data = [data]
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        candidate_name = item.get("candidate", "")
                        # Only add if candidate name is not empty
                        if candidate_name and candidate_name.strip():
                            candidates.append(CrossVerifyCandidate(
                                candidate=candidate_name.strip(),
                                evidence=item.get("evidence"),
                                source_url=item.get("source_url"),
                                confidence=item.get("confidence")
                            ))
        except Exception as e:
            logger.warning(f"Could not parse cross-verify candidates: {str(e)}")
            logger.debug(f"Data structure: {type(data)} - {data}")
        return candidates
    
    def parse_registries(self, data: Any) -> List[RegistryPage]:
        """Parse registry pages from response"""
        registries = []
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        registries.append(RegistryPage(
                            country=item.get("country"),
                            registry_name=item.get("registry_name"),
                            registry_url=item.get("registry_url"),
                            next_steps=item.get("next_steps")
                        ))
        except Exception as e:
            logger.warning(f"Could not parse registries: {str(e)}")
        return registries
    
    def parse_hierarchy(self, data: Any) -> List[HierarchyLayer]:
        """Parse ownership hierarchy from response"""
        layers = []
        try:
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        layers.append(HierarchyLayer(
                            layer=item.get("layer", ""),
                            name=item.get("name", ""),
                            jurisdiction=item.get("jurisdiction"),
                            nationality=item.get("nationality"),
                            source_url=item.get("source_url")
                        ))
        except Exception as e:
            logger.warning(f"Could not parse hierarchy: {str(e)}")
        return layers
    
    async def search_ubo(self, request: UBOSearchRequest) -> UBOSearchResponse:
        """Main method to perform UBO search"""
        start_time = time.time()
        step_results = []
        step_number = 1
        
        try:
            company_name = request.company_name
            location = request.location
            domain = request.domain
            include_full = request.include_full_analysis
            
            logger.info(f"Starting UBO search for: {company_name}")
            
            # Step 1: Domain Search
            step_start = time.time()
            domain_result = await self.search_domain(company_name, location)
            step_time = int((time.time() - step_start) * 1000)
            
            domain_info = None
            step_results.append(StepResult(
                step_name="Domain Search",
                step_number=step_number,
                status="completed" if domain_result.get("success") else "failed",
                data=domain_result.get("data"),
                raw_content=domain_result.get("raw_content"),
                error=domain_result.get("error"),
                processing_time_ms=step_time
            ))
            step_number += 1
            
            if domain_result.get("success") and domain_result.get("data"):
                domain_info = self.parse_domain_info(domain_result["data"])
                # If domain not provided, use the found domain
                if not domain and domain_info and domain_info.domain:
                    domain = domain_info.domain
            
            # Step 2: C-Suite (if full analysis)
            c_suite = []
            if include_full:
                step_start = time.time()
                csuite_result = await self.search_csuite(company_name, domain, location)
                step_time = int((time.time() - step_start) * 1000)
                
                step_results.append(StepResult(
                    step_name="C-Suite Search",
                    step_number=step_number,
                    status="completed" if csuite_result.get("success") else "failed",
                    data=csuite_result.get("data"),
                    raw_content=csuite_result.get("raw_content"),
                    error=csuite_result.get("error"),
                    processing_time_ms=step_time
                ))
                step_number += 1
                
                if csuite_result.get("success") and csuite_result.get("data"):
                    c_suite = self.parse_executives(csuite_result["data"])
            
            # Step 3: UBOs Search
            step_start = time.time()
            ubo_result = await self.search_ubos(company_name, domain, location)
            step_time = int((time.time() - step_start) * 1000)
            
            possible_ubos = []
            step_results.append(StepResult(
                step_name="UBOs Search",
                step_number=step_number,
                status="completed" if ubo_result.get("success") else "failed",
                data=ubo_result.get("data"),
                raw_content=ubo_result.get("raw_content"),
                error=ubo_result.get("error"),
                processing_time_ms=step_time
            ))
            step_number += 1
            
            if ubo_result.get("success") and ubo_result.get("data"):
                possible_ubos = self.parse_ubos(ubo_result["data"])
            
            # Step 4: Cross-Verification
            step_start = time.time()
            cross_result = await self.cross_verify_ubos(company_name, domain, location)
            step_time = int((time.time() - step_start) * 1000)
            
            cross_candidates = []
            step_results.append(StepResult(
                step_name="Cross-Verification",
                step_number=step_number,
                status="completed" if cross_result.get("success") else "failed",
                data=cross_result.get("data"),
                raw_content=cross_result.get("raw_content"),
                error=cross_result.get("error"),
                processing_time_ms=step_time
            ))
            step_number += 1
            
            if cross_result.get("success") and cross_result.get("data"):
                cross_candidates = self.parse_cross_verify(cross_result["data"])
                logger.info(f"Parsed {len(cross_candidates)} cross-verification candidates")
                if cross_candidates:
                    logger.debug(f"Cross-verification candidates: {[c.candidate for c in cross_candidates]}")
            
            # Extract summary from cross-verification results
            probable_ubos = []
            confidence_levels = []
            cross_verification_summary = []
            
            for candidate in cross_candidates:
                # Collect candidate names for probable_ubos
                if candidate.candidate:
                    probable_ubos.append(candidate.candidate)
                
                # Collect confidence levels
                if candidate.confidence:
                    confidence_levels.append(candidate.confidence)
                
                # Build cross-verification summary for display
                candidate_info = {}
                if candidate.candidate:
                    candidate_info["candidate"] = candidate.candidate
                if candidate.confidence:
                    candidate_info["confidence"] = candidate.confidence
                if candidate.evidence:
                    candidate_info["evidence"] = candidate.evidence
                if candidate.source_url:
                    candidate_info["source_url"] = candidate.source_url
                
                if candidate_info:
                    cross_verification_summary.append(candidate_info)
            
            # Use cross-verification results even if no candidate names found
            # Format as a summary string for display
            if probable_ubos:
                ubo_names = " / ".join(probable_ubos)
            elif cross_candidates:
                # If we have cross-verification data but no candidate names, create a summary from evidence
                summary_parts = []
                for i, candidate in enumerate(cross_candidates, 1):
                    part = f"Candidate {i}"
                    if candidate.evidence:
                        # Use first part of evidence as summary
                        evidence_summary = candidate.evidence[:50] + "..." if len(candidate.evidence) > 50 else candidate.evidence
                        part += f": {evidence_summary}"
                    if candidate.confidence:
                        part += f" ({candidate.confidence} confidence)"
                    summary_parts.append(part)
                ubo_names = " / ".join(summary_parts) if summary_parts else "Cross-verification completed"
            else:
                ubo_names = None
            
            # Determine confidence level (safely handle unknown values)
            confidence = None
            if confidence_levels:
                try:
                    # Filter to only valid confidence levels
                    valid_levels = [c for c in confidence_levels if c in ["Low", "Medium", "High"]]
                    if valid_levels:
                        confidence_order = ["Low", "Medium", "High"]
                        confidence = max(valid_levels, key=lambda x: confidence_order.index(x))
                except (ValueError, IndexError):
                    # If all are invalid, just use the first one
                    confidence = confidence_levels[0] if confidence_levels else None
            
            # Optional full analysis steps
            verification_pages = []
            ownership_chain = []
            
            if include_full:
                # Step 5: Registries
                step_start = time.time()
                reg_result = await self.search_registries(company_name, domain, location)
                step_time = int((time.time() - step_start) * 1000)
                
                step_results.append(StepResult(
                    step_name="Registries Search",
                    step_number=step_number,
                    status="completed" if reg_result.get("success") else "failed",
                    data=reg_result.get("data"),
                    raw_content=reg_result.get("raw_content"),
                    error=reg_result.get("error"),
                    processing_time_ms=step_time
                ))
                step_number += 1
                
                if reg_result.get("success") and reg_result.get("data"):
                    verification_pages = self.parse_registries(reg_result["data"])
                
                # Step 6: Hierarchy
                step_start = time.time()
                hier_result = await self.search_hierarchy(company_name, domain, location)
                step_time = int((time.time() - step_start) * 1000)
                
                step_results.append(StepResult(
                    step_name="Ownership Hierarchy",
                    step_number=step_number,
                    status="completed" if hier_result.get("success") else "failed",
                    data=hier_result.get("data"),
                    raw_content=hier_result.get("raw_content"),
                    error=hier_result.get("error"),
                    processing_time_ms=step_time
                ))
                
                if hier_result.get("success") and hier_result.get("data"):
                    ownership_chain = self.parse_hierarchy(hier_result["data"])
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Build summary - use cross-verification results if available
            if ubo_names:
                ubo_found_display = ubo_names
            elif cross_candidates:
                # Show cross-verification summary when no UBO names found
                ubo_found_display = f"Cross-verification results available ({len(cross_candidates)} candidates)"
            else:
                ubo_found_display = "Not found"
            
            # Build summary (without cross-verification section)
            summary = {
                "Entity": company_name,
                "Intended / Probable UBO Found": ubo_found_display,
                "Confidence": confidence or "Low"
            }
            
            return UBOSearchResponse(
                success=True,
                entity=company_name,
                domain_info=domain_info,
                c_suite=c_suite,
                possible_ubos=possible_ubos,
                cross_candidates=cross_candidates,
                verification_pages=verification_pages,
                ownership_chain=ownership_chain,
                step_results=step_results,
                summary=summary,
                probable_ubos=ubo_names,
                confidence=confidence,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"UBO search failed: {str(e)}")
            return UBOSearchResponse(
                success=False,
                entity=request.company_name,
                step_results=step_results,
                error=str(e),
                processing_time_ms=processing_time
            )

