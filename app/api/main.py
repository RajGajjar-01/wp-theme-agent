from fastapi import APIRouter

from app.api.routes import convert, health, upload

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(convert.router, tags=["convert"])
