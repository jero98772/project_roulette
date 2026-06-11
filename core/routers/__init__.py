from fastapi import APIRouter

from .health import router as health_router
from .catalog import router as catalog_router
from .ensable_project import router as ensable_project_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(catalog_router)
v1_router.include_router(ensable_project_router)
api_router.include_router(v1_router)
