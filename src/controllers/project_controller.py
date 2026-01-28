import json
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox

from models.project import Project

class ProjectController(QObject):
    """
    프로젝트의 비즈니스 로직과 상태 관리를 담당하는 컨트롤러
    """
    # 시그널 정의
    project_loaded = Signal(Project)
    project_closed = Signal()
    status_updated = Signal(str)
    error_occurred = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_project: Project = None
        self.new_project()

    @Slot()
    def new_project(self):
        """새 프로젝트를 생성합니다."""
        if self.current_project and self.current_project.is_dirty:
            if not self._confirm_discard_changes():
                return
        
        self.current_project = Project()
        self.project_loaded.emit(self.current_project)
        self.status_updated.emit("새 프로젝트가 생성되었습니다.")

    @Slot()
    def open_project(self):
        """파일 대화상자를 열어 프로젝트 파일을 불러옵니다."""
        if self.current_project and self.current_project.is_dirty:
            if not self._confirm_discard_changes():
                return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent(), "프로젝트 열기", "", "DOE Project Files (*.doeproj);;All Files (*)"
        )
        
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_project = Project.from_dict(data)
            self.current_project.file_path = file_path
            self.current_project.is_dirty = False
            
            self.project_loaded.emit(self.current_project)
            self.status_updated.emit(f"프로젝트 '{Path(file_path).name}'를 불러왔습니다.")

        except Exception as e:
            self.error_occurred.emit("프로젝트 열기 실패", f"프로젝트 파일을 불러오는 중 오류가 발생했습니다: {e}")

    @Slot()
    def save_project(self) -> bool:
        """현재 프로젝트를 저장합니다. 파일 경로가 없으면 '다른 이름으로 저장'을 호출합니다."""
        if not self.current_project.file_path:
            return self.save_project_as()
        
        try:
            project_data = self.current_project.to_dict()
            with open(self.current_project.file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=4, ensure_ascii=False)
            
            self.current_project.is_dirty = False
            self.status_updated.emit(f"프로젝트가 '{self.current_project.file_path}'에 저장되었습니다.")
            return True

        except Exception as e:
            self.error_occurred.emit("프로젝트 저장 실패", f"프로젝트를 저장하는 중 오류가 발생했습니다: {e}")
            return False

    @Slot()
    def save_project_as(self) -> bool:
        """'다른 이름으로 저장' 대화상자를 열어 프로젝트를 저장합니다."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent(), "프로젝트 다른 이름으로 저장", "", "DOE Project Files (*.doeproj);;All Files (*)"
        )

        if not file_path:
            return False

        self.current_project.file_path = file_path
        self.current_project.name = Path(file_path).stem
        return self.save_project()

    def _confirm_discard_changes(self) -> bool:
        """저장되지 않은 변경 사항이 있을 경우 사용자에게 확인을 요청합니다."""
        msg_box = QMessageBox(self.parent())
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText("저장되지 않은 변경사항이 있습니다.")
        msg_box.setInformativeText("변경사항을 저장하지 않고 계속하시겠습니까?")
        msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Save)
        
        ret = msg_box.exec()

        if ret == QMessageBox.Save:
            return self.save_project()
        elif ret == QMessageBox.Discard:
            return True
        else:
            return False

    def close_project(self) -> bool:
        """애플리케이션 종료 시 프로젝트를 닫습니다."""
        if self.current_project and self.current_project.is_dirty:
            if not self._confirm_discard_changes():
                return False
        self.project_closed.emit()
        return True 