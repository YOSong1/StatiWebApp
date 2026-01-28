from __future__ import annotations

from fastapi import APIRouter, HTTPException

from webapp.api.schemas import (
    ApiResponse,
    DesignBBRequest,
    DesignCCDRequest,
    DesignFractionalFactorialRequest,
    DesignFullFactorialRequest,
    DesignOrthogonalArrayRequest,
    DesignPBRequest,
)
from webapp.serialization import to_jsonable
from webapp.services.design_service import DesignService


router = APIRouter(prefix="/design")


@router.post("/full_factorial", response_model=ApiResponse)
def full_factorial(req: DesignFullFactorialRequest):
    svc = DesignService()
    try:
        df = svc.full_factorial(req.levels)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(ok=True, data=to_jsonable(df))


@router.post("/fractional_factorial", response_model=ApiResponse)
def fractional_factorial(req: DesignFractionalFactorialRequest):
    svc = DesignService()
    try:
        df = svc.fractional_factorial(req.design_str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(ok=True, data=to_jsonable(df))


@router.post("/plackett_burman", response_model=ApiResponse)
def plackett_burman(req: DesignPBRequest):
    svc = DesignService()
    try:
        df = svc.plackett_burman(req.factors)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(ok=True, data=to_jsonable(df))


@router.post("/box_behnken", response_model=ApiResponse)
def box_behnken(req: DesignBBRequest):
    svc = DesignService()
    try:
        df = svc.box_behnken(req.factors, center=req.center)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(ok=True, data=to_jsonable(df))


@router.post("/ccd", response_model=ApiResponse)
def ccd(req: DesignCCDRequest):
    svc = DesignService()
    center = (int(req.center[0]), int(req.center[1])) if len(req.center) == 2 else (4, 4)
    try:
        df = svc.ccd(req.factors, center=center, alpha=req.alpha)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(ok=True, data=to_jsonable(df))


@router.post("/orthogonal_array", response_model=ApiResponse)
def orthogonal_array(req: DesignOrthogonalArrayRequest):
    svc = DesignService()
    try:
        df = svc.orthogonal_array(req.factors, design=req.design)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(ok=True, data=to_jsonable(df))
