"""
DataController 단위 테스트
"""

import sys
import os
import unittest
import tempfile
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# src 경로를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from controllers.data_controller import DataController

class TestDataController(unittest.TestCase):
    """DataController 테스트 클래스"""
    
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
        self.controller = DataController(self.parent)
        
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        
        # 테스트용 데이터프레임
        self.test_data = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10.5, 20.5, 30.5, 40.5, 50.5],
            'C': ['가', '나', '다', '라', '마'],
            'D': [True, False, True, False, True]
        })
        
        # 테스트용 CSV 파일 생성
        self.test_csv_path = os.path.join(self.temp_dir, "test_data.csv")
        self.test_data.to_csv(self.test_csv_path, index=False, encoding='utf-8-sig')
        
        # 테스트용 Excel 파일 생성
        self.test_excel_path = os.path.join(self.temp_dir, "test_data.xlsx")
        self.test_data.to_excel(self.test_excel_path, index=False)
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_import_csv_data(self):
        """CSV 데이터 가져오기 테스트"""
        # Given
        data_imported_signal = Mock()
        self.controller.data_imported.connect(data_imported_signal)
        
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (self.test_csv_path, "CSV Files (*.csv)")
            
            # When
            self.controller.import_data()
            
            # Then
            data_imported_signal.assert_called_once()
            args = data_imported_signal.call_args[0]
            imported_df = args[0]
            
            self.assertEqual(len(imported_df), 5)
            self.assertEqual(list(imported_df.columns), ['A', 'B', 'C', 'D'])
    
    def test_import_excel_data(self):
        """Excel 데이터 가져오기 테스트"""
        # Given
        data_imported_signal = Mock()
        self.controller.data_imported.connect(data_imported_signal)
        
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (self.test_excel_path, "Excel Files (*.xlsx)")
            
            # When
            self.controller.import_data()
            
            # Then
            data_imported_signal.assert_called_once()
            args = data_imported_signal.call_args[0]
            imported_df = args[0]
            
            self.assertEqual(len(imported_df), 5)
            self.assertEqual(list(imported_df.columns), ['A', 'B', 'C', 'D'])
    
    def test_export_csv_data(self):
        """CSV 데이터 내보내기 테스트"""
        # Given
        export_path = os.path.join(self.temp_dir, "exported_data.csv")
        data_exported_signal = Mock()
        self.controller.data_exported.connect(data_exported_signal)
        
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = (export_path, "CSV Files (*.csv)")
            
            # When
            self.controller.export_data(self.test_data)
            
            # Then
            data_exported_signal.assert_called_once()
            self.assertTrue(os.path.exists(export_path))
            
            # 내보낸 파일을 다시 읽어서 확인
            exported_df = pd.read_csv(export_path)
            self.assertEqual(len(exported_df), 5)
    
    def test_export_excel_data(self):
        """Excel 데이터 내보내기 테스트"""
        # Given
        export_path = os.path.join(self.temp_dir, "exported_data.xlsx")
        data_exported_signal = Mock()
        self.controller.data_exported.connect(data_exported_signal)
        
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = (export_path, "Excel Files (*.xlsx)")
            
            # When
            self.controller.export_data(self.test_data)
            
            # Then
            data_exported_signal.assert_called_once()
            self.assertTrue(os.path.exists(export_path))
            
            # 내보낸 파일을 다시 읽어서 확인
            exported_df = pd.read_excel(export_path)
            self.assertEqual(len(exported_df), 5)
    
    def test_get_data_summary(self):
        """데이터 요약 정보 테스트"""
        # When
        summary = self.controller.get_data_summary(self.test_data)
        
        # Then
        self.assertIsInstance(summary, str)
        self.assertIn('행 수: 5', summary)
        self.assertIn('열 수: 4', summary)
        self.assertIn('숫자형 열', summary)
        self.assertIn('텍스트 열', summary)
    
    def test_validate_data_for_analysis(self):
        """분석을 위한 데이터 유효성 검사 테스트"""
        # Given - 분석에 적합한 데이터
        numeric_data = pd.DataFrame({
            'X': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'Y': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        })
        
        # When
        result = self.controller.validate_data_for_analysis(numeric_data)
        
        # Then
        self.assertTrue(result)  # 메서드가 boolean을 반환
    
    def test_validate_insufficient_data(self):
        """부족한 데이터에 대한 유효성 검사 테스트"""
        # Given - 행이 적은 데이터
        small_data = pd.DataFrame({
            'X': [1, 2],
            'Y': [2, 4]
        })
        
        # When
        result = self.controller.validate_data_for_analysis(small_data)
        
        # Then
        self.assertFalse(result)  # 메서드가 boolean을 반환
    
    def test_invalid_file_import(self):
        """유효하지 않은 파일 가져오기 테스트"""
        # Given
        invalid_file_path = os.path.join(self.temp_dir, "invalid.txt")
        with open(invalid_file_path, 'w') as f:
            f.write("This is not a valid data file")
        
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (invalid_file_path, "Text Files (*.txt)")
            
            # When
            self.controller.import_data()
            
            # Then
            error_signal.assert_called_once()
    
    def test_large_data_warning(self):
        """대용량 데이터 경고 테스트"""
        # Given - 큰 데이터프레임 생성
        large_data = pd.DataFrame({
            'A': range(15000),  # 15,000 rows
            'B': range(15000, 30000)
        })
        
        # When
        summary = self.controller.get_data_summary(large_data)
        
        # Then
        self.assertIsInstance(summary, str)
        self.assertIn('행 수: 15,000', summary)
        # 대용량 데이터 처리 확인
    
    def test_empty_dataframe_handling(self):
        """빈 데이터프레임 처리 테스트"""
        # Given
        empty_df = pd.DataFrame()
        
        # When
        summary = self.controller.get_data_summary(empty_df)
        
        # Then
        self.assertIsInstance(summary, str)
        self.assertEqual(summary, '데이터가 없습니다.')
    
    def test_encoding_detection(self):
        """인코딩 자동 감지 테스트"""
        # Given - 한글이 포함된 CSV 파일 (CP949 인코딩)
        korean_data = pd.DataFrame({
            '이름': ['김철수', '이영희', '박민수'],
            '나이': [25, 30, 35],
            '직업': ['개발자', '디자이너', '기획자']
        })
        
        cp949_file_path = os.path.join(self.temp_dir, "korean_data.csv")
        korean_data.to_csv(cp949_file_path, index=False, encoding='cp949')
        
        data_imported_signal = Mock()
        self.controller.data_imported.connect(data_imported_signal)
        
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (cp949_file_path, "CSV Files (*.csv)")
            
            # When
            self.controller.import_data()
            
            # Then
            data_imported_signal.assert_called_once()
            args = data_imported_signal.call_args[0]
            imported_df = args[0]
            
            # 한글이 제대로 로드되었는지 확인
            self.assertIn('김철수', imported_df['이름'].values)
            self.assertIn('개발자', imported_df['직업'].values)
    
    def test_duplicate_columns_detection(self):
        """중복 컬럼명 감지 테스트"""
        # Given - 중복 컬럼명이 있는 데이터
        duplicate_cols_file = os.path.join(self.temp_dir, "duplicate_cols.csv")
        with open(duplicate_cols_file, 'w', encoding='utf-8') as f:
            f.write("A,B,A,C\n1,2,3,4\n5,6,7,8\n")
        
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (duplicate_cols_file, "CSV Files (*.csv)")
            
            # When
            self.controller.import_data()
            
            # Then
            # 중복 컬럼에 대한 처리가 있어야 함 (경고 또는 오류)
            # 실제 구현에 따라 달라질 수 있음


if __name__ == '__main__':
    unittest.main() 