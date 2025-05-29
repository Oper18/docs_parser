from functools import lru_cache
from pydantic_settings import BaseSettings


class TypesenseSettings(BaseSettings):
    typesense_host: str = "localhost"
    typesense_port: int = 8108
    typesense_protocol: str = "http"
    typesense_api_key: str


class GoogleSettings(BaseSettings):
    google_service_account_file: str


class Settings(TypesenseSettings, GoogleSettings):
    api_token: str = "dev_token"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
