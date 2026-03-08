@echo off
REM Run all CI checks locally before pushing
REM This script mimics what runs in GitHub Actions

setlocal enabledelayedexpansion

echo.
echo 🚀 Running CI checks locally...
echo.

set OVERALL_STATUS=0

REM 1. Check code formatting with Black
echo 📝 Checking code formatting with Black...
black --check --diff wayfare\ nanobot\ tests\
if %ERRORLEVEL% EQU 0 (
    echo ✓ Black formatting passed
) else (
    echo ✗ Black formatting failed
    echo 💡 Run 'black wayfare\ nanobot\ tests\' to fix
    set OVERALL_STATUS=1
)
echo.

REM 2. Run Ruff linter
echo 🔍 Running Ruff linter...
ruff check wayfare\ nanobot\ tests\
if %ERRORLEVEL% EQU 0 (
    echo ✓ Ruff linting passed
) else (
    echo ✗ Ruff linting failed
    echo 💡 Run 'ruff check --fix wayfare\ nanobot\ tests\' to fix
    set OVERALL_STATUS=1
)
echo.

REM 3. Run type checking with mypy (non-blocking)
echo 🔎 Running type checking with mypy...
mypy wayfare\ --ignore-missing-imports --no-strict-optional
if %ERRORLEVEL% EQU 0 (
    echo ✓ mypy type checking passed
) else (
    echo ⚠ mypy found issues (non-blocking)
)
echo.

REM 4. Run Pylint (non-blocking)
echo 🔬 Running Pylint...
pylint wayfare\ --disable=C0111,R0903,W0212,C0103 --max-line-length=100
if %ERRORLEVEL% EQU 0 (
    echo ✓ Pylint passed
) else (
    echo ⚠ Pylint found issues (non-blocking)
)
echo.

REM 5. Run unit tests
echo 🧪 Running unit tests...
pytest tests\ -v --tb=short --ignore=tests\wayfare\test_serialization_roundtrip.py
if %ERRORLEVEL% EQU 0 (
    echo ✓ Unit tests passed
) else (
    echo ✗ Unit tests failed
    set OVERALL_STATUS=1
)
echo.

REM 6. Run property-based tests
echo 🎲 Running property-based tests...
pytest tests\wayfare\test_serialization_roundtrip.py -v --tb=short
if %ERRORLEVEL% EQU 0 (
    echo ✓ Property-based tests passed
) else (
    echo ✗ Property-based tests failed
    set OVERALL_STATUS=1
)
echo.

REM 7. Check if Qdrant is running for integration tests
echo 🔌 Checking Qdrant connection...
curl -f http://localhost:6333/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✓ Qdrant is running
    
    REM Run integration tests
    echo 🔗 Running integration tests...
    set QDRANT_URL=http://localhost:6333
    pytest tests\wayfare\ -v --tb=short -k "integration"
    if !ERRORLEVEL! EQU 0 (
        echo ✓ Integration tests passed
    ) else (
        echo ✗ Integration tests failed
        set OVERALL_STATUS=1
    )
) else (
    echo ⚠ Qdrant is not running, skipping integration tests
    echo 💡 Start Qdrant: docker run -p 6333:6333 qdrant/qdrant:latest
)
echo.

REM 8. Generate coverage report (optional)
echo 📊 Generating coverage report...
pytest tests\ --cov=wayfare --cov=nanobot --cov-report=term --cov-report=html
if %ERRORLEVEL% EQU 0 (
    echo ✓ Coverage report generated
    echo 📈 Coverage report available in htmlcov\index.html
) else (
    echo ⚠ Coverage report generation failed (non-blocking)
)
echo.

REM Final status
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if %OVERALL_STATUS% EQU 0 (
    echo ✓ All CI checks passed! Ready to push.
    exit /b 0
) else (
    echo ✗ Some CI checks failed. Please fix before pushing.
    exit /b 1
)
