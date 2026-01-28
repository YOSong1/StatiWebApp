#!/usr/bin/env python3
"""
DOE Desktop Application
실험계획법(Design of Experiments) 데스크톱 애플리케이션

Author: Your Name
Version: 0.1.0
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QIcon

# 절대 import 사용
import views.main_window
from views.main_window import MainWindow


class DOEApplication(QApplication):
    """DOE 애플리케이션 메인 클래스"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # 애플리케이션 기본 설정
        self.setApplicationName("DOE Tool")
        self.setApplicationVersion("0.1.0")
        self.setOrganizationName("DOE Solutions")
        self.setOrganizationDomain("doe-solutions.com")
        
        # 고해상도 디스플레이 지원
        self.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        self.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 애플리케이션 아이콘 설정
        icon_path = current_dir / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 스타일 시트 적용
        self.apply_stylesheet()
        
        # 메인 윈도우 생성
        self.main_window = MainWindow()
        
    def apply_stylesheet(self):
        """애플리케이션 스타일 시트 적용"""
        style_path = current_dir / "resources" / "styles" / "main_style.qss"
        if style_path.exists():
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        else:
            # 기본 스타일 적용
            default_style = """
            QMainWindow {
                background-color: #f0f0f0;
            }
            
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 1px solid #d0d0d0;
                padding: 2px;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            
            QToolBar {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                spacing: 2px;
                padding: 2px;
            }
            
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                padding: 6px 12px;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background-color: #e8f4fd;
                border-color: #0078d4;
            }
            
            QPushButton:pressed {
                background-color: #d0e7f7;
            }
            
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: #ffffff;
                alternate-background-color: #f8f8f8;
            }
            
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 4px;
                font-weight: bold;
            }
            """
            self.setStyleSheet(default_style)
    
    def run(self):
        """애플리케이션 실행"""
        self.main_window.show()
        return self.exec()


def main():
    """메인 함수"""
    # 환경 변수 설정 (고해상도 디스플레이 지원)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    # 애플리케이션 생성 및 실행
    app = DOEApplication(sys.argv)
    
    try:
        exit_code = app.run()
        sys.exit(exit_code)
    except Exception as e:
        print(f"애플리케이션 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 