import asyncio
import io
from typing import List
from docx import Document

from db.typesense.models import BookPageModel
from lib.converter.base import BaseConverter


class WordReader(BaseConverter):
    _chars_per_page = 3300

    async def load_content(self):
        await super().load_content()
        loop = asyncio.get_running_loop()
        pdf_io = io.BytesIO(self.content)
        self.reader = await loop.run_in_executor(None, Document, pdf_io)

    async def collect_pages(self) -> List[BookPageModel]:
        book_name = self.file_path
        pages = list()
        page_num = 1
        current_text = ""
        char_count = 0

        for para in self.reader.paragraphs:
            para_text = para.text + "\n"
            char_count += len(para_text)
            current_text += para_text

            if char_count >= self._chars_per_page:
                pages.append(
                    BookPageModel(
                        file_path=self.file_path,
                        book_name=book_name,
                        page_number=page_num,
                        page_content=current_text.strip(),
                    )
                )
                page_num += 1
                current_text = ""
                char_count = 0

        if current_text.strip():
            pages.append(
                BookPageModel(
                    file_path=self.file_path,
                    book_name=book_name,
                    page_number=page_num,
                    page_content=current_text.strip(),
                )
            )

        return pages
