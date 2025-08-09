from pydantic import BaseModel


class InvestigateTaskCreateRequest(BaseModel):
    lang: str
    file_path: str
    project_name: str
    provider: str
