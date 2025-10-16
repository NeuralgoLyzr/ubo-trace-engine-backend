"""
SearchAPI Google Service for UBO Trace Engine
Provides domain search capabilities using SearchAPI with company_name, ubo_name, and location
"""

import httpx
import time
import logging
import json
from typing import Dict, List, Optional, Any
from utils.settings import get_settings

logger = logging.getLogger(__name__)

class SearchAPIService:
    """Service for interacting with SearchAPI Google service for domain search"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.searchapi_api_key
        self.base_url = "https://www.searchapi.io/api/v1/search"
        self.timeout = 30.0
        
        if not self.api_key:
            logger.warning("SearchAPI API key not found - domain search will be disabled")
            self.api_key = None
    
    async def search_domains(self, company_name: str, ubo_name: str, location: str) -> Dict[str, Any]:
        """Search for domains using all three parameters: company_name, ubo_name, location"""
        
        if not self.api_key:
            return {
                "success": False,
                "error": "SearchAPI API key not configured",
                "domains": [],
                "total_results": 0
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build comprehensive search query with all three parameters
            query = f"{company_name} {ubo_name} official website domain"
            
            # Get country code and SearchAPI-compatible location
            country_code = self._get_country_code(location)
            searchapi_location = self._get_searchapi_location(location)
            
            params = {
                "engine": "google",
                "q": query,
                "location": searchapi_location,
                "gl": country_code,
                "hl": "en",
                "num": 20
            }
            
            logger.info(f"SearchAPI domain search: {company_name} - {ubo_name} - {location}")
            logger.info(f"Search query: {query}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract only the required fields from organic_results
                domains = self._extract_domain_results(result)
                
                logger.info(f"SearchAPI domain search completed: {len(domains)} domains found")
                
                return {
                    "success": True,
                    "domains": domains,
                    "total_results": len(domains),
                    "search_query": query,
                    "search_params": {
                        "company_name": company_name,
                        "ubo_name": ubo_name,
                        "location": location,
                        "country_code": country_code
                    }
                }
                
        except Exception as e:
            logger.error(f"SearchAPI domain search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "domains": [],
                "total_results": 0
            }
    
    def _extract_domain_results(self, search_results: Dict) -> List[Dict[str, Any]]:
        """Extract only position, source, domain, and snippet from organic_results, avoiding duplicates"""
        
        domains = []
        seen_domains = set()  # Track unique domains to avoid duplicates
        organic_results = search_results.get("organic_results", [])
        
        for result in organic_results:
            # Extract only the required fields
            domain_info = {
                "position": result.get("position"),
                "source": result.get("source"),
                "domain": result.get("domain"),
                "snippet": result.get("snippet")
            }
            
            # Only add if we have the essential fields and haven't seen this domain before
            if domain_info["domain"] and domain_info["snippet"]:
                domain_name = domain_info["domain"].lower()  # Normalize domain name for comparison
                
                if domain_name not in seen_domains:
                    seen_domains.add(domain_name)
                    domains.append(domain_info)
                    logger.debug(f"Added unique domain: {domain_info['domain']} (position: {domain_info['position']})")
                else:
                    logger.debug(f"Skipped duplicate domain: {domain_info['domain']} (position: {domain_info['position']})")
        
        logger.info(f"Extracted {len(domains)} unique domains from {len(organic_results)} organic results")
        return domains
    
    def _get_country_code(self, location: str) -> str:
        """Get country code from location string"""
        location_mapping = {
            "uae": "ae",
            "united arab emirates": "ae",
            "isle of man": "im",
            "united kingdom": "gb",
            "uk": "gb",
            "usa": "us",
            "united states": "us",
            "india": "in",
            "singapore": "sg",
            "hong kong": "hk",
            "switzerland": "ch",
            "netherlands": "nl",
            "france": "fr",
            "germany": "de",
            "china": "cn",
            "japan": "jp",
            "australia": "au",
            "canada": "ca",
            "brazil": "br",
            "argentina": "ar"
        }
        
        location_lower = location.lower()
        for key, code in location_mapping.items():
            if key in location_lower:
                return code
        
        return "us"  # Default to US
    
    def _get_searchapi_location(self, location: str) -> str:
        """Get SearchAPI-compatible location string"""
        location_mapping = {
            "uae": "United Arab Emirates",
            "united arab emirates": "United Arab Emirates",
            "isle of man": "Isle of Man",
            "united kingdom": "United Kingdom",
            "uk": "United Kingdom",
            "usa": "United States",
            "united states": "United States",
            "india": "India",
            "singapore": "Singapore",
            "hong kong": "Hong Kong",
            "switzerland": "Switzerland",
            "netherlands": "Netherlands",
            "france": "France",
            "germany": "Germany",
            "china": "China",
            "japan": "Japan",
            "australia": "Australia",
            "canada": "Canada",
            "brazil": "Brazil",
            "argentina": "Argentina"
        }
        
        location_lower = location.lower()
        for key, full_name in location_mapping.items():
            if key in location_lower:
                return full_name
        
        return "United States"  # Default to United States
    
    async def analyze_domains_with_expert(self, company_name: str, ubo_name: str, location: str, 
                                       lyzr_domains: List[Dict], google_serp_domains: List[Dict]) -> Dict[str, Any]:
        """Analyze domain search results using Expert Lyzr AI agent for confidence scores and rankings"""
        
        # Check if Expert domain analysis is configured
        if not self.settings.agent_expert_domain or not self.settings.session_expert_domain:
            logger.warning("Expert domain analysis not configured - skipping analysis")
            return {
                "success": False,
                "error": "Expert domain analysis not configured",
                "expert_analysis": {},
                "raw_response": "",
                "processing_time_ms": 0
            }
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.settings.lyzr_api_key
            }
            
            # Build message for Expert agent
            message = f"""company_name: {company_name} , UBO_name: {ubo_name} , location: {location}

lyzr_agent_domains:{json.dumps(lyzr_domains, indent=2)}

google_serp_domain:{json.dumps(google_serp_domains, indent=2)}"""
            
            request_data = {
                "user_id": self.settings.lyzr_user_id,
                "agent_id": self.settings.agent_expert_domain,
                "session_id": self.settings.session_expert_domain,
                "message": message
            }
            
            logger.info(f"Calling Expert domain analysis agent for: {company_name}")
            logger.info(f"Analyzing {len(lyzr_domains)} Lyzr domains and {len(google_serp_domains)} Google SERP domains")
            
            # Log detailed domain data
            logger.info("=== LYZR DOMAINS DATA ===")
            logger.info(f"Lyzr domains count: {len(lyzr_domains)}")
            for i, domain in enumerate(lyzr_domains):
                logger.info(f"Lyzr domain {i+1}: {domain}")
            
            logger.info("=== GOOGLE SERP DOMAINS DATA ===")
            logger.info(f"Google SERP domains count: {len(google_serp_domains)}")
            for i, domain in enumerate(google_serp_domains):
                logger.info(f"Google SERP domain {i+1}: {domain}")
            
            logger.info("=== EXPERT AGENT MESSAGE ===")
            logger.info(f"Message being sent to Expert agent: {message}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.settings.lyzr_api_url,
                    headers=headers,
                    json=request_data
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract content from response
                content = result.get("response", "")
                if not content:
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    content = result.get("content", "")
                
                # Parse Expert analysis results
                expert_analysis = self._parse_expert_analysis(content)
                
                logger.info(f"Expert domain analysis completed")
                logger.info(f"Expert confidence score: {expert_analysis.get('overall_confidence', 0)}%")
                
                return {
                    "success": True,
                    "expert_analysis": expert_analysis,
                    "raw_response": content,
                    "processing_time_ms": int(time.time() * 1000)
                }
                
        except Exception as e:
            logger.error(f"Expert domain analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "expert_analysis": {},
                "raw_response": "",
                "processing_time_ms": 0
            }
    
    def _parse_expert_analysis(self, content: str) -> Dict[str, Any]:
        """Parse Expert agent response to extract confidence scores and rankings"""
        
        expert_analysis = {
            "overall_confidence": 0,
            "domain_rankings": [],
            "confidence_scores": {},
            "analysis_summary": "",
            "recommendations": [],
            "formatted_results": []  # New field for API endpoint format
        }
        
        try:
            # Try to parse JSON response
            parsed_json = json.loads(content)
            
            if isinstance(parsed_json, dict):
                # Extract overall confidence
                expert_analysis["overall_confidence"] = parsed_json.get("overall_confidence", 0)
                
                # Extract domain rankings - check both "domain_rankings" and "results" fields
                domain_rankings = parsed_json.get("domain_rankings", [])
                if not domain_rankings:
                    domain_rankings = parsed_json.get("results", [])
                expert_analysis["domain_rankings"] = domain_rankings
                
                # Extract confidence scores
                confidence_scores = parsed_json.get("confidence_scores", {})
                expert_analysis["confidence_scores"] = confidence_scores
                
                # Extract analysis summary
                expert_analysis["analysis_summary"] = parsed_json.get("analysis_summary", "")
                
                # Extract recommendations
                recommendations = parsed_json.get("recommendations", [])
                expert_analysis["recommendations"] = recommendations
                
                # Format results for API endpoint
                expert_analysis["formatted_results"] = self._format_expert_results_for_api(domain_rankings)
                
                logger.info(f"Successfully parsed Expert analysis: {len(domain_rankings)} domain rankings")
                
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Could not parse Expert JSON response: {str(e)}")
            
            # Fallback: try to extract information from text
            expert_analysis["analysis_summary"] = content[:500] if content else ""
            
            # Try to extract confidence score from text
            import re
            confidence_match = re.search(r'confidence[:\s]*(\d+)%?', content.lower())
            if confidence_match:
                expert_analysis["overall_confidence"] = int(confidence_match.group(1))
        
        return expert_analysis
    
    def _format_expert_results_for_api(self, domain_rankings: List[Dict]) -> List[Dict[str, Any]]:
        """Format Expert analysis results for API endpoint response"""
        
        formatted_results = []
        
        for ranking in domain_rankings:
            formatted_result = {
                "rank": ranking.get("rank", 0),
                "domain": ranking.get("domain", ""),
                "confidence_score": ranking.get("confidence_score", ranking.get("confidence", 0)),
                "reasoning": ranking.get("reasoning", ranking.get("summary", ""))
            }
            formatted_results.append(formatted_result)
        
        # Sort by rank to ensure proper ordering
        formatted_results.sort(key=lambda x: x.get("rank", 0))
        
        return formatted_results
    
    async def analyze_domains_for_api(self, company_name: str, ubo_name: str, location: str) -> Dict[str, Any]:
        """Analyze domains and return formatted results for API endpoint"""
        
        try:
            # Get Lyzr domain analysis results
            lyzr_domains = []
            try:
                from services.lyzr_service import LyzrAgentService
                lyzr_service = LyzrAgentService()
                if hasattr(lyzr_service, 'analyze_company_domains'):
                    lyzr_domain_response = await lyzr_service.analyze_company_domains(
                        company_name, ubo_name, location
                    )
                    if lyzr_domain_response.success:
                        lyzr_domains = [domain.dict() for domain in lyzr_domain_response.companies]
            except Exception as e:
                logger.warning(f"Lyzr domain analysis failed: {str(e)}")
            
            # Get Google SERP domains from SearchAPI
            google_serp_domains = []
            if self.api_key:
                try:
                    domain_search = await self.search_domains(company_name, ubo_name, location)
                    if domain_search.get("success"):
                        google_serp_domains = domain_search.get("domains", [])
                except Exception as e:
                    logger.warning(f"SearchAPI domain search failed: {str(e)}")
            
            # Call Expert agent for analysis
            if lyzr_domains or google_serp_domains:
                expert_analysis = await self.analyze_domains_with_expert(
                    company_name, ubo_name, location, lyzr_domains, google_serp_domains
                )
                
                if expert_analysis.get("success"):
                    expert_data = expert_analysis.get("expert_analysis", {})
                    formatted_results = expert_data.get("formatted_results", [])
                    
                    return {
                        "success": True,
                        "results": formatted_results,
                        "total_domains_analyzed": len(lyzr_domains) + len(google_serp_domains),
                        "overall_confidence": expert_data.get("overall_confidence", 0),
                        "analysis_summary": expert_data.get("analysis_summary", "")
                    }
                else:
                    return {
                        "success": False,
                        "error": expert_analysis.get("error", "Expert analysis failed"),
                        "results": [],
                        "total_domains_analyzed": 0,
                        "overall_confidence": 0,
                        "analysis_summary": ""
                    }
            else:
                return {
                    "success": False,
                    "error": "No domain data available for analysis",
                    "results": [],
                    "total_domains_analyzed": 0,
                    "overall_confidence": 0,
                    "analysis_summary": ""
                }
                
        except Exception as e:
            logger.error(f"Domain analysis for API failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total_domains_analyzed": 0,
                "overall_confidence": 0,
                "analysis_summary": ""
            }
    
    async def search_domain_ownership(self, company_name: str, ubo_name: str, location: str, domain: str) -> Dict[str, Any]:
        """Search for ownership information on a specific domain"""
        
        if not self.api_key:
            return {
                "success": False,
                "error": "SearchAPI API key not configured",
                "ownership_results": [],
                "total_results": 0
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build domain-specific ownership search query
            query = f"site:{domain} {company_name} {ubo_name} owner director"
            
            country_code = self._get_country_code(location)
            searchapi_location = self._get_searchapi_location(location)
            
            params = {
                "engine": "google",
                "q": query,
                "location": searchapi_location,
                "gl": country_code,
                "hl": "en",
                "num": 10
            }
            
            logger.info(f"SearchAPI domain ownership search: {domain} - {company_name} - {ubo_name}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract ownership information
                ownership_results = self._extract_domain_results(result)
                
                return {
                    "success": True,
                    "domain": domain,
                    "ownership_results": ownership_results,
                    "total_results": len(ownership_results),
                    "search_query": query
                }
                
        except Exception as e:
            logger.error(f"SearchAPI domain ownership search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "domain": domain,
                "ownership_results": [],
                "total_results": 0
            }
    
    async def search_related_domains(self, company_name: str, ubo_name: str, location: str) -> Dict[str, Any]:
        """Search for related domains (subsidiaries, parent companies, etc.)"""
        
        if not self.api_key:
            return {
                "success": False,
                "error": "SearchAPI API key not configured",
                "related_domains": [],
                "total_results": 0
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build related domains search query
            query = f"{company_name} {ubo_name} {location} subsidiary parent company website domain"
            
            country_code = self._get_country_code(location)
            searchapi_location = self._get_searchapi_location(location)
            
            params = {
                "engine": "google",
                "q": query,
                "location": searchapi_location,
                "gl": country_code,
                "hl": "en",
                "num": 15
            }
            
            logger.info(f"SearchAPI related domains search: {company_name} - {ubo_name} - {location}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract related domains
                related_domains = self._extract_domain_results(result)
                
                return {
                    "success": True,
                    "related_domains": related_domains,
                    "total_results": len(related_domains),
                    "search_query": query
                }
                
        except Exception as e:
            logger.error(f"SearchAPI related domains search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "related_domains": [],
                "total_results": 0
            }
