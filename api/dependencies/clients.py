from core.settings import settings
from lib.typesense.client import AsyncClient


async def typesense_client() -> AsyncClient:
    return AsyncClient(
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
