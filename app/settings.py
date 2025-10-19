"""Application settings using Pydantic BaseSettings."""

import os
import secrets
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    postgres_dsn: str = Field(
        default="postgresql://brownie:brownie@localhost:5432/brownie_metadata",
        env="METADATA_POSTGRES_DSN",
        description="PostgreSQL connection string"
    )
    
    # JWT Authentication
    jwt_secret: str = Field(
        default="CHANGE_THIS_TO_A_STRONG_SECRET_AT_LEAST_32_CHARS",
        env="METADATA_JWT_SECRET",
        description="JWT secret key for token signing"
    )
    jwt_expires_minutes: int = Field(
        default=60,
        env="METADATA_JWT_EXPIRES_MINUTES",
        description="JWT token expiration time in minutes"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        env="METADATA_JWT_ALGORITHM",
        description="JWT signing algorithm"
    )
    
    # Application
    debug: bool = Field(
        default=False,
        env="METADATA_DEBUG",
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        env="METADATA_LOG_LEVEL",
        description="Logging level"
    )
    host: str = Field(
        default="0.0.0.0",
        env="METADATA_HOST",
        description="Host to bind the server"
    )
    port: int = Field(
        default=8080,
        env="METADATA_PORT",
        description="Port to bind the server"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="METADATA_CORS_ORIGINS",
        description="Allowed CORS origins"
    )
    
    # Okta OIDC (stubs for v1)
    okta_domain: Optional[str] = Field(
        default=None,
        env="METADATA_OKTA_DOMAIN",
        description="Okta domain for OIDC"
    )
    okta_client_id: Optional[str] = Field(
        default=None,
        env="METADATA_OKTA_CLIENT_ID",
        description="Okta client ID"
    )
    okta_client_secret: Optional[str] = Field(
        default=None,
        env="METADATA_OKTA_CLIENT_SECRET",
        description="Okta client secret"
    )
    
    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        """Validate JWT secret strength."""
        if v == "CHANGE_THIS_TO_A_STRONG_SECRET_AT_LEAST_32_CHARS":
            raise ValueError(
                "JWT_SECRET must be changed from default value! "
                "Generate a strong secret with: openssl rand -base64 32"
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v
    
    @validator('postgres_dsn')
    def validate_postgres_dsn(cls, v):
        """Validate PostgreSQL DSN security."""
        if "password" in v and "brownie:brownie" in v:
            import warnings
            warnings.warn(
                "Using default database credentials! Change password in production.",
                UserWarning
            )
        return v
    
    @validator('debug')
    def validate_debug_mode(cls, v):
        """Warn about debug mode in production."""
        if v and os.getenv('ENVIRONMENT') == 'production':
            import warnings
            warnings.warn(
                "Debug mode is enabled in production! This is a security risk.",
                UserWarning
            )
        return v
    
    @validator('cors_origins')
    def validate_cors_origins(cls, v):
        """Validate CORS origins security."""
        if "*" in v:
            import warnings
            warnings.warn(
                "CORS allows all origins (*)! Restrict to specific domains in production.",
                UserWarning
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
