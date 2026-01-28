import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal, Slot

from utils.font_manager import get_font_manager

class ChartController(QObject):
    """
    차트 생성 및 관리를 담당하는 컨트롤러
    """
    # 시그널 정의
    chart_created = Signal(dict)  # 차트 정보
    status_updated = Signal(str)
    error_occurred = Signal(str, str)  # 제목, 메시지

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 한글 폰트 설정
        self.font_manager = get_font_manager()
        self.font_manager.setup_default_font()
        
        # 지원하는 차트 타입
        self.supported_chart_types = {
            "히스토그램": self._create_histogram,
            "박스플롯": self._create_boxplot,
            "산점도": self._create_scatter,
            "선 그래프": self._create_line_plot,
            "막대 그래프": self._create_bar_plot,
            "상관행렬": self._create_correlation_matrix,
            "주효과도": self._create_main_effects_plot,
            "상호작용도": self._create_interaction_plot
        }

    def create_chart(self, chart_type: str, dataframe: pd.DataFrame, 
                    x_var: str = None, y_var: str = None, group_var: str = None,
                    options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        차트를 생성하고 차트 정보를 반환합니다.
        
        Args:
            chart_type: 차트 유형
            dataframe: 데이터프레임
            x_var: X축 변수
            y_var: Y축 변수  
            group_var: 그룹 변수 (선택적)
            options: 차트 옵션 딕셔너리
        """
        if not self._validate_inputs(chart_type, dataframe, x_var, y_var):
            return None

        try:
            self.status_updated.emit(f"{chart_type} 차트를 생성하는 중...")
            
            # 기본 옵션 설정
            if options is None:
                options = {}
            
            default_options = {
                'show_grid': True,
                'show_legend': True,
                'bins': 20,
                'figsize': (10, 6),
                'dpi': 100
            }
            default_options.update(options)
            
            # 차트 생성
            chart_func = self.supported_chart_types[chart_type]
            figure = chart_func(dataframe, x_var, y_var, group_var, default_options)
            
            if figure is None:
                return None
            
            # 차트 정보 생성
            chart_info = {
                'type': chart_type,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'x_variable': x_var,
                'y_variable': y_var,
                'group_variable': group_var if group_var != "없음" else None,
                'options': default_options,
                'figure': figure,
                'description': self._generate_chart_description(chart_type, x_var, y_var, group_var)
            }
            
            self.chart_created.emit(chart_info)
            self.status_updated.emit(f"{chart_type} 차트가 성공적으로 생성되었습니다.")
            
            return chart_info
            
        except Exception as e:
            self.error_occurred.emit("차트 생성 실패", f"차트를 생성하는 중 오류가 발생했습니다:\n{str(e)}")
            return None

    def _validate_inputs(self, chart_type: str, dataframe: pd.DataFrame, 
                        x_var: str, y_var: str) -> bool:
        """입력값 유효성 검증"""
        if chart_type not in self.supported_chart_types:
            self.error_occurred.emit("차트 오류", f"지원하지 않는 차트 유형입니다: {chart_type}")
            return False
        
        if dataframe is None or dataframe.empty:
            self.error_occurred.emit("차트 오류", "차트를 그릴 데이터가 없습니다.")
            return False
        
        # 차트 유형별 변수 요구사항 검증
        if chart_type in ["히스토그램"] and not x_var:
            self.error_occurred.emit("차트 오류", f"{chart_type}에는 X축 변수가 필요합니다.")
            return False
        
        if chart_type in ["산점도", "선 그래프", "막대 그래프"] and (not x_var or not y_var):
            self.error_occurred.emit("차트 오류", f"{chart_type}에는 X축과 Y축 변수가 모두 필요합니다.")
            return False
        
        return True

    def _create_histogram(self, df: pd.DataFrame, x_var: str, y_var: str, 
                         group_var: str, options: Dict[str, Any]) -> plt.Figure:
        """히스토그램 생성"""
        fig, ax = plt.subplots(figsize=options['figsize'], dpi=options['dpi'])
        
        if x_var not in df.columns:
            self.error_occurred.emit("차트 오류", f"변수 '{x_var}'를 찾을 수 없습니다.")
            return None
        
        data = df[x_var].dropna()
        
        if group_var and group_var != "없음" and group_var in df.columns:
            # 그룹별 히스토그램
            groups = df.groupby(group_var)[x_var].apply(lambda x: x.dropna())
            for name, group_data in groups.items():
                ax.hist(group_data, bins=options['bins'], alpha=0.7, label=str(name))
            if options['show_legend']:
                ax.legend()
        else:
            # 단일 히스토그램
            ax.hist(data, bins=options['bins'], alpha=0.7)
        
        ax.set_xlabel(x_var)
        ax.set_ylabel('빈도수')
        ax.set_title(f'{x_var}의 분포')
        
        if options['show_grid']:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def _create_boxplot(self, df: pd.DataFrame, x_var: str, y_var: str, 
                       group_var: str, options: Dict[str, Any]) -> plt.Figure:
        """박스플롯 생성"""
        fig, ax = plt.subplots(figsize=options['figsize'], dpi=options['dpi'])
        
        if y_var and y_var in df.columns:
            # Y축 변수가 있는 경우
            if x_var and x_var in df.columns:
                # X축 변수도 있는 경우 (그룹별 박스플롯)
                sns.boxplot(data=df, x=x_var, y=y_var, ax=ax)
            else:
                # Y축 변수만 있는 경우
                sns.boxplot(data=df, y=y_var, ax=ax)
        else:
            # X축 변수만 있는 경우
            if x_var in df.columns:
                sns.boxplot(data=df, y=x_var, ax=ax)
            else:
                self.error_occurred.emit("차트 오류", "박스플롯에 사용할 변수를 찾을 수 없습니다.")
                return None
        
        ax.set_title('박스플롯')
        
        if options['show_grid']:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def _create_scatter(self, df: pd.DataFrame, x_var: str, y_var: str, 
                       group_var: str, options: Dict[str, Any]) -> plt.Figure:
        """산점도 생성"""
        fig, ax = plt.subplots(figsize=options['figsize'], dpi=options['dpi'])
        
        if x_var not in df.columns or y_var not in df.columns:
            self.error_occurred.emit("차트 오류", f"변수 '{x_var}' 또는 '{y_var}'를 찾을 수 없습니다.")
            return None
        
        if group_var and group_var != "없음" and group_var in df.columns:
            # 그룹별 산점도
            groups = df[group_var].unique()
            for group in groups:
                group_data = df[df[group_var] == group]
                ax.scatter(group_data[x_var], group_data[y_var], 
                          label=str(group), alpha=0.7)
            if options['show_legend']:
                ax.legend()
        else:
            # 단일 산점도
            ax.scatter(df[x_var], df[y_var], alpha=0.7)
        
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f'{x_var} vs {y_var}')
        
        if options['show_grid']:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def _create_line_plot(self, df: pd.DataFrame, x_var: str, y_var: str, 
                         group_var: str, options: Dict[str, Any]) -> plt.Figure:
        """선 그래프 생성"""
        fig, ax = plt.subplots(figsize=options['figsize'], dpi=options['dpi'])
        
        if x_var not in df.columns or y_var not in df.columns:
            self.error_occurred.emit("차트 오류", f"변수 '{x_var}' 또는 '{y_var}'를 찾을 수 없습니다.")
            return None
        
        if group_var and group_var != "없음" and group_var in df.columns:
            # 그룹별 선 그래프
            groups = df[group_var].unique()
            for group in groups:
                group_data = df[df[group_var] == group].sort_values(x_var)
                ax.plot(group_data[x_var], group_data[y_var], 
                       marker='o', label=str(group))
            if options['show_legend']:
                ax.legend()
        else:
            # 단일 선 그래프
            sorted_df = df.sort_values(x_var)
            ax.plot(sorted_df[x_var], sorted_df[y_var], marker='o')
        
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f'{x_var} vs {y_var}')
        
        if options['show_grid']:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def _create_bar_plot(self, df: pd.DataFrame, x_var: str, y_var: str, 
                        group_var: str, options: Dict[str, Any]) -> plt.Figure:
        """막대 그래프 생성"""
        fig, ax = plt.subplots(figsize=options['figsize'], dpi=options['dpi'])
        
        if x_var not in df.columns or y_var not in df.columns:
            self.error_occurred.emit("차트 오류", f"변수 '{x_var}' 또는 '{y_var}'를 찾을 수 없습니다.")
            return None
        
        if group_var and group_var != "없음" and group_var in df.columns:
            # 그룹별 막대 그래프
            sns.barplot(data=df, x=x_var, y=y_var, hue=group_var, ax=ax)
        else:
            # 단일 막대 그래프
            if df[x_var].dtype == 'object' or df[x_var].dtype.name == 'category':
                # 범주형 X축
                sns.barplot(data=df, x=x_var, y=y_var, ax=ax)
            else:
                # 연속형 X축을 범주화
                df_copy = df.copy()
                df_copy[x_var + '_binned'] = pd.cut(df_copy[x_var], bins=10)
                grouped = df_copy.groupby(x_var + '_binned')[y_var].mean()
                ax.bar(range(len(grouped)), grouped.values)
                ax.set_xticks(range(len(grouped)))
                ax.set_xticklabels([str(x) for x in grouped.index], rotation=45)
        
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f'{x_var}별 {y_var}')
        
        if options['show_grid']:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def _create_correlation_matrix(self, df: pd.DataFrame, x_var: str, y_var: str, 
                                  group_var: str, options: Dict[str, Any]) -> plt.Figure:
        """상관행렬 히트맵 생성"""
        fig, ax = plt.subplots(figsize=options['figsize'], dpi=options['dpi'])
        
        # 숫자형 변수만 선택
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            self.error_occurred.emit("차트 오류", "상관행렬을 생성할 숫자형 데이터가 없습니다.")
            return None
        
        # 상관행렬 계산
        corr_matrix = numeric_df.corr()
        
        # 히트맵 생성
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, ax=ax)
        
        ax.set_title('변수 간 상관관계')
        
        plt.tight_layout()
        return fig

    def _create_main_effects_plot(self, df: pd.DataFrame, x_var: str, y_var: str, 
                                 group_var: str, options: Dict[str, Any]) -> plt.Figure:
        """주효과도 생성"""
        fig, ax = plt.subplots(figsize=options['figsize'], dpi=options['dpi'])
        
        # 범주형 변수들 찾기
        categorical_vars = df.select_dtypes(include=['object', 'category']).columns
        numeric_vars = df.select_dtypes(include=[np.number]).columns
        
        if len(categorical_vars) == 0 or len(numeric_vars) == 0:
            self.error_occurred.emit("차트 오류", "주효과도를 생성하려면 범주형 변수와 숫자형 변수가 필요합니다.")
            return None
        
        # 기본값 설정
        if not y_var or y_var not in numeric_vars:
            y_var = numeric_vars[0]
        if not x_var or x_var not in categorical_vars:
            x_var = categorical_vars[0]
        
        # 주효과 계산 및 플롯
        grouped = df.groupby(x_var)[y_var].mean()
        ax.plot(range(len(grouped)), grouped.values, 'bo-', linewidth=2, markersize=8)
        
        ax.set_xticks(range(len(grouped)))
        ax.set_xticklabels(grouped.index)
        ax.set_xlabel(x_var)
        ax.set_ylabel(f'{y_var}의 평균')
        ax.set_title(f'{x_var}의 주효과')
        
        if options['show_grid']:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def _create_interaction_plot(self, df: pd.DataFrame, x_var: str, y_var: str, 
                                group_var: str, options: Dict[str, Any]) -> plt.Figure:
        """상호작용도 생성"""
        fig, ax = plt.subplots(figsize=options['figsize'], dpi=options['dpi'])
        
        # 범주형 변수들 찾기
        categorical_vars = df.select_dtypes(include=['object', 'category']).columns
        numeric_vars = df.select_dtypes(include=[np.number]).columns
        
        if len(categorical_vars) < 2 or len(numeric_vars) == 0:
            self.error_occurred.emit("차트 오류", "상호작용도를 생성하려면 최소 2개의 범주형 변수와 1개의 숫자형 변수가 필요합니다.")
            return None
        
        # 기본값 설정
        if not y_var or y_var not in numeric_vars:
            y_var = numeric_vars[0]
        if not x_var or x_var not in categorical_vars:
            x_var = categorical_vars[0]
        if not group_var or group_var not in categorical_vars:
            remaining_cats = [col for col in categorical_vars if col != x_var]
            group_var = remaining_cats[0] if remaining_cats else None
        
        if not group_var:
            self.error_occurred.emit("차트 오류", "상호작용도를 위한 두 번째 범주형 변수를 찾을 수 없습니다.")
            return None
        
        # 상호작용 플롯 생성
        for group_val in df[group_var].unique():
            group_data = df[df[group_var] == group_val]
            grouped = group_data.groupby(x_var)[y_var].mean()
            ax.plot(range(len(grouped)), grouped.values, 'o-', 
                   label=f'{group_var}={group_val}', linewidth=2, markersize=6)
        
        ax.set_xticks(range(len(df[x_var].unique())))
        ax.set_xticklabels(df[x_var].unique())
        ax.set_xlabel(x_var)
        ax.set_ylabel(f'{y_var}의 평균')
        ax.set_title(f'{x_var}와 {group_var}의 상호작용')
        
        if options['show_legend']:
            ax.legend()
        
        if options['show_grid']:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    def _generate_chart_description(self, chart_type: str, x_var: str, 
                                   y_var: str, group_var: str) -> str:
        """차트 설명 생성"""
        description_parts = []
        
        if x_var:
            description_parts.append(f"X: {x_var}")
        if y_var:
            description_parts.append(f"Y: {y_var}")
        if group_var and group_var != "없음":
            description_parts.append(f"그룹: {group_var}")
        
        if description_parts:
            return ", ".join(description_parts)
        else:
            return chart_type

    def get_supported_chart_types(self) -> List[str]:
        """지원하는 차트 타입 목록 반환"""
        return list(self.supported_chart_types.keys()) 