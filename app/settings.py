"""Application settings using Pydantic BaseSettings."""

import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    postgres_dsn: str = Field(
        default="postgresql://brownie-fastapi-server@localhost:5432/brownie_metadata?sslmode=require&sslcert=../brownie-metadata-database/dev-certs/client.crt&sslkey=../brownie-metadata-database/dev-certs/client.key&sslrootcert=../brownie-metadata-database/dev-certs/ca.crt",
        alias="METADATA_POSTGRES_DSN",
        description="PostgreSQL connection string",
    )

    # JWT Authentication
    jwt_secret: str = Field(
        default="CHANGE_THIS_TO_A_STRONG_SECRET_AT_LEAST_32_CHARS",
        alias="METADATA_JWT_SECRET",
        description="JWT secret key for token signing",
    )
    jwt_expires_minutes: int = Field(
        default=60,
        alias="METADATA_JWT_EXPIRES_MINUTES",
        description="JWT token expiration time in minutes",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        alias="METADATA_JWT_ALGORITHM",
        description="JWT signing algorithm",
    )

    # Application
    debug: bool = Field(
        default=False, alias="METADATA_DEBUG", description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO", alias="METADATA_LOG_LEVEL", description="Logging level"
    )
    host: str = Field(
        default="0.0.0.0", alias="METADATA_HOST", description="Host to bind the server"
    )
    port: int = Field(
        default=8080, alias="METADATA_PORT", description="Port to bind the server"
    )

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        alias="METADATA_CORS_ORIGINS",
        description="Allowed CORS origins",
    )

    # Okta OIDC (stubs for v1)
    okta_domain: str | None = Field(
        default=None, alias="METADATA_OKTA_DOMAIN", description="Okta domain for OIDC"
    )
    okta_client_id: str | None = Field(
        default=None, alias="METADATA_OKTA_CLIENT_ID", description="Okta client ID"
    )
    okta_client_secret: str | None = Field(
        default=None,
        alias="METADATA_OKTA_CLIENT_SECRET",
        description="Okta client secret",
    )

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v, info):
        """Validate JWT secret strength."""
        # Allow test secrets in test environment
        import os
        is_test = os.getenv("PYTEST_CURRENT_TEST") or os.getenv("CI")
        
        if v == "CHANGE_THIS_TO_A_STRONG_SECRET_AT_LEAST_32_CHARS" and not is_test:
            raise ValueError(
                "JWT_SECRET must be changed from default value! "
                "Generate a strong secret with: openssl rand -base64 32"
            )
        if len(v) < 32 and not (is_test and v.startswith("test-")):
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @field_validator("postgres_dsn")
    @classmethod
    def validate_postgres_dsn(cls, v):
        """Validate PostgreSQL DSN security."""
        if "password" in v and "brownie:brownie" in v:
            import warnings

            warnings.warn(
                "Using default database credentials! Change password in production.",
                UserWarning,
                stacklevel=2,
            )
        return v

    @field_validator("debug")
    @classmethod
    def validate_debug_mode(cls, v):
        """Warn about debug mode in production."""
        if v and os.getenv("ENVIRONMENT") == "production":
            import warnings

            warnings.warn(
                "Debug mode is enabled in production! This is a security risk.",
                UserWarning,
                stacklevel=2,
            )
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate CORS origins security."""
        if "*" in v:
            import warnings

            warnings.warn(
                "CORS allows all origins (*)! Restrict to specific domains in production.",
                UserWarning,
                stacklevel=2,
            )
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "populate_by_name": True,
    }


# Global settings instance
settings = Settings()
