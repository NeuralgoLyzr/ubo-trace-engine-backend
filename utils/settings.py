"""
UBO Trace Engine Backend - Configuration Settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application settings
    app_name: str = "UBO Trace Engine Backend"
    debug: bool = True
    version: str = "1.0.0"
    
    # Database settings
    mongodb_url: str = ""  # Required - must be set in .env
    database_name: str = "ubo_trace_engine"
    
    # Lyzr AI Agent settings
    lyzr_api_url: str = "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"
    lyzr_api_key: str = ""  # Required - must be set in .env
    lyzr_user_id: str = ""  # Required - must be set in .env
    
    # Agent IDs for different stages
    agent_stage_1a: str = ""  # Required - must be set in .env
    agent_stage_1b: str = ""  # Required - must be set in .env
    agent_stage_2a: str = ""  # Required - must be set in .env
    agent_stage_2b: str = ""  # Required - must be set in .env
    
    # Session IDs for different stages
    session_stage_1a: str = ""  # Required - must be set in .env
    session_stage_1b: str = ""  # Required - must be set in .env
    session_stage_2a: str = ""  # Required - must be set in .env
    session_stage_2b: str = ""  # Required - must be set in .env
    
    # Company Domain Analysis Agent
    agent_company_domain: str = ""  # Required - must be set in .env
    session_company_domain: str = ""  # Required - must be set in .env
    
    # Expert Domain Analysis Agent
    agent_expert_domain: str = ""  # Required - must be set in .env
    session_expert_domain: str = ""  # Required - must be set in .env
    
    # UBO Search Agents
    agent_ubo_domain: str = ""  # Required - must be set in .env
    session_ubo_domain: str = ""  # Required - must be set in .env
    agent_ubo_csuite: str = ""  # Required - must be set in .env
    session_ubo_csuite: str = ""  # Required - must be set in .env
    agent_ubo_ubos: str = ""  # Required - must be set in .env
    session_ubo_ubos: str = ""  # Required - must be set in .env
    agent_ubo_crossverify: str = ""  # Required - must be set in .env
    session_ubo_crossverify: str = ""  # Required - must be set in .env
    agent_ubo_registries: str = ""  # Required - must be set in .env
    session_ubo_registries: str = ""  # Required - must be set in .env
    agent_ubo_hierarchy: str = ""  # Required - must be set in .env
    session_ubo_hierarchy: str = ""  # Required - must be set in .env
    
    # UBO Ownership Analysis Agent (for Google Search results)
    agent_ubo_ownership_analysis: str = ""  # Required - must be set in .env
    session_ubo_ownership_analysis: str = ""  # Required - must be set in .env
    
    # Apollo People Search Analysis Agent (for Apollo API results)
    agent_apollo_people_analysis: str = ""  # Required - must be set in .env
    session_apollo_people_analysis: str = ""  # Required - must be set in .env
    
    # Candidate UBO Analysis Agent
    agent_candidate_ubo_analysis: str = ""  # Required - must be set in .env
    session_candidate_ubo_analysis: str = ""  # Required - must be set in .env
    
    # UBO Verification Agent
    agent_ubo_verification: str = ""  # Required - must be set in .env
    session_ubo_verification: str = ""  # Required - must be set in .env
    
    # UK PSC Natural Person Verification Agent
    agent_psc_natural_person: str = ""  # Required - must be set in .env
    session_psc_natural_person: str = ""  # Required - must be set in .env
    
    # UK Companies House API settings
    companies_house_api_key: str = ""  # Required - must be set in .env
    
    # Apollo.io API settings
    apollo_api_key: str = ""  # Required - must be set in .env
    apollo_base_url: str = "https://api.apollo.io/v1"
    apollo_timeout: int = 30
    
    # SearchAPI Google settings
    searchapi_api_key: str = ""  # Optional - for domain search enhancement
    searchapi_timeout: int = 30
    
    # API settings
    api_timeout: int = 180  # Increased from 60 to 180 seconds for complex recursive searches
    max_retries: int = 3
    retry_delay: float = 5.0
    
    # Rate limiting
    rate_limit_per_minute: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_required_settings()
    
    def _validate_required_settings(self):
        """Validate that all required sensitive settings are provided"""
        required_fields = [
            'mongodb_url',
            'lyzr_api_key',
            'lyzr_user_id',
            'agent_stage_1a',
            'agent_stage_1b', 
            'agent_stage_2a',
            'agent_stage_2b',
            'session_stage_1a',
            'session_stage_1b',
            'session_stage_2a',
            'session_stage_2b',
            'agent_company_domain',
            'session_company_domain',
            'agent_expert_domain',
            'session_expert_domain',
            'agent_ubo_domain',
            'session_ubo_domain',
            'agent_ubo_csuite',
            'session_ubo_csuite',
            'agent_ubo_ubos',
            'session_ubo_ubos',
            'agent_ubo_crossverify',
            'session_ubo_crossverify',
            'agent_ubo_registries',
            'session_ubo_registries',
            'agent_ubo_hierarchy',
            'session_ubo_hierarchy',
            'agent_ubo_ownership_analysis',
            'session_ubo_ownership_analysis',
            'agent_apollo_people_analysis',
            'session_apollo_people_analysis',
            'agent_candidate_ubo_analysis',
            'session_candidate_ubo_analysis',
            'agent_ubo_verification',
            'session_ubo_verification',
            'apollo_api_key'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(self, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_fields)}. "
                f"Please set these in your .env file."
            )

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings
