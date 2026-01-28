"""
분석 결과 상세 보기 다이얼로그
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTextEdit, QLabel, QTableWidget, QTableWidgetItem, QScrollArea,
    QPushButton, QGroupBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
try:
    from scipy import stats
except Exception:  # scipy 미설치 환경 대비
    stats = None

class AnalysisDetailDialog(QDialog):
    """분석 결과 상세 보기 다이얼로그"""
    
    def __init__(self, analysis_type, result_data, parent=None):
        super().__init__(parent)
        
        self.analysis_type = analysis_type
        self.result_data = result_data
        
        self.setup_ui()
        self.populate_content()
    
    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle(f"📊 {self.analysis_type} 분석 결과 상세보기")
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)
        
        layout = QVBoxLayout(self)
        
        # 헤더
        self.setup_header()
        layout.addWidget(self.header_widget)
        
        # 메인 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 결과 요약 탭
        self.setup_summary_tab()
        self.tab_widget.addTab(self.summary_tab, "📋 결과 요약")
        
        # 상세 데이터 탭
        self.setup_data_tab()
        self.tab_widget.addTab(self.data_tab, "📊 상세 데이터")
        
        # 시각화 탭
        self.setup_visualization_tab()
        self.tab_widget.addTab(self.visualization_tab, "📈 시각화")
        
        # 해석 및 권장사항 탭
        self.setup_interpretation_tab()
        self.tab_widget.addTab(self.interpretation_tab, "💡 해석 & 권장사항")
        
        layout.addWidget(self.tab_widget)
        
        # 하단 버튼
        self.setup_buttons()
        layout.addWidget(self.button_widget)
    
    def setup_header(self):
        """헤더 설정"""
        self.header_widget = QGroupBox()
        layout = QVBoxLayout(self.header_widget)
        
        # 제목
        title_label = QLabel(f"🔬 {self.analysis_type} 분석 결과")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 기본 정보
        info_text = f"분석 시간: {self.result_data.get('timestamp', 'N/A')}"
        if 'summary' in self.result_data:
            info_text += f"\n요약: {self.result_data['summary']}"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(info_label)
    
    def setup_summary_tab(self):
        """결과 요약 탭"""
        self.summary_tab = QWidget()
        layout = QVBoxLayout(self.summary_tab)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 주요 결과 요약
        summary_group = QGroupBox("📋 주요 결과")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(200)
        summary_layout.addWidget(self.summary_text)
        
        scroll_layout.addWidget(summary_group)
        
        # 핵심 지표
        metrics_group = QGroupBox("📊 핵심 지표")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.metrics_table = QTableWidget()
        metrics_layout.addWidget(self.metrics_table)
        
        scroll_layout.addWidget(metrics_group)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
    
    def setup_data_tab(self):
        """상세 데이터 탭"""
        self.data_tab = QWidget()
        layout = QVBoxLayout(self.data_tab)
        
        # 데이터 테이블
        self.data_table = QTableWidget()
        layout.addWidget(self.data_table)
    
    def setup_visualization_tab(self):
        """시각화 탭"""
        self.visualization_tab = QWidget()
        layout = QVBoxLayout(self.visualization_tab)
        
        # matplotlib 캔버스
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
    
    def setup_interpretation_tab(self):
        """해석 및 권장사항 탭"""
        self.interpretation_tab = QWidget()
        layout = QVBoxLayout(self.interpretation_tab)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 결과 해석
        interpretation_group = QGroupBox("🤖 결과 해석")
        interpretation_layout = QVBoxLayout(interpretation_group)
        
        self.interpretation_text = QTextEdit()
        self.interpretation_text.setMinimumHeight(200)
        interpretation_layout.addWidget(self.interpretation_text)
        
        scroll_layout.addWidget(interpretation_group)
        
        # 실무 적용 방안
        application_group = QGroupBox("💼 실무 적용 방안")
        application_layout = QVBoxLayout(application_group)
        
        self.application_text = QTextEdit()
        self.application_text.setMinimumHeight(150)
        application_layout.addWidget(self.application_text)
        
        scroll_layout.addWidget(application_group)
        
        # 추가 분석 제안
        suggestions_group = QGroupBox("🔍 추가 분석 제안")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setMinimumHeight(150)
        suggestions_layout.addWidget(self.suggestions_text)
        
        scroll_layout.addWidget(suggestions_group)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
    
    def setup_buttons(self):
        """하단 버튼 설정"""
        self.button_widget = QWidget()
        layout = QHBoxLayout(self.button_widget)
        
        # 내보내기 버튼
        export_btn = QPushButton("📤 결과 내보내기")
        export_btn.clicked.connect(self.export_results)
        layout.addWidget(export_btn)
        
        # 인쇄 버튼
        print_btn = QPushButton("🖨️ 인쇄")
        print_btn.clicked.connect(self.print_results)
        layout.addWidget(print_btn)
        
        layout.addStretch()
        
        # 닫기 버튼
        close_btn = QPushButton("❌ 닫기")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def populate_content(self):
        """분석 유형에 따른 내용 채우기"""
        if self.analysis_type == "기초 통계":
            self.populate_basic_stats()
        elif self.analysis_type == "상관분석":
            self.populate_correlation()
        elif self.analysis_type == "ANOVA":
            self.populate_anova()
        elif self.analysis_type == "회귀분석":
            self.populate_regression()
        elif self.analysis_type == "DOE ANOVA":
            self.populate_doe_anova()
        else:
            # 그 밖의 분석 유형은 공통 ANOVA/회귀 정보로 요약
            self.populate_generic_anova()
    
    def populate_basic_stats(self):
        """기초 통계 분석 결과 채우기"""
        data = self.result_data.get('data')
        
        # 요약 텍스트
        summary = f"""
🔍 기초 통계 분석 결과

📊 분석 개요:
• 분석된 변수 수: {len(data.columns) if data is not None else 0}개
• 주요 통계량: 평균, 표준편차, 최솟값, 최댓값, 사분위수

📈 주요 발견사항:
• 모든 숫자형 변수에 대한 기술통계량을 계산했습니다
• 각 변수의 분포 특성과 변동성을 파악할 수 있습니다
• 이상값이나 특이한 패턴을 식별할 수 있습니다
        """
        self.summary_text.setText(summary.strip())
        
        # 핵심 지표 테이블
        if data is not None:
            self.metrics_table.setRowCount(len(data.columns))
            self.metrics_table.setColumnCount(4)
            self.metrics_table.setHorizontalHeaderLabels(["변수명", "평균", "표준편차", "변동계수"])
            
            for i, col in enumerate(data.columns):
                mean_val = data[col].mean()
                std_val = data[col].std()
                cv = std_val / mean_val if mean_val != 0 else 0
                
                self.metrics_table.setItem(i, 0, QTableWidgetItem(col))
                self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{mean_val:.3f}"))
                self.metrics_table.setItem(i, 2, QTableWidgetItem(f"{std_val:.3f}"))
                self.metrics_table.setItem(i, 3, QTableWidgetItem(f"{cv:.3f}"))
        
        # 상세 데이터 테이블
        if data is not None:
            self.populate_data_table(data)
        
        # 시각화
        self.create_basic_stats_visualization()
        
        # 해석
        self.populate_basic_stats_interpretation()
    
    def populate_correlation(self):
        """상관분석 결과 채우기"""
        data = self.result_data.get('data')
        
        # 요약 텍스트
        summary = f"""
🔍 상관분석 결과

📊 분석 개요:
• 분석된 변수 수: {len(data.columns) if data is not None else 0}개
• 상관계수 범위: -1 ~ +1
• 해석 기준: |r| > 0.7 (강한 상관), 0.3 < |r| < 0.7 (중간 상관), |r| < 0.3 (약한 상관)

📈 주요 발견사항:
• 변수간 선형 관계의 강도와 방향을 파악했습니다
• 다중공선성 문제를 사전에 확인할 수 있습니다
• 예측 모델링을 위한 변수 선택에 활용할 수 있습니다
        """
        self.summary_text.setText(summary.strip())
        
        # 핵심 지표 - 강한 상관관계 찾기
        if data is not None:
            strong_corr = []
            for i in range(len(data.columns)):
                for j in range(i+1, len(data.columns)):
                    corr_val = data.iloc[i, j]
                    if abs(corr_val) > 0.5:  # 중간 이상의 상관관계
                        strong_corr.append((data.columns[i], data.columns[j], corr_val))
            
            self.metrics_table.setRowCount(len(strong_corr))
            self.metrics_table.setColumnCount(3)
            self.metrics_table.setHorizontalHeaderLabels(["변수 1", "변수 2", "상관계수"])
            
            for i, (var1, var2, corr) in enumerate(strong_corr):
                self.metrics_table.setItem(i, 0, QTableWidgetItem(var1))
                self.metrics_table.setItem(i, 1, QTableWidgetItem(var2))
                self.metrics_table.setItem(i, 2, QTableWidgetItem(f"{corr:.3f}"))
        
        # 상세 데이터 테이블
        if data is not None:
            self.populate_data_table(data)
        
        # 시각화
        self.create_correlation_visualization()
        
        # 해석
        self.populate_correlation_interpretation()
    
    def populate_anova(self):
        """ANOVA 분석 결과 채우기"""
        # ANOVA 결과 처리
        summary = f"""
🔍 ANOVA 분석 결과

📊 분석 개요:
• 종속변수: {self.result_data.get('dependent_variable', 'N/A')}
• 요인변수: {self.result_data.get('factor_variable', 'N/A')}
• 그룹간 차이 검정을 수행했습니다

📈 주요 발견사항:
• 각 그룹별 평균과 표준편차를 비교했습니다
• 그룹간 유의한 차이가 있는지 확인했습니다
• 실험계획법에서 요인의 효과를 평가했습니다
        """
        self.summary_text.setText(summary.strip())
        
        # 그룹 통계 테이블
        group_stats = self.result_data.get('group_statistics')
        if group_stats is not None:
            self.populate_data_table(group_stats)
        
        # 시각화
        self.create_anova_visualization()
        
        # 해석
        self.populate_anova_interpretation()
    
    def populate_regression(self):
        """회귀분석 결과 채우기"""
        # 회귀분석 결과 처리
        r_squared = self.result_data.get('r_squared', 0)
        
        summary = f"""
🔍 회귀분석 결과

📊 분석 개요:
• 종속변수: {self.result_data.get('dependent_variable', 'N/A')}
• 독립변수 수: {len(self.result_data.get('independent_variables', []))}개
• 결정계수 (R²): {r_squared:.3f}
• 관측치 수: {self.result_data.get('n_observations', 0)}개

📈 주요 발견사항:
• 모델이 종속변수 변동의 {r_squared*100:.1f}%를 설명합니다
• 각 독립변수의 영향력을 계수로 확인할 수 있습니다
• 예측 모델로 활용할 수 있습니다
        """
        self.summary_text.setText(summary.strip())
        
        # 회귀계수 테이블
        coefficients = self.result_data.get('coefficients', {})
        if coefficients:
            self.metrics_table.setRowCount(len(coefficients) + 1)
            self.metrics_table.setColumnCount(2)
            self.metrics_table.setHorizontalHeaderLabels(["변수", "회귀계수"])
            
            # 절편
            intercept = self.result_data.get('intercept', 0)
            self.metrics_table.setItem(0, 0, QTableWidgetItem("절편"))
            self.metrics_table.setItem(0, 1, QTableWidgetItem(f"{intercept:.3f}"))
            
            # 계수들
            for i, (var, coef) in enumerate(coefficients.items(), 1):
                self.metrics_table.setItem(i, 0, QTableWidgetItem(var))
                self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{coef:.3f}"))
        
        # 시각화
        self.create_regression_visualization()
        
        # 해석
        self.populate_regression_interpretation()

    def populate_doe_anova(self):
        """DOE ANOVA 상세 결과 채우기"""
        results = self.result_data.get("results", {})
        response = results.get("response", "N/A")
        factors = results.get("factors", [])
        r2 = results.get("r_squared")
        adj_r2 = results.get("adj_r_squared")
        n_obs = results.get("n_obs")
        anova_df = results.get("anova")
        coefficients = results.get("coefficients")

        def _fmt(val, digits=3):
            if val is None:
                return "N/A"
            if isinstance(val, (int, float, np.floating)):
                return f"{val:.{digits}f}"
            return str(val)

        summary = f"""
🔍 DOE ANOVA 결과

📊 분석 개요:
• 반응 변수: {response}
• 요인: {', '.join(factors) if factors else 'N/A'}
• 관측치 수: { _fmt(n_obs, 0) }
• 결정계수: R²={_fmt(r2)}, Adj.R²={_fmt(adj_r2)}

📈 주요 발견사항:
• 각 요인의 주효과 및 2차 상호작용을 평가했습니다
• F-통계량과 p-값을 통해 유의한 요인을 식별할 수 있습니다
• 계수를 통해 효과 방향과 크기를 해석할 수 있습니다
        """
        self.summary_text.setText(summary.strip())

        # 핵심 지표 테이블
        metrics = [
            ("R²", r2),
            ("Adj. R²", adj_r2),
            ("관측치", n_obs),
        ]
        # 최고 영향 요인 (p-value 정렬)
        if isinstance(anova_df, pd.DataFrame) and "PR(>F)" in anova_df.columns:
            sorted_anova = anova_df.dropna(subset=["PR(>F)"]).sort_values("PR(>F)")
            if not sorted_anova.empty:
                top_term = sorted_anova.index[0]
                top_p = sorted_anova.iloc[0]["PR(>F)"]
                metrics.append(("가장 유의한 요인", f"{top_term} (p={top_p:.3g})"))

        self.metrics_table.setRowCount(len(metrics))
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["지표", "값"])
        for i, (k, v) in enumerate(metrics):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(str(k)))
            self.metrics_table.setItem(i, 1, QTableWidgetItem("N/A" if v is None else f"{v:.4g}" if isinstance(v, (int, float)) else str(v)))

        # 상세 데이터 테이블 (ANOVA 표)
        if isinstance(anova_df, pd.DataFrame):
            self.populate_data_table(anova_df.reset_index().rename(columns={"index": "Term"}))

        # 시각화: F-통계량 막대 그래프
        self.figure.clear()
        residuals = results.get("residuals")
        fitted = results.get("fitted")
        if self._plot_residual_diagnostics(residuals, fitted):
            pass
        elif isinstance(anova_df, pd.DataFrame) and "F" in anova_df.columns:
            ax = self.figure.add_subplot(111)
            plot_df = anova_df.copy()
            plot_df = plot_df.drop(index="Residual", errors="ignore")
            if not plot_df.empty:
                ax.bar(plot_df.index.astype(str), plot_df["F"].fillna(0))
                ax.set_ylabel("F-statistic")
                ax.set_title("DOE 요인 효과 (F 통계량)")
                ax.tick_params(axis='x', rotation=30)
        self.canvas.draw()

        # 해석
        interpretation = """
🤖 해석:
• p-값이 0.05보다 작은 요인은 반응에 유의미한 영향을 줍니다.
• 상호작용 항의 p-값이 낮다면 요인 조합을 함께 최적화해야 합니다.
• 잔차의 자유도가 충분히 큰지 확인해 모델 적합성을 점검하세요.

💡 적용/추가 제안:
• 유의한 요인 수준을 조합한 최적 조건을 실험해보세요.
• 필요하면 중심점/축소 실험을 추가해 반응표면을 탐색하세요.
• 잔차 정규성/등분산성을 플롯으로 확인해 가정 위반 여부를 검증하세요.
        """.strip()
        self.interpretation_text.setText(interpretation)
        self.application_text.setText("유의한 요인 조합을 생산 조건에 반영하고, 추가 실험으로 미세 조정하세요.")
        self.suggestions_text.setText("주효과/상호작용 플롯, 잔차 QQ 플롯, 예측값 vs 잔차 플롯을 추가로 확인하세요.")

    def _plot_residual_diagnostics(self, residuals, fitted):
        """잔차 진단 플롯(Residuals vs Fitted, QQ)"""
        if residuals is None or fitted is None or stats is None:
            return False
        try:
            res = np.asarray(residuals, dtype=float)
            fit = np.asarray(fitted, dtype=float)
            if len(res) != len(fit) or len(res) == 0:
                return False

            self.figure.clear()
            ax1 = self.figure.add_subplot(1, 2, 1)
            ax1.scatter(fit, res, alpha=0.7)
            ax1.axhline(0, color='gray', linestyle='--')
            ax1.set_xlabel("Fitted")
            ax1.set_ylabel("Residuals")
            ax1.set_title("Residuals vs Fitted")
            ax1.grid(True, alpha=0.3)

            ax2 = self.figure.add_subplot(1, 2, 2)
            stats.probplot(res, dist="norm", plot=ax2)
            ax2.set_title("QQ Plot")
            ax2.grid(True, alpha=0.3)

            self.figure.tight_layout()
            return True
        except Exception:
            return False

    def populate_generic_anova(self):
        """기타 분석 유형용 기본 채움: ANOVA 표와 간단 요약"""
        results = self.result_data.get("results", {})
        anova_df = results.get("anova")
        r2 = results.get("r_squared")
        adj_r2 = results.get("adj_r_squared")
        n_obs = results.get("n_obs")
        residuals = results.get("residuals")
        fitted = results.get("fitted")

        summary_lines = [f"분석 유형: {self.analysis_type}"]
        if r2 is not None:
            summary_lines.append(f"R²: {r2:.3f}")
        if adj_r2 is not None:
            summary_lines.append(f"Adj. R²: {adj_r2:.3f}")
        if n_obs is not None:
            summary_lines.append(f"관측치: {n_obs}")
        formula = results.get("formula")
        if formula:
            summary_lines.append(f"모델식: {formula}")
        self.summary_text.setText("\n".join(summary_lines))

        # 핵심 지표 테이블: 상위 F 또는 p 기준
        metrics = []
        if isinstance(anova_df, pd.DataFrame):
            df = anova_df.reset_index().rename(columns={"index": "Term"})
            if "F" in df.columns:
                top = df[df["Term"] != "Residual"].sort_values("F", ascending=False).head(3)
                for _, row in top.iterrows():
                    metrics.append((row["Term"], row["F"], row.get("PR(>F)", None)))
        self.metrics_table.setRowCount(len(metrics))
        self.metrics_table.setColumnCount(3)
        self.metrics_table.setHorizontalHeaderLabels(["요인", "F", "p-value"])
        for i, (term, fval, pval) in enumerate(metrics):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(str(term)))
            self.metrics_table.setItem(i, 1, QTableWidgetItem(f"{fval:.3f}"))
            if pval is None or pd.isna(pval):
                self.metrics_table.setItem(i, 2, QTableWidgetItem(""))
            else:
                self.metrics_table.setItem(i, 2, QTableWidgetItem(f"{pval:.3g}"))

        # 상세 데이터 탭에 ANOVA 표 표시
        if isinstance(anova_df, pd.DataFrame):
            self.populate_data_table(anova_df.reset_index().rename(columns={"index": "항목"}))

        # 시각화 탭: 잔차 진단이 있으면 우선 표시, 없으면 F-바차트
        self.figure.clear()
        if self._plot_residual_diagnostics(residuals, fitted):
            pass
        elif isinstance(anova_df, pd.DataFrame) and "F" in anova_df.columns:
            df_plot = anova_df.copy()
            if "Residual" in df_plot.index:
                df_plot = df_plot.drop(index="Residual", errors="ignore")
            df_plot = df_plot.sort_values("F", ascending=False).head(5)
            ax = self.figure.add_subplot(111)
            ax.bar(df_plot.index.astype(str), df_plot["F"].fillna(0))
            ax.set_title("요인별 F값 (상위)")
            ax.set_ylabel("F-statistic")
            ax.tick_params(axis='x', rotation=30)
        self.canvas.draw()
    
    def populate_data_table(self, data):
        """데이터 테이블 채우기"""
        if isinstance(data, pd.DataFrame):
            self.data_table.setRowCount(len(data))
            self.data_table.setColumnCount(len(data.columns))
            self.data_table.setHorizontalHeaderLabels([str(col) for col in data.columns])
            self.data_table.setVerticalHeaderLabels([str(idx) for idx in data.index])
            
            for i in range(len(data)):
                for j in range(len(data.columns)):
                    value = data.iloc[i, j]
                    if pd.isna(value):
                        item_text = "NaN"
                    elif isinstance(value, (int, float)):
                        item_text = f"{value:.3f}"
                    else:
                        item_text = str(value)
                    self.data_table.setItem(i, j, QTableWidgetItem(item_text))
    
    def create_basic_stats_visualization(self):
        """기초 통계 시각화"""
        self.figure.clear()
        
        data = self.result_data.get('data')
        if data is not None:
            # 2x2 서브플롯
            ax1 = self.figure.add_subplot(2, 2, 1)
            ax2 = self.figure.add_subplot(2, 2, 2)
            ax3 = self.figure.add_subplot(2, 2, 3)
            ax4 = self.figure.add_subplot(2, 2, 4)
            
            # 평균 막대 차트
            means = data.mean()
            ax1.bar(range(len(means)), means.values)
            ax1.set_title('변수별 평균')
            ax1.set_xticks(range(len(means)))
            ax1.set_xticklabels(means.index, rotation=45)
            
            # 표준편차 막대 차트
            stds = data.std()
            ax2.bar(range(len(stds)), stds.values)
            ax2.set_title('변수별 표준편차')
            ax2.set_xticks(range(len(stds)))
            ax2.set_xticklabels(stds.index, rotation=45)
            
            # 변동계수
            cv = stds / means
            ax3.bar(range(len(cv)), cv.values)
            ax3.set_title('변수별 변동계수')
            ax3.set_xticks(range(len(cv)))
            ax3.set_xticklabels(cv.index, rotation=45)
            
            # 박스플롯
            data_for_box = [data[col].dropna().values for col in data.columns]
            ax4.boxplot(data_for_box, labels=data.columns)
            ax4.set_title('변수별 분포')
            ax4.tick_params(axis='x', rotation=45)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def create_correlation_visualization(self):
        """상관분석 시각화"""
        self.figure.clear()
        
        data = self.result_data.get('data')
        if data is not None:
            ax = self.figure.add_subplot(1, 1, 1)
            
            # 히트맵
            im = ax.imshow(data.values, cmap='coolwarm', vmin=-1, vmax=1)
            
            # 축 레이블
            ax.set_xticks(range(len(data.columns)))
            ax.set_yticks(range(len(data.columns)))
            ax.set_xticklabels(data.columns, rotation=45)
            ax.set_yticklabels(data.columns)
            
            # 값 표시
            for i in range(len(data.columns)):
                for j in range(len(data.columns)):
                    text = ax.text(j, i, f'{data.iloc[i, j]:.2f}',
                                 ha="center", va="center", color="black")
            
            ax.set_title('상관계수 히트맵')
            self.figure.colorbar(im, ax=ax)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def create_anova_visualization(self):
        """ANOVA 시각화"""
        self.figure.clear()
        
        group_stats = self.result_data.get('group_statistics')
        if group_stats is not None:
            ax = self.figure.add_subplot(1, 1, 1)
            
            # 그룹별 평균과 표준편차
            means = group_stats['mean']
            stds = group_stats['std']
            
            x_pos = range(len(means))
            ax.bar(x_pos, means.values, yerr=stds.values, capsize=5)
            ax.set_xlabel('그룹')
            ax.set_ylabel('평균값')
            ax.set_title('그룹별 평균 비교')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(means.index)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def create_regression_visualization(self):
        """회귀분석 시각화"""
        self.figure.clear()
        
        # 회귀계수 시각화
        coefficients = self.result_data.get('coefficients', {})
        if coefficients:
            ax = self.figure.add_subplot(1, 1, 1)
            
            vars_list = list(coefficients.keys())
            coefs_list = list(coefficients.values())
            
            colors = ['red' if x < 0 else 'blue' for x in coefs_list]
            ax.barh(vars_list, coefs_list, color=colors)
            ax.set_xlabel('회귀계수')
            ax.set_title('변수별 회귀계수')
            ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def populate_basic_stats_interpretation(self):
        """기초 통계 해석"""
        interpretation = """
🤖 기초 통계 분석 해석:

📊 데이터 특성:
• 각 변수의 중심경향성(평균, 중앙값)과 산포도(표준편차, 범위)를 파악했습니다
• 변동계수를 통해 변수별 상대적 변동성을 비교할 수 있습니다
• 사분위수를 통해 데이터의 분포 형태를 이해할 수 있습니다

🔍 주요 관찰사항:
• 변동계수가 높은 변수는 상대적으로 불안정한 특성을 보입니다
• 최솟값과 최댓값의 차이가 큰 변수는 이상값 존재 가능성이 있습니다
• 평균과 중앙값의 차이가 큰 경우 분포가 치우쳐 있을 수 있습니다
        """
        self.interpretation_text.setText(interpretation.strip())
        
        application = """
💼 실무 적용 방안:

1. 품질 관리:
   • 변동계수가 높은 공정 변수는 관리 강화 필요
   • 관리도 작성 시 기준선 설정에 활용

2. 실험 설계:
   • 변동성이 큰 변수는 더 많은 반복 실험 필요
   • 블록 설계 시 블록 변수 선정에 활용

3. 데이터 전처리:
   • 이상값 탐지 및 처리 방향 결정
   • 정규화/표준화 필요성 판단
        """
        self.application_text.setText(application.strip())
        
        suggestions = """
🔍 추가 분석 제안:

1. 분포 분석:
   • 정규성 검정 (Shapiro-Wilk, Anderson-Darling)
   • 히스토그램 및 Q-Q 플롯 작성

2. 이상값 분석:
   • 박스플롯을 통한 이상값 시각화
   • Z-score 또는 IQR 방법으로 이상값 탐지

3. 변수간 관계 분석:
   • 상관분석으로 변수간 선형 관계 파악
   • 산점도 매트릭스로 비선형 관계 탐색
        """
        self.suggestions_text.setText(suggestions.strip())
    
    def populate_correlation_interpretation(self):
        """상관분석 해석"""
        interpretation = """
🤖 상관분석 해석:

📊 상관관계 해석 기준:
• |r| ≥ 0.7: 강한 상관관계 (매우 밀접한 관계)
• 0.3 ≤ |r| < 0.7: 중간 상관관계 (어느 정도 관계)
• |r| < 0.3: 약한 상관관계 (관계가 미약)

🔍 주요 관찰사항:
• 양의 상관관계: 한 변수가 증가하면 다른 변수도 증가
• 음의 상관관계: 한 변수가 증가하면 다른 변수는 감소
• 상관계수가 0에 가까우면 선형 관계가 없음을 의미
        """
        self.interpretation_text.setText(interpretation.strip())
        
        application = """
💼 실무 적용 방안:

1. 변수 선택:
   • 높은 상관관계를 보이는 변수들 중 하나만 선택하여 다중공선성 방지
   • 예측 모델링 시 독립변수 선정에 활용

2. 공정 관리:
   • 상관관계가 높은 변수들을 함께 모니터링
   • 한 변수의 변화로 다른 변수의 변화 예측 가능

3. 실험 설계:
   • 상관관계가 높은 요인들은 교호작용 가능성 검토
   • 블록 설계 시 상관관계 고려
        """
        self.application_text.setText(application.strip())
        
        suggestions = """
🔍 추가 분석 제안:

1. 편상관분석:
   • 다른 변수의 영향을 제거한 순수한 상관관계 분석

2. 주성분분석:
   • 상관관계가 높은 변수들을 주성분으로 축약

3. 회귀분석:
   • 상관관계를 바탕으로 예측 모델 구축
   • 인과관계 분석을 위한 추가 검정
        """
        self.suggestions_text.setText(suggestions.strip())
    
    def populate_anova_interpretation(self):
        """ANOVA 해석"""
        interpretation = """
🤖 ANOVA 분석 해석:

📊 분산분석의 목적:
• 여러 그룹간 평균의 차이가 통계적으로 유의한지 검정
• 요인(처리)이 반응변수에 미치는 영향 평가
• 그룹 내 변동과 그룹간 변동 비교

🔍 주요 관찰사항:
• 각 그룹별 평균과 표준편차 비교
• 그룹간 차이의 크기와 방향 파악
• 변동성의 균질성 확인
        """
        self.interpretation_text.setText(interpretation.strip())
        
        application = """
💼 실무 적용 방안:

1. 품질 개선:
   • 최적 조건(그룹) 식별
   • 공정 조건별 성능 비교

2. 실험계획법:
   • 요인의 주효과 평가
   • 유의한 요인 식별 및 최적화

3. 의사결정:
   • 여러 대안 중 최적안 선택
   • 투자 효과 검증
        """
        self.application_text.setText(application.strip())
        
        suggestions = """
🔍 추가 분석 제안:

1. 사후검정:
   • Tukey HSD, Bonferroni 등으로 그룹간 개별 비교

2. 효과크기 분석:
   • Cohen's d, eta-squared로 실질적 의미 평가

3. 잔차분석:
   • 정규성, 등분산성, 독립성 가정 검증
   • 이상값 및 영향점 탐지
        """
        self.suggestions_text.setText(suggestions.strip())
    
    def populate_regression_interpretation(self):
        """회귀분석 해석"""
        r_squared = self.result_data.get('r_squared', 0)
        
        interpretation = f"""
🤖 회귀분석 해석:

📊 모델 성능:
• 결정계수 (R²): {r_squared:.3f}
• 설명력: 모델이 종속변수 변동의 {r_squared*100:.1f}%를 설명
• 모델 적합도: {'우수' if r_squared > 0.7 else '보통' if r_squared > 0.5 else '개선 필요'}

🔍 회귀계수 해석:
• 양의 계수: 독립변수 증가 시 종속변수도 증가
• 음의 계수: 독립변수 증가 시 종속변수는 감소
• 계수의 크기: 영향력의 상대적 크기
        """
        self.interpretation_text.setText(interpretation.strip())
        
        application = """
💼 실무 적용 방안:

1. 예측 모델링:
   • 새로운 조건에서의 결과 예측
   • 목표값 달성을 위한 조건 설정

2. 공정 최적화:
   • 영향력이 큰 변수 우선 관리
   • 비용 대비 효과 분석

3. 의사결정 지원:
   • 시나리오별 결과 예측
   • 리스크 평가 및 관리
        """
        self.application_text.setText(application.strip())
        
        suggestions = """
🔍 추가 분석 제안:

1. 모델 진단:
   • 잔차분석으로 모델 가정 검증
   • 영향점 및 이상값 탐지

2. 변수 선택:
   • 단계적 회귀분석으로 최적 변수 조합 탐색
   • 정규화 회귀(Ridge, Lasso) 적용

3. 비선형 모델:
   • 다항회귀, 스플라인 회귀 검토
   • 머신러닝 모델과 성능 비교
        """
        self.suggestions_text.setText(suggestions.strip())
    
    def export_results(self):
        """결과 내보내기"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "분석 결과 내보내기",
            f"{self.analysis_type}_상세결과.txt",
            "텍스트 파일 (*.txt);;모든 파일 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"=== {self.analysis_type} 분석 결과 상세보고서 ===\n\n")
                    f.write(f"분석 시간: {self.result_data.get('timestamp', 'N/A')}\n\n")
                    
                    f.write("📋 결과 요약:\n")
                    f.write(self.summary_text.toPlainText())
                    f.write("\n\n")
                    
                    f.write("💡 해석 및 권장사항:\n")
                    f.write(self.interpretation_text.toPlainText())
                    f.write("\n\n")
                    
                    f.write("💼 실무 적용 방안:\n")
                    f.write(self.application_text.toPlainText())
                    f.write("\n\n")
                    
                    f.write("🔍 추가 분석 제안:\n")
                    f.write(self.suggestions_text.toPlainText())
                
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "완료", f"분석 결과를 저장했습니다:\n{file_path}")
                
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "오류", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def print_results(self):
        """결과 인쇄"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "인쇄", "인쇄 기능은 향후 구현 예정입니다.")
