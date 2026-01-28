# DOE Tool Web (FastAPI) 가이드

데스크톱(PySide6) 애플리케이션의 **계산/설계/차트 로직을 변경하지 않고**, 웹에서 동일한 흐름으로 실행할 수 있도록 FastAPI 레이어를 추가한 버전입니다.

## 1) 실행 방법(Windows)

가상환경은 현재 저장소의 `env/`를 사용한다고 가정합니다.

### A. 의존성 설치(최소)

```powershell
cd d:\StatisticsLecture\StatiWebApp
env\Scripts\python.exe -m pip install fastapi uvicorn[standard] python-multipart jinja2
```

### B. 서버 실행

권장(정석): uvicorn으로 실행

```powershell
cd d:\StatisticsLecture\StatiWebApp
env\Scripts\python.exe -m uvicorn webapp.app:app --app-dir "d:\StatisticsLecture\StatiWebApp\src" --host 127.0.0.1 --port 8000
```

간편 실행: python으로 바로 실행

```powershell
cd d:\StatisticsLecture\StatiWebApp
env\Scripts\python.exe "d:\StatisticsLecture\StatiWebApp\src\webapp\app.py"
```

개발 중 자동 리로드가 필요하면 `--reload` 옵션을 붙일 수 있습니다. 단, 가장 안정적인 리로드는 uvicorn 명령에 `--reload`를 붙여 실행하는 방식입니다.

### C. 접속

- 웹 UI: <http://127.0.0.1:8000/>
- API 문서(Swagger): <http://127.0.0.1:8000/docs>

## 2) 웹 UI 기본 사용 흐름

이 버전의 웹 UI는 “프로젝트 관리”를 노출하지 않고, **업로드 → 분석 선택 → 결과/시각화**에 집중합니다.

1. 메인 화면(`/`)에서 **CSV/XLSX를 업로드**합니다.
2. 업로드된 데이터의 컬럼이 자동으로 로드되면 **Response/Factors를 선택**합니다.
3. **DOE ANOVA + 주효과/상호작용도** 버튼(또는 개별 분석 버튼)을 눌러 결과를 확인합니다.
4. 하단의 **상관행렬/히스토그램** 등 추가 시각화를 확인합니다.

필요하면 **새 작업 시작** 버튼으로 내부 상태(프로젝트)를 초기화할 수 있습니다.

## 2-1) 데이터 패턴 기반 추천

업로드 후 화면에 **추천 버튼**이 자동으로 생성됩니다.

- 추천은 컬럼의 dtype/고유값 개수(수준 수)로 요인/반응 후보를 추정해 제공합니다.
- 예: 요인 후보(범주형 또는 수준이 적은 숫자형) + 반응 후보(연속형 숫자형)가 있으면 `DOE ANOVA` 워크플로우를 추천합니다.

화면에서 **추천 근거 보기(컬럼 프로파일)** 를 열면 아래 정보를 확인할 수 있습니다.

- 각 컬럼의 dtype
- 결측치 수(missing)
- 고유값 개수(unique)
- response 후보 / factor 후보 여부
- (가능한 경우) 수준(level) 미리보기

추천 API를 직접 호출할 수도 있습니다.

- `GET /api/v1/recommendations/projects/{project_id}`

참고: 내부적으로는 기존 API의 `project_id`를 자동으로 생성/저장(localStorage)하여 계산 로직을 그대로 재사용합니다.

## 3) API 사용 흐름(프론트 개발자용)

OpenAPI 스키마는 `/docs` 또는 `/openapi.json`에서 확인할 수 있습니다.

예시 흐름:

1. `POST /api/v1/projects` → `project_id` 확보
2. `POST /api/v1/projects/{project_id}/data/upload` (multipart 업로드)
3. `POST /api/v1/analysis/projects/{project_id}/basic_statistics`
4. `POST /api/v1/charts/projects/{project_id}` → `image_base64_png`

## 4) 주의사항

- 프로젝트 저장소는 현재 **서버 메모리 기반**입니다. 서버 재시작 시 in-memory 프로젝트는 초기화됩니다.
- 데스크톱 로직은 그대로 호출하므로, 입력 데이터 형식/변수명 제약은 기존 컨트롤러 로직을 따릅니다.
