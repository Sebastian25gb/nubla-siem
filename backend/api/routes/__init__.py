# /root/nubla-siem/backend/api/routes/__init__.py
from .auth import router as auth
from .logs import router as logs
from .register import router as register
from .users import router as users
from .mfa import router as mfa
from .normalizer import router as normalizer

__all__ = ["auth", "logs", "register", "users", "mfa", "normalizer"]