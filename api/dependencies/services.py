from fastapi import Depends
from services.search import TextSearch
from lib.typesense.client import AsyncClient
from api.dependencies.clients import typesense_client


async def search_service(
    typesense_client_obj: AsyncClient = Depends(typesense_client),
) -> TextSearch:
    return TextSearch(client=typesense_client_obj, project_name="")
