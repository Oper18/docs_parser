import os
import aiohttp
import aiofiles
import io
from abc import abstractmethod
from typing import IO, List

from db.typesense.models import BookPageModel
from lib.typesense.client import AsyncClient


class BaseConverter:
    _chunk_size = 50

    def __init__(
        self, client: AsyncClient, project_name: str, file_path: str, *args, **kwargs
    ):
        self.project_name = project_name
        self.client = client
        self.file_path = file_path
        self.reader = kwargs.get("reader")
        self.content: bytes = kwargs.get("content", b"")

    @classmethod
    async def create(
        cls, client: AsyncClient, project_name: str, file_path: str, *args, **kwargs
    ):
        instance = cls(client, project_name, file_path, *args, **kwargs)
        if not instance.reader or not instance.content:
            await instance.load_content()
        return instance

    async def download_file(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                return io.BytesIO(content)

    async def load_content(self):
        if not self.content:
            if self.file_path.startswith(("http://", "https://")):
                content = await self.download_file(self.file_path)
                self.file_name = os.path.basename(self.file_path)
            else:
                async with aiofiles.open(self.file_path, mode="rb") as file:
                    content = await file.read()
                self.file_name = os.path.basename(self.file_path)

            self.content = content

    @abstractmethod
    async def collect_pages(self) -> List[BookPageModel]:
        pass

    async def _save_to_typesense(
        self, pages: List[BookPageModel], *args, **kwargs
    ) -> None:
        await self.client.collections[self.project_name].documents.aimport_(
            [page.model_dump(mode="json") for page in pages], {"action": "create"}
        )

    async def save_to_db(self, db_name: str = "typesense", *args, **kwargs) -> None:
        method = getattr(self, f"_save_to_{db_name}", None)
        if not method:
            raise ValueError(f"Unsupported database: {db_name}")
        pages = await self.collect_pages()
        return await method(pages, *args, **kwargs)
