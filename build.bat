@echo off
chcp 65001 > nul
echo =================================
echo  DOE Tool .EXE 파일 빌드를 시작합니다.
echo  (프로젝트 가상환경 .venv 사용)
echo =================================

rem --- 배치 파일의 위치를 기준으로 .venv 경로를 설정 (안정성 향상) ---
set "PYINSTALLER_EXE=%~dp0\..\.venv\Scripts\pyinstaller.exe"

rem --- PyInstaller 실행 ---
"%PYINSTALLER_EXE%" --name DOETool_v2.0 --onefile --windowed --add-data "data;data" --add-data "resources;resources" src/main.py

rem --- 오류 확인 ---
if %errorlevel% neq 0 (
    echo.
    echo !!!!!!!!!!!!!!!!   오류   !!!!!!!!!!!!!!!!
    echo.
    echo  PyInstaller 빌드 중 오류가 발생했습니다.
    echo  위쪽의 오류 메시지를 확인해 주세요.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    goto end
)

echo.
echo =================================
echo  빌드가 성공적으로 완료되었습니다.
echo  dist 폴더에서 DOETool_v2.0.exe 파일을 확인하세요.
echo =================================

:end
pause 