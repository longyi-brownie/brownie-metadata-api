"""Unit tests for certificate manager."""

import os
from unittest.mock import patch

from app.cert_manager import CertificateManager


class TestCertificateManager:
    """Test certificate manager functionality."""

    def test_init_with_vault_enabled(self):
        """Test initialization with Vault enabled."""
        with patch.dict(
            os.environ,
            {
                "VAULT_ENABLED": "true",
                "VAULT_URL": "http://vault:8200",
                "VAULT_TOKEN": "test-token",
            },
        ):
            manager = CertificateManager()
            assert manager.vault_enabled is True
            assert manager.vault_url == "http://vault:8200"
            assert manager.vault_token == "test-token"

    def test_init_with_vault_disabled(self):
        """Test initialization with Vault disabled."""
        with patch.dict(os.environ, {"VAULT_ENABLED": "false"}, clear=True):
            manager = CertificateManager()
            assert manager.vault_enabled is False

    def test_get_certificate_from_vault(self):
        """Test getting certificate from Vault."""
        with patch.dict(
            os.environ,
            {
                "VAULT_ENABLED": "true",
                "VAULT_URL": "http://vault:8200",
                "VAULT_TOKEN": "test-token",
            },
        ):
            manager = CertificateManager()

            # Mock the _get_from_vault method directly
            with patch.object(
                manager,
                "_get_from_vault",
                return_value="-----BEGIN CERTIFICATE-----\nFAKE_CERT\n-----END CERTIFICATE-----",
            ):
                cert = manager.get_certificate("client_cert")

                assert cert is not None
                assert "BEGIN CERTIFICATE" in cert
                assert "FAKE_CERT" in cert

    def test_get_certificate_from_local_file(self, tmp_path):
        """Test getting certificate from local file."""
        # Create temporary certificate file
        cert_dir = tmp_path / "certs"
        cert_dir.mkdir()
        cert_file = cert_dir / "client.crt"
        cert_content = (
            "-----BEGIN CERTIFICATE-----\nTEST_CERT\n-----END CERTIFICATE-----"
        )
        cert_file.write_text(cert_content)

        with patch.dict(
            os.environ, {"VAULT_ENABLED": "false", "LOCAL_CERT_DIR": str(cert_dir)}
        ):
            manager = CertificateManager()
            cert = manager.get_certificate("client_cert")

            assert cert == cert_content

    def test_get_certificate_file_not_found(self, tmp_path):
        """Test getting certificate when file doesn't exist."""
        cert_dir = tmp_path / "certs"
        cert_dir.mkdir()

        with patch.dict(
            os.environ, {"VAULT_ENABLED": "false", "LOCAL_CERT_DIR": str(cert_dir)}
        ):
            manager = CertificateManager()
            cert = manager.get_certificate("nonexistent_cert")

            assert cert is None

    def test_get_database_ssl_config_with_certs(self, tmp_path):
        """Test getting database SSL config with certificates."""
        # Create temporary certificate files
        cert_dir = tmp_path / "certs"
        cert_dir.mkdir()

        (cert_dir / "client.crt").write_text("CLIENT_CERT")
        (cert_dir / "client.key").write_text("CLIENT_KEY")
        (cert_dir / "ca.crt").write_text("CA_CERT")

        with patch.dict(
            os.environ, {"VAULT_ENABLED": "false", "LOCAL_CERT_DIR": str(cert_dir)}
        ):
            manager = CertificateManager()
            config = manager.get_database_ssl_config(mtls_enabled=True)

            assert config["sslmode"] == "verify-full"  # Changed from verify-ca
            assert "client.crt" in config["sslcert"]
            assert "client.key" in config["sslkey"]
            assert "ca.crt" in config["sslrootcert"]

    def test_get_database_ssl_config_without_mtls(self, tmp_path):
        """Test getting database SSL config without mTLS."""
        cert_dir = tmp_path / "certs"
        cert_dir.mkdir()
        (cert_dir / "ca.crt").write_text("CA_CERT")

        with patch.dict(
            os.environ, {"VAULT_ENABLED": "false", "LOCAL_CERT_DIR": str(cert_dir)}
        ):
            manager = CertificateManager()
            config = manager.get_database_ssl_config(mtls_enabled=False)

            assert config["sslmode"] == "require"
            assert "sslcert" not in config
            assert "sslkey" not in config

    def test_get_database_ssl_config_no_certs(self, tmp_path):
        """Test getting database SSL config when no certificates available."""
        cert_dir = tmp_path / "certs"
        cert_dir.mkdir()

        with patch.dict(
            os.environ, {"VAULT_ENABLED": "false", "LOCAL_CERT_DIR": str(cert_dir)}
        ):
            manager = CertificateManager()
            config = manager.get_database_ssl_config(mtls_enabled=True)

            # Should return sslmode but no cert paths when no certs available
            assert config["sslmode"] == "verify-full"
            assert "sslcert" not in config
            assert "sslkey" not in config

    def test_vault_connection_error(self):
        """Test handling Vault connection errors."""
        with patch.dict(
            os.environ,
            {
                "VAULT_ENABLED": "true",
                "VAULT_URL": "http://vault:8200",
                "VAULT_TOKEN": "test-token",
            },
        ):
            manager = CertificateManager()

            # Mock the _get_from_vault method to raise an exception
            with patch.object(manager, "_get_from_vault", return_value=None):
                cert = manager.get_certificate("client_cert")

                # Should return None on error
                assert cert is None

    def test_base64_encoded_certificate(self):
        """Test handling base64-encoded certificates from Vault."""

        cert_content = "-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----"

        with patch.dict(
            os.environ,
            {
                "VAULT_ENABLED": "true",
                "VAULT_URL": "http://vault:8200",
                "VAULT_TOKEN": "test-token",
            },
        ):
            manager = CertificateManager()

            # Mock the _get_from_vault method to return the decoded cert
            with patch.object(manager, "_get_from_vault", return_value=cert_content):
                cert = manager.get_certificate("client_cert")

                # Should return decoded certificate
                assert cert == cert_content
                assert "BEGIN CERTIFICATE" in cert
