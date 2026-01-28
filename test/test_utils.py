"""
유틸리티 함수들의 단위 테스트
"""

import sys
import os
import unittest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# src 경로를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.data_utils import (
    detect_encoding, try_read_csv_with_encodings, validate_dataframe,
    get_data_summary, prepare_data_for_analysis, convert_data_types,
    check_analysis_requirements
)
from utils.file_utils import (
    ensure_directory_exists, get_safe_filename, get_unique_filename,
    backup_file, load_json_file, save_json_file, get_file_info,
    find_files_by_extension, export_dataframe, validate_file_path
)

class TestDataUtils(unittest.TestCase):
    """데이터 유틸리티 함수 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 테스트용 데이터프레임
        self.test_data = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10.5, 20.5, 30.5, 40.5, 50.5],
            'C': ['가', '나', '다', '라', '마'],
            'D': [True, False, True, False, True]
        })
        
        # 테스트용 CSV 파일들
        self.utf8_file = os.path.join(self.temp_dir, "utf8_data.csv")
        self.test_data.to_csv(self.utf8_file, index=False, encoding='utf-8')
        
        self.cp949_file = os.path.join(self.temp_dir, "cp949_data.csv")
        self.test_data.to_csv(self.cp949_file, index=False, encoding='cp949')
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_encoding(self):
        """인코딩 감지 테스트"""
        # UTF-8 파일
        encoding = detect_encoding(self.utf8_file)
        self.assertIn(encoding.lower(), ['utf-8', 'utf-8-sig'])
        
        # CP949 파일
        encoding = detect_encoding(self.cp949_file)
        self.assertEqual(encoding.lower(), 'cp949')
    
    def test_try_read_csv_with_encodings(self):
        """다중 인코딩 CSV 읽기 테스트"""
        # UTF-8 파일 읽기
        df = try_read_csv_with_encodings(self.utf8_file)
        self.assertEqual(len(df), 5)
        self.assertEqual(list(df.columns), ['A', 'B', 'C', 'D'])
        
        # CP949 파일 읽기
        df = try_read_csv_with_encodings(self.cp949_file)
        self.assertEqual(len(df), 5)
        self.assertIn('가', df['C'].values)
    
    def test_validate_dataframe(self):
        """데이터프레임 유효성 검사 테스트"""
        # 정상 데이터
        result = validate_dataframe(self.test_data)
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        
        # 빈 데이터프레임
        empty_df = pd.DataFrame()
        result = validate_dataframe(empty_df)
        self.assertFalse(result['is_valid'])
        self.assertIn("비어있습니다", str(result['errors']))
        
        # 중복 컬럼은 pandas에서 자동으로 처리되므로 다른 테스트로 변경
        # 매우 큰 데이터프레임으로 경고 테스트
        large_df = pd.DataFrame({'A': range(15000), 'B': range(15000)})
        result = validate_dataframe(large_df)
        self.assertTrue(result['is_valid'])  # 경고는 있지만 유효함
        self.assertGreater(len(result['warnings']), 0)
    
    def test_get_data_summary(self):
        """데이터 요약 정보 테스트"""
        summary = get_data_summary(self.test_data)
        
        # 기본 정보 확인
        self.assertIn('basic_info', summary)
        self.assertEqual(summary['basic_info']['rows'], 5)
        self.assertEqual(summary['basic_info']['columns'], 4)
        
        # 데이터 타입 분류 확인
        self.assertIn('data_types', summary)
        self.assertEqual(len(summary['data_types']['numeric']), 2)  # A, B
        self.assertEqual(len(summary['data_types']['categorical']), 1)  # C
        
        # 컬럼별 정보 확인
        self.assertIn('column_info', summary)
        self.assertIn('A', summary['column_info'])
        self.assertIn('mean', summary['column_info']['A'])
    
    def test_prepare_data_for_analysis(self):
        """분석용 데이터 전처리 테스트"""
        # 정상 데이터 전처리
        processed_df, info = prepare_data_for_analysis(self.test_data)
        self.assertEqual(processed_df.shape, self.test_data.shape)
        self.assertIn('original_shape', info)
        
        # 특정 컬럼 제외
        processed_df, info = prepare_data_for_analysis(
            self.test_data, exclude_columns=['C', 'D']
        )
        self.assertEqual(processed_df.shape[1], 2)  # A, B만 남음
        self.assertIn('제외된 컬럼', str(info['transformations']))
    
    def test_convert_data_types(self):
        """데이터 타입 변환 테스트"""
        # 타입 힌트 없이 자동 최적화
        converted_df = convert_data_types(self.test_data.copy())
        self.assertEqual(len(converted_df), len(self.test_data))
        
        # 타입 힌트 적용
        type_hints = {'C': 'category'}
        converted_df = convert_data_types(self.test_data.copy(), type_hints)
        self.assertEqual(converted_df['C'].dtype.name, 'category')
    
    def test_check_analysis_requirements(self):
        """분석 요구사항 검사 테스트"""
        # 상관분석 요구사항
        result = check_analysis_requirements(self.test_data, 'correlation')
        self.assertIn('is_suitable', result)
        
        # 숫자형 변수가 부족한 경우
        categorical_only = pd.DataFrame({'cat': ['A', 'B', 'C']})
        result = check_analysis_requirements(categorical_only, 'correlation')
        self.assertIn('is_suitable', result)
        
        # ANOVA 요구사항
        result = check_analysis_requirements(self.test_data, 'anova')
        self.assertIn('is_suitable', result)


class TestFileUtils(unittest.TestCase):
    """파일 유틸리티 함수 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 테스트용 데이터
        self.test_data = pd.DataFrame({
            'X': [1, 2, 3, 4, 5],
            'Y': [10, 20, 30, 40, 50]
        })
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensure_directory_exists(self):
        """디렉토리 생성 테스트"""
        new_dir_path = os.path.join(self.temp_dir, "new_dir", "sub_dir")
        file_path = os.path.join(new_dir_path, "test.txt")
        
        # 디렉토리가 없는 상태에서 파일 경로로 디렉토리 생성
        ensure_directory_exists(file_path)
        
        # 디렉토리가 생성되었는지 확인
        self.assertTrue(os.path.exists(new_dir_path))
    
    def test_get_safe_filename(self):
        """안전한 파일명 생성 테스트"""
        # 특수문자 제거
        unsafe_name = "test<>file:name?.txt"
        safe_name = get_safe_filename(unsafe_name)
        self.assertNotIn('<', safe_name)
        self.assertNotIn('>', safe_name)
        self.assertNotIn(':', safe_name)
        
        # 길이 제한
        long_name = "a" * 300 + ".txt"
        safe_name = get_safe_filename(long_name, max_length=255)
        self.assertLessEqual(len(safe_name), 255)
        self.assertTrue(safe_name.endswith('.txt'))
    
    def test_get_unique_filename(self):
        """고유 파일명 생성 테스트"""
        # 첫 번째 파일은 원본 이름 그대로
        test_file = os.path.join(self.temp_dir, "test.txt")
        unique_name = get_unique_filename(test_file)
        self.assertEqual(unique_name, test_file)
        
        # 파일 생성 후 고유 이름 생성
        with open(test_file, 'w') as f:
            f.write("test")
        
        unique_name = get_unique_filename(test_file)
        self.assertNotEqual(unique_name, test_file)
        self.assertIn("test_1.txt", unique_name)
    
    def test_backup_file(self):
        """파일 백업 테스트"""
        # 테스트 파일 생성
        test_file = os.path.join(self.temp_dir, "original.txt")
        with open(test_file, 'w') as f:
            f.write("original content")
        
        # 백업 생성
        backup_path = backup_file(test_file)
        
        # 백업 파일 존재 확인
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        
        # 백업 파일 내용 확인
        with open(backup_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "original content")
    
    def test_json_file_operations(self):
        """JSON 파일 읽기/쓰기 테스트"""
        test_data = {
            'name': '테스트',
            'values': [1, 2, 3],
            'nested': {'key': 'value'}
        }
        
        json_file = os.path.join(self.temp_dir, "test.json")
        
        # JSON 저장
        success = save_json_file(test_data, json_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(json_file))
        
        # JSON 로드
        loaded_data = load_json_file(json_file)
        self.assertEqual(loaded_data['name'], '테스트')
        self.assertEqual(loaded_data['values'], [1, 2, 3])
    
    def test_get_file_info(self):
        """파일 정보 가져오기 테스트"""
        # 존재하지 않는 파일
        info = get_file_info("nonexistent.txt")
        self.assertFalse(info['exists'])
        
        # 존재하는 파일
        test_file = os.path.join(self.temp_dir, "info_test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        info = get_file_info(test_file)
        self.assertTrue(info['exists'])
        self.assertEqual(info['name'], 'info_test.txt')
        self.assertEqual(info['extension'], '.txt')
        self.assertTrue(info['is_file'])
    
    def test_find_files_by_extension(self):
        """확장자별 파일 찾기 테스트"""
        # 테스트 파일들 생성
        test_files = [
            "test1.csv",
            "test2.txt", 
            "test3.csv",
            "test4.xlsx"
        ]
        
        for filename in test_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write("test")
        
        # CSV 파일들 찾기
        csv_files = find_files_by_extension(self.temp_dir, ['.csv'])
        self.assertEqual(len(csv_files), 2)
        
        # 여러 확장자 찾기
        data_files = find_files_by_extension(self.temp_dir, ['.csv', '.xlsx'])
        self.assertEqual(len(data_files), 3)
    
    def test_export_dataframe(self):
        """데이터프레임 내보내기 테스트"""
        # CSV 내보내기
        csv_path = os.path.join(self.temp_dir, "export_test.csv")
        success, message = export_dataframe(self.test_data, csv_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(csv_path))
        
        # Excel 내보내기
        excel_path = os.path.join(self.temp_dir, "export_test.xlsx")
        success, message = export_dataframe(self.test_data, excel_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(excel_path))
        
        # 지원하지 않는 형식
        unsupported_path = os.path.join(self.temp_dir, "export_test.xyz")
        success, message = export_dataframe(self.test_data, unsupported_path)
        self.assertFalse(success)
        self.assertIn("지원하지 않는", message)
    
    def test_validate_file_path(self):
        """파일 경로 유효성 검사 테스트"""
        # 정상 경로
        valid_path = os.path.join(self.temp_dir, "valid_file.txt")
        is_valid, message = validate_file_path(valid_path)
        self.assertTrue(is_valid)
        
        # 빈 경로
        is_valid, message = validate_file_path("")
        self.assertFalse(is_valid)
        self.assertIn("비어있습니다", message)
        
        # 유효하지 않은 문자
        invalid_path = os.path.join(self.temp_dir, "invalid<>file.txt")
        is_valid, message = validate_file_path(invalid_path)
        self.assertFalse(is_valid)
        
        # 존재하지 않는 파일 (must_exist=True)
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.txt")
        is_valid, message = validate_file_path(nonexistent_path, must_exist=True)
        self.assertFalse(is_valid)
        self.assertIn("존재하지 않습니다", message)


if __name__ == '__main__':
    # 모든 테스트 실행
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 각 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestDataUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestFileUtils))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite) 