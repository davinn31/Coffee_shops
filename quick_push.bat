@echo off
echo ========================================
echo   GitHub Quick Push Fix
echo ========================================
echo.

REM Check if git is initialized
if not exist ".git" (
    echo ERROR: Git not initialized in this folder!
    echo Please run setup_git.bat first
    pause
    exit /b
)

REM Check current branch
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i

REM Rename master to main if needed
if "%BRANCH%"=="master" (
    echo Renaming branch from master to main...
    git branch -M main
    set BRANCH=main
)

echo Current branch: %BRANCH%

REM Check if there are any commits
git rev-parse HEAD >nul 2>&1
if errorlevel 1 (
    echo No commits yet! Creating first commit...
    git add .
    git commit -m "First commit"
)

echo.
echo Adding files...
git add .
echo.

echo Enter commit message:
set /p msg="> "

if "%msg%"=="" set msg="Update"

git commit -m "%msg%"
echo.

echo Pushing to GitHub...
git pull origin %BRANCH% --allow-unrelated-histories
git push origin %BRANCH%
echo.

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Push failed!
    echo.
    echo Make sure you have run:
    echo   git remote add origin https://github.com/davinn31/Coffee_shops.git
    echo ========================================
) else (
    echo ========================================
    echo   SUCCESS! Files pushed to GitHub
    echo ========================================
)

pause

