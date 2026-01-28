# TODO v2 - 실험계획법 중심 실행 플랜

## 우선순위 흐름
1) **기반 정리**: PySide6 단일화, 인코딩 복구(UTF-8), `data_view.py` 재작성 및 DF-테이블 동기화, `analysis_controller.py` 문법/로직 복구, `requirements.txt` 정리(PyQt5 제거 등), 기본 아이콘/QSS 경로 수정 또는 자원 추가.
2) **실험계획법 핵심 메뉴 1차 구현(필수)**  
   - 정규/부분요인 설계(2-level full/frac factorial, Plackett-Burman) 생성 및 설계행렬/런시트 저장.  
   - 반응표면(RSM: CCD, Box-Behnken) 설계 생성.  
   - 블록/난수/순서 무작위화 옵션, 반복수 설정.  
   - 설계 타당성 검증(해당 요인·수준 수 입력 검증, 런 수 표시, 설계 요약).  
3) **분석 파이프라인 연결(필수)**  
   - 설계결과 → 데이터 입력/불러오기와 연계, 요인/반응 변수 매핑 UI.  
   - ANOVA(주효과/교호효과) 자동 모델 적합 및 유의성 테이블 출력.  
   - 잔차진단(정규성 Q-Q, 등분산, 영향도) 기본 차트.  
4) **DOE 시각화(필수)**  
   - 주효과/교호효과 플롯.  
   - 반응표면/등고선 플롯(2인자 기준).  
   - 최적화 탐색(그래픽 없이라도 조건 스캔 + 예측값/제약 필터).  
5) **보고/저장(필수)**: 설계 사양, 모델 결과, 플롯 요약을 PDF/Markdown/HTML 중 하나로 내보내기.
6) **테스트/검증**: 설계 생성/모델 적합/시각화 함수 단위 테스트, 샘플 데이터 기반 스모크 테스트, `test/run_tests.py` 갱신.

## 세부 작업 목록
- [ ] PySide6로 뷰 정리, `data_view.py` 재작성(Pass 제거, 행/열 삽입·삭제, 타입 변경, 복사/붙여넣기, DF 동기화).
- [ ] `analysis_controller.py` 문자열/따옴표 오류 수정, 변수 선택/결과 구조화 보강.
- [ ] 인코딩 정리(README, 메뉴 문서 등 UTF-8), 한글 메시지 복구.
- [ ] 의존성 정리(PyQt5 제거, pandas 중복 제거, 미사용 무거운 패키지 분리).
- [ ] 리소스 경로 수정 또는 `resources/icons`, `resources/styles` 추가.
- [ ] **DOE 설계 생성 UI/로직**:  
  - [ ] 정규 2수준 요인설계(Full factorial).  
  - [ ] 부분요인 설계(Resolution III/IV/V, 생성 다항식 옵션).  
  - [ ] Plackett-Burman.  
  - [ ] RSM: CCD(중심점/별점 거리 설정), Box-Behnken.  
  - [ ] 블로킹/랜덤화/반복수 옵션.  
  - [ ] 설계 요약(런 수, 요인·수준 요약) 및 런시트 내보내기(CSV/XLSX).
- [ ] **DOE-데이터 연계**: 설계 출력 → 데이터 시트 매핑(요인/반응 선택), 결측/형식 검증.
- [ ] **DOE 분석**: 주효과/교호효과 포함 ANOVA 모델 적합, 유의성/회귀계수/잔차 통계 출력.
- [ ] **잔차 진단 차트**: Q-Q, 잔차 vs 적합, 레버리지/쿡거리 요약.
- [ ] **DOE 시각화**: 주효과/교호효과 플롯, 반응표면/등고선(2인자), 필요 시 plotly 대체 가능.
- [ ] **최적화(간이)**: 설계 모델 기반 예측 함수와 조건 스캔으로 목표/제약 충족 조합 제안.
- [ ] **보고서 출력**: 설계 사양 + 모델 결과 + 주요 플롯을 Markdown→PDF/HTML 변환 또는 직접 HTML 렌더.
- [ ] 테스트 보강: 설계 생성 함수, ANOVA/회귀 결과, 시각화 호출 스모크 테스트; 샘플 데이터 고정.

## 제거/보류 제안
- 실무 DOE와 무관한 과도한 데이터 품질/대시보드 기능(예: great-expectations 기반 검증, 일반 BI 차트)은 초기 릴리스에서 보류 가능.
- UI 테마/고급 아이콘 작업은 핵심 DOE 기능 안정화 이후 진행.

---

## 2026-01-10 업데이트

### 완료/반영
- [x] `data_view.py` 편집/동기화 강화: 셀 단위 선택, 숨김/복원, 키 이동(Enter/좌우/상하) 커밋, 열 폭 균등/제한.
- [x] `analysis_controller.py` ANOVA/RSM 경로 보강: DOE ANOVA 포화시 단순화, main-effects ANOVA, RSM/Box-Behnken/CCD 2차 모델 추가.
- [x] DOE 분석 메뉴 연결: 완전요인 ANOVA 통합, 부분요인/Plackett/직교/Taguchi/혼합/분할구/RSM/Box-Behnken/CCD 메뉴 실행 경로 구현.
- [x] 차트: 주효과도/상호작용도 연속형 요인 지원, 제목/여백/폰트 개선, 차트 유형 자동 활성/비활성.
- [x] 프로젝트 저장 직렬화 개선(DataFrame/Series 포함), 분석/차트 복원, 차트 재생성.
- [x] 샘플 데이터 생성: sample2, rsm_sample, boxbehnken_sample, ccd_sample, orthogonal/taguchi_sample, mixture_sample, splitplot_sample.
- [x] 잔차 진단 플롯(Q-Q, 잔차 vs 적합) 상세보기 시각화 추가.
- [x] 상세보기 다이얼로그 기본 채움(ANOVA 요약/핵심 지표/표/잔차 플롯).

### TODO (우선순위)
- [ ] DOE 설계 생성 UI/로직: Full/Frac/Plackett/CCD/Box-Behnken 설계 생성 및 요약, 런시트 저장, 블록/랜덤화/반복 옵션.
- [ ] DOE-데이터 연계: 설계→데이터 시트 매핑(요인/반응 선택), 결측/형식 검증 가이드.
- [ ] 보고서/내보내기: 설계 사양 + 모델 결과 + 주요 플롯을 Markdown/PDF/HTML로 export.
- [ ] 잔차 진단 추가(레버리지/쿡거리 요약).
- [ ] 최적화(간이): 모델 기반 예측/조건 스캔 UI.
- [ ] 테스트 보강: 설계 생성/ANOVA/RSM/시각화 스모크 테스트, 샘플 데이터 기반 검증 스크립트.




---

Update TODO List - 2026-01-15

### Completed / Added
- Data menu: edit/transform/view features (row/col insert/delete, sort, find/replace, rename/type/derived/dummy/merge, summary/variable info/preview/filter)
- Clipboard paste: overwrite vs append option
- Data quality processing: missing/outlier logic implemented
- Unified data quality UI: target columns + preview + processing order
- Data quality logs added to Results tab
- Data validation menu removed
- Enter key commit stability in data grid
- DOE special designs: mixture component names + sum=1 notice, split-plot per-block seed, custom design template/ranges
- Data menu activation after DOE generation

### Remaining
- DOE report/export (spec + model + key plots)
- Optimization UI (goals/constraints)
- Residual diagnostics/leverages
- Test automation
- Docs/resources cleanup

### 완료/추가
- 데이터 메뉴 편집/변환/뷰 기능 구현
- 클립보드 붙여넣기 덮어쓰기/덧붙이기 선택
- 결측/이상값 처리 로직 구현
- 결측/이상값 통합 UI + 미리보기 + 처리 순서 옵션
- 처리 로그 결과 탭 기록
- 데이터 검증 메뉴 제거
- Enter 입력 커밋 문제 해결
- DOE 특수 설계 보완(혼합/스플릿플롯/커스텀)
- 설계 생성 후 데이터 메뉴 활성화

### 남은 작업
- DOE 보고서/내보내기
- 최적 조건 탐색 UI
- 잔차 진단/영향점 분석 보강
- 테스트/검증 자동화
- 문서/리소스 정리
