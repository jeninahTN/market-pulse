from fastapi import FastAPI, Request, Form, Response, Cookie, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.security_headers import SecurityHeadersMiddleware
import firebase_admin
from firebase_admin import auth, credentials
import os
import re
import secrets
import time
import uuid
import logging
from dotenv import load_dotenv
from app.data import (
    CROP_METADATA,
    REGION_DB_MARKETS,
)
from app.fast_data import (
    get_monitored_crops_ultra_fast,
    get_crop_detail_ultra_fast,
    get_custom_monitored_crops_ultra_fast,
)
from app.prediction import prediction_service
from app.voice import generate_voice_advisory
from app.security import (
    verify_password, get_password_hash,
    generate_secure_session_id, validate_password_strength, password_hash_needs_upgrade
)
from app.cache import clear_cache, get_cache_stats
from app.performance import performance_monitor
from app.auth_utils import (
    validate_email_format, validate_phone_format, format_phone_number,
    generate_password_reset_token, validate_reset_token, invalidate_reset_token,
    check_rate_limit
)
from app.sms_utils import (
    validate_uganda_phone_number, generate_sms_verification_code, verify_sms_code,
    check_sms_rate_limit, get_sms_status, send_sms_notification,
    create_sms_verification_response
)
from app.sms_providers import get_available_sms_providers, get_sms_balances
from app.notifications import send_password_reset_message
from app.observability import configure_logging, request_metrics, audit_log
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models, database

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

load_dotenv()
configure_logging()
logger = logging.getLogger("market_pulse")

# Initialize Firebase
try:
    cred_path = os.getenv(
        "FIREBASE_ADMIN_CREDENTIALS_PATH",
        os.path.join(os.path.dirname(__file__), "..", "market-pulse-8b45b-firebase-adminsdk-fbsvc-5bf51f3f9f.json"),
    )
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin initialized successfully.")
    else:
        print(
            f"Warning: Firebase credentials not found at {cred_path}. "
            "Set FIREBASE_ADMIN_CREDENTIALS_PATH to enable Firebase admin features."
        )
except Exception as e:
    print(f"Error initializing Firebase Admin: {e}")

app = FastAPI(title="Market Pulse")

# Security middleware - only add HTTPS redirect in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# HTTP security headers on every response (CSP, X-Frame-Options, etc.)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "https://localhost:8000", "https://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

trusted_hosts = [
    host.strip()
    for host in os.getenv(
        "MARKET_PULSE_TRUSTED_HOSTS",
        # Default to empty so first-time deployments don't get blocked by host filtering.
        # In production, set MARKET_PULSE_TRUSTED_HOSTS explicitly (e.g. "yourdomain.com,.yourdomain.com").
        "",
    ).split(",")
    if host.strip()
]
if os.getenv("ENVIRONMENT") == "production" and trusted_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# Use secure session management
secret_key = os.getenv("SECRET_KEY", "your_secret_key_here")
is_production = os.getenv("ENVIRONMENT") == "production"
ALLOW_AUTO_CREATE_LOGIN = os.getenv("MARKET_PULSE_ALLOW_AUTO_CREATE_LOGIN", "1") != "0"
ALLOW_MOCK_AUTH = os.getenv("MARKET_PULSE_ENABLE_MOCK_AUTH", "0") == "1" and not is_production
_default_base_url = os.getenv("RENDER_EXTERNAL_URL") or "http://127.0.0.1:8000"
APP_BASE_URL = os.getenv("MARKET_PULSE_APP_BASE_URL", _default_base_url).rstrip("/")
if is_production:
    # In production, never auto-create accounts during login.
    ALLOW_AUTO_CREATE_LOGIN = os.getenv("MARKET_PULSE_ALLOW_AUTO_CREATE_LOGIN", "0") != "0"


def _parse_csv_env(name: str):
    raw = os.getenv(name, "").strip()
    if not raw:
        return set()
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


_ADMIN_USER_IDS = {v for v in _parse_csv_env("MARKET_PULSE_ADMIN_USER_IDS") if v.isdigit()}
_ADMIN_USERNAMES = _parse_csv_env("MARKET_PULSE_ADMIN_USERNAMES")
_ADMIN_EMAILS = _parse_csv_env("MARKET_PULSE_ADMIN_EMAILS")


def _require_admin_user(
    user_id: Optional[str],
    db: Session,
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id_int = int(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.query(models.User).filter(models.User.id == user_id_int).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Production: require explicit admin allowlist.
    # Development: allow any authenticated user if no allowlist is configured
    # to avoid blocking local testing, but strongly recommend setting allowlist.
    allowlist_configured = bool(_ADMIN_USER_IDS or _ADMIN_USERNAMES or _ADMIN_EMAILS)
    if is_production and not allowlist_configured:
        raise HTTPException(status_code=403, detail="Admin allowlist not configured")

    if allowlist_configured:
        username = str(user.username or "").strip().lower()
        email = str(user.email or "").strip().lower()
        if (
            str(user.id) in _ADMIN_USER_IDS
            or (username and username in _ADMIN_USERNAMES)
            or (email and email in _ADMIN_EMAILS)
        ):
            return user
        raise HTTPException(status_code=403, detail="Admin access required")

    return user

app.add_middleware(
    SessionMiddleware, 
    secret_key=secret_key,
    https_only=is_production,
    same_site="strict" if is_production else "lax"
)

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# Keep CSP opt-in so current UI behavior (inline scripts/charts/theme toggles)
# is not broken. Enable when templates/scripts are CSP-hardened.
if os.getenv("MARKET_PULSE_ENABLE_CSP", "0") == "1":
    SECURITY_HEADERS["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.gstatic.com https://www.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "img-src 'self' data: blob: https:; "
        "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "connect-src 'self' https://identitytoolkit.googleapis.com https://www.googleapis.com https://securetoken.googleapis.com https: wss:; "
        "frame-src 'self' https://www.google.com https://www.gstatic.com; "
        "frame-ancestors 'none';"
    )


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    # Firebase Auth (Google sign-in) typically whitelists `localhost` by default,
    # but not always `127.0.0.1`. For local demos, auto-canonicalize to localhost.
    if (
        not is_production
        and os.getenv("MARKET_PULSE_PREFER_LOCALHOST", "1") == "1"
        and request.method == "GET"
        and request.url.hostname == "127.0.0.1"
        and not request.url.path.startswith("/static")
    ):
        port = request.url.port or 8000
        target = f"{request.url.scheme}://localhost:{port}{request.url.path}"
        if request.url.query:
            target += f"?{request.url.query}"
        return RedirectResponse(url=target, status_code=307)

    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.time()
    response = None
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        latency_ms = (time.time() - start) * 1000
        request_metrics.record(status_code=status_code, latency_ms=latency_ms)
        extra = {"request_id": request_id}
        if status_code >= 500:
            logger.warning(
                "http_request_server_error method=%s path=%s status=%s latency_ms=%.2f",
                request.method,
                request.url.path,
                status_code,
                latency_ms,
                extra=extra,
            )
        else:
            logger.info(
                "http_request method=%s path=%s status=%s latency_ms=%.2f",
                request.method,
                request.url.path,
                status_code,
                latency_ms,
                extra=extra,
            )

    if response is None:
        response = JSONResponse({"status": "error", "message": "Request failed"}, status_code=500)
    response.headers["X-Request-ID"] = request_id
    for header_name, header_value in SECURITY_HEADERS.items():
        response.headers.setdefault(header_name, header_value)
    return response

# Setup paths
BASE_DIR = Path(__file__).resolve().parent

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Favicon route
@app.get("/favicon.ico")
async def favicon():
    favicon_path = BASE_DIR / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    # Return empty response if favicon doesn't exist
    return Response(status_code=204)


@app.get("/service-worker.js")
async def service_worker():
    # Serve at the origin root so the SW scope covers the whole site (/, /offline, etc.).
    # If served under /static/, browsers scope it to /static/ only and navigations won't be intercepted.
    sw_path = BASE_DIR / "static" / "service-worker.js"
    if not sw_path.exists():
        return Response(status_code=404)
    response = FileResponse(sw_path, media_type="application/javascript")
    # Avoid stale SWs during development.
    response.headers["Cache-Control"] = "no-cache"
    return response

# Setup templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

I18N_KEY_PATTERN = re.compile(r'data-i18n="([^"]+)"')
SUPPORTED_LANGS = ["en", "lg", "rn", "teo", "luo", "sw"]


def _collect_template_i18n_keys():
    static_keys = set()
    dynamic_patterns = set()

    for template_path in (BASE_DIR / "templates").glob("*.html"):
        text = template_path.read_text(encoding="utf-8", errors="ignore")
        for match in I18N_KEY_PATTERN.findall(text):
            if "{{" in match or "}}" in match:
                dynamic_patterns.add(match)
            else:
                static_keys.add(match)

    expected_dynamic = {f"crop_{crop_id}" for crop_id in CROP_METADATA.keys()}
    expected_dynamic.update({f"market_{region}" for region in REGION_DB_MARKETS.keys()})

    merged = sorted(static_keys.union(expected_dynamic))
    return {
        "keys": merged,
        "static_keys": sorted(static_keys),
        "dynamic_patterns": sorted(dynamic_patterns),
        "expected_dynamic_keys": sorted(expected_dynamic),
    }


def _build_detail_snapshots(crops):
    snapshots = []
    for crop in crops or []:
        crop_id = crop.get("id")
        region = crop.get("region")
        if not crop_id or not region:
            continue
        try:
            snapshots.append(get_crop_detail_ultra_fast(crop_id, region))
        except Exception as exc:
            print(f"Could not build detail snapshot for {crop_id}/{region}: {exc}")
    return snapshots


@app.on_event("startup")
async def startup_refresh_scheduler():
    if os.getenv("MARKET_PULSE_DISABLE_SCHEDULER", "0") == "1":
        logger.info("refresh_scheduler_disabled_via_env")
        return
    from app.refresh_scheduler import start_refresh_scheduler

    start_refresh_scheduler()

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, 
                    user_id: Optional[str] = Cookie(default=None),
                    username: Optional[str] = Cookie(default=None), 
                    is_new_user: str = Cookie(default="false"),
                    db: Session = Depends(database.get_db)):
    if not user_id:
        return RedirectResponse(url="/login")
        
    db_user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not db_user:
        return RedirectResponse(url="/login")

    # Fetch monitored crops from DB
    db_crops = db_user.monitored_crops
    
    # Logic fix: Only use defaults if the user is FLAGED as new AND has no crops in DB.
    # If they are NOT new but have no crops, it means they deleted them all.
    if not db_crops and db_user.is_new_user:
        crops = get_monitored_crops_ultra_fast()
    else:
        pairs = [(c.crop_id, c.region) for c in db_crops]
        crops = get_custom_monitored_crops_ultra_fast(pairs)
    detail_snapshots = _build_detail_snapshots(crops)
    
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "title": "Dashboard",
            "crops": crops,
            "detail_snapshots": detail_snapshots,
            "username": db_user.fullname or db_user.username,
            "is_new_user": db_user.is_new_user,
        },
    )

@app.get("/history", response_class=HTMLResponse)
def read_history(request: Request, 
                       user_id: Optional[str] = Cookie(default=None),
                       db: Session = Depends(database.get_db)):
    if not user_id:
        return RedirectResponse(url="/login")
    
    db_user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not db_user:
        return RedirectResponse(url="/login")
        
    db_crops = db_user.monitored_crops
    pairs = [(c.crop_id, c.region) for c in db_crops]
    crops = get_custom_monitored_crops_ultra_fast(pairs)
    detail_snapshots = _build_detail_snapshots(crops)
    
    return templates.TemplateResponse(
        request,
        "history.html",
        {
            "request": request,
            "title": "Prediction History",
            "crops": crops,
            "detail_snapshots": detail_snapshots,
            "username": db_user.fullname or db_user.username,
        },
    )

@app.get("/detail/{crop}/{region}", response_class=HTMLResponse)
async def read_detail(request: Request, crop: str, region: str):
    detail = get_crop_detail_ultra_fast(crop, region)
    return templates.TemplateResponse(
        request,
        "detail.html",
        {"request": request, "title": f"{detail['name']} in {detail['region']}", "detail": detail},
    )

@app.get("/offline", response_class=HTMLResponse)
async def read_offline(request: Request):
    return templates.TemplateResponse(
        request,
        "offline.html",
        {"request": request, "title": "Offline Access"},
    )

@app.get("/help", response_class=HTMLResponse)
async def read_help(request: Request):
    return templates.TemplateResponse(
        request,
        "help.html",
        {"request": request, "title": "Help & Support"},
    )

@app.get("/ussd", response_class=HTMLResponse)
async def read_ussd(request: Request):
    return templates.TemplateResponse(
        request,
        "ussd.html",
        {"request": request, "title": "USSD Service"},
    )


@app.get("/translation-qa", response_class=HTMLResponse)
async def read_translation_qa(request: Request):
    audit = _collect_template_i18n_keys()
    return templates.TemplateResponse(
        request,
        "translation_qa.html",
        {
            "request": request,
            "title": "Translation QA Checklist",
            "i18n_keys": audit["keys"],
            "static_i18n_keys": audit["static_keys"],
            "dynamic_i18n_patterns": audit["dynamic_patterns"],
            "dynamic_i18n_expected_keys": audit["expected_dynamic_keys"],
            "supported_languages": SUPPORTED_LANGS,
        },
    )

@app.get("/api/voice-advisory")
async def get_voice_advisory(crop_id: str, region: str, lang: str = "en"):
    detail = get_crop_detail_ultra_fast(crop_id, region)
    if not detail:
        return {"error": "Crop not found"}, 404
    
    current_price = str(detail['current_price'])
    predicted_price = str(detail['predicted_price'])

    try:
        audio_url = generate_voice_advisory(crop_id, region, current_price, predicted_price, lang)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}

    return {"status": "success", "audio_url": audio_url}

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "title": "Login",
            "auth_mock_mode": ALLOW_MOCK_AUTH,
        },
    )

@app.post("/auth/login")
def login(login_id: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    # Check if user exists in DB
    user = (
        db.query(models.User)
        .filter((models.User.username == login_id) | (models.User.email == login_id))
        .first()
    )
    if not user:
        if not ALLOW_AUTO_CREATE_LOGIN:
            audit_log("login_failed", detail=f"user_not_found:{login_id[:40]}")
            return HTMLResponse(
                content="<script>alert('Invalid login details!'); window.history.back();</script>",
                status_code=401,
            )

        # Development convenience: auto-create user if not exists.
        # In production this is disabled by default.
        hashed_password = get_password_hash(password)
        user = models.User(
            username=login_id,
            email=login_id if "@" in login_id else None,
            hashed_password=hashed_password,
            fullname=login_id.split("@")[0].title(),
            is_new_user=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not verify_password(password, user.hashed_password):
        audit_log("login_failed", user_id=user.id, detail="wrong_password")
        return HTMLResponse(
            content="<script>alert('Invalid password!'); window.history.back();</script>", 
            status_code=401
        )

    # Upgrade legacy hashes on successful login (e.g., SHA-256 -> bcrypt).
    try:
        if password_hash_needs_upgrade(user.hashed_password):
            user.hashed_password = get_password_hash(password)
            db.commit()
    except Exception as exc:
        # Never block a successful login due to a hash-upgrade failure.
        print(f"Password hash upgrade warning: {exc}")

    # Generate secure session
    session_id = generate_secure_session_id()
    
    audit_log("login_success", user_id=user.id)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="user_id", 
        value=str(user.id),
        secure=is_production,
        httponly=True,
        samesite="strict" if is_production else "lax"
    )
    response.set_cookie(
        key="username", 
        value=user.fullname or user.username,
        secure=is_production,
        httponly=True,
        samesite="strict" if is_production else "lax"
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        secure=is_production,
        httponly=True,
        samesite="strict" if is_production else "lax"
    )
    return response

@app.post("/auth/signup")
def signup(contact: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    # Password strength validation
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        return HTMLResponse(
            content=f"<script>alert('{message}'); window.history.back();</script>", 
            status_code=400
        )

    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.username == contact).first()
    if existing_user:
        return RedirectResponse(url="/login", status_code=303)
        
    # Hash password before storing
    hashed_password = get_password_hash(password)
    new_user = models.User(
        username=contact, 
        fullname=contact.split("@")[0].title(), 
        hashed_password=hashed_password, 
        is_new_user=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate secure session
    session_id = generate_secure_session_id()
    
    audit_log("signup_success", user_id=new_user.id)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="user_id", 
        value=str(new_user.id),
        secure=is_production,
        httponly=True,
        samesite="strict" if is_production else "lax"
    )
    response.set_cookie(
        key="username", 
        value=new_user.fullname,
        secure=is_production,
        httponly=True,
        samesite="strict" if is_production else "lax"
    )
    response.set_cookie(
        key="session_id",
        value=session_id,
        secure=is_production,
        httponly=True,
        samesite="strict" if is_production else "lax"
    )
    return response

@app.post("/auth/firebase-verify")
async def verify_firebase_token(request: Request, db: Session = Depends(database.get_db)):
    try:
        data = await request.json()
        id_token = data.get('idToken')
        provided_name = data.get('fullname') # Capture name from signup form
        
        # Verify the ID token (Bypass for MOCK_MODE)
        if id_token.startswith("MOCK_TOKEN_"):
            if not ALLOW_MOCK_AUTH:
                return {"status": "error", "message": "Mock auth is disabled"}
            # Mock Token Format: MOCK_TOKEN_TYPE_IDENTIFIER
            parts = id_token.split("_")
            identifier = parts[-1]
            type_info = parts[-2]
            uid = f"mock_uid_{identifier}"
            email = identifier if type_info == "EMAIL" else None
            phone = identifier if type_info == "PHONE" else None
            name = provided_name or (email.split('@')[0] if email else phone).title()
        else:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email')
            phone = decoded_token.get('phone_number')
            name = provided_name or decoded_token.get('name')
            if not name:
                # Handle cases where name is missing in real Firebase token
                name = (email.split('@')[0] if email else phone).title()
        
        # Identifier for our DB (Username)
        identifier = email or phone
        if not identifier:
            return {"status": "error", "message": "No identifier found in token"}

        # Check if user exists in our DB (by UID, Email, or Phone)
        user = db.query(models.User).filter(
            (models.User.google_id == uid) | 
            (models.User.username == identifier)
        ).first()
        
        if not user:
            user = models.User(
                username=identifier,
                fullname=name,
                google_id=uid,
                is_new_user=True,
                hashed_password="firebase_managed"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif provided_name:
            # Update existing user's name if they previously had none or a placeholder
            user.fullname = provided_name
            db.commit()
            db.refresh(user)
            
        return {
            "status": "success",
            "redirect": "/",
            "user_id": str(user.id),
            "username": user.fullname or user.username
        }
    except Exception as e:
        print(f"Firebase token verification failed: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/auth/google/login")
async def google_login_redirect():
    """Google auth is initiated from frontend Firebase flow."""
    return RedirectResponse(url="/login", status_code=303)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id", secure=is_production, httponly=True, samesite="strict" if is_production else "lax")
    response.delete_cookie("username", secure=is_production, httponly=True, samesite="strict" if is_production else "lax")
    response.delete_cookie("is_new_user", secure=is_production, httponly=True, samesite="strict" if is_production else "lax")
    response.delete_cookie("session_id", secure=is_production, httponly=True, samesite="strict" if is_production else "lax")
    return response

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {"request": request, "title": "Forgot Password"},
    )

@app.post("/auth/forgot-password")
async def forgot_password(contact: str = Form(...), db: Session = Depends(database.get_db)):
    """Handle forgot password request"""
    
    # Rate limiting check
    if not check_rate_limit(f"forgot_{contact}", db=db):
        return JSONResponse(
            content={"status": "error", "message": "Too many requests. Please try again later."},
            status_code=429
        )
    
    # Find user by email or phone
    user = None
    if validate_email_format(contact):
        user = db.query(models.User).filter(models.User.username == contact).first()
    elif validate_phone_format(contact):
        formatted_phone = format_phone_number(contact)
        user = db.query(models.User).filter(models.User.username == formatted_phone).first()
    
    if not user:
        # Don't reveal if user exists or not
        return JSONResponse(
            content={"status": "success", "message": "If an account exists, a reset link has been sent."}
        )
    
    # Generate reset token
    reset_token = generate_password_reset_token(user.id, user.username, db=db)
    reset_link = f"{APP_BASE_URL}/reset-password?token={reset_token}"
    sent = send_password_reset_message(user.username, reset_link)
    if not sent:
        print(f"Password reset delivery failed for contact: {user.username}")

    return JSONResponse(
        {
            "status": "success",
            "message": "If an account exists, password reset instructions have been sent."
        }
    )

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str, db: Session = Depends(database.get_db)):
    """Show reset password page"""
    
    # Validate token
    token_data = validate_reset_token(token, db)
    
    return templates.TemplateResponse(
        request,
        "reset_password.html",
        {
            "request": request,
            "title": "Reset Password",
            "token": token,
            "token_valid": token_data is not None,
        },
    )

@app.post("/auth/reset-password-confirm")
async def reset_password_confirm(token: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    """Handle password reset confirmation"""
    
    # Validate token
    token_data = validate_reset_token(token, db)
    if not token_data:
        return JSONResponse(
            content={"status": "error", "message": "Invalid or expired reset link"},
            status_code=400
        )
    
    # Validate password strength
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        return JSONResponse(
            content={"status": "error", "message": message},
            status_code=400
        )
    
    # Get user
    user = db.query(models.User).filter(models.User.id == token_data['user_id']).first()
    if not user:
        return JSONResponse(
            content={"status": "error", "message": "User not found"},
            status_code=400
        )
    
    # Update password
    user.hashed_password = get_password_hash(password)
    db.commit()
    
    # Invalidate token
    invalidate_reset_token(token, db)
    
    return JSONResponse({
        "status": "success", 
        "message": "Password reset successfully"
    })

@app.post("/auth/sms/send-verification")
async def send_sms_verification(contact: str = Form(...), db: Session = Depends(database.get_db)):
    """Send SMS verification code"""
    
    # Validate phone number
    phone_validation = validate_uganda_phone_number(contact)
    if not phone_validation['valid']:
        return JSONResponse(
            content={"status": "error", "message": phone_validation['error']},
            status_code=400
        )
    
    phone = phone_validation['formatted']
    
    # Rate limiting check
    if not check_sms_rate_limit(phone, db=db):
        return JSONResponse(
            content={"status": "error", "message": "Too many SMS requests. Please wait 15 minutes and try again."},
            status_code=429
        )
    
    # Check SMS status
    sms_status = get_sms_status(phone, db=db)
    if sms_status['active'] and not sms_status['can_resend']:
        return JSONResponse(
            content={
                "status": "error", 
                "message": f"Please wait {sms_status['time_until_resend']} seconds before requesting another code",
                "can_resend_after": sms_status['time_until_resend']
            },
            status_code=429
        )
    
    # Generate verification code
    code = generate_sms_verification_code(phone, db=db)
    
    # Send SMS (mock implementation)
    message = f"Your Market Pulse verification code is: {code}. Valid for 10 minutes."
    sms_sent = send_sms_notification(phone, message)
    
    if not sms_sent:
        return JSONResponse(
            content={"status": "error", "message": "Failed to send SMS. Please try again."},
            status_code=500
        )
    
    # Return success response
    response_data = create_sms_verification_response(phone, code)
    response_data.update({
        "phone": phone,
        "attempts_remaining": 3,
        "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
    })
    
    return JSONResponse(content=response_data)

@app.post("/auth/sms/verify-code")
async def verify_sms_code_endpoint(phone: str = Form(...), code: str = Form(...), db: Session = Depends(database.get_db)):
    """Verify SMS verification code"""
    
    # Validate phone number
    phone_validation = validate_uganda_phone_number(phone)
    if not phone_validation['valid']:
        return JSONResponse(
            content={"status": "error", "message": phone_validation['error']},
            status_code=400
        )
    
    phone = phone_validation['formatted']
    
    # Verify code
    verification_result = verify_sms_code(phone, code, db=db)
    
    if not verification_result['valid']:
        return JSONResponse(
            content={
                "status": "error", 
                "message": verification_result['error']
            },
            status_code=400
        )
    
    # Code verified successfully - create or update user
    user = db.query(models.User).filter(models.User.username == phone).first()
    if not user:
        # Create new user
        user = models.User(
            username=phone,
            fullname=f"User {phone[-4:]}",  # Default name
            hashed_password=get_password_hash(secrets.token_urlsafe(16)),  # Random password
            is_new_user=True,
            phone_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user
        user.phone_verified = True
        db.commit()
    
    return JSONResponse({
        "status": "success",
        "message": "Phone number verified successfully",
        "user_id": user.id,
        "redirect": "/"
    })

@app.get("/auth/sms/status/{phone}")
async def get_sms_verification_status(phone: str, db: Session = Depends(database.get_db)):
    """Get SMS verification status for a phone number"""
    
    # Validate phone number
    phone_validation = validate_uganda_phone_number(phone)
    if not phone_validation['valid']:
        return JSONResponse(
            content={"status": "error", "message": phone_validation['error']},
            status_code=400
        )
    
    phone = phone_validation['formatted']
    sms_status = get_sms_status(phone, db=db)
    
    return JSONResponse({
        "status": "success",
        "data": sms_status
    })

@app.get("/admin/sms/providers")
async def get_sms_providers(
    user_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(database.get_db),
):
    """Get available SMS providers"""
    _require_admin_user(user_id, db)
    providers = get_available_sms_providers()
    balances = get_sms_balances()
    
    return JSONResponse({
        "status": "success",
        "providers": providers,
        "balances": balances,
        "current_provider": os.getenv("SMS_PREFERRED_PROVIDER", "Mock")
    })

@app.post("/admin/sms/test")
async def test_sms_provider(
    phone: str = Form(...),
    message: str = Form(...),
    provider: str = Form(...),
    user_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(database.get_db),
):
    """Test SMS provider"""
    _require_admin_user(user_id, db)
     
    # Validate phone number
    phone_validation = validate_uganda_phone_number(phone)
    if not phone_validation['valid']:
        return JSONResponse(
            content={"status": "error", "message": phone_validation['error']},
            status_code=400
        )
    
    phone = phone_validation['formatted']
    
    # Send test SMS
    result = send_sms_notification(phone, message, provider)
    
    return JSONResponse({
        "status": "success" if result['success'] else "error",
        "message": "Test SMS sent successfully" if result['success'] else f"Failed: {result['error']}",
        "provider": result['provider'],
        "message_id": result.get('message_id'),
        "cost": result.get('cost', 0)
    })

@app.get("/admin/sms/logs")
async def get_sms_logs(
    user_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(database.get_db),
):
    """Get SMS delivery logs (mock implementation)"""
    _require_admin_user(user_id, db)
    # In production, this would query a database or logging service
    mock_logs = [
        {
            "id": 1,
            "phone": "+256712345678",
            "message": "Your Market Pulse verification code is: 123456",
            "provider": "Mock",
            "status": "Delivered",
            "cost": 0.06,
            "sent_at": "2024-03-30T18:00:00Z",
            "delivered_at": "2024-03-30T18:01:00Z"
        },
        {
            "id": 2,
            "phone": "+256723456789",
            "message": "Your Market Pulse verification code is: 789012",
            "provider": "Mock",
            "status": "Failed",
            "cost": 0,
            "sent_at": "2024-03-30T17:55:00Z",
            "error": "Invalid phone number"
        }
    ]
    
    return JSONResponse({
        "status": "success",
        "logs": mock_logs,
        "total_count": len(mock_logs),
        "delivered_count": sum(1 for log in mock_logs if log['status'] == 'Delivered'),
        "failed_count": sum(1 for log in mock_logs if log['status'] == 'Failed')
    })

@app.get("/predict-form", response_class=HTMLResponse)
async def read_predict_form(request: Request):
    crops = get_monitored_crops_ultra_fast()
    detail_snapshots = _build_detail_snapshots(crops)

    # All 5 crops — always show full list regardless of what the user monitors
    all_crops = [
        {"id": "maize",   "name": "Maize"},
        {"id": "beans",   "name": "Beans"},
        {"id": "coffee",  "name": "Coffee"},
        {"id": "matooke", "name": "Matooke"},
        {"id": "cassava", "name": "Cassava"},
    ]

    # All 7 markets — always show full list
    all_markets = [
        {"region": "nakawa",  "name": "Nakawa"},
        {"region": "owino",   "name": "Owino"},
        {"region": "kalerwe", "name": "Kalerwe"},
        {"region": "masaka",  "name": "Masaka"},
        {"region": "mbale",   "name": "Mbale"},
        {"region": "gulu",    "name": "Gulu"},
        {"region": "kasese",  "name": "Kasese"},
    ]

    return templates.TemplateResponse(
        request,
        "predict.html",
        {
            "request": request,
            "title": "Get Price Prediction",
            "crops": crops,
            "all_crops": all_crops,
            "all_markets": all_markets,
            "detail_snapshots": detail_snapshots,
        },
    )

@app.get("/predict", response_class=HTMLResponse)
async def predict_get_redirect():
    """Redirect GET /predict to the predict form page."""
    return RedirectResponse(url="/predict-form", status_code=301)

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request,
                         user_id: Optional[str] = Cookie(default=None),
                         username: Optional[str] = Cookie(default=None),
                         is_new_user: str = Cookie(default="false"),
                         db: Session = Depends(database.get_db)):
    """Alias for the root dashboard — avoids 404 when /dashboard is typed directly."""
    return await read_root(request, user_id, username, is_new_user, db)

@app.post("/refresh-now")
async def refresh_now(
    request: Request,
    user_id: Optional[str] = Cookie(default=None),
):
    wants_json = "application/json" in request.headers.get("accept", "").lower() or (
        request.headers.get("x-requested-with", "").lower() == "xmlhttprequest"
    )

    if not user_id:
        if wants_json:
            return JSONResponse({"status": "error", "message": "Not authenticated"}, status_code=401)
        return RedirectResponse(url="/login", status_code=303)

    try:
        from app.refresh_scheduler import run_refresh_cycle_async

        # Clear cache to ensure fresh data
        clear_cache()
        
        # Start async refresh to reduce UI lag
        summary = run_refresh_cycle_async()
        print(f"Manual refresh started: {summary}")
        
        if wants_json:
            payload = {
                "status": summary.get("status", "unknown"),
                "message": "Refresh started in background" if summary.get("status") == "started" else "Refresh failed",
                "summary": summary,
                "cache_stats": get_cache_stats()
            }
            return JSONResponse(payload, status_code=200)
    except Exception as exc:
        print(f"Manual refresh failed: {exc}")
        if wants_json:
            return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)

    return RedirectResponse(url="/", status_code=303)

@app.get("/api/performance")
async def get_performance_stats():
    """Get application performance statistics"""
    try:
        perf_stats = performance_monitor.get_stats()
        system_stats = performance_monitor.get_system_stats()
        
        return {
            "status": "success",
            "performance_metrics": perf_stats,
            "system_metrics": system_stats,
            "cache_stats": get_cache_stats()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/health/live")
async def liveness_check():
    return {"status": "ok", "service": "market_pulse"}


@app.get("/health/ready")
async def readiness_check(db: Session = Depends(database.get_db)):
    checks = {"database": False, "redis": False}
    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        logger.error("readiness_database_failed error=%s", exc)

    # Redis check (optional dependency)
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        checks["redis"] = True
    else:
        try:
            import redis
            client = redis.from_url(redis_url, decode_responses=True)
            checks["redis"] = bool(client.ping())
        except Exception as exc:
            logger.error("readiness_redis_failed error=%s", exc)

    ready = all(checks.values())
    payload = {"status": "ready" if ready else "not_ready", "checks": checks}
    return JSONResponse(content=payload, status_code=200 if ready else 503)


@app.get("/metrics")
async def metrics_endpoint():
    metrics = request_metrics.snapshot()
    lines = [
        "# HELP market_pulse_total_requests Total HTTP requests",
        "# TYPE market_pulse_total_requests counter",
        f"market_pulse_total_requests {int(metrics['total_requests'])}",
        "# HELP market_pulse_http_avg_latency_ms Average request latency in ms",
        "# TYPE market_pulse_http_avg_latency_ms gauge",
        f"market_pulse_http_avg_latency_ms {metrics['avg_latency_ms']}",
        "# HELP market_pulse_http_p95_latency_ms P95 request latency in ms",
        "# TYPE market_pulse_http_p95_latency_ms gauge",
        f"market_pulse_http_p95_latency_ms {metrics['p95_latency_ms']}",
        "# HELP market_pulse_http_status_count Status family counts",
        "# TYPE market_pulse_http_status_count gauge",
        f"market_pulse_http_status_count{{status_family=\"2xx\"}} {int(metrics['status_2xx'])}",
        f"market_pulse_http_status_count{{status_family=\"4xx\"}} {int(metrics['status_4xx'])}",
        f"market_pulse_http_status_count{{status_family=\"5xx\"}} {int(metrics['status_5xx'])}",
    ]
    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")

@app.post("/predict-form")
async def process_predict_form(crop_id: str = Form(...), region: str = Form(...), 
                               user_id: Optional[str] = Cookie(default=None),
                               db: Session = Depends(database.get_db)):
    response = RedirectResponse(url=f"/detail/{crop_id}/{region}", status_code=303)
    
    if not user_id:
        return response

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user:
        # Check if crop already monitored
        existing = db.query(models.MonitoredCrop).filter(
            models.MonitoredCrop.user_id == user.id,
            models.MonitoredCrop.crop_id == crop_id,
            models.MonitoredCrop.region == region
        ).first()
        
        if not existing:
            # Add the new one
            db.add(models.MonitoredCrop(user_id=user.id, crop_id=crop_id, region=region))
            
        user.is_new_user = False
        db.commit()
        
    return response

@app.get("/delete-prediction/{crop_id}/{region}")
async def delete_prediction(crop_id: str, region: str, 
                             user_id: Optional[str] = Cookie(default=None),
                             db: Session = Depends(database.get_db)):
    response = RedirectResponse(url="/", status_code=303)
    
    if not user_id:
        return response

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user:
        # If no customization exists yet and user is still new, start with defaults
        if not user.monitored_crops and user.is_new_user:
            defaults = [
                ("matooke", "nakawa"),
                ("cassava", "gulu"),
                ("coffee", "mbale"),
                ("maize", "kasese"),
                ("beans", "owino"),
            ]
            for d_crop, d_reg in defaults:
                db.add(models.MonitoredCrop(user_id=user.id, crop_id=d_crop, region=d_reg))
            db.commit() # Commit to ensure they exist before trying to delete one

        db.query(models.MonitoredCrop).filter(
            models.MonitoredCrop.user_id == user.id,
            models.MonitoredCrop.crop_id == crop_id,
            models.MonitoredCrop.region == region
        ).delete()
        user.is_new_user = False
        db.commit()
            
    return response

class PredictionRequest(BaseModel):
    features: List[float]

@app.post("/predict")
async def predict_price(request: PredictionRequest):
    try:
        prediction = prediction_service.predict(request.features)
        if prediction is not None:
            # Extract the predicted price from the prediction dictionary
            predicted_price = prediction.get('prediction', prediction.get('predicted_price', 0))
            return {"predicted_price": predicted_price}
        else:
            return {"error": "Prediction failed"}, 500
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}, 500
