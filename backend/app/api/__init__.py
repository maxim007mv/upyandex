from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.subscribers import router as subscribers_router
from app.api.templates import router as templates_router
from app.api.mailings import router as mailings_router
from app.api.stats import router as stats_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(subscribers_router)
api_router.include_router(templates_router)
api_router.include_router(mailings_router)
api_router.include_router(stats_router)
