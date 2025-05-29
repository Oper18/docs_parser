from typing import List

from fastapi import APIRouter, Depends, Request

from api.v1.models.search import BookPageSearchRequest, BookPageResponse
from api.dependencies.auth import authenticated_user
from api.dependencies.services import search_service
from services.search import TextSearch
from db.models import User

router = APIRouter(prefix="/search", tags=["search"])


@router.post(r"", responses={200: {"model": List[BookPageResponse]}})
async def send_message_handler(
    request: Request,
    data: BookPageSearchRequest,
    search_service_obj: TextSearch = Depends(search_service),
    user: User = Depends(authenticated_user),
) -> List[BookPageResponse]:
    search_service_obj.project_name = data.project_name
    return await search_service_obj.search(data.query)
