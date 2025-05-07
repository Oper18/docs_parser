from abc import abstractmethod
import asyncio
import aiohttp
import io
from pypdf import PdfReader
from typing import IO

from lib.typesense.client import AsyncClient
from lib.converter.base import BaseConverter


class BasePdfConverter(BaseConverter):
    _chunk_size = 20

    def __init__(
        self, client: AsyncClient, project_name: str, file_path: str, *args, **kwargs
    ):
        super().__init__(client, project_name, file_path, *args, **kwargs)
        self.file_name = ""

    async def download_file(self, url: str | IO[bytes]):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                return io.BytesIO(content)

    async def load_content(self):
        await super().load_content()
        loop = asyncio.get_running_loop()
        pdf_io = io.BytesIO(self.content)
        self.reader = await loop.run_in_executor(None, PdfReader, pdf_io)

    @abstractmethod
    async def get_title(self) -> str:
        pass
