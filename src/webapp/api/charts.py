from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from webapp.api.schemas import ApiResponse, CreateChartRequest
from webapp.serialization import to_jsonable
from webapp.services.chart_service import ChartError, ChartService


router = APIRouter(prefix="/charts")


def _store(request):
    return request.app.state.project_store


@router.post("/projects/{project_id}", response_model=ApiResponse)
def create_chart(project_id: str, request: Request, body: CreateChartRequest):
    project = _store(request).get(project_id)
    if not project or project.dataframe is None or project.dataframe.empty:
        raise HTTPException(status_code=400, detail="데이터가 없습니다")
    try:
        chart_info = ChartService().create_chart_base64(
            chart_type=body.chart_type,
            df=project.dataframe,
            x_var=body.x_var,
            y_var=body.y_var,
            group_var=body.group_var,
            options=body.options,
        )
    except ChartError as e:
        raise HTTPException(status_code=400, detail={"title": e.title, "message": e.message})
    project.add_chart(chart_info)
    return ApiResponse(ok=True, data=to_jsonable(chart_info))


@router.get("/projects/{project_id}/history", response_model=ApiResponse)
def chart_history(project_id: str, request: Request):
    project = _store(request).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return ApiResponse(ok=True, data=to_jsonable(project.chart_history))
