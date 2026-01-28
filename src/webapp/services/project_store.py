from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Dict, Optional
from uuid import uuid4

from models.project import Project


@dataclass
class StoredProject:
    project: Project


class ProjectStore:
    """웹 세션/사용자 단위 프로젝트 저장소.

    현재는 메모리 기반(프로세스 내)으로 제공한다.
    배포 환경에서는 Redis/DB로 교체 가능한 형태로 인터페이스를 유지한다.
    """

    def __init__(self):
        self._lock = RLock()
        self._projects: Dict[str, StoredProject] = {}

    def create(self, name: str | None = None) -> str:
        with self._lock:
            project_id = str(uuid4())
            p = Project()
            if name:
                p.name = name
            self._projects[project_id] = StoredProject(project=p)
            return project_id

    def get(self, project_id: str) -> Optional[Project]:
        with self._lock:
            item = self._projects.get(project_id)
            return item.project if item else None

    def set(self, project_id: str, project: Project) -> None:
        with self._lock:
            self._projects[project_id] = StoredProject(project=project)

    def delete(self, project_id: str) -> bool:
        with self._lock:
            return self._projects.pop(project_id, None) is not None

    def list_ids(self) -> list[str]:
        with self._lock:
            return list(self._projects.keys())
