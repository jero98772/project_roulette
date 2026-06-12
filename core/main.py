from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.database.database import init_db
from core.settings.default import AppSettings, setup_logging
from core.routers import api_router

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: AppSettings = app.state.settings
    try:
        setup_logging(settings)
        init_db()
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
    app.state.settings = settings
    app.include_router(api_router)

    return app


app = boostrap()
