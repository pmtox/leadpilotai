from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous Multilingual AI Sales Agent Backend API",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
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
    return {
        "status": "healthy",
        "database": "sqlite_connected",
        "cors_allowed": settings.cors_origins_list
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
