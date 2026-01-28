import pandas as pd
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox

class DataEditController:
    def __init__(self, model):
        self.model = model  # pandas DataFrame 등
class DataTransformController:
    def __init__(self, model):
        self.model = model  # pandas DataFrame 등

    def change_column_type(self, col_name, dtype):
        """변수(열) 타입 변경"""
        self.model[col_name] = self.model[col_name].astype(dtype)

    def fill_missing(self, col_name, method='mean'):
        """결측치 처리 (평균/중앙값/삭제 등)"""
        if method == 'mean':
            value = self.model[col_name].mean()
            self.model[col_name] = self.model[col_name].fillna(value)
        elif method == 'median':
            value = self.model[col_name].median()
            self.model[col_name] = self.model[col_name].fillna(value)
        elif method == 'delete':
            self.model = self.model.dropna(subset=[col_name]).reset_index(drop=True)

    def standardize(self, col_name):
        """표준화 (z-score)"""
        s = self.model[col_name]
        self.model[col_name] = (s - s.mean()) / s.std()

    def normalize(self, col_name):
        """정규화 (0~1)"""
        s = self.model[col_name]
        self.model[col_name] = (s - s.min()) / (s.max() - s.min())

    def create_derived_column(self, new_col, formula):
        """파생 변수 생성 (수식: 'A + B * 2' 등)"""
        self.model[new_col] = self.model.eval(formula)

    def edit_cell(self, row, col, value):
        """특정 셀 값 수정"""
        self.model.iat[row, col] = value

    def add_row(self, data=None):
        """행 추가 (data: dict 또는 None)"""
        import pandas as pd
        if data is None:
            data = {col: None for col in self.model.columns}
        self.model = pd.concat([self.model, pd.DataFrame([data])], ignore_index=True)

    def delete_row(self, row):
        """행 삭제"""
        self.model = self.model.drop(index=row).reset_index(drop=True)

    def add_column(self, col_name, default=None):
        """열 추가"""
        self.model[col_name] = default

    def delete_column(self, col_name):
        """열 삭제"""
        self.model = self.model.drop(columns=[col_name])

    def copy_selection(self, rows, cols):
        """선택 영역 복사 (리스트 반환)"""
        return self.model.iloc[rows, cols].values.tolist()

    def paste_selection(self, start_row, start_col, data):
        """선택 영역 붙여넣기 (data: 2차원 리스트)"""
        for i, row_data in enumerate(data):
            for j, value in enumerate(row_data):
                self.model.iat[start_row + i, start_col + j] = value
from models.project import Project

class DataController(QObject):
    """
    데이터 가져오기, 내보내기, 유효성 검증 등을 담당하는 컨트롤러
    """
    # 시그널 정의
    data_imported = Signal(pd.DataFrame, str)  # DataFrame, 설명
    data_exported = Signal(str)  # 파일 경로
    status_updated = Signal(str)
    error_occurred = Signal(str, str)  # 제목, 메시지

    def __init__(self, parent=None):
        super().__init__(parent)
        self.supported_import_formats = {
            "Excel files (*.xlsx *.xls)": [".xlsx", ".xls"],
            "CSV files (*.csv)": [".csv"],
            "All supported files": [".csv", ".xlsx", ".xls"]
        }
        self.supported_export_formats = {
            "Excel files (*.xlsx)": ".xlsx",
            "CSV files (*.csv)": ".csv"
        }

    @Slot()
    def import_data(self):
        """파일 대화상자를 열어 데이터를 가져옵니다."""
        filter_str = ";;".join(self.supported_import_formats.keys())
        file_path, selected_filter = QFileDialog.getOpenFileName(
            self.parent(), "데이터 가져오기", "", filter_str
        )
        
        if not file_path:
            return

        try:
            self.status_updated.emit("데이터를 불러오는 중...")
            df = self._load_dataframe(file_path)
            
            # 데이터 유효성 검증
            if not self._validate_dataframe(df):
                return
            
            description = Path(file_path).name
            self.data_imported.emit(df, description)
            self.status_updated.emit(f"데이터 '{description}'를 성공적으로 불러왔습니다.")
            
        except Exception as e:
            self.error_occurred.emit("데이터 가져오기 실패", 
                                   f"파일을 불러오는 중 오류가 발생했습니다:\n{str(e)}")

    @Slot(pd.DataFrame)
    def export_data(self, dataframe: pd.DataFrame):
        """데이터프레임을 파일로 내보냅니다."""
        if dataframe is None or dataframe.empty:
            self.error_occurred.emit("내보내기 오류", "내보낼 데이터가 없습니다.")
            return

        filter_str = ";;".join(self.supported_export_formats.keys())
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self.parent(), "데이터 내보내기", "", filter_str
        )
        
        if not file_path:
            return

        try:
            self.status_updated.emit("데이터를 저장하는 중...")
            
            # 선택된 필터에 따라 확장자 추가
            for format_name, extension in self.supported_export_formats.items():
                if format_name in selected_filter:
                    if not file_path.endswith(extension):
                        file_path += extension
                    break
            
            self._save_dataframe(dataframe, file_path)
            self.data_exported.emit(file_path)
            self.status_updated.emit(f"데이터를 '{file_path}'에 성공적으로 저장했습니다.")
            
        except Exception as e:
            self.error_occurred.emit("데이터 내보내기 실패", 
                                   f"파일을 저장하는 중 오류가 발생했습니다:\n{str(e)}")

    def _load_dataframe(self, file_path: str) -> pd.DataFrame:
        """파일 경로에서 DataFrame을 로드합니다."""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.csv':
            # CSV 인코딩 자동 감지
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='cp949')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin-1')
        
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_extension}")
        
        return df

    def _save_dataframe(self, df: pd.DataFrame, file_path: str):
        """DataFrame을 파일로 저장합니다."""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.csv':
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
        elif file_extension == '.xlsx':
            df.to_excel(file_path, index=False)
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_extension}")

    def _validate_dataframe(self, df: pd.DataFrame) -> bool:
        """DataFrame의 유효성을 검증합니다."""
        if df is None:
            self.error_occurred.emit("데이터 오류", "데이터를 읽을 수 없습니다.")
            return False
        
        if df.empty:
            self.error_occurred.emit("데이터 오류", "파일에 데이터가 없습니다.")
            return False
        
        # 열 이름 중복 검사
        if df.columns.duplicated().any():
            self.error_occurred.emit("데이터 오류", 
                                   "중복된 열 이름이 있습니다. 데이터를 확인해주세요.")
            return False
        
        # 데이터 크기 검사 (메모리 사용량 고려)
        if len(df) > 1000000:  # 100만 행 초과
            reply = QMessageBox.question(
                self.parent(),
                "대용량 데이터",
                f"데이터가 매우 큽니다 ({len(df):,}행, {len(df.columns)}열).\n"
                "불러오기를 계속하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return False
        
        return True

    def get_data_summary(self, df: pd.DataFrame) -> str:
        """DataFrame의 요약 정보를 생성합니다."""
        if df is None or df.empty:
            return "데이터가 없습니다."
        
        summary_parts = [
            f"행 수: {len(df):,}",
            f"열 수: {len(df.columns)}",
            f"메모리 사용량: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB"
        ]
        
        # 데이터 타입별 열 수
        numeric_cols = df.select_dtypes(include=['number']).columns
        text_cols = df.select_dtypes(include=['object']).columns
        datetime_cols = df.select_dtypes(include=['datetime']).columns
        
        if len(numeric_cols) > 0:
            summary_parts.append(f"숫자형 열: {len(numeric_cols)}개")
        if len(text_cols) > 0:
            summary_parts.append(f"텍스트 열: {len(text_cols)}개")
        if len(datetime_cols) > 0:
            summary_parts.append(f"날짜/시간 열: {len(datetime_cols)}개")
        
        # 결측값 정보
        missing_count = df.isnull().sum().sum()
        if missing_count > 0:
            summary_parts.append(f"결측값: {missing_count:,}개")
        
        return " | ".join(summary_parts)

    @Slot(pd.DataFrame)
    def validate_data_for_analysis(self, df: pd.DataFrame) -> bool:
        """분석에 적합한 데이터인지 검증합니다."""
        if df is None or df.empty:
            self.error_occurred.emit("분석 오류", "분석할 데이터가 없습니다.")
            return False
        
        # 최소 행 수 검사
        if len(df) < 3:
            self.error_occurred.emit("분석 오류", 
                                   "분석에는 최소 3행 이상의 데이터가 필요합니다.")
            return False
        
        # 숫자형 데이터 존재 검사
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            self.error_occurred.emit("분석 오류", 
                                   "분석에 필요한 숫자형 데이터가 없습니다.")
            return False
        
        return True 
