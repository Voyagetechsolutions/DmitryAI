# config.py - Configuration management with Pydantic

from pydantic import BaseSettings, Field, validator
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Configuration priority:
    1. Environment variables
    2. .env file
    3. Default values
    """
    
    # Server Configuration
    dmitry_port: int = Field(default=8765, env="DMITRY_PORT")
    host: str = Field(default="127.0.0.1", env="HOST")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    
    # Platform Integration
    platform_url: Optional[str] = Field(default=None, env="PLATFORM_URL")
    platform_timeout: float = Field(default=30.0, env="PLATFORM_TIMEOUT")
    platform_retry_attempts: int = Field(default=3, env="PLATFORM_RETRY_ATTEMPTS")
    platform_retry_delay: float = Field(default=1.0, env="PLATFORM_RETRY_DELAY")
    
    # Service Mesh
    service_name: str = Field(default="dmitry", env="SERVICE_NAME")
    service_type: str = Field(default="dmitry", env="SERVICE_TYPE")
    heartbeat_interval: int = Field(default=10, env="HEARTBEAT_INTERVAL")
    
    # Security
    jwt_secret: str = Field(default="change-me-in-production", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration: int = Field(default=3600, env="JWT_EXPIRATION")
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Circuit Breaker
    circuit_breaker_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_THRESHOLD")
    circuit_breaker_timeout: int = Field(default=60, env="CIRCUIT_BREAKER_TIMEOUT")
    
    # Caching
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=300, env="CACHE_TTL")
    enable_caching: bool = Field(default=False, env="ENABLE_CACHING")
    
    # Observability
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None, 
        env="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    
    # Database (if needed)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Paths
    log_dir: Path = Field(default=Path("logs"), env="LOG_DIR")
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("llm_temperature")
    def validate_temperature(cls, v):
        """Validate LLM temperature."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
    
    @validator("dmitry_port")
    def validate_port(cls, v):
        """Validate port number."""
        if not 1024 <= v <= 65535:
            raise ValueError("Port must be between 1024 and 65535")
        return v
    
    @validator("jwt_secret")
    def validate_jwt_secret(cls, v):
        """Warn if using default JWT secret."""
        if v == "change-me-in-production":
            import warnings
            warnings.warn(
                "Using default JWT secret. Change this in production!",
                UserWarning
            )
        return v
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def service_url(self) -> str:
        """Get service URL."""
        return f"http://{self.host}:{self.dmitry_port}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return not self.debug and self.jwt_secret != "change-me-in-production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings (singleton).
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


def reload_settings():
    """Reload settings from environment."""
    global _settings
    _settings = None
    return get_settings()


# Convenience function
settings = get_settings()


if __name__ == "__main__":
    # Test configuration
    settings = get_settings()
    print("Configuration loaded successfully!")
    print(f"Port: {settings.dmitry_port}")
    print(f"Log Level: {settings.log_level}")
    print(f"Platform URL: {settings.platform_url}")
    print(f"Service URL: {settings.service_url}")
    print(f"Is Production: {settings.is_production}")
