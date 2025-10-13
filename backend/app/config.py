from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # App Configuration
    app_title: str = "AI Monitoring Agent"
    app_description: str = "Conversational interface for monitoring data"
    environment: str = "development"
    log_level: str = "INFO"
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    
    # Monitoring Sources
    prometheus_url: str = ""
    grafana_url: str = ""
    alertmanager_url: str = ""
    
    # Azure Monitor Configuration (optional)
    enable_azure_monitor: bool = False
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_workspace_id: Optional[str] = None
    azure_subscription_id: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None
    
    # API Configuration
    cors_origins: str = "*"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Query Configuration
    default_time_range: str = "1h"
    max_time_range: str = "7d"
    query_timeout: int = 30
    max_query_results: int = 1000
    cache_ttl: int = 300
    
    # Security
    jwt_secret: Optional[str] = None
    enable_auth: bool = False
    
    # Feature Flags
    enable_grafana_proxy: bool = True
    enable_metrics_export: bool = True
    enable_real_time_updates: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def is_configured(self) -> bool:
        """Check if the basic required configuration is present"""
        return (
            bool(self.openai_api_key) and 
            self.openai_api_key != "your_openai_api_key_here" and
            bool(self.prometheus_url)
        )

# Global settings instance
settings = Settings()