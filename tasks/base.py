import asyncio
import logging

from typesense.exceptions import ObjectAlreadyExists

from lib.typesense.client import AsyncClient
from db.typesense.models import UploadTaskModel, UploadTaskType, UploadTaskStatus
from services.upload import FileUploader


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class BaseTaskRunner:
    _task_type: str = ""
    _service_method_task_type_map = {
        UploadTaskType.upload: "upload_file_content",
        UploadTaskType.investigate: "create_upload_files_tasks",
    }

    def __init__(self, client: AsyncClient):
        self.client = client
        self.service = FileUploader(self.client, "")

    async def reset_pending_tasks(self):
        logger.info(
            f"{self.__class__.__name__}, Looking for tasks with status {UploadTaskStatus.pending.value} and type {self._task_type}"
        )
        res = await self.client.collections["tasks"].documents.asearch(
            {
                "q": "*",
                "query_by": "project_name",
                "limit": 10,
                "filter_by": f"status:={UploadTaskStatus.pending.value} && task_type:={self._task_type}",
            }
        )
        for hit in res["hits"]:
            _obj = hit["document"]
            _obj["status"] = UploadTaskStatus.waiting.value
            await self.client.collections["tasks"].documents[_obj["id"]].aupdate(_obj)

    async def get_waiting_tasks(self):
        logger.info(
            f"{self.__class__.__name__}, Looking for tasks with status {UploadTaskStatus.waiting.value} and type {self._task_type}"
        )
        res = await self.client.collections["tasks"].documents.asearch(
            {
                "q": "*",
                "query_by": "project_name",
                "limit": 10,
                "filter_by": f"status:={UploadTaskStatus.waiting.value} && task_type:={self._task_type}",
            }
        )
        return [hit["document"] for hit in res["hits"]]

    async def _mark_task_failed(self, task: dict):
        task["status"] = UploadTaskStatus.failed
        await self.client.collections["tasks"].documents[task["id"]].update(task)

    async def process_task(self, task: dict):
        try:
            task_obj = UploadTaskModel.model_validate(task)
        except Exception as e:
            logger.error(
                f"{self.__class__.__name__}, Failed model validation for task {task["id"]}: {e}"
            )
            await self._mark_task_failed(task)
            return
        else:
            self.service.project_name = task_obj.project_name
            method = getattr(
                self.service,
                self._service_method_task_type_map.get(task_obj.task_type),
                None,
            )
            if not method:
                logger.error(
                    f"{self.__class__.__name__}, Method for {task_obj.task_type} was not found"
                )
                await self._mark_task_failed(task)
                return
            await method(task["id"], task_obj)

    async def run(self):
        try:
            await self.client.create_collection("tasks", UploadTaskModel)
        except ObjectAlreadyExists:
            pass
        await self.reset_pending_tasks()
        while True:
            tasks = await self.get_waiting_tasks()
            for task in tasks:
                await self.process_task(task)
            if not tasks:
                logger.info(f"{self.__class__.__name__}, No tasks found")
                await asyncio.sleep(60)
