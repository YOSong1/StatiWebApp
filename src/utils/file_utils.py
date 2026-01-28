"""
파일 I/O 관련 공통 유틸리티 함수들
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

def ensure_directory_exists(file_path: str) -> None:
    """
    파일 경로의 디렉토리가 존재하지 않으면 생성합니다.
    
    Args:
        file_path: 파일 경로
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def get_safe_filename(filename: str, max_length: int = 255) -> str:
    """
    안전한 파일명을 생성합니다 (특수문자 제거, 길이 제한).
    
    Args:
        filename: 원본 파일명
        max_length: 최대 길이
        
    Returns:
        str: 안전한 파일명
    """
    # 윈도우에서 사용할 수 없는 문자들 제거
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')
    
    # 길이 제한
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:max_length - len(ext)] + ext
    
    return safe_name

def get_unique_filename(file_path: str) -> str:
    """
    중복되지 않는 파일명을 생성합니다.
    
    Args:
        file_path: 원본 파일 경로
        
    Returns:
        str: 중복되지 않는 파일 경로
    """
    if not os.path.exists(file_path):
        return file_path
    
    path = Path(file_path)
    counter = 1
    
    while True:
        new_name = f"{path.stem}_{counter}{path.suffix}"
        new_path = path.parent / new_name
        
        if not new_path.exists():
            return str(new_path)
        
        counter += 1
        
        # 무한 루프 방지
        if counter > 9999:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{path.stem}_{timestamp}{path.suffix}"
            return str(path.parent / new_name)

def backup_file(file_path: str, backup_dir: str = None) -> Optional[str]:
    """
    파일을 백업합니다.
    
    Args:
        file_path: 백업할 파일 경로
        backup_dir: 백업 디렉토리 (None이면 원본 파일과 같은 디렉토리)
        
    Returns:
        Optional[str]: 백업 파일 경로 (실패시 None)
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        path = Path(file_path)
        
        if backup_dir is None:
            backup_dir = path.parent
        else:
            backup_dir = Path(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_backup_{timestamp}{path.suffix}"
        backup_path = backup_dir / backup_name
        
        # 파일 복사
        import shutil
        shutil.copy2(file_path, backup_path)
        
        return str(backup_path)
    
    except Exception:
        return None

def load_json_file(file_path: str, default: Any = None) -> Any:
    """
    JSON 파일을 안전하게 로드합니다.
    
    Args:
        file_path: JSON 파일 경로
        default: 로드 실패시 반환할 기본값
        
    Returns:
        Any: 로드된 데이터 또는 기본값
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def save_json_file(data: Any, file_path: str, 
                   indent: int = 2, ensure_ascii: bool = False) -> bool:
    """
    데이터를 JSON 파일로 안전하게 저장합니다.
    
    Args:
        data: 저장할 데이터
        file_path: 저장할 파일 경로
        indent: 들여쓰기 레벨
        ensure_ascii: ASCII 강제 여부
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        ensure_directory_exists(file_path)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, 
                     default=str)  # datetime 등을 문자열로 변환
        return True
    except Exception:
        return False

def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    파일의 정보를 가져옵니다.
    
    Args:
        file_path: 파일 경로
        
    Returns:
        Dict: 파일 정보
    """
    if not os.path.exists(file_path):
        return {'exists': False}
    
    try:
        stat = os.stat(file_path)
        path = Path(file_path)
        
        return {
            'exists': True,
            'name': path.name,
            'size': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'extension': path.suffix.lower(),
            'is_file': path.is_file(),
            'is_dir': path.is_dir()
        }
    except Exception as e:
        return {'exists': True, 'error': str(e)}

def find_files_by_extension(directory: str, extensions: List[str], 
                           recursive: bool = True) -> List[str]:
    """
    특정 확장자의 파일들을 찾습니다.
    
    Args:
        directory: 검색할 디렉토리
        extensions: 확장자 리스트 (예: ['.csv', '.xlsx'])
        recursive: 하위 디렉토리 포함 여부
        
    Returns:
        List[str]: 찾은 파일 경로 리스트
    """
    if not os.path.exists(directory):
        return []
    
    found_files = []
    extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                 for ext in extensions]
    
    try:
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        found_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path) and \
                   any(file.lower().endswith(ext) for ext in extensions):
                    found_files.append(file_path)
    except Exception:
        pass
    
    return sorted(found_files)

def get_csv_info(file_path: str) -> Dict[str, Any]:
    """
    CSV 파일의 기본 정보를 가져옵니다 (데이터를 모두 로드하지 않음).
    
    Args:
        file_path: CSV 파일 경로
        
    Returns:
        Dict: CSV 파일 정보
    """
    from utils.data_utils import detect_encoding
    
    info = get_file_info(file_path)
    if not info.get('exists', False):
        return info
    
    try:
        # 인코딩 감지
        encoding = detect_encoding(file_path)
        info['encoding'] = encoding
        
        # 첫 몇 줄만 읽어서 기본 정보 파악
        sample_df = pd.read_csv(file_path, encoding=encoding, nrows=5)
        
        # 전체 행 수 추정 (파일 크기 기반)
        with open(file_path, 'r', encoding=encoding) as f:
            first_line = f.readline()
            sample_lines = [f.readline() for _ in range(10) if f.readline()]
            avg_line_length = sum(len(line) for line in sample_lines) / len(sample_lines)
        
        estimated_rows = int(info['size'] / avg_line_length) if avg_line_length > 0 else 0
        
        info.update({
            'columns': sample_df.columns.tolist(),
            'column_count': len(sample_df.columns),
            'estimated_rows': estimated_rows,
            'dtypes': sample_df.dtypes.to_dict(),
            'sample_data': sample_df.head(3).to_dict('records')
        })
        
    except Exception as e:
        info['error'] = str(e)
    
    return info

def export_dataframe(df: pd.DataFrame, file_path: str, 
                    file_format: str = None) -> Tuple[bool, str]:
    """
    데이터프레임을 파일로 내보냅니다.
    
    Args:
        df: 내보낼 데이터프레임
        file_path: 저장할 파일 경로
        file_format: 파일 형식 (None이면 확장자로 자동 판단)
        
    Returns:
        Tuple[bool, str]: (성공 여부, 메시지)
    """
    try:
        ensure_directory_exists(file_path)
        
        if file_format is None:
            file_format = Path(file_path).suffix.lower()
        
        if file_format in ['.csv']:
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
        elif file_format in ['.xlsx', '.xls']:
            df.to_excel(file_path, index=False)
        elif file_format in ['.json']:
            df.to_json(file_path, orient='records', indent=2, force_ascii=False)
        elif file_format in ['.parquet']:
            df.to_parquet(file_path, index=False)
        else:
            return False, f"지원하지 않는 파일 형식입니다: {file_format}"
        
        return True, f"파일이 성공적으로 저장되었습니다: {file_path}"
    
    except Exception as e:
        return False, f"파일 저장 중 오류가 발생했습니다: {str(e)}"

def clean_temp_files(temp_dir: str, max_age_hours: int = 24) -> int:
    """
    임시 파일들을 정리합니다.
    
    Args:
        temp_dir: 임시 디렉토리 경로
        max_age_hours: 최대 보관 시간 (시간)
        
    Returns:
        int: 삭제된 파일 수
    """
    if not os.path.exists(temp_dir):
        return 0
    
    deleted_count = 0
    current_time = datetime.now()
    
    try:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    hours_old = (current_time - file_time).total_seconds() / 3600
                    
                    if hours_old > max_age_hours:
                        os.remove(file_path)
                        deleted_count += 1
                except Exception:
                    continue
    except Exception:
        pass
    
    return deleted_count

def validate_file_path(file_path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """
    파일 경로의 유효성을 검사합니다.
    
    Args:
        file_path: 검사할 파일 경로
        must_exist: 파일이 존재해야 하는지 여부
        
    Returns:
        Tuple[bool, str]: (유효 여부, 메시지)
    """
    if not file_path or not file_path.strip():
        return False, "파일 경로가 비어있습니다."
    
    try:
        path = Path(file_path)
        
        # 경로 길이 검사 (Windows 기준)
        if len(str(path)) > 260:
            return False, "파일 경로가 너무 깁니다."
        
        # 파일명 검사
        if path.name:
            invalid_chars = '<>:"/\\|?*'
            if any(char in path.name for char in invalid_chars):
                return False, f"파일명에 사용할 수 없는 문자가 포함되어 있습니다: {invalid_chars}"
        
        # 존재 여부 검사
        if must_exist and not path.exists():
            return False, "파일이 존재하지 않습니다."
        
        # 디렉토리 쓰기 권한 검사 (새 파일 생성 시)
        if not must_exist:
            parent_dir = path.parent
            if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
                return False, "디렉토리에 쓰기 권한이 없습니다."
        
        return True, "유효한 파일 경로입니다."
    
    except Exception as e:
        return False, f"파일 경로 검사 중 오류: {str(e)}" 