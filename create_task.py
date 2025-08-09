import sys
import asyncio

from typesense.exceptions import ObjectAlreadyExists

from core.settings import settings
from lib.typesense.client import AsyncClient
from db.typesense.models import UploadTaskModel, UploadTaskType, BookPageModel
from service.upload import FileUploader


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
    service = FileUploader(client, "kgb_project")
    await service.create_investigate_task(sys.argv[1], sys.argv[2], "google")
    try:
        await client.create_collection("kgb_project", BookPageModel)
    except ObjectAlreadyExists:
        pass


if __name__ == "__main__":
    asyncio.run(main())
