import asyncio
import functools

from pydantic import BaseModel

from typesense import Client
from typesense.api_call import ApiCall
from typesense.collections import Collection, Collections
from typesense.documents import Document, Documents

from db.typesense.models import BookPageModel


class AsyncObjectGeneric:
    def __getattr__(self, name):
        if name[0] == "a":
            method = getattr(self, name[1:], None)
            if not method:
                raise AttributeError(
                    f"{self.__class__.__name__}, Attribute {name} not found"
                )

            @functools.wraps(method)
            async def async_wrapper(*args, **kwargs):
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, method, *args, **kwargs)

            return async_wrapper
        raise AttributeError(f"{self.__class__.__name__}, Attribute {name} not found")


class AsyncDocument(Document, AsyncObjectGeneric):
    pass


class AsyncDocuments(Documents, AsyncObjectGeneric):
    def __getitem__(self, document_id: str) -> AsyncDocument:
        if document_id not in self.documents:
            self.documents[document_id] = AsyncDocument(
                self.api_call, self.collection_name, document_id
            )

        return self.documents[document_id]


class AsyncCollection(Collection, AsyncObjectGeneric):
    def __init__(self, api_call: ApiCall, name: str):
        super().__init__(api_call, name)
        self.documents: AsyncDocuments = AsyncDocuments(api_call, name)


class AsyncCollections(Collections, AsyncObjectGeneric):
    def __getitem__(self, collection_name: str) -> AsyncCollection:
        if not self.collections.get(collection_name):
            self.collections[collection_name] = AsyncCollection(
                self.api_call, collection_name
            )
        return self.collections[collection_name]


class AsyncClient(Client, AsyncObjectGeneric):
    _TYPES_MAP = {str: "string", int: "int64"}

    def __init__(self, config_dict):
        super().__init__(config_dict)
        self.collections: AsyncCollections = AsyncCollections(self.api_call)

    def get_collection_fields_from_model(self, model: BaseModel):
        return [
            {"name": name, "type": self._TYPES_MAP.get(field.annotation, "string")}
            for name, field in model.model_fields.items()
        ]

    async def create_collection(
        self, collection_name: str, model: BaseModel = BookPageModel
    ):
        return await self.collections.acreate(
            {
                "name": collection_name,
                "fields": self.get_collection_fields_from_model(model),
                "default_sorting_field": model.Config.default_sorting_field,
            }
        )
