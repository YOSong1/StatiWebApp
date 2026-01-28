# 단위 테스트 문서

DOE Desktop Application의 단위 테스트 모음입니다.

## 테스트 구조

```
test/
├── __init__.py                     # 테스트 패키지 초기화
├── README.md                       # 테스트 문서 (현재 파일)
├── run_tests.py                    # 테스트 실행 스크립트
├── test_project_controller.py      # ProjectController 테스트
├── test_data_controller.py         # DataController 테스트
├── test_analysis_controller.py     # AnalysisController 테스트
├── test_chart_controller.py        # ChartController 테스트
└── test_utils.py                   # 유틸리티 함수 테스트
```

## 테스트 실행 방법

### 1. 전체 테스트 실행

```bash
# 기본 실행
python test/run_tests.py

# 상세 출력 모드
python test/run_tests.py -v

# 코드 커버리지 포함 (coverage 패키지 필요)
python test/run_tests.py --coverage
```

### 2. 특정 모듈 테스트

```bash
# 컨트롤러 테스트만 실행
python test/run_tests.py controller

# 유틸리티 테스트만 실행
python test/run_tests.py utils

# 프로젝트 컨트롤러만 테스트
python test/run_tests.py project
```

### 3. 개별 테스트 파일 실행

```bash
# 특정 테스트 파일만 실행
python -m unittest test.test_project_controller

# 특정 테스트 클래스만 실행
python -m unittest test.test_project_controller.TestProjectController

# 특정 테스트 메서드만 실행
python -m unittest test.test_project_controller.TestProjectController.test_new_project
```

## 테스트 모듈 상세

### 1. ProjectController 테스트 (`test_project_controller.py`)

**테스트 대상**: `src/controllers/project_controller.py`

**주요 테스트 케이스**:
- 새 프로젝트 생성
- 프로젝트 저장/불러오기
- 프로젝트 닫기 (변경사항 처리)
- 파일 경로 유효성 검사
- 오류 상황 처리

### 2. DataController 테스트 (`test_data_controller.py`)

**테스트 대상**: `src/controllers/data_controller.py`

**주요 테스트 케이스**:
- CSV/Excel 파일 가져오기
- 다양한 인코딩 처리 (UTF-8, CP949)
- 데이터 내보내기
- 데이터 요약 정보 생성
- 대용량 데이터 처리
- 오류 파일 처리

### 3. AnalysisController 테스트 (`test_analysis_controller.py`)

**테스트 대상**: `src/controllers/analysis_controller.py`

**주요 테스트 케이스**:
- 기초 통계 분석
- 상관분석
- ANOVA 분석
- 회귀분석
- 결측값 처리
- 데이터 유효성 검사

### 4. ChartController 테스트 (`test_chart_controller.py`)

**테스트 대상**: `src/controllers/chart_controller.py`

**주요 테스트 케이스**:
- 8가지 차트 타입 생성 (히스토그램, 박스플롯, 산점도 등)
- 차트 옵션 적용
- 그룹별 차트 생성
- 차트 유효성 검사
- matplotlib Figure 객체 생성 확인

### 5. 유틸리티 테스트 (`test_utils.py`)

**테스트 대상**: 
- `src/utils/data_utils.py`
- `src/utils/file_utils.py`

**주요 테스트 케이스**:
- 인코딩 자동 감지
- 데이터프레임 유효성 검사
- 파일 I/O 작업
- 안전한 파일명 생성
- JSON 데이터 처리

## 테스트 데이터

각 테스트에서는 다음과 같은 테스트 데이터를 사용합니다:

```python
# 기본 테스트 데이터
test_data = pd.DataFrame({
    'numerical_1': [1, 2, 3, 4, 5],
    'numerical_2': [10.5, 20.5, 30.5, 40.5, 50.5],
    'categorical': ['A', 'B', 'C', 'D', 'E'],
    'boolean': [True, False, True, False, True]
})

# 통계 분석용 대용량 데이터
large_data = pd.DataFrame({
    'score': np.random.normal(75, 15, 100),
    'group': np.random.choice(['A', 'B', 'C'], 100),
    'treatment': np.random.choice(['T', 'C'], 100)
})
```

## 모킹(Mocking)

테스트에서는 다음 요소들을 모킹합니다:

- **파일 다이얼로그**: `QFileDialog.getOpenFileName`, `QFileDialog.getSaveFileName`
- **메시지 박스**: `QMessageBox.critical`, `QMessageBox.question`
- **시그널/슬롯**: Qt 시그널 연결 및 발생 확인

## 코드 커버리지

코드 커버리지 분석을 위해서는 `coverage` 패키지를 설치해야 합니다:

```bash
pip install coverage
```

커버리지 실행:

```bash
# 테스트와 함께 커버리지 실행
python test/run_tests.py --coverage

# 또는 직접 커버리지 실행
coverage run -m unittest discover test
coverage report
coverage html  # HTML 보고서 생성
```

## 테스트 작성 가이드라인

### 1. 테스트 파일 명명 규칙
- `test_<모듈명>.py` 형식
- 테스트 클래스는 `Test<클래스명>` 형식
- 테스트 메서드는 `test_<기능명>` 형식

### 2. 테스트 구조
```python
def test_기능명(self):
    """기능 설명"""
    # Given - 테스트 준비
    # When - 테스트 실행
    # Then - 결과 검증
```

### 3. 어설션(Assertion) 사용
- `assertEqual()`: 값 비교
- `assertTrue()`, `assertFalse()`: 불린 값 검증
- `assertIn()`, `assertNotIn()`: 포함 관계 검증
- `assertIsNone()`, `assertIsNotNone()`: None 검증
- `assertRaises()`: 예외 발생 검증

### 4. 임시 파일 처리
```python
def setUp(self):
    self.temp_dir = tempfile.mkdtemp()

def tearDown(self):
    shutil.rmtree(self.temp_dir, ignore_errors=True)
```

## 지속적 통합(CI) 통합

GitHub Actions 등 CI 환경에서 테스트를 실행할 수 있습니다:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install coverage
    - name: Run tests
      run: python test/run_tests.py --coverage
```

## 문제 해결

### 1. ImportError 발생 시
- `src/` 디렉토리가 Python 경로에 추가되었는지 확인
- 상대 경로가 올바른지 확인

### 2. Qt 관련 오류 시
- QApplication 초기화 여부 확인
- 테스트에서 실제 GUI 위젯 대신 Mock 객체 사용

### 3. 파일 권한 오류 시
- 임시 디렉토리 권한 확인
- tearDown에서 파일 정리 확인

## 참고 자료

- [Python unittest 공식 문서](https://docs.python.org/3/library/unittest.html)
- [unittest.mock 가이드](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py 문서](https://coverage.readthedocs.io/)
- [PySide6 테스팅 가이드](https://doc.qt.io/qtforpython/tutorials/qmltutorial/index.html) 