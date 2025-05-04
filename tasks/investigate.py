from tasks.base import BaseTaskRunner
from db.typesense.models import UploadTaskType


class InvestigateTaskRunner(BaseTaskRunner):
    _task_type = UploadTaskType.investigate.value
