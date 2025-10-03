"""API v1"""

from fastapi import APIRouter
from app.api.v1 import utils, cases

api_router = APIRouter()
api_router.include_router(utils.router)
api_router.include_router(cases.router)

__all__ = ["api_router"]
