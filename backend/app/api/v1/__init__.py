"""API v1"""

from fastapi import APIRouter
from app.api.v1 import utils

api_router = APIRouter()
api_router.include_router(utils.router)

__all__ = ["api_router"]
