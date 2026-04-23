"""
Role-Based Access Control (RBAC) System

Provides fine-grained authorization with:
- Hierarchical roles
- Granular permissions
- Resource-based access control
- Policy enforcement
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions"""

    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"

    # API key management
    API_KEY_CREATE = "api_key:create"
    API_KEY_READ = "api_key:read"
    API_KEY_REVOKE = "api_key:revoke"

    # ML Models
    MODEL_TRAIN = "model:train"
    MODEL_PREDICT = "model:predict"
    MODEL_DEPLOY = "model:deploy"
    MODEL_DELETE = "model:delete"
    MODEL_LIST = "model:list"

    # Data pipeline
    PIPELINE_CREATE = "pipeline:create"
    PIPELINE_RUN = "pipeline:run"
    PIPELINE_STOP = "pipeline:stop"
    PIPELINE_DELETE = "pipeline:delete"
    PIPELINE_MONITOR = "pipeline:monitor"

    # Decision engine
    DECISION_VIEW = "decision:view"
    DECISION_APPROVE = "decision:approve"
    DECISION_CONFIGURE = "decision:configure"

    # Orchestrator
    ORCHESTRATOR_VIEW = "orchestrator:view"
    ORCHESTRATOR_MANAGE = "orchestrator:manage"
    TASK_CREATE = "task:create"
    TASK_CANCEL = "task:cancel"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    REPORT_CREATE = "report:create"
    REPORT_SCHEDULE = "report:schedule"

    # System administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_AUDIT = "system:audit"

    # Tenant management (multi-tenant)
    TENANT_CREATE = "tenant:create"
    TENANT_MANAGE = "tenant:manage"


class Role(str, Enum):
    """Predefined system roles"""

    # Super admin - full system access
    SUPER_ADMIN = "super_admin"

    # Admin - manage users and configurations
    ADMIN = "admin"

    # Data scientist - ML model operations
    DATA_SCIENTIST = "data_scientist"

    # Data engineer - pipeline operations
    DATA_ENGINEER = "data_engineer"

    # Analyst - read-only analytics access
    ANALYST = "analyst"

    # Operator - monitoring and basic operations
    OPERATOR = "operator"

    # Developer - API access for integrations
    DEVELOPER = "developer"

    # User - basic access
    USER = "user"

    # Service account - for automated processes
    SERVICE = "service"


@dataclass
class RoleDefinition:
    """Definition of a role with its permissions"""
    name: str
    description: str
    permissions: set[Permission]
    inherits_from: list[str] = field(default_factory=list)
    is_system_role: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourcePolicy:
    """Resource-based access policy"""
    resource_type: str  # e.g., "model", "pipeline", "report"
    resource_id: str
    principal_type: str  # "user", "role", "group"
    principal_id: str
    permissions: set[Permission]
    conditions: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None


class RBACManager:
    """
    Role-Based Access Control Manager.
    
    Features:
    - Role hierarchy with inheritance
    - Fine-grained permissions
    - Resource-based policies
    - Custom role creation
    - Audit logging
    """

    # Default role definitions
    DEFAULT_ROLES: dict[str, RoleDefinition] = {
        Role.SUPER_ADMIN.value: RoleDefinition(
            name=Role.SUPER_ADMIN.value,
            description="Super administrator with full system access",
            permissions=set(Permission),  # All permissions
            is_system_role=True
        ),

        Role.ADMIN.value: RoleDefinition(
            name=Role.ADMIN.value,
            description="Administrator for user and system management",
            permissions={
                Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE,
                Permission.USER_DELETE, Permission.USER_LIST,
                Permission.API_KEY_CREATE, Permission.API_KEY_READ, Permission.API_KEY_REVOKE,
                Permission.MODEL_LIST, Permission.MODEL_PREDICT,
                Permission.PIPELINE_MONITOR,
                Permission.DECISION_VIEW,
                Permission.ORCHESTRATOR_VIEW,
                Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT,
                Permission.REPORT_CREATE, Permission.REPORT_SCHEDULE,
                Permission.SYSTEM_CONFIG, Permission.SYSTEM_MONITOR, Permission.SYSTEM_AUDIT
            },
            is_system_role=True
        ),

        Role.DATA_SCIENTIST.value: RoleDefinition(
            name=Role.DATA_SCIENTIST.value,
            description="Data scientist for ML operations",
            permissions={
                Permission.USER_READ,
                Permission.MODEL_TRAIN, Permission.MODEL_PREDICT, Permission.MODEL_DEPLOY,
                Permission.MODEL_DELETE, Permission.MODEL_LIST,
                Permission.PIPELINE_MONITOR,
                Permission.DECISION_VIEW,
                Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT,
                Permission.REPORT_CREATE
            },
            inherits_from=[Role.USER.value],
            is_system_role=True
        ),

        Role.DATA_ENGINEER.value: RoleDefinition(
            name=Role.DATA_ENGINEER.value,
            description="Data engineer for pipeline operations",
            permissions={
                Permission.USER_READ,
                Permission.MODEL_PREDICT, Permission.MODEL_LIST,
                Permission.PIPELINE_CREATE, Permission.PIPELINE_RUN, Permission.PIPELINE_STOP,
                Permission.PIPELINE_DELETE, Permission.PIPELINE_MONITOR,
                Permission.ORCHESTRATOR_VIEW,
                Permission.TASK_CREATE, Permission.TASK_CANCEL,
                Permission.ANALYTICS_VIEW
            },
            inherits_from=[Role.USER.value],
            is_system_role=True
        ),

        Role.ANALYST.value: RoleDefinition(
            name=Role.ANALYST.value,
            description="Analyst with read-only access to analytics",
            permissions={
                Permission.USER_READ,
                Permission.MODEL_LIST, Permission.MODEL_PREDICT,
                Permission.PIPELINE_MONITOR,
                Permission.DECISION_VIEW,
                Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT,
                Permission.REPORT_CREATE, Permission.REPORT_SCHEDULE
            },
            inherits_from=[Role.USER.value],
            is_system_role=True
        ),

        Role.OPERATOR.value: RoleDefinition(
            name=Role.OPERATOR.value,
            description="System operator for monitoring",
            permissions={
                Permission.USER_READ,
                Permission.MODEL_LIST,
                Permission.PIPELINE_MONITOR,
                Permission.ORCHESTRATOR_VIEW,
                Permission.SYSTEM_MONITOR,
                Permission.ANALYTICS_VIEW
            },
            inherits_from=[Role.USER.value],
            is_system_role=True
        ),

        Role.DEVELOPER.value: RoleDefinition(
            name=Role.DEVELOPER.value,
            description="Developer for API integrations",
            permissions={
                Permission.USER_READ,
                Permission.API_KEY_CREATE, Permission.API_KEY_READ,
                Permission.MODEL_PREDICT, Permission.MODEL_LIST,
                Permission.PIPELINE_RUN, Permission.PIPELINE_MONITOR,
                Permission.ANALYTICS_VIEW
            },
            inherits_from=[Role.USER.value],
            is_system_role=True
        ),

        Role.USER.value: RoleDefinition(
            name=Role.USER.value,
            description="Basic user access",
            permissions={
                Permission.USER_READ,
                Permission.MODEL_PREDICT,
                Permission.ANALYTICS_VIEW
            },
            is_system_role=True
        ),

        Role.SERVICE.value: RoleDefinition(
            name=Role.SERVICE.value,
            description="Service account for automated processes",
            permissions={
                Permission.MODEL_PREDICT, Permission.MODEL_LIST,
                Permission.PIPELINE_RUN, Permission.PIPELINE_MONITOR,
                Permission.TASK_CREATE,
                Permission.ANALYTICS_VIEW
            },
            is_system_role=True
        )
    }

    def __init__(self):
        self.roles: dict[str, RoleDefinition] = self.DEFAULT_ROLES.copy()
        self.resource_policies: list[ResourcePolicy] = []
        self._permission_cache: dict[str, set[Permission]] = {}

    def get_role_permissions(self, role_name: str) -> set[Permission]:
        """
        Get all permissions for a role including inherited permissions.
        
        Args:
            role_name: Name of the role
            
        Returns:
            Set of all permissions for the role
        """
        # Check cache
        if role_name in self._permission_cache:
            return self._permission_cache[role_name]

        role = self.roles.get(role_name)
        if not role:
            logger.warning(f"Role not found: {role_name}")
            return set()

        # Start with role's own permissions
        permissions = role.permissions.copy()

        # Add inherited permissions
        for parent_role in role.inherits_from:
            permissions.update(self.get_role_permissions(parent_role))

        # Cache and return
        self._permission_cache[role_name] = permissions
        return permissions

    def get_user_permissions(
        self,
        user_roles: list[str],
        user_permissions: list[str] | None = None
    ) -> set[Permission]:
        """
        Get all permissions for a user based on roles and direct permissions.
        
        Args:
            user_roles: List of user's roles
            user_permissions: Optional direct permissions
            
        Returns:
            Set of all user permissions
        """
        permissions: set[Permission] = set()

        # Add role-based permissions
        for role_name in user_roles:
            permissions.update(self.get_role_permissions(role_name))

        # Add direct permissions
        if user_permissions:
            for perm_str in user_permissions:
                try:
                    permissions.add(Permission(perm_str))
                except ValueError:
                    logger.warning(f"Invalid permission: {perm_str}")

        return permissions

    def has_permission(
        self,
        user_roles: list[str],
        user_permissions: list[str] | None,
        required_permission: Permission
    ) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_roles: User's roles
            user_permissions: User's direct permissions
            required_permission: Required permission
            
        Returns:
            True if user has the permission
        """
        permissions = self.get_user_permissions(user_roles, user_permissions)
        return required_permission in permissions

    def has_any_permission(
        self,
        user_roles: list[str],
        user_permissions: list[str] | None,
        required_permissions: list[Permission]
    ) -> bool:
        """Check if user has any of the required permissions"""
        permissions = self.get_user_permissions(user_roles, user_permissions)
        return bool(permissions.intersection(required_permissions))

    def has_all_permissions(
        self,
        user_roles: list[str],
        user_permissions: list[str] | None,
        required_permissions: list[Permission]
    ) -> bool:
        """Check if user has all required permissions"""
        permissions = self.get_user_permissions(user_roles, user_permissions)
        return all(p in permissions for p in required_permissions)

    def create_custom_role(
        self,
        name: str,
        description: str,
        permissions: set[Permission],
        inherits_from: list[str] | None = None
    ) -> RoleDefinition:
        """
        Create a custom role.
        
        Args:
            name: Role name
            description: Role description
            permissions: Role permissions
            inherits_from: Parent roles to inherit from
            
        Returns:
            Created role definition
        """
        if name in self.roles:
            raise ValueError(f"Role already exists: {name}")

        role = RoleDefinition(
            name=name,
            description=description,
            permissions=permissions,
            inherits_from=inherits_from or [],
            is_system_role=False
        )

        self.roles[name] = role
        self._permission_cache.pop(name, None)

        logger.info(f"Custom role created: {name}")
        return role

    def add_resource_policy(
        self,
        resource_type: str,
        resource_id: str,
        principal_type: str,
        principal_id: str,
        permissions: set[Permission],
        conditions: dict[str, Any] | None = None
    ) -> ResourcePolicy:
        """
        Add a resource-based access policy.
        
        Args:
            resource_type: Type of resource (model, pipeline, etc.)
            resource_id: Resource identifier
            principal_type: Type of principal (user, role, group)
            principal_id: Principal identifier
            permissions: Allowed permissions
            conditions: Optional conditions
            
        Returns:
            Created policy
        """
        policy = ResourcePolicy(
            resource_type=resource_type,
            resource_id=resource_id,
            principal_type=principal_type,
            principal_id=principal_id,
            permissions=permissions,
            conditions=conditions or {}
        )

        self.resource_policies.append(policy)
        logger.info(f"Resource policy added for {resource_type}/{resource_id}")

        return policy

    def check_resource_access(
        self,
        resource_type: str,
        resource_id: str,
        user_id: str,
        user_roles: list[str],
        required_permission: Permission
    ) -> bool:
        """
        Check if user has access to a specific resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            user_id: User identifier
            user_roles: User's roles
            required_permission: Required permission
            
        Returns:
            True if access is allowed
        """
        # Check global permissions first
        if self.has_permission(user_roles, None, required_permission):
            return True

        # Check resource-specific policies
        for policy in self.resource_policies:
            if policy.resource_type != resource_type:
                continue
            if policy.resource_id != resource_id and policy.resource_id != "*":
                continue
            if required_permission not in policy.permissions:
                continue

            # Check principal
            if policy.principal_type == "user" and policy.principal_id == user_id:
                return True
            if policy.principal_type == "role" and policy.principal_id in user_roles:
                return True

        return False


# Global RBAC manager instance
_rbac_manager: RBACManager | None = None


def get_rbac_manager() -> RBACManager:
    """Get global RBAC manager instance"""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


def require_permission(permission: Permission):
    """
    Decorator to require a permission for a function.
    
    Usage:
        @require_permission(Permission.MODEL_PREDICT)
        async def predict(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from context (implementation depends on framework)
            user = kwargs.get("current_user")
            if not user:
                raise PermissionError("Authentication required")

            rbac = get_rbac_manager()
            if not rbac.has_permission(
                user.roles,
                user.permissions,
                permission
            ):
                logger.warning(f"Permission denied: {permission.value} for user {user.id}")
                raise PermissionError(f"Permission denied: {permission.value}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: Role):
    """
    Decorator to require a role for a function.
    
    Usage:
        @require_role(Role.ADMIN)
        async def admin_function(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user:
                raise PermissionError("Authentication required")

            if role.value not in user.roles:
                logger.warning(f"Role required: {role.value} for user {user.id}")
                raise PermissionError(f"Role required: {role.value}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
