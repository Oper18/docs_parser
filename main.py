from fastapi import FastAPI

from middlewares import AuthMiddleware
from api.v1.router import router as v1_router

app = FastAPI()


app.add_middleware(AuthMiddleware)
app.include_router(v1_router)
