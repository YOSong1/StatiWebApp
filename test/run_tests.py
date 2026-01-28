#!/usr/bin/env python3
"""
전체 단위 테스트 실행 스크립트

Usage:
    python test/run_tests.py              # 모든 테스트 실행
    python test/run_tests.py -v           # 상세 출력
    python test/run_tests.py controller   # 특정 모듈만 테스트
"""

import sys
import os
import unittest
import argparse
from pathlib import Path

# 현재 스크립트 위치 기준으로 src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

# 테스트 모듈들 임포트
try:
    from test_project_controller import TestProjectController
    from test_data_controller import TestDataController
    from test_analysis_controller import TestAnalysisController
    from test_chart_controller import TestChartController
    from test_utils import TestDataUtils, TestFileUtils
except ImportError as e:
    print(f"테스트 모듈 임포트 오류: {e}")
    print("src 디렉토리의 모든 모듈이 올바르게 구현되어 있는지 확인해주세요.")
    sys.exit(1)

def create_test_suite(test_pattern=None):
    """
    테스트 스위트 생성
    
    Args:
        test_pattern: 실행할 테스트 패턴 (None이면 모든 테스트)
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 사용 가능한 테스트 클래스들
    test_classes = {
        'project': TestProjectController,
        'data': TestDataController,
        'analysis': TestAnalysisController,
        'chart': TestChartController,
        'utils_data': TestDataUtils,
        'utils_file': TestFileUtils
    }
    
    if test_pattern is None:
        # 모든 테스트 추가
        for test_class in test_classes.values():
            suite.addTests(loader.loadTestsFromTestCase(test_class))
    else:
        # 패턴에 맞는 테스트만 추가
        pattern_lower = test_pattern.lower()
        added = False
        
        for name, test_class in test_classes.items():
            if pattern_lower in name or pattern_lower in test_class.__name__.lower():
                suite.addTests(loader.loadTestsFromTestCase(test_class))
                added = True
        
        if not added:
            print(f"경고: '{test_pattern}' 패턴에 맞는 테스트를 찾을 수 없습니다.")
            print(f"사용 가능한 테스트: {', '.join(test_classes.keys())}")
    
    return suite

def print_test_info():
    """테스트 정보 출력"""
    print("=" * 60)
    print("DOE Desktop Application - 단위 테스트")
    print("=" * 60)
    print()
    
    test_modules = [
        ("Project Controller", "프로젝트 관리 로직"),
        ("Data Controller", "데이터 입출력 로직"),
        ("Analysis Controller", "통계 분석 로직"),
        ("Chart Controller", "차트 생성 로직"),
        ("Data Utils", "데이터 처리 유틸리티"),
        ("File Utils", "파일 처리 유틸리티")
    ]
    
    print("테스트 모듈:")
    for module, description in test_modules:
        print(f"  • {module:<20} : {description}")
    print()

def run_coverage_analysis():
    """코드 커버리지 분석 (coverage 패키지가 있는 경우)"""
    try:
        import coverage
        
        print("코드 커버리지 분석을 시작합니다...")
        
        # Coverage 인스턴스 생성
        cov = coverage.Coverage()
        cov.start()
        
        # 테스트 실행
        suite = create_test_suite()
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        # Coverage 중지 및 보고서 생성
        cov.stop()
        cov.save()
        
        print("\n" + "=" * 60)
        print("코드 커버리지 보고서:")
        print("=" * 60)
        
        cov.report(show_missing=True)
        
        return result
        
    except ImportError:
        print("코드 커버리지 분석을 위해 'coverage' 패키지를 설치해주세요:")
        print("pip install coverage")
        return None

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="DOE Desktop Application 단위 테스트 실행기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python run_tests.py                    # 모든 테스트 실행
  python run_tests.py -v                 # 상세 출력으로 모든 테스트 실행
  python run_tests.py controller         # 컨트롤러 테스트만 실행
  python run_tests.py utils              # 유틸리티 테스트만 실행
  python run_tests.py --coverage         # 코드 커버리지와 함께 실행
        """
    )
    
    parser.add_argument(
        'pattern', 
        nargs='?', 
        help='실행할 테스트 패턴 (선택사항)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='상세 출력 모드'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='코드 커버리지 분석 포함'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='사용 가능한 테스트 모듈 목록 표시'
    )
    
    args = parser.parse_args()
    
    if args.list:
        print_test_info()
        return
    
    # 테스트 정보 출력
    print_test_info()
    
    # 코드 커버리지 실행
    if args.coverage:
        result = run_coverage_analysis()
        if result is not None:
            return 0 if result.wasSuccessful() else 1
    
    # 일반 테스트 실행
    suite = create_test_suite(args.pattern)
    
    if suite.countTestCases() == 0:
        print("실행할 테스트가 없습니다.")
        return 1
    
    print(f"총 {suite.countTestCases()}개의 테스트를 실행합니다.")
    print("-" * 60)
    
    # 테스트 실행
    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        buffer=True,  # 테스트 중 print 출력 캡처
        failfast=False  # 첫 번째 실패에서 중단하지 않음
    )
    
    result = runner.run(suite)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    
    print(f"총 테스트 수: {total_tests}")
    print(f"성공: {total_tests - failures - errors - skipped}")
    print(f"실패: {failures}")
    print(f"에러: {errors}")
    
    if skipped > 0:
        print(f"건너뜀: {skipped}")
    
    if result.wasSuccessful():
        print("\n✅ 모든 테스트가 성공했습니다!")
        return 0
    else:
        print("\n❌ 일부 테스트가 실패했습니다.")
        
        if failures:
            print(f"\n실패한 테스트 ({failures}개):")
            for test, traceback in result.failures:
                print(f"  • {test}")
        
        if errors:
            print(f"\n에러가 발생한 테스트 ({errors}개):")
            for test, traceback in result.errors:
                print(f"  • {test}")
        
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 