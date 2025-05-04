import asyncio
from typing import List
from pypdf import PdfWriter
from pdf2image import convert_from_bytes
import pytesseract
import io

from db.typesense.models import BookPageModel
from lib.converter.pdf.base_reader import BasePdfConverter
from lib.typesense.client import AsyncClient


class PdfImageConverter(BasePdfConverter):
    def __init__(
        self, client: AsyncClient, project_name: str, file_path: str, *args, **kwargs
    ):
        super().__init__(client, project_name, file_path, *args, **kwargs)
        self.lang: str = kwargs.get("lang", "eng")

    async def get_title(self) -> str:
        if self.reader.metadata and self.reader.metadata.title:
            return self.reader.metadata.title
        first_page = self.reader.pages[0]
        text = first_page.extract_text()
        lines = text.split("\n")
        return next((line.strip() for line in lines if line.strip()), "")

    async def _pages_chunk(self):
        total_pages = self.reader.get_num_pages()
        for i in range(0, total_pages, self._chunk_size):
            writer = PdfWriter()
            for j in range(i, min(i + self._chunk_size, total_pages)):
                writer.add_page(self.reader.get_page(j))
            buffer = io.BytesIO()
            writer.write(buffer)
            yield buffer.getvalue()
            buffer.close()

    async def collect_pages(self) -> List[BookPageModel]:
        book_name = await self.get_title() or self.file_name
        pages = []
        loop = asyncio.get_running_loop()

        async for bytes_chunk in self._pages_chunk():
            pdf_images = await loop.run_in_executor(None, convert_from_bytes, bytes_chunk)

            for page_num, image in enumerate(pdf_images, start=1):
                text = await loop.run_in_executor(
                    None, pytesseract.image_to_string, image, self.lang
                )
                pages.append(
                    BookPageModel(
                        file_path=self.file_path,
                        book_name=book_name,
                        page_number=page_num,
                        page_content=text,
                    )
                )
        return pages
