import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from core.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
)


logger = logging.getLogger(__name__)


def database_exists(cursor, db_name: str) -> bool:
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    return cursor.fetchone() is not None


def create_database(cursor, db_name: str) -> None:
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))


def create_database_if_not_exists() -> None:
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    exists = database_exists(cursor, DB_NAME)

    if not exists:
        create_database(cursor, DB_NAME)
        logger.info("Database '%s' created.", DB_NAME)
    else:
        logger.info("Database '%s' already exists.", DB_NAME)

    cursor.close()
    conn.close()
