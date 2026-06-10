import psycopg
from sqlmodel import Session, text
from core.database.database import engine


def test_postgres_is_alive_psycopg():
    conn = psycopg.connect(
        host="localhost",
        port=5433,
        dbname="postgres",
        user="postgres",
        password="postgres",
    )

    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        row = cur.fetchone()

        assert row is not None
        assert row[0] == 1
    conn.close()


def test_postgres_is_alive_sqlmodel():
    with Session(engine) as session:
        result = session.execute(text("SELECT 1"))
        row = result.one()

        assert row[0] == 1
