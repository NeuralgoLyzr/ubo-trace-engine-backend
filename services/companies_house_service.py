"""
UK Companies House API Service for UBO Trace Engine
Provides company search and Persons with Significant Control (PSC) lookup
"""

import httpx
import time
import logging
import json
from typing import Dict, List, Optional, Any
from utils.settings import get_settings

logger = logging.getLogger(__name__)

class CompaniesHouseService:
    """Service for interacting with UK Companies House API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.companies_house_api_key
        self.base_url = "https://api.company-information.service.gov.uk"
        self.timeout = 30.0
        
        if not self.api_key:
            logger.warning("Companies House API key not configured")
    
    async def search_company(self, company_name: str) -> Dict[str, Any]:
        """Search for a company by name"""
        try:
            # URL encode the company name
            import urllib.parse
            encoded_name = urllib.parse.quote(company_name)
            
            url = f"{self.base_url}/search/companies"
            params = {"q": company_name}
            
            # Basic auth with API key
            auth = (self.api_key, "")
            
            logger.info(f"Searching Companies House for: {company_name}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params=params,
                    auth=auth
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Companies House search completed: {result.get('total_results', 0)} results")
                
                return {
                    "success": True,
                    "data": result,
                    "total_results": result.get("total_results", 0),
                    "items": result.get("items", [])
                }
                
        except Exception as e:
            logger.error(f"Companies House search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def get_psc(self, company_number: str) -> Dict[str, Any]:
        """Get Persons with Significant Control for a company"""
        try:
            url = f"{self.base_url}/company/{company_number}/persons-with-significant-control"
            
            # Basic auth with API key
            auth = (self.api_key, "")
            
            logger.info(f"Fetching PSC for company: {company_number}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    auth=auth
                )
                response.raise_for_status()
                
                result = response.json()
                items = result.get("items", [])
                logger.info(f"PSC lookup completed: {len(items)} PSC items found")
                
                return {
                    "success": True,
                    "data": result,
                    "items": items,
                    "total_results": result.get("total_results", 0),
                    "active_count": result.get("active_count", 0)
                }
                
        except Exception as e:
            logger.error(f"PSC lookup failed for company {company_number}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None,
                "items": []
            }
    
    def extract_psc_info(self, psc_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant information from a PSC item"""
        info = {
            "name": psc_item.get("name", ""),
            "kind": psc_item.get("kind", ""),
            "company_name": None,  # Will be set if it's a corporate entity
            "identification": {},
            "address": psc_item.get("address", {}),
            "date_of_birth": psc_item.get("date_of_birth", {}),
            "nationality": psc_item.get("nationality", ""),
            "country_of_residence": psc_item.get("country_of_residence", ""),
            "natures_of_control": psc_item.get("natures_of_control", []),
            "ceased": psc_item.get("ceased", False)
        }
        
        # If it's a corporate entity, extract company name
        if psc_item.get("kind") == "corporate-entity-person-with-significant-control":
            info["company_name"] = psc_item.get("name", "")
            # Extract identification if available
            identification = psc_item.get("identification", {})
            if identification:
                info["identification"] = {
                    "country_registered": identification.get("country_registered", ""),
                    "legal_authority": identification.get("legal_authority", ""),
                    "legal_form": identification.get("legal_form", ""),
                    "place_registered": identification.get("place_registered", ""),
                    "registration_number": identification.get("registration_number", "")
                }
        elif psc_item.get("kind") == "individual-person-with-significant-control":
            # For natural persons, extract identification details
            identification = {}
            
            # Add name elements if available
            name_elements = psc_item.get("name_elements", {})
            if name_elements:
                identification["name_elements"] = name_elements
                identification["title"] = name_elements.get("title", "")
                identification["forename"] = name_elements.get("forename", "")
                identification["middle_name"] = name_elements.get("middle_name", "")
                identification["surname"] = name_elements.get("surname", "")
            
            # Add date of birth
            dob = psc_item.get("date_of_birth", {})
            if dob:
                identification["date_of_birth"] = dob
                identification["birth_year"] = dob.get("year")
                identification["birth_month"] = dob.get("month")
            
            # Add nationality and country of residence
            if psc_item.get("nationality"):
                identification["nationality"] = psc_item.get("nationality")
            if psc_item.get("country_of_residence"):
                identification["country_of_residence"] = psc_item.get("country_of_residence")
            
            info["identification"] = identification
        
        # Calculate age from date of birth if available
        age = None
        dob = psc_item.get("date_of_birth", {})
        if dob.get("year"):
            from datetime import datetime
            current_year = datetime.now().year
            birth_year = dob.get("year")
            age = current_year - birth_year
            # Adjust if we have month and it hasn't passed yet this year
            if dob.get("month"):
                current_month = datetime.now().month
                birth_month = dob.get("month")
                if current_month < birth_month:
                    age -= 1
        
        info["age"] = age
        
        return info

