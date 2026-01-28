"""
ProjectController 단위 테스트
"""

import sys
import os
import unittest
import tempfile
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# src 경로를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from controllers.project_controller import ProjectController
from models.project import Project

class TestProjectController(unittest.TestCase):
    """ProjectController 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """클래스 레벨 설정 - QApplication 초기화"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """테스트 준비"""
        # QObject 부모 생성
        self.parent = QObject()
        self.controller = ProjectController(self.parent)
        
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_path = os.path.join(self.temp_dir, "test_project.json")
        
        # 테스트용 데이터프레임
        self.test_data = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10, 20, 30, 40, 50],
            'C': ['a', 'b', 'c', 'd', 'e']
        })
    
    def tearDown(self):
        """테스트 정리"""
        # 임시 파일들 정리
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_new_project(self):
        """새 프로젝트 생성 테스트"""
        # When
        self.controller.new_project()
        
        # Then
        project = self.controller.current_project
        self.assertIsInstance(project, Project)
        self.assertEqual(project.name, "새 프로젝트")
        self.assertTrue(project.dataframe.empty)
        self.assertEqual(len(project.analysis_history), 0)
        self.assertEqual(len(project.chart_history), 0)
        self.assertIsNotNone(project.created_at)
        self.assertFalse(project.is_dirty)  # 새 프로젝트는 dirty가 아님
    
    def test_current_project_property(self):
        """현재 프로젝트 속성 테스트"""
        # Given - setUp에서 이미 new_project()가 호출됨
        self.assertIsNotNone(self.controller.current_project)
        
        # When
        old_project_id = id(self.controller.current_project)
        self.controller.new_project()
        
        # Then
        self.assertIsNotNone(self.controller.current_project)
        self.assertNotEqual(id(self.controller.current_project), old_project_id)
    
    def test_save_project(self):
        """프로젝트 저장 테스트"""
        # Given
        project = self.controller.current_project
        project.name = "테스트 프로젝트"
        project.update_data(self.test_data, "테스트 데이터")
        project.file_path = self.test_project_path
        
        # When
        result = self.controller.save_project()
        
        # Then
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.test_project_path))
        self.assertFalse(project.is_dirty)
    
    def test_save_project_as(self):
        """다른 이름으로 프로젝트 저장 테스트"""
        # Given
        project = self.controller.current_project
        project.name = "테스트 프로젝트"
        project.update_data(self.test_data, "테스트 데이터")
        
        with patch('controllers.project_controller.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = (self.test_project_path, "DOE Project Files (*.doeproj)")
            
            # When
            result = self.controller.save_project_as()
            
            # Then
            self.assertTrue(result)
            self.assertTrue(os.path.exists(self.test_project_path))
            self.assertEqual(project.file_path, self.test_project_path)
            self.assertFalse(project.is_dirty)
    
    def test_open_project(self):
        """프로젝트 열기 테스트"""
        # Given - 먼저 프로젝트를 저장
        project = self.controller.current_project
        project.name = "테스트 프로젝트"
        project.update_data(self.test_data, "테스트 데이터")
        project.file_path = self.test_project_path
        self.controller.save_project()
        
        # 새로운 컨트롤러로 열기 테스트
        new_controller = ProjectController()
        
        with patch('controllers.project_controller.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (self.test_project_path, "DOE Project Files (*.doeproj)")
            
            # When
            new_controller.open_project()
            
            # Then
            self.assertIsNotNone(new_controller.current_project)
            self.assertEqual(new_controller.current_project.name, "테스트 프로젝트")
            self.assertEqual(len(new_controller.current_project.dataframe), 5)
    
    def test_close_project_with_unsaved_changes(self):
        """저장되지 않은 변경사항이 있는 프로젝트 닫기 테스트"""
        # Given
        project = self.controller.current_project
        project.is_dirty = True
        
        # QMessageBox를 완전히 모킹하여 안전하게 테스트
        with patch('controllers.project_controller.QMessageBox') as mock_msgbox_class:
            # QMessageBox 상수들을 모킹
            mock_msgbox_class.Save = 0x00000800
            mock_msgbox_class.Discard = 0x00800000
            mock_msgbox_class.Cancel = 0x00400000
            mock_msgbox_class.Yes = 0x00004000
            mock_msgbox_class.No = 0x00010000
            mock_msgbox_class.Question = 0x00000004
            
            # QMessageBox 인스턴스 모킹
            mock_msgbox_instance = Mock()
            mock_msgbox_instance.exec.return_value = mock_msgbox_class.Save
            mock_msgbox_class.return_value = mock_msgbox_instance
            
            with patch.object(self.controller, 'save_project') as mock_save:
                mock_save.return_value = True
                
                # When
                result = self.controller.close_project()
                
                # Then
                self.assertTrue(result)
                mock_save.assert_called_once()
    
    def test_close_project_discard_changes(self):
        """변경사항 무시하고 프로젝트 닫기 테스트"""
        # Given
        project = self.controller.current_project
        project.is_dirty = True
        
        with patch('controllers.project_controller.QMessageBox') as mock_msgbox_class:
            # QMessageBox 상수들을 모킹
            mock_msgbox_class.Save = 0x00000800
            mock_msgbox_class.Discard = 0x00800000
            mock_msgbox_class.Cancel = 0x00400000
            mock_msgbox_class.Yes = 0x00004000
            mock_msgbox_class.No = 0x00010000
            mock_msgbox_class.Question = 0x00000004
            
            # QMessageBox 인스턴스 모킹
            mock_msgbox_instance = Mock()
            mock_msgbox_instance.exec.return_value = mock_msgbox_class.Discard
            mock_msgbox_class.return_value = mock_msgbox_instance
            
            # When
            result = self.controller.close_project()
            
            # Then
            self.assertTrue(result)
            # 프로젝트는 여전히 존재하지만 닫기는 성공
    
    def test_signals_emitted(self):
        """시그널 발생 테스트"""
        # Given
        project_loaded_signal = Mock()
        status_updated_signal = Mock()
        self.controller.project_loaded.connect(project_loaded_signal)
        self.controller.status_updated.connect(status_updated_signal)
        
        # When
        self.controller.new_project()
        
        # Then
        project_loaded_signal.assert_called_once()
        status_updated_signal.assert_called()
    
    def test_load_project_from_file(self):
        """파일에서 프로젝트 로드 테스트"""
        # Given - 프로젝트 데이터를 올바른 형식으로 생성
        project_data = {
            "project_info": {
                "name": "테스트 프로젝트",
                "created_at": "2024-01-01T12:00:00"
            },
            "data": {
                "dataframe": self.test_data.to_dict('records'),
                "columns": self.test_data.columns.tolist(),
                "description": "테스트 데이터"
            },
            "analysis_history": [],
            "chart_history": [],
            "settings": {}
        }
        
        import json
        with open(self.test_project_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        # When - open_project 메서드를 사용
        with patch('controllers.project_controller.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (self.test_project_path, "DOE Project Files (*.doeproj)")
            self.controller.open_project()
        
        # Then
        self.assertIsNotNone(self.controller.current_project)
        self.assertEqual(self.controller.current_project.name, "테스트 프로젝트")
        self.assertEqual(len(self.controller.current_project.dataframe), 5)
    
    def test_invalid_project_file(self):
        """유효하지 않은 프로젝트 파일 테스트"""
        # Given - 잘못된 JSON 파일
        with open(self.test_project_path, 'w') as f:
            f.write("invalid json content")
        
        error_signal = Mock()
        self.controller.error_occurred.connect(error_signal)
        
        # When
        with patch('controllers.project_controller.QFileDialog.getOpenFileName') as mock_dialog:
            mock_dialog.return_value = (self.test_project_path, "DOE Project Files (*.doeproj)")
            self.controller.open_project()
            
        # Then
        error_signal.assert_called_once()


if __name__ == '__main__':
    unittest.main() 