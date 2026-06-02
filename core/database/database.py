from sqlmodel import SQLModel, create_engine, Session

DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "test_sqlmodel"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)


def create_tables():
    SQLModel.metadata.create_all(engine)


def get_db():
    with Session(engine) as session:
        yield session
