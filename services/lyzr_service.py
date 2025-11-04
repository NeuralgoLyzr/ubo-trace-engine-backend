"""
UBO Trace Engine Backend - Lyzr AI Agent Service
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
    LyzrAgentRequest, LyzrAgentResponse, TraceStage, TraceStageResult,
    CompanyDomainAnalysisRequest, CompanyDomainAnalysisResponse, CompanyDomain
)

logger = logging.getLogger(__name__)

class LyzrAgentService:
    """Service for interacting with Lyzr AI agents"""
    
    def __init__(self):
        self.api_url = settings.lyzr_api_url
        self.api_key = settings.lyzr_api_key
        self.user_id = settings.lyzr_user_id
        self.timeout = settings.api_timeout
        
        # Agent configurations for different stages
        self.agent_configs = {
            TraceStage.STAGE_1A: {
                "agent_id": settings.agent_stage_1a,
                "session_id": settings.session_stage_1a,
                "description": "Direct Evidence (General)"
            },
            TraceStage.STAGE_1B: {
                "agent_id": settings.agent_stage_1b,
                "session_id": settings.session_stage_1b,
                "description": "Direct Evidence (Time-filtered)"
            },
            TraceStage.STAGE_2A: {
                "agent_id": settings.agent_stage_2a,
                "session_id": settings.session_stage_2a,
                "description": "Indirect Evidence (General)"
            },
            TraceStage.STAGE_2B: {
                "agent_id": settings.agent_stage_2b,
                "session_id": settings.session_stage_2b,
                "description": "Indirect Evidence (Time-filtered)"
            }
        }
    
    def _infer_domain_from_entity(self, entity: str) -> str:
        """Infer plausible domain name from entity text for context building"""
        words = re.findall(r'[A-Za-z]+', entity)
        core = [w.lower() for w in words if w.lower() not in
                ["limited", "ltd", "company", "co", "dmcc", "llc", "inc", "plc",
                 "mea", "pvt", "private", "holdings", "group", "corp"]]
        if not core:
            return "unknown"
        return f"{''.join(core[:2])}.com"
    
    async def call_agent(self, stage: TraceStage, entity: str, ubo_name: Optional[str] = None, location: Optional[str] = None, domain: Optional[str] = None) -> LyzrAgentResponse:
        """Call the appropriate Lyzr AI agent for the given stage"""
        
        start_time = time.time()
        
        try:
            config = self.agent_configs.get(stage)
            if not config:
                raise ValueError(f"Unknown stage: {stage}")
            
            # Build simple message with available parameters
            message_parts = [f"Entity: {entity}"]
            if ubo_name:
                message_parts.append(f"UBO Name: {ubo_name}")
            if location:
                message_parts.append(f"Location: {location}")
            if domain:
                message_parts.append(f"Domain: {domain}")
            message = ", ".join(message_parts)
            
            request_data = LyzrAgentRequest(
                user_id=self.user_id,
                agent_id=config["agent_id"],
                session_id=config["session_id"],
                message=message
            )
            
            logger.info(f"Sending request to Lyzr agent {stage}: {config['agent_id']}")
            logger.info(f"Message: {message}")
            
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
                logger.info(f"Full response structure: {list(result.keys())}")
                
                # Try different response formats
                content = result.get("response", "")
                if not content:
                    # Fallback to OpenAI-style format
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    # Try direct content field
                    content = result.get("content", "")
                
                # Try to parse JSON response to extract facts and summary
                facts = []
                summary = None
                
                try:
                    import json
                    parsed_json = json.loads(content)
                    if isinstance(parsed_json, dict) and "facts" in parsed_json:
                        # Extract structured facts
                        facts_data = parsed_json.get("facts", [])
                        for fact_item in facts_data:
                            if isinstance(fact_item, dict) and "fact" in fact_item and "url" in fact_item:
                                facts.append({
                                    "fact": fact_item["fact"],
                                    "url": fact_item["url"]
                                })
                        
                        # Extract summary
                        summary = parsed_json.get("summary", "")
                        
                        logger.info(f"Extracted {len(facts)} facts and summary from JSON response")
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Could not parse JSON response: {str(e)}")
                    facts = []
                    summary = None
                
                processing_time = int((time.time() - start_time) * 1000)
                
                logger.info(f"Lyzr agent {stage} completed in {processing_time}ms")
                logger.info(f"Response content length: {len(content)} chars")
                if content:
                    logger.info(f"Response preview: {content[:200]}...")
                else:
                    logger.warning(f"Empty response from Lyzr agent {stage}")
                
                return LyzrAgentResponse(
                    success=True,
                    content=content,
                    facts=facts,
                    summary=summary,
                    processing_time_ms=processing_time
                )
                
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Lyzr agent {stage} failed: {str(e)}")
            
            return LyzrAgentResponse(
                success=False,
                error=str(e),
                processing_time_ms=processing_time
            )
    
    def parse_results(self, content: str, ubo_name: Optional[str] = None) -> Dict[str, Any]:
        """Parse the AI response and extract structured data"""
        
        urls = self._extract_urls(content)
        direct, indirect = [], []
        name_variants = self._partial_name_patterns(ubo_name) if ubo_name else []
        
        # Try to parse JSON response first (for Stage 1A, 1B, 2A, and 2B structured format)
        try:
            import json
            parsed_json = json.loads(content)
            if isinstance(parsed_json, dict) and "facts" in parsed_json:
                # Handle structured response format
                facts = parsed_json.get("facts", [])
                for fact_item in facts:
                    if isinstance(fact_item, dict):
                        fact_text = fact_item.get("fact", "")
                        fact_url = fact_item.get("url", "")
                        
                        if fact_text and fact_url:
                            # All stages now use the same format: "Fact — URL"
                            formatted_fact = f"{fact_text} — {fact_url}"
                            
                            # Determine if this is direct or indirect evidence based on content
                            fact_lower = fact_text.lower()
                            if any(keyword in fact_lower for keyword in ["subsidiary", "holding", "fund", "trust", "affiliate", "through", "owned by", "via"]):
                                indirect.append(formatted_fact)
                            else:
                                direct.append(formatted_fact)
                            
                            # Add URL to URLs list
                            if fact_url not in urls:
                                urls.append(fact_url)
                
                return {
                    "direct": direct,
                    "indirect": indirect,
                    "urls": urls,
                    "has_direct": bool(direct),
                    "has_indirect": bool(indirect),
                }
        except (json.JSONDecodeError, KeyError):
            # Fall back to text parsing if JSON parsing fails
            pass
        
        # Original text parsing logic
        sentences = re.split(r'(?<=[\.\n])\s+', content)
        
        for sentence in sentences:
            sentence_low = sentence.lower()
            # Only check for name mentions if ubo_name is provided
            if not ubo_name or self._find_mentions(sentence, name_variants):
                if any(keyword in sentence_low for keyword in ["shareholder", "director", "beneficial owner", "%", "appointed"]):
                    direct.append(sentence.strip())
                elif any(keyword in sentence_low for keyword in ["subsidiary", "holding", "fund", "trust", "affiliate", "through", "owned by"]):
                    indirect.append(sentence.strip())
        
        return {
            "direct": list(set(direct))[:10],
            "indirect": list(set(indirect))[:10],
            "urls": urls,
            "has_direct": bool(direct),
            "has_indirect": bool(indirect),
        }
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract unique URLs from text"""
        return sorted(set(re.findall(r'https?://[^\s\)\]>,]+', text)))
    
    def _partial_name_patterns(self, full_name: Optional[str]) -> List[str]:
        """Return regex variants for partial match detection"""
        if not full_name:
            return []
        parts = full_name.split()
        patterns = [full_name.lower()]
        if len(parts) >= 2:
            initials = f"{parts[0][0]}\\.? ?{parts[-1]}".lower()
            patterns.append(initials)
            patterns.append(parts[-1].lower())  # last name only
        return patterns
    
    def _find_mentions(self, text: str, patterns: List[str]) -> bool:
        """Check if any pattern is mentioned in the text"""
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in patterns)
    
    def _has_zero_domain_results(self, response: CompanyDomainAnalysisResponse) -> bool:
        """Check if domain analysis response has zero findings"""
        if not response.success:
            return True
        
        return len(response.companies) == 0
    
    async def analyze_company_domains(self, company_name: str, ubo_name: Optional[str] = None, address: str = "") -> CompanyDomainAnalysisResponse:
        """Analyze company domains using the specialized Lyzr agent with retry logic for zero results"""
        
        start_time = time.time()
        max_retries = 5
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries + 1):  # 0, 1, 2, 3, 4, 5 (total 6 attempts)
            is_retry = attempt > 0
            
            try:
                if is_retry:
                    logger.info(f"Retry attempt {attempt} for domain analysis (company: {company_name})")
                
                # Build message in the format expected by the agent
                message_parts = [f"company_name : {company_name}"]
                if ubo_name:
                    message_parts.append(f"UBO_name: {ubo_name}")
                if address:
                    message_parts.append(f"address: {address}")
                message = " , ".join(message_parts)
                
                request_data = LyzrAgentRequest(
                    user_id=self.user_id,
                    agent_id=settings.agent_company_domain,
                    session_id=settings.session_company_domain,
                    message=message
                )
                
                logger.info(f"Sending company domain analysis request")
                logger.info(f"Message: {message}")
                
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
                    logger.info(f"Company domain analysis response structure: {list(result.keys())}")
                    
                    # Extract content from response
                    content = result.get("response", "")
                    if not content:
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if not content:
                        content = result.get("content", "")
                    
                    # Parse the JSON response to extract companies
                    companies = []
                    try:
                        parsed_json = json.loads(content)
                        if isinstance(parsed_json, dict) and "companies" in parsed_json:
                            companies_data = parsed_json.get("companies", [])
                            for company_data in companies_data:
                                if isinstance(company_data, dict):
                                    company = CompanyDomain(
                                        rank=company_data.get("rank", 0),
                                        domain=company_data.get("domain", ""),
                                        short_summary=company_data.get("short_summary", ""),
                                        relation=company_data.get("relation", "")
                                    )
                                    companies.append(company)
                            
                            logger.info(f"Successfully parsed {len(companies)} company domains")
                        else:
                            logger.warning(f"Unexpected response format: {parsed_json}")
                            
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        logger.error(f"Failed to parse company domain response: {str(e)}")
                        logger.error(f"Raw content: {content}")
                        companies = []
                    
                    processing_time = int((time.time() - start_time) * 1000)
                    
                    # Create response object
                    domain_response = CompanyDomainAnalysisResponse(
                        success=True,
                        companies=companies,
                        processing_time_ms=processing_time
                    )
                    
                    # Check if we have zero results and should retry
                    if self._has_zero_domain_results(domain_response) and attempt < max_retries:
                        logger.warning(f"Domain analysis returned zero results (attempt {attempt + 1}/{max_retries + 1}). Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        # Either we have results or we've exhausted retries
                        if self._has_zero_domain_results(domain_response):
                            logger.warning(f"Domain analysis still has zero results after {max_retries + 1} attempts")
                        else:
                            logger.info(f"Domain analysis completed successfully with {len(companies)} companies found")
                        
                        logger.info(f"Company domain analysis completed in {processing_time}ms")
                        logger.info(f"Found {len(companies)} company domains")
                        
                        return domain_response
                
            except Exception as e:
                processing_time = int((time.time() - start_time) * 1000)
                logger.error(f"Domain analysis failed (attempt {attempt + 1}): {str(e)}")
                
                # If this is not the last attempt, wait before retrying
                if attempt < max_retries:
                    logger.info(f"Retrying domain analysis in {retry_delay} seconds due to error...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed
                    return CompanyDomainAnalysisResponse(
                        success=False,
                        error=str(e),
                        processing_time_ms=processing_time
                    )
        
        # This should never be reached, but just in case
        processing_time = int((time.time() - start_time) * 1000)
        return CompanyDomainAnalysisResponse(
            success=False,
            error="Unexpected error in retry loop",
            processing_time_ms=processing_time
        )
