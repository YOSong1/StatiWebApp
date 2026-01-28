# DeskTopApp 리팩토링 문서

이 문서는 `DeskTopApp` 프로젝트의 가독성 향상과 유지보수를 위한 리팩토링 과정을 기록합니다.

## 1. 리팩토링 목표

- **아키텍처 개선**: 기존의 View 중심 로직을 Model-View-Controller(MVC) 패턴으로 전환하여 관심사를 명확히 분리합니다.
- **코드 응집도 향상**: 관련된 기능들을 각자의 Controller와 Model로 묶어 응집도를 높입니다.
- **View 단순화**: View(UI) 계층의 코드는 사용자 인터페이스 표시에만 집중하도록 비즈니스 로직을 모두 Controller로 이동합니다.
- **상태 관리 중앙화**: 프로젝트 데이터와 애플리케이션 상태를 Model에서 중앙 관리하여 데이터 흐름을 명확하게 합니다.
- **유지보수성 및 확장성 확보**: 향후 새로운 기능을 추가하거나 기존 기능을 수정하기 용이한 구조를 만듭니다.

## 2. 주요 변경 사항

### 2.1. 프로젝트 관리 로직 분리 (Project Management Refactoring)

**문제점**:
- 프로젝트 생성, 저장, 불러오기 등의 핵심 로직이 `views/main_window.py`에 직접 구현되어 있어 View가 너무 많은 역할을 수행하고 있었습니다.
- 프로젝트 데이터 구조가 `dict` 형태로 명시적이지 않게 사용되어 데이터의 형태를 파악하기 어려웠습니다.
- `utils/project_manager.py`는 View에서 직접 호출되어 의존성 방향이 복잡했습니다.

**해결책**:
1.  **`models/project.py` 생성**:
    - 프로젝트의 모든 데이터(데이터프레임, 분석 결과, 차트 히스토리 등)를 담는 `Project` 데이터 클래스를 정의했습니다.
    - 이를 통해 프로젝트의 상태를 명확하고 타입-세이프하게 관리할 수 있습니다.

2.  **`controllers/project_controller.py` 생성**:
    - `Project` 모델을 관리하는 컨트롤러를 만들었습니다.
    - `main_window.py`에 있던 프로젝트 관련 메서드(`new_project`, `open_project`, `save_project` 등)를 모두 이곳으로 이전했습니다.
    - 기존 `utils/project_manager.py`의 파일 입출력 로직을 통합하고 해당 파일을 삭제하여 로직을 중앙화했습니다.

3.  **`views/main_window.py` 리팩토링**:
    - `ProjectController`를 멤버로 소유하고, UI 액션(메뉴 클릭 등)이 발생하면 컨트롤러의 메서드를 호출하도록 변경했습니다.
    - 컨트롤러에서 발생하는 시그널(`project_loaded`, `status_updated` 등)을 받아 UI를 갱신하는 역할만 수행하도록 코드를 대폭 축소하고 단순화했습니다.

### 2.2. 데이터 관리 로직 분리 (Data Management Refactoring)

**문제점**:
- 데이터 가져오기/내보내기 로직이 `views/main_window.py`에 직접 구현되어 있어 View가 파일 시스템과 직접 상호작용하고 있었습니다.
- 데이터 유효성 검증, 인코딩 처리, 파일 형식 지원 등의 로직이 UI 코드와 섞여 있어 재사용성이 낮았습니다.
- 오류 처리가 각 메서드마다 중복되어 있어 일관성 있는 오류 처리가 어려웠습니다.

**해결책**:
1.  **`controllers/data_controller.py` 생성**:
    - 데이터 가져오기/내보내기의 모든 비즈니스 로직을 담당하는 `DataController` 클래스를 만들었습니다.
    - CSV, Excel 파일의 자동 인코딩 감지 및 처리 로직을 중앙화했습니다.
    - 데이터 유효성 검증(중복 열 이름, 대용량 데이터 경고 등)을 체계화했습니다.
    - 데이터 요약 정보 생성 및 분석 적합성 검증 기능을 추가했습니다.

2.  **`views/main_window.py` 수정**:
    - 기존의 `import_data`와 `export_data` 메서드를 제거했습니다.
    - `DataController`의 시그널(`data_imported`, `data_exported`)을 받아 UI를 업데이트하는 슬롯 메서드들을 추가했습니다.
    - 메뉴 액션을 `DataController`의 슬롯에 직접 연결하여 View의 역할을 단순화했습니다.

3.  **향상된 기능**:
    - **자동 인코딩 감지**: CSV 파일의 인코딩을 자동으로 감지하여 한글 파일도 올바르게 처리합니다.
    - **대용량 데이터 처리**: 100만 행 이상의 데이터에 대해 사용자에게 확인을 요청합니다.
    - **데이터 유효성 검증**: 중복 열 이름, 빈 데이터 등을 사전에 검사합니다.
    - **분석 적합성 검증**: 분석에 필요한 최소 조건(행 수, 숫자형 데이터 존재 등)을 확인합니다.

### 2.3. 분석 로직 분리 (Analysis Logic Refactoring)

**문제점**:
- 통계 분석 로직이 `views/project_explorer.py`에 직접 구현되어 있어 View가 복잡한 계산 로직을 포함하고 있었습니다.
- 분석 메서드들이 `views/main_window.py`에 중복으로 정의되어 일관성이 부족했습니다.
- 오류 처리와 결과 해석이 각 분석마다 다르게 구현되어 있었습니다.

**해결책**:
1.  **`controllers/analysis_controller.py` 생성**:
    - 기초 통계, 상관분석, ANOVA, 회귀분석의 모든 로직을 중앙화했습니다.
    - 각 분석에 대한 데이터 유효성 검증을 표준화했습니다.
    - 통계적 해석 기능을 추가하여 사용자가 결과를 쉽게 이해할 수 있도록 했습니다.
    - 라이브러리 의존성 오류를 우아하게 처리하도록 개선했습니다.

2.  **분석 결과 구조 표준화**:
    - 모든 분석 결과가 동일한 구조(`type`, `timestamp`, `status`, `description`, `results`)를 가지도록 했습니다.
    - 결과에 통계적 해석을 자동으로 포함하여 사용자 친화적으로 만들었습니다.

3.  **`views/main_window.py` 연동**:
    - `AnalysisController`의 시그널을 받아 UI를 업데이트하는 슬롯을 추가했습니다.
    - 기존의 중복된 분석 메서드들을 `AnalysisController`를 사용하도록 수정했습니다.

### 2.4. 현재 진행 상황

**✅ 완료된 작업**:
- [x] 프로젝트 관리 로직 분리 (`ProjectController`)
- [x] 데이터 관리 로직 분리 (`DataController`)
- [x] 분석 로직 분리 (`AnalysisController`)
- [x] 차트 생성 로직 분리 (`ChartController`)
- [x] `views/main_window.py` 중복 메서드 정리 (16개 중복 메서드 제거)
- [x] 공통 유틸리티 정리 (`utils/data_utils.py`, `utils/file_utils.py`)
- [x] `utils/project_manager.py` 제거 및 로직 통합
- [x] View 클래스들의 역할 단순화

**✅ 추가 완료된 작업**:
- [x] 테스트 코드 작성 완료 (src/test 구조로 변경)
- [x] 코드를 `src/` 폴더로 구조 변경
- [x] `test/` 폴더에 92개 테스트 케이스 포함한 단위 테스트 작성
- [x] 테스트 실행 스크립트 (`run_tests.py`) 및 문서 작성

**📋 향후 추천 작업**:
- [ ] `views/project_explorer.py`에서 분석 관련 메서드들을 제거하고 `AnalysisController` 사용
- [ ] `views/results_view.py`와 `views/analysis_detail_dialog.py` 최적화
- [ ] 에러 처리 표준화 및 로깅 시스템 구축
- [ ] CI/CD 파이프라인 구축 (GitHub Actions)
- [ ] 코드 커버리지 목표 설정 및 개선

### 2.5. 아키텍처 개선 효과

**코드 재사용성**: 
- 분석 로직이 컨트롤러에 중앙화되어 여러 View에서 동일한 로직을 재사용할 수 있게 되었습니다.

**유지보수성**: 
- 각 컨트롤러가 명확한 책임을 가지므로 버그 수정이나 기능 추가가 쉬워졌습니다.

**테스트 용이성**: 
- View로부터 분리된 컨트롤러들은 독립적으로 단위 테스트가 가능합니다.

**확장성**: 
- 새로운 분석 기법을 추가할 때 `AnalysisController`에만 메서드를 추가하면 됩니다.

**(계속 진행 중...)** 