from fastapi import Depends
from services.search import TextSearch
from services.upload import FileUploader
from lib.typesense.client import AsyncClient
from api.dependencies.clients import typesense_client
from api.v1.models.tasks import InvestigateTaskCreateRequest


async def search_service(
    typesense_client_obj: AsyncClient = Depends(typesense_client),
) -> TextSearch:
    return TextSearch(client=typesense_client_obj, project_name="")


async def upload_service(
    data: InvestigateTaskCreateRequest,
    typesense_client_obj: AsyncClient = Depends(typesense_client),
) -> FileUploader:
    return FileUploader(client=typesense_client_obj, project_name=data.project_name)
