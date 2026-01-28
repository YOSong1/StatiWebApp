from __future__ import annotations

from typing import Any, Callable, Dict

import pandas as pd

from controllers.analysis_controller import AnalysisController


class AnalysisError(RuntimeError):
    def __init__(self, title: str, message: str):
        super().__init__(f"{title}: {message}")
        self.title = title
        self.message = message


def _run_with_signals(invoker: Callable[[AnalysisController], None]) -> Dict[str, Any]:
    controller = AnalysisController()
    holder: Dict[str, Any] = {}

    def on_completed(name: str, result: dict):
        holder["name"] = name
        holder["result"] = result

    def on_error(title: str, message: str):
        holder["error"] = (title, message)

    controller.analysis_completed.connect(on_completed)
    controller.error_occurred.connect(on_error)

    invoker(controller)

    if "error" in holder:
        title, message = holder["error"]
        raise AnalysisError(title, message)
    if "result" not in holder:
        raise AnalysisError("분석 오류", "분석 결과가 생성되지 않았습니다.")
    return holder["result"]


class AnalysisRunner:
    """Qt 의존 컨트롤러를 웹에서 안전하게 실행하기 위한 래퍼."""

    def basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        return _run_with_signals(lambda c: c.run_basic_statistics(df))

    def correlation(self, df: pd.DataFrame) -> Dict[str, Any]:
        return _run_with_signals(lambda c: c.run_correlation_analysis(df))

    def anova(self, df: pd.DataFrame) -> Dict[str, Any]:
        return _run_with_signals(lambda c: c.run_anova(df))

    def regression(self, df: pd.DataFrame) -> Dict[str, Any]:
        return _run_with_signals(lambda c: c.run_regression(df))

    def doe_anova(self, df: pd.DataFrame, response: str, factors: list[str]) -> Dict[str, Any]:
        return _run_with_signals(lambda c: c.run_doe_anova(df, response=response, factors=factors))

    def main_effects_anova(self, df: pd.DataFrame, response: str, factors: list[str], analysis_type: str) -> Dict[str, Any]:
        return _run_with_signals(lambda c: c.run_main_effects_anova(df, response=response, factors=factors, analysis_type=analysis_type))

    def rsm_quadratic(self, df: pd.DataFrame, response: str, factors: list[str], analysis_type: str = "RSM") -> Dict[str, Any]:
        return _run_with_signals(lambda c: c.run_rsm_quadratic(df, response=response, factors=factors, analysis_type=analysis_type))
