"""
Okta OIDC authentication integration.

This module provides Okta OIDC authentication as an alternative to JWT-based auth.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx
import structlog
from fastapi import Depends, HTTPException, status, APIRouter, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, UserRole, Organization, Team
from .schemas import UserClaims, TokenResponse
from .settings import settings

logger = structlog.get_logger(__name__)

# Okta security
okta_security = HTTPBearer()

# Okta router
okta_router = APIRouter(prefix="/okta", tags=["okta"])


class OktaClient:
    """Okta OIDC client for authentication."""
    
    def __init__(self):
        self.domain = settings.okta_domain
        self.client_id = settings.okta_client_id
        self.client_secret = settings.okta_client_secret
        self.redirect_uri = f"{settings.host}:{settings.port}/api/v1/okta/callback"
        
        if not all([self.domain, self.client_id, self.client_secret]):
            logger.warning("Okta configuration incomplete - OIDC features disabled")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = f"https://{self.domain}"
            self.authorization_endpoint = f"{self.base_url}/oauth2/default/v1/authorize"
            self.token_endpoint = f"{self.base_url}/oauth2/default/v1/token"
            self.userinfo_endpoint = f"{self.base_url}/oauth2/default/v1/userinfo"
            self.jwks_uri = f"{self.base_url}/oauth2/default/v1/keys"
    
    def get_authorization_url(self, state: str) -> str:
        """Get Okta authorization URL."""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Okta OIDC not configured"
            )
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "openid profile email",
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_endpoint}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Okta OIDC not configured"
            )
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error("Failed to exchange code for token", status=response.status_code)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Okta."""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Okta OIDC not configured"
            )
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                logger.error("Failed to get user info", status=response.status_code)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user information"
                )
            
            return response.json()
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """Verify and decode ID token."""
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Okta OIDC not configured"
            )
        
        try:
            # In production, you should verify the JWT signature using Okta's JWKS
            # For now, we'll just decode it (not recommended for production)
            payload = jwt.decode(
                id_token,
                options={"verify_signature": False}  # Disable for development
            )
            return payload
        except JWTError as e:
            logger.error("Failed to verify ID token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID token"
            )


# Global Okta client
okta_client = OktaClient()


async def get_or_create_okta_user(
    user_info: Dict[str, Any], 
    db: Session
) -> User:
    """Get or create user from Okta user info."""
    email = user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found in user info"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        # Update user info from Okta
        user.full_name = user_info.get("name", user.full_name)
        user.avatar_url = user_info.get("picture", user.avatar_url)
        user.is_verified = True
        db.commit()
        return user
    
    # Create new user - need to determine organization and team
    # For now, create a default organization and team
    org_name = f"{email.split('@')[1].split('.')[0].title()} Organization"
    org_slug = org_name.lower().replace(" ", "-")
    
    organization = Organization(
        name=org_name,
        slug=org_slug,
        is_active=True,
        max_teams=10,
        max_users_per_team=50,
    )
    db.add(organization)
    db.flush()
    
    team_name = "Default Team"
    team_slug = team_name.lower().replace(" ", "-")
    
    team = Team(
        name=team_name,
        slug=team_slug,
        org_id=organization.id,
        organization_id=organization.id,
        is_active=True,
    )
    db.add(team)
    db.flush()
    
    # Create user
    user = User(
        email=email,
        username=user_info.get("preferred_username", email.split("@")[0]),
        full_name=user_info.get("name"),
        avatar_url=user_info.get("picture"),
        is_active=True,
        is_verified=True,
        team_id=team.id,
        role=UserRole.ADMIN,  # First user is admin
        org_id=organization.id,
        organization_id=organization.id,
    )
    db.add(user)
    db.commit()
    
    return user


def create_okta_token(user: User) -> str:
    """Create a JWT token for Okta-authenticated user."""
    roles = [user.role.value] if user.role else []
    
    token_data = {
        "sub": str(user.id),
        "org_id": str(user.org_id),
        "email": user.email,
        "roles": roles,
        "auth_provider": "okta",
        "iat": datetime.utcnow(),
    }
    
    from .auth import create_access_token
    return create_access_token(token_data)


# Okta endpoints
@okta_router.get("/login")
async def okta_login(request: Request):
    """Initiate Okta OIDC login."""
    if not okta_client.enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Okta OIDC not configured"
        )
    
    # Generate state parameter for CSRF protection
    state = str(uuid.uuid4())
    
    # Store state in session (in production, use proper session management)
    request.session["okta_state"] = state
    
    auth_url = okta_client.get_authorization_url(state)
    
    return {
        "authorization_url": auth_url,
        "state": state
    }


@okta_router.get("/callback")
async def okta_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Okta OIDC callback."""
    if not okta_client.enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Okta OIDC not configured"
        )
    
    # Verify state parameter
    stored_state = request.session.get("okta_state")
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    try:
        # Exchange code for tokens
        token_response = await okta_client.exchange_code_for_token(code)
        access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received"
            )
        
        # Get user info
        user_info = await okta_client.get_user_info(access_token)
        
        # Get or create user
        user = await get_or_create_okta_user(user_info, db)
        
        # Create JWT token
        jwt_token = create_okta_token(user)
        
        return TokenResponse(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=settings.jwt_expires_minutes * 60
        )
        
    except Exception as e:
        logger.error("Okta callback failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication failed"
        )


@okta_router.get("/userinfo")
async def okta_userinfo(
    credentials: HTTPAuthorizationCredentials = Depends(okta_security),
    db: Session = Depends(get_db)
):
    """Get user information from Okta token."""
    if not okta_client.enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Okta OIDC not configured"
        )
    
    # This would typically verify the Okta access token
    # For now, we'll just return a placeholder
    return {
        "message": "Okta userinfo endpoint - implement token verification"
    }
