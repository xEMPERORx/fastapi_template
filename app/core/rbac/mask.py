"""
Codec + SQLAlchemy column type for the 256-bit permission mask.

A mask is stored as a fixed-width big-endian byte string (`BYTEA` on
Postgres, `BLOB` on the in-memory SQLite the test suite uses) rather than a
numeric/integer-array column: nothing in this design ever needs SQL-side
bitwise filtering (every mask operation happens in Python against a handful
of already-fetched rows — see `app.core.rbac.effective_mask` and
`RoleService.create_role`'s subset check), so there's no reason to pay for a
DB-side integer representation. Using raw bytes also means DB storage and the
JWT's hex-encoded `perm_mask` claim (see `app.schema.auth.TokenPayload`) share
one code path.
"""

from sqlalchemy import LargeBinary
from sqlalchemy.types import TypeDecorator

MASK_BYTES = 32  # 256 bits


def mask_to_bytes(mask: int | None) -> bytes:
    return (mask or 0).to_bytes(MASK_BYTES, "big")


def bytes_to_mask(data: bytes | None) -> int:
    return int.from_bytes(data, "big") if data else 0


def mask_to_hex(mask: int | None) -> str:
    return mask_to_bytes(mask).hex()


def hex_to_mask(value: str | None) -> int:
    return int.from_bytes(bytes.fromhex(value), "big") if value else 0


class PermissionMaskType(TypeDecorator):
    """A Python `int` bitmask, stored as `MASK_BYTES` big-endian bytes."""

    impl = LargeBinary(MASK_BYTES)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return mask_to_bytes(value)

    def process_result_value(self, value, dialect):
        return bytes_to_mask(value)
