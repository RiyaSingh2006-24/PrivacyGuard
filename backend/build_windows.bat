@echo off
setlocal

title PrivacyGuard Windows Builder

echo.
echo ================================================
echo        PrivacyGuard Windows Build
echo ================================================
echo.

set BACKEND=%~dp0
set FRONTEND=%BACKEND%..\frontend

where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set PYTHON=py -3
) else (
    set PYTHON=python
)

echo [1/8] Checking Python...
%PYTHON% --version
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo Install Python and enable "Add Python to PATH".
    pause
    exit /b 1
)

echo.
echo [2/8] Checking Node.js...
where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed.
    echo Install Node.js LTS before building PrivacyGuard.
    pause
    exit /b 1
)
node --version
npm --version

echo.
echo [3/8] Preparing Python environment...
cd /d "%BACKEND%"
if not exist venv (
    %PYTHON% -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Python dependencies failed.
    pause
    exit /b 1
)

echo.
echo [4/8] Preparing frontend...
cd /d "%FRONTEND%"
if exist package-lock.json (
    call npm ci
) else (
    call npm install
)
if errorlevel 1 (
    echo ERROR: Frontend dependencies failed.
    pause
    exit /b 1
)

echo.
echo [5/8] Building React frontend...
call npm run build
if errorlevel 1 (
    echo ERROR: React production build failed.
    pause
    exit /b 1
)

echo.
echo [6/8] Preparing packaged frontend...
cd /d "%BACKEND%"
if exist web (
    rmdir /s /q web
)
mkdir web
xcopy "%FRONTEND%\dist\*" "%BACKEND%\web\" /E /I /Y >nul

echo.
echo [7/8] Cleaning previous build...
if exist build (
    rmdir /s /q build
)
if exist dist (
    rmdir /s /q dist
)
if exist PrivacyGuard.spec (
    del /q PrivacyGuard.spec
)

echo.
echo [8/8] Building PrivacyGuard.exe...
python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --name PrivacyGuard ^
    --add-data "web;web" ^
    --collect-all reportlab ^
    start_backend.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo BUILD FAILED
    echo ================================================
    pause
    exit /b 1
)

echo.
echo ================================================
echo       PRIVACYGUARD BUILD SUCCESSFUL
echo ================================================
echo.
echo Application:
echo %BACKEND%dist\PrivacyGuard\PrivacyGuard.exe
echo.
echo IMPORTANT:
echo Distribute the entire PrivacyGuard folder,
echo not only PrivacyGuard.exe.
echo.
echo ================================================
echo.
pause
