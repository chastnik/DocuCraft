"""Security utilities: JWT, password hashing."""

from datetime import datetime, timedelta
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import bcrypt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_password_to_72_bytes(password: str) -> str:
    """Truncate password to 72 bytes, ensuring we don't break UTF-8 characters."""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= 72:
        return password
    
    # Truncate to 72 bytes
    password_bytes = password_bytes[:72]
    # Remove any incomplete UTF-8 sequences at the end
    while password_bytes and (password_bytes[-1] & 0x80) and not (password_bytes[-1] & 0x40):
        password_bytes = password_bytes[:-1]
    
    return password_bytes.decode('utf-8', errors='ignore')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Bcrypt has a maximum password length of 72 bytes.
    We truncate the password to 72 bytes if it's longer.
    """
    # Bcrypt limitation: max 72 bytes
    plain_password = _truncate_password_to_72_bytes(plain_password)
    # Use bcrypt directly to avoid passlib initialization issues
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception:
        # Fallback to passlib for compatibility
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password.
    
    Bcrypt has a maximum password length of 72 bytes.
    We truncate the password to 72 bytes if it's longer.
    """
    # Bcrypt limitation: max 72 bytes
    password = _truncate_password_to_72_bytes(password)
    # Use bcrypt directly to avoid passlib initialization issues
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None

