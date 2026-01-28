import numpy as np
import pandas as pd
from datetime import datetime
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QMessageBox
import statsmodels.api as sm
import statsmodels.formula.api as smf


class AnalysisController(QObject):
    """
    기본 통계/상관/ANOVA/회귀 분석을 수행하는 컨트롤러.
    DOE 분석 확장을 위한 뼈대 역할을 한다.
    """

    analysis_completed = Signal(str, dict)  # 분석 이름, 결과 dict
    status_updated = Signal(str)
    error_occurred = Signal(str, str)  # 제목, 메시지

    def __init__(self, parent=None):
        super().__init__(parent)

    # 기초 통계 ------------------------------------------------------------
    @Slot(pd.DataFrame)
    def run_basic_statistics(self, dataframe: pd.DataFrame):
        if not self._validate_data(dataframe):
            return
        try:
            self.status_updated.emit("기초 통계량을 계산하는 중입니다...")
            numeric_data = dataframe.select_dtypes(include=[np.number])
            if numeric_data.empty:
                self.error_occurred.emit("분석 오류", "숫자형 데이터가 없습니다.")
                return

            stats_result = {
                "type": "기초 통계",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "완료",
                "description": f"{len(numeric_data.columns)}개 변수의 기초 통계량",
                "results": {
                    "summary": numeric_data.describe(),
                    "missing_values": numeric_data.isnull().sum(),
                    "data_types": numeric_data.dtypes,
                    "variable_count": len(numeric_data.columns),
                    "observation_count": len(numeric_data),
                },
            }

            self.analysis_completed.emit("기초 통계", stats_result)
            self.status_updated.emit("기초 통계 분석이 완료되었습니다.")
        except Exception as exc:  # pragma: no cover - 런타임 예외 보호
            self.error_occurred.emit("기초 통계 분석 실패", f"분석 중 오류가 발생했습니다:\n{exc}")

    # 상관 분석 ------------------------------------------------------------
    @Slot(pd.DataFrame)
    def run_correlation_analysis(self, dataframe: pd.DataFrame):
        if not self._validate_data(dataframe):
            return
        try:
            self.status_updated.emit("상관분석을 수행하는 중입니다...")
            numeric_data = dataframe.select_dtypes(include=[np.number])
            if len(numeric_data.columns) < 2:
                self.error_occurred.emit("분석 오류", "상관분석에는 최소 2개의 숫자형 변수가 필요합니다.")
                return

            corr_matrix = numeric_data.corr()
            strong = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:
                        strong.append(
                            {
                                "var1": corr_matrix.columns[i],
                                "var2": corr_matrix.columns[j],
                                "correlation": corr_value,
                                "strength": self._get_correlation_strength(abs(corr_value)),
                            }
                        )

            result = {
                "type": "상관분석",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "완료",
                "description": f"{len(numeric_data.columns)}개 변수 간 상관관계 분석",
                "results": {
                    "correlation_matrix": corr_matrix,
                    "strong_correlations": strong,
                    "variable_count": len(numeric_data.columns),
                    "total_pairs": len(corr_matrix.columns) * (len(corr_matrix.columns) - 1) // 2,
                },
            }

            self.analysis_completed.emit("상관분석", result)
            self.status_updated.emit("상관분석이 완료되었습니다.")
        except Exception as exc:  # pragma: no cover
            self.error_occurred.emit("상관분석 실패", f"분석 중 오류가 발생했습니다:\n{exc}")

    # DOE ANOVA -----------------------------------------------------------
    @Slot(pd.DataFrame)
    def run_doe_anova(self, dataframe: pd.DataFrame, response: str, factors: list):
        """DOE용 ANOVA: 주효과 + 2요인 교호효과 포함"""
        if dataframe is None or dataframe.empty:
            self.error_occurred.emit("분석 오류", "분석할 데이터가 없습니다.")
            return
        if response not in dataframe.columns or any(f not in dataframe.columns for f in factors):
            self.error_occurred.emit("분석 오류", "요인/반응 열을 찾을 수 없습니다.")
            return
        try:
            df = dataframe.copy()
            df[response] = pd.to_numeric(df[response], errors="coerce")
            df = df.dropna(subset=[response] + factors)
            if len(df) < len(factors) + 1:
                self.error_occurred.emit("분석 오류", "표본 수가 부족합니다.")
                return

            main_terms = " + ".join([f"C({f})" for f in factors])
            inter_terms = " + ".join([f"C({f1}):C({f2})" for i, f1 in enumerate(factors) for f2 in factors[i + 1 :]])
            formula = f"{response} ~ {main_terms}"
            if inter_terms:
                formula += " + " + inter_terms
            main_only_formula = f"{response} ~ {main_terms}"

            def fit_and_anova(frm):
                model_local = smf.ols(formula=frm, data=df).fit()
                if model_local.df_resid <= 0:
                    raise ValueError("잔차 자유도가 0입니다.")
                anova_local = sm.stats.anova_lm(model_local, typ=2)
                return model_local, anova_local

            # 단계적 단순화: (1) 주효과+교호 -> (2) 주효과 -> (3) 단일 요인
            tried = []
            success = False
            fallback_reason = ""
            chosen_formula = None
            model = None
            anova_table = None

            formulas = [
                ("main+interaction", formula),
                ("main_only", main_only_formula),
            ]
            # 단일 요인 후보
            for f in factors:
                formulas.append((f"single_factor:{f}", f"{response} ~ C({f})"))

            for name, frm in formulas:
                tried.append(name)
                try:
                    model_tmp, anova_tmp = fit_and_anova(frm)
                    model, anova_table = model_tmp, anova_tmp
                    chosen_formula = frm
                    success = True
                    fallback_reason = "" if name == "main+interaction" else name
                    break
                except Exception:
                    continue

            if not success:
                self.error_occurred.emit(
                    "분석 오류",
                    "잔차 자유도가 0이거나 데이터가 부족합니다.\n"
                    "요인 수준을 줄이거나(카테고리 합치기), 관측을 더 추가한 뒤 다시 시도하세요."
                )
                return

            result = {
                "type": "DOE ANOVA",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "완료",
                "description": f"DOE ANOVA: response={response}, factors={', '.join(factors)}",
                "results": {
                    "formula": chosen_formula,
                    "fallback": fallback_reason,
                    "anova": anova_table,
                    "factors": factors,
                    "response": response,
                    "coefficients": model.params,
                    "r_squared": model.rsquared,
                    "adj_r_squared": model.rsquared_adj,
                    "n_obs": int(model.nobs),
                    "residuals": model.resid.tolist(),
                    "fitted": model.fittedvalues.tolist(),
                },
            }
            self.analysis_completed.emit("DOE ANOVA", result)
            self.status_updated.emit("DOE ANOVA가 완료되었습니다.")
        except Exception as exc:
            self.error_occurred.emit("DOE ANOVA 실패", f"분석 중 오류가 발생했습니다:\n{exc}")

    # 부분요인/직교/Taguchi용: 주효과 중심 ANOVA -------------------------
    def run_main_effects_anova(self, dataframe: pd.DataFrame, response: str, factors: list, analysis_type="부분요인 ANOVA"):
        if dataframe is None or dataframe.empty:
            self.error_occurred.emit("분석 오류", "분석할 데이터가 없습니다.")
            return
        if response not in dataframe.columns or any(f not in dataframe.columns for f in factors):
            self.error_occurred.emit("분석 오류", "요인/반응 열을 찾을 수 없습니다.")
            return
        try:
            df = dataframe.copy()
            df[response] = pd.to_numeric(df[response], errors="coerce")
            df = df.dropna(subset=[response] + factors)
            if len(df) < len(factors) + 1:
                self.error_occurred.emit("분석 오류", "표본 수가 부족합니다.")
                return

            main_terms = " + ".join([f"C({f})" for f in factors])
            formula = f"{response} ~ {main_terms}"

            model = smf.ols(formula=formula, data=df).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)

            result = {
                "type": analysis_type,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "완료",
                "description": f"{analysis_type}: response={response}, factors={', '.join(factors)}",
                "results": {
                    "formula": formula,
                    "anova": anova_table,
                    "factors": factors,
                    "response": response,
                    "coefficients": model.params,
                    "r_squared": model.rsquared,
                    "adj_r_squared": model.rsquared_adj,
                    "n_obs": int(model.nobs),
                    "residuals": model.resid.tolist(),
                    "fitted": model.fittedvalues.tolist(),
                },
            }
            self.analysis_completed.emit(analysis_type, result)
            self.status_updated.emit(f"{analysis_type}가 완료되었습니다.")
        except Exception as exc:
            self.error_occurred.emit(f"{analysis_type} 실패", f"분석 중 오류가 발생했습니다:\n{exc}")

    # RSM/CCD/Box-Behnken: 2차 모델 적합 ---------------------------------
    def run_rsm_quadratic(self, dataframe: pd.DataFrame, response: str, factors: list, analysis_type="RSM"):
        if dataframe is None or dataframe.empty:
            self.error_occurred.emit("분석 오류", "분석할 데이터가 없습니다.")
            return
        if response not in dataframe.columns or any(f not in dataframe.columns for f in factors):
            self.error_occurred.emit("분석 오류", "요인/반응 열을 찾을 수 없습니다.")
            return
        try:
            df = dataframe.copy()
            df[response] = pd.to_numeric(df[response], errors="coerce")
            df = df.dropna(subset=[response] + factors)
            if len(df) < len(factors) + 1:
                self.error_occurred.emit("분석 오류", "표본 수가 부족합니다.")
                return

            # 2차 모델 공식 생성: main + interaction + squared
            terms = [f"{f}" for f in factors]
            inter_terms = [f"{f1}:{f2}" for i, f1 in enumerate(factors) for f2 in factors[i + 1 :]]
            quad_terms = [f"I({f}**2)" for f in factors]
            formula_rhs = " + ".join(terms + inter_terms + quad_terms)
            formula = f"{response} ~ {formula_rhs}"

            model = smf.ols(formula=formula, data=df).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)

            result = {
                "type": analysis_type,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "완료",
                "description": f"{analysis_type}: response={response}, factors={', '.join(factors)}",
                "results": {
                    "formula": formula,
                    "anova": anova_table,
                    "factors": factors,
                    "response": response,
                    "coefficients": model.params,
                    "r_squared": model.rsquared,
                    "adj_r_squared": model.rsquared_adj,
                    "n_obs": int(model.nobs),
                    "residuals": model.resid.tolist(),
                    "fitted": model.fittedvalues.tolist(),
                },
            }
            self.analysis_completed.emit(analysis_type, result)
            self.status_updated.emit(f"{analysis_type}가 완료되었습니다.")
        except Exception as exc:
            self.error_occurred.emit(f"{analysis_type} 실패", f"분석 중 오류가 발생했습니다:\n{exc}")
    # ANOVA ---------------------------------------------------------------
    @Slot(pd.DataFrame)
    def run_anova(self, dataframe: pd.DataFrame):
        if not self._validate_data(dataframe):
            return
        try:
            self.status_updated.emit("ANOVA 분석을 수행하는 중입니다...")
            numeric_cols = dataframe.select_dtypes(include=[np.number]).columns
            categorical_cols = dataframe.select_dtypes(include=["object", "category"]).columns

            if len(numeric_cols) == 0:
                self.error_occurred.emit("분석 오류", "ANOVA에는 숫자형 종속변수가 필요합니다.")
                return
            if len(categorical_cols) == 0:
                self.error_occurred.emit("분석 오류", "ANOVA에는 범주형 독립변수가 필요합니다.")
                return

            try:
                from scipy import stats
            except ImportError:
                self.error_occurred.emit("분석 오류", "scipy가 설치되어 있지 않아 ANOVA를 실행할 수 없습니다.")
                return

            categorical_var = categorical_cols[0]
            numeric_var = numeric_cols[0]

            groups = []
            names = []
            for group_name in dataframe[categorical_var].dropna().unique():
                group_data = dataframe[dataframe[categorical_var] == group_name][numeric_var].dropna()
                if len(group_data) > 0:
                    groups.append(group_data)
                    names.append(str(group_name))

            if len(groups) < 2:
                self.error_occurred.emit("분석 오류", "ANOVA에는 최소 2개 이상의 그룹이 필요합니다.")
                return

            f_stat, p_value = stats.f_oneway(*groups)
            group_stats = [
                {
                    "group": names[i],
                    "count": len(group),
                    "mean": group.mean(),
                    "std": group.std(),
                    "min": group.min(),
                    "max": group.max(),
                }
                for i, group in enumerate(groups)
            ]

            result = {
                "type": "ANOVA",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "완료",
                "description": f"{categorical_var} ~ {numeric_var} 일원분산분석",
                "results": {
                    "independent_var": categorical_var,
                    "dependent_var": numeric_var,
                    "f_statistic": f_stat,
                    "p_value": p_value,
                    "significant": p_value < 0.05,
                    "group_count": len(groups),
                    "group_stats": group_stats,
                    "interpretation": self._interpret_anova_result(p_value),
                },
            }

            self.analysis_completed.emit("ANOVA", result)
            self.status_updated.emit("ANOVA 분석이 완료되었습니다.")
        except Exception as exc:  # pragma: no cover
            self.error_occurred.emit("ANOVA 실패", f"분석 중 오류가 발생했습니다:\n{exc}")

    # 회귀분석 -------------------------------------------------------------
    @Slot(pd.DataFrame)
    def run_regression(self, dataframe: pd.DataFrame):
        if not self._validate_data(dataframe):
            return
        try:
            self.status_updated.emit("회귀분석을 수행하는 중입니다...")
            numeric_data = dataframe.select_dtypes(include=[np.number])
            if len(numeric_data.columns) < 2:
                self.error_occurred.emit("분석 오류", "회귀분석에는 최소 2개의 숫자형 변수가 필요합니다.")
                return

            try:
                from sklearn.linear_model import LinearRegression
                from sklearn.metrics import mean_squared_error, r2_score
            except ImportError:
                self.error_occurred.emit("분석 오류", "scikit-learn이 설치되어 있지 않아 회귀분석을 실행할 수 없습니다.")
                return

            y = numeric_data.iloc[:, 0].dropna()
            X = numeric_data.iloc[:, 1:].dropna()
            common_index = y.index.intersection(X.index)
            y = y.loc[common_index]
            X = X.loc[common_index]

            if len(y) < 3:
                self.error_occurred.emit("분석 오류", "회귀분석에는 최소 3개 이상의 관측치가 필요합니다.")
                return

            model = LinearRegression()
            model.fit(X, y)
            y_pred = model.predict(X)

            r2 = r2_score(y, y_pred)
            mse = mean_squared_error(y, y_pred)
            rmse = np.sqrt(mse)

            coefficients = [
                {"variable": col, "coefficient": model.coef_[i], "abs_coefficient": abs(model.coef_[i])}
                for i, col in enumerate(X.columns)
            ]

            result = {
                "type": "회귀분석",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "완료",
                "description": f"{y.name} ~ {len(X.columns)}개 변수의 선형회귀",
                "results": {
                    "dependent_var": y.name,
                    "independent_vars": list(X.columns),
                    "intercept": model.intercept_,
                    "coefficients": coefficients,
                    "r_squared": r2,
                    "rmse": rmse,
                    "observations": len(y),
                    "model_fit": self._interpret_r_squared(r2),
                },
            }

            self.analysis_completed.emit("회귀분석", result)
            self.status_updated.emit("회귀분석이 완료되었습니다.")
        except Exception as exc:  # pragma: no cover
            self.error_occurred.emit("회귀분석 실패", f"분석 중 오류가 발생했습니다:\n{exc}")

    # 검증/해석 -----------------------------------------------------------
    def _validate_data(self, dataframe: pd.DataFrame) -> bool:
        if dataframe is None or dataframe.empty:
            self.error_occurred.emit("분석 오류", "분석할 데이터가 없습니다.")
            return False
        if len(dataframe) < 3:
            self.error_occurred.emit("분석 오류", "분석에는 최소 3행 이상의 데이터가 필요합니다.")
            return False
        return True

    def _get_correlation_strength(self, abs_corr: float) -> str:
        if abs_corr >= 0.9:
            return "매우 강함"
        elif abs_corr >= 0.7:
            return "강함"
        elif abs_corr >= 0.5:
            return "보통"
        elif abs_corr >= 0.3:
            return "약함"
        else:
            return "매우 약함"

    def _interpret_anova_result(self, p_value: float) -> str:
        if p_value < 0.001:
            return "그룹 차이가 매우 유의함 (p < 0.001)"
        elif p_value < 0.01:
            return "그룹 차이가 유의함 (p < 0.01)"
        elif p_value < 0.05:
            return "그룹 차이가 유의함 (p < 0.05)"
        else:
            return "그룹 차이가 통계적으로 유의하지 않음 (p ≥ 0.05)"

    def _interpret_r_squared(self, r2: float) -> str:
        if r2 >= 0.9:
            return "매우 좋은 적합"
        elif r2 >= 0.7:
            return "좋은 적합"
        elif r2 >= 0.5:
            return "보통 적합"
        elif r2 >= 0.3:
            return "낮은 적합"
        else:
            return "매우 낮은 적합"
