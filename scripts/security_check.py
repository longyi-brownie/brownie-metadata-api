#!/usr/bin/env python3
"""
Security validation script for Brownie Metadata API.

This script validates security configuration and checks for common security issues.
"""

import os
import sys
import secrets
import base64
from pathlib import Path
from typing import List, Dict, Any


class SecurityValidator:
    """Validates security configuration."""
    
    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def add_issue(self, severity: str, message: str, fix: str = None):
        """Add a security issue."""
        self.issues.append({
            "severity": severity,
            "message": message,
            "fix": fix
        })
    
    def add_warning(self, message: str, fix: str = None):
        """Add a security warning."""
        self.warnings.append({
            "message": message,
            "fix": fix
        })
    
    def check_jwt_secret(self):
        """Check JWT secret security."""
        jwt_secret = os.getenv("METADATA_JWT_SECRET")
        
        if not jwt_secret:
            self.add_issue(
                "CRITICAL",
                "JWT secret not set",
                "Set METADATA_JWT_SECRET environment variable"
            )
            return
        
        if jwt_secret == "CHANGE_THIS_TO_A_STRONG_SECRET_AT_LEAST_32_CHARS":
            self.add_issue(
                "CRITICAL",
                "JWT secret is still the default value",
                "Generate a strong secret with: openssl rand -base64 32"
            )
            return
        
        if len(jwt_secret) < 32:
            self.add_issue(
                "HIGH",
                f"JWT secret is too short ({len(jwt_secret)} chars, need 32+)",
                "Generate a longer secret with: openssl rand -base64 32"
            )
        
        # Check for weak patterns
        weak_patterns = ["password", "secret", "key", "123456", "admin", "test"]
        jwt_lower = jwt_secret.lower()
        for pattern in weak_patterns:
            if pattern in jwt_lower:
                self.add_issue(
                    "MEDIUM",
                    f"JWT secret contains weak pattern: {pattern}",
                    "Use a cryptographically random secret"
                )
                break
    
    def check_database_security(self):
        """Check database security configuration."""
        dsn = os.getenv("METADATA_POSTGRES_DSN", "")
        
        if "brownie:brownie" in dsn:
            self.add_issue(
                "HIGH",
                "Using default database credentials",
                "Change database password in production"
            )
        
        if "sslmode=require" not in dsn and "sslmode=verify-full" not in dsn:
            self.add_warning(
                "Database connection not using SSL",
                "Add ?sslmode=require to DSN for encrypted connections"
            )
        
        if "sslcert=" not in dsn and os.getenv("VAULT_ENABLED", "false").lower() == "true":
            self.add_warning(
                "Vault enabled but no client certificates in DSN",
                "Configure client certificate authentication"
            )
    
    def check_cors_configuration(self):
        """Check CORS configuration."""
        cors_origins = os.getenv("METADATA_CORS_ORIGINS", "")
        
        if "*" in cors_origins:
            self.add_issue(
                "HIGH",
                "CORS allows all origins (*)",
                "Restrict CORS to specific domains in production"
            )
        
        if not cors_origins:
            self.add_warning(
                "CORS origins not configured",
                "Set METADATA_CORS_ORIGINS environment variable"
            )
    
    def check_debug_mode(self):
        """Check debug mode configuration."""
        debug = os.getenv("METADATA_DEBUG", "false").lower()
        environment = os.getenv("ENVIRONMENT", "development")
        
        if debug == "true" and environment == "production":
            self.add_issue(
                "CRITICAL",
                "Debug mode enabled in production",
                "Set METADATA_DEBUG=false in production"
            )
    
    def check_file_permissions(self):
        """Check file permissions for sensitive files."""
        sensitive_files = [
            ".env",
            "dev-certs/",
            "secrets/",
            "*.key",
            "*.crt",
            "*.pem"
        ]
        
        for pattern in sensitive_files:
            if "*" in pattern:
                # Check for files matching pattern
                for file_path in Path(".").glob(pattern):
                    if file_path.exists():
                        self._check_file_permissions(file_path)
            else:
                file_path = Path(pattern)
                if file_path.exists():
                    self._check_file_permissions(file_path)
    
    def _check_file_permissions(self, file_path: Path):
        """Check permissions for a specific file."""
        try:
            stat = file_path.stat()
            mode = stat.st_mode
            
            # Check if file is readable by others
            if mode & 0o004:
                self.add_issue(
                    "MEDIUM",
                    f"File {file_path} is readable by others",
                    f"Run: chmod 600 {file_path}"
                )
        except Exception:
            pass
    
    def check_gitignore(self):
        """Check .gitignore for security."""
        gitignore_path = Path(".gitignore")
        
        if not gitignore_path.exists():
            self.add_issue(
                "CRITICAL",
                ".gitignore file not found",
                "Create .gitignore file to prevent committing secrets"
            )
            return
        
        gitignore_content = gitignore_path.read_text()
        
        required_patterns = [
            ".env",
            "*.key",
            "*.crt",
            "*.pem",
            "secrets/",
            "dev-certs/"
        ]
        
        for pattern in required_patterns:
            if pattern not in gitignore_content:
                self.add_issue(
                    "HIGH",
                    f"Pattern '{pattern}' not in .gitignore",
                    f"Add '{pattern}' to .gitignore"
                )
    
    def check_environment_files(self):
        """Check for environment files that shouldn't be committed."""
        env_files = [".env", ".env.local", ".env.production", ".env.staging"]
        
        for env_file in env_files:
            if Path(env_file).exists():
                self.add_issue(
                    "CRITICAL",
                    f"Environment file {env_file} exists (should be in .gitignore)",
                    f"Add {env_file} to .gitignore and remove from git"
                )
    
    def generate_secure_jwt_secret(self) -> str:
        """Generate a secure JWT secret."""
        return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    
    def run_all_checks(self):
        """Run all security checks."""
        print("🔍 Running security validation...")
        print("=" * 50)
        
        self.check_jwt_secret()
        self.check_database_security()
        self.check_cors_configuration()
        self.check_debug_mode()
        self.check_file_permissions()
        self.check_gitignore()
        self.check_environment_files()
        
        self.print_results()
    
    def print_results(self):
        """Print validation results."""
        if not self.issues and not self.warnings:
            print("✅ All security checks passed!")
            return
        
        if self.issues:
            print("\n🚨 SECURITY ISSUES FOUND:")
            print("-" * 30)
            
            for issue in self.issues:
                severity_icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠", 
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }.get(issue["severity"], "⚪")
                
                print(f"{severity_icon} {issue['severity']}: {issue['message']}")
                if issue.get("fix"):
                    print(f"   💡 Fix: {issue['fix']}")
                print()
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            print("-" * 15)
            
            for warning in self.warnings:
                print(f"⚠️  {warning['message']}")
                if warning.get("fix"):
                    print(f"   💡 Fix: {warning['fix']}")
                print()
        
        # Summary
        total_issues = len(self.issues)
        critical_issues = len([i for i in self.issues if i["severity"] == "CRITICAL"])
        
        print("=" * 50)
        print(f"📊 Summary: {total_issues} issues, {len(self.warnings)} warnings")
        
        if critical_issues > 0:
            print(f"🔴 {critical_issues} critical issues must be fixed!")
            sys.exit(1)
        elif total_issues > 0:
            print(f"🟡 {total_issues} issues should be fixed")
            sys.exit(1)
        else:
            print("✅ Security validation passed!")


def main():
    """Main function."""
    print("🛡️  Brownie Metadata API - Security Validator")
    print("=" * 50)
    
    validator = SecurityValidator()
    validator.run_all_checks()
    
    # Offer to generate JWT secret if needed
    if not os.getenv("METADATA_JWT_SECRET"):
        print("\n🔑 Generate JWT secret:")
        print(f"   export METADATA_JWT_SECRET='{validator.generate_secure_jwt_secret()}'")


if __name__ == "__main__":
    main()
