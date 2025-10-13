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
    
    def _build_prompt(self, stage: TraceStage, entity: str, ubo_name: str, location: str, domain: Optional[str] = None) -> str:
        """Build the appropriate prompt for each stage based on the notebook logic"""
        
        if not domain or domain.strip().lower() in ["", "unknown"]:
            domain = self._infer_domain_from_entity(entity)
        
        if stage == TraceStage.STAGE_1A:
            return f"""
You are an independent corporate-ownership investigator preparing a verifiable
evidence report on potential control links between "{ubo_name}" and "{entity}"
operating in {location}.  Domain context: {domain}.

OBJECTIVE:
Return *only verified factual information* backed by official or primary sources.

RESEARCH SCOPE:
•  Company registry entries (e.g., {location} registrar, Companies House, OpenCorporates)
•  Beneficial-ownership filings, shareholder lists, annual returns, PDFs, or government data
•  Major business-wire releases (Bloomberg, Reuters, PR Newswire) that cite ownership facts
•  Audit or financial-statement disclosures that explicitly mention {ubo_name} and {entity}

MANDATORY OUTPUT:
For each finding, provide:
  •  Exact Fact (e.g. "Liu Jianfeng holds 30 % of shares in Louis Dreyfus Company Metals MEA DMCC")
  •  Evidence Type (one of [Registry | Filing | News | Disclosure])
  •  Date (if available)
  •  Verified URL (official domain or primary source only)

Rules:
– No speculation or inference wording ("likely", "appears", etc.)
– If nothing is found, explicitly state **"No verified connection located in official records."**
"""
        
        elif stage == TraceStage.STAGE_1B:
            return f"""
Conduct a *time-scoped factual search (Jan 2023 – present)* for direct relationships between
"{ubo_name}" and "{entity}" in {location}.  Domain context: {domain}.

Include:
•  Any new or amended ownership filings, director appointments, or resignations
•  Updates in government or financial-regulator databases (2023–2025)
•  Corporate announcements confirming changes in control or shareholding

STRICT REQUIREMENTS:
Every statement must have → (Date | Fact | Source URL).
Prefer registry or regulator links > official press releases > news aggregators.
Ignore speculation, commentary, or analyst opinion.
Return *only verified evidence* within the past two years.
"""
        
        elif stage == TraceStage.STAGE_2A:
            return f"""
Investigate *indirect or layered ownership structures* linking "{ubo_name}" to "{entity}"
({domain}) registered or operating in {location}.

TRACE ELEMENTS:
•  Parent / subsidiary / holding relationships
•  Funds, SPVs, nominee shareholders, or trusts connected to either party
•  Entities sharing registered address, directors, or auditors
•  Partial-name or abbreviated-name occurrences (e.g., initials, middle-name variants)
•  Cross-border vehicles used for control or investment

MANDATORY FORMAT:
(1) Fact — Relationship type — Jurisdiction — Verified URL
(2) If none found, output "No verified indirect relationship detected."

SOURCE QUALITY ORDER → Registry > Court / SEC / FCA filing > Audited report > Major press.
No AI-inferred reasoning; every item must include at least one URL.
"""
        
        elif stage == TraceStage.STAGE_2B:
            return f"""
Perform a *time-filtered indirect-connection review (Jan 2023 – present)* between
"{ubo_name}" and "{entity}" in {location}.  Domain context: {domain}.

Look for:
•  Acquisitions, restructurings, or control transfers involving related entities
•  Fund-ownership changes, trust amendments, or partnership filings (2023-2025)
•  Shared executives or signatories appearing across filings
•  Corporate-registry updates citing {ubo_name} or a name variant

OUTPUT FORMAT (chronological):
Date — Evidence Type — Verified Fact — Source URL

Each fact must be verifiable from the URL.
Exclude rumors, unverified blog posts, or secondary summaries.
If no data exists, state "None found in official records (2023-2025)."
"""
        
        return ""
    
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
            
            prompt = self._build_prompt(stage, entity, ubo_name, location, domain)
            
            request_data = LyzrAgentRequest(
                user_id=self.user_id,
                agent_id=config["agent_id"],
                session_id=config["session_id"],
                message=prompt
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
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                processing_time = int((time.time() - start_time) * 1000)
                
                logger.info(f"Lyzr agent {stage} completed in {processing_time}ms")
                
                return LyzrAgentResponse(
                    success=True,
                    content=content,
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
