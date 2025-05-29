from typing import List
from pydantic import BaseModel, Field
from db.typesense.models import BookPageModel


class BookPageSearchRequest(BaseModel):
    query: str
    project_name: str = "kgb_project"


class BookPageResponse(BookPageModel):
    snippets: List[str] = Field(default_factory=list)
