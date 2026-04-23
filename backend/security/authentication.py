"""
Enterprise Authentication System

Provides comprehensive authentication mechanisms:
- JWT token generation and validation
- API key authentication
- OAuth2 integration
- Session management
- Multi-factor authentication support
"""

import hashlib
import logging
import secrets
import urllib.parse
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# JWT handling
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Types of authentication tokens"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    SERVICE = "service"


@dataclass
class TokenPayload:
    """JWT token payload structure"""
    sub: str  # Subject (user ID)
    type: TokenType
    exp: datetime
    iat: datetime = field(default_factory=lambda: datetime.now(UTC))
    jti: str = field(default_factory=lambda: str(uuid.uuid4()))
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    scopes: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class User:
    """User model for authentication"""
    id: str
    email: str
    username: str
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    mfa_enabled: bool = False
    mfa_secret: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime | None = None
    oauth_provider: str | None = None
    oauth_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class APIKey:
    """API Key model"""
    id: str
    key_hash: str
    name: str
    user_id: str
    scopes: list[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    last_used: datetime | None = None
    rate_limit: int = 1000  # requests per hour
    metadata: dict[str, Any] = field(default_factory=dict)


class JWTHandler:
    """
    JWT token handler for access and refresh tokens.
    
    Features:
    - Secure token generation
    - Token validation and decoding
    - Token revocation support
    - Refresh token rotation
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

        # Token blacklist (in production, use Redis)
        self._revoked_tokens: set = set()

    def create_access_token(
        self,
        user: User,
        additional_claims: dict[str, Any] | None = None,
        expires_delta: timedelta | None = None
    ) -> str:
        """
        Create a new access token for a user.
        
        Args:
            user: User object
            additional_claims: Additional claims to include
            expires_delta: Custom expiration time
            
        Returns:
            JWT access token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)

        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "sub": user.id,
            "type": TokenType.ACCESS.value,
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "email": user.email,
            "username": user.username,
            "roles": user.roles,
            "permissions": user.permissions,
            "is_superuser": user.is_superuser,
            "tenant_id": user.tenant_id
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Access token created for user {user.id}")

        return token

    def create_refresh_token(
        self,
        user: User,
        session_id: str | None = None
    ) -> str:
        """
        Create a new refresh token for a user.
        
        Args:
            user: User object
            session_id: Optional session identifier
            
        Returns:
            JWT refresh token string
        """
        now = datetime.now(UTC)
        expire = now + timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": user.id,
            "type": TokenType.REFRESH.value,
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "session_id": session_id or str(uuid.uuid4())
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Refresh token created for user {user.id}")

        return token

    def verify_token(
        self,
        token: str,
        expected_type: TokenType | None = None
    ) -> dict[str, Any] | None:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            expected_type: Expected token type for validation
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check if token is revoked
            jti = payload.get("jti")
            if jti and jti in self._revoked_tokens:
                logger.warning(f"Revoked token used: {jti}")
                return None

            # Validate token type
            if expected_type:
                token_type = payload.get("type")
                if token_type != expected_type.value:
                    logger.warning(f"Token type mismatch: expected {expected_type.value}, got {token_type}")
                    return None

            return payload

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by adding it to the blacklist.
        
        Args:
            token: JWT token to revoke
            
        Returns:
            True if successfully revoked
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            jti = payload.get("jti")
            if jti:
                self._revoked_tokens.add(jti)
                logger.info(f"Token revoked: {jti}")
                return True
        except JWTError:
            pass
        return False

    def refresh_access_token(
        self,
        refresh_token: str,
        user: User
    ) -> tuple[str, str] | None:
        """
        Generate new access and refresh tokens using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            user: User object
            
        Returns:
            Tuple of (new_access_token, new_refresh_token) or None
        """
        payload = self.verify_token(refresh_token, TokenType.REFRESH)

        if not payload:
            return None

        if payload.get("sub") != user.id:
            logger.warning("Refresh token user mismatch")
            return None

        # Revoke old refresh token
        self.revoke_token(refresh_token)

        # Generate new tokens
        new_access = self.create_access_token(user)
        new_refresh = self.create_refresh_token(user, payload.get("session_id"))

        return new_access, new_refresh


class APIKeyManager:
    """
    API Key management system.
    
    Features:
    - Secure key generation
    - Key validation
    - Scope-based authorization
    - Rate limiting support
    """

    def __init__(self, prefix: str = "ieap_"):
        self.prefix = prefix
        # In production, this would be a database
        self._keys: dict[str, APIKey] = {}

    def generate_api_key(
        self,
        name: str,
        user_id: str,
        scopes: list[str],
        expires_in_days: int | None = None,
        rate_limit: int = 1000
    ) -> tuple[str, APIKey]:
        """
        Generate a new API key.
        
        Args:
            name: Human-readable key name
            user_id: Owner user ID
            scopes: List of authorized scopes
            expires_in_days: Optional expiration
            rate_limit: Rate limit per hour
            
        Returns:
            Tuple of (raw_key, APIKey object)
        """
        # Generate a secure random key
        raw_key = f"{self.prefix}{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw_key)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        api_key = APIKey(
            id=str(uuid.uuid4()),
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            scopes=scopes,
            expires_at=expires_at,
            rate_limit=rate_limit
        )

        self._keys[key_hash] = api_key
        logger.info(f"API key '{name}' created for user {user_id}")

        return raw_key, api_key

    def validate_api_key(
        self,
        raw_key: str,
        required_scopes: list[str] | None = None
    ) -> APIKey | None:
        """
        Validate an API key and check scopes.
        
        Args:
            raw_key: Raw API key string
            required_scopes: Required scopes for authorization
            
        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = self._hash_key(raw_key)
        api_key = self._keys.get(key_hash)

        if not api_key:
            logger.warning("Invalid API key attempted")
            return None

        if not api_key.is_active:
            logger.warning(f"Inactive API key used: {api_key.name}")
            return None

        if api_key.expires_at and api_key.expires_at < datetime.now():
            logger.warning(f"Expired API key used: {api_key.name}")
            return None

        if required_scopes:
            if not all(scope in api_key.scopes for scope in required_scopes):
                logger.warning(f"API key lacks required scopes: {required_scopes}")
                return None

        # Update last used
        api_key.last_used = datetime.now()

        return api_key

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key by ID"""
        for key_hash, api_key in self._keys.items():
            if api_key.id == key_id:
                api_key.is_active = False
                logger.info(f"API key revoked: {api_key.name}")
                return True
        return False

    def _hash_key(self, raw_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(raw_key.encode()).hexdigest()


class OAuth2ExchangeError(Exception):
    """OAuth2 token exchange failed."""


class OAuth2Handler:
    """
    OAuth2 integration for third-party authentication.
    
    Supports:
    - Google
    - Microsoft Azure AD
    - GitHub
    - Okta
    - Custom OIDC providers
    """

    def __init__(self, providers_config: dict[str, dict[str, str]]):
        self.providers = providers_config
        self._state_store: dict[str, dict] = {}

    def get_authorization_url(
        self,
        provider: str,
        redirect_uri: str,
        scopes: list[str] | None = None
    ) -> str | None:
        """
        Get OAuth2 authorization URL for a provider.
        
        Args:
            provider: OAuth2 provider name
            redirect_uri: Callback URL
            scopes: Requested scopes
            
        Returns:
            Authorization URL or None
        """
        if provider not in self.providers:
            logger.error(f"Unknown OAuth2 provider: {provider}")
            return None

        config = self.providers[provider]
        state = secrets.token_urlsafe(32)

        # Store state for validation
        self._state_store[state] = {
            "provider": provider,
            "redirect_uri": redirect_uri,
            "created_at": datetime.now()
        }

        # Build authorization URL based on provider
        if provider == "google":
            base_url = "https://accounts.google.com/o/oauth2/v2/auth"
            default_scopes = ["openid", "email", "profile"]
        elif provider == "microsoft":
            base_url = f"https://login.microsoftonline.com/{config.get('tenant_id', 'common')}/oauth2/v2/authorize"
            default_scopes = ["openid", "email", "profile"]
        elif provider == "github":
            base_url = "https://github.com/login/oauth/authorize"
            default_scopes = ["read:user", "user:email"]
        else:
            base_url = config.get("authorization_url", "")
            default_scopes = []

        scopes = scopes or default_scopes

        params = {
            "client_id": config.get("client_id"),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state
        }

        query_string = urllib.parse.urlencode(params)

        return f"{base_url}?{query_string}"

    async def exchange_code(
        self,
        provider: str,
        code: str,
        state: str,
        redirect_uri: str
    ) -> dict[str, Any] | None:
        """
        Exchange authorization code for tokens.
        
        Args:
            provider: OAuth2 provider
            code: Authorization code
            state: State parameter for validation
            redirect_uri: Callback URL
            
        Returns:
            Token response or None
        """
        import httpx

        # Validate state and reuse the original redirect URI used during authorization
        state_data = self._state_store.pop(state, None)
        if not state_data or state_data["provider"] != provider:
            logger.error("Invalid OAuth2 state")
            raise OAuth2ExchangeError("Invalid OAuth2 state")

        config = self.providers.get(provider, {})
        if not config:
            logger.error(f"No config found for provider: {provider}")
            raise OAuth2ExchangeError(f"No config found for provider: {provider}")

        token_url = config.get("token_url")
        if not token_url:
            logger.error(f"No token URL configured for provider: {provider}")
            raise OAuth2ExchangeError(f"No token URL configured for provider: {provider}")

        redirect_uri_to_use = config.get("redirect_uri") or redirect_uri
        logger.debug(f"Using redirect_uri for token exchange: {redirect_uri_to_use}")
        if not redirect_uri_to_use:
            logger.error("No redirect URI available for OAuth2 token exchange")
            raise OAuth2ExchangeError("No redirect URI available for OAuth2 token exchange")

        token_data = {
            "client_id": config.get("client_id"),
            "client_secret": config.get("client_secret"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri_to_use
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=token_data, headers=headers, timeout=30.0)
                response.raise_for_status()
                tokens = response.json()

                # Get user info
                userinfo_url = config.get("userinfo_url")
                if userinfo_url:
                    auth_headers = {"Authorization": f"Bearer {tokens.get('access_token')}"}
                    user_response = await client.get(userinfo_url, headers=auth_headers, timeout=30.0)
                    user_response.raise_for_status()
                    user_info = user_response.json()
                    tokens["user_info"] = user_info

                logger.info(f"Successfully exchanged OAuth2 code for provider: {provider}")
                return tokens
        except httpx.HTTPStatusError as e:
            response_text = e.response.text if e.response is not None else "<no response>"
            error_message = f"Token endpoint returned {e.response.status_code}: {response_text}"
            logger.info(
                f"Failed to exchange OAuth2 code for {provider}: {error_message}"
            )
            raise OAuth2ExchangeError(error_message)
        except Exception as e:
            logger.error(f"Failed to exchange OAuth2 code for {provider}: {e}")
            raise OAuth2ExchangeError(str(e))


class AuthenticationManager:
    """
    Central authentication manager coordinating all auth mechanisms.
    """

    def __init__(
        self,
        jwt_secret_key: str,
        jwt_algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        api_key_prefix: str = "ieap_",
        oauth2_providers: dict[str, dict[str, str]] | None = None
    ):
        self.jwt_handler = JWTHandler(
            secret_key=jwt_secret_key,
            algorithm=jwt_algorithm,
            access_token_expire_minutes=access_token_expire_minutes,
            refresh_token_expire_days=refresh_token_expire_days
        )

        self.api_key_manager = APIKeyManager(prefix=api_key_prefix)

        self.oauth2_handler = OAuth2Handler(oauth2_providers or {})

        # Password hashing
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto"
        )

        # User store (in production, this would be a database)
        self._users: dict[str, User] = {}

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        roles: list[str] | None = None,
        tenant_id: str | None = None
    ) -> User:
        """Create a new user"""
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            hashed_password=self.pwd_context.hash(password),
            roles=roles or ["user"],
            tenant_id=tenant_id
        )

        self._users[user.id] = user
        logger.info(f"User created: {user.email}")

        return user

    def authenticate_user(
        self,
        email: str,
        password: str
    ) -> User | None:
        """Authenticate user with email and password"""
        for user in self._users.values():
            if user.email == email:
                if self.pwd_context.verify(password, user.hashed_password):
                    user.last_login = datetime.now()
                    logger.info(f"User authenticated: {user.email}")
                    return user
                logger.warning(f"Failed authentication for: {email}")
                return None

        logger.warning(f"User not found: {email}")
        return None

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID"""
        return self._users.get(user_id)


# Convenience functions
_auth_manager: AuthenticationManager | None = None


def get_auth_manager() -> AuthenticationManager:
    """Get global authentication manager instance"""
    global _auth_manager
    if _auth_manager is None:
        from config import get_settings
        settings = get_settings()

        # Build OAuth2 providers config
        oauth2_providers = {}
        if settings.security.oauth2_enabled and "google" in settings.security.oauth2_providers:
            oauth2_providers["google"] = {
                "client_id": settings.security.oauth2_google_client_id,
                "client_secret": settings.security.oauth2_google_client_secret.get_secret_value(),
                "redirect_uri": settings.security.oauth2_google_redirect_uri,
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo"
            }

        _auth_manager = AuthenticationManager(
            jwt_secret_key=settings.security.jwt_secret_key.get_secret_value(),
            jwt_algorithm=settings.security.jwt_algorithm,
            access_token_expire_minutes=settings.security.jwt_access_token_expire_minutes,
            refresh_token_expire_days=settings.security.jwt_refresh_token_expire_days,
            api_key_prefix=settings.security.api_key_prefix,
            oauth2_providers=oauth2_providers
        )
    return _auth_manager


def create_access_token(user: User, **kwargs) -> str:
    """Create access token for user"""
    return get_auth_manager().jwt_handler.create_access_token(user, **kwargs)


def create_refresh_token(user: User, **kwargs) -> str:
    """Create refresh token for user"""
    return get_auth_manager().jwt_handler.create_refresh_token(user, **kwargs)


def verify_token(token: str, expected_type: TokenType | None = None) -> dict | None:
    """Verify and decode token"""
    return get_auth_manager().jwt_handler.verify_token(token, expected_type)


def get_current_user(token: str) -> User | None:
    """Get current user from token"""
    payload = verify_token(token, TokenType.ACCESS)
    if payload:
        return get_auth_manager().get_user_by_id(payload.get("sub"))
    return None
