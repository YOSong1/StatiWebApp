from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple

import pandas as pd

from utils.data_utils import try_read_csv_with_encodings


def load_dataframe_from_upload(filename: str, content: bytes) -> pd.DataFrame:
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        bio = io.BytesIO(content)
        try:
            return pd.read_csv(bio, encoding="utf-8")
        except UnicodeDecodeError:
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".csv", delete=True) as tmp:
                tmp.write(content)
                tmp.flush()
                return try_read_csv_with_encodings(tmp.name)

    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(io.BytesIO(content))

    raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")


def dataframe_preview(df: pd.DataFrame, rows: int = 20) -> Tuple[list[str], list[list[object]]]:
    head = df.head(rows)
    cols = [str(c) for c in head.columns.tolist()]
    data = head.where(pd.notnull(head), None).values.tolist()
    return cols, data
