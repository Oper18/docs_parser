from fastapi import HTTPException, Request
from starlette import status
from db.models import User


def authenticated_user(request: Request) -> User:
    if request.user.authorized:
        return request.user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authorized"
    )
