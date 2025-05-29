import re
from typing import Tuple
from fastapi import Request
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp, Receive, Scope, Send

from db.models import User
from core.settings import settings


class HeadersParsing:
    def __init__(self, headers: Headers):
        self.headers = headers

    @property
    def range(self) -> Tuple[int, int]:
        value = self.headers.get("Range", "")
        if not value:
            return 0, 0
        return self._get_range_header_value(value)

    def _get_range_header_value(self, value: str) -> Tuple[int, int]:
        if not value:
            return 0, 0
        _from = re.search(r"[0-9]+-", value)
        if _from:
            _from = int(_from.group().replace("-", ""))
        else:
            _from = 0
        _to = re.search(r"-[0-9]+", value)
        if _to:
            _to = int(_to.group().replace("-", ""))
        else:
            _to = 0
        return _from, _to

    @property
    def auth_token(self) -> str:
        value = self.headers.get("authorization", "")
        if not value:
            return ""
        value = value.split(" ")
        if len(value) < 2:
            return ""
        return value[1]

    @property
    def connection_id(self) -> str:
        return self.headers.get("connectionid", "")


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *args, **kwargs) -> None:
        self.app = app
        super().__init__(app, *args, **kwargs)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not scope.get("headers"):
            scope["headers"] = list()
        headers = Headers(scope=scope)
        headers_parser = HeadersParsing(headers)
        scope["user"] = User(pk="", username="")
        scope["auth"] = {"status": False, "reason": ""}
        if headers_parser.auth_token and headers_parser.auth_token == settings.api_token:
            scope["user"] = User(pk="1", username="admin", authorized=True)
            scope["auth"]["reason"] = ""
            scope["auth"]["status"] = True
        else:
            scope["auth"]["reason"] = "no token"

        await super().__call__(scope, receive, send)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        return await call_next(request)
