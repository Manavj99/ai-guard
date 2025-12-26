"""Enterprise Features for AI-Guard.

This module provides enterprise-grade features including:
- Multi-tenant architecture
- Role-Based Access Control (RBAC)
- JWT authentication
- Audit logging and compliance
"""

import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles in the system."""

    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class Permission(Enum):
    """System permissions."""

    READ_CODE = "read_code"
    WRITE_CODE = "write_code"
    EXECUTE_ANALYSIS = "execute_analysis"
    VIEW_REPORTS = "view_reports"
    MANAGE_USERS = "manage_users"
    MANAGE_TENANTS = "manage_tenants"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SECURITY = "manage_security"
    MANAGE_SETTINGS = "manage_settings"


class TenantStatus(Enum):
    """Tenant status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    INACTIVE = "inactive"


@dataclass
class User:
    """User entity."""

    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    tenant_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tenant:
    """Tenant entity."""

    id: str
    name: str
    domain: str
    status: TenantStatus = TenantStatus.ACTIVE
    max_users: int = 100
    created_at: datetime = field(default_factory=datetime.now)
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLog:
    """Audit log entry."""

    id: str
    user_id: str
    tenant_id: str
    action: str
    resource: str
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


class RoleManager:
    """Manages roles and permissions."""

    def __init__(self):
        """Initialize the role manager."""
        self._lock = threading.RLock()
        self.roles: Dict[str, UserRole] = {role.value: role for role in UserRole}
        self.role_permissions: Dict[UserRole, Set[Permission]] = {
            UserRole.ADMIN: {
                Permission.READ_CODE,
                Permission.WRITE_CODE,
                Permission.EXECUTE_ANALYSIS,
                Permission.VIEW_REPORTS,
                Permission.MANAGE_USERS,
                Permission.MANAGE_TENANTS,
                Permission.VIEW_AUDIT_LOGS,
                Permission.MANAGE_SECURITY,
                Permission.MANAGE_SETTINGS,
            },
            UserRole.MANAGER: {
                Permission.READ_CODE,
                Permission.EXECUTE_ANALYSIS,
                Permission.VIEW_REPORTS,
                Permission.MANAGE_USERS,
                Permission.VIEW_AUDIT_LOGS,
            },
            UserRole.DEVELOPER: {
                Permission.READ_CODE,
                Permission.WRITE_CODE,
                Permission.EXECUTE_ANALYSIS,
                Permission.VIEW_REPORTS,
            },
            UserRole.VIEWER: {Permission.READ_CODE, Permission.VIEW_REPORTS},
            UserRole.AUDITOR: {Permission.READ_CODE, Permission.VIEW_AUDIT_LOGS},
        }

        logger.info("Role Manager initialized")

    def get_permissions(self, role: UserRole) -> Set[Permission]:
        """Get permissions for a role."""
        with self._lock:
            return self.role_permissions.get(role, set()).copy()

    def has_permission(self, role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        with self._lock:
            return permission in self.role_permissions.get(role, set())

    def add_permission(self, role: UserRole, permission: Permission) -> None:
        """Add a permission to a role."""
        with self._lock:
            if role not in self.role_permissions:
                self.role_permissions[role] = set()
            self.role_permissions[role].add(permission)
            logger.info(f"Added permission {permission.value} to role {role.value}")


class UserManager:
    """Manages users and authentication."""

    def __init__(self, role_manager: Optional[RoleManager] = None):
        """Initialize the user manager."""
        self._lock = threading.RLock()
        self.role_manager = role_manager or RoleManager()
        self.users: Dict[str, User] = {}
        self.user_tokens: Dict[str, str] = {}  # token -> user_id
        self.token_expiry: Dict[str, datetime] = {}  # token -> expiry

        logger.info("User Manager initialized")

    def create_user(
        self, username: str, email: str, full_name: str, role: UserRole, tenant_id: str
    ) -> User:
        """Create a new user."""
        with self._lock:
            user_id = str(uuid.uuid4())
            user = User(
                id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                tenant_id=tenant_id,
                permissions=self.role_manager.get_permissions(role),
            )

            self.users[user_id] = user
            logger.info(f"Created user: {username} ({role.value})")
            return user

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate a user and return a JWT token."""
        with self._lock:
            # Find user by username
            user = None
            for u in self.users.values():
                if u.username == username and u.is_active:
                    user = u
                    break

            if not user:
                logger.warning(f"Authentication failed for user: {username}")
                return None

            # Simple password validation (in production, use proper hashing)
            if password != "password":  # Default password for demo
                logger.warning(f"Invalid password for user: {username}")
                return None

            # Generate JWT token (simplified)
            token = f"jwt_{user.id}_{int(time.time())}"
            self.user_tokens[token] = user.id
            self.token_expiry[token] = datetime.now() + timedelta(hours=24)

            user.last_login = datetime.now()
            logger.info(f"User authenticated: {username}")
            return token

    def validate_token(self, token: str) -> Optional[User]:
        """Validate a JWT token and return the user."""
        with self._lock:
            if token not in self.user_tokens:
                return None

            # Check token expiry
            if token in self.token_expiry:
                if datetime.now() > self.token_expiry[token]:
                    # Token expired
                    del self.user_tokens[token]
                    del self.token_expiry[token]
                    return None

            user_id = self.user_tokens[token]
            return self.users.get(user_id)

    def revoke_token(self, token: str) -> bool:
        """Revoke a user token."""
        with self._lock:
            if token in self.user_tokens:
                del self.user_tokens[token]
                if token in self.token_expiry:
                    del self.token_expiry[token]
                logger.info("Token revoked")
                return True
            return False

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        with self._lock:
            return self.users.get(user_id)

    def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Update a user's role."""
        with self._lock:
            user = self.users.get(user_id)
            if not user:
                return False

            user.role = new_role
            user.permissions = self.role_manager.get_permissions(new_role)
            logger.info(f"Updated user {user.username} role to {new_role.value}")
            return True


class TenantManager:
    """Manages tenants (multi-tenancy)."""

    def __init__(self):
        """Initialize the tenant manager."""
        self._lock = threading.RLock()
        self.tenants: Dict[str, Tenant] = {}

        logger.info("Tenant Manager initialized")

    def create_tenant(self, name: str, domain: str, max_users: int = 100) -> Tenant:
        """Create a new tenant."""
        with self._lock:
            tenant_id = str(uuid.uuid4())
            tenant = Tenant(id=tenant_id, name=name, domain=domain, max_users=max_users)

            self.tenants[tenant_id] = tenant
            logger.info(f"Created tenant: {name} ({domain})")
            return tenant

    def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get a tenant by ID."""
        with self._lock:
            return self.tenants.get(tenant_id)

    def update_tenant_status(self, tenant_id: str, status: TenantStatus) -> bool:
        """Update tenant status."""
        with self._lock:
            tenant = self.tenants.get(tenant_id)
            if not tenant:
                return False

            tenant.status = status
            logger.info(f"Updated tenant {tenant.name} status to {status.value}")
            return True

    def get_tenant_users_count(self, tenant_id: str, user_manager: UserManager) -> int:
        """Get the number of users in a tenant."""
        with self._lock:
            count = 0
            for user in user_manager.users.values():
                if user.tenant_id == tenant_id:
                    count += 1
            return count


class AuditManager:
    """Manages audit logging and compliance."""

    def __init__(self):
        """Initialize the audit manager."""
        self._lock = threading.RLock()
        self.audit_logs: List[AuditLog] = []

        logger.info("Audit Manager initialized")

    def log_action(
        self,
        user_id: str,
        tenant_id: str,
        action: str,
        resource: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log a user action."""
        with self._lock:
            log_id = str(uuid.uuid4())
            audit_log = AuditLog(
                id=log_id,
                user_id=user_id,
                tenant_id=tenant_id,
                action=action,
                resource=resource,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                details=details or {},
            )

            self.audit_logs.append(audit_log)
            logger.info(f"Audit log: {action} on {resource} by user {user_id}")
            return audit_log

    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLog]:
        """Get audit logs with optional filters."""
        with self._lock:
            logs = self.audit_logs.copy()

            # Apply filters
            if user_id:
                logs = [log for log in logs if log.user_id == user_id]
            if tenant_id:
                logs = [log for log in logs if log.tenant_id == tenant_id]
            if action:
                logs = [log for log in logs if log.action == action]
            if start_date:
                logs = [log for log in logs if log.timestamp >= start_date]
            if end_date:
                logs = [log for log in logs if log.timestamp <= end_date]

            return logs

    def generate_compliance_report(
        self, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate a compliance report for a tenant."""
        with self._lock:
            logs = self.get_audit_logs(
                tenant_id=tenant_id, start_date=start_date, end_date=end_date
            )

            total_actions = len(logs)
            successful_actions = len([log for log in logs if log.success])
            failed_actions = total_actions - successful_actions

            # Group by action type
            action_counts = {}
            for log in logs:
                action_counts[log.action] = action_counts.get(log.action, 0) + 1

            # Group by user
            user_counts = {}
            for log in logs:
                user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1

            return {
                "tenant_id": tenant_id,
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "summary": {
                    "total_actions": total_actions,
                    "successful_actions": successful_actions,
                    "failed_actions": failed_actions,
                    "success_rate": (successful_actions / max(total_actions, 1)) * 100,
                },
                "action_breakdown": action_counts,
                "user_activity": user_counts,
                "generated_at": datetime.now().isoformat(),
            }


class EnterpriseSystem:
    """Main enterprise system orchestrating all enterprise features."""

    def __init__(self):
        """Initialize the enterprise system."""
        self._lock = threading.RLock()

        # Initialize managers
        self.role_manager = RoleManager()
        self.user_manager = UserManager(self.role_manager)
        self.tenant_manager = TenantManager()
        self.audit_manager = AuditManager()

        # Create default tenant and admin user
        self._create_default_setup()

        logger.info("Enterprise System initialized")

    def _create_default_setup(self):
        """Create default tenant and admin user."""
        with self._lock:
            # Create default tenant
            default_tenant = self.tenant_manager.create_tenant(
                name="Default Organization", domain="default.local", max_users=1000
            )

            # Create admin user
            admin_user = self.user_manager.create_user(
                username="admin",
                email="admin@default.local",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                tenant_id=default_tenant.id,
            )

            # Log the setup
            self.audit_manager.log_action(
                user_id=admin_user.id,
                tenant_id=default_tenant.id,
                action="system_initialization",
                resource="enterprise_system",
                details={"setup_type": "default"},
            )

            logger.info("Default tenant and admin user created")

    def authenticate_and_authorize(
        self, token: str, permission: Permission
    ) -> Optional[User]:
        """Authenticate user and check authorization."""
        with self._lock:
            user = self.user_manager.validate_token(token)
            if not user:
                return None

            if permission not in user.permissions:
                logger.warning(
                    f"User {user.username} lacks permission: {permission.value}"
                )
                return None

            return user

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get enterprise system statistics."""
        with self._lock:
            return {
                "tenants": {
                    "total": len(self.tenant_manager.tenants),
                    "active": len(
                        [
                            t
                            for t in self.tenant_manager.tenants.values()
                            if t.status == TenantStatus.ACTIVE
                        ]
                    ),
                },
                "users": {
                    "total": len(self.user_manager.users),
                    "active": len(
                        [u for u in self.user_manager.users.values() if u.is_active]
                    ),
                },
                "audit_logs": {
                    "total": len(self.audit_manager.audit_logs),
                    "last_24h": len(
                        [
                            log
                            for log in self.audit_manager.audit_logs
                            if log.timestamp > datetime.now() - timedelta(hours=24)
                        ]
                    ),
                },
                "roles": {"total": len(UserRole), "permissions": len(Permission)},
            }


# Global instance
_enterprise_system: Optional[EnterpriseSystem] = None
_enterprise_lock = threading.RLock()


def get_enterprise_system() -> EnterpriseSystem:
    """Get the global enterprise system instance."""
    global _enterprise_system
    with _enterprise_lock:
        if _enterprise_system is None:
            _enterprise_system = EnterpriseSystem()
        return _enterprise_system


def initialize_enterprise() -> bool:
    """Initialize the enterprise system."""
    try:
        get_enterprise_system()
        logger.info("Enterprise system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Enterprise system initialization failed: {e}")
        return False


if __name__ == "__main__":
    # Test enterprise system
    print("🏢 Testing AI-Guard Enterprise Features")

    success = initialize_enterprise()
    if success:
        print("✅ Enterprise system initialized successfully")

        enterprise_system = get_enterprise_system()

        # Test authentication
        token = enterprise_system.user_manager.authenticate_user("admin", "password")
        if token:
            print("✅ Admin authentication successful")

            # Test authorization
            user = enterprise_system.authenticate_and_authorize(
                token, Permission.MANAGE_USERS
            )
            if user:
                print(f"✅ Authorization successful for user: {user.username}")

            # Test audit logging
            enterprise_system.audit_manager.log_action(
                user_id=user.id,
                tenant_id=user.tenant_id,
                action="test_action",
                resource="test_resource",
                details={"test": True},
            )
            print("✅ Audit logging successful")

        # Show statistics
        stats = enterprise_system.get_system_statistics()
        print(f"📊 Enterprise Statistics: {json.dumps(stats, indent=2)}")
    else:
        print("❌ Enterprise system initialization failed")
