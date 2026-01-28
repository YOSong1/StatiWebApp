from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile

from webapp.api.schemas import ApiResponse
from webapp.services.data_service import dataframe_preview, load_dataframe_from_upload


router = APIRouter()


def _store(request):
    return request.app.state.project_store


@router.post("/projects/{project_id}/data/upload", response_model=ApiResponse)
async def upload_data(project_id: str, request: Request, file: UploadFile = File(...)):
    project = _store(request).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")

    content = await file.read()
    try:
        df = load_dataframe_from_upload(file.filename or "upload.csv", content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    project.update_data(df, description=file.filename or "업로드 데이터")
    return ApiResponse(ok=True, data={"rows": int(df.shape[0]), "cols": int(df.shape[1]), "columns": [str(c) for c in df.columns.tolist()]})


@router.get("/projects/{project_id}/data/summary", response_model=ApiResponse)
def data_summary(project_id: str, request: Request):
    project = _store(request).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    df = project.dataframe
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="데이터가 없습니다")

    summary = {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "columns": [str(c) for c in df.columns.tolist()],
        "dtypes": {str(k): str(v) for k, v in df.dtypes.to_dict().items()},
        "missing_total": int(df.isnull().sum().sum()),
    }
    return ApiResponse(ok=True, data=summary)


@router.get("/projects/{project_id}/data/preview", response_model=ApiResponse)
def data_preview(project_id: str, request: Request, rows: int = Query(default=20, ge=1, le=200)):
    project = _store(request).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    df = project.dataframe
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="데이터가 없습니다")

    cols, data = dataframe_preview(df, rows=rows)
    return ApiResponse(ok=True, data={"columns": cols, "rows": data})
