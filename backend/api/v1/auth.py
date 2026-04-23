"""
Authentication Endpoints

Provides:
- User registration
- Login/logout
- Token refresh
- Password reset
- API key management
- OAuth2 flows
"""

import logging
import secrets
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from api.schemas.auth import (
    APIKeyCreateRequest,
    APIKeyListItem,
    APIKeyResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from security.audit import get_audit_logger
from security.authentication import TokenType, get_auth_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account"
)
async def register(request: UserRegisterRequest):
    """
    Register a new user.

    - Creates user account
    - Sends verification email (in production)
    - Returns user details
    """

    auth_manager = get_auth_manager()

    # Check if user already exists
    for user in auth_manager._users.values():
        if user.email == request.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        if user.username == request.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Create user
    user = auth_manager.create_user(
        email=request.email,
        username=request.username,
        password=request.password,
        roles=["user"]
    )

    # TODO: Send verification email

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_verified=user.is_verified,
        roles=user.roles,
        created_at=user.created_at
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and return tokens"
)
async def login(request: LoginRequest, req: Request):
    """
    Authenticate user with email and password.

    Returns:
    - Access token (short-lived)
    - Refresh token (long-lived)
    """

    auth_manager = get_auth_manager()
    audit = get_audit_logger()

    # Get client IP
    client_ip = req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = req.client.host if req.client else "unknown"

    # Authenticate
    user = auth_manager.authenticate_user(request.email, request.password)

    if not user:
        # Log failed login
        await audit.log_login(
            user_id="unknown",
            username=request.email,
            ip_address=client_ip,
            success=False,
            error_message="Invalid credentials"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Generate tokens
    access_token = auth_manager.jwt_handler.create_access_token(user)
    refresh_token = auth_manager.jwt_handler.create_refresh_token(user)

    # Log successful login
    await audit.log_login(
        user_id=user.id,
        username=user.username,
        ip_address=client_ip,
        success=True
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_manager.jwt_handler.access_token_expire_minutes * 60
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Get new access token using refresh token"
)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using a valid refresh token.

    - Validates refresh token
    - Issues new access and refresh tokens
    - Revokes old refresh token (rotation)
    """

    auth_manager = get_auth_manager()

    # Verify refresh token
    payload = auth_manager.jwt_handler.verify_token(
        request.refresh_token,
        TokenType.REFRESH
    )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Get user
    user = auth_manager.get_user_by_id(payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Generate new tokens
    tokens = auth_manager.jwt_handler.refresh_access_token(
        request.refresh_token,
        user
    )

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

    access_token, refresh_token = tokens

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_manager.jwt_handler.access_token_expire_minutes * 60
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User logout",
    description="Invalidate current tokens"
)
async def logout(
    request: Request,
    refresh_token: str | None = None
):
    """
    Logout user by revoking tokens.
    """

    auth_manager = get_auth_manager()

    # Get access token from header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        auth_manager.jwt_handler.revoke_token(access_token)

    # Revoke refresh token if provided
    if refresh_token:
        auth_manager.jwt_handler.revoke_token(refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get authenticated user's profile"
)
async def get_current_user_profile(
    current_user = Depends(lambda: None)  # Replace with actual dependency
):
    """Get current authenticated user's profile."""

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        roles=current_user.roles,
        created_at=current_user.created_at
    )


@router.post(
    "/api-keys",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description="Generate a new API key for programmatic access"
)
async def create_api_key(request: APIKeyCreateRequest):
    """
    Create a new API key.

    Note: The key is only shown once. Store it securely!
    """

    auth_manager = get_auth_manager()

    # For demo, use a mock user ID
    user_id = "user_123"

    raw_key, api_key = auth_manager.api_key_manager.generate_api_key(
        name=request.name,
        user_id=user_id,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days
    )

    return APIKeyResponse(
        id=api_key.id,
        key=raw_key,  # Only returned on creation!
        name=api_key.name,
        scopes=api_key.scopes,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at
    )


@router.get(
    "/api-keys",
    response_model=list[APIKeyListItem],
    summary="List API keys",
    description="Get all API keys for the current user"
)
async def list_api_keys():
    """List all API keys for the authenticated user."""

    auth_manager = get_auth_manager()

    # For demo, return all keys
    keys = []
    for _, api_key in auth_manager.api_key_manager._keys.items():
        keys.append(APIKeyListItem(
            id=api_key.id,
            name=api_key.name,
            scopes=api_key.scopes,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used=api_key.last_used
        ))

    return keys


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API key",
    description="Revoke an API key"
)
async def revoke_api_key(key_id: str):
    """Revoke an API key by ID."""

    auth_manager = get_auth_manager()

    if not auth_manager.api_key_manager.revoke_api_key(key_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )


# OAuth2 Endpoints
@router.get(
    "/oauth/{provider}",
    summary="OAuth2 login",
    description="Initiate OAuth2 login flow"
)
async def oauth_login(
    provider: str,
    req: Request
):
    """
    Initiate OAuth2 login flow.

    Redirects user to OAuth2 provider's authorization URL.
    """

    auth_manager = get_auth_manager()

    if not auth_manager.oauth2_handler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth2 not configured"
        )

    provider_config = auth_manager.oauth2_handler.providers.get(provider)
    if not provider_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth2 provider '{provider}' not supported"
        )

    callback_url = provider_config.get("redirect_uri")
    if not callback_url:
        callback_url = str(req.base_url).rstrip("/") + f"/api/v1/auth/oauth/{provider}/callback"

    auth_url = auth_manager.oauth2_handler.get_authorization_url(
        provider=provider,
        redirect_uri=callback_url,
        scopes=["openid", "email", "profile"]
    )

    if not auth_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth2 provider '{provider}' not supported"
        )

    logger.info(f"OAuth2 redirect URL for provider {provider}: {auth_url}")
    logger.debug(f"OAuth2 callback URL configured: {callback_url}")

    return RedirectResponse(url=auth_url)


async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    req: Request
):
    """
    Handle OAuth2 provider callback.

    Exchanges authorization code for tokens and creates/logs in user.
    """
    auth_manager = get_auth_manager()
    audit = get_audit_logger()

    if not auth_manager.oauth2_handler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth2 not configured"
        )

    # Get client IP
    client_ip = req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = req.client.host if req.client else "unknown"

    # Exchange code for tokens using the exact callback URL without query parameters
    redirect_uri = str(req.base_url).rstrip("/") + req.url.path
    logger.debug(f"OAuth callback received code: {code}, state: {state}, redirect_uri: {redirect_uri}")
    try:
        tokens = await auth_manager.oauth2_handler.exchange_code(
            provider=provider,
            code=code,
            state=state,
            redirect_uri=redirect_uri
        )
    except Exception as e:
        error_detail = f"{type(e).__name__}: {e}"
        logger.exception("OAuth2 callback exchange failed")
        await audit.log_login(
            user_id="unknown",
            username=f"oauth_{provider}",
            ip_address=client_ip,
            success=False,
            error_message=error_detail
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        ) from e

    # Get user info from tokens
    user_info = tokens.get("user_info", {})
    email = user_info.get("email")
    google_id = user_info.get("id")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by OAuth2 provider"
        )

    # Check if user exists, create if not
    user = None
    for u in auth_manager._users.values():
        if u.email == email:
            user = u
            break

    if not user:
        # Create new user from OAuth
        username = email.split("@")[0]
        # Ensure unique username
        counter = 1
        original_username = username
        while any(u.username == username for u in auth_manager._users.values()):
            username = f"{original_username}{counter}"
            counter += 1

        user = auth_manager.create_user(
            email=email,
            username=username,
            password=secrets.token_urlsafe(32),  # Random password for OAuth users
            roles=["user"]
        )
        # Mark as OAuth user
        user.oauth_provider = provider
        user.oauth_id = google_id

    # Generate tokens
    access_token = auth_manager.jwt_handler.create_access_token(user)
    refresh_token = auth_manager.jwt_handler.create_refresh_token(user)

    # Log successful OAuth login
    await audit.log_login(
        user_id=user.id,
        username=user.username,
        ip_address=client_ip,
        success=True
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_manager.jwt_handler.access_token_expire_minutes * 60
    )


@router.get("/oauth/{provider}/callback")
async def oauth_callback_html(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    *,
    req: Request
):
    """
    Handle OAuth2 provider callback and redirect to frontend.

    This endpoint handles the OAuth callback and redirects to the frontend
    with tokens in the URL hash for the SPA to handle.
    """
    if error:
        error_payload = error_description or error
        logger.error(
            f"OAuth2 provider returned error for {provider}: {error_payload}"
        )
        redirect_url = f"http://localhost:3000/login?error={urllib.parse.quote_plus(error_payload)}"
        return RedirectResponse(url=redirect_url)

    if not code or not state:
        logger.error("OAuth2 callback missing code or state")
        error_payload = "Missing OAuth2 code or state"
        redirect_url = f"http://localhost:3000/login?error={urllib.parse.quote_plus(error_payload)}"
        return RedirectResponse(url=redirect_url)

    try:
        # Get tokens using the existing callback logic
        token_response = await oauth_callback(provider, code, state, req)

        # Redirect to frontend with tokens in hash
        frontend_url = "http://localhost:3000/auth/callback"
        token_data = urllib.parse.urlencode({
            "access_token": token_response.access_token,
            "refresh_token": token_response.refresh_token,
            "expires_in": token_response.expires_in
        })
        redirect_url = f"{frontend_url}#{token_data}"
        return RedirectResponse(url=redirect_url)

    except HTTPException as e:
        logger.error(f"OAuth callback HTML redirect error: {e.detail}")
        error_message = str(e.detail)
        redirect_url = f"http://localhost:3000/login?error={urllib.parse.quote_plus(error_message)}"
        return RedirectResponse(url=redirect_url)


# Utility dependency for other files

