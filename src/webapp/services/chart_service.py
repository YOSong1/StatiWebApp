from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from controllers.chart_controller import ChartController
from webapp.serialization import fig_to_base64_png


class ChartError(RuntimeError):
    def __init__(self, title: str, message: str):
        super().__init__(f"{title}: {message}")
        self.title = title
        self.message = message


class ChartService:
    def create_chart_base64(
        self,
        chart_type: str,
        df: pd.DataFrame,
        x_var: str | None = None,
        y_var: str | None = None,
        group_var: str | None = None,
        options: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if chart_type in {"주효과도", "상호작용도"}:
            # ChartController는 범주형(object/category) 요인을 요구한다.
            # DOE 데이터가 -1/1, 0/1 같은 숫자형으로 들어오는 경우가 많아,
            # 웹 어댑터에서만 임시로 범주형으로 변환해 호환성을 높인다.
            # (프로젝트의 원본 데이터프레임은 변경하지 않음)
            df = df.copy()
            for col in [x_var, group_var]:
                if col and col in df.columns:
                    df[col] = df[col].astype(str).astype("category")

        controller = ChartController()
        holder: Dict[str, Any] = {}

        def on_error(title: str, message: str):
            holder["error"] = (title, message)

        controller.error_occurred.connect(on_error)
        chart_info = controller.create_chart(
            chart_type=chart_type,
            dataframe=df,
            x_var=x_var,
            y_var=y_var,
            group_var=group_var,
            options=options,
        )

        if "error" in holder:
            title, message = holder["error"]
            raise ChartError(title, message)
        if chart_info is None:
            raise ChartError("차트 오류", "차트 생성에 실패했습니다.")

        fig = chart_info.get("figure")
        if fig is None:
            raise ChartError("차트 오류", "Figure가 생성되지 않았습니다.")

        image_base64 = fig_to_base64_png(fig)
        try:
            import matplotlib.pyplot as plt

            plt.close(fig)
        except Exception:
            pass

        chart_info = {k: v for k, v in chart_info.items() if k != "figure"}
        chart_info["image_base64_png"] = image_base64
        return chart_info
