"""
FastAPI Dependency Injection

Provides reusable dependencies for:
- Authentication
- Authorization
- Database sessions
- Caching
- Rate limiting
"""

import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)


# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_request_id(request: Request) -> str:
    """Get request ID from request state"""
    return getattr(request.state, "request_id", "unknown")


async def get_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
) -> str | None:
    """Extract bearer token from request"""
    if credentials:
        return credentials.credentials
    return None


async def get_api_key(
    api_key: str | None = Depends(api_key_header)
) -> str | None:
    """Extract API key from request"""
    return api_key


async def get_current_user(
    token: str | None = Depends(get_token),
    api_key: str | None = Depends(get_api_key)
):
    """
    Get current authenticated user from token or API key.
    
    Returns user object or raises 401 if not authenticated.
    """
    from security.authentication import TokenType, get_auth_manager, verify_token

    auth_manager = get_auth_manager()

    # Try JWT token first
    if token:
        payload = verify_token(token, TokenType.ACCESS)
        if payload:
            user = auth_manager.get_user_by_id(payload.get("sub"))
            if user and user.is_active:
                return user

    # Try API key
    if api_key:
        api_key_obj = auth_manager.api_key_manager.validate_api_key(api_key)
        if api_key_obj:
            user = auth_manager.get_user_by_id(api_key_obj.user_id)
            if user and user.is_active:
                return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """Get current user and verify they are active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


async def get_current_verified_user(
    current_user = Depends(get_current_active_user)
):
    """Get current user and verify email is confirmed"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


async def get_current_superuser(
    current_user = Depends(get_current_active_user)
):
    """Get current user and verify they are superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return current_user


def require_permission(permission: str):
    """
    Dependency factory for permission-based access control.
    
    Usage:
        @router.get("/models")
        async def list_models(
            user = Depends(require_permission("model:list"))
        ):
            ...
    """
    async def permission_checker(
        current_user = Depends(get_current_active_user)
    ):
        from security.authorization import Permission, get_rbac_manager

        rbac = get_rbac_manager()

        try:
            perm = Permission(permission)
        except ValueError:
            logger.error(f"Invalid permission: {permission}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid permission configuration"
            )

        if not rbac.has_permission(
            current_user.roles,
            current_user.permissions,
            perm
        ):
            logger.warning(
                f"Permission denied: {permission} for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )

        return current_user

    return permission_checker


def require_role(role: str):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            user = Depends(require_role("admin"))
        ):
            ...
    """
    async def role_checker(
        current_user = Depends(get_current_active_user)
    ):
        if role not in current_user.roles:
            logger.warning(
                f"Role required: {role} for user {current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}"
            )
        return current_user

    return role_checker


def require_any_role(roles: list[str]):
    """
    Dependency factory requiring any of the specified roles.
    """
    async def role_checker(
        current_user = Depends(get_current_active_user)
    ):
        if not any(role in current_user.roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(roles)}"
            )
        return current_user

    return role_checker


# Database dependency (placeholder - implement with actual database)
async def get_db_session():
    """
    Get database session.
    
    In production, this would yield a SQLAlchemy session.
    """
    # from database import SessionLocal
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    yield None


# Cache dependency (placeholder - implement with Redis)
async def get_cache():
    """
    Get cache client.
    
    In production, this would return a Redis client.
    """
    # from cache import redis_client
    # return redis_client
    return


# Pagination dependency
class PaginationParams:
    """Common pagination parameters"""

    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ):
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )
        if page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be >= 1"
            )

        self.page = page
        self.page_size = min(page_size, max_page_size)
        self.offset = (page - 1) * self.page_size
        self.limit = self.page_size


def get_pagination(
    page: int = 1,
    page_size: int = 20
) -> PaginationParams:
    """Get pagination parameters"""
    return PaginationParams(page=page, page_size=page_size)


# Optional authentication (for public endpoints that show more data when authenticated)
async def get_optional_user(
    token: str | None = Depends(get_token),
    api_key: str | None = Depends(get_api_key)
):
    """Get current user if authenticated, None otherwise"""
    try:
        from security.authentication import TokenType, get_auth_manager, verify_token

        auth_manager = get_auth_manager()

        if token:
            payload = verify_token(token, TokenType.ACCESS)
            if payload:
                user = auth_manager.get_user_by_id(payload.get("sub"))
                if user and user.is_active:
                    return user

        if api_key:
            api_key_obj = auth_manager.api_key_manager.validate_api_key(api_key)
            if api_key_obj:
                user = auth_manager.get_user_by_id(api_key_obj.user_id)
                if user and user.is_active:
                    return user
    except Exception:
        pass

    return None
