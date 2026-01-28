"""
분석 결과 뷰
통계 분석 결과와 해석을 종합적으로 표시
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTextEdit, QLabel, QScrollArea, QGroupBox,
    QTableWidget, QTableWidgetItem, QSplitter,
    QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ResultsView(QWidget):
    """분석 결과 종합 뷰"""
    
    def __init__(self):
        super().__init__()
        
        self.current_data = None
        self.analysis_results = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        
        # 상단 요약 정보
        self.setup_summary_section()
        layout.addWidget(self.summary_section)
        
        # 메인 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 기초 통계 탭
        self.setup_basic_stats_tab()
        self.tab_widget.addTab(self.basic_stats_tab, "📊 기초 통계")
        
        # 고급 분석 탭
        self.setup_advanced_analysis_tab()
        self.tab_widget.addTab(self.advanced_analysis_tab, "🔬 고급 분석")
        
        # 해석 및 권장사항 탭
        self.setup_interpretation_tab()
        self.tab_widget.addTab(self.interpretation_tab, "💡 해석 & 권장사항")
        
        layout.addWidget(self.tab_widget)
    
    def setup_summary_section(self):
        """요약 정보 섹션"""
        self.summary_section = QGroupBox("📋 분석 요약")
        layout = QHBoxLayout(self.summary_section)
        
        # 데이터 요약
        self.data_summary_label = QLabel("데이터를 불러오면 요약 정보가 표시됩니다")
        self.data_summary_label.setStyleSheet("font-size: 12px; padding: 10px;")
        layout.addWidget(self.data_summary_label)
        
        # 분석 상태
        self.analysis_status_label = QLabel("분석 대기 중")
        self.analysis_status_label.setStyleSheet("font-size: 12px; color: orange; padding: 10px;")
        layout.addWidget(self.analysis_status_label)
    
    def setup_basic_stats_tab(self):
        """기초 통계 탭"""
        self.basic_stats_tab = QWidget()
        layout = QVBoxLayout(self.basic_stats_tab)
        
        # 스플리터로 좌우 분할
        splitter = QSplitter(Qt.Horizontal)
        
        # 좌측: 통계 테이블
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("📊 기술통계량"))
        self.stats_table = QTableWidget()
        left_layout.addWidget(self.stats_table)
        
        # 우측: 분포 정보
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_layout.addWidget(QLabel("📈 분포 특성"))
        self.distribution_info = QTextEdit()
        self.distribution_info.setMaximumHeight(200)
        right_layout.addWidget(self.distribution_info)
        
        # 정규성 검정 결과
        right_layout.addWidget(QLabel("🔍 정규성 검정"))
        self.normality_results = QTextEdit()
        self.normality_results.setMaximumHeight(150)
        right_layout.addWidget(self.normality_results)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter)
    
    def setup_advanced_analysis_tab(self):
        """고급 분석 탭"""
        self.advanced_analysis_tab = QWidget()
        layout = QVBoxLayout(self.advanced_analysis_tab)
        
        # 분석 결과 영역
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.advanced_layout = QVBoxLayout(scroll_widget)
        
        # 기본 메시지
        self.advanced_placeholder = QLabel("고급 분석 결과가 여기에 표시됩니다\n\n• ANOVA 분석\n• 회귀분석\n• 상관분석\n• 요인분석")
        self.advanced_placeholder.setAlignment(Qt.AlignCenter)
        self.advanced_placeholder.setStyleSheet("color: gray; font-size: 14px; padding: 50px;")
        self.advanced_layout.addWidget(self.advanced_placeholder)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
    
    def setup_interpretation_tab(self):
        """해석 및 권장사항 탭"""
        self.interpretation_tab = QWidget()
        layout = QVBoxLayout(self.interpretation_tab)
        
        # 자동 해석 영역
        interpretation_group = QGroupBox("🤖 자동 해석")
        interpretation_layout = QVBoxLayout(interpretation_group)
        
        self.auto_interpretation = QTextEdit()
        self.auto_interpretation.setPlaceholderText("데이터 분석 후 자동으로 해석이 생성됩니다...")
        interpretation_layout.addWidget(self.auto_interpretation)
        
        layout.addWidget(interpretation_group)
        
        # 권장사항 영역
        recommendations_group = QGroupBox("💡 권장사항")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations = QTextEdit()
        self.recommendations.setPlaceholderText("분석 결과에 따른 권장사항이 표시됩니다...")
        recommendations_layout.addWidget(self.recommendations)
        
        layout.addWidget(recommendations_group)
        
        # 추가 분석 제안
        suggestions_group = QGroupBox("🔍 추가 분석 제안")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.analysis_suggestions = QTextEdit()
        self.analysis_suggestions.setPlaceholderText("추가로 수행할 수 있는 분석들이 제안됩니다...")
        suggestions_layout.addWidget(self.analysis_suggestions)
        
        layout.addWidget(suggestions_group)
    
    def set_data(self, data):
        """데이터 설정 및 기초 분석 수행"""
        self.current_data = data
        if data is not None:
            self.update_summary()
            self.perform_basic_analysis()
            self.generate_interpretation()
    
    def update_summary(self):
        """요약 정보 업데이트"""
        if self.current_data is None:
            return
        
        data = self.current_data
        summary_text = f"📊 데이터: {data.shape[0]}행 × {data.shape[1]}열 | "
        summary_text += f"숫자형: {len(data.select_dtypes(include=['number']).columns)}개 | "
        summary_text += f"범주형: {len(data.select_dtypes(include=['object', 'category']).columns)}개"
        
        self.data_summary_label.setText(summary_text)
        self.analysis_status_label.setText("✅ 분석 완료")
        self.analysis_status_label.setStyleSheet("font-size: 12px; color: green; padding: 10px;")
    
    def perform_basic_analysis(self):
        """기초 통계 분석 수행"""
        if self.current_data is None:
            return
        
        # 숫자형 데이터만 선택
        numeric_data = self.current_data.select_dtypes(include=['number'])
        
        if numeric_data.empty:
            self.stats_table.setRowCount(1)
            self.stats_table.setColumnCount(1)
            self.stats_table.setItem(0, 0, QTableWidgetItem("숫자형 데이터가 없습니다"))
            return
        
        # 기술통계량 계산
        desc_stats = numeric_data.describe()
        
        # 테이블 설정
        self.stats_table.setRowCount(len(desc_stats.index))
        self.stats_table.setColumnCount(len(desc_stats.columns))
        self.stats_table.setHorizontalHeaderLabels([str(col) for col in desc_stats.columns])
        self.stats_table.setVerticalHeaderLabels([str(idx) for idx in desc_stats.index])
        
        # 데이터 입력
        for i, row_name in enumerate(desc_stats.index):
            for j, col_name in enumerate(desc_stats.columns):
                value = desc_stats.loc[row_name, col_name]
                self.stats_table.setItem(i, j, QTableWidgetItem(f"{value:.3f}"))
        
        # 분포 특성 분석
        self.analyze_distributions(numeric_data)
        
        # 정규성 검정
        self.test_normality(numeric_data)
    
    def analyze_distributions(self, numeric_data):
        """분포 특성 분석"""
        distribution_text = "📈 변수별 분포 특성:\n\n"
        
        for col in numeric_data.columns:
            data_col = numeric_data[col].dropna()
            
            # 기본 통계
            mean_val = data_col.mean()
            median_val = data_col.median()
            std_val = data_col.std()
            skew_val = data_col.skew()
            
            distribution_text += f"🔹 {col}:\n"
            distribution_text += f"  • 평균: {mean_val:.3f}\n"
            distribution_text += f"  • 중앙값: {median_val:.3f}\n"
            distribution_text += f"  • 표준편차: {std_val:.3f}\n"
            distribution_text += f"  • 왜도: {skew_val:.3f}"
            
            # 왜도 해석
            if abs(skew_val) < 0.5:
                distribution_text += " (대칭적)\n"
            elif skew_val > 0.5:
                distribution_text += " (우측 꼬리)\n"
            else:
                distribution_text += " (좌측 꼬리)\n"
            
            distribution_text += "\n"
        
        self.distribution_info.setText(distribution_text)
    
    def test_normality(self, numeric_data):
        """정규성 검정"""
        normality_text = "🔍 정규성 검정 결과:\n\n"
        
        try:
            from scipy import stats
            
            for col in numeric_data.columns:
                data_col = numeric_data[col].dropna()
                
                if len(data_col) < 3:
                    normality_text += f"🔹 {col}: 데이터 부족\n"
                    continue
                
                # Shapiro-Wilk 검정
                if len(data_col) <= 5000:  # 샘플 크기 제한
                    stat, p_value = stats.shapiro(data_col)
                    test_name = "Shapiro-Wilk"
                else:
                    # 큰 샘플의 경우 Kolmogorov-Smirnov 검정
                    stat, p_value = stats.kstest(data_col, 'norm')
                    test_name = "Kolmogorov-Smirnov"
                
                normality_text += f"🔹 {col} ({test_name}):\n"
                normality_text += f"  • 검정통계량: {stat:.4f}\n"
                normality_text += f"  • p-값: {p_value:.4f}\n"
                
                if p_value > 0.05:
                    normality_text += "  • 결론: 정규분포를 따름 (α=0.05)\n"
                else:
                    normality_text += "  • 결론: 정규분포를 따르지 않음 (α=0.05)\n"
                
                normality_text += "\n"
                
        except ImportError:
            normality_text += "정규성 검정을 위해 scipy 패키지가 필요합니다.\n"
            normality_text += "pip install scipy 명령으로 설치해주세요."
        
        self.normality_results.setText(normality_text)
    
    def generate_interpretation(self):
        """자동 해석 생성"""
        if self.current_data is None:
            return
        
        data = self.current_data
        numeric_data = data.select_dtypes(include=['number'])
        categorical_data = data.select_dtypes(include=['object', 'category'])
        
        # 자동 해석
        interpretation = "🤖 데이터 분석 자동 해석:\n\n"
        
        # 데이터 개요
        interpretation += f"📊 데이터 개요:\n"
        interpretation += f"• 총 {data.shape[0]}개의 관측치와 {data.shape[1]}개의 변수\n"
        interpretation += f"• 숫자형 변수 {len(numeric_data.columns)}개, 범주형 변수 {len(categorical_data.columns)}개\n\n"
        
        # 숫자형 변수 분석
        if not numeric_data.empty:
            interpretation += "📈 숫자형 변수 특성:\n"
            
            for col in numeric_data.columns:
                col_data = numeric_data[col].dropna()
                cv = col_data.std() / col_data.mean() if col_data.mean() != 0 else 0
                
                interpretation += f"• {col}: "
                if cv < 0.1:
                    interpretation += "변동성이 낮음 (안정적)\n"
                elif cv < 0.3:
                    interpretation += "변동성이 보통\n"
                else:
                    interpretation += "변동성이 높음 (주의 필요)\n"
            
            interpretation += "\n"
        
        # 범주형 변수 분석
        if not categorical_data.empty:
            interpretation += "📋 범주형 변수 특성:\n"
            
            for col in categorical_data.columns:
                unique_count = data[col].nunique()
                total_count = len(data[col].dropna())
                
                interpretation += f"• {col}: {unique_count}개 범주"
                if unique_count / total_count < 0.1:
                    interpretation += " (범주가 적음 - 분석에 적합)\n"
                elif unique_count / total_count > 0.5:
                    interpretation += " (범주가 많음 - 그룹화 고려)\n"
                else:
                    interpretation += " (적절한 범주 수)\n"
        
        self.auto_interpretation.setText(interpretation)
        
        # 권장사항 생성
        self.generate_recommendations()
        
        # 추가 분석 제안
        self.suggest_additional_analysis()
    
    def generate_recommendations(self):
        """권장사항 생성"""
        if self.current_data is None:
            return
        
        data = self.current_data
        numeric_data = data.select_dtypes(include=['number'])
        categorical_data = data.select_dtypes(include=['object', 'category'])
        
        recommendations = "💡 분석 권장사항:\n\n"
        
        # 데이터 품질 권장사항
        missing_ratio = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
        if missing_ratio > 0.05:
            recommendations += "⚠️ 결측값 처리:\n"
            recommendations += f"• 전체 데이터의 {missing_ratio*100:.1f}%가 결측값입니다\n"
            recommendations += "• 결측값 처리 방법을 고려해주세요 (제거, 대체 등)\n\n"
        
        # 변수 유형별 권장사항
        if len(numeric_data.columns) >= 2:
            recommendations += "📊 숫자형 변수 분석:\n"
            recommendations += "• 상관분석을 통해 변수간 관계를 파악해보세요\n"
            recommendations += "• 산점도를 통해 시각적으로 관계를 확인해보세요\n\n"
        
        if len(categorical_data.columns) >= 1 and len(numeric_data.columns) >= 1:
            recommendations += "🔍 그룹별 분석:\n"
            recommendations += "• 범주형 변수를 기준으로 그룹별 차이를 분석해보세요\n"
            recommendations += "• ANOVA 또는 t-검정을 고려해보세요\n\n"
        
        # 실험계획법 권장사항
        if len(categorical_data.columns) >= 2:
            recommendations += "🧪 실험계획법 분석:\n"
            recommendations += "• 주효과도를 통해 각 요인의 영향을 확인해보세요\n"
            recommendations += "• 상호작용도를 통해 요인간 상호작용을 분석해보세요\n\n"
        
        self.recommendations.setText(recommendations)
    
    def suggest_additional_analysis(self):
        """추가 분석 제안"""
        if self.current_data is None:
            return
        
        data = self.current_data
        numeric_data = data.select_dtypes(include=['number'])
        categorical_data = data.select_dtypes(include=['object', 'category'])
        
        suggestions = "🔍 추가 분석 제안:\n\n"
        
        # 기본 분석
        suggestions += "📊 기본 분석:\n"
        suggestions += "• 히스토그램: 각 변수의 분포 확인\n"
        suggestions += "• 박스플롯: 이상값 및 분포 비교\n"
        suggestions += "• 상관행렬: 변수간 선형 관계\n\n"
        
        # 고급 분석
        if len(numeric_data.columns) >= 2:
            suggestions += "🔬 고급 분석:\n"
            suggestions += "• 회귀분석: 예측 모델 구축\n"
            suggestions += "• 주성분분석: 차원 축소\n"
            suggestions += "• 클러스터링: 유사한 그룹 찾기\n\n"
        
        # 실험계획법 분석
        if len(categorical_data.columns) >= 1:
            suggestions += "🧪 실험계획법:\n"
            suggestions += "• 분산분석(ANOVA): 그룹간 차이 검정\n"
            suggestions += "• 다중비교: 어떤 그룹이 다른지 확인\n"
            suggestions += "• 반응표면분석: 최적 조건 탐색\n\n"
        
        # 시각화 제안
        suggestions += "📈 추천 시각화:\n"
        suggestions += "• 주효과도: 각 요인의 개별 효과\n"
        suggestions += "• 상호작용도: 요인간 상호작용 효과\n"
        suggestions += "• 잔차분석: 모델 적합성 확인\n"
        
        self.analysis_suggestions.setText(suggestions)
    
    def add_analysis_result(self, analysis_type, result):
        """고급 분석 결과 추가"""
        # 기존 placeholder 제거
        if hasattr(self, 'advanced_placeholder'):
            self.advanced_placeholder.setVisible(False)
        
        # 새 분석 결과 위젯 생성
        result_widget = self.create_analysis_result_widget(analysis_type, result)
        self.advanced_layout.addWidget(result_widget)
    
    def create_analysis_result_widget(self, analysis_type, result):
        """분석 결과 위젯 생성"""
        group_box = QGroupBox(f"📊 {analysis_type} 분석 결과")
        layout = QVBoxLayout(group_box)
        
        # 헤더 (제목 + 버튼)
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        # 상세 보기 버튼
        detail_btn = QPushButton("🔍 상세 보기")
        detail_btn.setMaximumWidth(100)
        detail_btn.clicked.connect(lambda: self.show_analysis_detail(analysis_type, result))
        header_layout.addWidget(detail_btn)
        
        layout.addLayout(header_layout)
        
        # 결과 텍스트
        summary_text = QTextEdit()
        summary_text.setMaximumHeight(180)
        summary_text.setReadOnly(True)
        summary_text.setText(self._format_result_summary(analysis_type, result))
        layout.addWidget(summary_text)

        # 표 형태로 보여줄 수 있는 결과 (예: ANOVA 테이블)
        anova_df = None
        if isinstance(result, dict):
            anova_df = result.get("results", {}).get("anova")
        if anova_df is not None:
            layout.addWidget(self._create_table_widget(anova_df))
        
        return group_box

    def _format_result_summary(self, analysis_type, result):
        """결과 요약을 보기 좋게 문자열로 구성"""
        if not isinstance(result, dict):
            return str(result)

        lines = []
        description = result.get("description")
        timestamp = result.get("timestamp")
        if description:
            lines.append(f"설명: {description}")
        if timestamp:
            lines.append(f"시각: {timestamp}")

        details = result.get("results", {})

        if analysis_type == "DOE ANOVA":
            lines.append(f"반응 변수: {details.get('response', 'N/A')}")
            factors = details.get("factors", [])
            lines.append(f"요인: {', '.join(factors) if factors else 'N/A'}")
            if "r_squared" in details:
                lines.append(f"R²: {details.get('r_squared'):.3f}")
            if "adj_r_squared" in details:
                lines.append(f"Adj. R²: {details.get('adj_r_squared'):.3f}")
            if "n_obs" in details:
                lines.append(f"관측치: {details.get('n_obs')}")
        elif analysis_type in ("ANOVA", "상관분석", "회귀분석", "기초 통계"):
            # 기본 필드 표시
            for key in ("independent_var", "dependent_var", "variable_count", "observation_count"):
                if key in details:
                    lines.append(f"{key}: {details[key]}")

        # fallback: 다른 키도 간략히 추가 (원본 데이터 제외)
        for key, value in result.items():
            if key in ("data", "results"):
                continue
            if key in ("description", "timestamp"):
                continue
            lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def _create_table_widget(self, df):
        """pandas DataFrame을 읽기 좋은 테이블 위젯으로 변환"""
        # ANOVA 테이블인 경우 Mean Sq와 F 기각치(α=0.05)를 추가해 표시
        table_df = df.copy()
        try:
            if {"sum_sq", "df"}.issubset(table_df.columns):
                table_df["mean_sq"] = table_df["sum_sq"] / table_df["df"]

                # F 기각치 계산 (Residual df 필요)
                if "Residual" in table_df.index:
                    import math
                    try:
                        from scipy.stats import f as f_dist
                        resid_df = table_df.loc["Residual", "df"]
                        if resid_df and not math.isnan(resid_df):
                            f_crit = []
                            for idx, row in table_df.iterrows():
                                if idx == "Residual":
                                    f_crit.append(float("nan"))
                                else:
                                    num_df = row["df"]
                                    if num_df and not math.isnan(num_df):
                                        f_val = f_dist.ppf(0.95, num_df, resid_df)
                                        f_crit.append(f_val)
                                    else:
                                        f_crit.append(float("nan"))
                            table_df["F_crit(0.05)"] = f_crit
                    except Exception:
                        # scipy 미설치/계산 실패 시 무시
                        pass
        except Exception:
            table_df = df

        table = QTableWidget()
        table.setRowCount(table_df.shape[0])
        table.setColumnCount(table_df.shape[1] + 1)  # index 포함

        headers = ["항목"] + [str(col) for col in table_df.columns]
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalHeaderLabels([str(idx) for idx in table_df.index])

        for i, (idx, row) in enumerate(table_df.iterrows()):
            table.setItem(i, 0, QTableWidgetItem(str(idx)))
            for j, col in enumerate(table_df.columns, start=1):
                table.setItem(i, j, QTableWidgetItem(self._value_to_str(row[col])))

        table.resizeColumnsToContents()
        return table

    @staticmethod
    def _value_to_str(value):
        """숫자를 짧게 표시"""
        try:
            if pd.isna(value):
                return "NaN"
        except Exception:
            pass
        if isinstance(value, float):
            return f"{value:.4g}"
        return str(value)

    def display_results(self, analysis_type, result):
        """
        Main window가 호출하는 결과 표시 진입점.
        새로운 분석 결과를 내부 히스토리에 기록하고 화면에 추가한다.
        """
        if result is None:
            return

        # 결과 히스토리에 누적
        if analysis_type not in self.analysis_results:
            self.analysis_results[analysis_type] = []
        self.analysis_results[analysis_type].append(result)

        # 상태 라벨 업데이트
        status = "완료"
        if isinstance(result, dict):
            status = result.get("status", status)
        self.analysis_status_label.setText(f"{analysis_type} - {status}")
        self.analysis_status_label.setStyleSheet("font-size: 12px; color: green; padding: 10px;")

        # 실제 화면 반영
        self.add_analysis_result(analysis_type, result)
    
    def show_analysis_detail(self, analysis_type, result):
        """분석 결과 상세 보기 다이얼로그 표시"""
        try:
            from views.analysis_detail_dialog import AnalysisDetailDialog
            
            dialog = AnalysisDetailDialog(analysis_type, result, self)
            dialog.exec()
            
        except ImportError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "오류", f"상세 보기 모듈을 불러올 수 없습니다:\n{str(e)}")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "오류", f"상세 보기 중 오류가 발생했습니다:\n{str(e)}")
    
    def clear_results(self):
        """결과 초기화"""
        self.current_data = None
        self.analysis_results.clear()
        
        # UI 초기화
        self.data_summary_label.setText("데이터를 불러오면 요약 정보가 표시됩니다")
        self.analysis_status_label.setText("분석 대기 중")
        self.analysis_status_label.setStyleSheet("font-size: 12px; color: orange; padding: 10px;")
        
        self.stats_table.clear()
        self.distribution_info.clear()
        self.normality_results.clear()
        self.auto_interpretation.clear()
        self.recommendations.clear()
        self.analysis_suggestions.clear()
        
        # 고급 분석 결과 초기화
        for i in reversed(range(self.advanced_layout.count())):
            child = self.advanced_layout.itemAt(i).widget()
            if child and child != self.advanced_placeholder:
                child.setParent(None)
        
        if hasattr(self, 'advanced_placeholder'):
            self.advanced_placeholder.setVisible(True) 
