from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from webapp.api.schemas import ApiResponse, DoeAnovaRequest, MainEffectsAnovaRequest, RsmQuadraticRequest
from webapp.serialization import to_jsonable
from webapp.services.analysis_runner import AnalysisError, AnalysisRunner


router = APIRouter(prefix="/analysis")


def _store(request):
    return request.app.state.project_store


def _get_df(project_id: str, request):
    project = _store(request).get(project_id)
    if not project or project.dataframe is None or project.dataframe.empty:
        raise HTTPException(status_code=400, detail="데이터가 없습니다")
    return project, project.dataframe


@router.post("/projects/{project_id}/basic_statistics", response_model=ApiResponse)
def basic_statistics(project_id: str, request: Request):
    project, df = _get_df(project_id, request)
    try:
        res = AnalysisRunner().basic_statistics(df)
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail={"title": e.title, "message": e.message})
    project.add_analysis(res)
    return ApiResponse(ok=True, data=to_jsonable(res))


@router.post("/projects/{project_id}/correlation", response_model=ApiResponse)
def correlation(project_id: str, request: Request):
    project, df = _get_df(project_id, request)
    try:
        res = AnalysisRunner().correlation(df)
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail={"title": e.title, "message": e.message})
    project.add_analysis(res)
    return ApiResponse(ok=True, data=to_jsonable(res))


@router.post("/projects/{project_id}/anova", response_model=ApiResponse)
def anova(project_id: str, request: Request):
    project, df = _get_df(project_id, request)
    try:
        res = AnalysisRunner().anova(df)
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail={"title": e.title, "message": e.message})
    project.add_analysis(res)
    return ApiResponse(ok=True, data=to_jsonable(res))


@router.post("/projects/{project_id}/regression", response_model=ApiResponse)
def regression(project_id: str, request: Request):
    project, df = _get_df(project_id, request)
    try:
        res = AnalysisRunner().regression(df)
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail={"title": e.title, "message": e.message})
    project.add_analysis(res)
    return ApiResponse(ok=True, data=to_jsonable(res))


@router.post("/projects/{project_id}/doe_anova", response_model=ApiResponse)
def doe_anova(project_id: str, request: Request, body: DoeAnovaRequest):
    project, df = _get_df(project_id, request)
    try:
        res = AnalysisRunner().doe_anova(df, response=body.response, factors=body.factors)
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail={"title": e.title, "message": e.message})
    project.add_analysis(res)
    return ApiResponse(ok=True, data=to_jsonable(res))


@router.post("/projects/{project_id}/main_effects_anova", response_model=ApiResponse)
def main_effects_anova(project_id: str, request: Request, body: MainEffectsAnovaRequest):
    project, df = _get_df(project_id, request)
    try:
        res = AnalysisRunner().main_effects_anova(
            df,
            response=body.response,
            factors=body.factors,
            analysis_type=body.analysis_type,
        )
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail={"title": e.title, "message": e.message})
    project.add_analysis(res)
    return ApiResponse(ok=True, data=to_jsonable(res))


@router.post("/projects/{project_id}/rsm_quadratic", response_model=ApiResponse)
def rsm_quadratic(project_id: str, request: Request, body: RsmQuadraticRequest):
    project, df = _get_df(project_id, request)
    try:
        res = AnalysisRunner().rsm_quadratic(
            df,
            response=body.response,
            factors=body.factors,
            analysis_type=body.analysis_type,
        )
    except AnalysisError as e:
        raise HTTPException(status_code=400, detail={"title": e.title, "message": e.message})
    project.add_analysis(res)
    return ApiResponse(ok=True, data=to_jsonable(res))


@router.get("/projects/{project_id}/history", response_model=ApiResponse)
def analysis_history(project_id: str, request: Request):
    project = _store(request).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
    return ApiResponse(ok=True, data=to_jsonable(project.analysis_history))
