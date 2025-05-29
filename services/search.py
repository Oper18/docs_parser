from typing import List
from lib.typesense.client import AsyncClient
from api.v1.models.search import BookPageResponse


class TextSearch:
    def __init__(self, client: AsyncClient, project_name: str):
        self.client = client
        self.project_name = project_name

    async def search(self, query: str) -> List[BookPageResponse]:
        query_params = {
            "q": query,
            "query_by": "book_name,page_content",
            "sort_by": "page_number:asc",
            "order": "asc",
        }
        res = await self.client.collections[self.project_name].documents.asearch(
            query_params
        )
        return [
            BookPageResponse(
                **hit["document"],
                snippets=[highlight["snippet"] for highlight in hit["highlights"]],
            )
            for hit in res["hits"]
            if hit.get("document")
        ]
