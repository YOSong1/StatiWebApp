"""
메인 윈도우 클래스
DOE 애플리케이션의 메인 사용자 인터페이스
"""

import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QToolBar, QStatusBar,
    QTreeWidget, QTreeWidgetItem, QTabWidget,
    QTableWidget, QLabel, QPushButton, QFileDialog,
    QMessageBox, QProgressBar, QFrame, QListWidgetItem,
    QDialog, QTextEdit, QGroupBox, QInputDialog, QLineEdit,
    QFormLayout, QSpinBox, QCheckBox, QDialogButtonBox, QListWidget, QComboBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont

from views.data_view import DataTableView
from views.chart_view import ChartView
from views.project_explorer import ProjectExplorer
from controllers.project_controller import ProjectController
from controllers.data_controller import DataController
from controllers.analysis_controller import AnalysisController
from controllers.chart_controller import ChartController
from controllers.design_controller import DesignController
from models.project import Project
import pandas as pd
import numpy as np

# 분석 가이드 다이얼로그 추가
try:
    from src.views.analysis_guide_dialog import AnalysisGuideDialog
except ImportError:
    AnalysisGuideDialog = None


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    # 시그널 정의
    file_opened = Signal(str)
    data_imported = Signal(object)
    analysis_requested = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # 컨트롤러 초기화
        self.project_controller = ProjectController(self)
        self.data_controller = DataController(self)
        self.analysis_controller = AnalysisController(self)
        self.chart_controller = ChartController(self)
        self.design_controller = DesignController(self)
        
        # 윈도우 기본 설정
        self.setWindowTitle("DOE Tool - 실험계획법 분석 도구")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # 중앙 위젯 설정
        self.setup_ui()
        
        # 메뉴 및 툴바 설정
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()
        
        # 이벤트 연결
        self.connect_signals()
        
        # 초기 상태 설정
        self.update_ui_state()
    
    def create_project_data(self):
        """현재 상태에서 프로젝트 데이터 생성"""
        import json
        from datetime import datetime
        
        project_data = {
            'project_info': {
                'name': getattr(self.project_explorer, 'project_name', '새 프로젝트'),
                'description': '실험계획법 분석 프로젝트',
                'created_at': datetime.now().isoformat()
            },
            'data': None,
            'analysis_results': [],
            'chart_history': [],
            'settings': {}
        }
        
        try:
            # 현재 데이터 저장
            if hasattr(self, 'data_view') and self.data_view.get_data() is not None:
                data = self.data_view.get_data()
                project_data['data'] = {
                    'dataframe': data.to_dict('records'),
                    'columns': list(data.columns),
                    'index': list(data.index),
                    'description': getattr(self.project_explorer, 'current_data_description', '데이터'),
                    'loaded_at': datetime.now().isoformat()
                }
            
            # 분석 결과 저장
            if hasattr(self.project_explorer, 'analysis_history'):
                project_data['analysis_results'] = self.project_explorer.analysis_history.copy()
            
            # 차트 히스토리 저장
            if hasattr(self.project_explorer, 'chart_history'):
                project_data['chart_history'] = self.project_explorer.chart_history.copy()
            
            # 애플리케이션 설정 저장
            project_data['settings'] = {
                'current_tab': self.tab_widget.currentIndex() if hasattr(self, 'tab_widget') else 0,
            }
            
        except Exception as e:
            print(f"프로젝트 데이터 생성 중 오류: {str(e)}")
        
        return project_data
    
    def restore_project_data(self, project_data):
        """프로젝트 데이터 복원"""
        try:
            import pandas as pd
            
            # 데이터 복원
            if project_data.get('data') and project_data['data'].get('dataframe'):
                data_dict = project_data['data']['dataframe']
                columns = project_data['data'].get('columns', [])
                
                # DataFrame 복원
                data = pd.DataFrame(data_dict)
                if columns:
                    data.columns = columns
                
                description = project_data['data'].get('description', '불러온 데이터')
                
                # 데이터 뷰에 데이터 설정
                if hasattr(self, 'data_view'):
                    self.data_view.set_data(data)
                
                # 프로젝트 탐색기에 데이터 설정
                if hasattr(self, 'project_explorer'):
                    self.project_explorer.set_data(data, description)
                
                # 결과 뷰에 데이터 설정
                if hasattr(self, 'results_view'):
                    self.results_view.set_data(data)
            
            # 분석 결과 복원
            if project_data.get('analysis_results') and hasattr(self, 'project_explorer'):
                self.project_explorer.analysis_history = project_data['analysis_results'].copy()
                
                # 분석 트리 업데이트
                self.project_explorer.analysis_tree.clear()
                for result in project_data['analysis_results']:
                    self.project_explorer.add_analysis_result(
                        result.get('type', '알 수 없음'),
                        result,
                        result.get('status', '완료')
                    )
            
            # 차트 히스토리 복원
            if project_data.get('chart_history') and hasattr(self, 'project_explorer'):
                self.project_explorer.chart_history = project_data['chart_history'].copy()
                
                # 차트 리스트 업데이트
                self.project_explorer.chart_list.clear()
                for chart_data in project_data['chart_history']:
                    # 차트 리스트에 직접 추가 (add_chart_result를 사용하지 않음)
                    timestamp = chart_data.get('timestamp', '00:00:00')
                    chart_type = chart_data.get('type', '차트')
                    
                    item = QListWidgetItem(f"[{timestamp}] {chart_type}")
                    item.setData(Qt.UserRole, chart_data)
                    self.project_explorer.chart_list.addItem(item)
            
            # 프로젝트 정보 복원
            if project_data.get('project_info') and hasattr(self, 'project_explorer'):
                project_name = project_data['project_info'].get('name', '불러온 프로젝트')
                self.project_explorer.set_project_name(project_name)
            
            # 설정 복원
            if project_data.get('settings'):
                settings = project_data['settings']
                
                # 탭 위치 복원
                if 'current_tab' in settings and hasattr(self, 'tab_widget'):
                    self.tab_widget.setCurrentIndex(settings['current_tab'])
            
            # 통계 업데이트
            if hasattr(self, 'project_explorer'):
                self.project_explorer.update_stats()
                self.project_explorer.update_analysis_summary()
            
            return True
            
        except Exception as e:
            print(f"프로젝트 데이터 복원 중 오류: {str(e)}")
            return False
    
    def setup_ui(self):
        """UI 구성 요소 설정"""
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃 (수평 분할)
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # 왼쪽 패널 - 프로젝트 탐색기
        self.setup_project_explorer()
        main_splitter.addWidget(self.project_explorer)
        
        # 오른쪽 패널 - 메인 콘텐츠 영역
        self.setup_content_area()
        main_splitter.addWidget(self.content_widget)
        
        # 분할 비율 설정 (왼쪽 20%, 오른쪽 80%)
        main_splitter.setSizes([250, 950])
    
    def setup_project_explorer(self):
        """프로젝트 탐색기 설정"""
        self.project_explorer = ProjectExplorer()
        self.project_explorer.setMaximumWidth(300)
        self.project_explorer.setMinimumWidth(200)
        
        # 시그널 연결
        self.project_explorer.data_selected.connect(self.on_project_data_selected)
        self.project_explorer.analysis_selected.connect(self.on_project_analysis_selected)
        self.project_explorer.chart_selected.connect(self.on_project_chart_selected)
    
    def on_project_data_selected(self, data):
        """프로젝트에서 데이터 선택 시"""
        if data is not None:
            self.data_view.set_data(data)
            self.tab_widget.setCurrentWidget(self.data_view)
    
    def on_project_analysis_selected(self, analysis_type, result):
        """프로젝트에서 분석 결과 선택 시"""
        self.results_view.add_analysis_result(analysis_type, result)
        self.tab_widget.setCurrentWidget(self.results_view)
    
    def on_project_chart_selected(self, chart_info):
        """프로젝트에서 차트 선택 시"""
        self.chart_view.display_chart(chart_info)
        self.tab_widget.setCurrentWidget(self.chart_view)
    
    def on_chart_updated(self):
        """차트 업데이트 시"""
        if hasattr(self, 'project_explorer'):
            # 현재 차트 뷰의 정보를 가져와서 프로젝트 탐색기에 전달
            chart_info = self.chart_view.get_current_chart_info()
            if chart_info:
                # 차트 히스토리에 추가
                self.project_explorer.add_chart_result(
                    chart_info.get('type', '차트'), 
                    chart_info,
                    chart_info.get('description', '')
                )
                
                # 프로젝트 상태 변경
                if self.project_controller.current_project:
                    self.project_controller.current_project.is_dirty = True

    def setup_content_area(self):
        """메인 콘텐츠 영역 설정"""
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        content_layout.addWidget(self.tab_widget)
        
        # 데이터 뷰 탭
        self.data_view = DataTableView()
        self.tab_widget.addTab(self.data_view, "데이터")
        
        # 차트 뷰 탭
        self.chart_view = ChartView()
        self.chart_view.chart_updated.connect(self.on_chart_updated)
        self.tab_widget.addTab(self.chart_view, "차트")
        
        # 결과 뷰 탭 - 새로운 ResultsView 사용
        from views.results_view import ResultsView
        self.results_view = ResultsView()
        self.tab_widget.addTab(self.results_view, "결과")
    
    def setup_menus(self):
        """메뉴바 설정"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")
        
        # 새 프로젝트
        self.new_action = QAction("새 프로젝트(&N)", self)
        self.new_action.setShortcut(QKeySequence.New)
        self.new_action.setStatusTip("새 프로젝트를 생성합니다")
        self.new_action.triggered.connect(self.project_controller.new_project)
        file_menu.addAction(self.new_action)
        
        # 프로젝트 열기
        self.open_action = QAction("프로젝트 열기(&O)", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.setStatusTip("기존 프로젝트를 엽니다")
        self.open_action.triggered.connect(self.project_controller.open_project)
        file_menu.addAction(self.open_action)
        
        # 프로젝트 저장
        self.save_action = QAction("프로젝트 저장(&S)", self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.setStatusTip("현재 프로젝트를 저장합니다")
        self.save_action.triggered.connect(self.project_controller.save_project)
        file_menu.addAction(self.save_action)
        
        # 다른 이름으로 저장
        self.save_as_action = QAction("다른 이름으로 저장(&A)", self)
        self.save_as_action.setShortcut(QKeySequence.SaveAs)
        self.save_as_action.setStatusTip("프로젝트를 다른 이름으로 저장합니다")
        self.save_as_action.triggered.connect(self.project_controller.save_project_as)
        file_menu.addAction(self.save_as_action)
        
        file_menu.addSeparator()
        
        # 데이터 가져오기
        self.import_action = QAction("데이터 가져오기(&I)", self)
        self.import_action.setShortcut("Ctrl+I")
        self.import_action.setStatusTip("CSV, Excel 파일에서 데이터를 가져옵니다")
        self.import_action.triggered.connect(self.data_controller.import_data)
        file_menu.addAction(self.import_action)
        
        # 데이터 내보내기
        self.export_action = QAction("데이터 내보내기(&E)", self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.setStatusTip("데이터를 파일로 내보냅니다")
        self.export_action.triggered.connect(self.export_current_data)
        file_menu.addAction(self.export_action)
        
        file_menu.addSeparator()
        
        # 종료
        self.exit_action = QAction("종료(&X)", self)
        self.exit_action.setShortcut(QKeySequence.Quit)
        self.exit_action.setStatusTip("애플리케이션을 종료합니다")
        self.exit_action.triggered.connect(self.close)
        file_menu.addAction(self.exit_action)
        
        # 데이터 메뉴
        data_menu = menubar.addMenu("데이터(&D)")
        
        # 데이터 입출력 서브메뉴
        io_menu = data_menu.addMenu("데이터 입출력")
        
        # 데이터 가져오기 (파일 메뉴와 동일한 기능)
        self.import_data_action2 = QAction("데이터 가져오기(&I)", self)
        self.import_data_action2.setShortcut("Ctrl+Shift+I")
        self.import_data_action2.setStatusTip("CSV, Excel 파일에서 데이터를 가져옵니다")
        self.import_data_action2.triggered.connect(self.data_controller.import_data)
        io_menu.addAction(self.import_data_action2)
        
        # 데이터 내보내기 (파일 메뉴와 동일한 기능)
        self.export_data_action2 = QAction("데이터 내보내기(&E)", self)
        self.export_data_action2.setShortcut("Ctrl+Shift+E")
        self.export_data_action2.setStatusTip("데이터를 파일로 내보냅니다")
        self.export_data_action2.triggered.connect(self.export_current_data)
        io_menu.addAction(self.export_data_action2)
        
        io_menu.addSeparator()
        
        # 클립보드 작업
        self.copy_data_action = QAction("클립보드로 복사(&C)", self)
        self.copy_data_action.setShortcut("Ctrl+Shift+C")
        self.copy_data_action.setStatusTip("선택된 데이터를 클립보드로 복사합니다")
        self.copy_data_action.triggered.connect(self.copy_data_to_clipboard)
        io_menu.addAction(self.copy_data_action)
        
        self.paste_data_action = QAction("클립보드에서 붙여넣기(&V)", self)
        self.paste_data_action.setShortcut("Ctrl+Shift+V")
        self.paste_data_action.setStatusTip("클립보드에서 데이터를 붙여넣습니다")
        self.paste_data_action.triggered.connect(self.paste_data_from_clipboard)
        io_menu.addAction(self.paste_data_action)
        
        # 데이터베이스 연결
        self.connect_db_action = QAction("데이터베이스 연결(&D)", self)
        self.connect_db_action.setStatusTip("데이터베이스에서 데이터를 가져옵니다")
        self.connect_db_action.triggered.connect(self.connect_to_database)
        io_menu.addAction(self.connect_db_action)
        
        # 데이터 편집 서브메뉴
        edit_menu = data_menu.addMenu("데이터 편집")
        
        # 데이터 편집 모드
        self.edit_data_action = QAction("데이터 편집 모드(&E)", self)
        self.edit_data_action.setStatusTip("데이터 편집 모드로 전환합니다")
        self.edit_data_action.triggered.connect(self.edit_data)
        edit_menu.addAction(self.edit_data_action)
        
        edit_menu.addSeparator()
        
        # 행/열 관리
        self.insert_row_action = QAction("행 삽입(&R)", self)
        self.insert_row_action.setStatusTip("선택된 위치에 새 행을 삽입합니다")
        self.insert_row_action.triggered.connect(self.insert_row)
        edit_menu.addAction(self.insert_row_action)
        
        self.delete_row_action = QAction("행 삭제(&D)", self)
        self.delete_row_action.setStatusTip("선택된 행을 삭제합니다")
        self.delete_row_action.triggered.connect(self.delete_row)
        edit_menu.addAction(self.delete_row_action)
        
        self.insert_column_action = QAction("열 삽입(&C)", self)
        self.insert_column_action.setStatusTip("선택된 위치에 새 열을 삽입합니다")
        self.insert_column_action.triggered.connect(self.insert_column)
        edit_menu.addAction(self.insert_column_action)
        
        self.delete_column_action = QAction("열 삭제(&L)", self)
        self.delete_column_action.setStatusTip("선택된 열을 삭제합니다")
        self.delete_column_action.triggered.connect(self.delete_column)
        edit_menu.addAction(self.delete_column_action)
        
        edit_menu.addSeparator()
        
        # 데이터 정렬
        self.sort_ascending_action = QAction("오름차순 정렬(&A)", self)
        self.sort_ascending_action.setStatusTip("선택된 열을 오름차순으로 정렬합니다")
        self.sort_ascending_action.triggered.connect(self.sort_ascending)
        edit_menu.addAction(self.sort_ascending_action)
        
        self.sort_descending_action = QAction("내림차순 정렬(&S)", self)
        self.sort_descending_action.setStatusTip("선택된 열을 내림차순으로 정렬합니다")
        self.sort_descending_action.triggered.connect(self.sort_descending)
        edit_menu.addAction(self.sort_descending_action)
        
        # 찾기/바꾸기
        self.find_replace_action = QAction("찾기/바꾸기(&F)", self)
        self.find_replace_action.setShortcut("Ctrl+H")
        self.find_replace_action.setStatusTip("데이터에서 값을 찾고 바꿉니다")
        self.find_replace_action.triggered.connect(self.find_replace_data)
        edit_menu.addAction(self.find_replace_action)
        
        # 데이터 변환 서브메뉴
        transform_menu = data_menu.addMenu("데이터 변환")
        
        # 변수 관리
        self.rename_variables_action = QAction("변수명 변경(&R)", self)
        self.rename_variables_action.setStatusTip("변수(열) 이름을 변경합니다")
        self.rename_variables_action.triggered.connect(self.rename_variables)
        transform_menu.addAction(self.rename_variables_action)
        
        self.change_data_types_action = QAction("데이터 타입 변경(&T)", self)
        self.change_data_types_action.setStatusTip("변수의 데이터 타입을 변경합니다")
        self.change_data_types_action.triggered.connect(self.change_data_types)
        transform_menu.addAction(self.change_data_types_action)
        
        transform_menu.addSeparator()
        
        # 파생변수 생성
        self.create_derived_variable_action = QAction("파생변수 생성(&D)", self)
        self.create_derived_variable_action.setStatusTip("기존 변수를 이용해 새로운 변수를 생성합니다")
        self.create_derived_variable_action.triggered.connect(self.create_derived_variable)
        transform_menu.addAction(self.create_derived_variable_action)
        
        # 더미변수 생성
        self.create_dummy_variables_action = QAction("더미변수 생성(&U)", self)
        self.create_dummy_variables_action.setStatusTip("범주형 변수를 더미변수로 변환합니다")
        self.create_dummy_variables_action.triggered.connect(self.create_dummy_variables)
        transform_menu.addAction(self.create_dummy_variables_action)
        
        transform_menu.addSeparator()
        
        # 데이터 병합/분할
        self.merge_data_action = QAction("데이터 병합(&M)", self)
        self.merge_data_action.setStatusTip("다른 데이터와 병합합니다")
        self.merge_data_action.triggered.connect(self.merge_data)
        transform_menu.addAction(self.merge_data_action)
        
        self.split_data_action = QAction("데이터 분할(&S)", self)
        self.split_data_action.setStatusTip("데이터를 조건에 따라 분할합니다")
        self.split_data_action.triggered.connect(self.split_data)
        transform_menu.addAction(self.split_data_action)
        
        # 데이터 품질 서브메뉴
        quality_menu = data_menu.addMenu("데이터 품질")
        
        # 결측값 처리 (도구 메뉴에서 이동)
        self.handle_missing_action2 = QAction("결측값 처리(&M)", self)
        self.handle_missing_action2.setStatusTip("결측값을 처리합니다")
        self.handle_missing_action2.triggered.connect(self.handle_missing_values)
        quality_menu.addAction(self.handle_missing_action2)
        
        # 이상값 탐지 (도구 메뉴에서 이동)
        self.detect_outliers_action2 = QAction("이상값 탐지(&O)", self)
        self.detect_outliers_action2.setStatusTip("데이터의 이상값을 탐지합니다")
        self.detect_outliers_action2.triggered.connect(self.detect_outliers)
        quality_menu.addAction(self.detect_outliers_action2)
        
        # 중복값 제거
        self.remove_duplicates_action = QAction("중복값 제거(&D)", self)
        self.remove_duplicates_action.setStatusTip("중복된 행을 제거합니다")
        self.remove_duplicates_action.triggered.connect(self.remove_duplicates)
        quality_menu.addAction(self.remove_duplicates_action)
        
        # 데이터 검증 (도구 메뉴에서 이동)
        
        # 데이터 뷰 서브메뉴
        view_menu = data_menu.addMenu("데이터 뷰")
        
        # 데이터 요약 정보
        self.data_summary_action = QAction("데이터 요약 정보(&S)", self)
        self.data_summary_action.setStatusTip("데이터의 기본 정보를 표시합니다")
        self.data_summary_action.triggered.connect(self.show_data_summary)
        view_menu.addAction(self.data_summary_action)
        
        # 변수 정보
        self.variable_info_action = QAction("변수 정보(&V)", self)
        self.variable_info_action.setStatusTip("각 변수의 상세 정보를 표시합니다")
        self.variable_info_action.triggered.connect(self.show_variable_info)
        view_menu.addAction(self.variable_info_action)
        
        # 데이터 미리보기
        self.data_preview_action = QAction("데이터 미리보기(&P)", self)
        self.data_preview_action.setStatusTip("데이터의 처음과 마지막 부분을 미리봅니다")
        self.data_preview_action.triggered.connect(self.show_data_preview)
        view_menu.addAction(self.data_preview_action)
        
        view_menu.addSeparator()
        
        # 필터 설정
        self.set_filter_action = QAction("필터 설정(&F)", self)
        self.set_filter_action.setStatusTip("데이터 필터를 설정합니다")
        self.set_filter_action.triggered.connect(self.set_data_filter)
        view_menu.addAction(self.set_filter_action)
        
        # 필터 해제
        self.clear_filter_action = QAction("필터 해제(&C)", self)
        self.clear_filter_action.setStatusTip("설정된 필터를 해제합니다")
        self.clear_filter_action.triggered.connect(self.clear_data_filter)
        
        # DOE 메뉴
        doe_menu = menubar.addMenu("실험설계(&O)")
        
        # 스크리닝 설계 서브메뉴
        screening_menu = doe_menu.addMenu("스크리닝 설계")
        
        # 완전요인설계
        self.full_factorial_action = QAction("완전요인설계(&F)", self)
        self.full_factorial_action.setStatusTip("모든 인수의 모든 수준 조합을 생성합니다")
        self.full_factorial_action.triggered.connect(self.create_full_factorial_design)
        screening_menu.addAction(self.full_factorial_action)
        
        # 부분요인설계
        self.fractional_factorial_action = QAction("부분요인설계(&R)", self)
        self.fractional_factorial_action.setStatusTip("완전요인설계의 일부분을 선택하여 생성합니다")
        self.fractional_factorial_action.triggered.connect(self.create_fractional_factorial_design)
        screening_menu.addAction(self.fractional_factorial_action)
        
        # Plackett-Burman 설계
        self.plackett_burman_action = QAction("Plackett-Burman 설계(&P)", self)
        self.plackett_burman_action.setStatusTip("많은 인수를 효율적으로 스크리닝합니다")
        self.plackett_burman_action.triggered.connect(self.create_plackett_burman_design)
        screening_menu.addAction(self.plackett_burman_action)
        
        # 최적화 설계 서브메뉴
        optimization_menu = doe_menu.addMenu("최적화 설계")
        
        # 반응표면설계
        self.rsm_action = QAction("반응표면설계(RSM)(&S)", self)
        self.rsm_action.setStatusTip("반응표면을 모델링하여 최적점을 찾습니다")
        self.rsm_action.triggered.connect(self.create_rsm_design)
        optimization_menu.addAction(self.rsm_action)
        
        # Box-Behnken 설계
        self.box_behnken_action = QAction("Box-Behnken 설계(&B)", self)
        self.box_behnken_action.setStatusTip("3수준 반응표면설계를 생성합니다")
        self.box_behnken_action.triggered.connect(self.create_box_behnken_design)
        optimization_menu.addAction(self.box_behnken_action)
        
        # 중심합성설계
        self.ccd_action = QAction("중심합성설계(CCD)(&C)", self)
        self.ccd_action.setStatusTip("중심점과 축점을 포함한 반응표면설계를 생성합니다")
        self.ccd_action.triggered.connect(self.create_ccd_design)
        optimization_menu.addAction(self.ccd_action)
        
        # 견고성 설계 서브메뉴
        robustness_menu = doe_menu.addMenu("견고성 설계")
        
        # 직교배열설계
        self.orthogonal_array_action = QAction("직교배열설계(&O)", self)
        self.orthogonal_array_action.setStatusTip("직교배열을 이용한 실험설계를 생성합니다")
        self.orthogonal_array_action.triggered.connect(self.create_orthogonal_array_design)
        robustness_menu.addAction(self.orthogonal_array_action)
        
        # 다구치설계
        self.taguchi_action = QAction("다구치설계(&T)", self)
        self.taguchi_action.setStatusTip("품질공학 기반의 견고한 설계를 생성합니다")
        self.taguchi_action.triggered.connect(self.create_taguchi_design)
        robustness_menu.addAction(self.taguchi_action)
        
        # 특수 설계 서브메뉴
        special_menu = doe_menu.addMenu("특수 설계")
        
        # 혼합설계
        self.mixture_action = QAction("혼합설계(&M)", self)
        self.mixture_action.setStatusTip("성분의 합이 일정한 혼합물 실험을 설계합니다")
        self.mixture_action.triggered.connect(self.create_mixture_design)
        special_menu.addAction(self.mixture_action)
        
        # 분할구설계
        self.split_plot_action = QAction("분할구설계(&S)", self)
        self.split_plot_action.setStatusTip("제약조건이 있는 인수들을 고려한 설계를 생성합니다")
        self.split_plot_action.triggered.connect(self.create_split_plot_design)
        special_menu.addAction(self.split_plot_action)
        
        doe_menu.addSeparator()
        
        # 사용자 정의 설계
        self.custom_design_action = QAction("사용자 정의 설계(&U)", self)
        self.custom_design_action.setStatusTip("사용자가 직접 실험점을 정의합니다")
        self.custom_design_action.triggered.connect(self.create_custom_design)
        doe_menu.addAction(self.custom_design_action)
        
        # 분석/해석 메뉴 (DOE와 일반 분석을 명확히 분리)
        analysis_menu = menubar.addMenu("분석/해석(&A)")

        # DOE 분석 서브메뉴
        doe_analysis_menu = analysis_menu.addMenu("DOE 분석")
        # DOE 분석 - 스크리닝
        doe_screening_menu = doe_analysis_menu.addMenu("스크리닝 분석")

        # 기본 DOE ANOVA (통합)
        self.doe_anova_action = QAction("완전요인 ANOVA", self)
        self.doe_anova_action.setStatusTip("현재 데이터에서 반응/요인을 선택해 완전요인 ANOVA를 실행합니다.")
        self.doe_anova_action.triggered.connect(self.run_doe_anova_dialog)
        doe_screening_menu.addAction(self.doe_anova_action)

        self.doe_fractional_action = QAction("부분요인 ANOVA", self)
        self.doe_fractional_action.setStatusTip("부분요인설계 데이터에 대해 해석 가능한 효과로 ANOVA를 수행합니다.")
        self.doe_fractional_action.triggered.connect(self.run_fractional_factorial_anova)
        doe_screening_menu.addAction(self.doe_fractional_action)

        self.doe_plackett_action = QAction("Plackett-Burman 분석", self)
        self.doe_plackett_action.setStatusTip("Plackett-Burman 스크리닝 설계에 대한 주효과 분석을 수행합니다.")
        self.doe_plackett_action.triggered.connect(self.run_plackett_burman_analysis)
        doe_screening_menu.addAction(self.doe_plackett_action)

        # DOE 분석 - 최적화
        doe_optimization_menu = doe_analysis_menu.addMenu("최적화 분석")
        self.doe_rsm_action = QAction("반응표면분석 (RSM)", self)
        self.doe_rsm_action.setStatusTip("반응표면설계/중심합성/Box-Behnken 데이터로 2차 모델을 적합합니다.")
        self.doe_rsm_action.triggered.connect(self.run_rsm_analysis)
        doe_optimization_menu.addAction(self.doe_rsm_action)

        self.doe_box_behnken_action = QAction("Box-Behnken 분석", self)
        self.doe_box_behnken_action.setStatusTip("Box-Behnken 설계 데이터에 대한 2차 회귀/최적화 분석을 수행합니다.")
        self.doe_box_behnken_action.triggered.connect(self.run_box_behnken_analysis)
        doe_optimization_menu.addAction(self.doe_box_behnken_action)

        self.doe_ccd_action = QAction("중심합성설계(CCD) 분석", self)
        self.doe_ccd_action.setStatusTip("CCD 설계 데이터에 대한 2차 회귀/최적화 분석을 수행합니다.")
        self.doe_ccd_action.triggered.connect(self.run_ccd_analysis)
        doe_optimization_menu.addAction(self.doe_ccd_action)

        # DOE 분석 - 견고성/직교배열
        doe_robust_menu = doe_analysis_menu.addMenu("견고성/직교배열 분석")
        self.doe_orthogonal_action = QAction("직교배열 분석", self)
        self.doe_orthogonal_action.setStatusTip("직교배열 설계에 대한 주효과/SN비 분석을 수행합니다.")
        self.doe_orthogonal_action.triggered.connect(self.run_orthogonal_analysis)
        doe_robust_menu.addAction(self.doe_orthogonal_action)

        self.doe_taguchi_action = QAction("다구치(S/N) 분석", self)
        self.doe_taguchi_action.setStatusTip("다구치 설계에 대한 S/N비 및 주효과 분석을 수행합니다.")
        self.doe_taguchi_action.triggered.connect(self.run_taguchi_analysis)
        doe_robust_menu.addAction(self.doe_taguchi_action)

        # DOE 분석 - 특수/기타
        doe_special_menu = doe_analysis_menu.addMenu("특수/기타 분석")
        self.doe_mixture_action = QAction("혼합 설계 분석", self)
        self.doe_mixture_action.setStatusTip("혼합물 설계 데이터에 대한 전용 모델 분석을 수행합니다.")
        self.doe_mixture_action.triggered.connect(self.run_mixture_analysis)
        doe_special_menu.addAction(self.doe_mixture_action)

        self.doe_split_plot_action = QAction("분할구 설계 분석", self)
        self.doe_split_plot_action.setStatusTip("분할구 설계 데이터에 대한 적합한 분석을 수행합니다.")
        self.doe_split_plot_action.triggered.connect(self.run_split_plot_analysis)
        doe_special_menu.addAction(self.doe_split_plot_action)

        doe_special_menu.addSeparator()

        self.doe_custom_action = QAction("사용자 정의 DOE 분석", self)
        self.doe_custom_action.setStatusTip("사용자 정의 설계/분석 흐름을 실행합니다.")
        self.doe_custom_action.triggered.connect(lambda: self.show_doe_analysis_placeholder("사용자 정의 DOE 분석"))
        doe_special_menu.addAction(self.doe_custom_action)

        analysis_menu.addSeparator()

        # 일반 분석 서브메뉴
        general_analysis_menu = analysis_menu.addMenu("일반 분석")

        # 기초 통계
        self.basic_stats_action = QAction("기초 통계(&B)", self)
        self.basic_stats_action.setStatusTip("기초 통계량을 계산합니다")
        self.basic_stats_action.triggered.connect(self.basic_statistics)
        general_analysis_menu.addAction(self.basic_stats_action)
        
        general_analysis_menu.addSeparator()
        
        # 분산분석 서브메뉴
        anova_menu = general_analysis_menu.addMenu("분산분석")
        
        # 일원분산분석
        self.one_way_anova_action = QAction("일원분산분석(&O)", self)
        self.one_way_anova_action.setStatusTip("하나의 인수에 대한 분산분석을 수행합니다")
        self.one_way_anova_action.triggered.connect(self.run_one_way_anova_request)
        anova_menu.addAction(self.one_way_anova_action)
        
        # 이원분산분석
        self.two_way_anova_action = QAction("이원분산분석(&T)", self)
        self.two_way_anova_action.setStatusTip("두 개의 인수에 대한 분산분석을 수행합니다")
        self.two_way_anova_action.triggered.connect(self.run_two_way_anova_request)
        anova_menu.addAction(self.two_way_anova_action)
        
        # 다원분산분석
        self.multi_way_anova_action = QAction("다원분산분석(&M)", self)
        self.multi_way_anova_action.setStatusTip("여러 인수에 대한 분산분석을 수행합니다")
        self.multi_way_anova_action.triggered.connect(self.run_multi_way_anova)
        anova_menu.addAction(self.multi_way_anova_action)
        
        # 반복측정분산분석
        self.repeated_anova_action = QAction("반복측정분산분석(&R)", self)
        self.repeated_anova_action.setStatusTip("반복측정 데이터에 대한 분산분석을 수행합니다")
        self.repeated_anova_action.triggered.connect(self.run_repeated_anova)
        anova_menu.addAction(self.repeated_anova_action)
        
        # 회귀분석 서브메뉴
        regression_menu = general_analysis_menu.addMenu("회귀분석")
        
        # 단순회귀분석
        self.simple_regression_action = QAction("단순회귀분석(&S)", self)
        self.simple_regression_action.setStatusTip("하나의 독립변수에 대한 회귀분석을 수행합니다")
        self.simple_regression_action.triggered.connect(self.run_simple_regression)
        regression_menu.addAction(self.simple_regression_action)
        
        # 다중회귀분석
        self.multiple_regression_action = QAction("다중회귀분석(&M)", self)
        self.multiple_regression_action.setStatusTip("여러 독립변수에 대한 회귀분석을 수행합니다")
        self.multiple_regression_action.triggered.connect(self.run_multiple_regression)
        regression_menu.addAction(self.multiple_regression_action)
        
        # 단계적회귀분석
        self.stepwise_regression_action = QAction("단계적회귀분석(&T)", self)
        self.stepwise_regression_action.setStatusTip("변수 선택을 통한 회귀분석을 수행합니다")
        self.stepwise_regression_action.triggered.connect(self.run_stepwise_regression)
        regression_menu.addAction(self.stepwise_regression_action)
        
        # 비선형회귀분석
        self.nonlinear_regression_action = QAction("비선형회귀분석(&N)", self)
        self.nonlinear_regression_action.setStatusTip("비선형 모델에 대한 회귀분석을 수행합니다")
        self.nonlinear_regression_action.triggered.connect(self.run_nonlinear_regression)
        regression_menu.addAction(self.nonlinear_regression_action)
        
        # 상관분석
        self.correlation_action = QAction("상관분석(&C)", self)
        self.correlation_action.setStatusTip("변수 간의 상관관계를 분석합니다")
        self.correlation_action.triggered.connect(self.run_correlation_analysis)
        general_analysis_menu.addAction(self.correlation_action)
        
        # 비모수검정 서브메뉴
        nonparametric_menu = general_analysis_menu.addMenu("비모수검정")
        
        # Mann-Whitney U 검정
        self.mann_whitney_action = QAction("Mann-Whitney U 검정(&U)", self)
        self.mann_whitney_action.setStatusTip("두 독립표본의 중위수 차이를 검정합니다")
        self.mann_whitney_action.triggered.connect(self.run_mann_whitney_test)
        nonparametric_menu.addAction(self.mann_whitney_action)
        
        # Kruskal-Wallis 검정
        self.kruskal_wallis_action = QAction("Kruskal-Wallis 검정(&K)", self)
        self.kruskal_wallis_action.setStatusTip("여러 독립표본의 중위수 차이를 검정합니다")
        self.kruskal_wallis_action.triggered.connect(self.run_kruskal_wallis_test)
        nonparametric_menu.addAction(self.kruskal_wallis_action)
        
        # Wilcoxon 부호순위 검정
        self.wilcoxon_action = QAction("Wilcoxon 부호순위 검정(&W)", self)
        self.wilcoxon_action.setStatusTip("대응표본의 중위수 차이를 검정합니다")
        self.wilcoxon_action.triggered.connect(self.run_wilcoxon_test)
        nonparametric_menu.addAction(self.wilcoxon_action)
        
        # 다변량분석 서브메뉴
        multivariate_menu = general_analysis_menu.addMenu("다변량분석")
        
        # 주성분분석
        self.pca_action = QAction("주성분분석(PCA)(&P)", self)
        self.pca_action.setStatusTip("차원축소를 통한 주성분분석을 수행합니다")
        self.pca_action.triggered.connect(self.run_pca_analysis)
        multivariate_menu.addAction(self.pca_action)
        
        # 군집분석
        self.cluster_action = QAction("군집분석(&C)", self)
        self.cluster_action.setStatusTip("데이터의 군집구조를 분석합니다")
        self.cluster_action.triggered.connect(self.run_cluster_analysis)
        multivariate_menu.addAction(self.cluster_action)
        
        # 판별분석
        self.discriminant_action = QAction("판별분석(&D)", self)
        self.discriminant_action.setStatusTip("그룹 분류를 위한 판별분석을 수행합니다")
        self.discriminant_action.triggered.connect(self.run_discriminant_analysis)
        multivariate_menu.addAction(self.discriminant_action)
        
        analysis_menu.addSeparator()
        
        # 종합분석실행 (기존 기능 유지)
        self.comprehensive_analysis_action = QAction("종합분석실행(&A)", self)
        self.comprehensive_analysis_action.setStatusTip("모든 적용 가능한 분석을 자동으로 실행합니다")
        self.comprehensive_analysis_action.triggered.connect(self.run_analysis)
        analysis_menu.addAction(self.comprehensive_analysis_action)
        
        # 차트 메뉴
        chart_menu = menubar.addMenu("차트(&C)")
        
        # 기본 차트
        basic_chart_menu = chart_menu.addMenu("기본 차트")
        
        # 산점도
        self.scatter_plot_action = QAction("산점도(&S)", self)
        self.scatter_plot_action.setStatusTip("두 변수 간의 관계를 산점도로 표시합니다")
        self.scatter_plot_action.triggered.connect(self.create_scatter_plot)
        basic_chart_menu.addAction(self.scatter_plot_action)
        
        # 히스토그램
        self.histogram_action = QAction("히스토그램(&H)", self)
        self.histogram_action.setStatusTip("변수의 분포를 히스토그램으로 표시합니다")
        self.histogram_action.triggered.connect(self.create_histogram)
        basic_chart_menu.addAction(self.histogram_action)
        
        # 박스플롯
        self.boxplot_action = QAction("박스플롯(&B)", self)
        self.boxplot_action.setStatusTip("변수의 분포와 이상값을 박스플롯으로 표시합니다")
        self.boxplot_action.triggered.connect(self.create_boxplot)
        basic_chart_menu.addAction(self.boxplot_action)
        
        # 선 그래프
        self.line_plot_action = QAction("선 그래프(&L)", self)
        self.line_plot_action.setStatusTip("시계열 데이터를 선 그래프로 표시합니다")
        self.line_plot_action.triggered.connect(self.create_line_plot)
        basic_chart_menu.addAction(self.line_plot_action)
        
        # 막대 그래프
        self.bar_plot_action = QAction("막대 그래프(&R)", self)
        self.bar_plot_action.setStatusTip("범주형 데이터를 막대 그래프로 표시합니다")
        self.bar_plot_action.triggered.connect(self.create_bar_plot)
        basic_chart_menu.addAction(self.bar_plot_action)
        
        # DOE 전용 차트
        doe_chart_menu = chart_menu.addMenu("DOE 차트")
        
        # 주효과도
        self.main_effects_action = QAction("주효과도(&M)", self)
        self.main_effects_action.setStatusTip("각 인수의 주효과를 시각화합니다")
        self.main_effects_action.triggered.connect(self.create_main_effects_plot)
        doe_chart_menu.addAction(self.main_effects_action)
        
        # 상호작용도
        self.interaction_plot_action = QAction("상호작용도(&I)", self)
        self.interaction_plot_action.setStatusTip("인수 간의 상호작용을 시각화합니다")
        self.interaction_plot_action.triggered.connect(self.create_interaction_plot)
        doe_chart_menu.addAction(self.interaction_plot_action)
        
        # 잔차도
        self.residual_plot_action = QAction("잔차도(&R)", self)
        self.residual_plot_action.setStatusTip("회귀모델의 잔차를 시각화합니다")
        self.residual_plot_action.triggered.connect(self.create_residual_plot)
        doe_chart_menu.addAction(self.residual_plot_action)
        
        # 등고선도
        self.contour_plot_action = QAction("등고선도(&C)", self)
        self.contour_plot_action.setStatusTip("반응표면을 등고선으로 시각화합니다")
        self.contour_plot_action.triggered.connect(self.create_contour_plot)
        doe_chart_menu.addAction(self.contour_plot_action)
        
        # 3D 표면도
        self.surface_plot_action = QAction("3D 표면도(&3)", self)
        self.surface_plot_action.setStatusTip("반응표면을 3D로 시각화합니다")
        self.surface_plot_action.triggered.connect(self.create_surface_plot)
        doe_chart_menu.addAction(self.surface_plot_action)
        
        # 파레토 차트
        self.pareto_chart_action = QAction("파레토 차트(&P)", self)
        self.pareto_chart_action.setStatusTip("효과의 크기를 파레토 차트로 표시합니다")
        self.pareto_chart_action.triggered.connect(self.create_pareto_chart)
        doe_chart_menu.addAction(self.pareto_chart_action)
        
        # 진단 차트
        diagnostic_chart_menu = chart_menu.addMenu("진단 차트")
        
        # 정규확률도
        self.normal_plot_action = QAction("정규확률도(&N)", self)
        self.normal_plot_action.setStatusTip("데이터의 정규성을 확인하는 Q-Q 플롯을 생성합니다")
        self.normal_plot_action.triggered.connect(self.create_normal_plot)
        diagnostic_chart_menu.addAction(self.normal_plot_action)
        
        # 상관행렬 히트맵
        self.correlation_heatmap_action = QAction("상관행렬 히트맵(&H)", self)
        self.correlation_heatmap_action.setStatusTip("변수 간 상관관계를 히트맵으로 표시합니다")
        self.correlation_heatmap_action.triggered.connect(self.create_correlation_heatmap)
        diagnostic_chart_menu.addAction(self.correlation_heatmap_action)
        
        chart_menu.addSeparator()
        
        # 차트 관리
        self.clear_charts_action = QAction("모든 차트 지우기(&A)", self)
        self.clear_charts_action.setStatusTip("생성된 모든 차트를 지웁니다")
        self.clear_charts_action.triggered.connect(self.clear_all_charts)
        chart_menu.addAction(self.clear_charts_action)
        
        # 도구 메뉴
        tools_menu = menubar.addMenu("도구(&T)")
        
        # 설정
        self.preferences_action = QAction("설정(&P)", self)
        self.preferences_action.setStatusTip("애플리케이션 설정을 변경합니다")
        self.preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(self.preferences_action)
        
        tools_menu.addSeparator()
        
        # 데이터 변환
        transform_menu = tools_menu.addMenu("데이터 변환")
        
        # 로그 변환
        self.log_transform_action = QAction("로그 변환(&L)", self)
        self.log_transform_action.setStatusTip("선택된 변수에 로그 변환을 적용합니다")
        self.log_transform_action.triggered.connect(self.apply_log_transform)
        transform_menu.addAction(self.log_transform_action)
        
        # 표준화
        self.standardize_action = QAction("표준화(&S)", self)
        self.standardize_action.setStatusTip("선택된 변수를 표준화합니다")
        self.standardize_action.triggered.connect(self.apply_standardization)
        transform_menu.addAction(self.standardize_action)
        
        # 정규화
        self.normalize_action = QAction("정규화(&N)", self)
        self.normalize_action.setStatusTip("선택된 변수를 정규화합니다")
        self.normalize_action.triggered.connect(self.apply_normalization)
        transform_menu.addAction(self.normalize_action)
        
        # 데이터 품질
        quality_menu = tools_menu.addMenu("데이터 품질")
        
        # 결측값 처리
        self.handle_missing_action = QAction("결측값 처리(&M)", self)
        self.handle_missing_action.setStatusTip("결측값을 처리합니다")
        self.handle_missing_action.triggered.connect(self.handle_missing_values)
        quality_menu.addAction(self.handle_missing_action)
        
        # 이상값 탐지
        self.detect_outliers_action = QAction("이상값 탐지(&O)", self)
        self.detect_outliers_action.setStatusTip("데이터의 이상값을 탐지합니다")
        self.detect_outliers_action.triggered.connect(self.detect_outliers)
        quality_menu.addAction(self.detect_outliers_action)
        
        # 데이터 검증
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")
        
        # 정보
        self.about_action = QAction("정보(&A)", self)
        self.about_action.setStatusTip("애플리케이션 정보를 표시합니다")
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)
    
    def setup_toolbar(self):
        """툴바 설정"""
        toolbar = self.addToolBar("메인")
        toolbar.setMovable(False)
        
        # 새 프로젝트
        toolbar.addAction(self.new_action)
        
        # 프로젝트 열기
        toolbar.addAction(self.open_action)
        
        toolbar.addSeparator()
        
        # 데이터 가져오기
        toolbar.addAction(self.import_action)
        
        # 데이터 내보내기
        toolbar.addAction(self.export_action)
        
        toolbar.addSeparator()
        
        # 분석 실행 버튼
        self.run_analysis_btn = QPushButton("분석 실행")
        self.run_analysis_btn.setStatusTip("선택된 분석을 실행합니다")
        self.run_analysis_btn.clicked.connect(self.run_analysis)
        toolbar.addWidget(self.run_analysis_btn)
        
        # 분석 중지 버튼
        self.stop_analysis_btn = QPushButton("중지")
        self.stop_analysis_btn.setStatusTip("실행 중인 분석을 중지합니다")
        self.stop_analysis_btn.setEnabled(False)
        self.stop_analysis_btn.clicked.connect(self.stop_analysis)
        toolbar.addWidget(self.stop_analysis_btn)
    
    def setup_statusbar(self):
        """상태바 설정"""
        self.status_bar = self.statusBar()
        
        # 상태 레이블
        self.status_label = QLabel("준비")
        self.status_bar.addWidget(self.status_label)
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 메모리 사용량 표시
        self.memory_label = QLabel("메모리: N/A")
        self.status_bar.addPermanentWidget(self.memory_label)
        
        # 메모리 사용량 업데이트 타이머
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_memory_usage)
        self.timer.start(5000)  # 5초마다 업데이트
    
    def connect_signals(self):
        """시그널 연결"""
        # 탭 변경 시그널
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 데이터 뷰 시그널
        self.data_view.data_changed.connect(self.on_data_changed)
        
        # 컨트롤러 시그널 연결
        self.project_controller.project_loaded.connect(self.on_project_loaded)
        self.project_controller.status_updated.connect(self.update_status_bar)
        self.project_controller.error_occurred.connect(self.show_error_message)
        
        # 데이터 컨트롤러 시그널 연결
        self.data_controller.data_imported.connect(self.on_data_imported)
        self.data_controller.data_exported.connect(self.on_data_exported)
        self.data_controller.status_updated.connect(self.update_status_bar)
        self.data_controller.error_occurred.connect(self.show_error_message)
        
        # 분석 컨트롤러 시그널 연결
        self.analysis_controller.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_controller.status_updated.connect(self.update_status_bar)
        self.analysis_controller.error_occurred.connect(self.show_error_message)
        
        # 차트 컨트롤러 시그널 연결
        self.chart_controller.chart_created.connect(self.on_chart_created)
        self.chart_controller.status_updated.connect(self.update_status_bar)
        self.chart_controller.error_occurred.connect(self.show_error_message)
        
        # 차트 뷰에 차트 컨트롤러 설정
        self.chart_view.set_chart_controller(self.chart_controller)

        # 🔥 핵심 수정: analysis_requested 시그널 연결
        self.analysis_requested.connect(self.handle_analysis_request)
    
    def update_ui_state(self):
        """UI 상태 업데이트"""
        # 데이터가 있는지 확인
        has_data = self.data_view.has_data()
        df = self.data_view.get_data() if has_data else None

        numeric_cols = []
        categorical_cols = []
        if df is not None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

        has_numeric = len(numeric_cols) > 0
        has_numeric2 = len(numeric_cols) >= 2
        has_numeric3 = len(numeric_cols) >= 3
        has_cat = len(categorical_cols) > 0
        has_cat2 = len(categorical_cols) >= 2
        has_any_factor = df is not None and df.shape[1] >= 2

        # 분석 관련 액션 활성화 조건
        self.basic_stats_action.setEnabled(has_numeric)
        self.correlation_action.setEnabled(has_numeric2)
        self.one_way_anova_action.setEnabled(has_numeric and has_any_factor)
        self.two_way_anova_action.setEnabled(has_numeric and (has_cat2 or (df is not None and df.shape[1] >= 3)))
        self.multi_way_anova_action.setEnabled(has_numeric and (df is not None and df.shape[1] >= 4))
        self.repeated_anova_action.setEnabled(has_numeric and has_any_factor)
        self.simple_regression_action.setEnabled(has_numeric2)
        self.multiple_regression_action.setEnabled(has_numeric3)
        self.stepwise_regression_action.setEnabled(has_numeric3)
        self.nonlinear_regression_action.setEnabled(has_numeric2)
        self.mann_whitney_action.setEnabled(has_numeric and has_any_factor)
        self.kruskal_wallis_action.setEnabled(has_numeric and has_any_factor)
        self.wilcoxon_action.setEnabled(has_numeric)
        self.pca_action.setEnabled(has_numeric2)
        self.cluster_action.setEnabled(has_numeric2)
        self.discriminant_action.setEnabled(has_numeric2)
        self.comprehensive_analysis_action.setEnabled(has_data)
        self.run_analysis_btn.setEnabled(has_data)

        # DOE 분석 메뉴
        doe_ready = has_numeric and has_any_factor
        self.doe_anova_action.setEnabled(doe_ready)
        self.doe_fractional_action.setEnabled(doe_ready)
        self.doe_plackett_action.setEnabled(doe_ready)
        self.doe_rsm_action.setEnabled(has_numeric2)
        self.doe_box_behnken_action.setEnabled(has_numeric2)
        self.doe_ccd_action.setEnabled(has_numeric2)
        self.doe_orthogonal_action.setEnabled(doe_ready)
        self.doe_taguchi_action.setEnabled(doe_ready)
        self.doe_mixture_action.setEnabled(has_numeric2)
        self.doe_split_plot_action.setEnabled(doe_ready)

        # 차트 관련 액션 활성화 조건
        self.scatter_plot_action.setEnabled(has_numeric2)
        self.histogram_action.setEnabled(has_numeric)
        self.boxplot_action.setEnabled(has_numeric)
        self.line_plot_action.setEnabled(has_numeric)
        self.bar_plot_action.setEnabled(has_numeric)
        self.main_effects_action.setEnabled(has_numeric and (has_cat or has_any_factor))
        self.interaction_plot_action.setEnabled(has_numeric and (has_cat2 or has_numeric2))
        self.residual_plot_action.setEnabled(has_numeric2)
        self.contour_plot_action.setEnabled(has_numeric2)
        self.surface_plot_action.setEnabled(has_numeric2)
        self.pareto_chart_action.setEnabled(has_numeric)
        self.normal_plot_action.setEnabled(has_numeric)
        self.correlation_heatmap_action.setEnabled(has_numeric2)
        
        # 데이터 변환 관련 액션 활성화/비활성화 (실제 데이터가 필요한 기능들)
        self.log_transform_action.setEnabled(has_data)
        self.standardize_action.setEnabled(has_data)
        self.normalize_action.setEnabled(has_data)
        self.handle_missing_action.setEnabled(has_data)
        self.detect_outliers_action.setEnabled(has_data)
        
        # 새로운 데이터 메뉴 액션들 활성화/비활성화
        self.import_data_action2.setEnabled(True)  # 항상 활성화
        self.export_data_action2.setEnabled(has_data)
        self.copy_data_action.setEnabled(has_data)
        self.paste_data_action.setEnabled(True)  # 항상 활성화
        self.connect_db_action.setEnabled(True)  # 항상 활성화
        
        # 데이터 편집 관련
        self.edit_data_action.setEnabled(has_data)
        self.insert_row_action.setEnabled(has_data)
        self.delete_row_action.setEnabled(has_data)
        self.insert_column_action.setEnabled(has_data)
        self.delete_column_action.setEnabled(has_data)
        self.sort_ascending_action.setEnabled(has_data)
        self.sort_descending_action.setEnabled(has_data)
        self.find_replace_action.setEnabled(has_data)
        
        # 데이터 변환 관련
        self.rename_variables_action.setEnabled(has_data)
        self.change_data_types_action.setEnabled(has_data)
        self.create_derived_variable_action.setEnabled(has_data)
        self.create_dummy_variables_action.setEnabled(has_data)
        self.merge_data_action.setEnabled(has_data)
        self.split_data_action.setEnabled(has_data)
        
        # 데이터 품질 관련
        self.handle_missing_action2.setEnabled(has_data)
        self.detect_outliers_action2.setEnabled(has_data)
        self.remove_duplicates_action.setEnabled(has_data)
        
        # 데이터 뷰 관련
        self.data_summary_action.setEnabled(has_data)
        self.variable_info_action.setEnabled(has_data)
        self.data_preview_action.setEnabled(has_data)
        self.set_filter_action.setEnabled(has_data)
        self.clear_filter_action.setEnabled(has_data)
        
        # 내보내기 관련 액션 활성화/비활성화
        self.export_action.setEnabled(has_data)
    
    # 슬롯 메서드들
    def new_project(self):
        """새 프로젝트 생성"""
        # 현재 프로젝트 경로 초기화
        self.current_project_path = None
        
        # 윈도우 제목 초기화
        self.setWindowTitle("DOE Tool - 실험계획법 분석 도구")
        
        # 각 뷰 초기화
        self.data_view.clear_data()
        self.chart_view.clear_charts()
        
        # 프로젝트 탐색기 초기화
        if hasattr(self, 'project_explorer'):
            self.project_explorer.clear_project()
            self.project_explorer.set_project_name("새 프로젝트")
        
        # 결과 뷰 초기화
        if hasattr(self, 'results_view'):
            self.results_view.clear_results()
        
        self.update_ui_state()
        self.status_label.setText("새 프로젝트를 생성했습니다.")
    
    def open_project(self):
        """프로젝트 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "프로젝트 열기", "", 
            "DOE 프로젝트 파일 (*.json);;모든 파일 (*)"
        )
        if file_path:
            self.load_project_file(file_path)
    
    def save_project(self):
        """프로젝트 저장"""
        if self.current_project_path:
            self.save_project_file(self.current_project_path)
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """다른 이름으로 프로젝트 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "프로젝트 저장", "새_프로젝트.json",
            "DOE 프로젝트 파일 (*.json)"
        )
        if file_path:
            self.save_project_file(file_path)
            self.current_project_path = file_path
    
    def load_project_file(self, file_path: str):
        """프로젝트 파일 불러오기"""
        try:
            import json
            
            self.status_label.setText("프로젝트 불러오는 중...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # JSON 파일 불러오기
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            if project_data is None:
                QMessageBox.critical(self, "오류", "프로젝트 파일을 불러올 수 없습니다.")
                return
            
            self.progress_bar.setValue(50)
            
            # 현재 프로젝트 초기화
            self.new_project()
            
            # 프로젝트 데이터 복원
            if self.restore_project_data(project_data):
                self.current_project_path = file_path
                project_name = project_data.get('project_info', {}).get('name', '불러온 프로젝트')
                self.setWindowTitle(f"DOE Tool - {project_name}")
                
                self.progress_bar.setValue(100)
                self.status_label.setText(f"프로젝트 불러오기 완료: {os.path.basename(file_path)}")
                
                QMessageBox.information(self, "완료", f"프로젝트를 성공적으로 불러왔습니다.\n\n파일: {file_path}")
            else:
                QMessageBox.critical(self, "오류", "프로젝트 데이터 복원 중 오류가 발생했습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"프로젝트 불러오기 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            if hasattr(self, 'status_label'):
                self.status_label.setText("준비")
    
    def save_project_file(self, file_path: str):
        """프로젝트 파일 저장"""
        try:
            import json
            
            self.status_label.setText("프로젝트 저장 중...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # 프로젝트 데이터 생성
            project_data = self.create_project_data()
            
            self.progress_bar.setValue(50)
            
            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.current_project_path = file_path
            project_name = project_data.get('project_info', {}).get('name', '프로젝트')
            self.setWindowTitle(f"DOE Tool - {project_name}")
            
            self.progress_bar.setValue(100)
            self.status_label.setText(f"프로젝트 저장 완료: {os.path.basename(file_path)}")
            
            QMessageBox.information(self, "완료", f"프로젝트를 성공적으로 저장했습니다.\n\n파일: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"프로젝트 저장 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            if hasattr(self, 'status_label'):
                self.status_label.setText("준비")
    
    def import_data(self):
        """데이터 가져오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "데이터 가져오기", "", 
            "Excel 파일 (*.xlsx *.xls);;CSV 파일 (*.csv);;모든 파일 (*)"
        )
        if file_path:
            try:
                self.data_view.load_data_from_file(file_path)
                self.status_label.setText(f"데이터를 가져왔습니다: {file_path}")
                self.update_ui_state()
            except Exception as e:
                QMessageBox.critical(self, "오류", f"데이터를 가져오는 중 오류가 발생했습니다:\n{str(e)}")
    
    def export_data(self):
        """데이터 내보내기"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "내보낼 데이터가 없습니다.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "데이터 내보내기", "", 
            "Excel 파일 (*.xlsx);;CSV 파일 (*.csv);;모든 파일 (*)"
        )
        if file_path:
            try:
                self.data_view.save_data_to_file(file_path)
                self.status_label.setText(f"데이터를 내보냈습니다: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"데이터를 내보내는 중 오류가 발생했습니다:\n{str(e)}")
    
    def edit_data(self):
        """데이터 편집"""
        self.tab_widget.setCurrentWidget(self.data_view)
        self.status_label.setText("데이터 편집 모드로 전환되었습니다.")
    
    def create_full_factorial_design(self):
        """완전요인설계 생성"""
        # 요인 수 입력
        factors, ok = QInputDialog.getInt(
            self, "완전요인설계", "요인 수를 입력하세요:", 3, 1, 10
        )
        if not ok:
            return

        try:
            options = self._show_full_factorial_dialog(factors)
            if options is None:
                return
            df = self.design_controller.create_full_factorial(options["levels"])
            df = self._apply_randomization(df, randomize=options["randomize"], seed=options["seed"])
            df = self._apply_replication(df, repeats=options["replicates"])
            self._update_design_result(
                df,
                f"완전요인설계 ({factors}요인)",
                self._format_design_summary("완전요인설계", df, factors),
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설계를 생성하는 중 오류가 발생했습니다:\n{e}")

    def create_fractional_factorial_design(self):
        """부분요인설계 생성"""
        try:
            options = self._show_fractional_factorial_dialog()
            if options is None:
                return
            df = self.design_controller.create_fractional_factorial(options["design_str"])
            df = self._apply_randomization(df, randomize=options["randomize"], seed=options["seed"])
            df = self._apply_replication(df, repeats=options["replicates"])
            factors = df.shape[1]
            self._update_design_result(
                df,
                "부분요인설계",
                self._format_design_summary("부분요인설계", df, factors),
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설계를 생성하는 중 오류가 발생했습니다:\n{e}")

    def create_plackett_burman_design(self):
        """Plackett-Burman 설계 생성"""
        try:
            options = self._show_plackett_burman_dialog()
            if options is None:
                return
            df = self.design_controller.create_plackett_burman(options["factors"])
            df = self._apply_randomization(df, randomize=options["randomize"], seed=options["seed"])
            df = self._apply_replication(df, repeats=options["replicates"])
            self._update_design_result(
                df,
                f"Plackett-Burman 설계 ({options['factors']}요인)",
                self._format_design_summary("Plackett-Burman", df, options["factors"]),
            )
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설계를 생성하는 중 오류가 발생했습니다:\n{e}")
    
    def create_rsm_design(self):
        """Create response surface design (CCD)"""
        try:
            options = self._show_ccd_dialog("CCD (RSM)")
            if options is None:
                return
            df = self.design_controller.create_ccd(
                options["factors"],
                center=options["center"],
                alpha=options["alpha"],
            )
            df = self._apply_randomization(df, randomize=options["randomize"], seed=options["seed"])
            df = self._apply_replication(df, repeats=options["replicates"])
            self._update_design_result(
                df,
                f"RSM-CCD ({options['factors']} factors)",
                self._format_design_summary("RSM-CCD", df, options["factors"]),
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create CCD design:\n{e}")
    
    def create_box_behnken_design(self):
        """Create Box-Behnken design"""
        try:
            options = self._show_box_behnken_dialog()
            if options is None:
                return
            df = self.design_controller.create_box_behnken(
                options["factors"],
                center=options["center"],
            )
            df = self._apply_randomization(df, randomize=options["randomize"], seed=options["seed"])
            df = self._apply_replication(df, repeats=options["replicates"])
            self._update_design_result(
                df,
                f"Box-Behnken ({options['factors']} factors)",
                self._format_design_summary("Box-Behnken", df, options["factors"]),
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create Box-Behnken design:\n{e}")
    
    def create_ccd_design(self):
        """Create CCD design"""
        try:
            options = self._show_ccd_dialog("Central Composite")
            if options is None:
                return
            df = self.design_controller.create_ccd(
                options["factors"],
                center=options["center"],
                alpha=options["alpha"],
            )
            df = self._apply_randomization(df, randomize=options["randomize"], seed=options["seed"])
            df = self._apply_replication(df, repeats=options["replicates"])
            self._update_design_result(
                df,
                f"CCD ({options['factors']} factors)",
                self._format_design_summary("CCD", df, options["factors"]),
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create CCD design:\n{e}")
    
    def create_orthogonal_array_design(self):
        """Create orthogonal array (Taguchi)"""
        designs = ["L4 (2-level, up to 3 factors)", "L8 (2-level, up to 7 factors)", "L9 (3-level, up to 4 factors)"]
        design_choice, ok = QInputDialog.getItem(self, "Select Orthogonal Array", "Choose design:", designs, 1, False)
        if not ok or not design_choice:
            return
        design_code = design_choice.split()[0]
        max_factors = {"L4": 3, "L8": 7, "L9": 4}[design_code]
        factors, ok = QInputDialog.getInt(self, "Factors", f"Number of factors (max {max_factors}):", min(2, max_factors), 1, max_factors)
        if not ok:
            return
        try:
            df = self.design_controller.create_orthogonal_array(factors, design=design_code)
            self.data_view.set_data(df)
            self.project_explorer.set_data(df, f"{design_code} ({factors} factors)")
            self.status_label.setText("Orthogonal array created.")
            self.update_ui_state()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create orthogonal array:\n{e}")
    
    def create_taguchi_design(self):
        """Create Taguchi design"""
        self.create_orthogonal_array_design()
    
    def create_mixture_design(self):
        """Mixture design (simplex lattice)"""
        options = self._show_mixture_design_dialog()
        if options is None:
            return
        components = options["components"]
        degree = options["degree"]
        component_names = options["component_names"]

        try:
            lattice_points = self._generate_simplex_lattice(components, degree)
            df = pd.DataFrame(lattice_points, columns=component_names)

            sums = df.sum(axis=1)
            tol = 1e-6
            invalid = (sums - 1.0).abs() > tol
            invalid_rows = df.index[invalid].tolist()
            if invalid_rows:
                head_rows = invalid_rows[:50]
                tail_note = "" if len(invalid_rows) <= 50 else f"\n... {len(invalid_rows) - 50} more"
                msg = "Sum-to-1 check failed.\n\n"
                msg += f"Invalid row indices: {', '.join(map(str, head_rows))}{tail_note}"
                QMessageBox.critical(self, "Error", msg)
                return

            df = self._apply_randomization(df, randomize=options["randomize"], seed=options["seed"])
            df = self._apply_replication(df, repeats=options["replicates"])
            summary = (
                "Mixture Design (Simplex Lattice)\n"
                f"Components: {components}\n"
                f"Degree: {degree}\n"
                f"Runs: {len(df)}\n"
                "Sum check: OK (sum=1)"
            )
            self._update_design_result(df, f"Mixture (q={components}, m={degree})", summary)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create mixture design:\n{str(e)}")

    def create_split_plot_design(self):
        """Split-plot design"""
        options = self._show_split_plot_dialog()
        if options is None:
            return

        wp_levels = options["whole_levels"]
        sp_levels = options["subplot_levels"]
        randomize_whole = options["randomize_whole"]
        randomize_subplot = options["randomize_subplot"]
        seed = options["seed"]
        seed_per_block = options["seed_per_block"]
        replicates = options["replicates"]

        try:
            whole_df = self.design_controller.create_full_factorial(wp_levels)
            whole_df.columns = [f"W{i+1}" for i in range(len(wp_levels))]
            subplot_df = self.design_controller.create_full_factorial(sp_levels)
            subplot_df.columns = [f"S{i+1}" for i in range(len(sp_levels))]

            if randomize_whole:
                whole_df = self._apply_randomization(whole_df, True, seed=seed)

            rows = []
            for idx, w_row in whole_df.iterrows():
                if randomize_subplot:
                    if seed is None:
                        sub_seed = None
                    else:
                        sub_seed = seed + idx if seed_per_block else seed
                    sub_df = self._apply_randomization(subplot_df, True, seed=sub_seed)
                else:
                    sub_df = subplot_df
                for _, s_row in sub_df.iterrows():
                    row = {**w_row.to_dict(), **s_row.to_dict()}
                    row["WholePlot"] = idx + 1
                    rows.append(row)

            df = pd.DataFrame(rows)
            df = self._apply_replication(df, repeats=replicates)

            summary = (
                "Split-Plot Design\n"
                f"Whole-plot factors: {len(wp_levels)}\n"
                f"Sub-plot factors: {len(sp_levels)}\n"
                f"Whole runs: {len(whole_df)}\n"
                f"Sub runs per whole: {len(subplot_df)}\n"
                f"Total runs: {len(df)}"
            )
            self._update_design_result(df, "Split-Plot Design", summary)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create split-plot design:\n{str(e)}")

    def create_custom_design(self):
        """Custom design"""
        choice_box = QMessageBox(self)
        choice_box.setWindowTitle("Custom Design")
        choice_box.setText("How do you want to create the custom design?")
        create_btn = choice_box.addButton("Create blank design", QMessageBox.AcceptRole)
        load_btn = choice_box.addButton("Load from file", QMessageBox.ActionRole)
        cancel_btn = choice_box.addButton("Cancel", QMessageBox.RejectRole)
        choice_box.setDefaultButton(create_btn)
        choice_box.exec()

        if choice_box.clickedButton() == cancel_btn:
            return

        if choice_box.clickedButton() == load_btn:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Load custom design", "",
                "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*)"
            )
            if not file_path:
                return
            try:
                df = self.data_view.read_dataframe_from_file(file_path)
                summary = (
                    "Custom Design (Loaded)\n"
                    f"Columns: {len(df.columns)}\n"
                    f"Runs: {len(df)}"
                )
                self._update_design_result(df, "Custom Design", summary)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load design file:\n{str(e)}")
            return

        factors, ok = QInputDialog.getInt(self, "Custom Design", "Number of factors:", 3, 1, 50)
        if not ok:
            return
        runs, ok = QInputDialog.getInt(self, "Custom Design", "Number of runs:", 8, 1, 100000)
        if not ok:
            return

        template = self._show_custom_template_dialog()
        if template is None:
            return

        df = pd.DataFrame(index=range(runs))
        template_type = template["type"]
        levels = template.get("levels", [])

        for i in range(factors):
            col = f"F{i+1}"
            if template_type == "none":
                df[col] = [None] * runs
            else:
                df[col] = [levels[(r + i) % len(levels)] for r in range(runs)]

        summary = (
            "Custom Design (Blank)\n"
            f"Factors: {factors}\n"
            f"Runs: {runs}"
        )
        self._update_design_result(df, "Custom Design", summary)

    def _generate_simplex_lattice(self, components: int, degree: int):
        # Generate simplex-lattice points where sum(parts)=degree.
        points = []

        def _recurse(parts_left, remaining, current):
            if parts_left == 1:
                points.append(current + [remaining])
                return
            for i in range(remaining + 1):
                _recurse(parts_left - 1, remaining - i, current + [i])

        _recurse(components, degree, [])
        return [[v / degree for v in row] for row in points]

    def _apply_randomization(self, df, randomize: bool, seed=None):
        if df is None or df.empty or not randomize:
            return df
        random_state = seed if seed is not None else None
        return df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    def _apply_replication(self, df, repeats: int):
        if df is None or df.empty or repeats <= 1:
            return df
        return df.loc[df.index.repeat(repeats)].reset_index(drop=True)

    def _format_design_summary(self, name: str, df: pd.DataFrame, factors: int) -> str:
        runs = len(df)
        level_summary = ", ".join(
            [f"F{i+1}:{df[col].nunique()}수준" for i, col in enumerate(df.columns)]
        )
        return f"{name}\n요인 수: {factors}\n런 수: {runs}\n수준 요약: {level_summary}"

    def _update_design_result(self, df: pd.DataFrame, label: str, summary: str):
        # 반응 변수 열이 없으면 기본 Response 열 추가
        if "Response" not in df.columns:
            df = df.copy()
            df["Response"] = None
        self.data_view.set_data(df)
        self.project_explorer.set_data(df, label)
        self.status_label.setText(f"{label} 생성 완료 (런 수: {len(df)})")
        QMessageBox.information(self, "설계 요약", summary)
        self.update_ui_state()

    def _add_common_design_controls(self, form_layout: QFormLayout):
        replicates_spin = QSpinBox()
        replicates_spin.setRange(1, 30)
        replicates_spin.setValue(1)
        form_layout.addRow("반복수:", replicates_spin)

        randomize_check = QCheckBox("런 순서를 무작위화합니다")
        randomize_check.setChecked(True)
        form_layout.addRow("랜덤화:", randomize_check)

        seed_check = QCheckBox("고정 시드 사용")
        seed_spin = QSpinBox()
        seed_spin.setRange(0, 99999)
        seed_spin.setValue(42)
        seed_spin.setEnabled(False)
        seed_check.toggled.connect(seed_spin.setEnabled)
        form_layout.addRow("시드:", seed_spin)
        form_layout.addRow("", seed_check)

        return {
            "replicates": replicates_spin,
            "randomize": randomize_check,
            "seed": seed_spin,
            "seed_check": seed_check,
        }

    def _finalize_common_options(self, controls: dict) -> dict:
        seed = None
        if controls["seed_check"].isChecked():
            seed = int(controls["seed"].value())
        return {
            "replicates": int(controls["replicates"].value()),
            "randomize": controls["randomize"].isChecked(),
            "seed": seed,
        }

    def _show_mixture_design_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Mixture Design Options")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        comp_spin = QSpinBox()
        comp_spin.setRange(2, 10)
        comp_spin.setValue(3)
        form_layout.addRow("Components", comp_spin)

        degree_spin = QSpinBox()
        degree_spin.setRange(2, 10)
        degree_spin.setValue(3)
        form_layout.addRow("Degree", degree_spin)

        name_input = QLineEdit("C1, C2, C3")
        form_layout.addRow("Component names (comma separated)", name_input)

        note_label = QLabel("Sum-to-1 check will be validated after generation.")
        form_layout.addRow("", note_label)

        common = self._add_common_design_controls(form_layout)

        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        components = int(comp_spin.value())
        raw_names = [n.strip() for n in name_input.text().split(",") if n.strip()]
        if not raw_names:
            raw_names = [f"C{i+1}" for i in range(components)]
        elif len(raw_names) == 1 and components > 1:
            base = raw_names[0]
            raw_names = [f"{base}{i+1}" for i in range(components)]
        elif len(raw_names) != components:
            QMessageBox.warning(self, "Input Error", "Component name count does not match components.")
            return None

        if len(set(raw_names)) != len(raw_names):
            QMessageBox.warning(self, "Input Error", "Component names must be unique.")
            return None

        options = self._finalize_common_options(common)
        options["components"] = components
        options["degree"] = int(degree_spin.value())
        options["component_names"] = raw_names
        return options

    def _show_split_plot_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Split-Plot Design Options")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        wp_spin = QSpinBox()
        wp_spin.setRange(1, 10)
        wp_spin.setValue(2)
        form_layout.addRow("Whole-plot factors", wp_spin)

        wp_levels_input = QLineEdit("2,2")
        form_layout.addRow("Whole-plot levels (e.g., 2,2)", wp_levels_input)

        sp_spin = QSpinBox()
        sp_spin.setRange(1, 10)
        sp_spin.setValue(2)
        form_layout.addRow("Sub-plot factors", sp_spin)

        sp_levels_input = QLineEdit("2,2")
        form_layout.addRow("Sub-plot levels (e.g., 2,2)", sp_levels_input)

        randomize_whole = QCheckBox("Randomize whole-plot")
        randomize_whole.setChecked(True)
        form_layout.addRow("", randomize_whole)

        randomize_subplot = QCheckBox("Randomize sub-plot (within each whole-plot)")
        randomize_subplot.setChecked(True)
        form_layout.addRow("", randomize_subplot)

        seed_per_block = QCheckBox("Use distinct seed per whole-plot block")
        seed_per_block.setChecked(True)
        form_layout.addRow("", seed_per_block)

        common = self._add_common_design_controls(form_layout)

        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        def _parse_levels(text: str, count: int):
            levels = [int(v.strip()) for v in text.split(",") if v.strip()]
            if len(levels) == 1:
                levels = levels * count
            if len(levels) != count:
                return None
            return levels

        wp_levels = _parse_levels(wp_levels_input.text(), int(wp_spin.value()))
        if not wp_levels:
            QMessageBox.warning(self, "Input Error", "Whole-plot level count mismatch.")
            return None

        sp_levels = _parse_levels(sp_levels_input.text(), int(sp_spin.value()))
        if not sp_levels:
            QMessageBox.warning(self, "Input Error", "Sub-plot level count mismatch.")
            return None

        options = self._finalize_common_options(common)
        options["whole_levels"] = wp_levels
        options["subplot_levels"] = sp_levels
        options["randomize_whole"] = randomize_whole.isChecked()
        options["randomize_subplot"] = randomize_subplot.isChecked()
        options["seed_per_block"] = seed_per_block.isChecked()
        return options

    def _show_custom_template_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Custom Design Template")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        template_combo = QComboBox()
        template_combo.addItems([
            "None",
            "2-level (-1, 1)",
            "3-level (-1, 0, 1)",
            "Range (min, max)",
        ])
        form_layout.addRow("Template", template_combo)

        min_input = QLineEdit("0")
        max_input = QLineEdit("1")
        form_layout.addRow("Min value", min_input)
        form_layout.addRow("Max value", max_input)

        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        selection = template_combo.currentText()
        if selection == "None":
            return {"type": "none"}

        if selection.startswith("2-level"):
            return {"type": "levels", "levels": [-1, 1]}

        if selection.startswith("3-level"):
            return {"type": "levels", "levels": [-1, 0, 1]}

        try:
            min_val = float(min_input.text().strip())
            max_val = float(max_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Range values must be numeric.")
            return None

        if min_val == max_val:
            QMessageBox.warning(self, "Input Error", "Min and max cannot be the same.")
            return None

        return {"type": "levels", "levels": [min_val, max_val]}

    def _show_full_factorial_dialog(self, factors: int):
        dialog = QDialog(self)
        dialog.setWindowTitle("완전요인설계 옵션")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        levels_input = QLineEdit(",".join(["2"] * factors))
        form_layout.addRow("수준 수(쉼표 구분):", levels_input)

        common = self._add_common_design_controls(form_layout)

        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        levels = [int(v.strip()) for v in levels_input.text().split(",") if v.strip()]
        if len(levels) == 1:
            levels = levels * factors
        if len(levels) != factors:
            QMessageBox.warning(self, "입력 오류", "수준 수가 요인 수와 일치하지 않습니다.")
            return None

        options = self._finalize_common_options(common)
        options["levels"] = levels
        return options

    def _show_fractional_factorial_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("부분요인설계 옵션")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        design_input = QLineEdit("a b ab")
        form_layout.addRow("Generator 문자열:", design_input)

        common = self._add_common_design_controls(form_layout)

        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        design_str = design_input.text().strip()
        if not design_str:
            QMessageBox.warning(self, "입력 오류", "Generator 문자열을 입력하세요.")
            return None

        options = self._finalize_common_options(common)
        options["design_str"] = design_str
        return options

    def _show_plackett_burman_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Plackett-Burman 설계 옵션")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        factors_spin = QSpinBox()
        factors_spin.setRange(3, 47)
        factors_spin.setValue(4)
        form_layout.addRow("요인 수:", factors_spin)

        common = self._add_common_design_controls(form_layout)

        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        options = self._finalize_common_options(common)
        options["factors"] = int(factors_spin.value())
        return options

    def _show_box_behnken_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Box-Behnken 옵션")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        factors_spin = QSpinBox()
        factors_spin.setRange(3, 10)
        factors_spin.setValue(3)
        form_layout.addRow("요인 수:", factors_spin)

        center_spin = QSpinBox()
        center_spin.setRange(0, 10)
        center_spin.setValue(1)
        form_layout.addRow("중심점 수:", center_spin)

        common = self._add_common_design_controls(form_layout)

        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        options = self._finalize_common_options(common)
        options["factors"] = int(factors_spin.value())
        options["center"] = int(center_spin.value())
        return options

    def _show_ccd_dialog(self, title: str):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{title} 옵션")
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        factors_spin = QSpinBox()
        factors_spin.setRange(2, 10)
        factors_spin.setValue(3)
        form_layout.addRow("요인 수:", factors_spin)

        center_factorial_spin = QSpinBox()
        center_factorial_spin.setRange(0, 10)
        center_factorial_spin.setValue(4)
        form_layout.addRow("중심점(요인부):", center_factorial_spin)

        center_star_spin = QSpinBox()
        center_star_spin.setRange(0, 10)
        center_star_spin.setValue(4)
        form_layout.addRow("중심점(축점부):", center_star_spin)

        alpha_input = QLineEdit("orthogonal")
        form_layout.addRow("알파(orthogonal/rotatable):", alpha_input)

        common = self._add_common_design_controls(form_layout)

        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return None

        alpha = alpha_input.text().strip() or "orthogonal"
        if alpha not in {"orthogonal", "rotatable"}:
            QMessageBox.warning(self, "입력 오류", "알파는 orthogonal 또는 rotatable 만 허용됩니다.")
            return None

        options = self._finalize_common_options(common)
        options["factors"] = int(factors_spin.value())
        options["center"] = (int(center_factorial_spin.value()), int(center_star_spin.value()))
        options["alpha"] = alpha
        return options

    def run_doe_anova_dialog(self):
        """현재 데이터에서 요인/반응을 선택해 DOE ANOVA 실행"""
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="DOE ANOVA", max_factors=3)
        if not response or not factors:
            return
        self._run_doe_anova(df, response, factors)

    def run_full_factorial_anova(self):
        """완전요인설계 데이터용 ANOVA 실행"""
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="완전요인 ANOVA", max_factors=None)
        if not response or not factors:
            return
        self._run_doe_anova(df, response, factors)

    def run_fractional_factorial_anova(self):
        """부분요인설계 데이터용 ANOVA 실행"""
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="부분요인 ANOVA", max_factors=None)
        if not response or not factors:
            return
        self._run_doe_anova(df, response, factors)

    def run_plackett_burman_analysis(self):
        """Plackett-Burman 설계 데이터용 주효과 ANOVA 실행"""
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="Plackett-Burman 분석", max_factors=None)
        if not response or not factors:
            return
        # 주효과 중심
        self.analysis_controller.run_main_effects_anova(df, response, factors, analysis_type="Plackett-Burman 분석")

    def _prompt_response_and_factors(self, df, title="DOE ANOVA", max_factors=None):
        """반응/요인 입력 공통 처리"""
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            QMessageBox.information(self, "알림", "숫자형 반응 변수가 필요합니다.")
            return None, None

        response, ok = QInputDialog.getItem(self, title, "반응 변수를 선택하세요:", numeric_cols, 0, False)
        if not ok or not response:
            return None, None

        default_factors = [c for c in df.columns if c != response]
        if max_factors:
            default_factors = default_factors[:max_factors]
        factor_text, ok = QInputDialog.getText(
            self,
            title,
            "요인 열 이름을 쉼표로 구분해 입력하세요" + (f" (최대 {max_factors}개)" if max_factors else "") + ":",
            text=",".join(default_factors)
        )
        if not ok:
            return None, None
        factors = [c.strip() for c in factor_text.split(",") if c.strip()]
        if not factors:
            QMessageBox.information(self, "알림", "요인을 하나 이상 입력하세요.")
            return None, None
        for f in factors:
            if f not in df.columns:
                QMessageBox.information(self, "알림", f"요인 열 '{f}'을(를) 찾을 수 없습니다.")
                return None, None
        if max_factors and len(factors) > max_factors:
            QMessageBox.information(self, "알림", f"요인은 최대 {max_factors}개까지 선택할 수 있습니다.")
            return None, None
        return response, factors

    def _run_doe_anova(self, df, response, factors):
        """공통 DOE ANOVA 실행"""
        model_df = df[[response] + factors].copy()
        for f in factors:
            model_df[f] = model_df[f].astype("category")

        self.status_label.setText(f"{response} ~ {', '.join(factors)} ANOVA 실행 중...")
        self.analysis_controller.run_doe_anova(model_df, response, factors)

    def _run_main_effects_anova(self, df, response, factors, analysis_type):
        """주효과만 포함한 ANOVA 실행"""
        model_df = df[[response] + factors].copy()
        for f in factors:
            model_df[f] = model_df[f].astype("category")
        self.status_label.setText(f"{analysis_type} 실행 중...")
        self.analysis_controller.run_main_effects_anova(model_df, response, factors, analysis_type=analysis_type)

    def _run_rsm_quadratic(self, df, response, factors, analysis_type):
        model_df = df[[response] + factors].copy()
        # 숫자형으로 강제 변환
        for f in factors:
            model_df[f] = pd.to_numeric(model_df[f], errors="coerce")
        self.status_label.setText(f"{analysis_type} 실행 중...")
        self.analysis_controller.run_rsm_quadratic(model_df, response, factors, analysis_type=analysis_type)

    def run_rsm_analysis(self):
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="반응표면분석 (RSM)", max_factors=None)
        if not response or not factors:
            return
        self._run_rsm_quadratic(df, response, factors, analysis_type="RSM 분석")

    def run_box_behnken_analysis(self):
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="Box-Behnken 분석", max_factors=None)
        if not response or not factors:
            return
        self._run_rsm_quadratic(df, response, factors, analysis_type="Box-Behnken 분석")

    def run_ccd_analysis(self):
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="CCD 분석", max_factors=None)
        if not response or not factors:
            return
        self._run_rsm_quadratic(df, response, factors, analysis_type="CCD 분석")

    def run_orthogonal_analysis(self):
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="직교배열 분석", max_factors=None)
        if not response or not factors:
            return
        self._run_main_effects_anova(df, response, factors, analysis_type="직교배열 분석")

    def run_taguchi_analysis(self):
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="다구치 분석", max_factors=None)
        if not response or not factors:
            return
        self._run_main_effects_anova(df, response, factors, analysis_type="다구치 분석")

    def run_mixture_analysis(self):
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="혼합 설계 분석", max_factors=None)
        if not response or not factors:
            return
        self._run_main_effects_anova(df, response, factors, analysis_type="혼합 설계 분석")

    def run_split_plot_analysis(self):
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        response, factors = self._prompt_response_and_factors(df, title="분할구 설계 분석", max_factors=None)
        if not response or not factors:
            return
        self._run_main_effects_anova(df, response, factors, analysis_type="분할구 설계 분석")

    def basic_statistics(self):
        """기초 통계 분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("기초 통계량을 계산 중입니다...")
        self.analysis_requested.emit("basic_stats")
    
    def run_one_way_anova_request(self):
        """일원분산분석 요청"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("일원분산분석을 수행 중입니다...")
        self.run_one_way_anova()
    
    def run_two_way_anova_request(self):
        """이원분산분석 요청"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("이원분산분석을 수행 중입니다...")
        self.run_two_way_anova()
    
    def run_multi_way_anova(self):
        """다원분산분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("다원분산분석을 수행 중입니다...")
        self.analysis_requested.emit("multi_way_anova")
    
    def run_repeated_anova(self):
        """반복측정분산분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("반복측정분산분석을 수행 중입니다...")
        self.analysis_requested.emit("repeated_anova")
    
    def run_simple_regression(self):
        """단순회귀분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("단순회귀분석을 수행 중입니다...")
        self.analysis_requested.emit("simple_regression")
    
    def run_multiple_regression(self):
        """다중회귀분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("다중회귀분석을 수행 중입니다...")
        self.analysis_requested.emit("multiple_regression")
    
    def run_stepwise_regression(self):
        """단계적회귀분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("단계적회귀분석을 수행 중입니다...")
        self.analysis_requested.emit("stepwise_regression")
    
    def run_nonlinear_regression(self):
        """비선형회귀분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("비선형회귀분석을 수행 중입니다...")
        self.analysis_requested.emit("nonlinear_regression")
    
    def run_correlation_analysis(self):
        """상관분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("상관분석을 수행 중입니다...")
        self.analysis_requested.emit("correlation_analysis")
    
    def run_mann_whitney_test(self):
        """Mann-Whitney U 검정"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("Mann-Whitney U 검정을 수행 중입니다...")
        self.analysis_requested.emit("mann_whitney_test")
    
    def run_kruskal_wallis_test(self):
        """Kruskal-Wallis 검정"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("Kruskal-Wallis 검정을 수행 중입니다...")
        self.analysis_requested.emit("kruskal_wallis_test")
    
    def run_wilcoxon_test(self):
        """Wilcoxon 부호순위 검정"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("Wilcoxon 부호순위 검정을 수행 중입니다...")
        self.analysis_requested.emit("wilcoxon_test")
    
    def run_pca_analysis(self):
        """주성분분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("주성분분석을 수행 중입니다...")
        self.analysis_requested.emit("pca_analysis")
    
    def run_cluster_analysis(self):
        """군집분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("군집분석을 수행 중입니다...")
        self.analysis_requested.emit("cluster_analysis")
    
    def run_discriminant_analysis(self):
        """판별분석"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        self.status_label.setText("판별분석을 수행 중입니다...")
        self.analysis_requested.emit("discriminant_analysis")
    
    def run_analysis(self):
        """종합 분석 실행"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        # UI 상태 변경
        self.run_analysis_btn.setEnabled(False)
        self.stop_analysis_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("종합 분석을 실행 중입니다...")
        
        try:
            # 기존 분석 결과 확인하여 중복 실행 방지
            existing_analyses = set()
            for i in range(self.project_explorer.analysis_tree.topLevelItemCount()):
                item = self.project_explorer.analysis_tree.topLevelItem(i)
                existing_analyses.add(item.text(0))
            
            # 1. 기초 통계 분석
            self.progress_bar.setValue(25)
            if "기초 통계" not in existing_analyses:
                self.project_explorer.run_basic_statistics()
            
            # 2. 상관분석
            self.progress_bar.setValue(50)
            if "상관분석" not in existing_analyses:
                self.project_explorer.run_correlation_analysis()
            
            # 3. ANOVA 분석 (범주형 변수가 있는 경우)
            data = self.data_view.get_data()
            categorical_cols = data.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                self.progress_bar.setValue(75)
                if "ANOVA" not in existing_analyses:
                    self.project_explorer.run_anova()
            
            # 4. 회귀분석
            self.progress_bar.setValue(90)
            if "회귀분석" not in existing_analyses:
                self.project_explorer.run_regression()
            
            # 완료
            self.progress_bar.setValue(100)
            self.status_label.setText("종합 분석이 완료되었습니다.")
            
            # 결과 탭으로 이동
            self.tab_widget.setCurrentWidget(self.results_view)
            
            QMessageBox.information(self, "분석 완료", 
                "종합 분석이 완료되었습니다.\n\n"
                "• 기초 통계 분석\n"
                "• 상관분석\n"
                + ("• ANOVA 분석\n" if len(categorical_cols) > 0 else "")
                + "• 회귀분석\n\n"
                "결과는 '결과' 탭과 프로젝트 탐색기에서 확인할 수 있습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"분석 중 오류가 발생했습니다:\n{str(e)}")
            self.status_label.setText("분석 중 오류가 발생했습니다.")
        
        finally:
            # UI 상태 복원
            self.run_analysis_btn.setEnabled(True)
            self.stop_analysis_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
    
    def stop_analysis(self):
        """분석 중지"""
        self.run_analysis_btn.setEnabled(True)
        self.stop_analysis_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("분석이 중지되었습니다.")
        
        QMessageBox.information(self, "분석 중지", "분석이 사용자에 의해 중지되었습니다.")
    
    def show_about(self):
        """정보 다이얼로그 표시"""
        QMessageBox.about(
            self, "DOE Tool 정보",
            "<h3>DOE Tool v0.1.0</h3>"
            "<p>실험계획법(Design of Experiments) 분석 도구</p>"
            "<p>Python과 PySide6로 개발되었습니다.</p>"
            "<p><b>주요 기능:</b></p>"
            "<ul>"
            "<li>데이터 가져오기/내보내기</li>"
            "<li>요인설계 생성</li>"
            "<li>통계 분석 (ANOVA, 회귀분석)</li>"
            "<li>시각화 및 보고서 생성</li>"
            "</ul>"
        )
    
    def on_tab_changed(self, index):
        """탭 변경 이벤트"""
        tab_names = ["데이터", "차트", "결과"]
        if index < len(tab_names):
            self.status_label.setText(f"{tab_names[index]} 탭이 선택되었습니다.")
    
    def on_data_changed(self):
        """데이터 변경 이벤트"""
        # 차트 뷰, 결과 뷰, 프로젝트 탐색기에 데이터 전달
        if self.data_view.has_data():
            data = self.data_view.get_data()
            
            # 차트 뷰 초기화 및 새 데이터 설정
            self.chart_view.clear_charts()
            self.chart_view.set_data(data)
            
            # 결과 뷰 초기화 및 새 데이터 설정
            self.results_view.clear_results()
            self.results_view.set_data(data)
            
            # 프로젝트 탐색기에 새 데이터 설정 (분석 결과 자동 초기화됨)
            self.project_explorer.set_data(data, "현재 데이터")
        else:
            # 데이터가 없으면 모든 뷰 초기화
            self.chart_view.clear_charts()
            self.results_view.clear_results()
            self.project_explorer.set_data(None)
        
        self.update_ui_state()
        self.status_label.setText("데이터가 변경되었습니다.")
    
    def update_memory_usage(self):
        """메모리 사용량 업데이트"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"메모리: {memory_mb:.1f}MB")
        except ImportError:
            # psutil이 없으면 기본값 표시
            self.memory_label.setText("메모리: N/A")
    
    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        reply = QMessageBox.question(
            self, "종료 확인", 
            "정말로 애플리케이션을 종료하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    @Slot(Project)
    def on_project_loaded(self, project: Project):
        """컨트롤러에서 새 프로젝트가 로드되었을 때 UI를 업데이트합니다."""
        self.setWindowTitle(f"DOE Tool - {project.name}")
        
        # 데이터 뷰 업데이트
        self.data_view.set_data(project.dataframe)
        if hasattr(self, 'chart_view'):
            self.chart_view.set_data(project.dataframe)
        
        # 프로젝트 탐색기 업데이트
        self.project_explorer.clear_project()
        self.project_explorer.set_project_name(project.name)
        if project.dataframe is not None and not project.dataframe.empty:
            self.project_explorer.set_data(project.dataframe, project.data_description)
        
        # 분석 및 차트 히스토리 복원
        if hasattr(project, 'analysis_history') and project.analysis_history:
            for result in project.analysis_history:
                # 프로젝트 탐색기에 분석 결과 추가
                self.project_explorer.add_analysis_result(
                    result.get('type', '알 수 없음'),
                    result,
                    result.get('status', '완료')
                )
                # 결과 뷰에도 분석 결과 추가
                self.results_view.add_analysis_result(result.get('type', '알 수 없음'), result)
        
        if hasattr(project, 'chart_history') and project.chart_history:
            for chart_data in project.chart_history:
                self.project_explorer.add_chart_result(
                    chart_data.get('type', '차트'),
                    chart_data,
                    chart_data.get('description', '')
                )
            # 마지막 차트를 뷰에 복원
            try:
                last_chart = project.chart_history[-1]
                self.chart_view.display_chart(last_chart)
            except Exception:
                pass
        
        self.update_ui_state()
        self.update_status_bar(f"'{project.name}' 프로젝트가 로드되었습니다.")
        
        # 분석 결과가 있으면 결과 탭으로 이동
        if hasattr(project, 'analysis_history') and project.analysis_history:
            self.tab_widget.setCurrentWidget(self.results_view)

    @Slot(str)
    def update_status_bar(self, message: str):
        """상태바 메시지를 업데이트합니다."""
        self.status_bar.showMessage(message, 5000)

    @Slot(str, str)
    def show_error_message(self, title: str, message: str):
        """오류 메시지 박스를 표시합니다."""
        QMessageBox.critical(self, title, message)

    def show_doe_analysis_placeholder(self, analysis_name: str):
        """DOE 분석 항목이 아직 구현되지 않았을 때 안내."""
        QMessageBox.information(
            self,
            "준비중",
            f"'{analysis_name}' 분석 기능은 준비 중입니다.\n필요한 데이터와 요구 사항을 알려주시면 우선 구현할 수 있습니다."
        )

    @Slot(pd.DataFrame, str)
    def on_data_imported(self, dataframe, description):
        """데이터 가져오기 완료 시 호출되는 슬롯"""
        # 현재 프로젝트에 데이터 업데이트
        self.project_controller.current_project.update_data(dataframe, description)
        self.project_controller.current_project.is_dirty = True
        
        # UI 업데이트 (프로젝트 전체 상태 갱신)
        self.on_project_loaded(self.project_controller.current_project)

    @Slot(str)
    def on_data_exported(self, file_path):
        """데이터 내보내기 완료 시 호출되는 슬롯"""
        # 추가적인 UI 업데이트가 필요한 경우 여기에 작성
        pass

    @Slot(str, dict)
    def on_analysis_completed(self, analysis_type: str, result: dict):
        """분석 완료 시 호출되는 슬롯"""
        # 프로젝트에 분석 결과 추가
        self.project_controller.current_project.add_analysis(result)
        
        # 프로젝트 탐색기에 분석 결과 추가
        self.project_explorer.add_analysis_result(analysis_type, result, result.get('status', '완료'))
        
        # 결과 뷰에 분석 결과 표시
        self.results_view.display_results(analysis_type, result)
        self.tab_widget.setCurrentWidget(self.results_view)

    @Slot(dict)
    def on_chart_created(self, chart_info: dict):
        """차트 생성 완료 시 호출되는 슬롯"""
        # 프로젝트에 차트 정보 추가
        self.project_controller.current_project.add_chart(chart_info)
        
        # 프로젝트 탐색기에 차트 추가
        self.project_explorer.add_chart_result(
            chart_info.get('type', '차트'),
            chart_info,
            chart_info.get('description', '')
        )
        
        # 차트 뷰에 차트 표시
        self.chart_view.display_chart(chart_info)
        self.tab_widget.setCurrentWidget(self.chart_view)

    def export_current_data(self):
        """현재 프로젝트의 데이터를 내보냅니다."""
        if self.project_controller.current_project is None:
            QMessageBox.information(self, "정보", "내보낼 프로젝트가 없습니다.")
            return
        
        dataframe = self.project_controller.current_project.dataframe
        self.data_controller.export_data(dataframe)

    def clear_all_charts(self):
        """모든 차트를 지웁니다."""
        self.chart_view.clear_charts()
        self.status_label.setText("모든 차트가 지워졌습니다.")

    def show_preferences(self):
        """애플리케이션 설정을 변경합니다."""
        # TODO: 설정 다이얼로그 구현
        pass

    def apply_log_transform(self):
        """선택된 변수에 로그 변환을 적용합니다."""
        # TODO: 로그 변환 기능 구현
        pass

    def apply_standardization(self):
        """선택된 변수를 표준화합니다."""
        # TODO: 표준화 기능 구현
        pass

    def apply_normalization(self):
        """선택된 변수를 정규화합니다."""
        # TODO: 정규화 기능 구현
        pass

    def handle_missing_values(self):
        """Open unified data quality dialog (missing focused)."""
        self.show_data_quality_dialog(default_section="missing")

    def detect_outliers(self):
        """Open unified data quality dialog (outlier focused)."""
        self.show_data_quality_dialog(default_section="outlier")

    def show_data_quality_dialog(self, default_section="missing"):
        """Unified UI for missing/outlier handling with column targets and preview."""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to process.")
            return

        data = self.data_view.get_data()
        if data is None or data.empty:
            QMessageBox.information(self, "Notice", "No data to process.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Data Quality (Missing/Outlier)")
        dialog.setModal(True)
        dialog.resize(720, 600)
        layout = QVBoxLayout(dialog)

        # Target columns
        cols_group = QGroupBox("Target Columns")
        cols_layout = QVBoxLayout(cols_group)
        cols_list = QListWidget()
        cols_list.setSelectionMode(QAbstractItemView.MultiSelection)
        selected_cols = set(self.data_view.get_selected_columns())
        for col in data.columns:
            item = QListWidgetItem(str(col))
            cols_list.addItem(item)
            if selected_cols:
                if col in selected_cols:
                    item.setSelected(True)
            else:
                item.setSelected(True)
        cols_layout.addWidget(cols_list)

        col_btns = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_none_btn = QPushButton("Select None")
        col_btns.addWidget(select_all_btn)
        col_btns.addWidget(select_none_btn)
        col_btns.addStretch()
        cols_layout.addLayout(col_btns)
        layout.addWidget(cols_group)

        # Missing values
        missing_group = QGroupBox("Missing Values")
        missing_layout = QFormLayout(missing_group)
        missing_enable = QCheckBox("Enable missing value handling")
        missing_method = QComboBox()
        missing_method.addItems([
            "Drop rows with missing values",
            "Fill numeric with mean",
            "Fill numeric with median",
            "Fill with 0",
            "Fill with value",
        ])
        missing_value = QLineEdit()
        missing_value.setPlaceholderText("Fill value")
        missing_layout.addRow(missing_enable)
        missing_layout.addRow("Method:", missing_method)
        missing_layout.addRow("Value:", missing_value)
        layout.addWidget(missing_group)

        # Outliers
        outlier_group = QGroupBox("Outliers")
        outlier_layout = QFormLayout(outlier_group)
        outlier_enable = QCheckBox("Enable outlier handling")
        outlier_method = QComboBox()
        outlier_method.addItems(["IQR (1.5x)", "Z-score (3.0)"])
        outlier_action = QComboBox()
        outlier_action.addItems(["Remove rows", "Replace outliers with NaN", "Clip to bounds"])
        outlier_layout.addRow(outlier_enable)
        outlier_layout.addRow("Method:", outlier_method)
        outlier_layout.addRow("Action:", outlier_action)
        layout.addWidget(outlier_group)

        # Processing order
        order_group = QGroupBox("Processing Order")
        order_layout = QFormLayout(order_group)
        order_combo = QComboBox()
        order_combo.addItems(["Missing -> Outliers", "Outliers -> Missing"])
        order_layout.addRow("Order:", order_combo)
        layout.addWidget(order_group)

        # Preview
        preview_label = QLabel("Preview (top 10 rows)")
        layout.addWidget(preview_label)
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setFont(QFont("Consolas", 9))
        preview_text.setPlainText("No preview generated.")
        layout.addWidget(preview_text)

        summary_label = QLabel("No preview generated.")
        summary_label.setStyleSheet("color: gray;")
        layout.addWidget(summary_label)

        # Buttons
        button_row = QHBoxLayout()
        preview_btn = QPushButton("Preview")
        button_row.addWidget(preview_btn)
        button_row.addStretch()
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Apply")
        button_row.addWidget(button_box)
        layout.addLayout(button_row)

        def _update_missing_controls():
            enabled = missing_enable.isChecked()
            missing_method.setEnabled(enabled)
            allow_value = enabled and missing_method.currentText() == "Fill with value"
            missing_value.setEnabled(allow_value)
            if not allow_value:
                missing_value.setText("")

        def _update_outlier_controls():
            enabled = outlier_enable.isChecked()
            outlier_method.setEnabled(enabled)
            outlier_action.setEnabled(enabled)

        def _select_all():
            for i in range(cols_list.count()):
                cols_list.item(i).setSelected(True)

        def _select_none():
            for i in range(cols_list.count()):
                cols_list.item(i).setSelected(False)

        def _collect_options():
            columns = [item.text() for item in cols_list.selectedItems()]
            if not columns:
                QMessageBox.information(dialog, "Notice", "Select at least one column.")
                return None

            missing_opts = {
                "enabled": missing_enable.isChecked(),
                "method": missing_method.currentText(),
                "fill_value": missing_value.text(),
            }
            outlier_opts = {
                "enabled": outlier_enable.isChecked(),
                "method": outlier_method.currentText(),
                "action": outlier_action.currentText(),
            }
            order = order_combo.currentText()

            if not missing_opts["enabled"] and not outlier_opts["enabled"]:
                QMessageBox.information(dialog, "Notice", "Select at least one operation.")
                return None

            return columns, missing_opts, outlier_opts, order

        def _run_preview():
            collected = _collect_options()
            if not collected:
                return
            columns, missing_opts, outlier_opts, order = collected
            preview_df, info = self._apply_data_quality_operations(
                data, columns, missing_opts, outlier_opts, order
            )
            if preview_df.empty:
                preview_text.setPlainText("(empty result)")
            else:
                preview_text.setPlainText(preview_df.head(10).to_string(index=True))
            summary_label.setText(self._format_data_quality_summary(info))
            dialog.preview_df = preview_df
            dialog.preview_info = info

        def _apply_changes():
            collected = _collect_options()
            if not collected:
                return
            columns, missing_opts, outlier_opts, order = collected
            updated, info = self._apply_data_quality_operations(
                data, columns, missing_opts, outlier_opts, order
            )
            if updated.equals(data):
                QMessageBox.information(dialog, "Notice", "No changes were applied.")
                return
            self.data_view.set_data(updated)
            self.status_label.setText("Data quality processing applied.")
            self._log_data_quality_result(info)
            dialog.accept()

        select_all_btn.clicked.connect(_select_all)
        select_none_btn.clicked.connect(_select_none)
        missing_enable.toggled.connect(_update_missing_controls)
        missing_method.currentTextChanged.connect(_update_missing_controls)
        outlier_enable.toggled.connect(_update_outlier_controls)
        preview_btn.clicked.connect(_run_preview)
        button_box.accepted.connect(_apply_changes)
        button_box.rejected.connect(dialog.reject)

        # Defaults
        if default_section == "outlier":
            missing_enable.setChecked(False)
            outlier_enable.setChecked(True)
        elif default_section == "both":
            missing_enable.setChecked(True)
            outlier_enable.setChecked(True)
        else:
            missing_enable.setChecked(True)
            outlier_enable.setChecked(False)

        _update_missing_controls()
        _update_outlier_controls()

        dialog.exec()

    def _apply_data_quality_operations(self, data, columns, missing_opts, outlier_opts, order):
        working = data.copy()
        info = {
            "rows_before": len(data),
            "rows_after": len(data),
            "columns": columns,
            "order": order,
            "missing": {"enabled": False},
            "outliers": {"enabled": False},
        }

        def _apply_missing(current):
            if missing_opts and missing_opts.get("enabled"):
                updated, missing_info = self._apply_missing_handling(
                    current,
                    columns,
                    missing_opts.get("method"),
                    missing_opts.get("fill_value", ""),
                )
                missing_info["enabled"] = True
                info["missing"] = missing_info
                return updated
            return current

        def _apply_outliers(current):
            if outlier_opts and outlier_opts.get("enabled"):
                updated, outlier_info = self._apply_outlier_handling(
                    current,
                    columns,
                    outlier_opts.get("method"),
                    outlier_opts.get("action"),
                )
                outlier_info["enabled"] = True
                info["outliers"] = outlier_info
                return updated
            return current

        if order == "Outliers -> Missing":
            working = _apply_outliers(working)
            working = _apply_missing(working)
        else:
            working = _apply_missing(working)
            working = _apply_outliers(working)

        info["rows_after"] = len(working)
        return working, info

    def _apply_missing_handling(self, df, columns, method, fill_value_text):
        working = df.copy()
        columns = [c for c in columns if c in working.columns]
        info = {
            "method": method,
            "columns": columns,
            "numeric_columns": [],
            "missing_before": 0,
            "missing_after": 0,
            "rows_removed": 0,
        }

        if not columns:
            info["skipped_reason"] = "No columns selected."
            return working, info

        info["missing_before"] = int(working[columns].isna().sum().sum())

        if method == "Drop rows with missing values":
            before_rows = len(working)
            working = working.dropna(subset=columns).reset_index(drop=True)
            info["rows_removed"] = before_rows - len(working)
        elif method == "Fill numeric with mean":
            numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(working[c])]
            info["numeric_columns"] = numeric_cols
            if not numeric_cols:
                info["skipped_reason"] = "No numeric columns."
            else:
                for col in numeric_cols:
                    working[col] = working[col].fillna(working[col].mean())
        elif method == "Fill numeric with median":
            numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(working[c])]
            info["numeric_columns"] = numeric_cols
            if not numeric_cols:
                info["skipped_reason"] = "No numeric columns."
            else:
                for col in numeric_cols:
                    working[col] = working[col].fillna(working[col].median())
        elif method == "Fill with 0":
            working[columns] = working[columns].fillna(0)
        elif method == "Fill with value":
            value_text = fill_value_text if fill_value_text is not None else ""
            if value_text == "":
                fill_value = ""
            else:
                try:
                    fill_value = int(value_text) if value_text.isdigit() else float(value_text)
                except ValueError:
                    fill_value = value_text
            working[columns] = working[columns].fillna(fill_value)

        info["missing_after"] = int(working[columns].isna().sum().sum())
        return working, info

    def _apply_outlier_handling(self, df, columns, method, action):
        working = df.copy()
        numeric_cols = [c for c in columns if c in working.columns and pd.api.types.is_numeric_dtype(working[c])]
        info = {
            "method": method,
            "action": action,
            "numeric_columns": numeric_cols,
            "outlier_cells": 0,
            "rows_removed": 0,
        }

        if not numeric_cols:
            info["skipped_reason"] = "No numeric columns."
            return working, info

        outlier_masks = {}
        bounds = {}
        for col in numeric_cols:
            series = pd.to_numeric(working[col], errors="coerce")
            if method == "IQR (1.5x)":
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if pd.isna(iqr) or iqr == 0:
                    lower, upper = q1, q3
                else:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
            else:
                mean_val = series.mean()
                std_val = series.std(ddof=0)
                if pd.isna(std_val) or std_val == 0:
                    lower, upper = mean_val, mean_val
                else:
                    lower = mean_val - 3.0 * std_val
                    upper = mean_val + 3.0 * std_val

            mask = series.lt(lower) | series.gt(upper)
            outlier_masks[col] = mask
            bounds[col] = (lower, upper)

        info["outlier_cells"] = int(sum(mask.sum() for mask in outlier_masks.values()))

        if action == "Remove rows":
            row_mask = None
            for mask in outlier_masks.values():
                row_mask = mask if row_mask is None else (row_mask | mask)
            if row_mask is not None:
                info["rows_removed"] = int(row_mask.sum())
                if info["rows_removed"] > 0:
                    working = working.loc[~row_mask].reset_index(drop=True)
        elif action == "Replace outliers with NaN":
            for col, mask in outlier_masks.items():
                if mask.any():
                    working.loc[mask, col] = None
        elif action == "Clip to bounds":
            for col in numeric_cols:
                lower, upper = bounds[col]
                working[col] = pd.to_numeric(working[col], errors="coerce").clip(lower, upper)

        return working, info

    def _format_data_quality_summary(self, info):
        lines = [
            f"Order: {info.get('order', 'Missing -> Outliers')}",
            f"Rows: {info.get('rows_before', 0)} -> {info.get('rows_after', 0)}",
        ]

        missing = info.get("missing", {})
        if missing.get("enabled"):
            missing_line = f"Missing (selected cols): {missing.get('missing_before', 0)} -> {missing.get('missing_after', 0)}"
            if missing.get("rows_removed"):
                missing_line += f", rows removed: {missing.get('rows_removed')}"
            if missing.get("skipped_reason"):
                missing_line += f" (skipped: {missing.get('skipped_reason')})"
            lines.append(missing_line)

        outliers = info.get("outliers", {})
        if outliers.get("enabled"):
            outlier_line = f"Outliers: {outliers.get('outlier_cells', 0)} cells"
            if outliers.get("rows_removed"):
                outlier_line += f", rows removed: {outliers.get('rows_removed')}"
            if outliers.get("skipped_reason"):
                outlier_line += f" (skipped: {outliers.get('skipped_reason')})"
            lines.append(outlier_line)

        return "\n".join(lines)

    def _log_data_quality_result(self, info):
        result = {
            "description": "Data quality processing",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Done",
            "rows_before": info.get("rows_before"),
            "rows_after": info.get("rows_after"),
            "columns": ", ".join(info.get("columns", [])),
            "order": info.get("order", "Missing -> Outliers"),
        }

        missing = info.get("missing", {})
        if missing.get("enabled"):
            result.update({
                "missing_method": missing.get("method"),
                "missing_before": missing.get("missing_before"),
                "missing_after": missing.get("missing_after"),
                "missing_rows_removed": missing.get("rows_removed"),
            })

        outliers = info.get("outliers", {})
        if outliers.get("enabled"):
            result.update({
                "outlier_method": outliers.get("method"),
                "outlier_action": outliers.get("action"),
                "outlier_cells": outliers.get("outlier_cells"),
                "outlier_rows_removed": outliers.get("rows_removed"),
            })

        self.results_view.display_results("Data Quality", result)

    def validate_data(self):
        """Validate data quality (reserved)."""
        # TODO: implement when needed
        pass
    def create_scatter_plot(self):
        """산점도 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("산점도를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 변수 선택 다이얼로그 후 차트 생성
    
    def create_histogram(self):
        """히스토그램 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("히스토그램을 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 변수 선택 다이얼로그 후 차트 생성
    
    def create_boxplot(self):
        """박스플롯 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("박스플롯을 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 변수 선택 다이얼로그 후 차트 생성
    
    def create_line_plot(self):
        """선 그래프 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("선 그래프를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 변수 선택 다이얼로그 후 차트 생성
    
    def create_bar_plot(self):
        """막대 그래프 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("막대 그래프를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 변수 선택 다이얼로그 후 차트 생성
    
    def create_main_effects_plot(self):
        """주효과도 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("주효과도를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: DOE 분석 결과 기반 주효과도 생성
    
    def create_interaction_plot(self):
        """상호작용도 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("상호작용도를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: DOE 분석 결과 기반 상호작용도 생성
    
    def create_residual_plot(self):
        """잔차도 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("잔차도를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 회귀분석 결과 기반 잔차도 생성
    
    def create_contour_plot(self):
        """등고선도 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("등고선도를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 반응표면 모델 기반 등고선도 생성
    
    def create_surface_plot(self):
        """3D 표면도 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("3D 표면도를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 반응표면 모델 기반 3D 표면도 생성
    
    def create_pareto_chart(self):
        """파레토 차트 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("파레토 차트를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 효과 크기 기반 파레토 차트 생성
    
    def create_normal_plot(self):
        """정규확률도 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("정규확률도를 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: Q-Q 플롯 생성
    
    def create_correlation_heatmap(self):
        """상관행렬 히트맵 생성"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "차트를 생성할 데이터가 없습니다.")
            return
        
        self.status_label.setText("상관행렬 히트맵을 생성합니다...")
        self.tab_widget.setCurrentWidget(self.chart_view)
        # TODO: 상관행렬 히트맵 생성

    # 데이터 입출력 메서드들
    def copy_data_to_clipboard(self):
        """선택된 데이터를 클립보드로 복사"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "복사할 데이터가 없습니다.")
            return
        
        try:
            # 선택된 데이터 또는 전체 데이터를 클립보드로 복사
            data = self.data_view.get_selected_data()  # 선택된 데이터가 있으면
            if data is None:
                data = self.data_view.get_data()  # 전체 데이터
            
            data.to_clipboard(sep='\t', index=False)
            self.status_label.setText("데이터가 클립보드로 복사되었습니다.")
            QMessageBox.information(self, "완료", "데이터가 클립보드로 복사되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"클립보드 복사 중 오류가 발생했습니다:\n{str(e)}")
    
    def paste_data_from_clipboard(self):
        """Paste data from clipboard"""
        try:
            import pandas as pd
            from PySide6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            text = clipboard.text()

            if not text.strip():
                QMessageBox.information(self, "Notice", "Clipboard is empty.")
                return

            from io import StringIO
            data = pd.read_csv(StringIO(text), sep='\t')

            if self.data_view.has_data():
                choice_box = QMessageBox(self)
                choice_box.setWindowTitle("Paste Options")
                choice_box.setText("How do you want to apply clipboard data?")
                overwrite_btn = choice_box.addButton("Overwrite existing data", QMessageBox.AcceptRole)
                append_btn = choice_box.addButton("Append to existing data", QMessageBox.ActionRole)
                cancel_btn = choice_box.addButton("Cancel", QMessageBox.RejectRole)
                choice_box.setDefaultButton(overwrite_btn)
                choice_box.exec()

                if choice_box.clickedButton() == cancel_btn:
                    return

                if choice_box.clickedButton() == append_btn:
                    try:
                        self.data_view.append_data(data)
                    except ValueError as e:
                        QMessageBox.critical(self, "Error", str(e))
                        return
                    total_rows = len(self.data_view.get_data()) if self.data_view.has_data() else len(data)
                    self.status_label.setText("Appended clipboard data to existing data.")
                    QMessageBox.information(
                        self,
                        "Done",
                        f"Appended {len(data)} rows. (Total {total_rows} rows)",
                    )
                    return

            self.data_view.set_data(data)
            self.status_label.setText("Loaded data from clipboard.")
            QMessageBox.information(
                self,
                "Done",
                f"Loaded {len(data)} rows and {len(data.columns)} columns from clipboard.",
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Clipboard paste failed:\n{str(e)}")
    def connect_to_database(self):
        """데이터베이스 연결"""
        self.status_label.setText("데이터베이스 연결 기능을 준비 중입니다.")
        QMessageBox.information(self, "알림", "데이터베이스 연결 기능은 향후 버전에서 제공될 예정입니다.")
        # TODO: 데이터베이스 연결 다이얼로그 구현
    
    # 데이터 편집 메서드들
    def insert_row(self):
        """Insert row"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to edit.")
            return
        self.data_view.insert_row()
        self.status_label.setText("Inserted a row.")
    def delete_row(self):
        """Delete row"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to edit.")
            return
        if self.data_view.table.currentRow() < 0:
            QMessageBox.information(self, "Notice", "Select a row to delete.")
            return
        self.data_view.delete_row()
        self.status_label.setText("Deleted a row.")
    def insert_column(self):
        """Insert column"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to edit.")
            return
        df = self.data_view.get_data()
        if df is None:
            QMessageBox.information(self, "Notice", "No data to edit.")
            return
        default_name = f"Column_{len(df.columns) + 1}"
        col_name, ok = QInputDialog.getText(
            self, "Insert Column", "Column name:", QLineEdit.Normal, default_name
        )
        if not ok or not col_name:
            return
        if col_name in df.columns:
            QMessageBox.warning(self, "Warning", "Column name already exists.")
            return

        target = self.data_view.table.currentColumn()
        if target < 0:
            target = len(df.columns)

        df = df.copy()
        df[col_name] = None
        cols = list(df.columns)
        cols.remove(col_name)
        cols.insert(target, col_name)
        df = df[cols]

        self.data_view.set_data(df)
        self.status_label.setText("Inserted a column.")
    def delete_column(self):
        """Delete column"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to edit.")
            return
        if self.data_view.table.currentColumn() < 0:
            QMessageBox.information(self, "Notice", "Select a column to delete.")
            return
        self.data_view.delete_column()
        self.status_label.setText("Deleted a column.")
    def sort_ascending(self):
        """Sort ascending"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to sort.")
            return
        df = self.data_view.get_data()
        if df is None:
            QMessageBox.information(self, "Notice", "No data to sort.")
            return
        col = self.data_view.table.currentColumn()
        if col < 0:
            QMessageBox.information(self, "Notice", "Select a column to sort.")
            return
        try:
            col_name = df.columns[col]
            sorted_df = df.sort_values(by=col_name, ascending=True, kind="mergesort")
            self.data_view.set_data(sorted_df)
            self.status_label.setText(f"Sorted ascending by '{col_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Sort failed:\n{str(e)}")
    def sort_descending(self):
        """Sort descending"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to sort.")
            return
        df = self.data_view.get_data()
        if df is None:
            QMessageBox.information(self, "Notice", "No data to sort.")
            return
        col = self.data_view.table.currentColumn()
        if col < 0:
            QMessageBox.information(self, "Notice", "Select a column to sort.")
            return
        try:
            col_name = df.columns[col]
            sorted_df = df.sort_values(by=col_name, ascending=False, kind="mergesort")
            self.data_view.set_data(sorted_df)
            self.status_label.setText(f"Sorted descending by '{col_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Sort failed:\n{str(e)}")
    def find_replace_data(self):
        """Find and replace"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to search.")
            return
        df = self.data_view.get_data()
        if df is None:
            QMessageBox.information(self, "Notice", "No data to search.")
            return

        find_text, ok = QInputDialog.getText(self, "Find/Replace", "Find value:")
        if not ok:
            return
        replace_text, ok = QInputDialog.getText(self, "Find/Replace", "Replace with:")
        if not ok:
            return

        columns = ["(All columns)"] + list(df.columns)
        col, ok = QInputDialog.getItem(self, "Find/Replace", "Target column:", columns, 0, False)
        if not ok:
            return

        def _replace_series(series, find_val, replace_val):
            try:
                return series.replace(find_val, replace_val)
            except Exception:
                return series

        updated = df.copy()
        if col == "(All columns)":
            for c in updated.columns:
                updated[c] = _replace_series(updated[c], find_text, replace_text)
        else:
            updated[col] = _replace_series(updated[col], find_text, replace_text)

        self.data_view.set_data(updated)
        self.status_label.setText("Find/replace completed.")
    def rename_variables(self):
        """Rename variable"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to rename.")
            return
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "Notice", "No data to rename.")
            return

        col, ok = QInputDialog.getItem(
            self, "Rename Variable", "Select column:", list(df.columns), 0, False
        )
        if not ok or not col:
            return

        new_name, ok = QInputDialog.getText(
            self, "Rename Variable", "New column name:", QLineEdit.Normal, col
        )
        if not ok or not new_name:
            return
        if new_name in df.columns and new_name != col:
            QMessageBox.warning(self, "Warning", "Column name already exists.")
            return

        updated = df.rename(columns={col: new_name})
        self.data_view.set_data(updated)
        self.status_label.setText(f"Renamed '{col}' to '{new_name}'.")
    def change_data_types(self):
        """Change data types"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to change.")
            return
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "Notice", "No data to change.")
            return

        col, ok = QInputDialog.getItem(
            self, "Change Type", "Select column:", list(df.columns), 0, False
        )
        if not ok or not col:
            return

        type_options = [
            "Int",
            "Float",
            "String",
            "DateTime",
            "Category",
        ]
        dtype_label, ok = QInputDialog.getItem(
            self, "Change Type", "Select type:", type_options, 0, False
        )
        if not ok or not dtype_label:
            return

        updated = df.copy()
        error_rows = []
        converted = None
        try:
            if dtype_label == "Int":
                converted = pd.to_numeric(updated[col], errors="coerce").astype("Int64")
            elif dtype_label == "Float":
                converted = pd.to_numeric(updated[col], errors="coerce").astype(float)
            elif dtype_label == "String":
                converted = updated[col].astype(str)
            elif dtype_label == "DateTime":
                converted = pd.to_datetime(updated[col], errors="coerce")
            elif dtype_label == "Category":
                converted = updated[col].astype("category")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Type conversion failed:\n{str(e)}")
            return

        if converted is None:
            return

        if dtype_label in ("Int", "Float", "DateTime"):
            mask = converted.isna() & updated[col].notna()
            error_rows = updated.index[mask].tolist()

        preview_df = pd.DataFrame({
            f"{col} (orig)": updated[col],
            f"{col} (new)": converted,
        }).head(10)

        dialog = QDialog(self)
        dialog.setWindowTitle("Type Change Preview")
        dialog.setModal(True)
        dialog.resize(640, 520)

        layout = QVBoxLayout(dialog)
        preview_label = QLabel("Preview (top 10 rows)")
        layout.addWidget(preview_label)

        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setFont(QFont("Consolas", 9))
        preview_text.setPlainText(preview_df.to_string(index=True))
        layout.addWidget(preview_text)

        error_label = QLabel(f"Potential error rows: {len(error_rows)}")
        layout.addWidget(error_label)

        error_text = QTextEdit()
        error_text.setReadOnly(True)
        error_text.setFont(QFont("Consolas", 9))
        if error_rows:
            head_rows = error_rows[:50]
            tail_note = "" if len(error_rows) <= 50 else f"\n {len(error_rows) - 50} more"
            error_text.setPlainText("Row indices:\n" + ", ".join(map(str, head_rows)) + tail_note)
        else:
            error_text.setPlainText("No error rows detected.")
        layout.addWidget(error_text)

        strict_check = QCheckBox("Abort if errors exist")
        strict_check.setChecked(True)
        layout.addWidget(strict_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        if strict_check.isChecked() and error_rows:
            QMessageBox.information(self, "Notice", "Conversion aborted due to error rows.")
            return

        updated[col] = converted
        self.data_view.set_data(updated)
        self.status_label.setText(f"Changed type of '{col}'.")
    def create_derived_variable(self):
        """Create derived variable"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to derive from.")
            return
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "Notice", "No data to derive from.")
            return

        new_col, ok = QInputDialog.getText(
            self, "Derived Variable", "New column name:"
        )
        if not ok or not new_col:
            return
        if new_col in df.columns:
            QMessageBox.warning(self, "Warning", "Column name already exists.")
            return

        formula, ok = QInputDialog.getText(
            self, "Derived Variable", "Formula (e.g., A + B * 2):"
        )
        if not ok or not formula:
            return

        updated = df.copy()
        try:
            derived = updated.eval(formula)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compute derived variable:\n{str(e)}")
            return

        error_rows = []
        try:
            mask = derived.isna()
            try:
                mask = mask | np.isinf(derived.astype(float))
            except Exception:
                pass
            error_rows = updated.index[mask].tolist()
        except Exception:
            error_rows = []

        preview_df = updated.copy()
        preview_df[new_col] = derived
        preview_preview = preview_df[[new_col]].head(10)

        dialog = QDialog(self)
        dialog.setWindowTitle("Derived Variable Preview")
        dialog.setModal(True)
        dialog.resize(640, 520)

        layout = QVBoxLayout(dialog)
        preview_label = QLabel("Preview (top 10 rows)")
        layout.addWidget(preview_label)

        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setFont(QFont("Consolas", 9))
        preview_text.setPlainText(preview_preview.to_string(index=True))
        layout.addWidget(preview_text)

        error_label = QLabel(f"NaN/Inf rows: {len(error_rows)}")
        layout.addWidget(error_label)

        error_text = QTextEdit()
        error_text.setReadOnly(True)
        error_text.setFont(QFont("Consolas", 9))
        if error_rows:
            head_rows = error_rows[:50]
            tail_note = "" if len(error_rows) <= 50 else f"\n {len(error_rows) - 50} more"
            error_text.setPlainText("Row indices:\n" + ", ".join(map(str, head_rows)) + tail_note)
        else:
            error_text.setPlainText("No NaN/Inf rows detected.")
        layout.addWidget(error_text)

        strict_check = QCheckBox("Abort if NaN/Inf rows exist")
        strict_check.setChecked(False)
        layout.addWidget(strict_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        if strict_check.isChecked() and error_rows:
            QMessageBox.information(self, "Notice", "Creation aborted due to NaN/Inf rows.")
            return

        updated[new_col] = derived
        self.data_view.set_data(updated)
        self.status_label.setText(f"Created derived column '{new_col}'.")
    def create_dummy_variables(self):
        """Create dummy variables"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to transform.")
            return
        df = self.data_view.get_data()
        if df is None or df.empty:
            QMessageBox.information(self, "Notice", "No data to transform.")
            return

        col, ok = QInputDialog.getItem(
            self, "Create Dummies", "Select column:", list(df.columns), 0, False
        )
        if not ok or not col:
            return

        drop_first = QMessageBox.question(
            self, "Create Dummies", "Drop first category?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes

        remove_original = QMessageBox.question(
            self, "Create Dummies", "Remove original column?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes

        try:
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=drop_first)
            if remove_original:
                updated = df.drop(columns=[col])
            else:
                updated = df.copy()
            updated = pd.concat([updated, dummies], axis=1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Dummy creation failed:\n{str(e)}")
            return

        self.data_view.set_data(updated)
        self.status_label.setText(f"Created dummy variables for '{col}'.")
    def merge_data(self):
        """Merge data"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No base data to merge.")
            return

        base_df = self.data_view.get_data()
        if base_df is None or base_df.empty:
            QMessageBox.information(self, "Notice", "No base data to merge.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select data to merge", "",
            "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*)"
        )
        if not file_path:
            return

        try:
            other_df = self.data_view.read_dataframe_from_file(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read data:\n{str(e)}")
            return

        common_cols = [c for c in base_df.columns if c in other_df.columns]
        if not common_cols:
            QMessageBox.information(self, "Notice", "No common columns found.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Merge Options")
        dialog.setModal(True)
        dialog.resize(520, 480)

        layout = QVBoxLayout(dialog)
        key_label = QLabel("Merge keys (multi-select)")
        layout.addWidget(key_label)

        key_list = QListWidget()
        key_list.setSelectionMode(QListWidget.MultiSelection)
        for col_name in common_cols:
            key_list.addItem(col_name)
        if common_cols:
            key_list.item(0).setSelected(True)
        layout.addWidget(key_list)

        form = QFormLayout()
        join_combo = QComboBox()
        join_map = {
            "inner": "inner",
            "left": "left",
            "right": "right",
            "outer": "outer",
        }
        for label in join_map.keys():
            join_combo.addItem(label)
        form.addRow("Join type", join_combo)

        left_suffix_edit = QLineEdit("_left")
        right_suffix_edit = QLineEdit("_right")
        form.addRow("Left suffix", left_suffix_edit)
        form.addRow("Right suffix", right_suffix_edit)

        drop_right_check = QCheckBox("Drop right-side overlapping columns (except keys)")
        form.addRow("", drop_right_check)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        keys = [item.text() for item in key_list.selectedItems()]
        if not keys:
            QMessageBox.information(self, "Notice", "Select at least one merge key.")
            return

        join_label = join_combo.currentText()
        left_suffix = left_suffix_edit.text().strip() or "_left"
        right_suffix = right_suffix_edit.text().strip() or "_right"

        try:
            merged = pd.merge(
                base_df,
                other_df,
                on=keys,
                how=join_map[join_label],
                suffixes=(left_suffix, right_suffix),
            )
            if drop_right_check.isChecked():
                overlap = set(base_df.columns) & set(other_df.columns) - set(keys)
                right_cols = [f"{col}{right_suffix}" for col in overlap]
                merged = merged.drop(columns=[c for c in right_cols if c in merged.columns])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Merge failed:\n{str(e)}")
            return

        self.data_view.set_data(merged)
        self.status_label.setText(f"Merge completed: {len(merged)} rows")
    def split_data(self):
        """데이터 분할"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "분할할 데이터가 없습니다.")
            return
        
        self.status_label.setText("데이터 분할 다이얼로그를 실행합니다.")
        # TODO: 데이터 분할 다이얼로그 구현
        QMessageBox.information(self, "알림", "데이터 분할 기능은 구현 예정입니다.")
    
    def remove_duplicates(self):
        """중복값 제거"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "처리할 데이터가 없습니다.")
            return
        
        try:
            data = self.data_view.get_data()
            original_count = len(data)
            
            # 중복값 제거
            data_cleaned = data.drop_duplicates()
            removed_count = original_count - len(data_cleaned)
            
            if removed_count > 0:
                # 데이터 뷰 업데이트
                self.data_view.set_data(data_cleaned)
                self.status_label.setText(f"중복값 {removed_count}개가 제거되었습니다.")
                QMessageBox.information(self, "완료", 
                    f"중복값 제거가 완료되었습니다.\n\n"
                    f"원본 행 수: {original_count}\n"
                    f"제거된 행 수: {removed_count}\n"
                    f"남은 행 수: {len(data_cleaned)}")
            else:
                self.status_label.setText("중복값이 발견되지 않았습니다.")
                QMessageBox.information(self, "알림", "중복값이 발견되지 않았습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"중복값 제거 중 오류가 발생했습니다:\n{str(e)}")
    
    # 데이터 뷰 메서드들
    def show_data_summary(self):
        """데이터 요약 정보 표시"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "요약할 데이터가 없습니다.")
            return
        
        try:
            data = self.data_view.get_data()
            
            # 기본 정보
            summary = f"데이터 요약 정보\n{'='*50}\n\n"
            summary += f"행 수: {len(data):,}\n"
            summary += f"열 수: {len(data.columns)}\n"
            summary += f"메모리 사용량: {data.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n\n"
            
            # 데이터 타입별 개수
            summary += "데이터 타입별 변수 개수:\n"
            type_counts = data.dtypes.value_counts()
            for dtype, count in type_counts.items():
                summary += f"  {dtype}: {count}개\n"
            
            # 결측값 정보
            missing_counts = data.isnull().sum()
            total_missing = missing_counts.sum()
            if total_missing > 0:
                summary += f"\n결측값: 총 {total_missing}개\n"
                for col, count in missing_counts[missing_counts > 0].items():
                    percentage = (count / len(data)) * 100
                    summary += f"  {col}: {count}개 ({percentage:.1f}%)\n"
            else:
                summary += "\n결측값: 없음\n"
            
            # 결과를 다이얼로그로 표시
            dialog = QDialog(self)
            dialog.setWindowTitle("데이터 요약 정보")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(summary)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            close_btn = QPushButton("닫기")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
            self.status_label.setText("데이터 요약 정보를 표시했습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 요약 정보 생성 중 오류가 발생했습니다:\n{str(e)}")
    
    def show_variable_info(self):
        """Show variable info"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "Notice", "No data to analyze.")
            return
        try:
            data = self.data_view.get_data()
            if data is None:
                QMessageBox.information(self, "Notice", "No data to analyze.")
                return

            info_lines = []
            info_lines.append("Variable Info")
            info_lines.append("=" * 50)
            info_lines.append(f"Columns: {len(data.columns)}")
            info_lines.append("")

            for col in data.columns:
                series = data[col]
                dtype = series.dtype
                non_null = series.notna().sum()
                missing = series.isna().sum()
                unique = series.nunique(dropna=True)

                info_lines.append(f"[{col}]")
                info_lines.append(f"  Type: {dtype}")
                info_lines.append(f"  Non-null: {non_null} / Missing: {missing}")
                info_lines.append(f"  Unique: {unique}")

                if pd.api.types.is_numeric_dtype(series):
                    desc = series.describe()
                    mean_val = desc.get("mean", float("nan"))
                    std_val = desc.get("std", float("nan"))
                    min_val = desc.get("min", float("nan"))
                    max_val = desc.get("max", float("nan"))
                    info_lines.append(
                        f"  Mean: {mean_val:.4g}, Std: {std_val:.4g}, Min: {min_val:.4g}, Max: {max_val:.4g}"
                    )
                info_lines.append("")

            dialog = QDialog(self)
            dialog.setWindowTitle("Variable Info")
            dialog.setModal(True)
            dialog.resize(600, 500)

            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setPlainText("\n".join(info_lines))
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 9))
            layout.addWidget(text_edit)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()
            self.status_label.setText("Displayed variable info.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to build variable info:\n{str(e)}")
    def show_data_preview(self):
        """데이터 미리보기"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "미리볼 데이터가 없습니다.")
            return
        
        try:
            data = self.data_view.get_data()
            
            preview = "데이터 미리보기\n" + "="*50 + "\n\n"
            preview += f"전체 데이터: {len(data)}행 × {len(data.columns)}열\n\n"
            
            # 처음 5행
            preview += "처음 5행:\n" + "-"*30 + "\n"
            preview += data.head().to_string() + "\n\n"
            
            # 마지막 5행
            if len(data) > 5:
                preview += "마지막 5행:\n" + "-"*30 + "\n"
                preview += data.tail().to_string() + "\n"
            
            # 결과를 다이얼로그로 표시
            dialog = QDialog(self)
            dialog.setWindowTitle("데이터 미리보기")
            dialog.setModal(True)
            dialog.resize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(preview)
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Consolas", 9))  # 고정폭 폰트 사용
            layout.addWidget(text_edit)
            
            close_btn = QPushButton("닫기")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
            self.status_label.setText("데이터 미리보기를 표시했습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 미리보기 생성 중 오류가 발생했습니다:\n{str(e)}")
    
    def set_data_filter(self):
        """데이터 필터 설정"""
        if not self.data_view.has_data():
            QMessageBox.information(self, "알림", "필터를 설정할 데이터가 없습니다.")
            return
        df = self.data_view.get_data()
        columns = list(df.columns)
        if not columns:
            QMessageBox.information(self, "알림", "필터를 설정할 열이 없습니다.")
            return

        col, ok = QInputDialog.getItem(self, "데이터 필터", "필터할 열을 선택하세요:", columns, 0, False)
        if not ok or not col:
            return

        # 선택된 열의 고유값 목록
        try:
            unique_vals = df[col].dropna().astype(str).unique().tolist()
        except Exception:
            unique_vals = []
        if not unique_vals:
            QMessageBox.information(self, "알림", f"열 '{col}'에 필터할 값이 없습니다.")
            return
        unique_vals = sorted(unique_vals)

        val, ok = QInputDialog.getItem(self, "데이터 필터", f"'{col}' 값을 선택하세요:", unique_vals, 0, False)
        if not ok or val is None:
            return

        filtered = df[df[col].astype(str) == val].copy()
        if filtered.empty:
            QMessageBox.information(self, "알림", f"{col}={val} 에 해당하는 데이터가 없습니다.")
            return

        # 뷰/탭에 필터된 데이터 반영 (프로젝트 원본은 유지)
        self.data_view.set_data(filtered)
        self.chart_view.clear_charts()
        self.chart_view.set_data(filtered)
        self.results_view.clear_results()
        self.results_view.set_data(filtered)
        self.project_explorer.set_data(filtered, f"필터 적용: {col}={val}")

        self.status_label.setText(f"필터 적용: {col}={val} ({len(filtered)}행)")
    
    def clear_data_filter(self):
        """데이터 필터 해제"""
        project = self.project_controller.current_project
        if project is None or project.dataframe is None or project.dataframe.empty:
            QMessageBox.information(self, "알림", "복원할 원본 데이터가 없습니다.")
            return

        df = project.dataframe
        self.data_view.set_data(df)
        self.chart_view.clear_charts()
        self.chart_view.set_data(df)
        self.results_view.clear_results()
        self.results_view.set_data(df)
        self.project_explorer.set_data(df, project.data_description)

        self.status_label.setText("데이터 필터를 해제했습니다.")

    def handle_analysis_request(self, request):
        """분석 요청 처리"""
        try:
            if request == "basic_stats":
                self.run_basic_statistics()
            elif request == "one_way_anova":
                self.run_one_way_anova()
            elif request == "two_way_anova":
                self.run_two_way_anova()
            elif request == "correlation_analysis":
                self.run_correlation_analysis_impl()
            elif request in ["multi_way_anova", "repeated_anova", "simple_regression", 
                           "multiple_regression", "stepwise_regression", "nonlinear_regression",
                           "mann_whitney_test", "kruskal_wallis_test", "wilcoxon_test",
                           "pca_analysis", "cluster_analysis", "discriminant_analysis"]:
                # 아직 구현되지 않은 분석들
                analysis_names = {
                    "multi_way_anova": "다원분산분석",
                    "repeated_anova": "반복측정분산분석", 
                    "simple_regression": "단순회귀분석",
                    "multiple_regression": "다중회귀분석",
                    "stepwise_regression": "단계적회귀분석",
                    "nonlinear_regression": "비선형회귀분석",
                    "correlation_analysis": "상관분석",
                    "mann_whitney_test": "Mann-Whitney U 검정",
                    "kruskal_wallis_test": "Kruskal-Wallis 검정",
                    "wilcoxon_test": "Wilcoxon 부호순위 검정",
                    "pca_analysis": "주성분분석",
                    "cluster_analysis": "군집분석",
                    "discriminant_analysis": "판별분석"
                }
                analysis_name = analysis_names.get(request, request)
                self.show_analysis_guide(analysis_name)
            else:
                QMessageBox.critical(self, "오류", f"알 수 없는 분석 요청: {request}")
        except Exception as e:
            QMessageBox.critical(self, "분석 오류", f"분석 중 오류가 발생했습니다:\n{str(e)}")
            self.status_label.setText("분석 실패")

    def run_one_way_anova(self):
        """일원분산분석 실제 구현"""
        # 현재 데이터 확인
        current_data = None
        if self.data_view.has_data():
            current_data = self.data_view.get_data()
        
        # 데이터 검증
        is_valid, message = self.validate_data_for_analysis('일원분산분석', current_data)
        
        if not is_valid:
            # 데이터가 없거나 부적합한 경우 스마트 가이드 표시
            self.show_smart_analysis_guide('일원분산분석', current_data, message)
            return
            
        try:
            # 데이터 가져오기
            data = current_data.copy()
            
            # 범주형 변수와 수치형 변수 찾기
            categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            
            if len(categorical_cols) == 0 or len(numeric_cols) == 0:
                QMessageBox.warning(self, "데이터 오류", "일원분산분석을 위해서는 최소 1개의 그룹 변수(텍스트)와 1개의 측정값(숫자)이 필요합니다.")
                return
            
            # 첫 번째 범주형 변수를 그룹 변수로, 첫 번째 수치형 변수를 종속 변수로 사용
            group_col = categorical_cols[0]
            value_col = numeric_cols[0]
            
            # 결측값 제거
            clean_data = data[[group_col, value_col]].dropna()
            
            if len(clean_data) < 6:
                QMessageBox.warning(self, "데이터 부족", f"분석을 위해서는 최소 6개 이상의 유효한 데이터가 필요합니다. (현재: {len(clean_data)}개)")
                return
            
            # 그룹별 데이터 분리
            groups = []
            group_names = clean_data[group_col].unique()
            
            for group_name in group_names:
                group_data = clean_data[clean_data[group_col] == group_name][value_col]
                if len(group_data) > 0:
                    groups.append(group_data.values)
            
            if len(groups) < 2:
                QMessageBox.warning(self, "그룹 부족", f"분석을 위해서는 최소 2개 이상의 그룹이 필요합니다. (현재: {len(groups)}개)")
                return
            
            # 각 그룹의 최소 크기 확인
            min_group_size = min(len(group) for group in groups)
            if min_group_size < 2:
                QMessageBox.warning(self, "그룹 크기 부족", "각 그룹은 최소 2개 이상의 데이터가 필요합니다.")
                return
            
            # 일원분산분석 수행
            from scipy.stats import f_oneway
            f_stat, p_value = f_oneway(*groups)
            
            # 기술통계 계산
            group_stats = []
            for i, group_name in enumerate(group_names):
                group_data = groups[i]
                stats = {
                    'group': str(group_name),
                    'n': len(group_data),
                    'mean': float(np.mean(group_data)),
                    'std': float(np.std(group_data, ddof=1)),
                    'min': float(np.min(group_data)),
                    'max': float(np.max(group_data))
                }
                group_stats.append(stats)
            
            # 결과 구성
            result = {
                'type': '일원분산분석',
                'group_variable': group_col,
                'dependent_variable': value_col,
                'groups': [str(name) for name in group_names],
                'group_statistics': group_stats,
                'f_statistic': float(f_stat),
                'p_value': float(p_value),
                'degrees_of_freedom': [len(groups) - 1, sum(len(g) for g in groups) - len(groups)],
                'interpretation': '유의함' if p_value < 0.05 else '유의하지 않음',
                'conclusion': f"F({len(groups) - 1}, {sum(len(g) for g in groups) - len(groups)}) = {f_stat:.4f}, p = {p_value:.4f}",
                'sample_size': len(clean_data),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 결과를 프로젝트 탐색기와 결과 뷰에 추가
            self.project_explorer.add_analysis_result('일원분산분석', result, '완료')
            self.results_view.add_analysis_result('일원분산분석', result)
            
            # 결과 탭으로 이동
            self.tab_widget.setCurrentWidget(self.results_view)
            
            self.status_label.setText(f"일원분산분석 완료: F = {f_stat:.4f}, p = {p_value:.4f}")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"일원분산분석 중 오류가 발생했습니다:\n{str(e)}")
            self.status_label.setText("일원분산분석 실패")
            print(f"일원분산분석 오류 상세: {e}")  # 디버깅용

    def run_two_way_anova(self):
        """이원분산분석 실제 구현"""
        # 현재 데이터 확인
        current_data = None
        if self.data_view.has_data():
            current_data = self.data_view.get_data()
        
        # 데이터 검증
        is_valid, message = self.validate_data_for_analysis('이원분산분석', current_data)
        
        if not is_valid:
            # 데이터가 없거나 부적합한 경우 스마트 가이드 표시
            self.show_smart_analysis_guide('이원분산분석', current_data, message)
            return
            
        try:
            # 데이터 가져오기
            data = current_data.copy()
            
            # 범주형 변수와 수치형 변수 찾기
            categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            
            if len(categorical_cols) < 2 or len(numeric_cols) == 0:
                QMessageBox.warning(self, "데이터 오류", "이원분산분석을 위해서는 최소 2개의 그룹 변수(텍스트)와 1개의 측정값(숫자)이 필요합니다.")
                return
            
            # 처음 두 범주형 변수를 요인으로, 첫 번째 수치형 변수를 종속 변수로 사용
            factor1_col = categorical_cols[0]
            factor2_col = categorical_cols[1]
            value_col = numeric_cols[0]
            
            # 결측값 제거
            clean_data = data[[factor1_col, factor2_col, value_col]].dropna()
            
            if len(clean_data) < 8:
                QMessageBox.warning(self, "데이터 부족", f"분석을 위해서는 최소 8개 이상의 유효한 데이터가 필요합니다. (현재: {len(clean_data)}개)")
                return
            
            # 각 조합별 데이터 개수 확인
            combination_counts = clean_data.groupby([factor1_col, factor2_col]).size()
            if combination_counts.min() < 1:
                QMessageBox.warning(self, "조합 부족", "각 요인 조합별로 최소 1개 이상의 데이터가 필요합니다.")
                return
            
            # 이원분산분석 수행 (statsmodels 사용)
            import statsmodels.api as sm
            from statsmodels.formula.api import ols
            
            # 공식 생성 - 컬럼명에 공백이나 특수문자가 있을 수 있으므로 Q() 사용
            formula = f"Q('{value_col}') ~ C(Q('{factor1_col}')) + C(Q('{factor2_col}')) + C(Q('{factor1_col}')):C(Q('{factor2_col}'))"
            
            # 모델 적합
            model = ols(formula, data=clean_data).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)
            
            # 결과 구성
            result = {
                'type': '이원분산분석',
                'factor1': factor1_col,
                'factor2': factor2_col,
                'dependent_variable': value_col,
                'anova_table': anova_table.to_dict(),
                'model_summary': {
                    'r_squared': float(model.rsquared),
                    'adj_r_squared': float(model.rsquared_adj),
                    'f_statistic': float(model.fvalue),
                    'p_value': float(model.f_pvalue)
                },
                'sample_size': len(clean_data),
                'coefficients': model.params.to_dict(),
                'residuals_summary': model.resid.describe().to_dict(),
                'f_statistic': float(model.fvalue),
                'p_value': float(model.f_pvalue),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 결과를 프로젝트 탐색기와 결과 뷰에 추가
            self.project_explorer.add_analysis_result('이원분산분석', result, '완료')
            self.results_view.add_analysis_result('이원분산분석', result)
            
            # 결과 탭으로 이동
            self.tab_widget.setCurrentWidget(self.results_view)
            
            self.status_label.setText(f"이원분산분석 완료: R² = {result['model_summary']['r_squared']:.4f}")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"이원분산분석 중 오류가 발생했습니다:\n{str(e)}")
            self.status_label.setText("이원분산분석 실패")
            print(f"이원분산분석 오류 상세: {e}")  # 디버깅용

    def show_analysis_guide(self, analysis_type, current_data_info=None):
        """분석 가이드 다이얼로그 표시"""
        if AnalysisGuideDialog:
            try:
                # 현재 데이터 정보가 없다면 기본값 생성
                if not current_data_info:
                    if hasattr(self, 'data_view') and self.data_view.has_data():
                        data = self.data_view.get_data()
                        current_data_info = {
                            'rows': len(data),
                            'cols': len(data.columns),
                            'numeric_cols': data.select_dtypes(include=['number']).columns.tolist(),
                            'categorical_cols': data.select_dtypes(include=['object', 'category']).columns.tolist()
                        }
                    else:
                        current_data_info = {
                            'rows': 0,
                            'cols': 0,
                            'numeric_cols': [],
                            'categorical_cols': []
                        }
                
                # 가이드 다이얼로그 생성 및 표시
                guide_dialog = AnalysisGuideDialog(analysis_type, current_data_info, self)
                guide_dialog.exec()
                
            except Exception as e:
                # 가이드 다이얼로그에 오류가 있으면 기본 메시지 표시
                QMessageBox.information(self, f"{analysis_type} 안내", 
                    f"{analysis_type}을 실행하기 위해서는 적절한 형식의 데이터가 필요합니다.\n"
                    f"현재 데이터: {current_data_info.get('rows', 0)}행, {current_data_info.get('cols', 0)}열\n"
                    f"도움말을 참조하거나 샘플 데이터를 사용해보세요.")
        else:
            # 가이드 다이얼로그를 불러올 수 없으면 기본 메시지 표시
            QMessageBox.information(self, f"{analysis_type} 안내", 
                f"{analysis_type}을 실행하기 위해서는 적절한 형식의 데이터가 필요합니다.\n"
                f"현재 데이터: {current_data_info.get('rows', 0) if current_data_info else 0}행, "
                f"{current_data_info.get('cols', 0) if current_data_info else 0}열\n"
                f"도움말을 참조하거나 샘플 데이터를 사용해보세요.")
    
    def import_sample_data(self, filename):
        """샘플 데이터 가져오기"""
        try:
            # data 폴더에서 샘플 파일 찾기
            sample_path = os.path.join('data', filename)
            if not os.path.exists(sample_path):
                # 현재 디렉토리에서 찾기
                if os.path.exists(filename):
                    sample_path = filename
                else:
                    raise FileNotFoundError(f"샘플 파일을 찾을 수 없습니다: {filename}")
            
            # 파일 확장자에 따라 적절한 방법으로 읽기
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                data = pd.read_excel(sample_path)
            elif filename.endswith('.csv'):
                data = pd.read_csv(sample_path)
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {filename}")
            
            # 데이터 설정
            if hasattr(self, 'data_view'):
                self.data_view.set_data(data)
            
            if hasattr(self, 'project_explorer'):
                self.project_explorer.set_data(data, f"샘플 데이터: {filename}")
            
            if hasattr(self, 'results_view'):
                self.results_view.set_data(data)
            
            # 데이터 탭으로 이동
            if hasattr(self, 'tab_widget'):
                self.tab_widget.setCurrentWidget(self.data_view)
            
            self.status_label.setText(f"샘플 데이터 '{filename}'을 불러왔습니다.")
            QMessageBox.information(self, "샘플 데이터", f"샘플 데이터 '{filename}'을 성공적으로 불러왔습니다.")
            
        except Exception as e:
            QMessageBox.warning(self, "오류", f"샘플 데이터를 불러오는 중 오류가 발생했습니다:\n{str(e)}")
    
    def run_basic_statistics(self):
        """기초 통계 분석 실제 구현"""
        # 현재 데이터 확인
        current_data = None
        if self.data_view.has_data():
            current_data = self.data_view.get_data()
        
        # 데이터 검증
        is_valid, message = self.validate_data_for_analysis('기초 통계', current_data)
        
        if not is_valid:
            # 데이터가 없거나 부적합한 경우 스마트 가이드 표시
            self.show_smart_analysis_guide('기초 통계', current_data, message)
            return
            
        try:
            # 데이터 가져오기
            data = current_data.copy()
            
            # 숫자 컬럼만 선택
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_cols) == 0:
                QMessageBox.warning(self, "데이터 오류", "기초 통계 분석을 위해서는 최소 1개의 숫자형 변수가 필요합니다.")
                return
            
            # 결측값 제거된 데이터로 통계 계산
            numeric_data = data[numeric_cols].dropna()
            
            if len(numeric_data) == 0:
                QMessageBox.warning(self, "데이터 부족", "유효한 숫자 데이터가 없습니다. 결측값을 확인해주세요.")
                return
            
            # 기초 통계 계산
            stats_result = numeric_data.describe()
            
            # 추가 통계량 계산
            additional_stats = {}
            for col in numeric_cols:
                col_data = data[col].dropna()
                if len(col_data) > 0:
                    additional_stats[col] = {
                        'variance': float(col_data.var()),
                        'skewness': float(col_data.skew()),
                        'kurtosis': float(col_data.kurtosis()),
                        'missing_count': int(data[col].isnull().sum()),
                        'missing_percent': float(data[col].isnull().sum() / len(data) * 100)
                    }
            
            # 결과 구성
            result = {
                'type': '기초 통계',
                'statistics': stats_result.to_dict(),
                'additional_statistics': additional_stats,
                'variables': numeric_cols,
                'total_observations': len(data),
                'valid_observations': len(numeric_data),
                'missing_values': data[numeric_cols].isnull().sum().to_dict(),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 결과 추가
            if hasattr(self, 'project_explorer'):
                self.project_explorer.add_analysis_result('기초 통계', result, '완료')
            
            if hasattr(self, 'results_view'):
                self.results_view.add_analysis_result('기초 통계', result)
                self.tab_widget.setCurrentWidget(self.results_view)
            
            self.status_label.setText(f"기초 통계 분석이 완료되었습니다. ({len(numeric_cols)}개 변수)")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"기초 통계 분석 중 오류가 발생했습니다:\n{str(e)}")
            self.status_label.setText("기초 통계 분석 실패")
            print(f"기초 통계 오류 상세: {e}")  # 디버깅용

    def run_correlation_analysis_impl(self):
        """상관분석 실제 구현"""
        # 현재 데이터 확인
        current_data = None
        if self.data_view.has_data():
            current_data = self.data_view.get_data()
        
        # 데이터 검증
        is_valid, message = self.validate_data_for_analysis('상관분석', current_data)
        
        if not is_valid:
            # 데이터가 없거나 부적합한 경우 스마트 가이드 표시
            self.show_smart_analysis_guide('상관분석', current_data, message)
            return
            
        try:
            # 데이터 가져오기
            data = current_data.copy()
            
            # 숫자 컬럼만 선택
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_cols) < 2:
                QMessageBox.warning(self, "데이터 오류", "상관분석을 위해서는 최소 2개의 숫자형 변수가 필요합니다.")
                return
            
            # 결측값 제거된 데이터로 상관분석
            numeric_data = data[numeric_cols].dropna()
            
            if len(numeric_data) < 3:
                QMessageBox.warning(self, "데이터 부족", f"상관분석을 위해서는 최소 3개 이상의 유효한 데이터가 필요합니다. (현재: {len(numeric_data)}개)")
                return
            
            # 상관분석 계산
            correlation_matrix = numeric_data.corr()
            
            # 상관계수의 유의성 검정 (간단한 버전)
            from scipy.stats import pearsonr
            significance_matrix = {}
            for i, col1 in enumerate(numeric_cols):
                significance_matrix[col1] = {}
                for j, col2 in enumerate(numeric_cols):
                    if i != j:
                        try:
                            _, p_value = pearsonr(numeric_data[col1], numeric_data[col2])
                            significance_matrix[col1][col2] = float(p_value)
                        except:
                            significance_matrix[col1][col2] = 1.0
                    else:
                        significance_matrix[col1][col2] = 0.0
            
            # 결과 구성
            result = {
                'type': '상관분석',
                'correlation_matrix': correlation_matrix.to_dict(),
                'significance_matrix': significance_matrix,
                'variables': numeric_cols,
                'sample_size': len(numeric_data),
                'total_observations': len(data),
                'missing_values': data[numeric_cols].isnull().sum().to_dict(),
                'strong_correlations': self._find_strong_correlations(correlation_matrix),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 결과 추가
            if hasattr(self, 'project_explorer'):
                self.project_explorer.add_analysis_result('상관분석', result, '완료')
            
            if hasattr(self, 'results_view'):
                self.results_view.add_analysis_result('상관분석', result)
                self.tab_widget.setCurrentWidget(self.results_view)
            
            self.status_label.setText(f"상관분석이 완료되었습니다. ({len(numeric_cols)}개 변수)")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"상관분석 중 오류가 발생했습니다:\n{str(e)}")
            self.status_label.setText("상관분석 실패")
            print(f"상관분석 오류 상세: {e}")  # 디버깅용

    def _find_strong_correlations(self, correlation_matrix, threshold=0.7):
        """강한 상관관계 찾기"""
        strong_corr = []
        for i, col1 in enumerate(correlation_matrix.columns):
            for j, col2 in enumerate(correlation_matrix.columns):
                if i < j:  # 중복 제거
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) >= threshold:
                        strong_corr.append({
                            'var1': col1,
                            'var2': col2,
                            'correlation': float(corr_value),
                            'strength': 'strong positive' if corr_value > 0 else 'strong negative'
                        })
        return strong_corr

    def get_recommended_sample_data(self, analysis_type):
        """분석 유형에 따른 권장 샘플 데이터 반환"""
        sample_recommendations = {
            '기초 통계': {
                'files': ['basic_statistics_sample.xlsx'],
                'description': '키, 몸무게, 나이, 점수, 온도 데이터 (50행)',
                'reason': '다양한 수치형 변수로 기초 통계량 계산에 적합'
            },
            '상관분석': {
                'files': ['basic_statistics_sample.xlsx'],
                'description': '키, 몸무게, 나이, 점수, 온도 데이터 (50행)',
                'reason': '여러 수치형 변수 간 상관관계 분석에 적합'
            },
            '일원분산분석': {
                'files': ['factorial_2x3_design_categorical.xlsx'],
                'description': '2×3 요인설계 데이터 (24행)',
                'reason': '그룹 변수와 측정값이 포함된 분산분석용 데이터'
            },
            '이원분산분석': {
                'files': ['factorial_2x3_design_categorical.xlsx'],
                'description': '2×3 요인설계 데이터 (24행)',
                'reason': '두 개의 요인과 측정값이 포함된 이원분산분석용 데이터'
            },
            '다원분산분석': {
                'files': ['factorial_2x3_design_categorical.xlsx'],
                'description': '2×3 요인설계 데이터 (24행)',
                'reason': '현재는 이원분산분석으로 대체 가능'
            },
            '단순회귀분석': {
                'files': ['basic_statistics_sample.xlsx'],
                'description': '키, 몸무게, 나이, 점수, 온도 데이터 (50행)',
                'reason': '두 변수 간 선형관계 분석에 적합'
            },
            '다중회귀분석': {
                'files': ['basic_statistics_sample.xlsx'],
                'description': '키, 몸무게, 나이, 점수, 온도 데이터 (50행)',
                'reason': '여러 독립변수와 종속변수 관계 분석에 적합'
            },
            '주성분분석': {
                'files': ['basic_statistics_sample.xlsx'],
                'description': '키, 몸무게, 나이, 점수, 온도 데이터 (50행)',
                'reason': '다차원 데이터의 차원축소 분석에 적합'
            },
            '군집분석': {
                'files': ['basic_statistics_sample.xlsx'],
                'description': '키, 몸무게, 나이, 점수, 온도 데이터 (50행)',
                'reason': '유사한 특성을 가진 데이터 그룹화에 적합'
            }
        }
        
        return sample_recommendations.get(analysis_type, {
            'files': ['basic_statistics_sample.xlsx'],
            'description': '기본 샘플 데이터',
            'reason': '일반적인 분석에 사용 가능'
        })

    def validate_data_for_analysis(self, analysis_type, data):
        """현재 데이터가 분석에 적합한지 검증"""
        if data is None or len(data) == 0:
            return False, "데이터가 없습니다."
        
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
        
        validation_rules = {
            '기초 통계': {
                'min_numeric': 1,
                'min_rows': 3,
                'message': '최소 1개의 수치형 변수와 3행 이상의 데이터가 필요합니다.'
            },
            '상관분석': {
                'min_numeric': 2,
                'min_rows': 5,
                'message': '최소 2개의 수치형 변수와 5행 이상의 데이터가 필요합니다.'
            },
            '일원분산분석': {
                'min_categorical': 1,
                'min_numeric': 1,
                'min_rows': 6,
                'message': '최소 1개의 그룹 변수(텍스트)와 1개의 측정값(숫자), 6행 이상의 데이터가 필요합니다.'
            },
            '이원분산분석': {
                'min_categorical': 2,
                'min_numeric': 1,
                'min_rows': 8,
                'message': '최소 2개의 그룹 변수(텍스트)와 1개의 측정값(숫자), 8행 이상의 데이터가 필요합니다.'
            }
        }
        
        rule = validation_rules.get(analysis_type, {
            'min_numeric': 1,
            'min_rows': 3,
            'message': '적절한 형식의 데이터가 필요합니다.'
        })
        
        # 검증 수행
        if len(data) < rule.get('min_rows', 3):
            return False, f"데이터 행 수가 부족합니다. (현재: {len(data)}행, 필요: {rule.get('min_rows', 3)}행 이상)"
        
        if len(numeric_cols) < rule.get('min_numeric', 0):
            return False, f"수치형 변수가 부족합니다. (현재: {len(numeric_cols)}개, 필요: {rule.get('min_numeric', 0)}개 이상)"
        
        if len(categorical_cols) < rule.get('min_categorical', 0):
            return False, f"그룹 변수가 부족합니다. (현재: {len(categorical_cols)}개, 필요: {rule.get('min_categorical', 0)}개 이상)"
        
        return True, "데이터가 분석에 적합합니다."

    def show_smart_analysis_guide(self, analysis_type, current_data, validation_message):
        """스마트 분석 가이드 - 데이터 상태에 따른 맞춤형 안내"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont, QIcon
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{analysis_type} - 스마트 가이드")
        dialog.setModal(True)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # 제목
        title_label = QLabel(f"📊 {analysis_type} 분석 가이드")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 현재 상태 분석
        status_group = QGroupBox("🔍 현재 데이터 상태")
        status_layout = QVBoxLayout(status_group)
        
        if current_data is None:
            status_text = "❌ 데이터가 없습니다."
            status_color = "color: red;"
        else:
            numeric_cols = current_data.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = current_data.select_dtypes(include=['object', 'category']).columns.tolist()
            
            status_text = f"""
📋 데이터 정보:
• 총 행 수: {len(current_data)}행
• 총 열 수: {len(current_data.columns)}열
• 숫자형 변수: {len(numeric_cols)}개 ({', '.join(numeric_cols[:3])}{'...' if len(numeric_cols) > 3 else ''})
• 그룹형 변수: {len(categorical_cols)}개 ({', '.join(categorical_cols[:3])}{'...' if len(categorical_cols) > 3 else ''})

⚠️ 문제점: {validation_message}
            """
            status_color = "color: orange;"
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet(status_color)
        status_label.setWordWrap(True)
        status_layout.addWidget(status_label)
        layout.addWidget(status_group)
        
        # 권장 샘플 데이터
        recommendation = self.get_recommended_sample_data(analysis_type)
        sample_group = QGroupBox("💡 권장 해결방법")
        sample_layout = QVBoxLayout(sample_group)
        
        sample_text = f"""
📊 권장 샘플 데이터: {recommendation['files'][0]}
📝 설명: {recommendation['description']}
🎯 적합한 이유: {recommendation['reason']}

🚀 사용 방법:
1. 아래 '샘플 데이터 불러오기' 버튼 클릭
2. 자동으로 적절한 샘플 데이터가 로드됩니다
3. 다시 분석 메뉴를 선택하면 분석이 실행됩니다

또는

1. 파일 → 데이터 가져오기로 직접 데이터 불러오기
2. Excel (.xlsx) 또는 CSV (.csv) 파일 선택
3. 데이터 형식이 분석 요구사항에 맞는지 확인
        """
        
        sample_label = QLabel(sample_text)
        sample_label.setWordWrap(True)
        sample_layout.addWidget(sample_label)
        layout.addWidget(sample_group)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        # 샘플 데이터 불러오기 버튼
        load_sample_btn = QPushButton("📊 샘플 데이터 불러오기")
        load_sample_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        def load_sample_and_analyze():
            dialog.accept()
            sample_file = recommendation['files'][0]
            self.import_sample_data(sample_file)
            # 잠시 후 분석 재실행
            QTimer.singleShot(500, lambda: self.retry_analysis(analysis_type))
        
        load_sample_btn.clicked.connect(load_sample_and_analyze)
        button_layout.addWidget(load_sample_btn)
        
        # 직접 데이터 가져오기 버튼
        import_btn = QPushButton("📁 직접 데이터 가져오기")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        def import_and_retry():
            dialog.accept()
            self.import_data()
        
        import_btn.clicked.connect(import_and_retry)
        button_layout.addWidget(import_btn)
        
        # 취소 버튼
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()

    def retry_analysis(self, analysis_type):
        """분석 재시도"""
        analysis_methods = {
            '기초 통계': self.run_basic_statistics,
            '상관분석': self.run_correlation_analysis_impl,
            '일원분산분석': self.run_one_way_anova,
            '이원분산분석': self.run_two_way_anova
        }
        
        method = analysis_methods.get(analysis_type)
        if method:
            method()

  
