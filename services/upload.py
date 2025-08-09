import asyncio
from typing import IO, List, Optional, Tuple
import io
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from core.settings import settings
from lib.typesense.client import AsyncClient
from lib.converter.base import BaseConverter
from lib.converter.pdf.reader import PdfReader
from lib.converter.word.reader import WordReader
from db.typesense.models import UploadTaskModel, UploadTaskType, UploadTaskStatus


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class FileUploader:
    _ext_converter_map = {"pdf": PdfReader, "docx": WordReader, "doc": WordReader}

    def __init__(self, client: AsyncClient, project_name: str):
        self.client = client
        self.project_name = project_name
        self.google_service = None

    async def create_converter(
        self, file_path: str, file_content: IO[bytes], file_ext: str, *args, **kwargs
    ) -> BaseConverter:
        logger.info(f"Creating converter for {file_ext} file.")
        converter_cls = self._ext_converter_map.get(file_ext.lower())
        if not converter_cls:
            raise ValueError(f"Unsupported file format {file_ext}")
        return await converter_cls.create(
            self.client,
            self.project_name,
            file_path,
            content=file_content,
            *args,
            **kwargs,
        )

    def _sync_google_load_file(
        self, file_id: str, file_name: str = ""
    ) -> Tuple[str, bytes]:
        if not self.google_service:
            credentials = service_account.Credentials.from_service_account_file(
                settings.google_service_account_file,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            self.google_service = build("drive", "v3", credentials=credentials)
        if not file_name:
            file_info = (
                self.google_service.files()
                .get(fileId=file_id, fields="id, name, mimeType, modifiedTime, size")
                .execute()
            )
            logger.info(f"Google file info: {file_info}")
            file_name = file_info["name"]
        request = self.google_service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f"Download {int(status.progress() * 100)}% complete.")

        file_bytes = buffer.getvalue()
        logger.info(f"Downloaded {len(file_bytes)} bytes.")
        return file_name, file_bytes

    async def _google_upload_file_content(self, task: UploadTaskModel):
        loop = asyncio.get_event_loop()
        file_name, file_bytes = await loop.run_in_executor(
            None, self._sync_google_load_file, task.file_path, task.file_name
        )
        file_ext = file_name.split(".")[-1]
        converter_obj = await self.create_converter(
            file_name, file_bytes, file_ext, lang=task.lang
        )
        await converter_obj.save_to_db()

    async def upload_file_content(self, task_id: str, task: UploadTaskModel):
        if task.task_type != UploadTaskType.upload:
            logger.info(f"Uploading files accept for task {UploadTaskType.upload} only")
            return
        task.status = UploadTaskStatus.pending
        await (
            self.client.collections["tasks"]
            .documents[task_id]
            .aupdate(task.model_dump(mode="json"))
        )
        logger.info(f"Start file {task.file_path}-{task.file_name} uploading...")
        method = getattr(self, f"_{task.provider}_upload_file_content", None)
        if not method:
            logger.info(f"Failed file {task.file_path}-{task.file_name} uploading")
            task.status = UploadTaskStatus.failed
        else:
            await method(task)
            logger.info(f"Complete file {task.file_path}-{task.file_name} uploading")
            task.status = UploadTaskStatus.success
        await (
            self.client.collections["tasks"]
            .documents[task_id]
            .aupdate(task.model_dump(mode="json"))
        )
        logger.info(f"Update task {task_id} status to {task.status}")

    def _check_upload_task_exists(self, file_path: str, project_name: str) -> bool:
        query_params = {
            "q": "*",
            "query_by": "file_path",
            "filter_by": f"file_path:{file_path} && status:[{UploadTaskStatus.waiting.value},{UploadTaskStatus.pending.value},{UploadTaskStatus.success.value}]",
            "limit": 1,
        }
        res = self.client.collections[project_name].documents.search(query_params)
        return len(res["hits"]) > 0

    def _sync_google_list_folder(
        self, folder_id: str, task: UploadTaskModel, folder_name: str = ""
    ) -> List[UploadTaskModel]:
        if not self.google_service:
            credentials = service_account.Credentials.from_service_account_file(
                settings.google_service_account_file,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            self.google_service = build("drive", "v3", credentials=credentials)
        tasks = list()
        results = (
            self.google_service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed=false",
                pageSize=1000,
                fields="files(id, name, mimeType)",
            )
            .execute()
        )
        for item in results.get("files", []):
            if item["mimeType"].split(".")[
                -1
            ] != "folder" and not self._check_upload_task_exists(
                item["id"], task.project_name
            ):
                tasks.append(
                    UploadTaskModel(
                        lang=task.lang,
                        file_path=item["id"],
                        project_name=task.project_name,
                        file_name=f"{folder_name}/{item['name']}",
                        task_type=UploadTaskType.upload,
                        provider=task.provider,
                    )
                )
            else:
                tasks.extend(
                    self._sync_google_list_folder(
                        item["id"], task, f"{folder_name}/{item['name']}"
                    )
                )
        return tasks

    async def _google_create_upload_files_tasks(self, task: UploadTaskModel):
        loop = asyncio.get_event_loop()
        tasks = await loop.run_in_executor(
            None, self._sync_google_list_folder, task.file_path, task
        )
        await self.client.collections["tasks"].documents.aimport_(
            [task.model_dump(mode="json") for task in tasks], {"action": "create"}
        )

    async def create_upload_files_tasks(self, task_id: str, task: UploadTaskModel):
        task.status = UploadTaskStatus.pending
        await (
            self.client.collections["tasks"]
            .documents[task_id]
            .aupdate(task.model_dump(mode="json"))
        )
        method = getattr(self, f"_{task.provider}_create_upload_files_tasks", None)
        if not method:
            task.status = UploadTaskStatus.failed
        else:
            await method(task)
            task.status = UploadTaskStatus.success
        await (
            self.client.collections["tasks"]
            .documents[task_id]
            .aupdate(task.model_dump(mode="json"))
        )

    async def get_tasks(
        self,
        task_type: UploadTaskType,
        status: Optional[UploadTaskStatus] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> List[UploadTaskModel]:
        query_params = {
            "q": "*",
            "query_by": "task_type",
            "filter_by": f"task_type:{task_type.value}",
            "page": page,
            "per_page": per_page,
        }
        if status:
            query_params["filter_by"] += f" && status:{status.value}"
        res = await self.client.collections["tasks"].documents.asearch(query_params)
        return [UploadTaskModel.model_validate(hit["document"]) for hit in res["hits"]]

    def _google_build_task_model(self, file_path: str, lang: str) -> UploadTaskModel:
        if "http" in file_path:
            file_path = file_path.split("/")[-1]
        return UploadTaskModel(
            lang=lang,
            file_path=file_path,
            project_name=self.project_name,
            provider="google",
            task_type=UploadTaskType.investigate,
        )

    async def create_investigate_task(
        self, file_path: str, lang: str, provider: str
    ) -> UploadTaskModel:
        method = getattr(self, f"_{provider}_build_task_model", None)
        if not method:
            raise ValueError(f"Unsupported provider: {provider}")
        task = method(file_path, lang)
        await self.client.collections["tasks"].documents.acreate(
            task.model_dump(mode="json")
        )
