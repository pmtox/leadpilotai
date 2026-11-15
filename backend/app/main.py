import secrets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from starlette.middleware.sessions import SessionMiddleware
from backend.app.core.config import settings
from backend.app.database.connection import engine
from backend.app.database.base import Base
# Import models to ensure they are registered with Base.metadata
import backend.app.models
from backend.app.api.customers import router as customers_router
from backend.app.api.conversations import router as conversations_router
from backend.app.api.leads import router as leads_router
from backend.app.api.actions import router as actions_router
from backend.app.api.callbacks import router as callbacks_router
from backend.app.api.auth import router as auth_router

# Initialize database tables
Base.metadata.create_all(bind=engine)

def migrate_existing_columns():
    """Add nullable fields to existing MVP databases without losing local data."""
    additions = {
        "customers": {
            "email": "VARCHAR(254)",
            "user_id": "INTEGER REFERENCES users(id)",
        },
        "leads": {"budget_min": "FLOAT", "budget_max": "FLOAT"},
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, columns in additions.items():
            if not inspector.has_table(table_name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.exec_driver_sql(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                    )
        connection.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_customers_user_id ON customers (user_id)"
        )

migrate_existing_columns()

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous Multilingual AI Sales Agent Backend API",
    version="1.0.0"
)

if not settings.AUTH_SESSION_SECRET and settings.APP_ENV.casefold() == "production":
    raise RuntimeError("AUTH_SESSION_SECRET must be set in production.")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.AUTH_SESSION_SECRET or secrets.token_urlsafe(32),
    same_site="lax",
    https_only=settings.APP_ENV.casefold() == "production",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(conversations_router)
app.include_router(leads_router)
app.include_router(actions_router)
app.include_router(callbacks_router)

@app.get("/")
def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
        "checkpoint": "CP-01"
    }

@app.get("/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": f"{engine.dialect.name}_connected",
        "cors_allowed": settings.cors_origins_list
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
