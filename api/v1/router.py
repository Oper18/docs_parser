from fastapi import APIRouter

from .routes.search import router as search_router

router = APIRouter(prefix="/v1", tags=["v1"])


router.include_router(search_router)
