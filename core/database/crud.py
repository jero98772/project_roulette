from sqlmodel import Session, select
from core.database.models import (
    Project,
    ProjectProgrammingLanguage,
    ProjectTech,
    ProjectAddon,
    ProjectExtra,
)

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def create_database_if_not_exists():
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database="postgres",  # Connect to default db first
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"Database '{DB_NAME}' created.")
    else:
        print(f"Database '{DB_NAME}' already exists.")

    cursor.close()
    conn.close()


def get_or_create_language(db: Session, name: str) -> ProjectProgrammingLanguage:
    obj = db.exec(
        select(ProjectProgrammingLanguage).where(
            ProjectProgrammingLanguage.name == name
        )
    ).first()
    if not obj:
        obj = ProjectProgrammingLanguage(name=name)
        db.add(obj)
        db.flush()
    return obj


def get_or_create_tech(db: Session, name: str) -> ProjectTech:
    obj = db.exec(select(ProjectTech).where(ProjectTech.name == name)).first()
    if not obj:
        obj = ProjectTech(name=name)
        db.add(obj)
        db.flush()
    return obj


def get_or_create_addon(db: Session, name: str) -> ProjectAddon:
    obj = db.exec(select(ProjectAddon).where(ProjectAddon.name == name)).first()
    if not obj:
        obj = ProjectAddon(name=name)
        db.add(obj)
        db.flush()
    return obj


def create_project(
    db: Session,
    language_name: str,
    tech_name: str | None = None,
    addon_name: str | None = None,
) -> Project:
    language = get_or_create_language(db, language_name)
    tech = get_or_create_tech(db, tech_name) if tech_name else None
    addon = get_or_create_addon(db, addon_name) if addon_name else None

    project = Project(
        programming_language_id=language.id,
        project_tech_id=tech.id if tech else None,
        project_addon_id=addon.id if addon else None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def get_all_projects(db: Session) -> list[Project]:
    return db.exec(select(Project)).all()


def delete_project(db: Session, project_id: int) -> bool:
    project = get_project(db, project_id)
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True


def add_extra_to_project(
    db: Session,
    project_id: int,
    language_name: str,
    tech_name: str | None = None,
    addon_name: str | None = None,
) -> ProjectExtra:
    language = get_or_create_language(db, language_name)
    tech = get_or_create_tech(db, tech_name) if tech_name else None
    addon = get_or_create_addon(db, addon_name) if addon_name else None

    extra = ProjectExtra(
        projects_id=project_id,
        project_programming_language_id=language.id,
        project_tech_id=tech.id if tech else None,
        project_addon_id=addon.id if addon else None,
    )
    db.add(extra)
    db.commit()
    db.refresh(extra)
    return extra
