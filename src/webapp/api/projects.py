from __future__ import annotations

import json

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from models.project import Project
from webapp.api.schemas import ApiResponse, CreateProjectRequest
from webapp.serialization import to_jsonable


router = APIRouter()


def _store(request):
    return request.app.state.project_store


@router.get("/health", response_model=ApiResponse)
def health():
    return ApiResponse(ok=True, data={"status": "ok"})


@router.post("/projects", response_model=ApiResponse)
def create_project(req: CreateProjectRequest, request: Request):
    project_id = _store(request).create(name=req.name)
    project = _store(request).get(project_id)
    return ApiResponse(ok=True, data={"project_id": project_id, "project": to_jsonable(project.to_dict())})


@router.get("/projects", response_model=ApiResponse)
def list_projects(request: Request):
    ids = _store(request).list_ids()
    data = []
    for pid in ids:
        p = _store(request).get(pid)
        if p:
            data.append({"project_id": pid, "name": p.name})
    return ApiResponse(ok=True, data=data)


@router.get("/projects/{project_id}", response_model=ApiResponse)
def get_project(project_id: str, request: Request):
    project = _store(request).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return ApiResponse(ok=True, data={"project_id": project_id, "project": to_jsonable(project.to_dict())})


@router.delete("/projects/{project_id}", response_model=ApiResponse)
def delete_project(project_id: str, request: Request):
    ok = _store(request).delete(project_id)
    return ApiResponse(ok=True, data={"deleted": ok})


@router.post("/projects/import", response_model=ApiResponse)
async def import_project(request: Request, file: UploadFile = File(...)):
    raw = await file.read()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        payload = json.loads(raw.decode("cp949"))

    project = Project.from_dict(payload)
    project_id = _store(request).create(name=project.name)
    _store(request).set(project_id, project)
    return ApiResponse(ok=True, data={"project_id": project_id, "project": to_jsonable(project.to_dict())})


@router.get("/projects/{project_id}/export", response_model=ApiResponse)
def export_project(project_id: str, request: Request):
    project = _store(request).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return ApiResponse(
        ok=True,
        data={
            "filename": f"{project.name}.doeproj",
            "content": json.dumps(to_jsonable(project.to_dict()), ensure_ascii=False, indent=2),
        },
    )
