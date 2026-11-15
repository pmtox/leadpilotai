from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from backend.app.core.config import settings
from backend.app.database.connection import get_db
from backend.app.models.user import User

oauth = OAuth()


def get_google_client():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return None

    client = oauth.create_client("google")
    if client is None:
        oauth.register(
            name="google",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    return oauth.create_client("google")


def is_admin_email(email: str) -> bool:
    return email.casefold() in settings.admin_emails


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")

    role = "admin" if is_admin_email(user.email) else "user"
    if user.role != role:
        user.role = role
        db.commit()
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin" or not is_admin_email(user.email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


