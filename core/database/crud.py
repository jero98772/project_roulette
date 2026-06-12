from typing import Optional, Sequence, cast

import yaml
from sqlmodel import Session, select

from core.database.models import (
    Project,
    ProjectAddon,
    ProjectExtra,
    ProjectProgrammingLanguage,
    ProjectTech,
)


class ProgrammingLanguageCRUD:
    @staticmethod
    def create(session: Session, name: str) -> ProjectProgrammingLanguage:
        lang = ProjectProgrammingLanguage(name=name)
        session.add(lang)
        session.commit()
        session.refresh(lang)
        return lang

    @staticmethod
    def get(session: Session, lang_id: int) -> Optional[ProjectProgrammingLanguage]:
        return session.get(ProjectProgrammingLanguage, lang_id)

    @staticmethod
    def get_by_name(
        session: Session, name: str
    ) -> Optional[ProjectProgrammingLanguage]:
        return session.exec(
            select(ProjectProgrammingLanguage).where(
                ProjectProgrammingLanguage.name == name
            )
        ).first()

    @staticmethod
    def get_all(session: Session) -> Sequence[ProjectProgrammingLanguage]:
        return session.exec(select(ProjectProgrammingLanguage)).all()


class TechCRUD:
    @staticmethod
    def create(session: Session, name: str) -> ProjectTech:
        tech = ProjectTech(name=name)
        session.add(tech)
        session.commit()
        session.refresh(tech)
        return tech

    @staticmethod
    def get(session: Session, tech_id: int) -> Optional[ProjectTech]:
        return session.get(ProjectTech, tech_id)

    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[ProjectTech]:
        return session.exec(select(ProjectTech).where(ProjectTech.name == name)).first()

    @staticmethod
    def get_all(session: Session) -> Sequence[ProjectTech]:
        return session.exec(select(ProjectTech)).all()


class AddonCRUD:
    @staticmethod
    def create(session: Session, name: str) -> ProjectAddon:
        addon = ProjectAddon(name=name)
        session.add(addon)
        session.commit()
        session.refresh(addon)
        return addon

    @staticmethod
    def get(session: Session, addon_id: int) -> Optional[ProjectAddon]:
        return session.get(ProjectAddon, addon_id)

    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional[ProjectAddon]:
        return session.exec(
            select(ProjectAddon).where(ProjectAddon.name == name)
        ).first()

    @staticmethod
    def get_all(session: Session) -> Sequence[ProjectAddon]:
        return session.exec(select(ProjectAddon)).all()


class ProjectCRUD:
    @staticmethod
    def create(
        session: Session,
        programming_language_id: int,
        description: Optional[str] = None,
        project_tech_id: Optional[int] = None,
        project_addon_id: Optional[int] = None,
    ) -> Project:
        project = Project(
            description=description,
            programming_language_id=programming_language_id,
            project_tech_id=cast(int, project_tech_id),
            project_addon_id=cast(int, project_addon_id),
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project

    @staticmethod
    def get(session: Session, project_id: int) -> Optional[Project]:
        return session.get(Project, project_id)

    @staticmethod
    def get_all(session: Session) -> Sequence[Project]:
        return session.exec(select(Project)).all()


class ProjectExtraCRUD:
    @staticmethod
    def create(
        session: Session,
        projects_id: int,
        project_programming_language_id: int,
        project_tech_id: Optional[int] = None,
        project_addon_id: Optional[int] = None,
    ) -> ProjectExtra:
        extra = ProjectExtra(
            projects_id=projects_id,
            project_programming_language_id=project_programming_language_id,
            project_tech_id=cast(int, project_tech_id),
            project_addon_id=cast(int, project_addon_id),
        )
        session.add(extra)
        session.commit()
        session.refresh(extra)
        return extra

    @staticmethod
    def get(session: Session, extra_id: int) -> Optional[ProjectExtra]:
        return session.get(ProjectExtra, extra_id)

    @staticmethod
    def get_by_project(session: Session, project_id: int) -> Sequence[ProjectExtra]:
        return session.exec(
            select(ProjectExtra).where(ProjectExtra.projects_id == project_id)
        ).all()

    @staticmethod
    def get_all(session: Session) -> Sequence[ProjectExtra]:
        return session.exec(select(ProjectExtra)).all()


def seed_from_yaml(session: Session, yaml_path: str) -> dict[str, list[str]]:
    with open(yaml_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    inserted: dict[str, list[str]] = {
        "programming_languages": [],
        "techs": [],
        "addons": [],
    }

    for name in data.get("programming_languages", []):
        if name is None:
            continue
        name = str(name).strip()
        if not ProgrammingLanguageCRUD.get_by_name(session, name):
            ProgrammingLanguageCRUD.create(session, name)
            inserted["programming_languages"].append(name)

    for name in data.get("techs", []):
        if name is None:
            continue
        name = str(name).strip()
        if not TechCRUD.get_by_name(session, name):
            TechCRUD.create(session, name)
            inserted["techs"].append(name)

    for name in data.get("addons", []):
        if name is None:
            continue
        name = str(name).strip()
        if not AddonCRUD.get_by_name(session, name):
            AddonCRUD.create(session, name)
            inserted["addons"].append(name)

    return inserted
