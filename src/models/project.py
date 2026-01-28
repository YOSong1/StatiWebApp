from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

@dataclass
class Project:
    """
    애플리케이션의 단일 프로젝트 상태를 관리하는 데이터 클래스
    """
    name: str = "새 프로젝트"
    file_path: Optional[str] = None
    is_dirty: bool = False  # 변경 여부
    created_at: datetime = field(default_factory=datetime.now)
    
    # 데이터
    dataframe: Optional[pd.DataFrame] = None
    data_description: str = ""
    
    # 분석 및 차트 히스토리
    analysis_history: List[Dict[str, Any]] = field(default_factory=list)
    chart_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 애플리케이션 설정
    settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # DataFrame이 None일 때 빈 DataFrame으로 초기화
        if self.dataframe is None:
            self.dataframe = pd.DataFrame()

    def update_data(self, df: pd.DataFrame, description: str):
        """데이터프레임과 설명을 업데이트합니다."""
        self.dataframe = df
        self.data_description = description
        self.is_dirty = True

    def add_analysis(self, result: Dict[str, Any]):
        """분석 결과를 히스토리에 추가합니다."""
        self.analysis_history.append(result)
        self.is_dirty = True

    def add_chart(self, chart_info: Dict[str, Any]):
        """차트 정보를 히스토리에 추가합니다."""
        self.chart_history.append(chart_info)
        self.is_dirty = True

    def to_dict(self) -> Dict[str, Any]:
        """프로젝트 데이터를 파일 저장을 위해 dict로 변환합니다."""
        data_dict = None
        if self.dataframe is not None and not self.dataframe.empty:
            data_dict = {
                'dataframe': self.dataframe.to_dict('records'),
                'columns': list(self.dataframe.columns),
                'description': self.data_description
            }

        return {
            'project_info': {
                'name': self.name,
                'created_at': self.created_at.isoformat()
            },
            'data': data_dict,
            'analysis_history': _serialize(self.analysis_history),
            'chart_history': _serialize(self.chart_history),
            'settings': _serialize(self.settings)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """dict로부터 프로젝트 데이터를 복원합니다."""
        project_info = data.get('project_info', {})
        
        df = None
        data_info = data.get('data')
        if data_info and 'dataframe' in data_info:
            df = pd.DataFrame(data_info['dataframe'])
            if 'columns' in data_info:
                df.columns = data_info['columns']

        return cls(
            name=project_info.get('name', '제목 없는 프로젝트'),
            created_at=datetime.fromisoformat(project_info.get('created_at', datetime.now().isoformat())),
            dataframe=df,
            data_description=data_info.get('description', '') if data_info else '',
            analysis_history=_deserialize(data.get('analysis_history', [])),
            chart_history=_deserialize(data.get('chart_history', [])),
            settings=_deserialize(data.get('settings', {}))
        )

# 직렬화/역직렬화 헬퍼 ---------------------------------------------
def _serialize(obj):
    """JSON 직렬화를 위한 보조 함수"""
    if isinstance(obj, pd.DataFrame):
        return {
            "__type__": "DataFrame",
            "columns": list(obj.columns),
            "index": list(obj.index),
            "data": obj.to_dict("records"),
        }
    if isinstance(obj, pd.Series):
        return {
            "__type__": "Series",
            "index": list(obj.index),
            "data": obj.to_dict(),
        }
    if isinstance(obj, list):
        return [_serialize(o) for o in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def _deserialize(obj):
    """JSON 역직렬화를 위한 보조 함수"""
    if isinstance(obj, dict) and "__type__" in obj:
        if obj["__type__"] == "DataFrame":
            df = pd.DataFrame(obj.get("data", []))
            if "columns" in obj:
                df = df[obj["columns"]]
            if "index" in obj:
                df.index = obj["index"]
            return df
        if obj["__type__"] == "Series":
            return pd.Series(obj.get("data", {}), index=obj.get("index", None))
    if isinstance(obj, list):
        return [_deserialize(o) for o in obj]
    if isinstance(obj, dict):
        return {k: _deserialize(v) for k, v in obj.items()}
    return obj
