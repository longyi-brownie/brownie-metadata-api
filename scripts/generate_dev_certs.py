#!/usr/bin/env python3
"""
Generate development certificates for database authentication.

This script creates self-signed certificates for local development.
For production, use Vault PKI or proper certificate management.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, cwd: Path = None) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def generate_ca_certificate(cert_dir: Path) -> bool:
    """Generate CA certificate."""
    print("Generating CA certificate...")

    # Create CA private key
    success, output = run_command([
        "openssl", "genrsa", "-out", "ca.key", "4096"
    ], cwd=cert_dir)

    if not success:
        print(f"Failed to generate CA key: {output}")
        return False

    # Create CA certificate
    ca_config = """
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = Brownie Development
OU = IT Department
CN = Brownie Metadata CA

[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
"""

    config_file = cert_dir / "ca.conf"
    config_file.write_text(ca_config)

    success, output = run_command([
        "openssl", "req", "-new", "-x509", "-days", "3650",
        "-key", "ca.key", "-out", "ca.crt", "-config", "ca.conf"
    ], cwd=cert_dir)

    if not success:
        print(f"Failed to generate CA certificate: {output}")
        return False

    print("✓ CA certificate generated")
    return True


def generate_client_certificate(cert_dir: Path) -> bool:
    """Generate client certificate."""
    print("Generating client certificate...")

    # Create client private key
    success, output = run_command([
        "openssl", "genrsa", "-out", "client.key", "2048"
    ], cwd=cert_dir)

    if not success:
        print(f"Failed to generate client key: {output}")
        return False

    # Create client certificate signing request
    client_config = """
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = CA
L = San Francisco
O = Brownie Development
OU = IT Department
CN = brownie-fastapi-server

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = brownie-fastapi-server
IP.1 = 127.0.0.1
"""

    config_file = cert_dir / "client.conf"
    config_file.write_text(client_config)

    success, output = run_command([
        "openssl", "req", "-new", "-key", "client.key",
        "-out", "client.csr", "-config", "client.conf"
    ], cwd=cert_dir)

    if not success:
        print(f"Failed to generate client CSR: {output}")
        return False

    # Sign client certificate with CA
    success, output = run_command([
        "openssl", "x509", "-req", "-in", "client.csr",
        "-CA", "ca.crt", "-CAkey", "ca.key", "-CAcreateserial",
        "-out", "client.crt", "-days", "365",
        "-extensions", "v3_req", "-extfile", "client.conf"
    ], cwd=cert_dir)

    if not success:
        print(f"Failed to sign client certificate: {output}")
        return False

    print("✓ Client certificate generated")
    return True


def setup_postgresql_certificates(cert_dir: Path) -> bool:
    """Setup PostgreSQL to use the certificates."""
    print("Setting up PostgreSQL certificates...")

    # Create PostgreSQL certificate directory
    pg_cert_dir = Path("/tmp/pg-certs")
    pg_cert_dir.mkdir(exist_ok=True)

    # Copy certificates to PostgreSQL directory
    import shutil
    shutil.copy2(cert_dir / "ca.crt", pg_cert_dir / "ca.crt")
    shutil.copy2(cert_dir / "client.crt", pg_cert_dir / "client.crt")
    shutil.copy2(cert_dir / "client.key", pg_cert_dir / "client.key")

    # Set proper permissions
    os.chmod(pg_cert_dir / "client.key", 0o600)
    os.chmod(pg_cert_dir / "client.crt", 0o644)
    os.chmod(pg_cert_dir / "ca.crt", 0o644)

    print(f"✓ PostgreSQL certificates copied to {pg_cert_dir}")
    print(f"  Update your PostgreSQL configuration to use certificates from: {pg_cert_dir}")

    return True


def main():
    """Main function."""
    print("🔐 Brownie Metadata API - Development Certificate Generator")
    print("=" * 60)

    # Check if OpenSSL is available
    success, _ = run_command(["openssl", "version"])
    if not success:
        print("❌ OpenSSL is required but not found. Please install OpenSSL.")
        sys.exit(1)

    # Create certificate directory
    cert_dir = Path("dev-certs")
    cert_dir.mkdir(exist_ok=True)

    print(f"📁 Certificate directory: {cert_dir.absolute()}")

    # Generate certificates
    if not generate_ca_certificate(cert_dir):
        sys.exit(1)

    if not generate_client_certificate(cert_dir):
        sys.exit(1)

    if not setup_postgresql_certificates(cert_dir):
        sys.exit(1)

    # Clean up temporary files
    for file in ["ca.conf", "client.conf", "client.csr", "ca.srl"]:
        temp_file = cert_dir / file
        if temp_file.exists():
            temp_file.unlink()

    print("\n✅ Development certificates generated successfully!")
    print("\n📋 Next steps:")
    print("1. Update your PostgreSQL configuration to use client certificate authentication")
    print("2. Set LOCAL_CERT_DIR=dev-certs in your environment")
    print("3. Update METADATA_POSTGRES_DSN to use certificate authentication")
    print("\n🔧 Example PostgreSQL configuration:")
    print("   ssl = on")
    print("   ssl_cert_file = '/tmp/pg-certs/client.crt'")
    print("   ssl_key_file = '/tmp/pg-certs/client.key'")
    print("   ssl_ca_file = '/tmp/pg-certs/ca.crt'")
    print("   ssl_cert_file = 'client'")
    print("\n🔧 Example DSN:")
    print("   postgresql://brownie-fastapi-server@localhost:5432/brownie_metadata?sslmode=require&sslcert=dev-certs/client.crt&sslkey=dev-certs/client.key&sslrootcert=dev-certs/ca.crt")


if __name__ == "__main__":
    main()
