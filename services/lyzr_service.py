"""
UBO Trace Engine Backend - Lyzr AI Agent Service
"""

import httpx
import time
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from utils.settings import settings
from models.schemas import LyzrAgentRequest, LyzrAgentResponse, TraceStage, TraceStageResult

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
    
    async def call_agent(self, stage: TraceStage, entity: str, ubo_name: str, location: str, domain: Optional[str] = None) -> LyzrAgentResponse:
        """Call the appropriate Lyzr AI agent for the given stage"""
        
        start_time = time.time()
        
        try:
            config = self.agent_configs.get(stage)
            if not config:
                raise ValueError(f"Unknown stage: {stage}")
            
            # Build simple message with only required parameters
            message = f"Entity: {entity}, UBO Name: {ubo_name}, Location: {location}"
            if domain:
                message += f", Domain: {domain}"
            
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
    
    def parse_results(self, content: str, ubo_name: str) -> Dict[str, Any]:
        """Parse the AI response and extract structured data"""
        
        urls = self._extract_urls(content)
        direct, indirect = [], []
        name_variants = self._partial_name_patterns(ubo_name)
        
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
            if self._find_mentions(sentence, name_variants):
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
    
    def _partial_name_patterns(self, full_name: str) -> List[str]:
        """Return regex variants for partial match detection"""
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
