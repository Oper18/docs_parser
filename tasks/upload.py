from tasks.base import BaseTaskRunner
from db.typesense.models import UploadTaskType


class UploadTaskRunner(BaseTaskRunner):
    _task_type = UploadTaskType.upload.value
