from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.database.crud import create_database_if_not_exists
from core.settings.default import AppSettings, setup_logging

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = AppSettings()
        setup_logging(settings)
        create_database_if_not_exists(settings)
        yield

    finally:
        pass


def boostrap(settings: AppSettings | None = None) -> FastAPI:
    if settings is None:
        settings = AppSettings()

    app = FastAPI(
        lifespan=lifespan,
        title=settings.TITLE,
        version=settings.VERSION,
        generate_unique_id_function=lambda route: route.name,
        openapi_url=settings.OPENAPI_URL,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOCS_URL,
    )
    return app


app = boostrap()


@app.get("/")
async def hello_world():
    return {"message": "Hello, World!"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
