from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    ok: bool = True
    data: Any = None
    error: Optional[Dict[str, Any]] = None


class CreateProjectRequest(BaseModel):
    name: Optional[str] = Field(default=None, description="프로젝트 이름")


class DesignFullFactorialRequest(BaseModel):
    levels: List[int]


class DesignFractionalFactorialRequest(BaseModel):
    design_str: str


class DesignPBRequest(BaseModel):
    factors: int


class DesignBBRequest(BaseModel):
    factors: int
    center: int = 1


class DesignCCDRequest(BaseModel):
    factors: int
    center: List[int] = Field(default_factory=lambda: [4, 4], description="[center1, center2]")
    alpha: str = "orthogonal"


class DesignOrthogonalArrayRequest(BaseModel):
    factors: int
    design: str = "L8"


class DoeAnovaRequest(BaseModel):
    response: str
    factors: List[str]


class MainEffectsAnovaRequest(BaseModel):
    response: str
    factors: List[str]
    analysis_type: str = "부분요인 ANOVA"


class RsmQuadraticRequest(BaseModel):
    response: str
    factors: List[str]
    analysis_type: str = "RSM"


class CreateChartRequest(BaseModel):
    chart_type: str
    x_var: Optional[str] = None
    y_var: Optional[str] = None
    group_var: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
