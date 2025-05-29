import sys
import asyncio

from typesense.exceptions import ObjectAlreadyExists

from core.settings import settings
from lib.typesense.client import AsyncClient
from db.typesense.models import UploadTaskModel, UploadTaskType, BookPageModel


async def main():
    client = AsyncClient(
        {
            "api_key": settings.typesense_api_key,
            "nodes": [
                {
                    "host": settings.typesense_host,
                    "port": settings.typesense_port,
                    "protocol": settings.typesense_protocol,
                }
            ],
            "connection_timeout_seconds": 10,
        }
    )
    task = UploadTaskModel(
        lang=sys.argv[2],
        file_path=sys.argv[1],
        project_name="kgb_project",
        provider="google",
        task_type=UploadTaskType.investigate,
    )
    await client.collections["tasks"].documents.acreate(task.model_dump(mode="json"))
    try:
        await client.create_collection("kgb_project", BookPageModel)
    except ObjectAlreadyExists:
        pass


if __name__ == "__main__":
    asyncio.run(main())
