"""
데이터 테이블 뷰
PySide6 기반으로 DataFrame과 QTableWidget을 동기화한다.
"""

from pathlib import Path
from typing import Optional, List

import pandas as pd
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
    QMenu,
    QInputDialog,
    QAbstractItemView,
    QApplication,
)
from PySide6.QtGui import QAction, QKeyEvent
from PySide6.QtWidgets import QStyledItemDelegate, QAbstractItemDelegate


class DataTableDelegate(QStyledItemDelegate):
    """셀 편집 중 좌우 방향키로 셀 이동/커밋 처리"""

    def __init__(self, table, parent=None):
        super().__init__(parent)
        self.table = table

    def eventFilter(self, editor, event):
        if isinstance(event, QKeyEvent) and event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Left, Qt.Key_Right):
                # 편집중 값 커밋 후 셀 이동
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)
                idx = self.table.currentIndex()
                if idx.isValid():
                    row = idx.row()
                    col = idx.column()
                    next_col = col - 1 if key == Qt.Key_Left else col + 1
                    next_col = max(0, min(next_col, self.table.columnCount() - 1))
                    self.table.setCurrentCell(row, next_col)
                return True
        return super().eventFilter(editor, event)


class DataTableView(QWidget):
    data_changed = Signal()
    selection_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.df: Optional[pd.DataFrame] = None
        self._df_full: Optional[pd.DataFrame] = None  # 숨긴 열을 포함한 전체 데이터
        self.hidden_columns: List[str] = []
        self._updating = False  # 내부 업데이트 루프 방지용 플래그
        self._build_ui()
        self._connect_signals()

    # UI ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.info_label = QLabel("데이터 없음")
        toolbar.addWidget(self.info_label)
        toolbar.addStretch()

        self.add_row_btn = QPushButton("행 추가")
        self.insert_row_btn = QPushButton("행 삽입")
        self.add_col_btn = QPushButton("열 추가")
        self.del_row_btn = QPushButton("행 삭제")
        self.del_col_btn = QPushButton("열 삭제")

        for btn in (
            self.add_row_btn,
            self.insert_row_btn,
            self.add_col_btn,
            self.del_row_btn,
            self.del_col_btn,
        ):
            toolbar.addWidget(btn)

        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        # 셀 단위 선택, 헤더 클릭 시 행/열 전체 선택
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # 편집 중 좌우 이동 커밋 지원 델리게이트
        self.table.setItemDelegate(DataTableDelegate(self.table, self))
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_body_menu)
        self.table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.horizontalHeader().customContextMenuRequested.connect(self._show_header_menu)
        # 균등한 기본 폭, 마지막 열 과도한 확장 방지
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(True)
        layout.addWidget(self.table)

        self._update_ui_state()

    def _connect_signals(self):
        self.add_row_btn.clicked.connect(self.add_row)
        self.insert_row_btn.clicked.connect(self.insert_row)
        self.add_col_btn.clicked.connect(self.add_column)
        self.del_row_btn.clicked.connect(self.delete_row)
        self.del_col_btn.clicked.connect(self.delete_column)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        # 키 이벤트 필터 등록 (Enter로 다음 행 이동 등)
        self.table.installEventFilter(self)
        # 헤더 클릭 시 행/열 선택
        self.table.verticalHeader().sectionClicked.connect(self.table.selectRow)
        self.table.horizontalHeader().sectionClicked.connect(self.table.selectColumn)

    # 데이터 연동 -----------------------------------------------------------
    def set_data(self, df: Optional[pd.DataFrame]):
        if df is None:
            self.clear_data()
            return
        self._df_full = df.copy()
        self.hidden_columns = []
        self._apply_hidden_columns()
        self.data_changed.emit()

    def get_data(self) -> Optional[pd.DataFrame]:
        if self.df is None:
            return None
        return self.df.copy()

    def clear_data(self):
        self.df = None
        self._df_full = None
        self.hidden_columns = []
        self._updating = True
        try:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
        finally:
            self._updating = False
        self._update_ui_state()
        self.data_changed.emit()

    def has_data(self) -> bool:
        return self.df is not None and not self.df.empty

    def read_dataframe_from_file(self, file_path: str) -> pd.DataFrame:
        """외부 파일을 DataFrame으로 읽어 반환."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        if path.suffix.lower() in {".xlsx", ".xls"}:
            df = pd.read_excel(path)
        elif path.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding="cp949")
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {path.suffix}")

        if df.empty:
            raise ValueError("파일에 데이터가 없습니다.")
        return df

    def load_data_from_file(self, file_path: str):
        """파일에서 DataFrame을 로드하여 설정."""
        df = self.read_dataframe_from_file(file_path)
        self.set_data(df)

    def save_data_to_file(self, file_path: str):
        if not self.has_data():
            raise ValueError("저장할 데이터가 없습니다.")

        self._update_dataframe_from_table()
        path = Path(file_path)

        if path.suffix.lower() == ".xlsx":
            self.df.to_excel(path, index=False)
        elif path.suffix.lower() == ".csv":
            self.df.to_csv(path, index=False, encoding="utf-8-sig")
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {path.suffix}")

    def append_data(self, df: pd.DataFrame):
        """
        기존 데이터에 행을 추가.
        컬럼이 모두 일치해야 하며, 없으면 그대로 설정.
        """
        if df is None or df.empty:
            return
        if self.df is None:
            self.set_data(df)
            return
        if list(self.df.columns) != list(df.columns):
            raise ValueError("컬럼 구성이 일치하지 않아 병합할 수 없습니다.")
        self.df = pd.concat([self.df, df], ignore_index=True)
        self._update_table_from_dataframe()
        self.data_changed.emit()

    # 테이블 <-> DataFrame -------------------------------------------------
    def _update_table_from_dataframe(self):
        if self.df is None:
            return

        self._updating = True
        try:
            self.table.setRowCount(len(self.df))
            self.table.setColumnCount(len(self.df.columns))
            self.table.setHorizontalHeaderLabels([str(c) for c in self.df.columns])

            for i, (_, row) in enumerate(self.df.iterrows()):
                for j, value in enumerate(row):
                    text = "" if pd.isna(value) else str(value)
                    self.table.setItem(i, j, QTableWidgetItem(text))
        finally:
            self._updating = False

        self._update_ui_state()
        # 열 폭 균등/제한 적용
        self._adjust_column_widths()

    def _apply_hidden_columns(self):
        """숨긴 열을 제외한 뷰를 갱신"""
        if self._df_full is None:
            self.df = None
        else:
            visible_cols = [c for c in self._df_full.columns if c not in self.hidden_columns]
            self.df = self._df_full[visible_cols].copy()
        self._update_table_from_dataframe()

    # 이벤트 필터: Enter 키로 다음 행 이동
    def eventFilter(self, obj, event):
        if obj in (self.table, self.table.viewport()) and event.type() == QEvent.KeyPress:
            key = event.key()

            # 편집 중이면 이동 전에 커밋 시도
            def _commit_current():
                if self.table.state() == QAbstractItemView.EditingState:
                    editor = QApplication.focusWidget()
                    if editor is not None:
                        self.table.closeEditor(editor, QAbstractItemDelegate.SubmitModelCache)
                # ???->??? ??
                self._update_dataframe_from_table()

            if key in (Qt.Key_Return, Qt.Key_Enter):
                current = self.table.currentIndex()
                if current.isValid():
                    _commit_current()
                    row = current.row()
                    col = current.column()
                    next_row = row + 1
                    # 마지막 행이면 새 행 추가
                    if next_row >= self.table.rowCount():
                        self.add_row()
                    self.table.setCurrentCell(next_row, col)
                    return True  # 기본 처리 막음

            if key in (Qt.Key_Left, Qt.Key_Right):
                current = self.table.currentIndex()
                if current.isValid():
                    _commit_current()
                    row = current.row()
                    col = current.column()
                    next_col = col - 1 if key == Qt.Key_Left else col + 1
                    next_col = max(0, min(next_col, self.table.columnCount() - 1))
                    self.table.setCurrentCell(row, next_col)
                    return True

        return super().eventFilter(obj, event)

    def _adjust_column_widths(self):
        """열 폭을 균등하게 하고 너무 넓지 않도록 제한"""
        header = self.table.horizontalHeader()
        default_width = 100
        max_width = 200
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
            width = max(default_width, self.table.sizeHintForColumn(col) + 10)
            width = min(width, max_width)
            header.resizeSection(col, width)

    def _update_dataframe_from_table(self):
        if self.table.rowCount() == 0 or self.table.columnCount() == 0:
            self.df = None
            self._df_full = None
            return

        headers = []
        for j in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(j)
            headers.append(header_item.text() if header_item else f"Column_{j+1}")

        data = []
        for i in range(self.table.rowCount()):
            row = []
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                value = item.text() if item else ""
                if value == "":
                    row.append(None)
                else:
                    # 숫자 변환 시도, 실패 시 문자열 유지
                    try:
                        row.append(int(value) if value.isdigit() else float(value))
                    except ValueError:
                        row.append(value)
            data.append(row)

        visible_df = pd.DataFrame(data, columns=headers)
        self.df = visible_df.copy()

        # 숨긴 열을 포함한 전체 데이터 업데이트
        if self._df_full is None:
            self._df_full = visible_df.copy()
        else:
            # 행 길이 맞추기
            if len(visible_df) > len(self._df_full):
                extra_rows = len(visible_df) - len(self._df_full)
                for col in self._df_full.columns:
                    self._df_full[col] = list(self._df_full[col]) + [None] * extra_rows
            elif len(visible_df) < len(self._df_full):
                self._df_full = self._df_full.iloc[: len(visible_df)].copy()

            for col in visible_df.columns:
                if col in self._df_full.columns:
                    self._df_full[col] = visible_df[col]
                else:
                    self._df_full[col] = visible_df[col]

    # 행/열 조작 -----------------------------------------------------------
    def add_row(self):
        if self.df is not None:
            new_row = {col: None for col in self.df.columns}
            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            self._update_table_from_dataframe()
        else:
            row = self.table.rowCount()
            self.table.insertRow(row)
        self._update_ui_state()
        self.data_changed.emit()

    def insert_row(self):
        target = self.table.currentRow()
        if target < 0:
            target = self.table.rowCount()
        if self.df is not None:
            empty = pd.DataFrame([{col: None for col in self.df.columns}])
            self.df = pd.concat(
                [self.df.iloc[:target], empty, self.df.iloc[target:]],
                ignore_index=True,
            )
            self._update_table_from_dataframe()
        else:
            self.table.insertRow(target)
        self._update_ui_state()
        self.data_changed.emit()

    def add_column(self):
        col_name, ok = QInputDialog.getText(
            self, "열 추가", "열 이름을 입력하세요:", text=f"Column_{self.table.columnCount()+1}"
        )
        if not ok or not col_name:
            return

        if self.df is not None:
            if col_name in self.df.columns:
                QMessageBox.warning(self, "경고", "같은 이름의 열이 이미 있습니다.")
                return
            self.df[col_name] = None
            self._update_table_from_dataframe()
        else:
            col_idx = self.table.columnCount()
            self.table.insertColumn(col_idx)
            self.table.setHorizontalHeaderItem(col_idx, QTableWidgetItem(col_name))
            for i in range(self.table.rowCount()):
                self.table.setItem(i, col_idx, QTableWidgetItem(""))
        self._update_ui_state()
        self.data_changed.emit()

    def delete_row(self):
        current = self.table.currentRow()
        if current < 0:
            return
        if self.df is not None and current < len(self.df):
            self.df = self.df.drop(self.df.index[current]).reset_index(drop=True)
            self._update_table_from_dataframe()
        else:
            self.table.removeRow(current)
        self._update_ui_state()
        self.data_changed.emit()

    def delete_column(self):
        current = self.table.currentColumn()
        if current < 0:
            return
        if self.df is not None and current < len(self.df.columns):
            col_name = self.df.columns[current]
            self.df = self.df.drop(columns=[col_name])
            self._update_table_from_dataframe()
        else:
            self.table.removeColumn(current)
        self._update_ui_state()
        self.data_changed.emit()

    # 컨텍스트 메뉴 --------------------------------------------------------
    def _show_body_menu(self, pos):
        if self.table.rowCount() == 0 and self.table.columnCount() == 0:
            return
        menu = QMenu(self)
        menu.addAction(QAction("행 추가", self, triggered=self.add_row))
        menu.addAction(QAction("행 삽입", self, triggered=self.insert_row))
        menu.addAction(QAction("열 추가", self, triggered=self.add_column))
        menu.addSeparator()
        menu.addAction(QAction("행 삭제", self, triggered=self.delete_row))
        menu.addAction(QAction("열 삭제", self, triggered=self.delete_column))
        menu.exec_(self.table.viewport().mapToGlobal(pos))

    def _show_header_menu(self, pos):
        section = self.table.horizontalHeader().logicalIndexAt(pos)
        if section < 0:
            return
        col_name = self.table.horizontalHeaderItem(section).text() if self.table.horizontalHeaderItem(section) else None
        menu = QMenu(self)
        change_type_action = QAction("열 타입 변경", self)
        change_type_action.triggered.connect(lambda: self._change_column_type(section, col_name))
        menu.addAction(change_type_action)

        hide_action = QAction("열 숨기기", self)
        hide_action.triggered.connect(lambda: self.hide_column_by_name(col_name))
        menu.addAction(hide_action)

        show_action = QAction("숨긴 열 복원", self)
        show_action.triggered.connect(self.restore_hidden_columns)
        menu.addAction(show_action)

        menu.exec_(self.table.horizontalHeader().mapToGlobal(pos))

    def _change_column_type(self, col_index: int, col_name: Optional[str]):
        if self.df is None or col_index < 0 or col_index >= len(self.df.columns):
            return
        types = ["int", "float", "str"]
        dtype, ok = QInputDialog.getItem(self, "열 타입 변경", "데이터 타입을 선택하세요:", types, 0, False)
        if not ok or not dtype:
            return
        target_col = col_name or self.df.columns[col_index]
        try:
            self.df[target_col] = self.df[target_col].astype(dtype)
            self._update_table_from_dataframe()
            self.data_changed.emit()
        except Exception as exc:
            QMessageBox.warning(self, "변환 실패", f"타입 변환에 실패했습니다:\n{exc}")

    def hide_column_by_name(self, col_name: Optional[str]):
        if not col_name or self._df_full is None:
            return
        if col_name not in self._df_full.columns:
            return
        if col_name not in self.hidden_columns:
            self.hidden_columns.append(col_name)
        self._apply_hidden_columns()
        self.data_changed.emit()

    def restore_hidden_columns(self):
        if not self.hidden_columns:
            QMessageBox.information(self, "알림", "숨긴 열이 없습니다.")
            return
        items = self.hidden_columns
        item, ok = QInputDialog.getItem(self, "숨긴 열 복원", "복원할 열을 선택하세요:", items, 0, False)
        if ok and item:
            self.hidden_columns = [c for c in self.hidden_columns if c != item]
            self._apply_hidden_columns()
            self.data_changed.emit()

        # 상태/선택 ------------------------------------------------------------
    def _update_ui_state(self):
        has_cells = self.table.rowCount() > 0 or self.table.columnCount() > 0
        self.del_row_btn.setEnabled(has_cells and self.table.currentRow() >= 0)
        self.del_col_btn.setEnabled(has_cells and self.table.currentColumn() >= 0)

        if self.df is not None:
            rows, cols = self.df.shape
            hidden = f" (숨김 {len(self.hidden_columns)}열)" if self.hidden_columns else ""
            self.info_label.setText(f"데이터 {rows}행 × {cols}열{hidden}")
        elif has_cells:
            rows, cols = self.table.rowCount(), self.table.columnCount()
            self.info_label.setText(f"테이블 {rows}행 × {cols}열")
        else:
            self.info_label.setText("데이터 없음")

    def _on_item_changed(self, _item):
        if self._updating:
            return
        self._update_dataframe_from_table()
        self._update_ui_state()
        self.data_changed.emit()

    def _on_selection_changed(self):
        self._update_ui_state()
        self.selection_changed.emit()

    # 헬퍼 ----------------------------------------------------------------
    def get_selected_columns(self) -> List[str]:
        cols = []
        for item in self.table.selectedItems():
            header = self.table.horizontalHeaderItem(item.column())
            if header and header.text() not in cols:
                cols.append(header.text())
        return cols

    def get_selected_data(self) -> Optional[pd.DataFrame]:
        if self.df is None:
            return None
        ranges = self.table.selectedRanges()
        if not ranges:
            return None
        r = ranges[0]
        return self.df.iloc[r.topRow() : r.bottomRow() + 1, r.leftColumn() : r.rightColumn() + 1]

    def get_numeric_columns(self) -> List[str]:
        if self.df is None:
            return []
        return [c for c in self.df.columns if pd.api.types.is_numeric_dtype(self.df[c])]
