from fastapi import APIRouter

import STGB_backend.endpoints.api as api
import STGB_backend.endpoints.auth as auth

api_router = APIRouter()

api_router.include_router(api.router, tags=['api'])
api_router.include_router(auth.router, tags=['auth'])
