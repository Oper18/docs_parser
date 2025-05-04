from typing import IO
from lib.converter.pdf.base_reader import BasePdfConverter
from lib.converter.pdf.img_reader import PdfImageConverter
from lib.converter.pdf.text_reader import PdfTextConverter
from lib.typesense.client import AsyncClient


class PdfReader:
    content_class_map = {"text": PdfTextConverter, "image": PdfImageConverter}

    def __init__(self, *args, **kwargs):
        self.obj = None

    def __getattr__(self, name):
        if hasattr(self.obj, name):
            return getattr(self.obj, name)
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object and its 'obj' have no attribute '{name}'"
            )

    @classmethod
    async def create(
        cls,
        client: AsyncClient,
        project_name: str,
        file_path: str | IO[bytes],
        *args,
        **kwargs,
    ):
        instance = cls()
        instance.obj = await BasePdfConverter.create(
            client, project_name, file_path, *args, **kwargs
        )
        content_type = await instance.detect_content_type()
        obj = cls.content_class_map.get(content_type, BasePdfConverter)
        instance.obj = await obj.create(
            client,
            project_name,
            file_path,
            reader=instance.obj.reader,
            content=instance.obj.content,
            lang=kwargs.get("lang", "eng"),
        )
        return instance

    async def detect_content_type(self, text_threshold: int = 100) -> str:
        """
        Detect whether the first page of the PDF contains primarily text or images.

        :param text_threshold: Minimum number of characters to consider a page as text (default: 100)
        :return: 'text' if the first page is primarily text, 'image' otherwise
        """
        if not self.reader or not self.reader.pages:
            raise ValueError("PDF has not been loaded or is empty")

        first_page = self.reader.pages[0]
        text = first_page.extract_text()

        if len(text.strip()) >= text_threshold:
            return "text"
        else:
            return "image"
