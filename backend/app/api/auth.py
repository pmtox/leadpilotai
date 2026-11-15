from typing import Literal, Optional
from urllib.parse import urlencode
from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from backend.app.core.auth import get_current_user, get_google_client, is_admin_email
from backend.app.core.config import settings
from backend.app.database.connection import get_db
from backend.app.models.customer import Customer
from backend.app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class ProfileUpdate(BaseModel):
    preferred_language: Literal["English", "Hindi", "Telugu", "Tamil"]


def _frontend_redirect(error: Optional[str] = None) -> RedirectResponse:
    suffix = f"?{urlencode({'auth_error': error})}" if error else ""
    return RedirectResponse(f"{settings.FRONTEND_URL}/{suffix}", status_code=303)


@router.get("/status")
def auth_status():
    return {
        "google_configured": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
    }


@router.get("/google")
async def google_login(request: Request):
    google = get_google_client()
    if google is None:
        return _frontend_redirect("google_not_configured")

    redirect_uri = settings.GOOGLE_REDIRECT_URI or str(request.url_for("google_callback"))
    return await google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    google = get_google_client()
    if google is None:
        return _frontend_redirect("google_not_configured")

    try:
        token = await google.authorize_access_token(request)
    except OAuthError:
        return _frontend_redirect("google_signin_failed")

    userinfo = token.get("userinfo") or {}
    email = userinfo.get("email")
    google_sub = userinfo.get("sub")
    if not email or not google_sub or userinfo.get("email_verified") is not True:
        return _frontend_redirect("google_email_unverified")

    email = email.strip().casefold()
    user = db.query(User).filter(User.google_sub == google_sub).first()
    if user is None:
        user = db.query(User).filter(func.lower(User.email) == email).first()
    if user is None:
        user = User(google_sub=google_sub, email=email, name=userinfo.get("name") or email)
        db.add(user)

    user.google_sub = google_sub
    user.email = email
    user.name = userinfo.get("name") or user.name
    user.picture = userinfo.get("picture")
    user.role = "admin" if is_admin_email(email) else "user"
    db.flush()

    customer = db.query(Customer).filter(Customer.user_id == user.id).first()
    if customer is None:
        customer = (
            db.query(Customer)
            .filter(
                func.lower(Customer.email) == email,
                Customer.user_id.is_(None),
            )
            .order_by(Customer.id.desc())
            .first()
        )
    if customer is None:
        customer = Customer(
            name=user.name,
            phone="",
            email=email,
            preferred_language="English",
            user_id=user.id,
        )
        db.add(customer)
    else:
        customer.user_id = user.id
        customer.email = email
        if not customer.name:
            customer.name = user.name

    db.commit()
    db.refresh(user)
    request.session.clear()
    request.session["user_id"] = user.id
    return _frontend_redirect()


@router.get("/me")
def current_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.user_id == user.id).first()
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Your account profile is not ready. Please sign out and sign in again.",
        )
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "picture": user.picture,
        "role": user.role,
        "preferred_language": customer.preferred_language or "English",
        "customer_id": customer.id,
    }


@router.patch("/profile")
def update_profile(
    profile: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer = db.query(Customer).filter(Customer.user_id == user.id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    customer.preferred_language = profile.preferred_language
    db.commit()
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "picture": user.picture,
        "role": user.role,
        "preferred_language": customer.preferred_language,
        "customer_id": customer.id,
    }


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Signed out"}
