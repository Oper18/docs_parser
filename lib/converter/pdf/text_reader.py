from typing import List

from db.typesense.models import BookPageModel
from lib.converter.pdf.base_reader import BasePdfConverter


class PdfTextConverter(BasePdfConverter):
    async def get_title(self) -> str:
        if self.reader.metadata.title:
            return self.reader.metadata.title
        first_page = self.reader.get_page(0)
        text = first_page.extract_text()
        lines = text.split("\n")
        return next((line.strip() for line in lines if line.strip()), "")

    async def collect_pages(self) -> List[BookPageModel]:
        book_name = await self.get_title() or self.file_name
        pages = list()
        for page_num, page in enumerate(self.reader.pages, start=1):
            text = page.extract_text()
            pages.append(
                BookPageModel(
                    file_path=self.file_path,
                    book_name=book_name,
                    page_number=page_num,
                    page_content=text,
                )
            )
        return pages
