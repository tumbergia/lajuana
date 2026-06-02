"""Equine permission tests.

Verifies:
- Guide cannot create/update/deactivate equines (403)
- Admin can create/update/deactivate equines (200)
- Unassigned cannot even read equines
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.api.deps import require_permissions
from app.common.enums import ROLE_PERMISSIONS, Permission, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError


class TestEquineRolePermissions:
    """Verify ROLE_PERMISSIONS mapping for equine operations."""

    def test_admin_has_all_equine_permissions(self) -> None:
        perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert Permission.EQUINE_READ in perms
        assert Permission.EQUINE_CREATE in perms
        assert Permission.EQUINE_UPDATE in perms

    def test_guide_has_read_only(self) -> None:
        perms = ROLE_PERMISSIONS[UserRole.GUIDE]
        assert Permission.EQUINE_READ in perms
        assert Permission.EQUINE_CREATE not in perms
        assert Permission.EQUINE_UPDATE not in perms

    def test_unassigned_has_no_equine_permissions(self) -> None:
        perms = ROLE_PERMISSIONS[UserRole.UNASSIGNED]
        assert Permission.EQUINE_READ not in perms
        assert Permission.EQUINE_CREATE not in perms
        assert Permission.EQUINE_UPDATE not in perms


class TestRequirePermissionsEquine:
    """Verify require_permissions dependency rejects/enforces correctly."""

    def test_guide_cannot_create_equine(self) -> None:
        dep = require_permissions(Permission.EQUINE_CREATE)
        user = SimpleNamespace(role=UserRole.GUIDE)
        with pytest.raises(ApiError) as exc:
            asyncio.run(dep(user))
        assert exc.value.status_code == 403
        assert exc.value.code == ErrorCode.AUTH_FORBIDDEN
        missing = exc.value.details.get("missing_permissions", [])
        assert Permission.EQUINE_CREATE.value in missing

    def test_guide_cannot_update_equine(self) -> None:
        dep = require_permissions(Permission.EQUINE_UPDATE)
        user = SimpleNamespace(role=UserRole.GUIDE)
        with pytest.raises(ApiError) as exc:
            asyncio.run(dep(user))
        assert exc.value.status_code == 403
        assert exc.value.code == ErrorCode.AUTH_FORBIDDEN
        missing = exc.value.details.get("missing_permissions", [])
        assert Permission.EQUINE_UPDATE.value in missing

    def test_guide_can_read_equine(self) -> None:
        dep = require_permissions(Permission.EQUINE_READ)
        user = SimpleNamespace(role=UserRole.GUIDE)
        result = asyncio.run(dep(user))
        assert result is user

    def test_admin_can_create_equine(self) -> None:
        dep = require_permissions(Permission.EQUINE_CREATE)
        user = SimpleNamespace(role=UserRole.ADMIN)
        result = asyncio.run(dep(user))
        assert result is user

    def test_admin_can_update_equine(self) -> None:
        dep = require_permissions(Permission.EQUINE_UPDATE)
        user = SimpleNamespace(role=UserRole.ADMIN)
        result = asyncio.run(dep(user))
        assert result is user
