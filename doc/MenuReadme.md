# DOE Desktop Application - 메뉴 시스템 개발 가이드

## 📋 개요

이 문서는 DOE Desktop Application의 메뉴 시스템 개발 과정을 상세히 기록한 가이드입니다. 커서(Cursor) 대화를 통해 메뉴 구조를 체계적으로 확장하고, 실제 기능을 구현하는 전체 과정을 설명합니다.

---

## 🚀 메뉴 시스템 개발 히스토리

### **Phase 1: 문제 분석 (2024.12.15)**

#### **🚨 초기 문제점 발견**
```
1. 기존 메뉴 구조의 한계:
   - 실험설계 메뉴에 요인설계만 있고 구현되지 않음
   - 분석 메뉴에 기초 통계, ANOVA만 있고 기능 부족
   - 메뉴와 툴바 버튼의 역할 중복
   - 프로젝트 저장/로드 시 분석 결과 처리 문제

2. 사용자 요구사항:
   - Minitab 수준의 체계적인 메뉴 구조
   - 실험설계 방법론별 명확한 구분
   - 고급 통계 분석 기능 확장
   - 메뉴 기능의 실제 구현
```

#### **🎯 해결 방향 설정**
```
1. 메뉴 구조 재설계: 기능별 논리적 그룹핑
2. 실험설계 방법론별 체계적 분류
3. 고급 통계 분석 메뉴 확장
4. 새로운 차트 및 도구 메뉴 추가
5. 실제 기능 구현 (시그널-슬롯 연결)
```

---

### **Phase 2: 메뉴 구조 설계 (2024.12.15)**

#### **🏗️ 새로운 메뉴 아키텍처 설계**

```
📁 파일 메뉴 (기존 유지)
├── 새 프로젝트, 프로젝트 열기/저장
├── 데이터 가져오기/내보내기
└── 최근 파일

🗂️ 데이터 메뉴 (대폭 확장)
├── 데이터 입출력
├── 데이터 편집
├── 데이터 변환
├── 데이터 품질
└── 데이터 뷰

🧪 실험설계 메뉴 (완전 신규)
├── 스크리닝 설계
├── 최적화 설계
├── 견고성 설계
├── 특수 설계
└── 사용자 정의 설계

📊 분석 메뉴 (대폭 확장)
├── 기초 통계 & 상관분석
├── 분산분석 (4종류)
├── 회귀분석 (4종류)
├── 비모수검정 (3종류)
├── 다변량분석 (3종류)
└── 종합분석실행

📈 차트 메뉴 (완전 신규)
├── 기본 차트
├── DOE 차트
├── 진단 차트
└── 모든 차트 지우기

🔧 도구 메뉴 (완전 신규)
├── 설정
├── 데이터 변환
└── 데이터 품질
```

#### **🎨 메뉴 설계 원칙**

1. **기능별 논리적 그룹핑**
   - 관련 기능들을 하나의 메뉴로 묶음
   - 서브메뉴를 통한 계층적 구조 구성

2. **사용자 워크플로우 고려**
   - 데이터 → 실험설계 → 분석 → 차트 순서
   - 자주 사용하는 기능의 접근성 향상

3. **확장성 고려**
   - 새로운 기능 추가가 용이한 구조
   - 플러그인 방식 확장 가능

4. **국제화 지원**
   - 한글 메뉴명과 영문 단축키 조합
   - 상태 팁을 통한 기능 설명

---

### **Phase 3: 실험설계 메뉴 구현 (2024.12.15)**

#### **🧪 DOE 방법론별 분류 및 구현**

```python
# 1. 스크리닝 설계 (많은 인수 중 중요한 것 선별)
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
```

#### **🎯 실험설계 방법론 분류 기준**

| **단계** | **목적** | **방법론** | **특징** |
|----------|----------|------------|----------|
| **스크리닝** | 중요 인수 선별 | 완전요인, 부분요인, Plackett-Burman | 많은 인수 처리 |
| **최적화** | 최적점 탐색 | RSM, Box-Behnken, CCD | 곡선 관계 모델링 |
| **견고성** | 안정 조건 탐색 | 직교배열, 다구치 | 품질공학 기반 |
| **특수** | 특별한 제약 | 혼합설계, 분할구설계 | 특수 조건 대응 |

---

### **Phase 4: 분석 메뉴 확장 (2024.12.15)**

#### **📊 통계 분석 메뉴 체계화**

```python
# 분산분석 서브메뉴 구현
anova_menu = analysis_menu.addMenu("분산분석")

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
```

#### **🔬 분석 기능 분류**

| **분석 그룹** | **기능** | **용도** |
|---------------|----------|----------|
| **기초 분석** | 기초 통계, 상관분석 | 데이터 탐색 |
| **분산분석** | 일원/이원/다원/반복측정 | 그룹 간 차이 검정 |
| **회귀분석** | 단순/다중/단계적/비선형 | 관계 모델링 |
| **비모수검정** | Mann-Whitney, Kruskal-Wallis, Wilcoxon | 분포 가정 불만족 시 |
| **다변량분석** | PCA, 군집분석, 판별분석 | 차원 축소 및 패턴 발견 |

---

### **Phase 5: 차트 메뉴 추가 (2024.12.15)**

#### **📈 시각화 메뉴 구현**

```python
# 차트 메뉴 생성
chart_menu = menubar.addMenu("차트(&C)")

# 기본 차트 서브메뉴
basic_chart_menu = chart_menu.addMenu("기본 차트")

# DOE 차트 서브메뉴  
doe_chart_menu = chart_menu.addMenu("DOE 차트")

# 진단 차트 서브메뉴
diagnostic_chart_menu = chart_menu.addMenu("진단 차트")
```

#### **📊 차트 분류 체계**

| **차트 그룹** | **차트 종류** | **용도** |
|---------------|---------------|----------|
| **기본 차트** | 산점도, 히스토그램, 박스플롯 | 기본 데이터 시각화 |
| **DOE 차트** | 주효과도, 상호작용도, 등고선도 | 실험설계 결과 시각화 |
| **진단 차트** | Q-Q Plot, 잔차도, 상관행렬 | 모델 진단 및 검증 |

---

### **Phase 6: 데이터 메뉴 확장 (2024.12.15)**

#### **🗂️ 데이터 관리 메뉴 체계화**

```python
# 데이터 메뉴 확장
data_menu = menubar.addMenu("데이터(&D)")

# 데이터 입출력 서브메뉴
io_menu = data_menu.addMenu("데이터 입출력")

# 데이터 편집 서브메뉴
edit_menu = data_menu.addMenu("데이터 편집")

# 데이터 변환 서브메뉴
transform_menu = data_menu.addMenu("데이터 변환")

# 데이터 품질 서브메뉴
quality_menu = data_menu.addMenu("데이터 품질")

# 데이터 뷰 서브메뉴
view_menu = data_menu.addMenu("데이터 뷰")
```

#### **🔧 데이터 처리 워크플로우**

```
1. 데이터 입출력: 가져오기/내보내기, 클립보드 연동
2. 데이터 편집: 행/열 편집, 정렬, 찾기/바꾸기
3. 데이터 변환: 변수 관리, 파생변수 생성, 수학적 변환
4. 데이터 품질: 결측값/이상값/중복값 처리
5. 데이터 뷰: 요약, 미리보기, 필터링
```

---

### **Phase 7: 실제 기능 구현 (2024.12.15)**

#### **🚨 핵심 문제 발견: 시그널-슬롯 연결 누락**

```python
# 문제: 메뉴 클릭 시 아무 반응 없음
def run_one_way_anova(self):
    """일원분산분석"""
    if not self.data_view.has_data():
        QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
        return
    
    self.status_label.setText("일원분산분석을 수행 중입니다...")
    self.analysis_requested.emit("one_way_anova")  # 시그널 발생
    
# ❌ 문제: analysis_requested 시그널을 받는 곳이 없음!
```

#### **✅ 해결: 시그널-슬롯 연결 추가**

```python
def connect_signals(self):
    """시그널 연결"""
    # 기존 시그널 연결들...
    
    # 🔥 핵심 수정: analysis_requested 시그널 연결
    self.analysis_requested.connect(self.handle_analysis_request)

def handle_analysis_request(self, request):
    """분석 요청 처리"""
    if request == "one_way_anova":
        self.run_one_way_anova()
    elif request == "two_way_anova":
        self.run_two_way_anova()
    # ... 기타 분석 요청 처리
```

#### **🔬 실제 분석 기능 구현**

```python
def run_one_way_anova(self):
    """일원분산분석 실제 구현"""
    try:
        from scipy.stats import f_oneway
        
        # 1. 데이터 가져오기
        data = self.data_view.get_data()
        
        # 2. 변수 타입 분리
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # 3. 데이터 유효성 검사
        if len(numeric_cols) == 0:
            QMessageBox.warning(self, "경고", "수치형 변수가 없습니다.")
            return
        
        if len(categorical_cols) == 0:
            QMessageBox.warning(self, "경고", "범주형 변수가 없습니다.")
            return
        
        # 4. 변수 선택 (자동)
        group_var = categorical_cols[0]
        dependent_var = numeric_cols[0]
        
        # 5. 그룹별 데이터 분리
        groups = []
        for group_name in data[group_var].unique():
            if pd.notna(group_name):
                group_data = data[data[group_var] == group_name][dependent_var].dropna()
                if len(group_data) > 0:
                    groups.append(group_data)
        
        # 6. 일원분산분석 수행
        f_stat, p_value = f_oneway(*groups)
        
        # 7. 결과 구성 및 저장
        result = {
            'type': '일원분산분석',
            'group_variable': group_var,
            'dependent_variable': dependent_var,
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            # ... 기타 통계량
        }
        
        # 8. 결과 표시
        self.project_explorer.add_analysis_result('일원분산분석', result, '완료')
        self.results_view.add_analysis_result('일원분산분석', result)
        
    except Exception as e:
        QMessageBox.critical(self, "오류", f"분석 중 오류: {str(e)}")
```

---

## 🏗️ 메뉴 기능 추가 표준 절차

### **1단계: 메뉴 아이템 생성**

```python
# 1. QAction 생성
self.new_analysis_action = QAction("새로운 분석(&N)", self)
self.new_analysis_action.setStatusTip("새로운 분석을 수행합니다")
self.new_analysis_action.setShortcut("Ctrl+N")

# 2. 메뉴에 추가
analysis_menu.addAction(self.new_analysis_action)

# 3. 시그널 연결
self.new_analysis_action.triggered.connect(self.run_new_analysis)
```

### **2단계: 요청 처리 메서드 구현**

```python
def run_new_analysis(self):
    """새로운 분석 요청 처리"""
    if not self.data_view.has_data():
        QMessageBox.information(self, "알림", "분석할 데이터가 없습니다.")
        return
    
    self.status_label.setText("새로운 분석을 수행 중입니다...")
    # 직접 분석 실행 또는 시그널 발생
    self.perform_new_analysis()
```

### **3단계: 실제 분석 기능 구현**

```python
def perform_new_analysis(self):
    """새로운 분석 실제 구현"""
    try:
        # 1. 데이터 가져오기
        data = self.data_view.get_data()
        
        # 2. 데이터 전처리
        # ... 전처리 로직
        
        # 3. 분석 수행
        # ... 분석 로직
        
        # 4. 결과 구성
        result = {
            'type': '새로운 분석',
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            # ... 분석 결과
        }
        
        # 5. 결과 저장 및 표시
        self.project_explorer.add_analysis_result('새로운 분석', result, '완료')
        self.results_view.add_analysis_result('새로운 분석', result)
        
        # 6. 결과 탭으로 이동
        self.tab_widget.setCurrentWidget(self.results_view)
        
        # 7. 상태 업데이트
        self.status_label.setText("새로운 분석 완료")
        
    except Exception as e:
        QMessageBox.critical(self, "오류", f"분석 중 오류가 발생했습니다:\n{str(e)}")
        self.status_label.setText("새로운 분석 실패")
```

### **4단계: UI 상태 관리**

```python
def update_ui_state(self):
    """UI 상태 업데이트"""
    has_data = self.data_view.has_data()
    
    # 새로운 분석 메뉴 활성화/비활성화
    self.new_analysis_action.setEnabled(has_data)
```

---

## 📊 현재 구현 상태 매트릭스

### **✅ 완전 구현된 기능 (바로 사용 가능)**

| **메뉴** | **기능** | **구현 상태** | **테스트 완료** |
|----------|----------|---------------|-----------------|
| 파일 | 프로젝트 관리 | ✅ 완료 | ✅ 완료 |
| 파일 | 데이터 가져오기/내보내기 | ✅ 완료 | ✅ 완료 |
| 분석 | 기초 통계 | ✅ 완료 | ✅ 완료 |
| 분석 | 상관분석 | ✅ 완료 | ✅ 완료 |
| 분석 | 일원분산분석 | ✅ 완료 | ✅ 완료 |
| 분석 | 이원분산분석 | ✅ 완료 | ✅ 완료 |
| 차트 | 기본 차트 | ✅ 완료 | ✅ 완료 |
| 데이터 | 클립보드 연동 | ✅ 완료 | ✅ 완료 |
| 데이터 | 중복값 제거 | ✅ 완료 | ✅ 완료 |

### **🔧 부분 구현된 기능 (메뉴 완성, 구현 대기)**

| **메뉴** | **기능** | **메뉴 상태** | **구현 상태** | **우선순위** |
|----------|----------|---------------|---------------|--------------|
| 분석 | 다원분산분석 | ✅ 완료 | 🔧 스텁 | 높음 |
| 분석 | 회귀분석 | ✅ 완료 | 🔧 스텁 | 높음 |
| 분석 | 비모수검정 | ✅ 완료 | 🔧 스텁 | 중간 |
| 분석 | 다변량분석 | ✅ 완료 | 🔧 스텁 | 중간 |
| 실험설계 | 완전요인설계 | ✅ 완료 | 🔧 스텁 | 높음 |
| 실험설계 | 반응표면설계 | ✅ 완료 | 🔧 스텁 | 높음 |
| 차트 | DOE 차트 | ✅ 완료 | 🔧 스텁 | 중간 |
| 차트 | 진단 차트 | ✅ 완료 | 🔧 스텁 | 중간 |
| 데이터 | 고급 편집 | ✅ 완료 | 🔧 스텁 | 낮음 |
| 데이터 | 데이터 변환 | ✅ 완료 | 🔧 스텁 | 중간 |

---

## 🎯 향후 메뉴 확장 로드맵

### **우선순위 1: 핵심 DOE 기능 (2024.12.16-31)**

```
1. 완전요인설계 마법사
   - 인수 및 수준 설정 다이얼로그
   - 설계 매트릭스 생성
   - 랜덤화 옵션

2. 기본 DOE 차트
   - 주효과도 (Main Effects Plot)
   - 상호작용도 (Interaction Plot)
   - 정규확률도 (Normal Plot)

3. DOE 분석 통합
   - 분산분석과 DOE 결과 연동
   - 효과 크기 계산
   - 최적 조건 예측
```

### **우선순위 2: 고급 통계 분석 (2025.01.01-15)**

```
1. 회귀분석 완성
   - 단순/다중 회귀분석
   - 모델 선택 및 진단
   - 잔차 분석

2. 다원분산분석
   - 3-way ANOVA 이상
   - 중첩 설계 분석
   - 혼합 효과 모델

3. 비모수 검정
   - Mann-Whitney U 검정
   - Kruskal-Wallis 검정
   - Wilcoxon 부호순위 검정
```

### **우선순위 3: 고급 DOE 방법론 (2025.01.16-31)**

```
1. 반응표면설계 (RSM)
   - Box-Behnken 설계
   - 중심합성설계 (CCD)
   - 등고선도 및 3D 표면도

2. 견고성 설계
   - 다구치 방법론
   - 직교배열 설계
   - S/N 비 분석

3. 특수 설계
   - 혼합설계 (Mixture Design)
   - 분할구설계 (Split-Plot Design)
   - 최적 설계 (Optimal Design)
```

### **우선순위 4: 사용성 및 고급 기능 (2025.02.01-28)**

```
1. 보고서 생성
   - 분석 결과 자동 문서화
   - 템플릿 시스템
   - PDF/Word 내보내기

2. 데이터 관리 고도화
   - 데이터베이스 연동
   - 대용량 데이터 처리
   - 실시간 데이터 연동

3. 고급 시각화
   - 인터랙티브 차트
   - 애니메이션 효과
   - 사용자 정의 차트
```

---

## 🔧 메뉴 개발 베스트 프랙티스

### **1. 메뉴 설계 원칙**

```
1. 사용자 중심 설계
   - 사용자 워크플로우 고려
   - 직관적인 메뉴 구조
   - 일관된 네이밍 규칙

2. 기능적 그룹핑
   - 관련 기능의 논리적 묶음
   - 계층적 구조 활용
   - 중복 기능 최소화

3. 접근성 고려
   - 키보드 단축키 제공
   - 상태 팁 및 도움말
   - 장애인 접근성 고려
```

### **2. 코드 구조 패턴**

```python
# 메뉴 생성 패턴
def setup_menus(self):
    """메뉴바 설정"""
    menubar = self.menuBar()
    
    # 1. 메뉴 생성
    menu = menubar.addMenu("메뉴명(&단축키)")
    
    # 2. 서브메뉴 생성 (필요시)
    submenu = menu.addMenu("서브메뉴명")
    
    # 3. 액션 생성 및 추가
    action = QAction("액션명(&단축키)", self)
    action.setStatusTip("상태 팁")
    action.setShortcut("Ctrl+Key")
    action.triggered.connect(self.handler_method)
    menu.addAction(action)
    
    # 4. 구분선 추가 (필요시)
    menu.addSeparator()

# 핸들러 메서드 패턴
def handler_method(self):
    """기능 실행 핸들러"""
    # 1. 전제 조건 확인
    if not self.validate_prerequisites():
        return
    
    # 2. 상태 업데이트
    self.update_status("작업 시작...")
    
    # 3. 실제 기능 실행
    try:
        result = self.perform_actual_work()
        self.handle_success(result)
    except Exception as e:
        self.handle_error(e)
    finally:
        self.cleanup()

# UI 상태 관리 패턴
def update_ui_state(self):
    """UI 상태 업데이트"""
    has_data = self.data_view.has_data()
    
    # 메뉴별 활성화 상태 설정
    self.action_name.setEnabled(has_data)
```

### **3. 오류 처리 패턴**

```python
def safe_analysis_execution(self, analysis_func, analysis_name):
    """안전한 분석 실행 패턴"""
    try:
        # 전제 조건 확인
        if not self.validate_data():
            return False
        
        # 상태 업데이트
        self.update_status(f"{analysis_name} 수행 중...")
        
        # 분석 실행
        result = analysis_func()
        
        # 결과 처리
        self.process_analysis_result(result, analysis_name)
        
        # 성공 메시지
        self.update_status(f"{analysis_name} 완료")
        return True
        
    except ImportError as e:
        self.show_dependency_error(str(e))
        return False
    except ValueError as e:
        self.show_data_error(str(e))
        return False
    except Exception as e:
        self.show_general_error(analysis_name, str(e))
        return False
```

---

## 📚 참고 자료 및 문서

### **기술 문서**
- `main_window.py`: 메인 윈도우 및 메뉴 구현
- `project_explorer.py`: 프로젝트 탐색기 구현
- `results_view.py`: 분석 결과 표시
- `README.md`: 전체 애플리케이션 가이드

### **외부 라이브러리 의존성**
```
scipy>=1.10.0          # 통계 분석
statsmodels>=0.14.0    # 고급 통계 모델
pandas>=2.0.0          # 데이터 처리
numpy>=1.24.0          # 수치 계산
matplotlib>=3.7.0      # 기본 시각화
seaborn>=0.12.0        # 통계 시각화
plotly>=5.15.0         # 인터랙티브 차트
```

### **DOE 관련 라이브러리**
```
pyDOE2>=1.3.0          # 실험설계 생성
factor-analyzer>=0.4.1  # 요인분석
pingouin>=0.5.3        # 고급 통계 함수
```

---

## 🎉 결론

이 가이드는 DOE Desktop Application의 메뉴 시스템을 체계적으로 확장하는 전체 과정을 문서화했습니다. 주요 성과는 다음과 같습니다:

### **✅ 달성된 목표**
1. **메뉴 구조 체계화**: 5개 주요 메뉴로 기능 분류
2. **실제 기능 구현**: 분산분석 등 핵심 기능 작동
3. **확장 가능한 아키텍처**: 새로운 기능 추가 용이
4. **사용자 경험 개선**: 직관적인 메뉴 구조

### **🚀 향후 개발 방향**
1. **DOE 핵심 기능 우선 구현**
2. **고급 통계 분석 확장**
3. **사용성 및 보고서 기능 추가**
4. **성능 최적화 및 안정성 향상**

이 문서를 참고하여 체계적으로 메뉴 기능을 확장해 나갈 수 있습니다.

---

**작성일**: 2024.12.15  
**최종 수정**: 2024.12.15  
**작성자**: DOE Desktop Application 개발팀  
**버전**: 1.0.0 