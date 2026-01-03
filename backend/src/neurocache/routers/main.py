from fastapi import APIRouter

from neurocache.routers import chat_router, health_router, thread_router, user_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(health_router)
api_router.include_router(thread_router)
api_router.include_router(user_router)
