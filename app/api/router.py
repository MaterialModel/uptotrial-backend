"""API router for endpoints."""

from fastapi import APIRouter

from app.api.endpoints import chat, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/v1/health", tags=["Health"])
api_router.include_router(chat.router, prefix="/v1/sessions", tags=["Chat"])