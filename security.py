import os
import secrets
import re
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

_SHA256_HEX_RE = re.compile(r"^[a-fA-F0-9]{64}$")


def _is_legacy_sha256_hash(value: str) -> bool:
    """Detect legacy SHA-256 hex digests used during earlier testing."""
    return bool(_SHA256_HEX_RE.match(str(value or "").strip()))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    plain_password = (plain_password or "")[:72]  # bcrypt 72-byte input limit
    hashed_password = str(hashed_password or "").strip()

    # Backwards compatibility: allow legacy SHA-256 hashes to verify so users can
    # still sign in, then we can upgrade their hash to bcrypt on successful login.
    if _is_legacy_sha256_hash(hashed_password):
        import hashlib

        return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == hashed_password

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
     
def get_password_hash(password: str) -> str:
    """Hash a password."""
    password = (password or "")[:72]  # bcrypt 72-byte input limit
    return pwd_context.hash(password)


def password_hash_needs_upgrade(hashed_password: str) -> bool:
    """Return True if the stored hash should be upgraded to the current scheme."""
    hashed_password = str(hashed_password or "").strip()
    if _is_legacy_sha256_hash(hashed_password):
        return True
    try:
        return pwd_context.needs_update(hashed_password)
    except Exception:
        # Unknown hash format: force upgrade after verifying via some fallback.
        return True

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def generate_secure_session_id() -> str:
    """Generate a secure session ID."""
    return secrets.token_urlsafe(32)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength (bcrypt-compatible)."""
    # Check bcrypt 72-byte limit
    if len(password.encode('utf-8')) > 72:
        return False, "Password must be less than 72 characters long"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"
