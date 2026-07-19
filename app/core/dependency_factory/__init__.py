"""
Dependency-injection wiring for the whole app, split by domain:
- `auth.py` — user/refresh-token repositories, register/login/logout/refresh/
  reset-password/Google-OAuth service factories
- `rbac.py` — role/permission repositories and services
- `users.py` — user-management service (spans both domains above)

Everything is re-exported here so existing `from app.core.dependency_factory
import get_x_service` call sites across the app are unaffected by the
internal split.
"""

from app.core.dependency_factory.auth import (
    get_google_oauth_service,
    get_login_service,
    get_logout_service,
    get_password_reset_service,
    get_refresh_service,
    get_refresh_token_repository,
    get_register_service,
    get_reset_password_service,
    get_user_repository,
    get_verify_mail_service,
)
from app.core.dependency_factory.rbac import (
    get_permission_repository,
    get_permission_service,
    get_role_repository,
    get_role_service,
)
from app.core.dependency_factory.tenant import get_tenant_repository, get_tenant_service
from app.core.dependency_factory.users import get_user_management_service

__all__ = [
    "get_user_repository",
    "get_refresh_token_repository",
    "get_register_service",
    "get_login_service",
    "get_logout_service",
    "get_refresh_service",
    "get_reset_password_service",
    "get_verify_mail_service",
    "get_password_reset_service",
    "get_google_oauth_service",
    "get_role_repository",
    "get_permission_repository",
    "get_role_service",
    "get_permission_service",
    "get_user_management_service",
    "get_tenant_repository",
    "get_tenant_service",
]
