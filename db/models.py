from pydantic import BaseModel


class User(BaseModel):
    pk: str
    username: str
    authorized: bool = False
