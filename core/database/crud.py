import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from core.settings.default import AppSettings

logger = logging.getLogger(__name__)


def database_exists(cursor, db_name: str) -> bool:
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    return cursor.fetchone() is not None


def create_database(cursor, db_name: str) -> None:
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))


def create_database_if_not_exists(settings: AppSettings) -> None:
    conn = psycopg2.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database="postgres",
    )
    logger.info("Connecting to postgress database")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    exists = database_exists(cursor, settings.DB_NAME)

    if not exists:
        create_database(cursor, settings.DB_NAME)
        logger.info("Database '%s' created.", settings.DB_NAME)
    else:
        logger.info("Database '%s' already exists.", settings.DB_NAME)

    cursor.close()
    conn.close()
