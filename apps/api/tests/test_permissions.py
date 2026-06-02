import asyncio
from types import SimpleNamespace

import pytest

from app.api.deps import require_permissions
from app.common.enums import ROLE_PERMISSIONS, Permission, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError


def test_role_permissions_unassigned_only_self_auth() -> None:
    perms = ROLE_PERMISSIONS[UserRole.UNASSIGNED]
    assert Permission.AUTH_SELF_READ in perms
    assert Permission.AUTH_SELF_UPDATE_PASSWORD in perms
    assert Permission.RESERVATION_CONFIRM not in perms


def test_role_permissions_guide_no_confirm_reservation() -> None:
    perms = ROLE_PERMISSIONS[UserRole.GUIDE]
    assert Permission.RESERVATION_CONFIRM not in perms
    assert Permission.ASSIGNMENT_CREATE not in perms
    assert Permission.ASSIGNMENT_UPDATE not in perms
    assert Permission.ASSIGNMENT_READ in perms
    assert Permission.LOG_CREATE in perms


def test_require_permissions_denies_missing_permission() -> None:
    dep = require_permissions(Permission.RESERVATION_CONFIRM)
    user = SimpleNamespace(role=UserRole.GUIDE)
    with pytest.raises(ApiError) as exc:
        asyncio.run(dep(user))
    assert exc.value.status_code == 403
    assert exc.value.code == ErrorCode.AUTH_FORBIDDEN


def test_require_permissions_allows_when_permission_exists() -> None:
    dep = require_permissions(Permission.LOG_CREATE)
    user = SimpleNamespace(role=UserRole.GUIDE)
    result = asyncio.run(dep(user))
    assert result is user
