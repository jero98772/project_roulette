import asyncio
import json
import os
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import jpype

from core.ensemble_project.api.ensemble_project_models import ProjectSelection
from core.settings.default import AppSettings


@dataclass
class ClojureSettings:
    CLOJURE_PROJECT_ROOT: str = os.environ.get(
        "CLOJURE_PROJECT_ROOT",
        str(Path(__file__).resolve().parents[2]),
    )
    ENSEMBLE_AI_GATEWAY_NS: str = os.environ.get(
        "CLOJURE_ENSEMBLE_AI_GATEWAY_NS",
        "core.ensemble-project.ensemble-project-ai-gatway-service",
    )
    OLLAMA_HOST: str = os.environ.get("OLLAMA_HOST", AppSettings().OLLAMA_HOST)
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", AppSettings().OLLAMA_MODEL)


class ClojureBridge:
    _instance: Optional["ClojureBridge"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, settings: Optional[ClojureSettings] = None):
        if self._initialized:
            return
        self.settings = settings or ClojureSettings()
        self._start_jvm()
        self._require_namespace()
        self._initialized = True

    def _build_classpath(self) -> str:
        result = subprocess.run(
            ["clojure", "-Spath"],
            capture_output=True,
            text=True,
            check=True,
            cwd=self.settings.CLOJURE_PROJECT_ROOT,
        )
        return result.stdout.strip()

    def _start_jvm(self) -> None:
        if jpype.isJVMStarted():
            return
        classpath = self._build_classpath()
        jpype.startJVM(classpath=[classpath])

    def _require_namespace(self) -> None:
        clojure = jpype.JClass("clojure.java.api.Clojure")
        require_fn = clojure.var("clojure.core", "require")
        require_fn.invoke(clojure.read(self.settings.ENSEMBLE_AI_GATEWAY_NS))

        ns = self.settings.ENSEMBLE_AI_GATEWAY_NS
        self._choose_valid_project = clojure.var(ns, "choose-valid-project")
        self._generate_description = clojure.var(ns, "generate-description")

    def choose_valid_project(self, projects: list) -> dict:
        projects_json = json.dumps(projects)
        result = self._choose_valid_project.invoke(
            self.settings.OLLAMA_HOST,
            self.settings.OLLAMA_MODEL,
            projects_json,
        )
        if result is None:
            raise ValueError(
                "Clojure selector did not return a structured selection result"
            )
        return json.loads(str(result))

    def generate_description(self, project: dict) -> str:
        project_json = json.dumps(project)
        result = self._generate_description.invoke(
            self.settings.OLLAMA_HOST,
            self.settings.OLLAMA_MODEL,
            project_json,
        )
        return str(result).strip() if result is not None else ""


class ClojureProjectGeneratorAIGateway:
    def __init__(self, settings: Optional[ClojureSettings] = None):
        self._bridge = ClojureBridge(settings)

    async def choose_valid_project(self, projects: list[dict]) -> ProjectSelection:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None, self._bridge.choose_valid_project, projects
        )
        return ProjectSelection(**raw)

    async def generate_description(self, project: dict) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._bridge.generate_description, project
        )
