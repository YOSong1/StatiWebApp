# 메뉴 구조 및 용도 (현재 코드 기준 요약)

## 파일
- 새 프로젝트, 프로젝트 열기/저장/다른 이름으로 저장: `.doeproj` 로드/저장.
- 종료: 앱 종료.

## 데이터
- 데이터 가져오기: CSV/XLSX 불러와 그리드에 표시.
- 데이터 내보내기 / 데이터 저장: 현재 테이블을 CSV/XLSX로 저장.
- Append Data (CSV/XLSX): 컬럼이 동일한 다른 CSV/XLSX를 읽어 행 단위로 이어붙임.

## 실험설계 (새 런시트 생성 후 기존 데이터 덮어씀)
- Screening Designs: Full Factorial, Fractional Factorial(생성자 문자열), Plackett-Burman.
- Response Surface: CCD(RSM), Box-Behnken, Central Composite.
- Robust/Orthogonal: Orthogonal Array(Taguchi), Taguchi(동일 동작).
- Special: Mixture(미구현 안내), Split-Plot(미구현 안내), Custom Design(미구현 안내).

## 분석 (일반 통계/다변량; DOE 설계 생성과 별개)
- 기초 통계: 요약통계 등.
- 분산분석(ANOVA): 일원/이원/다원/반복측정 ANOVA 등.
- DOE: DOE ANOVA(요인/반응 선택) - 현재 데이터에서 요인·반응을 선택해 주효과/교호효과 포함 ANOVA 수행.
- 회귀분석: 선형/다중 회귀 등.
- 상관분석: 상관행렬.
- 비모수검정: 비모수 테스트 모음.
- 다변량분석: PCA, 군집분석, 판별분석 등.
- 종합분석 실행: 기초 통계/상관/회귀를 일괄 수행.

## 차트
- 기본/DOE/잔차 등 다양한 차트 뷰 호출(상세 항목은 코드 다수, 기존 차트 컨트롤러와 연동).

## 도구
- 글꼴/환경 관련 유틸(코드상 폰트 리빌드 등), 기타 개발용 도구.

## 도움말
- 앱 정보, 사용 안내 등.
