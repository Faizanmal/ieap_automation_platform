"""
Enterprise Security Module

Comprehensive security features for the IEAP platform:
- JWT Authentication with refresh tokens
- API Key Management
- OAuth2 Integration
- Role-Based Access Control (RBAC)
- Data Encryption
- Audit Logging
- Rate Limiting
"""

from .audit import AuditEvent, AuditLogger, log_audit_event
from .authentication import (
    APIKeyManager,
    AuthenticationManager,
    JWTHandler,
    OAuth2Handler,
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_token,
)
from .authorization import (
    Permission,
    RBACManager,
    Role,
    require_permission,
    require_role,
)
from .encryption import (
    EncryptionService,
    decrypt_data,
    encrypt_data,
    hash_password,
    verify_password,
)

__all__ = [
    # Authentication
    "AuthenticationManager",
    "JWTHandler",
    "APIKeyManager",
    "OAuth2Handler",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",

    # Authorization
    "Permission",
    "Role",
    "RBACManager",
    "require_permission",
    "require_role",

    # Encryption
    "EncryptionService",
    "hash_password",
    "verify_password",
    "encrypt_data",
    "decrypt_data",

    # Audit
    "AuditLogger",
    "AuditEvent",
    "log_audit_event"
]
