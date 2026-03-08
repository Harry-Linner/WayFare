@echo off
REM WayFare MVP Backend - Development Environment Setup Script (Windows)
REM This script automates the setup of the development environment

setlocal enabledelayedexpansion

REM Configuration
set VENV_DIR=venv
set MODELS_DIR=wayfare\models
set ONNX_MODEL_NAME=bge-small-zh-v1.5.onnx
set ONNX_MODEL_URL=https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/main/onnx/model.onnx
set QDRANT_PORT=6333
set QDRANT_CONTAINER_NAME=wayfare-qdrant

echo ========================================
echo WayFare MVP Backend Setup
echo ========================================
echo.

REM Check if Python is installed
echo [*] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python is not installed or not in PATH.
    echo [X] Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [+] Python %PYTHON_VERSION% found

REM Check if Docker is installed
echo [*] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [!] Docker is not installed. Qdrant container will not be started.
    echo [!] Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    echo [!] After installing Docker, run: docker run -p 6333:6333 qdrant/qdrant
    set DOCKER_AVAILABLE=false
) else (
    echo [+] Docker found
    set DOCKER_AVAILABLE=true
)

REM Step 1: Create virtual environment
echo [*] Creating virtual environment...
if exist "%VENV_DIR%" (
    echo [!] Virtual environment already exists. Skipping creation.
) else (
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [X] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [+] Virtual environment created at %VENV_DIR%
)

REM Step 2: Activate virtual environment and install dependencies
echo [*] Installing dependencies...
call %VENV_DIR%\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip >nul 2>&1

REM Install dependencies
if exist "requirements-dev.txt" (
    pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo [X] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [+] Dependencies installed from requirements-dev.txt
) else (
    echo [X] requirements-dev.txt not found!
    pause
    exit /b 1
)

REM Step 3: Create models directory
echo [*] Setting up models directory...
if not exist "%MODELS_DIR%" (
    mkdir "%MODELS_DIR%"
    echo [+] Created directory: %MODELS_DIR%
) else (
    echo [+] Models directory already exists
)

REM Step 4: Download ONNX model
echo [*] Downloading ONNX model...
set ONNX_MODEL_PATH=%MODELS_DIR%\%ONNX_MODEL_NAME%

if exist "%ONNX_MODEL_PATH%" (
    echo [!] ONNX model already exists at %ONNX_MODEL_PATH%. Skipping download.
) else (
    echo [*] Downloading BAAI/bge-small-zh-v1.5 ONNX model (~100MB)...
    echo [*] This may take a few minutes depending on your internet connection...
    
    REM Try using curl (available in Windows 10+)
    curl --version >nul 2>&1
    if errorlevel 1 (
        echo [!] curl not found. Trying PowerShell download...
        powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%ONNX_MODEL_URL%' -OutFile '%ONNX_MODEL_PATH%' -UseBasicParsing}"
    ) else (
        curl -L "%ONNX_MODEL_URL%" -o "%ONNX_MODEL_PATH%" --progress-bar
    )
    
    if exist "%ONNX_MODEL_PATH%" (
        echo [+] ONNX model downloaded successfully
    ) else (
        echo [X] Failed to download ONNX model
        echo [!] You can manually download the model from:
        echo [!] %ONNX_MODEL_URL%
        echo [!] And save it to: %ONNX_MODEL_PATH%
        pause
        exit /b 1
    )
)

REM Step 5: Start Qdrant Docker container
if "%DOCKER_AVAILABLE%"=="true" (
    echo [*] Starting Qdrant Docker container...
    
    REM Check if container already exists
    docker ps -a --format "{{.Names}}" | findstr /x "%QDRANT_CONTAINER_NAME%" >nul 2>&1
    if errorlevel 1 (
        REM Container doesn't exist, create and start it
        echo [*] Creating and starting Qdrant container...
        
        REM Create storage directory if it doesn't exist
        if not exist ".wayfare\qdrant_storage" mkdir ".wayfare\qdrant_storage"
        
        docker run -d --name %QDRANT_CONTAINER_NAME% -p %QDRANT_PORT%:6333 -v "%CD%\.wayfare\qdrant_storage:/qdrant/storage" qdrant/qdrant
        if errorlevel 1 (
            echo [X] Failed to start Qdrant container
            pause
            exit /b 1
        )
        echo [+] Qdrant container started on port %QDRANT_PORT%
    ) else (
        REM Container exists, check if it's running
        docker ps --format "{{.Names}}" | findstr /x "%QDRANT_CONTAINER_NAME%" >nul 2>&1
        if errorlevel 1 (
            REM Container exists but not running, start it
            echo [*] Starting existing Qdrant container...
            docker start %QDRANT_CONTAINER_NAME%
            echo [+] Qdrant container started
        ) else (
            echo [!] Qdrant container is already running
        )
    )
    
    REM Wait for Qdrant to be ready
    echo [*] Waiting for Qdrant to be ready...
    timeout /t 3 /nobreak >nul
    
    REM Check if Qdrant is responding
    curl -s http://localhost:%QDRANT_PORT%/health >nul 2>&1
    if errorlevel 1 (
        echo [!] Qdrant container started but not responding yet. It may need more time to initialize.
    ) else (
        echo [+] Qdrant is ready and responding
    )
) else (
    echo [!] Skipping Qdrant container setup (Docker not available)
)

REM Step 6: Verify installation
echo [*] Verifying installation...

if exist "verify_dependencies.py" (
    python verify_dependencies.py
    if errorlevel 1 (
        echo [!] Some dependencies may be missing. Check the output above.
    ) else (
        echo [+] All dependencies verified
    )
) else (
    echo [!] verify_dependencies.py not found. Skipping verification.
)

REM Final summary
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Activate the virtual environment:
echo      %VENV_DIR%\Scripts\activate.bat
echo.
echo   2. Set your API key (if using LLM features):
echo      set OPENAI_API_KEY=your-api-key-here
echo.
echo   3. Run tests:
echo      pytest tests\
echo.
echo   4. Start the backend:
echo      python wayfare\main.py
echo.

if "%DOCKER_AVAILABLE%"=="true" (
    echo Qdrant Management:
    echo   Stop Qdrant:  docker stop %QDRANT_CONTAINER_NAME%
    echo   Start Qdrant: docker start %QDRANT_CONTAINER_NAME%
    echo   View logs:    docker logs %QDRANT_CONTAINER_NAME%
    echo.
)

echo Happy coding! 🚀
echo.
pause
