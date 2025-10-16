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
    
    # Apollo.io API settings
    apollo_api_key: str = ""  # Required - must be set in .env
    apollo_base_url: str = "https://api.apollo.io/v1"
    apollo_timeout: int = 30
    
    # API settings
    api_timeout: int = 60
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
