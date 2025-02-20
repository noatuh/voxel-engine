@echo off

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b
)

:: Upgrade pip
python -m pip install --upgrade pip

:: Install necessary Python libraries
pip install pygame ursina

:: Confirm installation
echo Dependencies installed successfully!
pause
