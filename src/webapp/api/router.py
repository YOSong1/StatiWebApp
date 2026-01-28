from __future__ import annotations

from fastapi import APIRouter

from webapp.api import analysis, charts, data, design, projects, recommendations


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(data.router, tags=["data"])
api_router.include_router(design.router, tags=["design"])
api_router.include_router(analysis.router, tags=["analysis"])
api_router.include_router(charts.router, tags=["charts"])
api_router.include_router(recommendations.router, tags=["recommendations"])
