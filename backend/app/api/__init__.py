from backend.app.api.customers import router as customers_router
from backend.app.api.conversations import router as conversations_router
from backend.app.api.leads import router as leads_router
from backend.app.api.actions import router as actions_router
from backend.app.api.callbacks import router as callbacks_router

__all__ = [
    "customers_router",
    "conversations_router",
    "leads_router",
    "actions_router",
    "callbacks_router"
]
