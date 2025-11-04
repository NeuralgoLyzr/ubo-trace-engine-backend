"""
Apollo.io API Service for UBO Trace Engine
Provides data enrichment capabilities using Apollo's database
"""

import httpx
import time
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from utils.settings import get_settings

logger = logging.getLogger(__name__)

class ApolloService:
    """Service for interacting with Apollo.io API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.apollo_api_key
        self.base_url = self.settings.apollo_base_url
        self.timeout = self.settings.apollo_timeout
        
        if not self.api_key:
            raise ValueError("Apollo API key is required")
    
    async def search_people(self, name: str, company_name: Optional[str] = None, 
                          location: Optional[str] = None) -> Dict[str, Any]:
        """Search for people using Apollo's People Search API"""
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key
            }
            
            # Build search query
            search_data = {
                "q": name,
                "page": 1,
                "per_page": 10
            }
            
            if company_name:
                search_data["organization_name"] = company_name
            
            if location:
                search_data["person_locations"] = [location]
            
            logger.info(f"Searching Apollo for person: {name}")
            logger.info(f"Search parameters: {search_data}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/people/search",
                    headers=headers,
                    json=search_data
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Apollo people search completed: {len(result.get('people', []))} results")
                
                # Filter relevant people
                all_people = result.get("people", [])
                relevant_people = self._filter_relevant_people(all_people, name, company_name or "")
                
                # Extract only relevant data
                filtered_people = [self._extract_relevant_person_data(person) for person in relevant_people]
                
                logger.info(f"Filtered to {len(filtered_people)} relevant people")
                
                return {
                    "success": True,
                    "people": filtered_people,
                    "total_results": len(filtered_people),
                    "search_params": search_data
                }
                
        except Exception as e:
            logger.error(f"Apollo people search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "people": [],
                "total_results": 0
            }
    
    async def search_people_by_organization(
        self,
        organization_name: str,
        person_titles: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        locations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search for people by organization using Apollo's People Search API with advanced filters"""
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "Accept": "application/json"
            }
            
            # Build search data matching the exact Apollo API format
            search_data = {
                "api_key": self.api_key,
                "q_organization_names": [organization_name]
            }
            
            # Add optional person titles (default to CEO, CTO, CFO, VP, Director if not provided)
            if person_titles:
                search_data["person_titles"] = person_titles
            else:
                search_data["person_titles"] = ["CEO", "CTO", "CFO", "VP", "Director"]
            
            # Add optional domains
            if domains:
                search_data["domains"] = domains
            
            # Add optional locations (note: API uses "q_organization_locatios" with typo)
            if locations:
                search_data["q_organization_locatios"] = locations
            
            logger.info(f"Searching Apollo for people in organization: {organization_name}")
            logger.info(f"Search parameters: {search_data}")
            
            # Increase timeout for Apollo API calls (60 seconds)
            timeout = httpx.Timeout(60.0, connect=10.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/people/search",
                    headers=headers,
                    json=search_data
                )
                response.raise_for_status()
                
                result = response.json()
                people = result.get("people", [])
                logger.info(f"Apollo people search by organization completed: {len(people)} results")
                
                # Extract relevant data
                filtered_people = [self._extract_relevant_person_data(person) for person in people]
                
                # Send to Lyzr agent for analysis (even if Apollo returned empty results)
                lyzr_analysis = await self._analyze_apollo_people_with_lyzr(
                    organization_name, filtered_people, search_data
                )
                
                return {
                    "success": True,
                    "people": filtered_people,
                    "total_results": len(filtered_people),
                    "lyzr_analysis": lyzr_analysis,
                    "search_params": {
                        "organization_name": organization_name,
                        "person_titles": search_data.get("person_titles"),
                        "domains": domains,
                        "locations": locations
                    },
                    "raw_response": result
                }
                
        except httpx.TimeoutException as e:
            error_msg = "Apollo API request timed out. The service may be experiencing high load. Please try again later."
            logger.error(f"Apollo people search timeout: {str(e)}")
            return {
                "success": False,
                "error": error_msg,
                "people": [],
                "total_results": 0,
                "lyzr_analysis": None
            }
        except httpx.ConnectError as e:
            error_msg = "Unable to connect to Apollo API. The service may be temporarily unavailable. Please try again later."
            logger.error(f"Apollo people search connection error: {str(e)}")
            # Log the actual error for debugging
            logger.debug(f"Connection error details: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": error_msg,
                "people": [],
                "total_results": 0,
                "lyzr_analysis": None
            }
        except httpx.ReadError as e:
            # Handle SSL/read errors
            error_msg = "Apollo API connection was interrupted. Please try again."
            logger.error(f"Apollo people search read error: {str(e)}")
            logger.debug(f"Read error details: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": error_msg,
                "people": [],
                "total_results": 0,
                "lyzr_analysis": None
            }
        except httpx.HTTPStatusError as e:
            error_msg = f"Apollo API returned error: HTTP {e.response.status_code}"
            logger.error(f"Apollo people search HTTP error {e.response.status_code}: {str(e)}")
            return {
                "success": False,
                "error": error_msg,
                "people": [],
                "total_results": 0,
                "lyzr_analysis": None
            }
        except Exception as e:
            error_msg = str(e)
            error_lower = error_msg.lower()
            
            # Check if it's a connection/disconnection/SSL error
            if any(keyword in error_lower for keyword in ["disconnected", "connection", "ssl", "record layer", "certificate", "tls"]):
                error_msg = "Apollo API connection was interrupted. Please try again later."
            elif "timeout" in error_lower:
                error_msg = "Apollo API request timed out. Please try again later."
            
            logger.error(f"Apollo people search by organization failed: {error_msg}")
            logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": error_msg,
                "people": [],
                "total_results": 0,
                "lyzr_analysis": None
            }
    
    async def search_organizations(self, company_name: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Search for organizations using Apollo's Organization Search API"""
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key
            }
            
            # Build search query
            search_data = {
                "q": company_name,
                "page": 1,
                "per_page": 10
            }
            
            if domain:
                search_data["website_url"] = domain
            
            logger.info(f"Searching Apollo for organization: {company_name}")
            logger.info(f"Search parameters: {search_data}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/organizations/search",
                    headers=headers,
                    json=search_data
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Apollo organization search completed: {len(result.get('organizations', []))} results")
                
                # Filter relevant organizations
                all_organizations = result.get("organizations", [])
                relevant_organizations = self._filter_relevant_organizations(all_organizations, company_name, domain)
                
                # Extract only relevant data
                filtered_organizations = [self._extract_relevant_company_data(org) for org in relevant_organizations]
                
                logger.info(f"Filtered to {len(filtered_organizations)} relevant organizations")
                
                return {
                    "success": True,
                    "organizations": filtered_organizations,
                    "total_results": len(filtered_organizations),
                    "search_params": search_data
                }
                
        except Exception as e:
            logger.error(f"Apollo organization search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "organizations": [],
                "total_results": 0
            }
    
    async def enrich_person(self, person_id: str) -> Dict[str, Any]:
        """Enrich person data using Apollo's Person Enrichment API"""
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key
            }
            
            logger.info(f"Enriching Apollo person: {person_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/people/{person_id}",
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Apollo person enrichment completed")
                
                return {
                    "success": True,
                    "person": result.get("person", {}),
                    "organization": result.get("organization", {})
                }
                
        except Exception as e:
            logger.error(f"Apollo person enrichment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "person": {},
                "organization": {}
            }
    
    async def enrich_organization(self, organization_id: str) -> Dict[str, Any]:
        """Enrich organization data using Apollo's Organization Enrichment API"""
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": self.api_key
            }
            
            logger.info(f"Enriching Apollo organization: {organization_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/organizations/{organization_id}",
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Apollo organization enrichment completed")
                
                return {
                    "success": True,
                    "organization": result.get("organization", {}),
                    "people": result.get("people", [])
                }
                
        except Exception as e:
            logger.error(f"Apollo organization enrichment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "organization": {},
                "people": []
            }
    
    async def enrich_ubo_trace_data(self, entity: str, ubo_name: Optional[str] = None, 
                                  location: Optional[str] = None, domain: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive enrichment for UBO trace data"""
        
        logger.info(f"Starting Apollo enrichment for UBO trace: {entity} - {ubo_name}")
        
        enrichment_results = {
            "entity_search": {},
            "ubo_search": {},
            "domain_search": {},
            "enrichment_summary": {
                "entity_found": False,
                "ubo_found": False,
                "domain_verified": False,
                "total_matches": 0
            }
        }
        
        try:
            # Search for the entity/organization
            entity_results = await self.search_organizations(entity, domain)
            enrichment_results["entity_search"] = entity_results
            
            if entity_results["success"] and entity_results["organizations"]:
                enrichment_results["enrichment_summary"]["entity_found"] = True
                enrichment_results["enrichment_summary"]["total_matches"] += len(entity_results["organizations"])
            
            # Search for the UBO/person (only if ubo_name is provided)
            if ubo_name:
                ubo_results = await self.search_people(ubo_name, entity, location)
                enrichment_results["ubo_search"] = ubo_results
                
                if ubo_results["success"] and ubo_results["people"]:
                    enrichment_results["enrichment_summary"]["ubo_found"] = True
                    enrichment_results["enrichment_summary"]["total_matches"] += len(ubo_results["people"])
            
            # If domain provided, search by domain
            if domain:
                domain_results = await self.search_organizations(domain.replace("www.", ""))
                enrichment_results["domain_search"] = domain_results
                
                if domain_results["success"] and domain_results["organizations"]:
                    enrichment_results["enrichment_summary"]["domain_verified"] = True
                    enrichment_results["enrichment_summary"]["total_matches"] += len(domain_results["organizations"])
            
            logger.info(f"Apollo enrichment completed: {enrichment_results['enrichment_summary']}")
            
        except Exception as e:
            logger.error(f"Apollo enrichment failed: {str(e)}")
            enrichment_results["error"] = str(e)
        
        return enrichment_results
    
    def _filter_relevant_organizations(self, organizations: List[Dict], entity_name: str, domain: Optional[str] = None) -> List[Dict]:
        """Filter organizations to return only relevant ones"""
        if not organizations:
            return []
        
        relevant_orgs = []
        entity_lower = entity_name.lower()
        
        for org in organizations:
            org_name = org.get("name", "").lower()
            org_website = org.get("website_url", "").lower()
            
            # Check if organization name contains key words from entity name
            entity_words = entity_lower.split()
            name_match_score = 0
            
            for word in entity_words:
                if len(word) > 3 and word in org_name:  # Only consider words longer than 3 chars
                    name_match_score += 1
            
            # Check domain match
            domain_match = False
            if domain and domain.lower() in org_website:
                domain_match = True
            
            # Include if significant name match or domain match
            if name_match_score >= 2 or domain_match:
                relevant_orgs.append(org)
        
        return relevant_orgs[:3]  # Return max 3 most relevant
    
    def _filter_relevant_people(self, people: List[Dict], ubo_name: str, entity_name: str) -> List[Dict]:
        """Filter people to return only relevant ones"""
        if not people:
            return []
        
        relevant_people = []
        ubo_lower = ubo_name.lower()
        entity_lower = entity_name.lower()
        
        for person in people:
            person_name = person.get("name", "").lower()
            person_org = person.get("organization", {}).get("name", "").lower()
            
            # Check name similarity
            name_words = ubo_lower.split()
            name_match_score = 0
            
            for word in name_words:
                if len(word) > 3 and word in person_name:
                    name_match_score += 1
            
            # Check if person's organization matches entity
            org_match = False
            if entity_lower in person_org or person_org in entity_lower:
                org_match = True
            
            # Include if significant name match or organization match
            if name_match_score >= 2 or org_match:
                relevant_people.append(person)
        
        return relevant_people[:3]  # Return max 3 most relevant
    
    def _extract_relevant_company_data(self, organization: Dict) -> Dict[str, Any]:
        """Extract only relevant company data for UBO trace"""
        return {
            "id": organization.get("id"),
            "name": organization.get("name"),
            "website": organization.get("website_url"),
            "industry": organization.get("industry"),
            "employee_count": organization.get("estimated_num_employees"),
            "founded_year": organization.get("founded_year"),
            "location": {
                "address": organization.get("street_address"),
                "city": organization.get("city"),
                "state": organization.get("state"),
                "country": organization.get("country"),
                "postal_code": organization.get("postal_code")
            },
            "contact": {
                "phone": organization.get("phone"),
                "linkedin": organization.get("linkedin_url")
            },
            "description": organization.get("short_description", "")[:200] if organization.get("short_description") else None
        }
    
    def _extract_relevant_person_data(self, person: Dict) -> Dict[str, Any]:
        """Extract only relevant person data for UBO trace"""
        return {
            "id": person.get("id"),
            "name": person.get("name"),
            "title": person.get("title"),
            "email": person.get("email"),
            "phone": person.get("phone_numbers", [{}])[0].get("raw_number") if person.get("phone_numbers") else None,
            "linkedin": person.get("linkedin_url"),
            "organization": {
                "name": person.get("organization", {}).get("name"),
                "industry": person.get("organization", {}).get("industry"),
                "website": person.get("organization", {}).get("website_url")
            },
            "seniority": person.get("seniority")
        }
    
    def extract_key_insights(self, enrichment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key insights from Apollo enrichment data"""
        
        insights = {
            "entity_verification": {
                "verified": False,
                "company_details": {},
                "confidence_score": 0
            },
            "ubo_verification": {
                "verified": False,
                "person_details": {},
                "confidence_score": 0
            },
            "domain_verification": {
                "verified": False,
                "domain_details": {},
                "confidence_score": 0
            },
            "overall_confidence": 0
        }
        
        try:
            # Analyze entity search results
            entity_search = enrichment_data.get("entity_search", {})
            if entity_search.get("success") and entity_search.get("organizations"):
                orgs = entity_search["organizations"]
                if orgs:
                    insights["entity_verification"]["verified"] = True
                    insights["entity_verification"]["company_details"] = orgs[0]
                    insights["entity_verification"]["confidence_score"] = min(100, len(orgs) * 30)
            
            # Analyze UBO search results
            ubo_search = enrichment_data.get("ubo_search", {})
            if ubo_search.get("success") and ubo_search.get("people"):
                people = ubo_search["people"]
                if people:
                    insights["ubo_verification"]["verified"] = True
                    insights["ubo_verification"]["person_details"] = people[0]
                    insights["ubo_verification"]["confidence_score"] = min(100, len(people) * 40)
            
            # Analyze domain search results
            domain_search = enrichment_data.get("domain_search", {})
            if domain_search.get("success") and domain_search.get("organizations"):
                orgs = domain_search["organizations"]
                if orgs:
                    insights["domain_verification"]["verified"] = True
                    insights["domain_verification"]["domain_details"] = orgs[0]
                    insights["domain_verification"]["confidence_score"] = min(100, len(orgs) * 50)
            
            # Calculate overall confidence
            scores = [
                insights["entity_verification"]["confidence_score"],
                insights["ubo_verification"]["confidence_score"],
                insights["domain_verification"]["confidence_score"]
            ]
            insights["overall_confidence"] = sum(scores) / len(scores) if scores else 0
            
        except Exception as e:
            logger.error(f"Failed to extract insights: {str(e)}")
        
        return insights
    
    async def _analyze_apollo_people_with_lyzr(
        self, 
        organization_name: str,
        people: List[Dict],
        search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze Apollo people search results using Lyzr agent with retry logic"""
        
        # Check if Lyzr agent is configured
        if not self.settings.agent_apollo_people_analysis or not self.settings.session_apollo_people_analysis:
            logger.warning("Apollo people analysis agent not configured - skipping analysis")
            return {
                "success": False,
                "error": "Apollo people analysis agent not configured",
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
                message = f"""organization_name: {organization_name}

search_params:
{json.dumps(search_params, indent=2)}

people:
{json.dumps(people, indent=2)}"""
                
                request_data = {
                    "user_id": self.settings.lyzr_user_id,
                    "agent_id": self.settings.agent_apollo_people_analysis,
                    "session_id": self.settings.session_apollo_people_analysis,
                    "message": message
                }
                
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{max_retries} for Lyzr Apollo people analysis: {organization_name}")
                else:
                    logger.info(f"Calling Lyzr Apollo people analysis agent for: {organization_name}")
                
                logger.info(f"Analyzing {len(people)} people from Apollo")
                
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
                            logger.warning(f"Lyzr Apollo people analysis returned empty response (attempt {attempt + 1}/{max_retries + 1}). Retrying in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            logger.warning(f"Lyzr Apollo people analysis returned empty response after {max_retries + 1} attempts")
                            return {
                                "success": False,
                                "error": "Lyzr agent returned empty response after retries",
                                "analysis": None,
                                "raw_response": ""
                            }
                    
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    logger.info(f"Lyzr Apollo people analysis completed in {processing_time_ms}ms (attempt {attempt + 1})")
                    
                    return {
                        "success": True,
                        "analysis": content,
                        "raw_response": content,
                        "processing_time_ms": processing_time_ms
                    }
                    
            except httpx.TimeoutException as e:
                error_msg = "Lyzr agent request timed out. The service may be experiencing high load."
                logger.error(f"Lyzr Apollo people analysis timeout (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                
                # Retry on timeout
                if attempt < max_retries:
                    logger.info(f"Retrying Lyzr Apollo people analysis in {retry_delay} seconds due to timeout...")
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
                logger.error(f"Lyzr Apollo people analysis connection error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}")
                
                # Retry on connection errors
                if attempt < max_retries:
                    logger.info(f"Retrying Lyzr Apollo people analysis in {retry_delay} seconds due to connection error...")
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
                logger.error(f"Lyzr Apollo people analysis failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg}")
                
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
                    logger.info(f"Retrying Lyzr Apollo people analysis in {retry_delay} seconds due to error...")
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
                
                logger.error(f"Lyzr Apollo people analysis failed (attempt {attempt + 1}/{max_retries + 1}): {error_msg}")
                
                # If this is not the last attempt, wait before retrying
                if attempt < max_retries:
                    logger.info(f"Retrying Lyzr Apollo people analysis in {retry_delay} seconds due to error...")
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
            "error": "Lyzr Apollo people analysis failed after all retries",
            "analysis": None,
            "raw_response": ""
        }
