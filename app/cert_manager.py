"""
Certificate management for database connections.

Supports both Vault (production) and local files (development) for certificate storage.
"""

import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path


class CertificateManager:
    """Manages database certificates from Vault or local files."""
    
    def __init__(self):
        self.vault_enabled = os.getenv("VAULT_ENABLED", "false").lower() == "true"
        self.vault_url = os.getenv("VAULT_URL")
        self.vault_token = os.getenv("VAULT_TOKEN")
        self.vault_path = os.getenv("VAULT_CERT_PATH", "secret/brownie-metadata/certs")
        
        # Local certificate paths (for development)
        self.local_cert_dir = os.getenv("LOCAL_CERT_DIR", "dev-certs")
        
    def get_certificate(self, cert_type: str) -> Optional[str]:
        """
        Get certificate content from Vault or local file.
        
        Args:
            cert_type: Type of certificate (client_cert, client_key, ca_cert)
            
        Returns:
            Certificate content as string, or None if not found
        """
        if self.vault_enabled:
            return self._get_from_vault(cert_type)
        else:
            return self._get_from_local_file(cert_type)
    
    def _get_from_vault(self, cert_type: str) -> Optional[str]:
        """Get certificate from HashiCorp Vault."""
        try:
            import hvac
            
            client = hvac.Client(url=self.vault_url, token=self.vault_token)
            
            # Read secret from Vault
            secret_response = client.secrets.kv.v2.read_secret_version(
                path=self.vault_path
            )
            
            secret_data = secret_response['data']['data']
            cert_content = secret_data.get(cert_type)
            
            if cert_content:
                # Decode if base64 encoded
                try:
                    return base64.b64decode(cert_content).decode('utf-8')
                except:
                    return cert_content
            
            return None
            
        except ImportError:
            raise RuntimeError("hvac package required for Vault integration. Install with: pip install hvac")
        except Exception as e:
            raise RuntimeError(f"Failed to get certificate from Vault: {e}")
    
    def _get_from_local_file(self, cert_type: str) -> Optional[str]:
        """Get certificate from local file."""
        cert_file_map = {
            "client_cert": "client.crt",
            "client_key": "client.key", 
            "ca_cert": "ca.crt"
        }
        
        filename = cert_file_map.get(cert_type)
        if not filename:
            return None
            
        cert_path = Path(self.local_cert_dir) / filename
        
        if cert_path.exists():
            return cert_path.read_text()
        
        return None
    
    def get_database_ssl_config(self, mtls_enabled: bool = False) -> Dict[str, Any]:
        """
        Get complete SSL configuration for database connection.
        
        Args:
            mtls_enabled: Enable mutual TLS (both client and server verify certificates)
        
        Returns:
            Dictionary with SSL configuration parameters
        """
        if mtls_enabled:
            ssl_config = {
                "sslmode": "verify-full"  # Full verification for mTLS
            }
        else:
            ssl_config = {
                "sslmode": "require"  # Basic SSL for development
            }
        
        if self.vault_enabled or self._has_local_certs():
            # Get certificates
            client_cert = self.get_certificate("client_cert")
            client_key = self.get_certificate("client_key")
            ca_cert = self.get_certificate("ca_cert")
            
            if client_cert and client_key:
                # Write certificates to temporary files for psycopg2
                cert_dir = Path("/tmp/brownie-certs")
                cert_dir.mkdir(exist_ok=True)
                
                (cert_dir / "client.crt").write_text(client_cert)
                (cert_dir / "client.key").write_text(client_key)
                
                ssl_config.update({
                    "sslcert": str(cert_dir / "client.crt"),
                    "sslkey": str(cert_dir / "client.key")
                })
                
                if ca_cert:
                    (cert_dir / "ca.crt").write_text(ca_cert)
                    ssl_config["sslrootcert"] = str(cert_dir / "ca.crt")
        
        return ssl_config
    
    def _has_local_certs(self) -> bool:
        """Check if local certificates exist."""
        cert_dir = Path(self.local_cert_dir)
        return (cert_dir / "client.crt").exists() and (cert_dir / "client.key").exists()
    
    def validate_certificates(self) -> Dict[str, bool]:
        """
        Validate that required certificates are available.
        
        Returns:
            Dictionary with validation results for each certificate type
        """
        results = {}
        
        for cert_type in ["client_cert", "client_key", "ca_cert"]:
            cert_content = self.get_certificate(cert_type)
            results[cert_type] = cert_content is not None
        
        return results


# Global certificate manager instance
cert_manager = CertificateManager()
