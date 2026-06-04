from fastapi import FastAPI

from app.api.v1.rooms import router as rooms_router

app = FastAPI()

app.include_router(rooms_router, prefix="/api/v1")
