# 📋 DOE Tool 배포 가이드 (.exe 생성)

이 문서는 Python으로 개발된 DOE Tool 애플리케이션을 Windows용 실행 파일(`.exe`)로 빌드하고 배포하는 방법을 안내합니다. **PyInstaller** 도구를 사용하여, 사용자가 파이썬이나 별도 라이브러리 설치 없이 프로그램을 즉시 실행할 수 있도록 만듭니다.

---

## 🎯 **배포 목표**
1.  **단일 실행 파일**: 모든 종속성과 리소스를 포함하는 하나의 `.exe` 파일을 생성합니다.
2.  **간편한 실행**: 사용자는 `.exe` 파일을 더블클릭하는 것만으로 프로그램을 실행할 수 있습니다.
3.  **콘솔 창 숨기기**: GUI 애플리케이션이므로, 실행 시 불필요한 검은색 콘솔 창이 나타나지 않도록 합니다.

---

## 🛠️ **빌드 환경 준비 (최초 1회)**

### **1. 의존성 라이브러리 설치**
프로젝트에 필요한 모든 라이브러리를 설치합니다. `requirements.txt` 파일이 이미 있으므로, 다음 명령어로 한 번에 설치할 수 있습니다.

터미널을 열고 `DeskTopApp` 디렉터리로 이동한 후, 아래 명령어를 실행하세요.
```bash
# DeskTopApp 폴더로 이동
cd DeskTopApp

# requirements.txt에 명시된 모든 라이브러리 설치
pip install -r requirements.txt
```

### **2. PyInstaller 설치**
`.exe` 파일을 생성하는 핵심 도구인 `pyinstaller`를 설치합니다.
```bash
pip install pyinstaller
```

---

## 🚀 **.EXE 파일 빌드하기**

환경 준비가 완료되었다면, 이제 다음 명령어로 `.exe` 파일을 빌드할 수 있습니다.

**중요:** 이 명령어는 반드시 `DeskTopApp` 디렉터리 안에서 실행해야 합니다.

```bash
pyinstaller --name DOETool_v2.0 --onefile --windowed --add-data "data;data" --add-data "resources;resources" src/main.py
```

### **명령어 옵션 상세 설명**
-   `pyinstaller`: PyInstaller를 실행합니다.
-   `--name DOETool_v2.0`: 생성될 `.exe` 파일의 이름을 `DOETool_v2.0.exe`로 지정합니다. 버전 정보를 포함하면 관리가 용이합니다.
-   `--onefile`: 모든 것을 하나의 실행 파일로 압축합니다. 이 옵션을 사용하지 않으면 여러 파일이 있는 폴더 형태로 생성됩니다.
-   `--windowed`: 프로그램 실행 시 뒤에 나타나는 검은색 명령 프롬프트(콘솔) 창을 숨깁니다. GUI 애플리케이션에 필수적인 옵션입니다.
-   `--add-data "data;data"`: `DeskTopApp/data` 폴더 안의 모든 파일(샘플 데이터 등)을 배포본에 포함시킵니다. 세미콜론 앞은 원본 경로, 뒤는 배포본에 포함될 경로입니다. `data` 폴더를 통째로 `data`라는 이름의 폴더로 복사하라는 의미입니다.
-   `--add-data "resources;resources"`: `DeskTopApp/resources` 폴더(아이콘, 이미지 등)를 배포본에 포함시킵니다.
-   `src/main.py`: 빌드할 메인 스크립트 파일의 경로입니다.

---

## ✅ **빌드 결과 확인 및 배포**

빌드가 성공적으로 완료되면 `DeskTopApp` 디렉터리 안에 두 개의 새로운 폴더가 생성됩니다.

1.  **`build` 폴더**: 빌드 과정에서 생성된 임시 파일들이 저장됩니다. 이 폴더는 무시해도 좋습니다.
2.  **`dist` 폴더**: **최종 결과물이 저장되는 가장 중요한 폴더입니다.**

`dist` 폴더 안에 있는 `DOETool_v2.0.exe` 파일을 사용자에게 전달하면 됩니다. 이 파일 하나만으로 모든 기능이 동작할 것입니다.

---

## 💡 **팁: 빌드 자동화 스크립트 만들기**

매번 긴 명령어를 입력하는 것은 번거롭습니다. `DeskTopApp` 폴더에 `build.bat`이라는 간단한 스크립트 파일을 만들어두면 더블클릭만으로 빌드를 자동화할 수 있습니다.

**1. `DeskTopApp` 폴더에 `build.bat` 파일 생성**

**2. 아래 내용 복사하여 붙여넣기**
```batch
@echo off
echo =================================
echo  DOE Tool .EXE 파일 빌드를 시작합니다.
echo =================================

pyinstaller --name DOETool_v2.0 --onefile --windowed --add-data "data;data" --add-data "resources;resources" src/main.py

echo.
echo =================================
echo  빌드가 완료되었습니다.
echo  dist 폴더에서 DOETool_v2.0.exe 파일을 확인하세요.
echo =================================
pause
```

이제부터는 코드를 수정한 뒤 `build.bat` 파일을 더블클릭하기만 하면 자동으로 새로운 `.exe` 파일이 `dist` 폴더에 생성됩니다. 