"""
데이터 처리 관련 공통 유틸리티 함수들
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import chardet

def detect_encoding(file_path: str) -> str:
    """
    파일의 인코딩을 자동 감지합니다.
    
    Args:
        file_path: 파일 경로
        
    Returns:
        str: 감지된 인코딩
    """
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read(10000)  # 처음 10KB만 읽어서 인코딩 추정
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            
            # 한국어 파일에서 자주 사용되는 인코딩 우선 순위 적용
            if encoding.lower() in ['euc-kr', 'cp949']:
                return 'cp949'
            elif encoding.lower() in ['utf-8', 'utf-8-sig']:
                return 'utf-8'
            else:
                return encoding
    except Exception:
        return 'utf-8'

def try_read_csv_with_encodings(file_path: str, encodings: List[str] = None) -> pd.DataFrame:
    """
    여러 인코딩을 시도해서 CSV 파일을 읽습니다.
    
    Args:
        file_path: CSV 파일 경로
        encodings: 시도할 인코딩 목록 (기본값: ['utf-8', 'cp949', 'latin-1'])
        
    Returns:
        pd.DataFrame: 읽어온 데이터프레임
        
    Raises:
        Exception: 모든 인코딩으로 읽기 실패한 경우
    """
    if encodings is None:
        encodings = ['utf-8', 'cp949', 'latin-1']
    
    # 자동 인코딩 감지 결과를 첫 번째로 시도
    detected_encoding = detect_encoding(file_path)
    if detected_encoding not in encodings:
        encodings.insert(0, detected_encoding)
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            # 인코딩 외의 다른 오류는 즉시 발생
            raise e
    
    raise Exception(f"지원하는 인코딩({', '.join(encodings)})으로 파일을 읽을 수 없습니다.")

def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    데이터프레임의 유효성을 검사합니다.
    
    Args:
        df: 검사할 데이터프레임
        
    Returns:
        Dict: 검사 결과
    """
    validation_result = {
        'is_valid': True,
        'warnings': [],
        'errors': [],
        'info': {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum()
        }
    }
    
    # 빈 데이터프레임 검사
    if df.empty:
        validation_result['errors'].append("데이터프레임이 비어있습니다.")
        validation_result['is_valid'] = False
        return validation_result
    
    # 중복 컬럼명 검사
    if len(df.columns) != len(set(df.columns)):
        duplicated_cols = df.columns[df.columns.duplicated()].tolist()
        validation_result['errors'].append(f"중복된 컬럼명이 있습니다: {duplicated_cols}")
        validation_result['is_valid'] = False
    
    # 대용량 데이터 경고
    if df.shape[0] > 10000:
        validation_result['warnings'].append(f"데이터가 많습니다 ({df.shape[0]:,}행). 처리 시간이 오래 걸릴 수 있습니다.")
    
    # 메모리 사용량 경고
    memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
    if memory_mb > 100:
        validation_result['warnings'].append(f"메모리 사용량이 큽니다 ({memory_mb:.1f} MB)")
    
    # 결측값 경고
    missing_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
    if missing_ratio > 0.1:
        validation_result['warnings'].append(f"결측값이 많습니다 ({missing_ratio:.1%})")
    
    return validation_result

def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    데이터프레임의 요약 정보를 생성합니다.
    
    Args:
        df: 요약할 데이터프레임
        
    Returns:
        Dict: 요약 정보
    """
    if df.empty:
        return {'error': '데이터가 없습니다.'}
    
    summary = {
        'basic_info': {
            'rows': df.shape[0],
            'columns': df.shape[1],
            'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB",
            'total_missing': df.isnull().sum().sum()
        },
        'column_info': {},
        'data_types': {
            'numeric': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical': df.select_dtypes(include=['object', 'category']).columns.tolist(),
            'datetime': df.select_dtypes(include=['datetime64']).columns.tolist()
        }
    }
    
    # 각 컬럼별 정보
    for col in df.columns:
        col_info = {
            'dtype': str(df[col].dtype),
            'missing': df[col].isnull().sum(),
            'unique': df[col].nunique()
        }
        
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info.update({
                'min': df[col].min(),
                'max': df[col].max(),
                'mean': df[col].mean(),
                'std': df[col].std()
            })
        elif pd.api.types.is_object_dtype(df[col]):
            value_counts = df[col].value_counts().head(5)
            col_info['top_values'] = value_counts.to_dict()
        
        summary['column_info'][col] = col_info
    
    return summary

def prepare_data_for_analysis(df: pd.DataFrame, 
                            target_column: str = None,
                            exclude_columns: List[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    분석을 위해 데이터를 전처리합니다.
    
    Args:
        df: 원본 데이터프레임
        target_column: 타겟 변수 (선택적)
        exclude_columns: 제외할 컬럼들 (선택적)
        
    Returns:
        Tuple[pd.DataFrame, Dict]: 전처리된 데이터프레임과 전처리 정보
    """
    if exclude_columns is None:
        exclude_columns = []
    
    processed_df = df.copy()
    processing_info = {
        'original_shape': df.shape,
        'excluded_columns': exclude_columns,
        'transformations': []
    }
    
    # 제외할 컬럼 제거
    if exclude_columns:
        processed_df = processed_df.drop(columns=exclude_columns, errors='ignore')
        processing_info['transformations'].append(f"제외된 컬럼: {exclude_columns}")
    
    # 완전히 비어있는 컬럼 제거
    empty_cols = processed_df.columns[processed_df.isnull().all()].tolist()
    if empty_cols:
        processed_df = processed_df.drop(columns=empty_cols)
        processing_info['transformations'].append(f"빈 컬럼 제거: {empty_cols}")
    
    # 단일 값만 가진 컬럼 제거 (상수 컬럼)
    constant_cols = []
    for col in processed_df.columns:
        if processed_df[col].nunique() <= 1:
            constant_cols.append(col)
    
    if constant_cols:
        processed_df = processed_df.drop(columns=constant_cols)
        processing_info['transformations'].append(f"상수 컬럼 제거: {constant_cols}")
    
    processing_info['final_shape'] = processed_df.shape
    
    return processed_df, processing_info

def convert_data_types(df: pd.DataFrame, type_hints: Dict[str, str] = None) -> pd.DataFrame:
    """
    데이터 타입을 자동으로 최적화하거나 힌트에 따라 변환합니다.
    
    Args:
        df: 변환할 데이터프레임
        type_hints: 컬럼별 타입 힌트 {'column_name': 'dtype'}
        
    Returns:
        pd.DataFrame: 타입이 변환된 데이터프레임
    """
    converted_df = df.copy()
    
    # 타입 힌트가 있는 경우 우선 적용
    if type_hints:
        for col, dtype in type_hints.items():
            if col in converted_df.columns:
                try:
                    if dtype == 'category':
                        converted_df[col] = converted_df[col].astype('category')
                    elif dtype == 'datetime':
                        converted_df[col] = pd.to_datetime(converted_df[col])
                    else:
                        converted_df[col] = converted_df[col].astype(dtype)
                except Exception:
                    pass  # 변환 실패 시 원본 유지
    
    # 자동 타입 최적화
    for col in converted_df.columns:
        if converted_df[col].dtype == 'object':
            # 숫자로 변환 가능한지 확인
            try:
                numeric_series = pd.to_numeric(converted_df[col], errors='coerce')
                if not numeric_series.isnull().all():
                    converted_df[col] = numeric_series
            except Exception:
                pass
        
        # 정수형 최적화
        if converted_df[col].dtype in ['int64', 'int32']:
            if converted_df[col].min() >= 0:
                if converted_df[col].max() < 256:
                    converted_df[col] = converted_df[col].astype('uint8')
                elif converted_df[col].max() < 65536:
                    converted_df[col] = converted_df[col].astype('uint16')
                elif converted_df[col].max() < 4294967296:
                    converted_df[col] = converted_df[col].astype('uint32')
        
        # 실수형 최적화
        if converted_df[col].dtype == 'float64':
            if converted_df[col].min() >= np.finfo(np.float32).min and \
               converted_df[col].max() <= np.finfo(np.float32).max:
                converted_df[col] = converted_df[col].astype('float32')
    
    return converted_df

def check_analysis_requirements(df: pd.DataFrame, 
                               analysis_type: str) -> Dict[str, Any]:
    """
    특정 분석에 필요한 데이터 요구사항을 검사합니다.
    
    Args:
        df: 검사할 데이터프레임
        analysis_type: 분석 유형 ('correlation', 'anova', 'regression' 등)
        
    Returns:
        Dict: 요구사항 검사 결과
    """
    result = {
        'is_suitable': True,
        'warnings': [],
        'errors': [],
        'recommendations': []
    }
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    
    if analysis_type.lower() == 'correlation':
        if len(numeric_cols) < 2:
            result['errors'].append("상관분석에는 최소 2개의 숫자형 변수가 필요합니다.")
            result['is_suitable'] = False
        elif len(numeric_cols) < 3:
            result['warnings'].append("변수가 적어 상관분석 결과가 제한적일 수 있습니다.")
    
    elif analysis_type.lower() == 'anova':
        if len(categorical_cols) == 0:
            result['errors'].append("ANOVA 분석에는 최소 1개의 범주형 변수가 필요합니다.")
            result['is_suitable'] = False
        if len(numeric_cols) == 0:
            result['errors'].append("ANOVA 분석에는 최소 1개의 숫자형 종속변수가 필요합니다.")
            result['is_suitable'] = False
    
    elif analysis_type.lower() == 'regression':
        if len(numeric_cols) < 2:
            result['errors'].append("회귀분석에는 최소 2개의 숫자형 변수가 필요합니다.")
            result['is_suitable'] = False
        elif len(numeric_cols) == 2:
            result['warnings'].append("단순회귀분석만 가능합니다.")
    
    # 일반적인 데이터 품질 검사
    if df.isnull().sum().sum() > 0:
        result['warnings'].append("결측값이 있습니다. 분석 전에 처리를 고려해보세요.")
    
    if df.duplicated().sum() > 0:
        result['warnings'].append("중복 행이 있습니다.")
    
    return result 