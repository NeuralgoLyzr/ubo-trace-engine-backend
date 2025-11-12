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
try:
    import json_repair
except ImportError:
    json_repair = None

from utils.settings import settings
from models.schemas import (
    UBOSearchRequest, UBOSearchResponse, DomainInfo, Executive, 
    UBOCandidate, CrossVerifyCandidate, RegistryPage, HierarchyLayer,
    LyzrAgentRequest, StepResult, TraceChainItem
)

logger = logging.getLogger(__name__)

class UBOSearchService:
    """Service for UBO search using Lyzr AI agents"""
    
    def __init__(self):
        self.api_url = settings.lyzr_api_url
        self.api_key = settings.lyzr_api_key
        self.user_id = settings.lyzr_user_id
        self.timeout = settings.api_timeout
    
    async def call_lyzr_agent(self, agent_id: str, session_id: str, message: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Call a Lyzr agent with the given parameters
        
        Args:
            agent_id: The agent ID to call
            session_id: The session ID to use
            message: The message to send
            timeout: Optional timeout in seconds (defaults to self.timeout)
        """
        start_time = time.time()
        
        # Use provided timeout or default
        request_timeout = timeout or self.timeout
        
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
            
            async with httpx.AsyncClient(timeout=request_timeout) as client:
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
    
    async def cross_verify_ubos(self, company_name: str, domain: Optional[str] = None, location: Optional[str] = None, tracing_company_name: Optional[str] = None) -> Dict[str, Any]:
        """Cross-verify UBO candidates with retry logic
        
        Args:
            company_name: The company/entity name to search for
            domain: Company domain (optional)
            location: Company location (optional)
            tracing_company_name: Original company name being traced (optional, for recursive searches)
        """
        message = f"company_name: {company_name}"
        if domain:
            message += f", domain: {domain}"
        if location:
            message += f", location: {location}"
        if tracing_company_name:
            message += f", tracing_company_name: {tracing_company_name}"
            logger.info(f"Cross-verification call includes tracing_company_name: {tracing_company_name}")
        
        max_retries = 3
        retry_delay = 5
        
        # Use longer timeout for cross-verification (180 seconds)
        cross_verify_timeout = 180
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} for cross-verify (company: {company_name})")
            
            result = await self.call_lyzr_agent(
                settings.agent_ubo_crossverify,
                settings.session_ubo_crossverify,
                message,
                timeout=cross_verify_timeout  # Use longer timeout for cross-verification
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
            logger.info(f"Parsing cross-verify data, type: {type(data)}")
            
            # Handle different data structures
            if isinstance(data, dict):
                # If data is a dict with a "candidates" key
                if "candidates" in data and isinstance(data["candidates"], list):
                    logger.info(f"Found 'candidates' key with {len(data['candidates'])} items")
                    data = data["candidates"]
                # If data is a dict with other keys, try to extract candidates
                elif "candidate" in data or "ubo_name" in data or "name" in data or "evidence" in data:
                    # Single candidate as dict
                    logger.info("Found single candidate as dict")
                    data = [data]
                else:
                    logger.warning(f"Unexpected dict structure: {list(data.keys())}")
            
            if isinstance(data, list):
                logger.info(f"Processing list with {len(data)} items")
                for idx, item in enumerate(data):
                    if isinstance(item, dict):
                        # Try multiple possible field names for candidate name
                        candidate_name = (
                            item.get("candidate") or 
                            item.get("ubo_name") or 
                            item.get("name") or 
                            item.get("candidate_name") or
                            ""
                        )
                        
                        logger.info(f"[ITEM {idx+1}] Extracted candidate_name: '{candidate_name}' from fields: {list(item.keys())}")
                        
                        # Only add if candidate name is not empty
                        if candidate_name and candidate_name.strip():
                            # Parse ubo_type enum
                            ubo_type_value = item.get("ubo_type")
                            ubo_type = None
                            if ubo_type_value:
                                try:
                                    from models.schemas import UBOType
                                    # Handle both string and enum values
                                    if isinstance(ubo_type_value, str):
                                        ubo_type = UBOType(ubo_type_value)
                                    else:
                                        ubo_type = ubo_type_value
                                except (ValueError, TypeError):
                                    logger.warning(f"Invalid ubo_type value: {ubo_type_value}, expected 'Control' or 'Ownership'")
                            
                            candidates.append(CrossVerifyCandidate(
                                candidate=candidate_name.strip(),
                                evidence=item.get("evidence"),
                                source_url=item.get("source_url"),
                                confidence=item.get("confidence"),
                                ubo_type=ubo_type,
                                relation=item.get("relation")  # Extract relation field from response
                            ))
                            logger.info(f"[ITEM {idx+1}] Added candidate: '{candidate_name.strip()}'")
                        else:
                            logger.warning(f"[ITEM {idx+1}] Skipping item with empty candidate_name")
            else:
                logger.warning(f"Data is not a list or dict: {type(data)}")
                
        except Exception as e:
            logger.warning(f"Could not parse cross-verify candidates: {str(e)}")
            import traceback
            logger.warning(f"Traceback: {traceback.format_exc()}")
            logger.debug(f"Data structure: {type(data)} - {data}")
        
        logger.info(f"Parsed {len(candidates)} cross-verify candidates: {[c.candidate for c in candidates]}")
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
    
    async def _check_natural_psc(self, name: str, company_name: str, identification: Optional[Dict] = None, depth: int = 0) -> bool:
        """Check if a name is a natural person using Lyzr agent"""
        import json
        from services.lyzr_service import LyzrAgentService
        from utils.settings import settings
        
        logger.info(f"[DEPTH {depth}] Natural PSC Check - INPUT:")
        logger.info(f"[DEPTH {depth}]   Name: {name}")
        logger.info(f"[DEPTH {depth}]   Company Name: {company_name}")
        logger.info(f"[DEPTH {depth}]   Identification: {json.dumps(identification or {}, indent=2)}")
        
        try:
            lyzr_service = LyzrAgentService()
            agent_id = settings.agent_psc_natural_person
            session_id = settings.session_psc_natural_person
            
            if not agent_id or not session_id:
                logger.warning(f"[DEPTH {depth}] PSC natural person agent not configured, skipping check")
                return False
            
            message_data = {
                "Company_name": company_name,
                "Name": name,
                "identification": identification or {}
            }
            message = json.dumps(message_data, indent=2)
            
            logger.info(f"[DEPTH {depth}] Natural PSC Check - Lyzr Agent Input:")
            logger.info(f"[DEPTH {depth}]   Agent ID: {agent_id}")
            logger.info(f"[DEPTH {depth}]   Session ID: {session_id}")
            logger.info(f"[DEPTH {depth}]   Message: {message}")
            
            lyzr_response = await lyzr_service.call_custom_agent(
                agent_id=agent_id,
                session_id=session_id,
                message=message,
                timeout=180  # Increased timeout for natural PSC checks
            )
            
            logger.info(f"[DEPTH {depth}] Natural PSC Check - Lyzr Agent Response:")
            logger.info(f"[DEPTH {depth}]   Success: {lyzr_response.success}")
            if lyzr_response.success:
                logger.info(f"[DEPTH {depth}]   Response Content: {lyzr_response.content[:500]}...")
            else:
                logger.warning(f"[DEPTH {depth}]   Error: {lyzr_response.error}")
            
            if not lyzr_response.success:
                logger.warning(f"[DEPTH {depth}] Lyzr agent call failed for natural PSC check: {lyzr_response.error}")
                return False
            
            # Parse response
            try:
                content = lyzr_response.content.strip()
                if content.startswith("```"):
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
                
                # Try to parse JSON, if it fails, try to repair it
                try:
                    parsed_response = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"[DEPTH {depth}] Initial JSON parsing failed: {str(e)}")
                    logger.info(f"[DEPTH {depth}] Attempting to repair malformed JSON...")
                    logger.info(f"[DEPTH {depth}] Raw content (first 500 chars): {content[:500]}")
                    
                    if json_repair:
                        try:
                            # Use json_repair to fix malformed JSON
                            repaired_content = json_repair.repair_json(content)
                            parsed_response = json.loads(repaired_content)
                            logger.info(f"[DEPTH {depth}] ✓ Successfully repaired and parsed JSON")
                        except Exception as repair_error:
                            logger.error(f"[DEPTH {depth}] JSON repair failed: {str(repair_error)}")
                            raise e  # Re-raise original error
                    else:
                        logger.error(f"[DEPTH {depth}] json_repair module not available, cannot repair JSON")
                        raise e  # Re-raise original error
                
                # Handle the natural PSC agent response schema: {"results": [{"name": "...", "natural_psc": true/false}]}
                natural_psc = False
                results_list = None
                
                if isinstance(parsed_response, dict):
                    # Check for the correct schema: {"results": [...]}
                    if "results" in parsed_response:
                        results_list = parsed_response.get("results", [])
                        logger.info(f"[DEPTH {depth}] Found 'results' key with {len(results_list)} items")
                    # Legacy support: direct dict with natural_psc field
                    elif "natural_psc" in parsed_response:
                        natural_psc = parsed_response.get("natural_psc", False)
                        logger.info(f"[DEPTH {depth}] Found direct natural_psc field: {natural_psc}")
                        return bool(natural_psc)
                    # Legacy support: if it's a dict but no results key, treat as single result
                    else:
                        logger.warning(f"[DEPTH {depth}] Dict response without 'results' key, treating as single result")
                        results_list = [parsed_response]
                elif isinstance(parsed_response, list):
                    # Legacy support: direct list response
                    logger.info(f"[DEPTH {depth}] Response is a direct list (legacy format)")
                    results_list = parsed_response
                else:
                    logger.warning(f"[DEPTH {depth}] Unexpected response type: {type(parsed_response)}")
                    return False
                
                # Process the results list
                if results_list:
                    logger.info(f"[DEPTH {depth}] Processing {len(results_list)} results, searching for name: '{name}'")
                    found_match = False
                    name_normalized = name.lower().strip()
                    
                    # Log all items in the list for debugging
                    logger.info(f"[DEPTH {depth}] Results items:")
                    for i, item in enumerate(results_list):
                        if isinstance(item, dict):
                            # Support both "name" (correct schema) and "Name" (legacy)
                            item_name = item.get("name") or item.get("Name") or ""
                            item_natural = item.get("natural_psc", "N/A")
                            logger.info(f"[DEPTH {depth}]   Item {i+1}: name='{item_name}', natural_psc={item_natural}")
                    
                    # Try exact match first
                    for item in results_list:
                        if isinstance(item, dict):
                            # Support both "name" (correct schema) and "Name" (legacy)
                            item_name = item.get("name") or item.get("Name") or ""
                            item_name_normalized = item_name.lower().strip() if item_name else ""
                            
                            logger.info(f"[DEPTH {depth}] Comparing: input='{name_normalized}' vs item='{item_name_normalized}'")
                            
                            # Check if this item's name matches the name we're checking
                            if item_name_normalized == name_normalized:
                                if "natural_psc" in item:
                                    natural_psc = item.get("natural_psc", False)
                                    found_match = True
                                    logger.info(f"[DEPTH {depth}] ✓ Found exact match: name='{item_name}', natural_psc={natural_psc}")
                                    break
                            # Also try fuzzy matching (contains check) as fallback
                            elif item_name_normalized and (name_normalized in item_name_normalized or item_name_normalized in name_normalized):
                                if "natural_psc" in item:
                                    natural_psc = item.get("natural_psc", False)
                                    found_match = True
                                    logger.info(f"[DEPTH {depth}] ✓ Found fuzzy match: name='{item_name}', natural_psc={natural_psc}")
                                    break
                    
                    if not found_match:
                        logger.warning(f"[DEPTH {depth}] ✗ No exact/fuzzy match found in results for: '{name}'")
                        available_names = [item.get("name") or item.get("Name", "N/A") for item in results_list if isinstance(item, dict)]
                        logger.warning(f"[DEPTH {depth}] Available names in response: {available_names}")
                        logger.warning(f"[DEPTH {depth}] Input name (normalized): '{name_normalized}'")
                        
                        # Try word-by-word matching (more lenient)
                        logger.info(f"[DEPTH {depth}] Trying word-based matching...")
                        name_words = set(name_normalized.split()) if name_normalized else set()
                        for item in results_list:
                            if isinstance(item, dict):
                                item_name = item.get("name") or item.get("Name") or ""
                                item_name_normalized = item_name.lower().strip() if item_name else ""
                                item_words = set(item_name_normalized.split()) if item_name_normalized else set()
                                
                                # Check if there's significant word overlap
                                if name_words and item_words:
                                    common_words = name_words.intersection(item_words)
                                    overlap_ratio = len(common_words) / max(len(name_words), len(item_words)) if max(len(name_words), len(item_words)) > 0 else 0
                                    
                                    logger.info(f"[DEPTH {depth}]   Comparing words: input={name_words} vs item={item_words}, overlap={common_words}, ratio={overlap_ratio:.2f}")
                                    
                                    # If at least 50% word overlap or all words match
                                    if overlap_ratio >= 0.5 or common_words == name_words or common_words == item_words:
                                        if "natural_psc" in item:
                                            natural_psc = item.get("natural_psc", False)
                                            found_match = True
                                            logger.info(f"[DEPTH {depth}] ✓ Found word-based match: name='{item_name}', natural_psc={natural_psc}, overlap_ratio={overlap_ratio:.2f}")
                                            break
                        
                        # If still no match, try more aggressive matching
                        if not found_match:
                            logger.warning(f"[DEPTH {depth}] No word-based match found, trying aggressive matching...")
                            
                            # Try removing common suffixes/prefixes and matching
                            name_clean = name_normalized.replace("mr ", "").replace("mrs ", "").replace("ms ", "").replace("dr ", "").strip()
                            for item in results_list:
                                if isinstance(item, dict):
                                    item_name = item.get("name") or item.get("Name") or ""
                                    item_name_normalized = item_name.lower().strip() if item_name else ""
                                    item_name_clean = item_name_normalized.replace("mr ", "").replace("mrs ", "").replace("ms ", "").replace("dr ", "").strip()
                                    
                                    if item_name_clean == name_clean or name_clean == item_name_clean:
                                        if "natural_psc" in item:
                                            natural_psc = item.get("natural_psc", False)
                                            found_match = True
                                            logger.info(f"[DEPTH {depth}] ✓ Found cleaned name match: name='{item_name}', natural_psc={natural_psc}")
                                            break
                            
                            # Last resort: if list has only one item, use it as fallback
                            if not found_match and len(results_list) == 1 and isinstance(results_list[0], dict):
                                if "natural_psc" in results_list[0]:
                                    natural_psc = results_list[0].get("natural_psc", False)
                                    logger.info(f"[DEPTH {depth}] Using single item as fallback, natural_psc = {natural_psc}")
                                    found_match = True
                            
                            # Final fallback: if checking a specific name and list has that exact name (case-insensitive), use it
                            if not found_match:
                                for item in results_list:
                                    if isinstance(item, dict):
                                        item_name = item.get("name") or item.get("Name") or ""
                                        item_name_normalized = item_name.lower().strip() if item_name else ""
                                        # Direct comparison after all normalization
                                        if item_name_normalized == name_normalized:
                                            if "natural_psc" in item:
                                                natural_psc = item.get("natural_psc", False)
                                                found_match = True
                                                logger.info(f"[DEPTH {depth}] ✓ Found final fallback match: name='{item_name}', natural_psc={natural_psc}")
                                                break
                else:
                    logger.warning(f"[DEPTH {depth}] No results list found in response")
                    return False
                
                logger.info(f"[DEPTH {depth}] Natural PSC Check - OUTPUT:")
                logger.info(f"[DEPTH {depth}]   Parsed Response Type: {type(parsed_response)}")
                logger.info(f"[DEPTH {depth}]   Parsed Response: {json.dumps(parsed_response, indent=2, default=str)}")
                logger.info(f"[DEPTH {depth}]   Natural PSC Result: {natural_psc}")
                
                return bool(natural_psc)
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logger.warning(f"[DEPTH {depth}] Failed to parse Lyzr response for natural PSC check: {str(e)}")
                logger.warning(f"[DEPTH {depth}] Response type: {type(parsed_response) if 'parsed_response' in locals() else 'unknown'}")
                logger.warning(f"[DEPTH {depth}] Raw response: {lyzr_response.content[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"[DEPTH {depth}] Error checking natural PSC: {str(e)}")
            import traceback
            logger.error(f"[DEPTH {depth}] Traceback: {traceback.format_exc()}")
            return False
    
    async def _find_natural_psc_recursive(self, candidate_name: str, original_company_name: str, domain: Optional[str] = None, location: Optional[str] = None, max_depth: int = 3, current_depth: int = 0, found_natural_persons: Optional[List[CrossVerifyCandidate]] = None, current_trace_chain: Optional[List[TraceChainItem]] = None, visited_companies: Optional[set] = None, unresolved_companies: Optional[List[str]] = None) -> Dict[str, Any]:
        """Recursively find all natural PSC candidates using cross-verification Lyzr agent
        
        Args:
            candidate_name: Current entity being searched
            original_company_name: The original company name we started with
            domain: Company domain (optional)
            location: Company location (optional, only used at depth 0)
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            found_natural_persons: List to accumulate found natural persons
            current_trace_chain: Current trace chain showing path from original company to current entity
            visited_companies: Set of normalized company names already processed to avoid duplicate calls
            unresolved_companies: List of companies that were processed but found 0 natural PSCs
        
        Returns:
            Dict with keys:
                - 'natural_psc_candidates': List of natural PSC candidates found
                - 'unresolved_companies': List of companies with 0 natural PSCs found
        """
        import json
        
        if found_natural_persons is None:
            found_natural_persons = []
        
        if unresolved_companies is None:
            unresolved_companies = []
        
        if current_trace_chain is None:
            current_trace_chain = []
            # Add the original company as the first item in trace chain
            if current_depth == 0:
                current_trace_chain.append(TraceChainItem(
                    entity_name=original_company_name,
                    entity_type="Company",
                    depth=0,
                    relation=None
                ))
        
        # Initialize visited_companies set if not provided
        if visited_companies is None:
            visited_companies = set()
        
        # Normalize company name for comparison (lowercase, strip whitespace)
        normalized_candidate = candidate_name.lower().strip() if candidate_name else ""
        
        # Check if we've already processed this company
        if normalized_candidate and normalized_candidate in visited_companies:
            logger.warning(f"[DEPTH {current_depth}] SKIPPING: Company '{candidate_name}' already processed (normalized: '{normalized_candidate}')")
            logger.warning(f"[DEPTH {current_depth}] Visited companies so far: {len(visited_companies)}")
            logger.warning(f"[DEPTH {current_depth}] Returning found natural persons: {len(found_natural_persons)}")
            return {
                'natural_psc_candidates': found_natural_persons,
                'unresolved_companies': unresolved_companies
            }
        
        # Add current candidate to visited set before processing
        if normalized_candidate:
            visited_companies.add(normalized_candidate)
            logger.info(f"[DEPTH {current_depth}] Added '{candidate_name}' to visited companies (normalized: '{normalized_candidate}')")
            logger.info(f"[DEPTH {current_depth}] Total visited companies: {len(visited_companies)}")
        
        logger.info("=" * 80)
        logger.info(f"[RECURSIVE SEARCH - DEPTH {current_depth}/{max_depth}]")
        logger.info(f"[DEPTH {current_depth}] INPUT:")
        logger.info(f"[DEPTH {current_depth}]   Candidate Name: {candidate_name}")
        logger.info(f"[DEPTH {current_depth}]   Original Company Name: {original_company_name}")
        logger.info(f"[DEPTH {current_depth}]   Domain: {domain}")
        logger.info(f"[DEPTH {current_depth}]   Location: {location}")
        logger.info(f"[DEPTH {current_depth}]   Current Depth: {current_depth}")
        logger.info(f"[DEPTH {current_depth}]   Max Depth: {max_depth}")
        logger.info(f"[DEPTH {current_depth}]   Natural Persons Found So Far: {len(found_natural_persons)}")
        logger.info(f"[DEPTH {current_depth}]   Visited Companies: {len(visited_companies)}")
        logger.info("=" * 80)
        
        if current_depth >= max_depth:
            logger.warning(f"[DEPTH {current_depth}] OUTPUT: Max depth {max_depth} reached for candidate: {candidate_name}")
            logger.warning(f"[DEPTH {current_depth}] Returning found natural persons: {len(found_natural_persons)}")
            # Add to unresolved if no natural PSCs found for this company
            if len(found_natural_persons) == 0 or not any(c.candidate == candidate_name for c in found_natural_persons):
                if candidate_name not in unresolved_companies:
                    unresolved_companies.append(candidate_name)
                    logger.info(f"[DEPTH {current_depth}] Added '{candidate_name}' to unresolved companies (max depth reached)")
            return {
                'natural_psc_candidates': found_natural_persons,
                'unresolved_companies': unresolved_companies
            }
        
        try:
            # First, check if the candidate itself is a natural person
            logger.info(f"[DEPTH {current_depth}] Step 1: Checking if candidate is natural person...")
            is_natural = await self._check_natural_psc(candidate_name, original_company_name, depth=current_depth)
            
            logger.info(f"[DEPTH {current_depth}] Step 1 Result: is_natural = {is_natural}")
            
            if is_natural:
                logger.info(f"[DEPTH {current_depth}] ✓ OUTPUT: Candidate {candidate_name} is already a natural person")
                # Build trace chain for this natural person
                trace_chain = current_trace_chain.copy()
                trace_chain.append(TraceChainItem(
                    entity_name=candidate_name,
                    entity_type="Natural Person",
                    depth=current_depth,
                    relation="Direct identification"
                ))
                # Create a candidate object for this natural person
                natural_candidate = CrossVerifyCandidate(
                    candidate=candidate_name,
                    evidence=f"Found as natural person at depth {current_depth}",
                    source_url=None,
                    confidence="High",
                    ubo_type=None,
                    trace_chain=trace_chain
                )
                found_natural_persons.append(natural_candidate)
                logger.info(f"[DEPTH {current_depth}] Added natural person: {candidate_name} (Total: {len(found_natural_persons)})")
                logger.info(f"[DEPTH {current_depth}] Trace chain length: {len(trace_chain)}")
                # Continue to check if we should recurse further (in case there are more entities to explore)
            
            # Call cross-verification agent to find related entities
            logger.info(f"[DEPTH {current_depth}] Step 2: Calling cross-verification agent...")
            logger.info(f"[DEPTH {current_depth}]   Searching for entities related to: {candidate_name}")
            
            # Only use location for the first call (depth 0), not for recursive calls
            location_for_call = location if current_depth == 0 else None
            if current_depth > 0:
                logger.info(f"[DEPTH {current_depth}]   Location not used for recursive calls (depth > 0)")
            
            cross_result = await self.cross_verify_ubos(candidate_name, domain, location_for_call, tracing_company_name=original_company_name)
            
            logger.info(f"[DEPTH {current_depth}] Step 2 Result:")
            logger.info(f"[DEPTH {current_depth}]   Success: {cross_result.get('success')}")
            
            if not cross_result.get("success"):
                error_msg = cross_result.get("error", "Unknown error")
                logger.warning(f"[DEPTH {current_depth}] OUTPUT: Cross-verification failed for: {candidate_name}")
                logger.warning(f"[DEPTH {current_depth}]   Error: {error_msg}")
                logger.warning(f"[DEPTH {current_depth}] Returning found natural persons: {len(found_natural_persons)}")
                # Add to unresolved if no natural PSCs found for this company
                if candidate_name not in unresolved_companies:
                    unresolved_companies.append(candidate_name)
                    logger.info(f"[DEPTH {current_depth}] Added '{candidate_name}' to unresolved companies (cross-verification failed)")
                return {
                    'natural_psc_candidates': found_natural_persons,
                    'unresolved_companies': unresolved_companies
                }
            
            # Parse cross-verification results
            cross_candidates = self.parse_cross_verify(cross_result.get("data"))
            
            logger.info(f"[DEPTH {current_depth}] Step 2 Details:")
            logger.info(f"[DEPTH {current_depth}]   Candidates Found: {len(cross_candidates)}")
            logger.info(f"[DEPTH {current_depth}]   Candidate Names: {[c.candidate for c in cross_candidates]}")
            
            # Log full candidate details for debugging
            if cross_candidates:
                logger.info(f"[DEPTH {current_depth}]   Full Candidate Details:")
                for i, cand in enumerate(cross_candidates, 1):
                    logger.info(f"[DEPTH {current_depth}]     {i}. {cand.candidate} (Confidence: {cand.confidence}, Type: {cand.ubo_type})")
                    if cand.evidence:
                        logger.info(f"[DEPTH {current_depth}]        Evidence: {cand.evidence[:200]}...")
            
            if not cross_candidates:
                logger.warning(f"[DEPTH {current_depth}] OUTPUT: No candidates found from cross-verification for: {candidate_name}")
                logger.warning(f"[DEPTH {current_depth}] Returning found natural persons: {len(found_natural_persons)}")
                # Add to unresolved if no natural PSCs found for this company
                if candidate_name not in unresolved_companies:
                    unresolved_companies.append(candidate_name)
                    logger.info(f"[DEPTH {current_depth}] Added '{candidate_name}' to unresolved companies (no candidates found)")
                return {
                    'natural_psc_candidates': found_natural_persons,
                    'unresolved_companies': unresolved_companies
                }
            
            # Process each candidate from cross-verification
            logger.info(f"[DEPTH {current_depth}] Step 3: Processing {len(cross_candidates)} candidates from cross-verification...")
            
            # Count non-natural entities for logging
            non_natural_count = 0
            natural_count = 0
            
            for idx, sub_candidate in enumerate(cross_candidates, 1):
                if not sub_candidate.candidate:
                    continue
                
                logger.info(f"[DEPTH {current_depth}] Step 3.{idx}: Processing sub-candidate: {sub_candidate.candidate}")
                logger.info(f"[DEPTH {current_depth}]   Candidate metadata: Confidence={sub_candidate.confidence}, UBO Type={sub_candidate.ubo_type}")
                
                # Check if this sub-candidate is natural
                logger.info(f"[DEPTH {current_depth}]   Checking if '{sub_candidate.candidate}' is a natural person...")
                is_sub_natural = await self._check_natural_psc(
                    sub_candidate.candidate,
                    original_company_name,
                    depth=current_depth
                )
                
                logger.info(f"[DEPTH {current_depth}] Step 3.{idx} Result: is_natural = {is_sub_natural}")
                if not is_sub_natural:
                    logger.info(f"[DEPTH {current_depth}]   '{sub_candidate.candidate}' is NOT a natural person - will recurse to find natural persons within it")
                
                if is_sub_natural:
                    natural_count += 1
                    logger.info(f"[DEPTH {current_depth}] ✓ Found natural person: {sub_candidate.candidate}")
                    
                    # Build trace chain for this natural person
                    trace_chain = current_trace_chain.copy()
                    # Add current entity if not already in chain (for depth > 0)
                    if current_depth > 0 and (not trace_chain or trace_chain[-1].entity_name != candidate_name):
                        trace_chain.append(TraceChainItem(
                            entity_name=candidate_name,
                            entity_type="Corporate Entity",
                            depth=current_depth,
                            relation=None
                        ))
                    # Add the natural person
                    trace_chain.append(TraceChainItem(
                        entity_name=sub_candidate.candidate,
                        entity_type="Natural Person",
                        depth=current_depth,
                        relation=sub_candidate.relation or "Found via cross-verification"
                    ))
                    
                    # Create a new candidate with trace chain, preserving original metadata
                    natural_candidate = CrossVerifyCandidate(
                        candidate=sub_candidate.candidate,
                        evidence=sub_candidate.evidence,
                        source_url=sub_candidate.source_url,
                        confidence=sub_candidate.confidence,
                        ubo_type=sub_candidate.ubo_type,
                        trace_chain=trace_chain
                    )
                    
                    # Add to found natural persons list
                    found_natural_persons.append(natural_candidate)
                    logger.info(f"[DEPTH {current_depth}] Added natural person: {sub_candidate.candidate} (Total: {len(found_natural_persons)})")
                    logger.info(f"[DEPTH {current_depth}] Trace chain length: {len(trace_chain)}")
                    # Continue to next candidate (don't stop here)
                else:
                    non_natural_count += 1
                    
                    # Normalize sub-candidate name for duplicate check
                    normalized_sub_candidate = sub_candidate.candidate.lower().strip() if sub_candidate.candidate else ""
                    
                    # Check if we've already processed this company
                    if normalized_sub_candidate and normalized_sub_candidate in visited_companies:
                        logger.warning(f"[DEPTH {current_depth}] SKIPPING RECURSION: Company '{sub_candidate.candidate}' already processed (normalized: '{normalized_sub_candidate}')")
                        logger.warning(f"[DEPTH {current_depth}]   This company was already searched at a previous depth")
                        continue
                    
                    # If not natural, recurse for this sub-candidate
                    logger.info(f"[DEPTH {current_depth}] Step 3.{idx}: Sub-candidate is not natural, recursing...")
                    logger.info(f"[DEPTH {current_depth}]   Non-natural entity #{non_natural_count} at depth {current_depth}: {sub_candidate.candidate}")
                    logger.info(f"[DEPTH {current_depth}]   Next candidate to search: {sub_candidate.candidate}")
                    logger.info(f"[DEPTH {current_depth}]   Remaining depth: {max_depth - current_depth - 1} levels")
                    logger.info("=" * 80)
                    
                    # Build trace chain for recursive call
                    next_trace_chain = current_trace_chain.copy()
                    # Add current entity if not already in chain (for depth > 0)
                    if current_depth > 0 and (not next_trace_chain or next_trace_chain[-1].entity_name != candidate_name):
                        next_trace_chain.append(TraceChainItem(
                            entity_name=candidate_name,
                            entity_type="Corporate Entity",
                            depth=current_depth,
                            relation=None
                        ))
                    # Add the sub-candidate (non-natural entity we're recursing into)
                    next_trace_chain.append(TraceChainItem(
                        entity_name=sub_candidate.candidate,
                        entity_type="Corporate Entity",
                        depth=current_depth,
                        relation=sub_candidate.relation or "Related entity"
                    ))
                    
                    # Recursively search for natural persons in this sub-candidate
                    # Don't pass location for recursive calls (only used in first call)
                    recursive_results = await self._find_natural_psc_recursive(
                        sub_candidate.candidate,
                        original_company_name,
                        domain,
                        None,  # Location only used for first call (depth 0)
                        max_depth,
                        current_depth + 1,
                        found_natural_persons,  # Pass the list to accumulate results
                        next_trace_chain,  # Pass the updated trace chain
                        visited_companies,  # Pass the visited companies set to avoid duplicate calls
                        unresolved_companies  # Pass the unresolved companies list
                    )
                    
                    logger.info("=" * 80)
                    # Extract results from dict
                    recursive_natural_pscs = recursive_results.get('natural_psc_candidates', [])
                    recursive_unresolved = recursive_results.get('unresolved_companies', [])
                    num_before = len(found_natural_persons)
                    found_natural_persons = recursive_natural_pscs  # Update with accumulated results
                    num_after = len(found_natural_persons)
                    new_natural_pscs = num_after - num_before
                    logger.info(f"[DEPTH {current_depth}] Recursive call for '{sub_candidate.candidate}' found {new_natural_pscs} new natural persons")
                    
                    # Merge unresolved companies
                    for unresolved in recursive_unresolved:
                        if unresolved not in unresolved_companies:
                            unresolved_companies.append(unresolved)
                    
                    # Check if this sub-candidate found 0 natural PSCs
                    # If no new natural PSCs were found from this recursive call, add to unresolved
                    if new_natural_pscs == 0:
                        if sub_candidate.candidate not in unresolved_companies:
                            unresolved_companies.append(sub_candidate.candidate)
                            logger.info(f"[DEPTH {current_depth}] Added '{sub_candidate.candidate}' to unresolved companies (0 natural PSCs found)")
            
            # Log summary of processing at this depth
            logger.info(f"[DEPTH {current_depth}] Step 3 Summary: Processed {len(cross_candidates)} candidates - {natural_count} natural, {non_natural_count} non-natural (all {non_natural_count} were recursively searched)")
            if non_natural_count > 0:
                remaining_depth = max_depth - current_depth - 1
                logger.info(f"[DEPTH {current_depth}] ⚠️  Exponential growth warning: {non_natural_count} non-natural entities will each spawn recursive searches (up to depth {current_depth + remaining_depth})")
            
            # Check if this company found 0 natural PSCs (after processing all candidates)
            # Only add to unresolved if we didn't find any natural persons from this company's search
            # We check by seeing if any natural person has this company in their trace chain at the current depth
            found_from_this_company = False
            for np in found_natural_persons:
                if np.trace_chain:
                    # Check if any trace chain item at current depth matches this company
                    for chain_item in np.trace_chain:
                        if chain_item.depth == current_depth and chain_item.entity_name == candidate_name:
                            found_from_this_company = True
                            break
                    if found_from_this_company:
                        break
            
            # If no natural PSCs found from this company's search, add to unresolved
            if not found_from_this_company and candidate_name not in unresolved_companies:
                unresolved_companies.append(candidate_name)
                logger.info(f"[DEPTH {current_depth}] Added '{candidate_name}' to unresolved companies (0 natural PSCs found after processing)")
            
            # Return all found natural persons
            logger.info(f"[DEPTH {current_depth}] OUTPUT: Returning {len(found_natural_persons)} natural persons found")
            logger.info(f"[DEPTH {current_depth}] Natural persons: {[c.candidate for c in found_natural_persons]}")
            logger.info(f"[DEPTH {current_depth}] Unresolved companies: {len(unresolved_companies)}")
            return {
                'natural_psc_candidates': found_natural_persons,
                'unresolved_companies': unresolved_companies
            }
            
        except Exception as e:
            logger.error(f"[DEPTH {current_depth}] ERROR in recursive natural PSC search for {candidate_name}: {str(e)}")
            import traceback
            logger.error(f"[DEPTH {current_depth}] Traceback: {traceback.format_exc()}")
            logger.warning(f"[DEPTH {current_depth}] Returning found natural persons: {len(found_natural_persons)}")
            # Add to unresolved on error if no natural PSCs found
            if candidate_name not in unresolved_companies:
                unresolved_companies.append(candidate_name)
                logger.info(f"[DEPTH {current_depth}] Added '{candidate_name}' to unresolved companies (error occurred)")
            return {
                'natural_psc_candidates': found_natural_persons,
                'unresolved_companies': unresolved_companies
            }
    
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
            cross_result = await self.cross_verify_ubos(company_name, domain, location, tracing_company_name=company_name)
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

