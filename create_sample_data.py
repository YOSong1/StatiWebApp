import pandas as pd
import numpy as np
import os

# data 디렉토리 생성
os.makedirs('data', exist_ok=True)

# 기초 통계 및 상관분석용 샘플 데이터 생성
np.random.seed(42)

# 키와 몸무게 간 상관관계가 있는 데이터 생성
height = np.random.normal(170, 10, 50)
weight = height * 0.8 + np.random.normal(0, 5, 50)
age = np.random.randint(20, 60, 50)
score = np.random.normal(85, 15, 50)
temperature = np.random.normal(23, 3, 50)

data = {
    'Height': np.round(height, 1),
    'Weight': np.round(weight, 1),
    'Age': age,
    'Score': np.round(score, 1),
    'Temperature': np.round(temperature, 1)
}

df = pd.DataFrame(data)
df.to_excel('data/basic_statistics_sample.xlsx', index=False)
print('기초 통계 샘플 데이터가 생성되었습니다.')

# 범주형 데이터가 포함된 분산분석용 샘플 데이터도 확인
try:
    existing_file = pd.read_excel('data/factorial_2x3_design_categorical.xlsx')
    print('분산분석 샘플 데이터가 이미 존재합니다.')
except:
    print('분산분석 샘플 데이터를 생성합니다.')
    # 2x3 요인설계 데이터 생성
    groups_a = ['A1', 'A2'] * 12  # 24개
    groups_b = ['B1', 'B2', 'B3'] * 8  # 24개
    values = np.random.normal(50, 10, 24)
    
    # 그룹별 효과 추가
    for i, (a, b) in enumerate(zip(groups_a, groups_b)):
        if a == 'A2':
            values[i] += 5
        if b == 'B2':
            values[i] += 3
        elif b == 'B3':
            values[i] += 7
    
    factorial_data = {
        'Group_A': groups_a,
        'Group_B': groups_b,
        'Value': np.round(values, 2),
        'ID': range(1, 25)
    }
    
    factorial_df = pd.DataFrame(factorial_data)
    factorial_df.to_excel('data/factorial_2x3_design_categorical.xlsx', index=False)
    print('분산분석 샘플 데이터가 생성되었습니다.') 