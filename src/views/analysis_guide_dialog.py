"""
분석 가이드 다이얼로그

사용자에게 분석 방법의 용도와 적절한 데이터 형식을 안내하는 다이얼로그
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QTabWidget, QWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QIcon

class AnalysisGuideDialog(QDialog):
    """분석 가이드 다이얼로그"""
    
    def __init__(self, analysis_type, current_data_info, parent=None):
        super().__init__(parent)
        self.analysis_type = analysis_type
        self.current_data_info = current_data_info
        
        self.setWindowTitle(f"{analysis_type} - 분석 가이드")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        # 분석별 정보
        self.analysis_info = {
            '일원분산분석': {
                'purpose': '하나의 범주형 변수(그룹)가 수치형 변수(결과)에 미치는 영향을 분석합니다.',
                'requirements': '범주형 변수 1개 + 수치형 변수 1개',
                'sample': 'Group(A,B,C) + Score(85.2, 87.1, 84.5)',
                'solution': '✅ 현재 구현됨!\n\n📋 사용법:\n1. 샘플 데이터 버튼 클릭\n2. 분석 → 분산분석 → 일원분산분석 선택\n3. 결과 탭에서 F-검정 결과 확인\n\n💡 필요한 데이터: 그룹을 나타내는 텍스트 열 + 측정값을 나타내는 숫자 열'
            },
            '이원분산분석': {
                'purpose': '두 개의 범주형 변수가 수치형 변수에 미치는 영향과 상호작용을 분석합니다.',
                'requirements': '범주형 변수 2개 + 수치형 변수 1개',
                'sample': 'Temperature(High,Low) + Pressure(High,Low) + Yield(95.2)',
                'solution': '✅ 현재 구현됨!\n\n📋 사용법:\n1. 샘플 데이터 버튼 클릭\n2. 분석 → 분산분석 → 이원분산분석 선택\n3. 결과 탭에서 주효과와 상호작용 확인\n\n💡 필요한 데이터: 2개의 그룹 변수(텍스트) + 1개의 측정값(숫자)'
            },
            '상관분석': {
                'purpose': '두 개 이상의 수치형 변수 간의 선형 관계 강도를 분석합니다.',
                'requirements': '수치형 변수 2개 이상',
                'sample': 'Height(170.2) + Weight(65.5) + Age(25)',
                'solution': '✅ 현재 구현됨!\n\n📋 사용법:\n1. 샘플 데이터 버튼 클릭\n2. 분석 → 회귀분석 → 상관분석 선택\n3. 결과 탭에서 상관계수 매트릭스 확인\n\n💡 필요한 데이터: 2개 이상의 숫자 열 (키, 몸무게, 나이 등)'
            },
            '기초 통계': {
                'purpose': '데이터의 기본적인 통계량(평균, 표준편차, 분포 등)을 계산합니다.',
                'requirements': '수치형 변수 1개 이상',
                'sample': 'Score(85.2) + Time(12.5) + Temperature(23.1)',
                'solution': '✅ 현재 구현됨!\n\n📋 사용법:\n1. 샘플 데이터 버튼 클릭\n2. 분석 → 기초 통계 선택\n3. 결과 탭에서 평균, 표준편차 등 확인\n\n💡 필요한 데이터: 1개 이상의 숫자 열'
            },
            '다원분산분석': {
                'purpose': '세 개 이상의 범주형 변수가 수치형 변수에 미치는 영향을 분석합니다.',
                'requirements': '범주형 변수 3개 이상 + 수치형 변수 1개',
                'sample': 'Factor1(A,B) + Factor2(High,Low) + Factor3(X,Y) + Result(95.2)',
                'solution': '🚧 향후 업데이트 예정\n\n📋 현재 대안:\n1. 일원분산분석으로 각 요인별 개별 분석\n2. 이원분산분석으로 주요 2개 요인 분석\n3. 상관분석으로 변수 간 관계 탐색'
            },
            '단순회귀분석': {
                'purpose': '하나의 독립변수가 종속변수에 미치는 선형 관계를 분석합니다.',
                'requirements': '수치형 변수 2개 (독립변수 1개 + 종속변수 1개)',
                'sample': 'X(10, 20, 30) + Y(15, 25, 35)',
                'solution': '🚧 향후 업데이트 예정\n\n📋 현재 대안:\n1. 상관분석으로 두 변수 간 관계 확인\n2. 산점도 차트로 시각적 관계 파악\n3. 기초 통계로 각 변수의 분포 확인'
            },
            '다중회귀분석': {
                'purpose': '여러 독립변수가 종속변수에 미치는 선형 관계를 분석합니다.',
                'requirements': '수치형 변수 3개 이상 (독립변수 2개 이상 + 종속변수 1개)',
                'sample': 'X1(10, 20) + X2(5, 15) + Y(25, 35)',
                'solution': '🚧 향후 업데이트 예정\n\n📋 현재 대안:\n1. 상관분석으로 모든 변수 간 관계 확인\n2. 각 독립변수와 종속변수 간 개별 상관분석\n3. 기초 통계로 변수별 분포 파악'
            },
            '주성분분석': {
                'purpose': '다차원 데이터의 차원을 축소하여 주요 성분을 찾습니다.',
                'requirements': '수치형 변수 3개 이상',
                'sample': 'Var1(1.2) + Var2(2.3) + Var3(3.4) + Var4(4.5)',
                'solution': '🚧 향후 업데이트 예정\n\n📋 현재 대안:\n1. 상관분석으로 변수 간 관계 확인\n2. 기초 통계로 각 변수의 중요도 파악\n3. 산점도로 변수 간 패턴 시각화'
            },
            '군집분석': {
                'purpose': '유사한 특성을 가진 데이터를 그룹으로 분류합니다.',
                'requirements': '수치형 변수 2개 이상',
                'sample': 'Feature1(1.2) + Feature2(2.3) + Feature3(3.4)',
                'solution': '🚧 향후 업데이트 예정\n\n📋 현재 대안:\n1. 기초 통계로 데이터 분포 확인\n2. 상관분석으로 변수 간 유사성 파악\n3. 산점도로 자연스러운 그룹 패턴 관찰'
            }
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 헤더
        self.create_header(layout)
        
        # 탭 위젯
        self.create_tabs(layout)
        
        # 버튼
        self.create_buttons(layout)
        
        self.setLayout(layout)
    
    def create_header(self, layout):
        """헤더 생성"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 1px solid #cce7ff;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        header_layout = QVBoxLayout()
        
        # 제목
        title_label = QLabel(f"📊 {self.analysis_type} 분석 가이드")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 현재 상황
        if self.current_data_info:
            status_text = f"현재 데이터: {self.current_data_info.get('rows', 0)}행, {self.current_data_info.get('cols', 0)}열"
            if 'numeric_cols' in self.current_data_info:
                status_text += f"\n수치형 변수: {len(self.current_data_info['numeric_cols'])}개"
            if 'categorical_cols' in self.current_data_info:
                status_text += f", 범주형 변수: {len(self.current_data_info['categorical_cols'])}개"
        else:
            status_text = "현재 데이터가 없습니다."
            
        status_label = QLabel(status_text)
        status_label.setStyleSheet("color: #666; font-size: 11px;")
        status_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(status_label)
        header_frame.setLayout(header_layout)
        
        layout.addWidget(header_frame)
    
    def create_tabs(self, layout):
        """탭 위젯 생성"""
        tab_widget = QTabWidget()
        
        info = self.analysis_info.get(self.analysis_type, self.get_default_info())
        
        # 분석 개요 탭
        self.create_overview_tab(tab_widget, info)
        
        # 데이터 요구사항 탭
        self.create_requirements_tab(tab_widget, info)
        
        # 샘플 데이터 탭
        self.create_sample_tab(tab_widget, info)
        
        # 해결 방법 탭
        self.create_solutions_tab(tab_widget, info)
        
        layout.addWidget(tab_widget)
    
    def create_overview_tab(self, tab_widget, info):
        """분석 개요 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 목적
        purpose_label = QLabel("🎯 분석 목적")
        purpose_label.setFont(self.get_section_font())
        purpose_text = QLabel(info['purpose'])
        purpose_text.setWordWrap(True)
        purpose_text.setStyleSheet("padding: 10px; background-color: #f9f9f9; border-radius: 5px;")
        
        # 사용 시기
        when_label = QLabel("⏰ 언제 사용하나요?")
        when_label.setFont(self.get_section_font())
        when_text = QLabel('\n'.join(info['when_to_use']))
        when_text.setWordWrap(True)
        when_text.setStyleSheet("padding: 10px; background-color: #f9f9f9; border-radius: 5px;")
        
        layout.addWidget(purpose_label)
        layout.addWidget(purpose_text)
        layout.addSpacing(15)
        layout.addWidget(when_label)
        layout.addWidget(when_text)
        layout.addStretch()
        
        widget.setLayout(layout)
        tab_widget.addTab(widget, "분석 개요")
    
    def create_requirements_tab(self, tab_widget, info):
        """데이터 요구사항 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        requirements = info['data_requirements']
        
        # 필수 변수
        vars_label = QLabel("📋 필요한 변수")
        vars_label.setFont(self.get_section_font())
        vars_text = QLabel('\n'.join(requirements['필수 변수']))
        vars_text.setWordWrap(True)
        vars_text.setStyleSheet("padding: 10px; background-color: #e8f5e8; border-radius: 5px;")
        
        # 데이터 조건
        conditions_label = QLabel("✅ 데이터 조건")
        conditions_label.setFont(self.get_section_font())
        conditions_text = QLabel('\n'.join(requirements['데이터 조건']))
        conditions_text.setWordWrap(True)
        conditions_text.setStyleSheet("padding: 10px; background-color: #fff3e0; border-radius: 5px;")
        
        layout.addWidget(vars_label)
        layout.addWidget(vars_text)
        layout.addSpacing(15)
        layout.addWidget(conditions_label)
        layout.addWidget(conditions_text)
        layout.addStretch()
        
        widget.setLayout(layout)
        tab_widget.addTab(widget, "데이터 요구사항")
    
    def create_sample_tab(self, tab_widget, info):
        """샘플 데이터 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        sample_label = QLabel("📊 데이터 형식 예시")
        sample_label.setFont(self.get_section_font())
        
        sample_text = QTextEdit()
        sample_text.setPlainText(info['sample_data'])
        sample_text.setMaximumHeight(200)
        sample_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 10px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        sample_text.setReadOnly(True)
        
        # 추가 설명
        note_label = QLabel("💡 참고사항")
        note_label.setFont(self.get_section_font())
        note_text = QLabel("• 열 이름은 한글 또는 영문 모두 가능합니다.\n• 각 행은 하나의 관측값(실험 결과)을 나타냅니다.\n• 결측값은 공백으로 두거나 'NaN'으로 표시하세요.")
        note_text.setWordWrap(True)
        note_text.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        
        layout.addWidget(sample_label)
        layout.addWidget(sample_text)
        layout.addSpacing(15)
        layout.addWidget(note_label)
        layout.addWidget(note_text)
        layout.addStretch()
        
        widget.setLayout(layout)
        tab_widget.addTab(widget, "샘플 데이터")
    
    def create_solutions_tab(self, tab_widget, info):
        """해결 방법 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        solution_label = QLabel("🔧 해결 방법")
        solution_label.setFont(self.get_section_font())
        
        solutions_text = QLabel('\n\n'.join([f"{i+1}. {sol}" for i, sol in enumerate(info['solutions'])]))
        solutions_text.setWordWrap(True)
        solutions_text.setStyleSheet("padding: 15px; background-color: #fff8e1; border-radius: 5px; line-height: 1.6;")
        
        # 샘플 데이터 버튼들
        buttons_label = QLabel("📁 샘플 데이터 사용하기")
        buttons_label.setFont(self.get_section_font())
        
        buttons_layout = QHBoxLayout()
        
        # 기존 샘플 데이터 버튼
        sample_btn = QPushButton("📊 샘플 데이터 열기")
        sample_btn.clicked.connect(self.open_sample_data)
        sample_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # 데이터 가이드 버튼
        guide_btn = QPushButton("📖 데이터 준비 가이드")
        guide_btn.clicked.connect(self.show_data_guide)
        guide_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        buttons_layout.addWidget(sample_btn)
        buttons_layout.addWidget(guide_btn)
        buttons_layout.addStretch()
        
        layout.addWidget(solution_label)
        layout.addWidget(solutions_text)
        layout.addSpacing(20)
        layout.addWidget(buttons_label)
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        widget.setLayout(layout)
        tab_widget.addTab(widget, "해결 방법")
    
    def create_buttons(self, layout):
        """버튼 생성"""
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                font-size: 12px;
                background-color: #666;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def get_section_font(self):
        """섹션 폰트 반환"""
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        return font
    
    def get_default_info(self):
        """기본 정보 반환"""
        return {
            'purpose': '이 분석에 대한 정보를 준비 중입니다.',
            'when_to_use': ['• 관련 문서를 참조하세요.'],
            'data_requirements': {
                '필수 변수': ['• 분석에 필요한 변수 타입을 확인하세요.'],
                '데이터 조건': ['• 충분한 데이터를 준비하세요.']
            },
            'sample_data': '샘플 데이터를 준비 중입니다.',
            'solutions': ['관련 문서나 도움말을 참조하세요.']
        }
    
    def open_sample_data(self):
        """샘플 데이터 열기"""
        # 부모 윈도우에 샘플 데이터 열기 신호 전송
        if self.parent():
            # 분석 타입에 따라 적절한 샘플 파일 선택
            sample_files = {
                '일원분산분석': 'factorial_2x3_design_categorical.xlsx',
                '이원분산분석': 'factorial_2x3_design_categorical.xlsx',
                '상관분석': 'basic_statistics_sample.xlsx',
                '기초 통계': 'basic_statistics_sample.xlsx'
            }
            
            filename = sample_files.get(self.analysis_type, 'basic_statistics_sample.xlsx')
            
            try:
                # 부모의 데이터 가져오기 메서드 호출
                if hasattr(self.parent(), 'import_sample_data'):
                    self.parent().import_sample_data(filename)
                self.accept()  # 다이얼로그 닫기
            except Exception as e:
                print(f"샘플 데이터 열기 오류: {e}")
    
    def show_data_guide(self):
        """데이터 준비 가이드 표시"""
        from PySide6.QtWidgets import QMessageBox
        
        guide_text = """
📖 데이터 준비 가이드

1. 💾 파일 형식
   • Excel 파일 (.xlsx, .xls)
   • CSV 파일 (.csv)
   • 첫 번째 행은 열 이름으로 사용됩니다.

2. 📊 데이터 구조
   • 각 행 = 하나의 관측값 (실험 결과)
   • 각 열 = 하나의 변수 (측정 항목)
   • 변수명은 한글/영문 모두 가능

3. 🔤 데이터 타입
   • 수치형: 숫자 데이터 (예: 23.5, 100, -15.2)
   • 범주형: 텍스트 데이터 (예: "A그룹", "처리군", "고온")

4. ✅ 주의사항
   • 결측값 최소화
   • 이상값 확인
   • 일관된 데이터 형식 유지
        """
        
        QMessageBox.information(self, "데이터 준비 가이드", guide_text) 