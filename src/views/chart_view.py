"""
차트 뷰 클래스
matplotlib을 사용한 차트 표시 위젯
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns
import pandas as pd
import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QLabel, QSplitter, QScrollArea,
    QGroupBox, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal

from utils.font_manager import get_font_manager


class ChartCanvas(FigureCanvas):
    """matplotlib 차트 캔버스"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.figure)
        self.setParent(parent)
        
        # 한글 폰트 설정 (폰트 매니저 사용)
        font_manager = get_font_manager()
        font_manager.setup_default_font()
        
        # 기본 스타일 설정
        self.figure.patch.set_facecolor('white')
        
    def clear_plot(self):
        """플롯 지우기"""
        self.figure.clear()
        self.draw()


class ChartView(QWidget):
    """차트 뷰 클래스"""
    
    # 시그널 정의
    chart_updated = Signal()
    
    def __init__(self):
        super().__init__()
        
        self.data = None
        self.current_axes = []
        self._recreating_chart = False  # 차트 재생성 중 플래그
        self.chart_controller = None  # ChartController 참조 (나중에 설정)
        # 차트 유형 정의 (활성/비활성 판단에 사용)
        self.chart_types = [
            "히스토그램",
            "박스플롯",
            "산점도",
            "선 그래프",
            "막대 그래프",
            "상관행렬",
            "주효과도",
            "상호작용도",
        ]
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QHBoxLayout(self)
        
        # 좌측 컨트롤 패널
        self.setup_control_panel()
        
        # 우측 차트 영역
        self.setup_chart_area()
        
        # 스플리터로 분할
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.control_panel)
        splitter.addWidget(self.chart_area)
        splitter.setSizes([250, 750])
        
        layout.addWidget(splitter)
    
    def setup_control_panel(self):
        """컨트롤 패널 설정"""
        self.control_panel = QWidget()
        self.control_panel.setMaximumWidth(300)
        self.control_panel.setMinimumWidth(200)
        
        layout = QVBoxLayout(self.control_panel)
        
        # 차트 유형 선택
        chart_group = QGroupBox("차트 유형")
        chart_layout = QVBoxLayout(chart_group)
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(self.chart_types)
        chart_layout.addWidget(self.chart_type_combo)
        
        layout.addWidget(chart_group)
        
        # 변수 선택
        var_group = QGroupBox("변수 선택")
        var_layout = QVBoxLayout(var_group)
        
        # X축 변수
        var_layout.addWidget(QLabel("X축:"))
        self.x_var_combo = QComboBox()
        var_layout.addWidget(self.x_var_combo)
        
        # Y축 변수
        var_layout.addWidget(QLabel("Y축:"))
        self.y_var_combo = QComboBox()
        var_layout.addWidget(self.y_var_combo)
        
        # 그룹 변수 (선택적)
        var_layout.addWidget(QLabel("그룹:"))
        self.group_var_combo = QComboBox()
        self.group_var_combo.addItem("없음")
        var_layout.addWidget(self.group_var_combo)
        
        layout.addWidget(var_group)
        
        # 차트 옵션
        option_group = QGroupBox("차트 옵션")
        option_layout = QVBoxLayout(option_group)
        
        # 그리드 표시
        self.show_grid_check = QCheckBox("그리드 표시")
        self.show_grid_check.setChecked(True)
        option_layout.addWidget(self.show_grid_check)
        
        # 범례 표시
        self.show_legend_check = QCheckBox("범례 표시")
        self.show_legend_check.setChecked(True)
        option_layout.addWidget(self.show_legend_check)
        
        # 빈 개수 (히스토그램용)
        option_layout.addWidget(QLabel("빈 개수:"))
        self.bins_spin = QSpinBox()
        self.bins_spin.setRange(5, 100)
        self.bins_spin.setValue(20)
        option_layout.addWidget(self.bins_spin)
        
        layout.addWidget(option_group)
        
        # 차트 생성 버튼
        self.create_chart_btn = QPushButton("차트 생성")
        self.create_chart_btn.clicked.connect(self.create_chart)
        layout.addWidget(self.create_chart_btn)
        
        # 차트 지우기 버튼
        self.clear_chart_btn = QPushButton("차트 지우기")
        self.clear_chart_btn.clicked.connect(self.clear_charts)
        layout.addWidget(self.clear_chart_btn)
        
        layout.addStretch()
    
    def setup_chart_area(self):
        """차트 영역 설정"""
        self.chart_area = QWidget()
        layout = QVBoxLayout(self.chart_area)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 차트 캔버스
        self.canvas = ChartCanvas(self.chart_area, width=8, height=6)
        scroll_area.setWidget(self.canvas)
        
        layout.addWidget(scroll_area)
    
    def setup_connections(self):
        """시그널 연결"""
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        self.show_grid_check.toggled.connect(self.update_chart_options)
        self.show_legend_check.toggled.connect(self.update_chart_options)
        
        # 변수 선택 변경 시그널 연결 (선택사항)
        self.x_var_combo.currentTextChanged.connect(self.on_variable_changed)
        self.y_var_combo.currentTextChanged.connect(self.on_variable_changed)
        self.group_var_combo.currentTextChanged.connect(self.on_variable_changed)
    
    def on_variable_changed(self):
        """변수 선택 변경 이벤트"""
        # 변수 선택이 변경되었을 때의 처리 (필요시 구현)
        pass
    
    def set_data(self, data):
        """데이터 설정"""
        self.data = data
        self.update_variable_lists()
        self.update_ui_state()
        self.update_chart_type_availability()
    
    def update_variable_lists(self):
        """변수 목록 업데이트"""
        # 기존 항목 제거
        self.x_var_combo.clear()
        self.y_var_combo.clear()
        self.group_var_combo.clear()
        self.group_var_combo.addItem("없음")
        
        if self.data is not None and not self.data.empty:
            columns = list(self.data.columns)
            
            # 모든 열 추가
            self.x_var_combo.addItems(columns)
            self.y_var_combo.addItems(columns)
            self.group_var_combo.addItems(columns)
            
            # 기본 선택 (첫 번째와 두 번째 열)
            if len(columns) >= 2:
                self.x_var_combo.setCurrentIndex(0)
                self.y_var_combo.setCurrentIndex(1)
            elif len(columns) >= 1:
                self.x_var_combo.setCurrentIndex(0)
    
    def update_ui_state(self):
        """UI 상태 업데이트"""
        has_data = self.data is not None and not self.data.empty
        
        self.create_chart_btn.setEnabled(has_data)
        
        # 변수 선택 콤보박스 활성화/비활성화
        self.x_var_combo.setEnabled(has_data)
        self.y_var_combo.setEnabled(has_data)
        self.group_var_combo.setEnabled(has_data)
        
        # 차트 유형에 따른 UI 업데이트
        if has_data:
            self.on_chart_type_changed(self.chart_type_combo.currentText())
        self.update_chart_type_availability()
    
    def on_chart_type_changed(self, chart_type):
        """차트 유형 변경 이벤트"""
        # 차트 유형에 따라 UI 요소 활성화/비활성화
        if chart_type in ["히스토그램"]:
            self.x_var_combo.setEnabled(True)
            self.y_var_combo.setEnabled(False)
            self.group_var_combo.setEnabled(False)
            self.bins_spin.setEnabled(True)
        elif chart_type in ["박스플롯"]:
            self.x_var_combo.setEnabled(True)
            self.y_var_combo.setEnabled(True)
            self.group_var_combo.setEnabled(True)
            self.bins_spin.setEnabled(False)

    def update_chart_type_availability(self):
        """데이터 유형에 따라 선택 가능한 차트 유형을 활성/비활성"""
        model = self.chart_type_combo.model()
        if model is None:
            return

        has_data = self.data is not None and not self.data.empty
        if not has_data:
            # 데이터 없으면 모두 비활성
            for i in range(len(self.chart_types)):
                item = model.item(i)
                if item:
                    item.setEnabled(False)
            return

        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.data.select_dtypes(exclude=[np.number]).columns.tolist()

        has_numeric = len(numeric_cols) > 0
        has_numeric2 = len(numeric_cols) >= 2
        has_numeric3 = len(numeric_cols) >= 3
        has_cat = len(categorical_cols) > 0
        has_cat2 = len(categorical_cols) >= 2

        # 활성 조건 정의
        for i, t in enumerate(self.chart_types):
            enabled = True
            if t == "히스토그램":
                enabled = has_numeric
            elif t == "박스플롯":
                enabled = has_numeric
            elif t == "산점도":
                enabled = has_numeric2
            elif t == "선 그래프":
                enabled = has_numeric  # y가 숫자여야 하므로
            elif t == "막대 그래프":
                enabled = has_numeric  # y가 숫자여야 하므로
            elif t == "상관행렬":
                enabled = has_numeric2
            elif t == "주효과도":
                # 범주형 요인이 있거나(1개 이상), 범주형이 없고 숫자형이 2개 이상일 때만 활성
                enabled = has_numeric and (has_cat or has_numeric2)
            elif t == "상호작용도":
                # 범주형 요인 2개 이상이거나, 범주형이 없고 숫자형이 3개 이상일 때 활성
                enabled = has_numeric and (has_cat2 or (not has_cat and has_numeric3))

            item = model.item(i)
            if item:
                item.setEnabled(enabled)

        # 현재 선택이 비활성화되었다면 첫 번째 활성 항목으로 이동
        current_idx = self.chart_type_combo.currentIndex()
        if current_idx >= 0:
            item = model.item(current_idx)
            if item and not item.isEnabled():
                for i in range(len(self.chart_types)):
                    it = model.item(i)
                    if it and it.isEnabled():
                        self.chart_type_combo.setCurrentIndex(i)
                        break
        elif chart_type in ["산점도", "선 그래프"]:
            self.x_var_combo.setEnabled(True)
            self.y_var_combo.setEnabled(True)
            self.group_var_combo.setEnabled(True)
            self.bins_spin.setEnabled(False)
        elif chart_type in ["막대 그래프"]:
            self.x_var_combo.setEnabled(True)
            self.y_var_combo.setEnabled(True)
            self.group_var_combo.setEnabled(True)
            self.bins_spin.setEnabled(False)
        elif chart_type in ["상관행렬"]:
            self.x_var_combo.setEnabled(False)
            self.y_var_combo.setEnabled(False)
            self.group_var_combo.setEnabled(False)
            self.bins_spin.setEnabled(False)
        else:
            self.x_var_combo.setEnabled(True)
            self.y_var_combo.setEnabled(True)
            self.group_var_combo.setEnabled(True)
            self.bins_spin.setEnabled(False)
    
    def update_chart_options(self):
        """차트 옵션 업데이트 (시그널 발생 없이)"""
        # 현재 차트가 있으면 옵션 적용
        if hasattr(self, 'current_axes') and self.current_axes:
            for ax in self.current_axes:
                ax.grid(self.show_grid_check.isChecked())
                if self.show_legend_check.isChecked():
                    ax.legend()
                else:
                    legend = ax.get_legend()
                    if legend:
                        legend.remove()
            # 캔버스만 업데이트하고 chart_updated 시그널은 발생시키지 않음
            self.canvas.draw()
    
    def create_chart(self):
        """선택된 차트 유형에 따라 차트 생성"""
        if self.data is None or self.data.empty:
            return
        
        chart_type = self.chart_type_combo.currentText()
        x_var = self.x_var_combo.currentText()
        y_var = self.y_var_combo.currentText()
        group_var = self.group_var_combo.currentText()
        
        if group_var == "없음":
            group_var = None
        
        # 차트 생성 전 캔버스 지우기
        self.canvas.clear_plot()
        
        try:
            # 차트 유형별 생성
            if chart_type == "히스토그램":
                if x_var:
                    self.create_histogram(x_var)
            elif chart_type == "박스플롯":
                if x_var:
                    self.create_boxplot(x_var, y_var, group_var)
            elif chart_type == "산점도":
                if x_var and y_var:
                    self.create_scatter(x_var, y_var, group_var)
            elif chart_type == "선 그래프":
                if x_var and y_var:
                    self.create_line_plot(x_var, y_var, group_var)
            elif chart_type == "막대 그래프":
                if x_var and y_var:
                    self.create_bar_plot(x_var, y_var, group_var)
            elif chart_type == "상관행렬":
                self.create_correlation_matrix()
            elif chart_type == "주효과도":
                self.create_main_effects_plot()
            elif chart_type == "상호작용도":
                self.create_interaction_plot()

            # 차트 옵션 적용
            self.apply_chart_options()

            # 즉시 그리기 (리사이즈 없이 바로 표시)
            self.canvas.draw()
            
            # 현재 차트 정보 저장
            import datetime
            self.current_chart_info = {
                # 새 키(읽기 쉬운 이름)
                'type': chart_type,
                'x_var': x_var,
                'y_var': y_var,
                'group_var': group_var,
                # 호환 키(재생성 함수와 일관)
                'chart_type': chart_type,
                'x_variable': x_var,
                'y_variable': y_var,
                'group_variable': group_var,
                'timestamp': datetime.datetime.now().strftime("%H:%M:%S"),
                'description': f"{chart_type} - {x_var}" + (f" vs {y_var}" if y_var else ""),
                'options': {
                    'show_grid': self.show_grid_check.isChecked(),
                    'show_legend': self.show_legend_check.isChecked(),
                    'bins': self.bins_spin.value()
                }
            }
            
            # 차트 업데이트 시그널 발생
            if not self._recreating_chart:
                self.chart_updated.emit()
            
        except Exception as e:
            print(f"차트 생성 중 오류: {str(e)}")
            # 오류 발생 시 빈 플롯 표시
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"차트 생성 오류:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()
    
    def create_histogram(self, x_var):
        """히스토그램 생성"""
        ax = self.canvas.figure.add_subplot(111)
        
        data = self.data[x_var].dropna()
        bins = self.bins_spin.value()
        
        ax.hist(data, bins=bins, alpha=0.7, edgecolor='black')
        ax.set_xlabel(x_var)
        ax.set_ylabel('빈도')
        ax.set_title(f'{x_var}의 히스토그램')
        
        self.current_axes = [ax]
    
    def create_boxplot(self, x_var, y_var, group_var=None):
        """박스플롯 생성"""
        ax = self.canvas.figure.add_subplot(111)
        
        if group_var:
            # 그룹별 박스플롯
            groups = self.data[group_var].unique()
            data_list = []
            labels = []
            for group in groups:
                group_data = self.data[self.data[group_var] == group][y_var].dropna()
                data_list.append(group_data)
                labels.append(f"{group}")
            
            ax.boxplot(data_list, labels=labels)
            ax.set_xlabel(group_var)
        else:
            # 단일 박스플롯
            data = self.data[y_var].dropna()
            ax.boxplot([data], labels=[y_var])
        
        ax.set_ylabel(y_var)
        ax.set_title(f'{y_var}의 박스플롯')
        
        self.current_axes = [ax]
    
    def create_scatter(self, x_var, y_var, group_var=None):
        """산점도 생성"""
        ax = self.canvas.figure.add_subplot(111)
        
        if group_var:
            # 그룹별 산점도
            groups = self.data[group_var].unique()
            for group in groups:
                group_data = self.data[self.data[group_var] == group]
                ax.scatter(group_data[x_var], group_data[y_var], 
                          label=f"{group}", alpha=0.7)
        else:
            ax.scatter(self.data[x_var], self.data[y_var], alpha=0.7)
        
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f'{x_var} vs {y_var} 산점도')
        
        self.current_axes = [ax]
    
    def create_line_plot(self, x_var, y_var, group_var=None):
        """선 그래프 생성"""
        ax = self.canvas.figure.add_subplot(111)
        
        if group_var:
            # 그룹별 선 그래프
            groups = self.data[group_var].unique()
            for group in groups:
                group_data = self.data[self.data[group_var] == group]
                ax.plot(group_data[x_var], group_data[y_var], 
                       label=f"{group}", marker='o')
        else:
            ax.plot(self.data[x_var], self.data[y_var], marker='o')
        
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f'{x_var} vs {y_var} 선 그래프')
        
        self.current_axes = [ax]
    
    def create_bar_plot(self, x_var, y_var, group_var=None):
        """막대 그래프 생성"""
        ax = self.canvas.figure.add_subplot(111)
        
        if group_var:
            # 그룹별 막대 그래프
            pivot_data = self.data.pivot_table(values=y_var, index=x_var, 
                                             columns=group_var, aggfunc='mean')
            pivot_data.plot(kind='bar', ax=ax)
        else:
            # 단순 막대 그래프
            if pd.api.types.is_numeric_dtype(self.data[x_var]):
                # 숫자형 데이터는 구간별로 그룹화
                grouped = self.data.groupby(pd.cut(self.data[x_var], bins=10))[y_var].mean()
                grouped.plot(kind='bar', ax=ax)
            else:
                # 범주형 데이터
                grouped = self.data.groupby(x_var)[y_var].mean()
                grouped.plot(kind='bar', ax=ax)
        
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f'{x_var}별 {y_var} 막대 그래프')
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        self.current_axes = [ax]
    
    def create_correlation_matrix(self):
        """상관행렬 히트맵 생성"""
        ax = self.canvas.figure.add_subplot(111)
        
        # 숫자형 열만 선택
        numeric_data = self.data.select_dtypes(include=[np.number])
        
        if numeric_data.empty:
            ax.text(0.5, 0.5, '숫자형 데이터가 없습니다', 
                   ha='center', va='center', transform=ax.transAxes)
            return
        
        # 상관계수 계산
        corr_matrix = numeric_data.corr()
        
        # 히트맵 생성
        im = ax.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        
        # 축 레이블 설정
        ax.set_xticks(range(len(corr_matrix.columns)))
        ax.set_yticks(range(len(corr_matrix.columns)))
        ax.set_xticklabels(corr_matrix.columns, rotation=45)
        ax.set_yticklabels(corr_matrix.columns)
        
        # 상관계수 값 표시
        for i in range(len(corr_matrix.columns)):
            for j in range(len(corr_matrix.columns)):
                text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                             ha="center", va="center", color="black")
        
        ax.set_title('상관행렬')
        
        # 컬러바 추가
        self.canvas.figure.colorbar(im, ax=ax)
        
        self.current_axes = [ax]
    
    def create_main_effects_plot(self):
        """주효과도 생성
        
        주효과도는 각 요인이 반응변수에 미치는 개별적인 영향을 시각화합니다.
        실험계획법에서 어떤 요인이 가장 중요한지 파악할 때 사용됩니다.
        
        사용 시기:
        - 요인설계 실험 후 각 요인의 영향력 비교
        - 중요한 요인 식별 및 우선순위 결정
        - 최적 조건 탐색의 첫 단계
        """
        # 기존 플롯 초기화
        self.canvas.figure.clear()
        
        # 숫자형 열과 범주형 열 구분 (범주형이 없으면 숫자형을 범주로 처리)
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns.tolist()
        if not categorical_cols and numeric_cols:
            categorical_cols = numeric_cols.copy()

        if len(numeric_cols) < 1 or len(categorical_cols) < 1:
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, '주효과도 생성을 위해서는\n숫자형 반응변수와\n범주형 요인변수가 필요합니다', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            self.current_axes = [ax]
            return
        
        # 반응변수 (첫 번째 숫자형 열)
        response_var = numeric_cols[0]
        
        # 요인변수들 (범주형 열들) - 반응변수는 제외
        factor_vars = [c for c in categorical_cols if c != response_var][:4]  # 최대 4개 요인만 표시
        
        if len(factor_vars) == 0:
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, '범주형 요인변수가 없습니다', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            self.current_axes = [ax]
            return
        
        # 서브플롯 배치 계산
        n_factors = len(factor_vars)
        if n_factors == 1:
            rows, cols = 1, 1
        elif n_factors == 2:
            rows, cols = 1, 2
        elif n_factors <= 4:
            rows, cols = 2, 2
        else:
            rows, cols = 2, 3
        
        axes = []
        for i, factor in enumerate(factor_vars):
            ax = self.canvas.figure.add_subplot(rows, cols, i + 1)
            
            # 숫자형 요인도 범주로 변환하여 그룹화
            factor_series = self.data[factor].astype('category')
            means = self.data.groupby(factor_series)[response_var].mean()
            stds = self.data.groupby(factor_series)[response_var].std()
            
            # 주효과도 그리기
            x_pos = range(len(means))
            ax.plot(x_pos, means.values, 'o-', linewidth=2, markersize=8)
            ax.errorbar(x_pos, means.values, yerr=stds.values, 
                       capsize=5, capthick=2, alpha=0.7)
            
            # 축 설정
            ax.set_xticks(x_pos)
            ax.set_xticklabels(means.index, rotation=45)
            ax.set_xlabel(f'{factor}')
            ax.set_ylabel(f'{response_var} 평균')
            ax.set_title(f'{factor}의 주효과', fontsize=11, fontweight='bold', pad=6)
            ax.grid(True, alpha=0.3)
            
            axes.append(ax)
        
        # 전체 제목
        self.canvas.figure.suptitle(f'{response_var}에 대한 주효과도', fontsize=14, fontweight='bold', y=0.98)
        
        # 레이아웃 조정 (제목과 플롯 사이 여백 확보)
        self.canvas.figure.tight_layout(pad=2.0, rect=[0, 0, 1, 0.93])
        self.canvas.draw()
        
        self.current_axes = axes
    
    def create_interaction_plot(self):
        """상호작용도 생성
        
        상호작용도는 두 요인이 함께 반응변수에 미치는 영향을 시각화합니다.
        한 요인의 효과가 다른 요인의 수준에 따라 달라지는지 확인할 때 사용됩니다.
        
        사용 시기:
        - 요인간 상호작용 효과 확인
        - 복잡한 요인 관계 이해
        - 최적 조건 조합 탐색
        - ANOVA에서 상호작용이 유의한 경우
        """
        # 기존 플롯 초기화
        self.canvas.figure.clear()
        
        # 숫자형 열과 범주형 열 구분 (범주형이 없으면 숫자형을 범주로 처리)
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns.tolist()
        if not categorical_cols and numeric_cols:
            categorical_cols = numeric_cols.copy()
        
        if len(numeric_cols) < 1 or len(categorical_cols) < 2:
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, '상호작용도 생성을 위해서는\n숫자형 반응변수와\n최소 2개의 범주형 요인변수가 필요합니다', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            self.current_axes = [ax]
            return
        
        # 반응변수 (첫 번째 숫자형 열)
        response_var = numeric_cols[0]

        # 요인 리스트에서 반응변수를 제외
        categorical_filtered = [c for c in categorical_cols if c != response_var]
        if len(categorical_filtered) < 2:
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, '상호작용도 생성을 위해서는\n반응변수를 제외한 요인 2개가 필요합니다', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            self.current_axes = [ax]
            return

        # 첫 번째와 두 번째 요인
        factor1 = categorical_filtered[0]
        factor2 = categorical_filtered[1]
        
        # 상호작용도 생성
        ax = self.canvas.figure.add_subplot(111)
        
        # factor2의 각 수준별로 선 그리기
        factor2_levels = sorted(self.data[factor2].astype('category').unique())
        colors = plt.cm.Set1(np.linspace(0, 1, len(factor2_levels)))
        
        for i, level2 in enumerate(factor2_levels):
            # factor2가 특정 수준일 때의 데이터
            subset = self.data[self.data[factor2] == level2]
            
            # factor1 수준별 평균 계산
            means = subset.groupby(subset[factor1].astype('category'))[response_var].mean()
            stds = subset.groupby(subset[factor1].astype('category'))[response_var].std()
            
            if len(means) > 0:
                x_pos = range(len(means))
                ax.plot(x_pos, means.values, 'o-', 
                       label=f'{factor2}={level2}', 
                       color=colors[i], linewidth=2, markersize=8)
                ax.errorbar(x_pos, means.values, yerr=stds.values, 
                           color=colors[i], alpha=0.5, capsize=3)
        
        # 축 설정
        factor1_levels = sorted(self.data[factor1].astype('category').unique())
        ax.set_xticks(range(len(factor1_levels)))
        ax.set_xticklabels(factor1_levels)
        ax.set_xlabel(factor1)
        ax.set_ylabel(f'{response_var} 평균')
        ax.set_title(f'{factor1} × {factor2} 상호작용도', fontsize=12, fontweight='bold', pad=6)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 상호작용 해석 도움말 추가
        interaction_strength = self._calculate_interaction_strength(factor1, factor2, response_var)
        ax.text(0.02, 0.98, f'상호작용 강도: {interaction_strength}', 
               transform=ax.transAxes, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        self.canvas.figure.tight_layout()
        self.canvas.draw()
        
        self.current_axes = [ax]
    
    def _calculate_interaction_strength(self, factor1, factor2, response_var):
        """상호작용 강도 계산 (간단한 휴리스틱)"""
        try:
            # 각 조합별 평균 계산
            interaction_means = self.data.groupby([factor1, factor2])[response_var].mean().unstack()
            
            # 선들의 기울기 차이로 상호작용 강도 추정
            slopes = []
            for col in interaction_means.columns:
                if len(interaction_means[col].dropna()) >= 2:
                    y_values = interaction_means[col].dropna().values
                    x_values = range(len(y_values))
                    if len(x_values) >= 2:
                        slope = (y_values[-1] - y_values[0]) / (x_values[-1] - x_values[0])
                        slopes.append(slope)
            
            if len(slopes) >= 2:
                slope_variance = np.var(slopes)
                if slope_variance < 1:
                    return "약함"
                elif slope_variance < 5:
                    return "보통"
                else:
                    return "강함"
            else:
                return "계산불가"
                
        except Exception:
            return "계산불가"
    
    def apply_chart_options(self):
        """차트 옵션 적용"""
        if hasattr(self, 'current_axes') and self.current_axes:
            for ax in self.current_axes:
                # 그리드 설정
                ax.grid(self.show_grid_check.isChecked())
                
                # 범례 설정
                if self.show_legend_check.isChecked() and ax.get_legend_handles_labels()[0]:
                    ax.legend()
        
        # 레이아웃 조정
        self.canvas.figure.tight_layout()
    
    def clear_charts(self):
        """모든 차트 지우기"""
        self.canvas.clear_plot()
        self.current_axes = []

    def set_chart_controller(self, chart_controller):
        """차트 컨트롤러 설정"""
        self.chart_controller = chart_controller
    
    def get_current_chart_info(self):
        """현재 차트 정보 반환"""
        if not hasattr(self, 'current_chart_info'):
            return None
        return getattr(self, 'current_chart_info', None)
    
    def display_chart(self, chart_info):
        """차트 정보를 받아서 차트를 표시"""
        if not chart_info or self.data is None or self.data.empty:
            return
        try:
            self._recreating_chart = True
            # 호환 키 처리
            chart_type = chart_info.get('type') or chart_info.get('chart_type')
            x_var = chart_info.get('x_var') or chart_info.get('x_variable')
            y_var = chart_info.get('y_var') or chart_info.get('y_variable')
            group_var = chart_info.get('group_var') or chart_info.get('group_variable')
            options = chart_info.get('options', {})

            if chart_type:
                idx = self.chart_type_combo.findText(chart_type)
                if idx >= 0:
                    self.chart_type_combo.setCurrentIndex(idx)

            def set_combo(combo, value):
                if value:
                    j = combo.findText(str(value))
                    if j >= 0:
                        combo.setCurrentIndex(j)

            set_combo(self.x_var_combo, x_var)
            set_combo(self.y_var_combo, y_var)
            if group_var:
                set_combo(self.group_var_combo, group_var)
            else:
                self.group_var_combo.setCurrentIndex(0)

            # 옵션 반영
            if 'show_grid' in options:
                self.show_grid_check.setChecked(bool(options.get('show_grid')))
            if 'show_legend' in options:
                self.show_legend_check.setChecked(bool(options.get('show_legend')))
            if 'bins' in options:
                try:
                    self.bins_spin.setValue(int(options.get('bins')))
                except Exception:
                    pass

            # 실제 차트 생성
            self._create_chart_without_signal()
        finally:
            self._recreating_chart = False

    def display_figure(self, figure):
        """matplotlib Figure를 캔버스에 표시"""
        # 기존 차트 지우기
        self.canvas.figure.clear()
        
        # 새 Figure의 내용을 복사
        for i, ax in enumerate(figure.axes):
            new_ax = self.canvas.figure.add_subplot(len(figure.axes), 1, i+1)
            
            # 데이터 복사
            for line in ax.lines:
                new_ax.plot(line.get_xdata(), line.get_ydata(), 
                           color=line.get_color(), linestyle=line.get_linestyle(),
                           marker=line.get_marker(), label=line.get_label())
            
            for collection in ax.collections:
                if hasattr(collection, 'get_offsets'):  # scatter plot
                    offsets = collection.get_offsets()
                    if len(offsets) > 0:
                        new_ax.scatter(offsets[:, 0], offsets[:, 1], 
                                     c=collection.get_facecolors(),
                                     alpha=collection.get_alpha())
            
            for patch in ax.patches:
                new_ax.add_patch(patch)
            
            for image in ax.images:
                new_ax.imshow(image.get_array(), cmap=image.get_cmap(), 
                            extent=image.get_extent())
            
            # 축 정보 복사
            new_ax.set_xlabel(ax.get_xlabel())
            new_ax.set_ylabel(ax.get_ylabel())
            new_ax.set_title(ax.get_title())
            new_ax.set_xlim(ax.get_xlim())
            new_ax.set_ylim(ax.get_ylim())
            
            # 범례 처리
            if ax.get_legend():
                new_ax.legend()
            
            # 그리드 처리
            if ax.get_gridspec() is not None:
                new_ax.grid(True, alpha=0.3)
        
        # 캔버스 업데이트
        self.canvas.draw()
        
        # 현재 축 업데이트
        self.current_axes = self.canvas.figure.axes
        self.chart_updated.emit()
    
    def recreate_chart_from_info(self, chart_info):
        """저장된 차트 정보로부터 차트 재생성 (시그널 발생 없이)"""
        if not chart_info or self.data is None:
            return
        
        try:
            # 시그널 일시 차단
            self._recreating_chart = True
            
            # 차트 타입 설정
            chart_type = chart_info.get('chart_type', '') or chart_info.get('type', '')
            if chart_type:
                index = self.chart_type_combo.findText(chart_type)
                if index >= 0:
                    self.chart_type_combo.setCurrentIndex(index)
            
            # 변수 설정
            x_var = chart_info.get('x_variable', '') or chart_info.get('x_var', '')
            y_var = chart_info.get('y_variable', '') or chart_info.get('y_var', '')
            group_var = chart_info.get('group_variable', '') or chart_info.get('group_var', '')
            
            if x_var:
                index = self.x_var_combo.findText(x_var)
                if index >= 0:
                    self.x_var_combo.setCurrentIndex(index)
            
            if y_var:
                index = self.y_var_combo.findText(y_var)
                if index >= 0:
                    self.y_var_combo.setCurrentIndex(index)
            
            if group_var:
                index = self.group_var_combo.findText(group_var)
                if index >= 0:
                    self.group_var_combo.setCurrentIndex(index)
            else:
                self.group_var_combo.setCurrentIndex(0)  # "없음" 선택
            
            # 옵션 설정
            options = chart_info.get('options', {})
            if 'show_grid' in options:
                self.show_grid_check.setChecked(options['show_grid'])
            if 'show_legend' in options:
                self.show_legend_check.setChecked(options['show_legend'])
            if 'bins' in options:
                self.bins_spin.setValue(options['bins'])
            
            # 차트 생성 (시그널 없이)
            self._create_chart_without_signal()
            
        except Exception as e:
            print(f"차트 재생성 중 오류: {str(e)}")
        finally:
            # 시그널 차단 해제
            self._recreating_chart = False
    
    def _create_chart_without_signal(self):
        """시그널 발생 없이 차트 생성"""
        if self.data is None or self.data.empty:
            return
        
        chart_type = self.chart_type_combo.currentText()
        x_var = self.x_var_combo.currentText()
        y_var = self.y_var_combo.currentText()
        group_var = self.group_var_combo.currentText()
        
        if group_var == "없음":
            group_var = None
        
        # 변수 선택 검증
        if not x_var and chart_type not in ["상관행렬", "주효과도", "상호작용도"]:
            return
        
        # 차트 지우기
        self.canvas.figure.clear()
        
        try:
            chart_created = False
            
            if chart_type == "히스토그램":
                self.create_histogram(x_var)
                chart_created = True
            elif chart_type == "박스플롯":
                self.create_boxplot(x_var, y_var, group_var)
                chart_created = True
            elif chart_type == "산점도":
                self.create_scatter(x_var, y_var, group_var)
                chart_created = True
            elif chart_type == "선 그래프":
                self.create_line_plot(x_var, y_var, group_var)
                chart_created = True
            elif chart_type == "막대 그래프":
                self.create_bar_plot(x_var, y_var, group_var)
                chart_created = True
            elif chart_type == "상관행렬":
                self.create_correlation_matrix()
                chart_created = True
            elif chart_type == "주효과도":
                self.create_main_effects_plot()
                chart_created = True
            elif chart_type == "상호작용도":
                self.create_interaction_plot()
                chart_created = True
            
            if chart_created:
                # 차트 옵션 적용
                self.apply_chart_options()
                
                # 캔버스 업데이트 (시그널 없이)
                self.canvas.draw()
            
        except Exception as e:
            print(f"차트 생성 중 오류: {e}") 
