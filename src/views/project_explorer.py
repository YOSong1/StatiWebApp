"""
프로젝트 탐색기 뷰
데이터, 분석 결과, 차트 등을 체계적으로 관리
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMenu, QMessageBox, QInputDialog, QSplitter,
    QTextEdit, QGroupBox, QListWidget, QListWidgetItem, QTabWidget, QGridLayout,
    QFileDialog, QStyle
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon
import pandas as pd
from datetime import datetime
import json
from pathlib import Path

class ProjectExplorer(QWidget):
    """프로젝트 탐색기 클래스"""
    
    # 시그널 정의
    data_selected = Signal(object)  # 데이터 선택 시
    analysis_selected = Signal(str, object)  # 분석 결과 선택 시
    chart_selected = Signal(object)  # 차트 선택 시
    
    def __init__(self):
        super().__init__()
        
        self.current_data = None
        self.analysis_history = []
        self.chart_history = []
        self.project_name = "새 프로젝트"
        self.current_data_description = "데이터"
        
        self.setup_ui()
        self.setup_connections()
        self.setup_context_menus()
        
        # 자동 저장 타이머
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_project)
        self.auto_save_timer.start(30000)  # 30초마다 자동 저장
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        
        # 프로젝트 정보 헤더
        self.setup_project_header()
        layout.addWidget(self.project_header)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 데이터 탭
        self.setup_data_tab()
        self.tab_widget.addTab(self.data_tab, "📊 데이터")
        
        # 분석 결과 탭
        self.setup_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "📈 분석")
        
        # 차트 탭
        self.setup_chart_tab()
        self.tab_widget.addTab(self.chart_tab, "📉 차트")
        
        layout.addWidget(self.tab_widget)
        
        # 하단 액션 버튼들
        self.setup_action_buttons()
        layout.addWidget(self.action_buttons)
    
    def setup_project_header(self):
        """프로젝트 헤더 설정"""
        self.project_header = QGroupBox("프로젝트 정보")
        layout = QVBoxLayout(self.project_header)
        
        # 프로젝트 이름
        self.project_name_label = QLabel("새 프로젝트")
        self.project_name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.project_name_label)
        
        # 생성 시간
        self.created_time_label = QLabel(f"생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.created_time_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.created_time_label)
        
        # 통계 정보
        self.stats_label = QLabel("데이터: 0행 | 분석: 0개 | 차트: 0개")
        self.stats_label.setStyleSheet("color: blue; font-size: 10px;")
        layout.addWidget(self.stats_label)
    
    def setup_data_tab(self):
        """데이터 탭 설정"""
        self.data_tab = QWidget()
        layout = QVBoxLayout(self.data_tab)
        
        # 데이터 목록
        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabels(["데이터", "정보"])
        self.data_tree.itemDoubleClicked.connect(self.on_data_item_double_clicked)
        layout.addWidget(self.data_tree)
        
        # 데이터 요약 정보
        self.data_summary = QTextEdit()
        self.data_summary.setMaximumHeight(100)
        self.data_summary.setPlaceholderText("데이터를 선택하면 요약 정보가 표시됩니다")
        layout.addWidget(self.data_summary)
    
    def setup_analysis_tab(self):
        """분석 탭 설정"""
        # 분석 탭 위젯 생성
        self.analysis_tab = QWidget()
        layout = QVBoxLayout(self.analysis_tab)
        
        # 분석 요약 정보
        summary_group = QGroupBox("📊 분석 요약")
        summary_layout = QVBoxLayout(summary_group)
        
        self.analysis_summary_label = QLabel("분석 결과가 없습니다")
        self.analysis_summary_label.setStyleSheet("color: gray; font-style: italic;")
        summary_layout.addWidget(self.analysis_summary_label)
        
        layout.addWidget(summary_group)
        
        # 분석 결과 트리
        results_group = QGroupBox("🔬 분석 결과")
        results_layout = QVBoxLayout(results_group)
        
        self.analysis_tree = QTreeWidget()
        self.analysis_tree.setHeaderLabels(["분석 유형", "상태", "시간"])
        self.analysis_tree.itemDoubleClicked.connect(self.on_analysis_item_double_clicked)
        
        # 컨텍스트 메뉴
        self.analysis_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.analysis_tree.customContextMenuRequested.connect(self.show_analysis_context_menu)
        
        results_layout.addWidget(self.analysis_tree)
        layout.addWidget(results_group)
        
        # 분석 실행 버튼들
        buttons_group = QGroupBox("⚡ 빠른 분석")
        buttons_layout = QGridLayout(buttons_group)
        
        # 기초 통계 버튼
        self.basic_stats_btn = QPushButton("📊 기초 통계")
        self.basic_stats_btn.clicked.connect(self.run_basic_statistics)
        buttons_layout.addWidget(self.basic_stats_btn, 0, 0)
        
        # 상관분석 버튼
        self.correlation_btn = QPushButton("🔗 상관분석")
        self.correlation_btn.clicked.connect(self.run_correlation_analysis)
        buttons_layout.addWidget(self.correlation_btn, 0, 1)
        
        # ANOVA 버튼
        self.anova_btn = QPushButton("🧪 ANOVA")
        self.anova_btn.clicked.connect(self.run_anova)
        buttons_layout.addWidget(self.anova_btn, 1, 0)
        
        # 회귀분석 버튼
        self.regression_btn = QPushButton("📈 회귀분석")
        self.regression_btn.clicked.connect(self.run_regression)
        buttons_layout.addWidget(self.regression_btn, 1, 1)
        
        layout.addWidget(buttons_group)
        
        # 초기에는 버튼들 비활성화
        self.update_analysis_buttons_state(False)
    
    def setup_chart_tab(self):
        """차트 탭 설정"""
        self.chart_tab = QWidget()
        layout = QVBoxLayout(self.chart_tab)
        
        # 차트 히스토리
        self.chart_list = QListWidget()
        self.chart_list.itemDoubleClicked.connect(self.on_chart_item_double_clicked)
        layout.addWidget(self.chart_list)
        
        # 차트 정보
        self.chart_info = QTextEdit()
        self.chart_info.setMaximumHeight(100)
        self.chart_info.setPlaceholderText("차트를 선택하면 정보가 표시됩니다")
        layout.addWidget(self.chart_info)
    
    def setup_action_buttons(self):
        """액션 버튼 설정"""
        self.action_buttons = QWidget()
        layout = QHBoxLayout(self.action_buttons)
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.clicked.connect(self.refresh_all)
        layout.addWidget(self.refresh_btn)
        
        # 내보내기 버튼
        self.export_btn = QPushButton("📤 내보내기")
        self.export_btn.clicked.connect(self.export_project)
        layout.addWidget(self.export_btn)
    
    def setup_connections(self):
        """시그널 연결"""
        self.data_tree.itemSelectionChanged.connect(self.on_data_selection_changed)
        self.chart_list.itemSelectionChanged.connect(self.on_chart_selection_changed)
    
    def setup_context_menus(self):
        """컨텍스트 메뉴 설정"""
        # 데이터 트리 컨텍스트 메뉴
        self.data_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.data_tree.customContextMenuRequested.connect(self.show_data_context_menu)
        
        # 분석 결과 트리 컨텍스트 메뉴
        self.analysis_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.analysis_tree.customContextMenuRequested.connect(self.show_analysis_context_menu)
        
        # 차트 리스트 컨텍스트 메뉴
        self.chart_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chart_list.customContextMenuRequested.connect(self.show_chart_context_menu)
    
    def set_data(self, data, description="데이터"):
        """데이터 설정"""
        # 새로운 데이터가 로드되면 기존 분석 결과 초기화
        data_changed = False
        if data is not None:
            if self.current_data is None:
                data_changed = True
            else:
                try:
                    # 데이터 형태나 내용이 다르면 변경된 것으로 간주
                    data_changed = (data.shape != self.current_data.shape or 
                                  not data.columns.equals(self.current_data.columns) or
                                  not data.equals(self.current_data))
                except:
                    # 비교 중 오류가 발생하면 변경된 것으로 간주
                    data_changed = True
        else:
            data_changed = self.current_data is not None
        
        if data_changed:
            self.clear_analysis_results()
        
        self.current_data = data
        self.current_data_description = description
        
        if data is not None:
            # 데이터 정보 업데이트
            self.add_data_to_tree(data, description)
            self.update_stats()
            
            # 분석 버튼 활성화 (데이터 기반)
            self.update_analysis_buttons_state(data)
        else:
            # 분석 버튼 비활성화
            self.update_analysis_buttons_state(False)
    
    def clear_analysis_results(self):
        """분석 결과 초기화"""
        # 분석 히스토리 초기화
        self.analysis_history.clear()
        
        # 분석 트리 초기화
        self.analysis_tree.clear()
        
        # 차트 히스토리도 초기화
        self.chart_history.clear()
        self.chart_list.clear()
        self.chart_info.clear()
        
        # 분석 요약 초기화
        self.analysis_summary_label.setText("분석 결과가 없습니다")
        self.analysis_summary_label.setStyleSheet("color: gray; font-style: italic;")
        
        # 통계 업데이트
        self.update_stats()
    
    def add_data_to_tree(self, data, name):
        """데이터를 트리에 추가"""
        if data is None:
            return
        
        # 기존 데이터 항목 제거
        self.data_tree.clear()
        
        # 루트 항목 생성
        root_item = QTreeWidgetItem(self.data_tree)
        root_item.setText(0, name)
        root_item.setText(1, f"{data.shape[0]}행 × {data.shape[1]}열")
        root_item.setData(0, Qt.UserRole, {"type": "dataset", "data": data, "name": name})
        
        # 컬럼 정보 추가
        columns_item = QTreeWidgetItem(root_item)
        columns_item.setText(0, "📋 컬럼")
        columns_item.setText(1, f"{len(data.columns)}개")
        
        for col in data.columns:
            col_item = QTreeWidgetItem(columns_item)
            col_item.setText(0, str(col))
            
            # 컬럼 타입과 기본 통계
            if pd.api.types.is_numeric_dtype(data[col]):
                col_type = "숫자형"
                stats = f"평균: {data[col].mean():.2f}"
            else:
                col_type = "범주형"
                stats = f"고유값: {data[col].nunique()}개"
            
            col_item.setText(1, f"{col_type} | {stats}")
            col_item.setData(0, Qt.UserRole, {"type": "column", "column": col, "data": data})
        
        # 기본 통계 정보 추가
        stats_item = QTreeWidgetItem(root_item)
        stats_item.setText(0, "📊 통계")
        stats_item.setText(1, "기본 통계량")
        
        # 숫자형 컬럼 통계
        numeric_cols = data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            numeric_item = QTreeWidgetItem(stats_item)
            numeric_item.setText(0, "숫자형 변수")
            numeric_item.setText(1, f"{len(numeric_cols)}개")
            
            for col in numeric_cols[:5]:  # 최대 5개만 표시
                stat_item = QTreeWidgetItem(numeric_item)
                stat_item.setText(0, col)
                mean_val = data[col].mean()
                std_val = data[col].std()
                stat_item.setText(1, f"μ={mean_val:.2f}, σ={std_val:.2f}")
        
        # 범주형 컬럼 통계
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            categorical_item = QTreeWidgetItem(stats_item)
            categorical_item.setText(0, "범주형 변수")
            categorical_item.setText(1, f"{len(categorical_cols)}개")
            
            for col in categorical_cols[:5]:  # 최대 5개만 표시
                cat_item = QTreeWidgetItem(categorical_item)
                cat_item.setText(0, col)
                unique_count = data[col].nunique()
                most_common = data[col].mode().iloc[0] if len(data[col].mode()) > 0 else "N/A"
                cat_item.setText(1, f"고유값: {unique_count}, 최빈값: {most_common}")
        
        # 트리 확장
        self.data_tree.expandAll()
    
    def add_analysis_result(self, analysis_type, result, status="완료"):
        """분석 결과 추가"""
        item = QTreeWidgetItem(self.analysis_tree)
        item.setText(0, analysis_type)
        item.setText(1, status)
        
        # timestamp 처리 - 문자열인 경우와 datetime 객체인 경우 모두 처리
        timestamp = result.get("timestamp", "")
        if isinstance(timestamp, str):
            # 이미 문자열인 경우 시간 부분만 추출
            if " " in timestamp:
                time_part = timestamp.split(" ")[1]  # "2025-06-15 14:30:25" -> "14:30:25"
            else:
                time_part = timestamp  # 이미 시간 형식인 경우
        else:
            # datetime 객체인 경우
            try:
                time_part = timestamp.strftime("%H:%M:%S")
            except:
                time_part = str(timestamp)
        
        item.setText(2, time_part)
        
        # 결과 데이터 저장
        item.setData(0, Qt.UserRole, result)
        
        # 상태에 따른 아이콘 설정
        if status == "완료":
            item.setIcon(0, self.style().standardIcon(QStyle.SP_DialogApplyButton))
        elif status == "오류":
            item.setIcon(0, self.style().standardIcon(QStyle.SP_DialogCancelButton))
        else:
            item.setIcon(0, self.style().standardIcon(QStyle.SP_DialogHelpButton))
        
        # 분석 요약 업데이트
        self.update_analysis_summary()
    
    def update_analysis_summary(self):
        """분석 요약 정보 업데이트"""
        total_analyses = self.analysis_tree.topLevelItemCount()
        
        if total_analyses == 0:
            self.analysis_summary_label.setText("분석 결과가 없습니다")
            self.analysis_summary_label.setStyleSheet("color: gray; font-style: italic;")
        else:
            # 분석 유형별 개수 계산
            analysis_counts = {}
            for i in range(total_analyses):
                item = self.analysis_tree.topLevelItem(i)
                analysis_type = item.text(0)
                analysis_counts[analysis_type] = analysis_counts.get(analysis_type, 0) + 1
            
            summary_text = f"총 {total_analyses}개 분석 완료\n"
            for analysis_type, count in analysis_counts.items():
                summary_text += f"• {analysis_type}: {count}개\n"
            
            self.analysis_summary_label.setText(summary_text.strip())
            self.analysis_summary_label.setStyleSheet("color: black; font-style: normal;")
    
    def on_data_item_double_clicked(self, item, column):
        """데이터 항목 더블클릭 이벤트"""
        data_info = item.data(0, Qt.UserRole)
        if data_info and data_info.get("type") == "dataset":
            self.data_selected.emit(data_info["data"])
    
    def on_analysis_item_double_clicked(self, item, column):
        """분석 항목 더블클릭 시 - 상세 보기 다이얼로그 열기"""
        result = item.data(0, Qt.UserRole)
        if result:
            self.show_analysis_detail(item)
    
    def on_chart_item_double_clicked(self, item):
        """차트 항목 더블클릭 이벤트"""
        chart_data = item.data(Qt.UserRole)
        
        if chart_data:
            # 차트 정보에서 실제 차트 설정 정보 추출
            chart_info = chart_data.get('info', {})
            self.chart_selected.emit(chart_info)
    
    def on_data_selection_changed(self):
        """데이터 선택 변경 이벤트"""
        current_item = self.data_tree.currentItem()
        if current_item:
            data_info = current_item.data(0, Qt.UserRole)
            if data_info and data_info.get("type") == "dataset":
                data = data_info["data"]
                summary = self.generate_data_summary(data)
                self.data_summary.setText(summary)
            elif data_info and data_info.get("type") == "column":
                col_name = data_info["column"]
                data = data_info["data"]
                summary = self.generate_column_summary(data, col_name)
                self.data_summary.setText(summary)
    
    def generate_data_summary(self, data):
        """데이터 요약 정보 생성"""
        summary = f"📊 데이터 요약\n"
        summary += f"• 크기: {data.shape[0]}행 × {data.shape[1]}열\n"
        summary += f"• 메모리 사용량: {data.memory_usage(deep=True).sum() / 1024:.1f} KB\n"
        
        # 결측값 정보
        missing_count = data.isnull().sum().sum()
        summary += f"• 결측값: {missing_count}개\n"
        
        # 데이터 타입 정보
        numeric_count = len(data.select_dtypes(include=['number']).columns)
        categorical_count = len(data.select_dtypes(include=['object', 'category']).columns)
        summary += f"• 숫자형: {numeric_count}개, 범주형: {categorical_count}개"
        
        return summary
    
    def generate_column_summary(self, data, col_name):
        """컬럼 요약 정보 생성"""
        col_data = data[col_name]
        summary = f"📋 {col_name} 컬럼 정보\n"
        
        if pd.api.types.is_numeric_dtype(col_data):
            summary += f"• 타입: 숫자형\n"
            summary += f"• 평균: {col_data.mean():.3f}\n"
            summary += f"• 표준편차: {col_data.std():.3f}\n"
            summary += f"• 최솟값: {col_data.min():.3f}\n"
            summary += f"• 최댓값: {col_data.max():.3f}\n"
        else:
            summary += f"• 타입: 범주형\n"
            summary += f"• 고유값: {col_data.nunique()}개\n"
            if col_data.nunique() <= 10:
                summary += f"• 값: {', '.join(map(str, col_data.unique()))}\n"
        
        summary += f"• 결측값: {col_data.isnull().sum()}개"
        
        return summary
    
    def show_data_context_menu(self, position):
        """데이터 컨텍스트 메뉴 표시"""
        item = self.data_tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # 데이터 보기
        view_action = QAction("📊 데이터 보기", self)
        view_action.triggered.connect(lambda: self.on_data_item_double_clicked(item, 0))
        menu.addAction(view_action)
        
        # 통계 요약
        stats_action = QAction("📈 통계 요약", self)
        stats_action.triggered.connect(lambda: self.show_detailed_stats(item))
        menu.addAction(stats_action)
        
        menu.exec(self.data_tree.mapToGlobal(position))
    
    def show_analysis_context_menu(self, position):
        """분석 결과 컨텍스트 메뉴"""
        item = self.analysis_tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # 상세 보기
        detail_action = menu.addAction("🔍 상세 보기")
        detail_action.triggered.connect(lambda: self.show_analysis_detail(item))
        
        # 결과 보기
        view_action = menu.addAction("📊 결과 보기")
        view_action.triggered.connect(lambda: self.on_analysis_item_double_clicked(item, 0))
        
        # 결과 내보내기
        export_action = menu.addAction("💾 결과 내보내기")
        export_action.triggered.connect(lambda: self.export_analysis_result(item))
        
        menu.addSeparator()
        
        # 삭제
        delete_action = menu.addAction("🗑️ 삭제")
        delete_action.triggered.connect(lambda: self.delete_analysis_result(item))
        
        menu.exec_(self.analysis_tree.mapToGlobal(position))
    
    def show_chart_context_menu(self, position):
        """차트 컨텍스트 메뉴 표시"""
        item = self.chart_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # 차트 보기
        view_action = QAction("📊 차트 보기", self)
        view_action.triggered.connect(lambda: self.on_chart_item_double_clicked(item))
        menu.addAction(view_action)
        
        # 삭제
        delete_action = QAction("🗑 삭제", self)
        delete_action.triggered.connect(lambda: self.delete_chart_item(item))
        menu.addAction(delete_action)
        
        menu.exec(self.chart_list.mapToGlobal(position))
    
    def show_detailed_stats(self, item):
        """상세 통계 표시"""
        data_info = item.data(0, Qt.UserRole)
        if data_info and data_info.get("type") == "dataset":
            data = data_info["data"]
            stats = data.describe()
            
            # 새 창에서 통계 표시 (간단히 메시지박스 사용)
            QMessageBox.information(self, "상세 통계", str(stats))
    
    def show_analysis_detail(self, item):
        """분석 결과 상세 보기 다이얼로그 표시"""
        result = item.data(0, Qt.UserRole)
        if not result:
            return
        
        try:
            from views.analysis_detail_dialog import AnalysisDetailDialog
            
            analysis_type = result.get("type", "알 수 없음")
            dialog = AnalysisDetailDialog(analysis_type, result, self)
            dialog.exec()
            
        except ImportError as e:
            QMessageBox.warning(self, "오류", f"상세 보기 모듈을 불러올 수 없습니다:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"상세 보기 중 오류가 발생했습니다:\n{str(e)}")
    
    def delete_analysis_result(self, item):
        """분석 결과 삭제"""
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"'{item.text(0)}' 분석 결과를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            index = self.analysis_tree.indexOfTopLevelItem(item)
            self.analysis_tree.takeTopLevelItem(index)
            self.update_analysis_summary()
    
    def delete_chart_item(self, item):
        """차트 항목 삭제"""
        row = self.chart_list.row(item)
        if 0 <= row < len(self.chart_history):
            del self.chart_history[row]
            self.chart_list.takeItem(row)
            self.update_stats()
    
    def refresh_all(self):
        """전체 새로고침"""
        if self.current_data is not None:
            self.add_data_to_tree(self.current_data, "현재 데이터")
        self.update_stats()
    
    def export_project(self):
        """프로젝트 내보내기"""
        try:
            # 메인 윈도우 참조 가져오기
            main_window = self.window()
            if hasattr(main_window, 'save_project_as'):
                main_window.save_project_as()
            else:
                QMessageBox.information(self, "내보내기", "프로젝트 내보내기 기능을 사용할 수 없습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"프로젝트 내보내기 중 오류가 발생했습니다:\n{str(e)}")
    
    def auto_save_project(self):
        """프로젝트 자동 저장"""
        # 자동 저장 로직 (실제로는 파일에 저장)
        pass
    
    def set_project_name(self, name):
        """프로젝트 이름 설정"""
        self.project_name = name
        self.project_name_label.setText(name)
    
    def clear_project(self):
        """프로젝트 초기화"""
        self.current_data = None
        self.analysis_history.clear()
        self.chart_history.clear()
        
        self.data_tree.clear()
        self.analysis_tree.clear()
        self.chart_list.clear()
        
        self.data_summary.clear()
        self.chart_info.clear()
        
        self.update_stats()
        
        # 분석 요약도 초기화
        self.update_analysis_summary()
    
    def add_chart_result(self, chart_type, chart_info, description=""):
        """차트 결과 추가 (중복 방지)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        chart_data = {
            "type": chart_type,
            "info": chart_info,
            "description": description,
            "timestamp": timestamp,
            "data_shape": self.current_data.shape if self.current_data is not None else None
        }
        
        # 중복 차트 확인 (최근 5초 내 동일한 차트 타입과 설정)
        current_time = datetime.now()
        is_duplicate = False
        
        for existing_chart in self.chart_history[-3:]:  # 최근 3개만 확인
            try:
                existing_time = datetime.strptime(existing_chart["timestamp"], "%H:%M:%S")
                # 시간 차이 계산 (같은 날짜 가정)
                time_diff = abs((current_time.hour * 3600 + current_time.minute * 60 + current_time.second) - 
                               (existing_time.hour * 3600 + existing_time.minute * 60 + existing_time.second))
                
                if (time_diff < 5 and  # 5초 이내
                    existing_chart["type"] == chart_type and
                    existing_chart["description"] == description):
                    is_duplicate = True
                    break
            except:
                continue
        
        if not is_duplicate:
            self.chart_history.append(chart_data)
            
            # 리스트에 항목 추가
            item = QListWidgetItem(f"[{timestamp}] {chart_type}")
            item.setData(Qt.UserRole, chart_data)
            self.chart_list.addItem(item)
            
            self.update_stats()
    
    def update_stats(self):
        """통계 정보 업데이트"""
        data_count = self.current_data.shape[0] if self.current_data is not None else 0
        analysis_count = self.analysis_tree.topLevelItemCount()
        chart_count = len(self.chart_history)
        
        self.stats_label.setText(f"데이터: {data_count}행 | 분석: {analysis_count}개 | 차트: {chart_count}개")
    
    def on_chart_selection_changed(self):
        """차트 선택 변경 이벤트"""
        current_item = self.chart_list.currentItem()
        if current_item:
            chart_info = current_item.data(Qt.UserRole)
            if chart_info:
                info_text = self.generate_chart_info(chart_info)
                self.chart_info.setText(info_text)
    
    def generate_chart_info(self, chart_info):
        """차트 정보 생성"""
        info = f"📈 {chart_info['type']} 차트\n"
        info += f"• 생성 시간: {chart_info['timestamp']}\n"
        
        if chart_info['data_shape']:
            info += f"• 데이터 크기: {chart_info['data_shape'][0]}행 × {chart_info['data_shape'][1]}열\n"
        
        if chart_info['description']:
            info += f"• 설명: {chart_info['description']}\n"
        
        # 차트 정보
        chart_data = chart_info['info']
        if isinstance(chart_data, dict):
            info += "• 차트 설정:\n"
            for key, value in chart_data.items():
                info += f"  - {key}: {value}\n"
        
        return info
    
    def update_analysis_buttons_state(self, data_or_enabled):
        """분석 버튼들 상태 업데이트 (데이터 기반 활성화)"""
        if isinstance(data_or_enabled, bool):
            enabled = data_or_enabled
            self.basic_stats_btn.setEnabled(enabled)
            self.correlation_btn.setEnabled(enabled)
            self.anova_btn.setEnabled(enabled)
            self.regression_btn.setEnabled(enabled)
            return

        data = data_or_enabled
        if data is None or data.empty:
            self.basic_stats_btn.setEnabled(False)
            self.correlation_btn.setEnabled(False)
            self.anova_btn.setEnabled(False)
            self.regression_btn.setEnabled(False)
            return

        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
        has_numeric = len(numeric_cols) > 0
        has_numeric2 = len(numeric_cols) >= 2
        has_cat = len(categorical_cols) > 0

        self.basic_stats_btn.setEnabled(has_numeric)
        self.correlation_btn.setEnabled(has_numeric2)
        # 빠른 ANOVA는 범주형 요인이 필요
        self.anova_btn.setEnabled(has_numeric and has_cat)
        self.regression_btn.setEnabled(has_numeric2)
    
    def run_basic_statistics(self):
        """기초 통계 분석 실행"""
        if self.current_data is None:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        try:
            # 기초 통계 계산
            numeric_data = self.current_data.select_dtypes(include=['number'])
            if numeric_data.empty:
                QMessageBox.information(self, "알림", "숫자형 데이터가 없습니다.")
                return
            
            desc_stats = numeric_data.describe()
            
            # 분석 결과 저장
            result = {
                "type": "기초 통계",
                "data": desc_stats,
                "summary": f"{len(numeric_data.columns)}개 변수의 기초 통계량",
                "timestamp": datetime.now()
            }
            
            self.add_analysis_result("기초 통계", result, "완료")
            
            # 시그널 발생
            self.analysis_selected.emit("기초 통계", result)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"기초 통계 분석 중 오류가 발생했습니다:\n{str(e)}")
    
    def run_correlation_analysis(self):
        """상관분석 실행"""
        if self.current_data is None:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        try:
            numeric_data = self.current_data.select_dtypes(include=['number'])
            if len(numeric_data.columns) < 2:
                QMessageBox.information(self, "알림", "상관분석을 위해서는 최소 2개의 숫자형 변수가 필요합니다.")
                return
            
            # 상관계수 계산
            correlation_matrix = numeric_data.corr()
            
            # 분석 결과 저장
            result = {
                "type": "상관분석",
                "data": correlation_matrix,
                "summary": f"{len(numeric_data.columns)}개 변수간 상관관계 분석",
                "timestamp": datetime.now()
            }
            
            self.add_analysis_result("상관분석", result, "완료")
            
            # 시그널 발생
            self.analysis_selected.emit("상관분석", result)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"상관분석 중 오류가 발생했습니다:\n{str(e)}")
    
    def run_anova(self):
        """ANOVA 분석 실행"""
        if self.current_data is None:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        try:
            numeric_cols = self.current_data.select_dtypes(include=['number']).columns
            categorical_cols = self.current_data.select_dtypes(include=['object', 'category']).columns
            
            if len(numeric_cols) == 0 or len(categorical_cols) == 0:
                QMessageBox.information(self, "알림", "ANOVA 분석을 위해서는 숫자형 변수와 범주형 변수가 모두 필요합니다.")
                return
            
            # 간단한 ANOVA 분석 (첫 번째 숫자형 변수와 첫 번째 범주형 변수 사용)
            dependent_var = numeric_cols[0]
            factor_var = categorical_cols[0]
            
            # 그룹별 기초 통계
            group_stats = self.current_data.groupby(factor_var)[dependent_var].describe()
            
            result = {
                "type": "ANOVA",
                "dependent_variable": dependent_var,
                "factor_variable": factor_var,
                "group_statistics": group_stats,
                "summary": f"{factor_var}에 따른 {dependent_var}의 차이 분석",
                "timestamp": datetime.now()
            }
            
            self.add_analysis_result("ANOVA", result, "완료")
            
            # 시그널 발생
            self.analysis_selected.emit("ANOVA", result)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"ANOVA 분석 중 오류가 발생했습니다:\n{str(e)}")
    
    def run_regression(self):
        """회귀분석 실행"""
        if self.current_data is None:
            QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
            return
        
        try:
            numeric_cols = self.current_data.select_dtypes(include=['number']).columns
            
            if len(numeric_cols) < 2:
                QMessageBox.information(self, "알림", "회귀분석을 위해서는 최소 2개의 숫자형 변수가 필요합니다.")
                return
            
            # 실제 회귀분석 수행
            try:
                from sklearn.linear_model import LinearRegression
                from sklearn.metrics import r2_score
                import numpy as np
                
                # 첫 번째 변수를 종속변수, 나머지를 독립변수로 사용
                y = self.current_data[numeric_cols[0]].dropna()
                X = self.current_data[numeric_cols[1:]].dropna()
                
                # 공통 인덱스만 사용 (결측값 제거)
                common_idx = y.index.intersection(X.index)
                y = y.loc[common_idx]
                X = X.loc[common_idx]
                
                if len(y) < 3:
                    QMessageBox.information(self, "알림", "회귀분석을 위한 충분한 데이터가 없습니다.")
                    return
                
                # 회귀분석 수행
                model = LinearRegression()
                model.fit(X, y)
                y_pred = model.predict(X)
                r2 = r2_score(y, y_pred)
                
                # 결과 정리
                coefficients = dict(zip(X.columns, model.coef_))
                
                result = {
                    "type": "회귀분석",
                    "dependent_variable": numeric_cols[0],
                    "independent_variables": list(X.columns),
                    "r_squared": r2,
                    "intercept": model.intercept_,
                    "coefficients": coefficients,
                    "n_observations": len(y),
                    "summary": f"{numeric_cols[0]}에 대한 다중회귀분석 (R² = {r2:.3f})",
                    "timestamp": datetime.now()
                }
                
                self.add_analysis_result("회귀분석", result, "완료")
                
            except ImportError:
                # sklearn이 없는 경우 기본 상관분석으로 대체
                correlation_matrix = self.current_data[numeric_cols].corr()
                
                result = {
                    "type": "회귀분석",
                    "variables": list(numeric_cols),
                    "correlation_matrix": correlation_matrix,
                    "summary": f"{len(numeric_cols)}개 변수간 상관관계 분석 (sklearn 미설치로 기본 분석)",
                    "note": "고급 회귀분석을 위해서는 'pip install scikit-learn' 명령으로 sklearn을 설치해주세요.",
                    "timestamp": datetime.now()
                }
                
                self.add_analysis_result("회귀분석", result, "완료")
            
            # 시그널 발생
            self.analysis_selected.emit("회귀분석", result)
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"회귀분석 중 오류가 발생했습니다:\n{str(e)}")
    
    def export_analysis_result(self, item):
        """분석 결과 내보내기"""
        result = item.data(0, Qt.UserRole)
        if not result:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "분석 결과 내보내기", 
            f"{result['type']}_결과.txt",
            "텍스트 파일 (*.txt);;모든 파일 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"분석 유형: {result['type']}\n")
                    f.write(f"분석 시간: {result['timestamp']}\n")
                    f.write(f"요약: {result['summary']}\n\n")
                    
                    if 'data' in result:
                        f.write("분석 결과:\n")
                        f.write(str(result['data']))
                
                QMessageBox.information(self, "완료", f"분석 결과를 저장했습니다:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 저장 중 오류가 발생했습니다:\n{str(e)}")
    
    def delete_analysis_result(self, item):
        """분석 결과 삭제"""
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"'{item.text(0)}' 분석 결과를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            index = self.analysis_tree.indexOfTopLevelItem(item)
            self.analysis_tree.takeTopLevelItem(index)
            self.update_analysis_summary() 
