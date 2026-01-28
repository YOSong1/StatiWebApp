"""
폰트 관리 유틸리티
matplotlib 한글 폰트 설정 및 관리
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
import platform
import os

class FontManager:
    """폰트 관리 클래스"""
    
    def __init__(self):
        self.available_fonts = self.get_available_korean_fonts()
        self.current_font = None
        self.setup_default_font()
    
    def get_available_korean_fonts(self):
        """사용 가능한 한글 폰트 목록 반환"""
        korean_fonts = []
        
        # 시스템별 기본 한글 폰트
        system_fonts = {
            'Windows': [
                'Malgun Gothic', '맑은 고딕',
                'Batang', '바탕',
                'Dotum', '돋움',
                'Gulim', '굴림',
                'Gungsuh', '궁서',
                'NanumGothic', '나눔고딕',
                'NanumBarunGothic', '나눔바른고딕'
            ],
            'Darwin': [  # macOS
                'AppleGothic', 'Apple SD Gothic Neo',
                'NanumGothic', 'NanumBarunGothic'
            ],
            'Linux': [
                'NanumGothic', 'NanumBarunGothic',
                'UnDotum', 'UnBatang'
            ]
        }
        
        current_system = platform.system()
        candidate_fonts = system_fonts.get(current_system, [])
        
        # 설치된 폰트 중에서 한글 폰트 찾기
        installed_fonts = [f.name for f in fm.fontManager.ttflist]
        
        for font in candidate_fonts:
            if font in installed_fonts:
                korean_fonts.append(font)
        
        # 기본 폰트도 추가
        korean_fonts.extend(['DejaVu Sans', 'Arial', 'sans-serif'])
        
        return korean_fonts
    
    def setup_default_font(self):
        """기본 한글 폰트 설정"""
        if self.available_fonts:
            self.set_font(self.available_fonts[0])
        else:
            # 폰트가 없으면 기본 설정
            plt.rcParams['font.family'] = ['sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
    
    def set_font(self, font_name):
        """지정된 폰트로 설정"""
        try:
            plt.rcParams['font.family'] = [font_name, 'DejaVu Sans', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            self.current_font = font_name
            
            # 폰트 캐시 새로고침
            plt.rcParams['font.size'] = plt.rcParams['font.size']
            
            return True
        except Exception as e:
            print(f"폰트 설정 실패: {e}")
            return False
    
    def get_font_list(self):
        """사용 가능한 폰트 목록 반환"""
        return self.available_fonts.copy()
    
    def get_current_font(self):
        """현재 설정된 폰트 반환"""
        return self.current_font
    
    def test_font(self, font_name):
        """폰트 테스트"""
        try:
            # 임시로 폰트 설정해보기
            original_font = plt.rcParams['font.family'].copy()
            plt.rcParams['font.family'] = [font_name]
            
            # 간단한 텍스트 렌더링 테스트
            fig, ax = plt.subplots(figsize=(1, 1))
            ax.text(0.5, 0.5, '한글테스트', fontsize=12)
            plt.close(fig)
            
            # 원래 폰트로 복원
            plt.rcParams['font.family'] = original_font
            return True
            
        except Exception:
            return False

# 전역 폰트 매니저 인스턴스
font_manager = FontManager()

def get_font_manager():
    """폰트 매니저 인스턴스 반환"""
    return font_manager

def set_korean_font(font_name=None):
    """한글 폰트 설정 (편의 함수)"""
    if font_name:
        return font_manager.set_font(font_name)
    else:
        font_manager.setup_default_font()
        return True 