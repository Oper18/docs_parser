from enum import Enum
from pydantic import BaseModel


class UploadTaskStatus(str, Enum):
    waiting = "waiting"
    pending = "pending"
    success = "success"
    failed = "failed"


class UploadTaskType(str, Enum):
    investigate = "investigate"
    upload = "upload"


class BookPageModel(BaseModel):
    file_path: str
    book_name: str
    page_number: int
    page_content: str

    class Config:
        default_sorting_field = "page_number"


class UploadTaskModel(BaseModel):
    lang: str
    file_path: str
    project_name: str
    status: UploadTaskStatus = UploadTaskStatus.waiting
    provider: str
    file_name: str = ""
    task_type: UploadTaskType = UploadTaskType.investigate
    priority: int = 1

    class Config:
        use_enum_values = True
        default_sorting_field = "priority"
