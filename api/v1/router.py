from fastapi import APIRouter

from .routes.search import router as search_router
from .routes.tasks import router as tasks_router

router = APIRouter(prefix="/v1")


router.include_router(search_router)
router.include_router(tasks_router)
