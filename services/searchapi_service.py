"""
SearchAPI Google Service for UBO Trace Engine
Provides domain search capabilities using SearchAPI with company_name, ubo_name, and location
"""

import httpx
import time
import logging
import json
import asyncio
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
    
    async def search_domains(self, company_name: str, ubo_name: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
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
            
            # Build comprehensive search query with available parameters
            query_parts = [company_name]
            if ubo_name:
                query_parts.append(ubo_name)
            query_parts.append("official website domain")
            query = " ".join(query_parts)
            
            # Get country code and SearchAPI-compatible location
            country_code = self._get_country_code(location) if location else "us"
            searchapi_location = self._get_searchapi_location(location) if location else "United States"
            
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
    
    def _get_country_code(self, location: Optional[str]) -> str:
        """Get country code (ISO 3166-1 alpha-2) from location string"""
        if not location:
            return "us"  # Default to US
        
        location_mapping = {
            # United Arab Emirates
            "uae": "ae",
            "united arab emirates": "ae",
            
            # United Kingdom
            "uk": "gb",
            "united kingdom": "gb",
            "gb": "gb",
            "great britain": "gb",
            
            # United States
            "usa": "us",
            "us": "us",
            "united states": "us",
            "united states of america": "us",
            
            # Isle of Man
            "isle of man": "im",
            "iom": "im",
            
            # Other countries
            "india": "in",
            "in": "in",
            
            "singapore": "sg",
            "sg": "sg",
            
            "hong kong": "hk",
            "hk": "hk",
            
            "switzerland": "ch",
            "ch": "ch",
            
            "netherlands": "nl",
            "nl": "nl",
            "holland": "nl",
            
            "france": "fr",
            "fr": "fr",
            
            "germany": "de",
            "de": "de",
            
            "china": "cn",
            "cn": "cn",
            "prc": "cn",
            "people's republic of china": "cn",
            
            "japan": "jp",
            "jp": "jp",
            
            "australia": "au",
            "au": "au",
            
            "canada": "ca",
            "ca": "ca",
            
            "brazil": "br",
            "br": "br",
            
            "argentina": "ar",
            "ar": "ar",
            
            # Additional countries
            "south korea": "kr",
            "kr": "kr",
            "korea": "kr",
            
            "south africa": "za",
            "za": "za",
            
            "mexico": "mx",
            "mx": "mx",
            
            "italy": "it",
            "it": "it",
            
            "spain": "es",
            "es": "es",
            
            "russia": "ru",
            "ru": "ru",
            "russian federation": "ru",
            
            "turkey": "tr",
            "tr": "tr",
            
            "saudi arabia": "sa",
            "sa": "sa",
            "ksa": "sa",
            
            "qatar": "qa",
            "qa": "qa",
            
            "kuwait": "kw",
            "kw": "kw",
            
            "bahrain": "bh",
            "bh": "bh",
            
            "oman": "om",
            "om": "om",
            
            "jordan": "jo",
            "jo": "jo",
            
            "lebanon": "lb",
            "lb": "lb",
            
            "egypt": "eg",
            "eg": "eg",
            
            "israel": "il",
            "il": "il",
            
            "indonesia": "id",
            "id": "id",
            
            "malaysia": "my",
            "my": "my",
            
            "thailand": "th",
            "th": "th",
            
            "philippines": "ph",
            "ph": "ph",
            
            "vietnam": "vn",
            "vn": "vn",
            
            "new zealand": "nz",
            "nz": "nz",
            
            "poland": "pl",
            "pl": "pl",
            
            "sweden": "se",
            "se": "se",
            
            "norway": "no",
            "no": "no",
            
            "denmark": "dk",
            "dk": "dk",
            
            "finland": "fi",
            "fi": "fi",
            
            "belgium": "be",
            "be": "be",
            
            "austria": "at",
            "at": "at",
            
            "portugal": "pt",
            "pt": "pt",
            
            "greece": "gr",
            "gr": "gr",
            
            "ireland": "ie",
            "ie": "ie",
        }
        
        location_lower = location.lower().strip()
        
        # Check for exact match first
        if location_lower in location_mapping:
            return location_mapping[location_lower]
        
        # Check for partial match (key in location string)
        for key, code in location_mapping.items():
            if key in location_lower:
                return code
        
        return "us"  # Default to US
    
    def _get_searchapi_location(self, location: Optional[str]) -> str:
        """Get SearchAPI-compatible location string, mapping short forms to full country names"""
        if not location:
            return "United States"  # Default
        
        location_mapping = {
            # United Arab Emirates
            "uae": "United Arab Emirates",
            "united arab emirates": "United Arab Emirates",
            
            # United Kingdom
            "uk": "United Kingdom",
            "united kingdom": "United Kingdom",
            "gb": "United Kingdom",
            "great britain": "United Kingdom",
            
            # United States
            "usa": "United States",
            "us": "United States",
            "united states": "United States",
            "united states of america": "United States",
            
            # Other common countries with short forms
            "isle of man": "Isle of Man",
            "iom": "Isle of Man",
            
            "india": "India",
            "in": "India",
            
            "singapore": "Singapore",
            "sg": "Singapore",
            
            "hong kong": "Hong Kong",
            "hk": "Hong Kong",
            
            "switzerland": "Switzerland",
            "ch": "Switzerland",
            
            "netherlands": "Netherlands",
            "nl": "Netherlands",
            "holland": "Netherlands",
            
            "france": "France",
            "fr": "France",
            
            "germany": "Germany",
            "de": "Germany",
            
            "china": "China",
            "cn": "China",
            "prc": "China",
            "people's republic of china": "China",
            
            "japan": "Japan",
            "jp": "Japan",
            
            "australia": "Australia",
            "au": "Australia",
            
            "canada": "Canada",
            "ca": "Canada",
            
            "brazil": "Brazil",
            "br": "Brazil",
            
            "argentina": "Argentina",
            "ar": "Argentina",
            
            # Additional common countries
            "south korea": "South Korea",
            "kr": "South Korea",
            "korea": "South Korea",
            
            "south africa": "South Africa",
            "za": "South Africa",
            
            "mexico": "Mexico",
            "mx": "Mexico",
            
            "italy": "Italy",
            "it": "Italy",
            
            "spain": "Spain",
            "es": "Spain",
            
            "russia": "Russia",
            "ru": "Russia",
            "russian federation": "Russia",
            
            "turkey": "Turkey",
            "tr": "Turkey",
            
            "saudi arabia": "Saudi Arabia",
            "sa": "Saudi Arabia",
            "ksa": "Saudi Arabia",
            
            "qatar": "Qatar",
            "qa": "Qatar",
            
            "kuwait": "Kuwait",
            "kw": "Kuwait",
            
            "bahrain": "Bahrain",
            "bh": "Bahrain",
            
            "oman": "Oman",
            "om": "Oman",
            
            "jordan": "Jordan",
            "jo": "Jordan",
            
            "lebanon": "Lebanon",
            "lb": "Lebanon",
            
            "egypt": "Egypt",
            "eg": "Egypt",
            
            "israel": "Israel",
            "il": "Israel",
            
            "indonesia": "Indonesia",
            "id": "Indonesia",
            
            "malaysia": "Malaysia",
            "my": "Malaysia",
            
            "thailand": "Thailand",
            "th": "Thailand",
            
            "philippines": "Philippines",
            "ph": "Philippines",
            
            "vietnam": "Vietnam",
            "vn": "Vietnam",
            
            "new zealand": "New Zealand",
            "nz": "New Zealand",
            
            "poland": "Poland",
            "pl": "Poland",
            
            "sweden": "Sweden",
            "se": "Sweden",
            
            "norway": "Norway",
            "no": "Norway",
            
            "denmark": "Denmark",
            "dk": "Denmark",
            
            "finland": "Finland",
            "fi": "Finland",
            
            "belgium": "Belgium",
            "be": "Belgium",
            
            "austria": "Austria",
            "at": "Austria",
            
            "portugal": "Portugal",
            "pt": "Portugal",
            
            "greece": "Greece",
            "gr": "Greece",
            
            "ireland": "Ireland",
            "ie": "Ireland",
        }
        
        location_lower = location.lower().strip()
        
        # Check for exact match first
        if location_lower in location_mapping:
            return location_mapping[location_lower]
        
        # Check for partial match (key in location string)
        for key, value in location_mapping.items():
            if key in location_lower:
                return value
        
        # If no mapping found, try to format the location nicely
        # Capitalize first letter of each word
        return location.title()
    
    async def analyze_domains_with_expert(self, company_name: str, ubo_name: Optional[str] = None, location: Optional[str] = None, 
                                       lyzr_domains: List[Dict] = None, google_serp_domains: List[Dict] = None) -> Dict[str, Any]:
        """Analyze domain search results using Expert Lyzr AI agent for confidence scores and rankings"""
        
        if lyzr_domains is None:
            lyzr_domains = []
        if google_serp_domains is None:
            google_serp_domains = []
        
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
            
            # Build message for Expert agent with available parameters
            message_parts = [f"company_name: {company_name}"]
            if ubo_name:
                message_parts.append(f"UBO_name: {ubo_name}")
            if location:
                message_parts.append(f"location: {location}")
            message = " , ".join(message_parts) + f"\n\nlyzr_agent_domains:{json.dumps(lyzr_domains, indent=2)}\n\ngoogle_serp_domain:{json.dumps(google_serp_domains, indent=2)}"
            
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
    
    async def analyze_domains_for_api(self, company_name: str, ubo_name: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """Analyze domains and return formatted results for API endpoint"""
        
        try:
            # Get Lyzr domain analysis results (only if ubo_name is provided)
            lyzr_domains = []
            if ubo_name:
                try:
                    from services.lyzr_service import LyzrAgentService
                    lyzr_service = LyzrAgentService()
                    if hasattr(lyzr_service, 'analyze_company_domains'):
                        # Note: analyze_company_domains requires address, but we'll handle it gracefully
                        # For now, we'll skip if address is not available
                        pass
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
    
    async def search_domain_ownership(self, company_name: str, ubo_name: Optional[str] = None, location: Optional[str] = None, domain: str = "") -> Dict[str, Any]:
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
            query_parts = [f"site:{domain}", company_name]
            if ubo_name:
                query_parts.append(ubo_name)
            query_parts.extend(["owner", "director"])
            query = " ".join(query_parts)
            
            country_code = self._get_country_code(location) if location else "us"
            searchapi_location = self._get_searchapi_location(location) if location else "United States"
            
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
    
    async def search_related_domains(self, company_name: str, ubo_name: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
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
            query_parts = [company_name]
            if ubo_name:
                query_parts.append(ubo_name)
            if location:
                query_parts.append(location)
            query_parts.extend(["subsidiary", "parent", "company", "website", "domain"])
            query = " ".join(query_parts)
            
            country_code = self._get_country_code(location) if location else "us"
            searchapi_location = self._get_searchapi_location(location) if location else "United States"
            
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
    
    async def search_ubo_ownership(self, company_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Search for UBO ownership information using Google Search API"""
        
        if not self.api_key:
            return {
                "success": False,
                "error": "SearchAPI API key not configured",
                "organic_results": [],
                "related_questions": [],
                "lyzr_analysis": None
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build UBO ownership search query
            query = f'{company_name} "ultimate beneficial owner" OR "shareholder" OR "ownership" "stake holding"'
            
            # Get country code and SearchAPI-compatible location
            country_code = "us"  # Default
            searchapi_location = "United States"  # Default
            
            if location:
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
            
            logger.info(f"SearchAPI UBO ownership search: {company_name} - {location}")
            logger.info(f"Search query: {query}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    error_msg = "SearchAPI rate limit exceeded. Please try again later."
                    logger.warning(f"SearchAPI rate limit exceeded for UBO ownership search")
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "organic_results": [],
                        "related_questions": [],
                        "lyzr_analysis": None
                    }
                
                response.raise_for_status()
                
                result = response.json()
                
                # Extract only organic_results and related_questions
                organic_results = result.get("organic_results", [])
                related_questions = result.get("related_questions", [])
                
                logger.info(f"SearchAPI UBO ownership search completed: {len(organic_results)} organic results, {len(related_questions)} related questions")
                
                # Send to Lyzr agent for analysis
                lyzr_analysis = await self._analyze_ubo_ownership_with_lyzr(
                    company_name, organic_results, related_questions
                )
                
                return {
                    "success": True,
                    "organic_results": organic_results,
                    "related_questions": related_questions,
                    "lyzr_analysis": lyzr_analysis,
                    "search_query": query,
                    "total_organic_results": len(organic_results),
                    "total_related_questions": len(related_questions)
                }
                
        except Exception as e:
            logger.error(f"SearchAPI UBO ownership search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "organic_results": [],
                "related_questions": [],
                "lyzr_analysis": None
            }
    
    async def _analyze_ubo_ownership_with_lyzr(self, company_name: str, 
                                               organic_results: List[Dict], 
                                               related_questions: List[Dict]) -> Dict[str, Any]:
        """Analyze UBO ownership search results using Lyzr agent with retry logic"""
        
        # Check if Lyzr agent is configured
        if not self.settings.agent_ubo_ownership_analysis or not self.settings.session_ubo_ownership_analysis:
            logger.warning("UBO ownership analysis agent not configured - skipping analysis")
            return {
                "success": False,
                "error": "UBO ownership analysis agent not configured",
                "analysis": None,
                "raw_response": ""
            }
        
        max_retries = 3
        retry_delay = 2.0  # Start with 2 seconds, exponential backoff
        
        for attempt in range(max_retries + 1):
            try:
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": self.settings.lyzr_api_key
                }
                
                # Build message for Lyzr agent
                message = f"""company_name: {company_name}

organic_results:
{json.dumps(organic_results, indent=2)}

related_questions:
{json.dumps(related_questions, indent=2)}"""
                
                request_data = {
                    "user_id": self.settings.lyzr_user_id,
                    "agent_id": self.settings.agent_ubo_ownership_analysis,
                    "session_id": self.settings.session_ubo_ownership_analysis,
                    "message": message
                }
                
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{max_retries} for Lyzr UBO ownership analysis: {company_name}")
                else:
                    logger.info(f"Calling Lyzr UBO ownership analysis agent for: {company_name}")
                
                logger.info(f"Analyzing {len(organic_results)} organic results and {len(related_questions)} related questions")
                
                start_time = time.time()
                # Increase timeout for Lyzr agent calls (60 seconds)
                timeout = httpx.Timeout(60.0, connect=10.0)
                
                async with httpx.AsyncClient(timeout=timeout) as client:
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
                    
                    # Check if we got a valid response
                    if not content or content.strip() == "":
                        if attempt < max_retries:
                            logger.warning(f"Lyzr UBO ownership analysis returned empty response (attempt {attempt + 1}/{max_retries + 1}). Retrying in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            logger.warning(f"Lyzr UBO ownership analysis returned empty response after {max_retries + 1} attempts")
                            return {
                                "success": False,
                                "error": "Lyzr agent returned empty response after retries",
                                "analysis": None,
                                "raw_response": ""
                            }
                    
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    logger.info(f"Lyzr UBO ownership analysis completed in {processing_time_ms}ms (attempt {attempt + 1})")
                    
                    return {
                        "success": True,
                        "analysis": content,
                        "raw_response": content,
                        "processing_time_ms": processing_time_ms
                    }
                    
            except httpx.TimeoutException as e:
                error_msg = "Lyzr agent request timed out. The service may be experiencing high load."
                logger.error(f"Lyzr UBO ownership analysis timeout (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                
                # Retry on timeout
                if attempt < max_retries:
                    logger.info(f"Retrying Lyzr UBO ownership analysis in {retry_delay} seconds due to timeout...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    return {
                        "success": False,
                        "error": error_msg,
                        "analysis": None,
                        "raw_response": ""
                    }
            except httpx.ConnectError as e:
                error_msg = "Unable to connect to Lyzr agent. Please check your internet connection."
                logger.error(f"Lyzr UBO ownership analysis connection error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                
                # Retry on connection errors
                if attempt < max_retries:
                    logger.info(f"Retrying Lyzr UBO ownership analysis in {retry_delay} seconds due to connection error...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    return {
                        "success": False,
                        "error": error_msg,
                        "analysis": None,
                        "raw_response": ""
                    }
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP error {e.response.status_code}: {str(e)}"
                logger.error(f"Lyzr UBO ownership analysis failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg}")
                
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    return {
                        "success": False,
                        "error": error_msg,
                        "analysis": None,
                        "raw_response": ""
                    }
                
                # Retry on 5xx errors (server errors) or network errors
                if attempt < max_retries:
                    logger.info(f"Retrying Lyzr UBO ownership analysis in {retry_delay} seconds due to error...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    return {
                        "success": False,
                        "error": error_msg,
                        "analysis": None,
                        "raw_response": ""
                    }
                    
            except Exception as e:
                error_msg = str(e)
                # Check if it's a connection/disconnection error
                if "disconnected" in error_msg.lower() or "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    error_msg = "Lyzr agent connection was interrupted or timed out. Please try again."
                
                logger.error(f"Lyzr UBO ownership analysis failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg}")
                
                # If this is not the last attempt, wait before retrying
                if attempt < max_retries:
                    logger.info(f"Retrying Lyzr UBO ownership analysis in {retry_delay} seconds due to error...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    # Final attempt failed
                    return {
                        "success": False,
                        "error": error_msg,
                        "analysis": None,
                        "raw_response": ""
                    }
        
        # This should never be reached, but just in case
        return {
            "success": False,
            "error": "Lyzr UBO ownership analysis failed after all retries",
            "analysis": None,
            "raw_response": ""
        }