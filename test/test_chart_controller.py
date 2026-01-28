"""
ChartController 단위 테스트
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from unittest.mock import Mock, patch, MagicMock

# src 경로를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from controllers.chart_controller import ChartController

class TestChartController(unittest.TestCase):
    """ChartController 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """클래스 레벨 설정 - QApplication 초기화"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """테스트 준비"""
        self.parent = QObject()
        self.controller = ChartController(self.parent)
        
        # 테스트용 데이터프레임
        np.random.seed(42)
        
        self.test_data = pd.DataFrame({
            'numerical_1': np.random.normal(50, 15, 100),
            'numerical_2': np.random.normal(75, 20, 100),
            'categorical_1': np.random.choice(['A', 'B', 'C'], 100),
            'categorical_2': np.random.choice(['Group1', 'Group2'], 100),
            'integer_col': np.random.randint(1, 100, 100)
        })
        
        # 상관행렬용 숫자형 데이터만
        self.numeric_data = self.test_data[['numerical_1', 'numerical_2', 'integer_col']].copy()
        
        # 빈 데이터프레임
        self.empty_data = pd.DataFrame()
        
        # 기본 차트 옵션
        self.default_options = {
            'show_grid': True,
            'show_legend': True,
            'bins': 20,
            'figsize': (10, 6),
            'dpi': 100
        }
    
    def tearDown(self):
        """테스트 정리"""
        # matplotlib 도표 정리
        plt.close('all')
    
    def test_get_supported_chart_types(self):
        """지원하는 차트 타입 목록 테스트"""
        # When
        chart_types = self.controller.get_supported_chart_types()
        
        # Then
        expected_types = [
            "히스토그램", "박스플롯", "산점도", "선 그래프",
            "막대 그래프", "상관행렬", "주효과도", "상호작용도"
        ]
        
        self.assertEqual(len(chart_types), len(expected_types))
        for chart_type in expected_types:
            self.assertIn(chart_type, chart_types)
    
    def test_create_histogram(self):
        """히스토그램 생성 테스트"""
        # Given
        chart_created_signal = Mock()
        self.controller.chart_created.connect(chart_created_signal)
        
        # When
        chart_info = self.controller.create_chart(
            chart_type="히스토그램",
            dataframe=self.test_data,
            x_var="numerical_1",
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['type'], '히스토그램')
        self.assertEqual(chart_info['x_variable'], 'numerical_1')
        self.assertIn('figure', chart_info)
        self.assertIsInstance(chart_info['figure'], plt.Figure)
        
        # 시그널 발생 확인
        chart_created_signal.assert_called_once()
    
    def test_create_scatter_plot(self):
        """산점도 생성 테스트"""
        # Given
        chart_created_signal = Mock()
        self.controller.chart_created.connect(chart_created_signal)
        
        # When
        chart_info = self.controller.create_chart(
            chart_type="산점도",
            dataframe=self.test_data,
            x_var="numerical_1",
            y_var="numerical_2",
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['type'], '산점도')
        self.assertEqual(chart_info['x_variable'], 'numerical_1')
        self.assertEqual(chart_info['y_variable'], 'numerical_2')
        self.assertIn('figure', chart_info)
        
        chart_created_signal.assert_called_once()
    
    def test_create_scatter_plot_with_group(self):
        """그룹별 산점도 생성 테스트"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="산점도",
            dataframe=self.test_data,
            x_var="numerical_1",
            y_var="numerical_2",
            group_var="categorical_1",
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['group_variable'], 'categorical_1')
        self.assertIn('그룹: categorical_1', chart_info['description'])
    
    def test_create_boxplot(self):
        """박스플롯 생성 테스트"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="박스플롯",
            dataframe=self.test_data,
            x_var="categorical_1",
            y_var="numerical_1",
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['type'], '박스플롯')
        self.assertIn('figure', chart_info)
    
    def test_create_line_plot(self):
        """선 그래프 생성 테스트"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="선 그래프",
            dataframe=self.test_data,
            x_var="numerical_1",
            y_var="numerical_2",
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['type'], '선 그래프')
    
    def test_create_bar_plot(self):
        """막대 그래프 생성 테스트"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="막대 그래프",
            dataframe=self.test_data,
            x_var="categorical_1",
            y_var="numerical_1",
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['type'], '막대 그래프')
    
    def test_create_correlation_matrix(self):
        """상관행렬 히트맵 생성 테스트"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="상관행렬",
            dataframe=self.numeric_data,
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['type'], '상관행렬')
        self.assertIn('figure', chart_info)
    
    def test_create_main_effects_plot(self):
        """주효과도 생성 테스트"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="주효과도",
            dataframe=self.test_data,
            x_var="categorical_1",
            y_var="numerical_1",
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['type'], '주효과도')
    
    def test_create_interaction_plot(self):
        """상호작용도 생성 테스트"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="상호작용도",
            dataframe=self.test_data,
            x_var="categorical_1",
            y_var="numerical_1",
            group_var="categorical_2",
            options=self.default_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['type'], '상호작용도')
    
    def test_unsupported_chart_type(self):
        """지원하지 않는 차트 타입 테스트"""
        # Given
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        chart_info = self.controller.create_chart(
            chart_type="지원하지않는차트",
            dataframe=self.test_data,
            x_var="numerical_1"
        )
        
        # Then
        self.assertIsNone(chart_info)
        error_signal.assert_called_once()
    
    def test_empty_dataframe(self):
        """빈 데이터프레임으로 차트 생성 테스트"""
        # Given
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        chart_info = self.controller.create_chart(
            chart_type="히스토그램",
            dataframe=self.empty_data,
            x_var="numerical_1"
        )
        
        # Then
        self.assertIsNone(chart_info)
        error_signal.assert_called_once()
    
    def test_missing_required_variables(self):
        """필수 변수가 없는 경우 테스트"""
        # Given
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When - 산점도에 y축 변수 없음
        chart_info = self.controller.create_chart(
            chart_type="산점도",
            dataframe=self.test_data,
            x_var="numerical_1",
            y_var=None  # 필수 변수 누락
        )
        
        # Then
        self.assertIsNone(chart_info)
        error_signal.assert_called_once()
    
    def test_nonexistent_variable(self):
        """존재하지 않는 변수로 차트 생성 테스트"""
        # Given
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        chart_info = self.controller.create_chart(
            chart_type="히스토그램",
            dataframe=self.test_data,
            x_var="nonexistent_column"
        )
        
        # Then
        self.assertIsNone(chart_info)
        error_signal.assert_called_once()
    
    def test_correlation_matrix_no_numeric_data(self):
        """숫자형 데이터가 없는 상관행렬 테스트"""
        # Given
        categorical_only_data = pd.DataFrame({
            'cat1': ['A', 'B', 'C', 'A', 'B'],
            'cat2': ['X', 'Y', 'X', 'Y', 'X']
        })
        
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        chart_info = self.controller.create_chart(
            chart_type="상관행렬",
            dataframe=categorical_only_data
        )
        
        # Then
        self.assertIsNone(chart_info)
        error_signal.assert_called_once()
    
    def test_chart_options_application(self):
        """차트 옵션 적용 테스트"""
        # Given
        custom_options = {
            'show_grid': False,
            'show_legend': False,
            'bins': 30,
            'figsize': (12, 8),
            'dpi': 150
        }
        
        # When
        chart_info = self.controller.create_chart(
            chart_type="히스토그램",
            dataframe=self.test_data,
            x_var="numerical_1",
            options=custom_options
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertEqual(chart_info['options']['bins'], 30)
        self.assertEqual(chart_info['options']['figsize'], (12, 8))
        self.assertEqual(chart_info['options']['dpi'], 150)
        self.assertFalse(chart_info['options']['show_grid'])
        self.assertFalse(chart_info['options']['show_legend'])
    
    def test_chart_description_generation(self):
        """차트 설명 생성 테스트"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="산점도",
            dataframe=self.test_data,
            x_var="numerical_1",
            y_var="numerical_2",
            group_var="categorical_1"
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        description = chart_info['description']
        self.assertIn("numerical_1", description)
        self.assertIn("numerical_2", description)
        self.assertIn("categorical_1", description)
    
    def test_insufficient_categorical_variables_for_interaction(self):
        """상호작용도 생성 시 범주형 변수 부족 테스트"""
        # Given - 범주형 변수가 1개만 있는 데이터
        insufficient_data = pd.DataFrame({
            'numeric': [1, 2, 3, 4, 5],
            'category': ['A', 'B', 'A', 'B', 'A']
        })
        
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        chart_info = self.controller.create_chart(
            chart_type="상호작용도",
            dataframe=insufficient_data,
            x_var="category",
            y_var="numeric"
        )
        
        # Then
        self.assertIsNone(chart_info)
        error_signal.assert_called_once()
    
    def test_status_update_signals(self):
        """상태 업데이트 시그널 테스트"""
        # Given
        status_updated_signal = Mock()
        self.controller.status_updated.connect(status_updated_signal)
        
        # When
        self.controller.create_chart(
            chart_type="히스토그램",
            dataframe=self.test_data,
            x_var="numerical_1"
        )
        
        # Then
        # 시작과 완료 시그널이 발생했는지 확인
        self.assertGreaterEqual(status_updated_signal.call_count, 2)
    
    def test_timestamp_in_chart_info(self):
        """차트 정보에 타임스탬프 포함 확인"""
        # When
        chart_info = self.controller.create_chart(
            chart_type="히스토그램",
            dataframe=self.test_data,
            x_var="numerical_1"
        )
        
        # Then
        self.assertIsNotNone(chart_info)
        self.assertIn('timestamp', chart_info)
        self.assertIsInstance(chart_info['timestamp'], str)
        # 타임스탬프 형식 확인 (HH:MM:SS)
        timestamp_parts = chart_info['timestamp'].split(':')
        self.assertEqual(len(timestamp_parts), 3)


if __name__ == '__main__':
    unittest.main() 