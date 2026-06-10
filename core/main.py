from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.database.crud import create_database_if_not_exists
from core.settings import setup_logging

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        setup_logging()
        create_database_if_not_exists()
        yield

    finally:
        pass


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
