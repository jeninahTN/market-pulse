"""
Authentication utilities for enhanced security and user experience
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re
import fastapi
from sqlalchemy.orm import Session

from app import models
from app.security import generate_secure_session_id

try:
    import redis
except Exception:
    redis = None


_REDIS_CLIENT = None


def _get_redis_client():
    global _REDIS_CLIENT
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT

    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url or redis is None:
        return None

    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        _REDIS_CLIENT = client
        return _REDIS_CLIENT
    except Exception as exc:
        print(f"Redis unavailable, falling back to DB state: {exc}")
        return None

def validate_email_format(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone_format(phone: str) -> bool:
    """Validate phone number format (Uganda format)"""
    # Remove all non-digit characters
    clean_phone = re.sub(r'\D', '', phone)
    
    # Uganda phone numbers: +256 7XX XXXXXX or 07XX XXXXXX
    if clean_phone.startswith('256'):
        return len(clean_phone) == 12 and clean_phone[3] in '7'
    elif clean_phone.startswith('0'):
        return len(clean_phone) == 10 and clean_phone[1] in '7'
    
    return False

def format_phone_number(phone: str) -> str:
    """Format phone number to standard format"""
    clean_phone = re.sub(r'\D', '', phone)
    
    if clean_phone.startswith('256'):
        return f"+{clean_phone}"
    elif clean_phone.startswith('0'):
        return f"+256{clean_phone[1:]}"
    
    return f"+256{clean_phone}"

def generate_password_reset_token(user_id: int, email: str, db: Session) -> str:
    """Generate secure password reset token"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=1)  # 1 hour expiry

    redis_client = _get_redis_client()
    if redis_client:
        key = f"reset_token:{token}"
        payload = f"{user_id}|{email}|{int(expires_at.timestamp())}"
        ttl = int((expires_at - datetime.now()).total_seconds())
        redis_client.setex(key, max(ttl, 1), payload)
        return token

    token_row = models.PasswordResetToken(
        token=token,
        user_id=user_id,
        contact=email,
        created_at=datetime.now(),
        expires_at=expires_at,
    )
    db.add(token_row)
    db.commit()
    return token

def validate_reset_token(token: str, db: Session) -> Optional[Dict[str, Any]]:
    """Validate password reset token"""
    redis_client = _get_redis_client()
    if redis_client:
        value = redis_client.get(f"reset_token:{token}")
        if not value:
            return None
        user_id, email, expires_epoch = value.split("|")
        expires_at = datetime.fromtimestamp(int(expires_epoch))
        if datetime.now() > expires_at:
            redis_client.delete(f"reset_token:{token}")
            return None
        return {"user_id": int(user_id), "email": email, "expires_at": expires_at}

    token_row = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token,
        models.PasswordResetToken.used_at.is_(None),
    ).first()
    if not token_row:
        return None
    if datetime.now() > token_row.expires_at:
        db.delete(token_row)
        db.commit()
        return None
    return {"user_id": token_row.user_id, "email": token_row.contact, "expires_at": token_row.expires_at}

def invalidate_reset_token(token: str, db: Session) -> bool:
    """Invalidate a used reset token"""
    redis_client = _get_redis_client()
    if redis_client:
        return bool(redis_client.delete(f"reset_token:{token}"))

    token_row = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == token,
        models.PasswordResetToken.used_at.is_(None),
    ).first()
    if not token_row:
        return False
    token_row.used_at = datetime.now()
    db.commit()
    return True

def cleanup_expired_tokens(db: Session):
    """Clean up expired tokens"""
    now = datetime.now()
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.expires_at < now
    ).delete()
    db.commit()

def get_password_strength_score(password: str) -> Dict[str, Any]:
    """
    Calculate password strength score and feedback
    Returns: {
        'score': 0-100,
        'strength': 'weak|medium|strong|very_strong',
        'feedback': list of suggestions,
        'requirements': dict of requirement fulfillment
    }
    """
    feedback = []
    requirements = {
        'length': False,
        'uppercase': False,
        'lowercase': False,
        'digit': False,
        'special': False
    }
    score = 0
    
    # Length check
    if len(password) >= 8:
        requirements['length'] = True
        score += 20
    else:
        feedback.append("Add at least 8 characters")
    
    # Uppercase check
    if re.search(r'[A-Z]', password):
        requirements['uppercase'] = True
        score += 20
    else:
        feedback.append("Add uppercase letter (A-Z)")
    
    # Lowercase check
    if re.search(r'[a-z]', password):
        requirements['lowercase'] = True
        score += 20
    else:
        feedback.append("Add lowercase letter (a-z)")
    
    # Digit check
    if re.search(r'\d', password):
        requirements['digit'] = True
        score += 20
    else:
        feedback.append("Add number (0-9)")
    
    # Special character check
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', password):
        requirements['special'] = True
        score += 20
    else:
        feedback.append("Add special character (!@#$%)")
    
    # Determine strength level
    if score >= 80:
        strength = 'very_strong'
    elif score >= 60:
        strength = 'strong'
    elif score >= 40:
        strength = 'medium'
    else:
        strength = 'weak'
    
    return {
        'score': score,
        'strength': strength,
        'feedback': feedback,
        'requirements': requirements
    }

def check_rate_limit(identifier: str, db: Session, max_attempts: int = 5, window_minutes: int = 15) -> bool:
    """
    Distributed rate limiting using Redis or DB
    """
    now = datetime.now()
    window_start = now.replace(second=0, microsecond=0)
    key = f"{identifier}:{window_start.strftime('%Y%m%d%H%M')}"
    ttl_seconds = window_minutes * 60

    redis_client = _get_redis_client()
    if redis_client:
        redis_key = f"rate_limit:{key}"
        count = redis_client.incr(redis_key)
        if count == 1:
            redis_client.expire(redis_key, ttl_seconds)
        return count <= max_attempts

    counter = db.query(models.RateLimitCounter).filter(models.RateLimitCounter.key == key).first()
    expires_at = now + timedelta(seconds=ttl_seconds)
    if not counter:
        counter = models.RateLimitCounter(
            key=key,
            count=1,
            window_started_at=window_start,
            expires_at=expires_at,
        )
        db.add(counter)
    else:
        counter.count += 1
        counter.expires_at = expires_at

    db.query(models.RateLimitCounter).filter(models.RateLimitCounter.expires_at < now).delete()
    db.commit()
    return counter.count <= max_attempts

def create_auth_response(user: models.User, remember_me: bool = False) -> fastapi.Response:
    """Create authentication response with secure cookies"""
    session_id = generate_secure_session_id()
    
    # Set cookie expiration based on remember me
    max_age = 30 * 24 * 60 * 60 if remember_me else None  # 30 days or session
    
    response = fastapi.responses.RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="user_id", 
        value=str(user.id),
        max_age=max_age,
        secure=os.getenv("ENVIRONMENT") == "production",
        httponly=True,
        samesite="strict" if os.getenv("ENVIRONMENT") == "production" else "lax"
    )
    response.set_cookie(
        key="username", 
        value=user.fullname or user.username,
        max_age=max_age,
        secure=os.getenv("ENVIRONMENT") == "production",
        httponly=True,
        samesite="strict" if os.getenv("ENVIRONMENT") == "production" else "lax"
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=max_age,
        secure=os.getenv("ENVIRONMENT") == "production",
        httponly=True,
        samesite="strict" if os.getenv("ENVIRONMENT") == "production" else "lax"
    )
    
    return response
