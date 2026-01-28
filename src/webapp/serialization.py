from __future__ import annotations

import base64
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def to_jsonable(value: Any) -> Any:
    """임의의 파이썬/넘파이/판다스 객체를 JSON 직렬화 가능한 형태로 변환한다."""
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, (np.integer, np.floating, np.bool_)):
        return value.item()

    if isinstance(value, np.ndarray):
        return value.tolist()

    if isinstance(value, pd.DataFrame):
        return {
            "__type__": "DataFrame",
            "columns": [str(c) for c in value.columns.tolist()],
            "index": [str(i) for i in value.index.tolist()],
            "data": value.where(pd.notnull(value), None).to_dict(orient="records"),
        }

    if isinstance(value, pd.Series):
        return {
            "__type__": "Series",
            "name": str(value.name) if value.name is not None else None,
            "index": [str(i) for i in value.index.tolist()],
            "data": value.where(pd.notnull(value), None).to_dict(),
        }

    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]

    return str(value)


def fig_to_base64_png(fig) -> str:
    """matplotlib Figure를 base64(PNG)로 변환."""
    import io

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
