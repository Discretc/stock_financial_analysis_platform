"""
V1 API router — aggregates all sub-routers.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.financials import router as financials_router
from app.api.v1.stocks import router as stocks_router
from app.api.v1.watchlists import router as watchlists_router
from app.api.v1.websocket import router as ws_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(stocks_router)
api_router.include_router(financials_router)
api_router.include_router(watchlists_router)
api_router.include_router(ws_router)
