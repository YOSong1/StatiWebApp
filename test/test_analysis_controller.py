"""
AnalysisController 단위 테스트
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

# src 경로를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from controllers.analysis_controller import AnalysisController

class TestAnalysisController(unittest.TestCase):
    """AnalysisController 테스트 클래스"""
    
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
        self.controller = AnalysisController(self.parent)
        
        # 테스트용 데이터프레임 - 다양한 분석에 적합
        np.random.seed(42)  # 재현 가능한 랜덤 데이터
        
        self.test_data = pd.DataFrame({
            'score': np.random.normal(75, 15, 100),  # 점수 (정규분포)
            'age': np.random.randint(20, 60, 100),   # 나이
            'group': np.random.choice(['A', 'B', 'C'], 100),  # 그룹 (범주형)
            'treatment': np.random.choice(['Treatment', 'Control'], 100),  # 처리 (범주형)
            'height': np.random.normal(170, 10, 100),  # 키
            'weight': np.random.normal(70, 15, 100)    # 몸무게
        })
        
        # 작은 데이터셋 (분석에 부적합)
        self.small_data = pd.DataFrame({
            'X': [1, 2, 3],
            'Y': [4, 5, 6]
        })
        
        # 숫자형 데이터만 있는 데이터셋
        self.numeric_only_data = self.test_data[['score', 'age', 'height', 'weight']].copy()
        
        # 범주형 데이터만 있는 데이터셋
        self.categorical_only_data = self.test_data[['group', 'treatment']].copy()
    
    def test_run_basic_statistics(self):
        """기초 통계 분석 테스트"""
        # Given
        analysis_completed_signal = Mock()
        self.controller.analysis_completed.connect(analysis_completed_signal)
        
        # When
        self.controller.run_basic_statistics(self.test_data)
        
        # Then
        # 시그널 발생 확인
        analysis_completed_signal.assert_called_once()
        
        # 시그널 인자 확인
        call_args = analysis_completed_signal.call_args[0]
        analysis_type = call_args[0]
        result = call_args[1]
        
        self.assertEqual(analysis_type, '기초 통계')
        self.assertEqual(result['type'], '기초 통계')
        self.assertEqual(result['status'], '완료')
        self.assertIn('results', result)
    
    def test_run_correlation_analysis(self):
        """상관분석 테스트"""
        # Given
        analysis_completed_signal = Mock()
        self.controller.analysis_completed.connect(analysis_completed_signal)
        
        # When
        self.controller.run_correlation_analysis(self.numeric_only_data)
        
        # Then
        # 시그널 발생 확인
        analysis_completed_signal.assert_called_once()
        
        # 시그널 인자 확인
        call_args = analysis_completed_signal.call_args[0]
        analysis_type = call_args[0]
        result = call_args[1]
        
        self.assertEqual(analysis_type, '상관분석')
        self.assertEqual(result['type'], '상관분석')
        self.assertEqual(result['status'], '완료')
        
        # 상관계수 행렬 확인
        results = result['results']
        self.assertIn('correlation_matrix', results)
        self.assertIn('strong_correlations', results)
    
    def test_run_anova(self):
        """ANOVA 분석 테스트"""
        # Given
        analysis_completed_signal = Mock()
        self.controller.analysis_completed.connect(analysis_completed_signal)
        
        # When
        self.controller.run_anova(self.test_data)
        
        # Then
        # 시그널 발생 확인
        analysis_completed_signal.assert_called_once()
        
        # 시그널 인자 확인
        call_args = analysis_completed_signal.call_args[0]
        analysis_type = call_args[0]
        result = call_args[1]
        
        self.assertEqual(analysis_type, 'ANOVA')
        self.assertEqual(result['type'], 'ANOVA')
        self.assertEqual(result['status'], '완료')
        
        # ANOVA 결과 확인
        results = result['results']
        self.assertIn('f_statistic', results)
        self.assertIn('p_value', results)
        self.assertIn('group_stats', results)
    
    def test_run_regression(self):
        """회귀분석 테스트"""
        # Given
        analysis_completed_signal = Mock()
        self.controller.analysis_completed.connect(analysis_completed_signal)
        
        # When
        self.controller.run_regression(self.test_data)
        
        # Then
        # 시그널 발생 확인
        analysis_completed_signal.assert_called_once()
        
        # 시그널 인자 확인
        call_args = analysis_completed_signal.call_args[0]
        analysis_type = call_args[0]
        result = call_args[1]
        
        self.assertEqual(analysis_type, '회귀분석')
        self.assertEqual(result['type'], '회귀분석')
        self.assertEqual(result['status'], '완료')
        
        # 회귀분석 결과 확인
        results = result['results']
        self.assertIn('r_squared', results)
        self.assertIn('coefficients', results)
    
    def test_insufficient_data_validation(self):
        """부족한 데이터에 대한 검증 테스트"""
        # Given - 빈 데이터프레임
        empty_data = pd.DataFrame()
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        self.controller.run_basic_statistics(empty_data)
        
        # Then
        error_signal.assert_called_once()
    
    def test_correlation_with_insufficient_numeric_data(self):
        """숫자형 변수가 부족한 상관분석 테스트"""
        # Given
        single_numeric_data = pd.DataFrame({'X': [1, 2, 3, 4, 5]})
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        result = self.controller.run_correlation_analysis(single_numeric_data)
        
        # Then
        self.assertIsNone(result)
        error_signal.assert_called_once()
    
    def test_anova_with_no_categorical_data(self):
        """범주형 변수가 없는 ANOVA 테스트"""
        # Given
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        self.controller.run_anova(self.numeric_only_data)
        
        # Then
        error_signal.assert_called_once()
    
    def test_regression_with_insufficient_variables(self):
        """변수가 부족한 회귀분석 테스트"""
        # Given
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # 숫자형 변수가 1개만 있는 데이터
        single_var_data = pd.DataFrame({'X': [1, 2, 3, 4, 5]})
        
        # When
        self.controller.run_regression(single_var_data)
        
        # Then
        error_signal.assert_called_once()
    
    def test_missing_data_handling(self):
        """결측값이 있는 데이터 처리 테스트"""
        # Given - 결측값이 있는 데이터
        data_with_missing = self.test_data.copy()
        data_with_missing.loc[0:10, 'score'] = np.nan
        data_with_missing.loc[5:15, 'age'] = np.nan
        
        analysis_completed_signal = Mock()
        self.controller.analysis_completed.connect(analysis_completed_signal)
        
        # When
        self.controller.run_basic_statistics(data_with_missing)
        
        # Then
        # 시그널이 발생했는지 확인 (결측값이 있어도 분석은 진행됨)
        analysis_completed_signal.assert_called_once()
    
    def test_categorical_analysis(self):
        """범주형 데이터 분석 테스트"""
        # Given
        analysis_completed_signal = Mock()
        self.controller.analysis_completed.connect(analysis_completed_signal)
        
        # When
        self.controller.run_basic_statistics(self.test_data)
        
        # Then
        # 시그널 발생 확인
        analysis_completed_signal.assert_called_once()
        
        # 시그널 인자 확인
        call_args = analysis_completed_signal.call_args[0]
        result = call_args[1]
        
        self.assertIn('results', result)
        # 기본 통계 결과가 있는지 확인
        self.assertIn('summary', result['results'])
    
    def test_statistical_interpretation(self):
        """통계적 해석 기능 테스트"""
        # Given
        analysis_completed_signal = Mock()
        self.controller.analysis_completed.connect(analysis_completed_signal)
        
        # When
        self.controller.run_correlation_analysis(self.numeric_only_data)
        
        # Then
        # 시그널 발생 확인
        analysis_completed_signal.assert_called_once()
        
        # 시그널 인자 확인
        call_args = analysis_completed_signal.call_args[0]
        result = call_args[1]
        
        self.assertIn('results', result)
        self.assertEqual(result['type'], '상관분석')
    
    def test_analysis_with_single_group(self):
        """단일 그룹 ANOVA 테스트 (에러 케이스)"""
        # Given - 모든 값이 같은 그룹인 데이터
        single_group_data = self.test_data.copy()
        single_group_data['group'] = 'A'  # 모든 값을 A로 설정
        
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        self.controller.run_anova(single_group_data)
        
        # Then
        error_signal.assert_called_once()
    
    def test_perfect_correlation_handling(self):
        """완전 상관관계 처리 테스트"""
        # Given - 완전 상관관계가 있는 데이터
        perfect_corr_data = pd.DataFrame({
            'X': [1, 2, 3, 4, 5],
            'Y': [2, 4, 6, 8, 10],  # Y = 2*X (완전 양의 상관)
            'Z': [10, 20, 30, 40, 50]  # Z = 10*X (완전 양의 상관)
        })
        
        analysis_completed_signal = Mock()
        self.controller.analysis_completed.connect(analysis_completed_signal)
        
        # When
        self.controller.run_correlation_analysis(perfect_corr_data)
        
        # Then
        # 시그널 발생 확인
        analysis_completed_signal.assert_called_once()
        
        # 시그널 인자 확인
        call_args = analysis_completed_signal.call_args[0]
        result = call_args[1]
        
        self.assertIn('results', result)
        correlation_matrix = result['results']['correlation_matrix']
        
        # 완전 상관관계 확인 (대각선 제외)
        self.assertAlmostEqual(correlation_matrix.loc['X', 'Y'], 1.0, places=5)
        self.assertAlmostEqual(correlation_matrix.loc['X', 'Z'], 1.0, places=5)


if __name__ == '__main__':
    unittest.main() 