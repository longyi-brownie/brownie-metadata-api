"""
Secrets management utilities for secure handling of sensitive data.

This module provides utilities for managing secrets in different environments:
- Development: Environment variables or local files
- Production: Vault, AWS Secrets Manager, or other secure stores
"""

import base64
import os
import secrets
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


class SecretsManager:
    """Manages secrets across different environments."""

    def __init__(self) -> None:
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.vault_enabled = os.getenv("VAULT_ENABLED", "false").lower() == "true"

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """
        Get a secret value from the appropriate source.

        Args:
            key: Secret key name
            default: Default value if secret not found

        Returns:
            Secret value or default
        """
        # Try environment variable first
        value = os.getenv(key)
        if value:
            return value

        # Try Vault if enabled
        if self.vault_enabled:
            value = self._get_from_vault(key)
            if value:
                return value

        # Try local secrets file
        value = self._get_from_local_file(key)
        if value:
            return value

        return default

    def _get_from_vault(self, key: str) -> str | None:
        """Get secret from Vault."""
        try:
            import hvac

            vault_url = os.getenv("VAULT_URL")
            vault_token = os.getenv("VAULT_TOKEN")
            vault_path = os.getenv("VAULT_SECRET_PATH", "secret/brownie-metadata")

            if not all([vault_url, vault_token]):
                return None

            client = hvac.Client(url=vault_url, token=vault_token)

            # Read secret from Vault
            secret_response = client.secrets.kv.v2.read_secret_version(
                path=f"{vault_path}/{key}"
            )

            secret_data = secret_response["data"]["data"]
            value = secret_data.get("value")
            return value if isinstance(value, str) else None

        except ImportError:
            logger.warning("hvac package not installed - Vault integration disabled")
            return None
        except Exception as e:
            logger.error("Failed to get secret from Vault", key=key, error=str(e))
            return None

    def _get_from_local_file(self, key: str) -> str | None:
        """Get secret from local file."""
        secrets_dir = Path("secrets")
        secret_file = secrets_dir / f"{key}.txt"

        if secret_file.exists():
            try:
                return secret_file.read_text().strip()
            except Exception as e:
                logger.error("Failed to read secret file", key=key, error=str(e))

        return None

    def generate_jwt_secret(self) -> str:
        """Generate a cryptographically secure JWT secret."""
        return base64.b64encode(secrets.token_bytes(32)).decode("utf-8")

    def generate_database_password(self, length: int = 32) -> str:
        """Generate a secure database password."""
        return secrets.token_urlsafe(length)

    def validate_secret_strength(self, secret: str, min_length: int = 32) -> bool:
        """Validate secret strength."""
        if len(secret) < min_length:
            return False

        # Check for common weak patterns
        weak_patterns = [
            "password",
            "secret",
            "key",
            "123456",
            "admin",
            "test",
            "default",
            "changeme",
            "brownie:brownie",
        ]

        secret_lower = secret.lower()
        for pattern in weak_patterns:
            if pattern in secret_lower:
                return False

        return True


def get_required_secret(key: str, description: str = "") -> str:
    """
    Get a required secret, raising an error if not found.

    Args:
        key: Secret key name
        description: Description of what the secret is for

    Returns:
        Secret value

    Raises:
        ValueError: If secret is not found
    """
    manager = SecretsManager()
    value = manager.get_secret(key)

    if not value:
        raise ValueError(
            f"Required secret '{key}' not found. {description}"
            f"Set {key} environment variable or configure secrets management."
        )

    return value


def get_jwt_secret() -> str:
    """Get JWT secret with validation."""
    manager = SecretsManager()

    # Try to get from environment
    secret = manager.get_secret("METADATA_JWT_SECRET")

    if not secret:
        # Generate a new one for development
        if manager.environment == "development":
            secret = manager.generate_jwt_secret()
            logger.warning(
                "Generated new JWT secret for development. "
                "Set METADATA_JWT_SECRET environment variable for production."
            )
        else:
            raise ValueError(
                "JWT secret not configured! Set METADATA_JWT_SECRET environment variable."
            )

    # Validate secret strength
    if not manager.validate_secret_strength(secret):
        raise ValueError(
            "JWT secret is too weak! Must be at least 32 characters and not contain common patterns."
        )

    return secret


def get_database_password() -> str:
    """Get database password with validation."""
    manager = SecretsManager()

    # Try to get from environment
    password = manager.get_secret("DATABASE_PASSWORD")

    if not password:
        # Generate a new one for development
        if manager.environment == "development":
            password = manager.generate_database_password()
            logger.warning(
                "Generated new database password for development. "
                "Set DATABASE_PASSWORD environment variable for production."
            )
        else:
            raise ValueError(
                "Database password not configured! Set DATABASE_PASSWORD environment variable."
            )

    return password


# Global secrets manager instance
secrets_manager = SecretsManager()
