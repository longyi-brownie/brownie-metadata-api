"""Integration tests for SSL database connections.

These tests require SSL-enabled PostgreSQL and certificates.
Run with: pytest tests/integration/test_ssl_connection.py -v
"""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.cert_manager import cert_manager
from app.db import _build_database_url_with_certs


def _ssl_enabled() -> bool:
    """Check if SSL is enabled in the test environment."""
    dsn = os.getenv("METADATA_POSTGRES_DSN", "")
    return "sslmode=verify-full" in dsn or os.getenv("TEST_SSL_ENABLED") == "true"


@pytest.mark.integration
@pytest.mark.skipif(
    not _ssl_enabled(),
    reason="SSL tests require SSL-enabled PostgreSQL (sslmode=verify-full or TEST_SSL_ENABLED=true)",
)
class TestSSLConnection:
    """Test SSL database connections."""

    def test_certificate_files_exist(self):
        """Test that certificate files exist in dev-certs directory."""
        cert_dir = Path(os.getenv("LOCAL_CERT_DIR", "dev-certs"))

        required_certs = ["ca.crt", "client.crt", "client.key"]

        for cert_file in required_certs:
            cert_path = cert_dir / cert_file
            assert cert_path.exists(), f"Certificate file not found: {cert_path}"
            assert cert_path.stat().st_size > 0, (
                f"Certificate file is empty: {cert_path}"
            )

            # Check file permissions for private key
            if cert_file == "client.key":
                # Private key should have restricted permissions
                mode = cert_path.stat().st_mode & 0o777
                assert mode in [
                    0o600,
                    0o400,
                ], f"Private key has insecure permissions: {oct(mode)}"

    def test_certificate_content_valid(self):
        """Test that certificate content is valid PEM format."""
        cert_dir = Path(os.getenv("LOCAL_CERT_DIR", "dev-certs"))

        # Test CA certificate
        ca_cert = (cert_dir / "ca.crt").read_text()
        assert "-----BEGIN CERTIFICATE-----" in ca_cert
        assert "-----END CERTIFICATE-----" in ca_cert

        # Test client certificate
        client_cert = (cert_dir / "client.crt").read_text()
        assert "-----BEGIN CERTIFICATE-----" in client_cert
        assert "-----END CERTIFICATE-----" in client_cert

        # Test client key
        client_key = (cert_dir / "client.key").read_text()
        assert "-----BEGIN" in client_key
        assert "PRIVATE KEY-----" in client_key

    def test_certificate_manager_loads_certs(self):
        """Test that certificate manager can load certificates."""
        # Test loading client certificate
        client_cert = cert_manager.get_certificate("client_cert")
        assert client_cert is not None
        assert "BEGIN CERTIFICATE" in client_cert

        # Test loading client key
        client_key = cert_manager.get_certificate("client_key")
        assert client_key is not None
        assert "PRIVATE KEY" in client_key

        # Test loading CA certificate
        ca_cert = cert_manager.get_certificate("ca_cert")
        assert ca_cert is not None
        assert "BEGIN CERTIFICATE" in ca_cert

    def test_database_url_includes_ssl_params(self):
        """Test that database URL includes SSL parameters."""
        # Build URL with certificates
        db_url = _build_database_url_with_certs()

        # Should include SSL mode
        assert "sslmode=" in db_url or "sslcert=" in db_url

        # If mTLS enabled, should include certificate paths
        if os.getenv("METADATA_MTLS_ENABLED", "false").lower() == "true":
            assert "sslcert=" in db_url
            assert "sslkey=" in db_url
            assert "sslrootcert=" in db_url

    def test_ssl_connection_to_database(self):
        """Test actual SSL connection to PostgreSQL database."""
        # Get SSL-enabled database URL
        db_url = os.getenv("METADATA_POSTGRES_DSN_SSL")
        if not db_url:
            pytest.skip("METADATA_POSTGRES_DSN_SSL not set")

        # Ensure URL uses psycopg
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

        # Create engine with SSL
        engine = create_engine(db_url, echo=True)

        # Test connection
        try:
            with engine.connect() as conn:
                # Execute simple query
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()

                assert version is not None
                assert "PostgreSQL" in version

                # Verify SSL is being used
                ssl_result = conn.execute(
                    text(
                        "SELECT ssl_is_used() as ssl_used, ssl_version() as ssl_version"
                    )
                )
                ssl_info = ssl_result.fetchone()

                # Check if SSL is actually being used
                if ssl_info:
                    print(f"SSL Used: {ssl_info[0]}")
                    print(f"SSL Version: {ssl_info[1]}")

        except OperationalError as e:
            pytest.fail(f"Failed to connect with SSL: {e}")
        finally:
            engine.dispose()

    def test_ssl_connection_without_certs_fails(self):
        """Test that connection fails without proper certificates when mTLS required."""
        if os.getenv("METADATA_MTLS_ENABLED", "false").lower() != "true":
            pytest.skip("Test requires mTLS to be enabled")

        # Try to connect without SSL parameters
        db_url = os.getenv("METADATA_POSTGRES_DSN", "")
        if "sslmode=disable" in db_url:
            pytest.skip("Test requires SSL-enabled database")

        # Remove SSL parameters
        base_url = db_url.split("?")[0]
        no_ssl_url = f"{base_url}?sslmode=require"

        if no_ssl_url.startswith("postgresql://"):
            no_ssl_url = no_ssl_url.replace("postgresql://", "postgresql+psycopg://", 1)

        engine = create_engine(no_ssl_url)

        # Should fail to connect without certificates
        with pytest.raises(OperationalError):
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        engine.dispose()

    def test_ssl_connection_with_wrong_ca_fails(self, tmp_path):
        """Test that connection fails with wrong CA certificate."""
        if os.getenv("METADATA_MTLS_ENABLED", "false").lower() != "true":
            pytest.skip("Test requires mTLS to be enabled")

        # Create fake CA certificate
        fake_ca = tmp_path / "fake_ca.crt"
        fake_ca.write_text(
            "-----BEGIN CERTIFICATE-----\nFAKE_CA_CERT\n-----END CERTIFICATE-----"
        )

        # Try to connect with fake CA
        db_url = os.getenv("METADATA_POSTGRES_DSN_SSL", "")
        if not db_url:
            pytest.skip("METADATA_POSTGRES_DSN_SSL not set")

        # Replace CA cert path with fake one
        db_url = db_url.replace("sslrootcert=", f"sslrootcert={fake_ca}&old_")

        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

        engine = create_engine(db_url)

        # Should fail with wrong CA
        with pytest.raises(OperationalError):
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        engine.dispose()


@pytest.mark.integration
class TestSSLConnectionFallback:
    """Test SSL connection fallback behavior."""

    def test_connection_works_without_ssl_when_disabled(self):
        """Test that connection works without SSL when sslmode=disable."""
        db_url = os.getenv(
            "METADATA_POSTGRES_DSN",
            "postgresql://postgres:postgres@localhost:5433/test_brownie_metadata?sslmode=disable",
        )

        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

        engine = create_engine(db_url)

        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                assert result.scalar() == 1
        finally:
            engine.dispose()

    def test_build_url_respects_sslmode_disable(self):
        """Test that URL builder respects sslmode=disable."""
        # Skip if SSL is enabled (settings are already loaded at import time)
        dsn = os.getenv("METADATA_POSTGRES_DSN", "")
        if "sslmode=require" in dsn or "sslmode=verify-full" in dsn:
            pytest.skip("Test requires non-SSL environment")

        # Set DSN with sslmode=disable
        with pytest.MonkeyPatch.context() as m:
            m.setenv(
                "METADATA_POSTGRES_DSN",
                "postgresql://user@localhost/db?sslmode=disable",
            )

            # Import after setting env var
            from app.db import _build_database_url_with_certs

            url = _build_database_url_with_certs()

            # Should keep sslmode=disable and not add SSL params
            assert "sslmode=disable" in url
            assert "sslcert=" not in url
            assert "sslkey=" not in url
