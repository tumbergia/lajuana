DEFAULT_RESERVATION_MIN_DAYS = 7
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
BCRYPT_ROUNDS = 12
TOKEN_TYPE_BEARER = "bearer"
AUTH_HEADER_NAME = "Authorization"
PASSWORD_HASH_SCHEME = "bcrypt"
PARTICIPANT_FORM_LINK_EXPIRY_HOURS = 48
PARTICIPANT_FORM_TOKEN_BYTES = 32


def build_code(prefix: str = "RES") -> str:
    """Genera código único con prefijo, fecha y token aleatorio."""
    import secrets
    from datetime import UTC, datetime

    return f"{prefix}-{datetime.now(UTC).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
