"""
HTTP Security Headers Middleware for Market Pulse.
Injects industry-standard security headers on every response.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended HTTP security headers to every response."""

    # CSP can break third-party scripts (Firebase) and icon fonts (Font Awesome).
    # Keep it opt-in and allow override via env var.
    _ENABLE_CSP = os.getenv("MARKET_PULSE_ENABLE_CSP", "0") == "1" or bool(
        os.getenv("MARKET_PULSE_CSP", "").strip()
    )

    _DEFAULT_CSP = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "script-src 'self' 'unsafe-inline' "
        "https://www.gstatic.com https://www.googleapis.com https://cdnjs.cloudflare.com "
        "https://cdn.jsdelivr.net https://unpkg.com https://www.google.com https://www.recaptcha.net; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' "
        "https://identitytoolkit.googleapis.com https://securetoken.googleapis.com "
        "https://www.googleapis.com https://firestore.googleapis.com https://*.googleapis.com "
        "https: wss:; "
        "media-src 'self' blob:; "
        "frame-src 'self' https://www.google.com https://recaptcha.google.com https://www.recaptcha.net https://www.gstatic.com; "
        "frame-ancestors 'none';"
    )

    # Allow tightening CSP per-environment via env var override
    _CSP = os.getenv("MARKET_PULSE_CSP", _DEFAULT_CSP)

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Control referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (opt-in; see above)
        if self._ENABLE_CSP and "Content-Security-Policy" not in response.headers:
            response.headers["Content-Security-Policy"] = self._CSP

        # Disable browser features not needed by the app
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        # Force HTTPS in production (belt-and-suspenders alongside HTTPSRedirectMiddleware)
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # Prevent IE/Edge from activating compatibility mode
        response.headers["X-UA-Compatible"] = "IE=edge"

        return response
