from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from webapp.api.schemas import ApiResponse
from webapp.serialization import to_jsonable


router = APIRouter(prefix="/recommendations")


def _store(request: Request):
    return request.app.state.project_store


def _is_numeric_dtype(dtype: Any) -> bool:
    try:
        return pd.api.types.is_numeric_dtype(dtype)
    except Exception:
        return False


def _is_categorical_dtype(dtype: Any) -> bool:
    try:
        return pd.api.types.is_object_dtype(dtype) or pd.api.types.is_categorical_dtype(dtype) or pd.api.types.is_bool_dtype(dtype)
    except Exception:
        return False


def _unique_count(series: pd.Series) -> int:
    try:
        return int(series.dropna().nunique())
    except Exception:
        return 0


def _guess_factor_candidates(df: pd.DataFrame) -> List[str]:
    cols: List[str] = []
    for c in df.columns:
        s = df[c]
        dt = df.dtypes.get(c)
        uniq = _unique_count(s)
        if uniq <= 1:
            continue

        # 범주형은 우선적으로 factor 후보
        if _is_categorical_dtype(dt):
            cols.append(str(c))
            continue

        # 숫자형인데 고유값이 적으면(수준 설계) factor 후보로 간주
        if _is_numeric_dtype(dt) and uniq <= 12:
            cols.append(str(c))
            continue

    return cols


def _guess_response_candidates(df: pd.DataFrame) -> List[str]:
    # 반응값은 보통 숫자형 연속값(고유값이 어느 정도 많음)
    candidates: List[str] = []
    for c in df.columns:
        dt = df.dtypes.get(c)
        if not _is_numeric_dtype(dt):
            continue
        uniq = _unique_count(df[c])
        if uniq <= 1:
            continue
        candidates.append(str(c))

    # “연속”에 가까운 것을 앞으로 오도록 정렬(고유값 많은 순)
    candidates.sort(key=lambda col: _unique_count(df[col]), reverse=True)
    return candidates


def _guess_continuous_numeric_predictors(df: pd.DataFrame) -> List[str]:
    cols: List[str] = []
    for c in df.columns:
        dt = df.dtypes.get(c)
        if not _is_numeric_dtype(dt):
            continue
        uniq = _unique_count(df[c])
        # RSM/회귀에 적합: 수준이 충분히 많은 숫자형
        if uniq >= 4:
            cols.append(str(c))
    cols.sort(key=lambda col: _unique_count(df[col]), reverse=True)
    return cols


def recommend_for_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    numeric_cols = [str(c) for c in df.select_dtypes(include="number").columns.tolist()]
    categorical_cols = [str(c) for c in df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()]

    factor_candidates = _guess_factor_candidates(df)
    response_candidates = _guess_response_candidates(df)
    continuous_numeric = _guess_continuous_numeric_predictors(df)

    factor_set = set(factor_candidates)
    response_set = set(response_candidates)

    # 컬럼별 프로파일(추천 근거)
    column_profile: List[Dict[str, Any]] = []

    def _preview_levels(series: pd.Series, max_levels: int = 10) -> Optional[List[str]]:
        try:
            uniq = series.dropna().unique().tolist()
            if len(uniq) == 0:
                return None
            if len(uniq) > max_levels:
                return None
            return [str(x) for x in uniq]
        except Exception:
            return None

    for c in df.columns:
        name = str(c)
        s = df[c]
        dt = df.dtypes.get(c)
        uniq = _unique_count(s)
        missing = int(s.isna().sum()) if hasattr(s, "isna") else 0
        is_numeric = _is_numeric_dtype(dt)
        is_categorical = _is_categorical_dtype(dt)
        levels_preview = _preview_levels(s) if (is_categorical or uniq <= 12) else None

        column_profile.append(
            {
                "name": name,
                "dtype": str(dt),
                "unique_non_null": int(uniq),
                "missing": int(missing),
                "is_numeric": bool(is_numeric),
                "is_categorical": bool(is_categorical),
                "is_factor_candidate": name in factor_set,
                "is_response_candidate": name in response_set,
                "levels_preview": levels_preview,
            }
        )

    # 기본 선택(프론트에서 select 기본값으로 활용)
    default_response = response_candidates[0] if response_candidates else (numeric_cols[0] if numeric_cols else (str(df.columns[-1]) if len(df.columns) else None))
    default_factors = [c for c in factor_candidates if c != default_response][:3]

    recommended: List[Dict[str, Any]] = []

    if len(numeric_cols) >= 2:
        recommended.append(
            {
                "id": "correlation",
                "label": "상관분석 + 상관행렬",
                "reason": "숫자형 변수가 2개 이상이라 상관관계를 볼 수 있습니다.",
                "action": "correlation",
            }
        )

    if default_response and len(continuous_numeric) >= 2:
        # 회귀 후보: response 제외한 수치형 predictor가 최소 1개 이상
        predictors = [c for c in continuous_numeric if c != default_response]
        if len(predictors) >= 1:
            recommended.append(
                {
                    "id": "regression",
                    "label": "회귀분석",
                    "reason": "연속형 숫자 변수가 충분해 회귀를 실행할 수 있습니다.",
                    "action": "regression",
                }
            )

    if default_response and len(factor_candidates) >= 1:
        recommended.append(
            {
                "id": "main_effects_plot",
                "label": "주효과도",
                "reason": "요인 후보가 있어 주효과도를 그릴 수 있습니다.",
                "action": "chart_main_effects",
                "suggested": {"response": default_response, "factors": default_factors},
            }
        )

    if default_response and len(factor_candidates) >= 2:
        recommended.append(
            {
                "id": "interaction_plot",
                "label": "상호작용도",
                "reason": "요인 후보가 2개 이상이라 상호작용도를 그릴 수 있습니다.",
                "action": "chart_interaction",
                "suggested": {"response": default_response, "factors": default_factors},
            }
        )

    if default_response and len(factor_candidates) >= 1:
        recommended.append(
            {
                "id": "doe_anova_workflow",
                "label": "DOE ANOVA + 주효과/상호작용도",
                "reason": "요인/반응 컬럼이 있어 DOE ANOVA 흐름을 실행할 수 있습니다.",
                "action": "doe_workflow",
                "suggested": {"response": default_response, "factors": default_factors},
            }
        )

    if default_response and len(continuous_numeric) >= 3:
        # RSM은 최소 2개 요인이 필요(여기선 response 포함 가능성 있으므로 제외 후 체크)
        predictors = [c for c in continuous_numeric if c != default_response]
        if len(predictors) >= 2:
            suggested_factors = predictors[:2]
            recommended.append(
                {
                    "id": "rsm_quadratic",
                    "label": "RSM(2차 모델)",
                    "reason": "연속형 요인이 2개 이상이라 2차 반응표면 모델을 시도할 수 있습니다.",
                    "action": "rsm",
                    "suggested": {"response": default_response, "factors": suggested_factors},
                }
            )

    return {
        "columns": [str(c) for c in df.columns.tolist()],
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "factor_candidates": factor_candidates,
        "response_candidates": response_candidates,
        "column_profile": column_profile,
        "default": {"response": default_response, "factors": default_factors},
        "recommended": recommended,
    }


@router.get("/projects/{project_id}", response_model=ApiResponse)
def recommendations(project_id: str, request: Request):
    project = _store(request).get(project_id)
    if not project or project.dataframe is None or project.dataframe.empty:
        raise HTTPException(status_code=400, detail="데이터가 없습니다")
    payload = recommend_for_dataframe(project.dataframe)
    return ApiResponse(ok=True, data=to_jsonable(payload))
