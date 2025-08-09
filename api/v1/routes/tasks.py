from fastapi import APIRouter, Depends, Request

from api.v1.models.tasks import InvestigateTaskCreateRequest
from api.dependencies.auth import authenticated_user
from api.dependencies.services import upload_service
from services.upload import FileUploader
from db.models import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(r"", responses={200: {"model": dict}})
async def create_task_handler(
    request: Request,
    data: InvestigateTaskCreateRequest,
    upload_service_obj: FileUploader = Depends(upload_service),
    user: User = Depends(authenticated_user),
) -> dict:
    await upload_service_obj.search(data.file_path, data.lang, data.provider)
    return dict()
