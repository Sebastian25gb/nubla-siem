from .routes.auth import router as auth
from .routes.logs import router as logs
from .routes.register import router as register
from .routes.users import router as users
from .routes.mfa import router as mfa

__all__ = ["auth", "logs", "register", "users", "mfa"]