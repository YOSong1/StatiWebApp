# 📋 DOE Tool 메뉴 수정 및 개선 기록

## 🎯 **수정 개요**
- **날짜**: 2025-06-15
- **목적**: 메뉴 사용성 개선 및 오류 해결
- **주요 개선**: 스마트 분석 가이드 시스템 도입

---

## 🚨 **발견된 문제점들**

### **1. 메뉴 비활성화 문제**
- **문제**: 데이터가 없으면 모든 분석 메뉴가 비활성화됨
- **사용자 불편**: 메뉴 선택 → 데이터 준비 방식 불가능
- **요구사항**: 두 가지 방식 모두 지원 필요
  - (1) 데이터 열기 → 메뉴 선택
  - (2) 메뉴 선택 → 데이터 열기

### **2. strftime 오류**
- **오류 메시지**: `'str' object has no attribute 'strftime'`
- **발생 위치**: `project_explorer.py` 351번 줄
- **원인**: timestamp가 이미 문자열인데 strftime() 호출

### **3. 분석 실행 오류**
- **기초 통계**: strftime 오류로 실행 실패
- **일원분산분석**: 권장 샘플 데이터 로드 후에도 오류 발생
- **사용자 혼란**: 적절한 안내 부족

---

## ✅ **구현된 해결방안**

### **1. 스마트 분석 가이드 시스템**

#### **핵심 기능**
- **메뉴 항상 활성화**: 데이터 유무와 관계없이 모든 분석 메뉴 선택 가능
- **지능형 데이터 검증**: 현재 데이터 상태 자동 분석
- **맞춤형 샘플 데이터 추천**: 분석 유형별 최적 샘플 자동 선택
- **원클릭 해결**: 샘플 데이터 로드 후 분석 자동 재실행

#### **구현 파일**
- `main_window.py`: 메뉴 활성화 로직 수정, 스마트 가이드 구현
- `analysis_guide_dialog.py`: 기존 가이드 개선

### **2. 메뉴 활성화 로직 수정**

#### **수정 위치**: `main_window.py` - `update_ui_state()` 메서드

**수정 전:**
```python
# 분석 관련 액션 활성화/비활성화
self.basic_stats_action.setEnabled(has_data)
self.one_way_anova_action.setEnabled(has_data)
# ... 모든 분석 메뉴가 has_data에 의존
```

**수정 후:**
```python
# 분석 관련 액션은 항상 활성화 (데이터 없으면 가이드 표시)
self.basic_stats_action.setEnabled(True)
self.one_way_anova_action.setEnabled(True)
# ... 모든 분석 메뉴 항상 활성화
```

### **3. timestamp 오류 해결**

#### **수정 위치**: `project_explorer.py` - `add_analysis_result()` 메서드

**수정 전:**
```python
item.setText(2, result["timestamp"].strftime("%H:%M:%S"))
```

**수정 후:**
```python
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
```

### **4. 스마트 가이드 구현**

#### **새로운 메서드들**

**A. 샘플 데이터 추천 시스템**
```python
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
        }
        # ... 기타 분석 유형들
    }
```

**B. 데이터 검증 시스템**
```python
def validate_data_for_analysis(self, analysis_type, data):
    """현재 데이터가 분석에 적합한지 검증"""
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
```

**C. 스마트 가이드 다이얼로그**
```python
def show_smart_analysis_guide(self, analysis_type, current_data, validation_message):
    """스마트 분석 가이드 - 데이터 상태에 따른 맞춤형 안내"""
    # 현재 데이터 상태 분석 표시
    # 권장 샘플 데이터 정보 제공
    # 원클릭 해결 버튼 제공
    # - "📊 샘플 데이터 불러오기"
    # - "📁 직접 데이터 가져오기"
```

### **5. 분석 메서드 강화**

#### **모든 분석 메서드에 공통 적용된 개선사항**

**A. 안전한 데이터 처리**
```python
# 현재 데이터 확인
current_data = None
if self.data_view.has_data():
    current_data = self.data_view.get_data()

# 데이터 검증
is_valid, message = self.validate_data_for_analysis('분석명', current_data)

if not is_valid:
    # 데이터가 없거나 부적합한 경우 스마트 가이드 표시
    self.show_smart_analysis_guide('분석명', current_data, message)
    return

try:
    # 데이터 복사본으로 안전한 처리
    data = current_data.copy()
    
    # 결측값 제거 및 추가 검증
    # ...
    
except Exception as e:
    QMessageBox.critical(self, "오류", f"분석 중 오류가 발생했습니다:\n{str(e)}")
    print(f"분석 오류 상세: {e}")  # 디버깅용
```

**B. 강화된 결과 구성**
- 추가 통계량 계산 (분산, 왜도, 첨도 등)
- 결측값 정보 상세 제공
- 강한 상관관계 자동 탐지
- 그룹별 기술통계 제공

---

## 📁 **수정된 파일 목록**

### **1. 핵심 수정 파일**
- `src/views/main_window.py` - 메뉴 활성화, 스마트 가이드, 분석 메서드 강화
- `src/views/project_explorer.py` - timestamp 처리 개선
- `src/views/analysis_guide_dialog.py` - 가이드 내용 개선

### **2. 문서 파일**
- `사용법_가이드.md` - v2.0으로 업데이트, 스마트 가이드 사용법 추가
- `메뉴_구현_현황.md` - 현재 구현 상태 상세 정리

---

## 🎯 **분석별 개선사항**

### **기초 통계 분석**
- ✅ 추가 통계량 계산 (분산, 왜도, 첨도)
- ✅ 결측값 비율 계산
- ✅ 유효 관측값 수 표시

### **상관분석**
- ✅ 상관계수 유의성 검정 추가
- ✅ 강한 상관관계 자동 탐지 (|r| ≥ 0.7)
- ✅ 상관관계 강도 분류

### **일원분산분석**
- ✅ 그룹별 기술통계 제공
- ✅ 각 그룹 최소 크기 검증
- ✅ F-검정 결과 상세 해석

### **이원분산분석**
- ✅ 요인 조합별 데이터 검증
- ✅ Q() 함수로 컬럼명 안전 처리
- ✅ 주효과와 상호작용 효과 분리

---

## 🚀 **사용자 경험 개선**

### **Before (수정 전)**
1. 데이터 없으면 메뉴 비활성화
2. 오류 발생 시 기술적 메시지만 표시
3. 어떤 데이터를 써야 할지 모름
4. 분석 실패 시 해결방법 불명확

### **After (수정 후)**
1. ✅ 메뉴 항상 활성화, 언제든 선택 가능
2. ✅ 친절한 가이드와 구체적 해결방안 제시
3. ✅ 분석별 최적 샘플 데이터 자동 추천
4. ✅ 원클릭으로 문제 해결 및 분석 자동 실행

---

## 📊 **구현 현황 매트릭스**

| 분석 유형 | 구현 상태 | 스마트 가이드 | 샘플 데이터 | 자동 검증 |
|-----------|-----------|---------------|-------------|-----------|
| 기초 통계 | ✅ 완료 | ✅ 적용 | basic_statistics_sample.xlsx | ✅ 적용 |
| 상관분석 | ✅ 완료 | ✅ 적용 | basic_statistics_sample.xlsx | ✅ 적용 |
| 일원분산분석 | ✅ 완료 | ✅ 적용 | factorial_2x3_design_categorical.xlsx | ✅ 적용 |
| 이원분산분석 | ✅ 완료 | ✅ 적용 | factorial_2x3_design_categorical.xlsx | ✅ 적용 |
| 다원분산분석 | 🚧 가이드만 | ✅ 적용 | - | ✅ 적용 |
| 단순회귀분석 | 🚧 가이드만 | ✅ 적용 | - | ✅ 적용 |
| 다중회귀분석 | 🚧 가이드만 | ✅ 적용 | - | ✅ 적용 |

---

## 🔄 **다음 개발 우선순위**

### **우선순위 1 (즉시 필요)**
1. **단순회귀분석 구현**
   - 상관분석 기반으로 확장
   - 회귀선 그래프 추가
   - R², 회귀계수 유의성 검정

2. **다중회귀분석 구현**
   - 단순회귀 확장
   - 다중공선성 진단
   - 잔차 분석

3. **기본 차트 기능**
   - 산점도 (회귀선 포함)
   - 히스토그램
   - 상자그림

### **우선순위 2 (다음 버전)**
1. **비모수 검정**
   - Mann-Whitney U 검정
   - Kruskal-Wallis 검정
   - Wilcoxon 부호순위 검정

2. **데이터 편집 기능**
   - 행/열 삽입/삭제
   - 데이터 정렬
   - 찾기/바꾸기

3. **데이터 변환**
   - 로그 변환
   - 표준화/정규화
   - 더미 변수 생성

### **우선순위 3 (장기 계획)**
1. **DOE 설계 생성**
   - 완전요인설계
   - 부분요인설계
   - 반응표면법

2. **고급 차트**
   - 주효과 그림
   - 상호작용 그림
   - 등고선 그림

3. **다변량 분석**
   - 주성분분석 (PCA)
   - 군집분석
   - 판별분석

---

## 🛠️ **개발 가이드라인**

### **새 기능 추가 시 체크리스트**
1. ✅ 메뉴 액션 생성 및 연결
2. ✅ 데이터 검증 로직 구현 (`validate_data_for_analysis`)
3. ✅ 실제 분석/처리 기능 구현
4. ✅ 결과 표시 및 저장
5. ✅ 오류 처리 및 사용자 안내
6. ✅ 스마트 가이드 정보 업데이트 (`get_recommended_sample_data`)
7. ✅ 샘플 데이터 준비 (필요시)
8. ✅ 사용법 가이드 업데이트

### **코드 구조 패턴**
```python
def run_new_analysis(self):
    """새로운 분석 실제 구현"""
    # 1. 현재 데이터 확인
    current_data = None
    if self.data_view.has_data():
        current_data = self.data_view.get_data()
    
    # 2. 데이터 검증
    is_valid, message = self.validate_data_for_analysis('분석명', current_data)
    
    if not is_valid:
        # 3. 스마트 가이드 표시
        self.show_smart_analysis_guide('분석명', current_data, message)
        return
        
    try:
        # 4. 안전한 데이터 처리
        data = current_data.copy()
        
        # 5. 분석 실행
        # ...
        
        # 6. 결과 구성
        result = {
            'type': '분석명',
            # ...
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 7. 결과 저장 및 표시
        self.project_explorer.add_analysis_result('분석명', result, '완료')
        self.results_view.add_analysis_result('분석명', result)
        self.tab_widget.setCurrentWidget(self.results_view)
        
    except Exception as e:
        # 8. 오류 처리
        QMessageBox.critical(self, "오류", f"분석 중 오류가 발생했습니다:\n{str(e)}")
        print(f"분석 오류 상세: {e}")  # 디버깅용
```

---

## 📝 **테스트 시나리오**

### **시나리오 1: 스마트 가이드 테스트**
1. 애플리케이션 실행
2. 분석 → 기초 통계 선택 (데이터 없는 상태)
3. 스마트 가이드 창 확인
4. "📊 샘플 데이터 불러오기" 클릭
5. 자동 데이터 로드 및 분석 실행 확인

### **시나리오 2: 오류 처리 테스트**
1. 부적절한 데이터로 분석 시도
2. 구체적인 오류 메시지 확인
3. 해결방안 제시 확인

### **시나리오 3: 두 가지 사용 방식 테스트**
1. 방식 1: 파일 → 데이터 가져오기 → 분석 선택
2. 방식 2: 분석 선택 → 스마트 가이드 → 샘플 데이터 로드

---

## 🎉 **최종 결과**

### **사용자 만족도 개선**
- ❌ 메뉴 비활성화로 인한 혼란 → ✅ 언제든 메뉴 선택 가능
- ❌ 기술적 오류 메시지 → ✅ 친절한 가이드와 해결방안
- ❌ 샘플 데이터 찾기 어려움 → ✅ 자동 추천 및 원클릭 로드
- ❌ 분석 실패 시 막막함 → ✅ 단계별 안내와 자동 재실행

### **개발자 관점 개선**
- ✅ 일관된 오류 처리 패턴
- ✅ 확장 가능한 검증 시스템
- ✅ 재사용 가능한 가이드 프레임워크
- ✅ 디버깅 정보 자동 출력

---

**작성일**: 2025-06-15  
**버전**: v2.0  
**다음 업데이트**: 새 기능 추가 시 