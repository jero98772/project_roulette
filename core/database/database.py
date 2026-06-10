from sqlmodel import SQLModel, create_engine, Session
from core.settings.default import AppSettings


settings = AppSettings()

engine = create_engine(settings.db_url, echo=True)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_db():
    with Session(engine) as session:
        yield session
