@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ╔════════════════════════════════════════════════════════════╗
echo ║     🚀 Push Creality Farm Manager to GitHub 🚀           ║
echo ║                                                            ║
echo ║     Repository: github.com/akali997/Creality_Farm         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [❌ ERROR] Git is not installed!
    echo.
    echo Please download and install Git from:
    echo https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

echo [✓] Git is installed
echo.

REM Check Git configuration
echo [Step 1/6] Checking Git configuration...
git config --global user.name >nul 2>&1
if errorlevel 1 (
    echo [!] Git user.name is not configured
    echo Setting up with your information...
    git config --global user.name "akali997"
    echo [✓] Set user.name to: akali997
) else (
    for /f "delims=" %%i in ('git config --global user.name') do set CURRENT_NAME=%%i
    echo [✓] Git user.name: !CURRENT_NAME!
)

git config --global user.email >nul 2>&1
if errorlevel 1 (
    echo [!] Git user.email is not configured
    echo Setting up with your email...
    git config --global user.email "chinhpcs@gmail.com"
    echo [✓] Set user.email to: chinhpcs@gmail.com
) else (
    for /f "delims=" %%i in ('git config --global user.email') do set CURRENT_EMAIL=%%i
    echo [✓] Git user.email: !CURRENT_EMAIL!
)
echo.

REM Check if already initialized
if exist ".git" (
    echo [Step 2/6] Git repository already exists
    echo.
    set /p REINIT="🔄 Do you want to reinitialize? This will reset Git history (y/n): "
    if /i "!REINIT!"=="y" (
        echo Removing existing .git folder...
        rmdir /s /q .git
        goto :init
    ) else (
        echo Keeping existing repository...
        goto :check_remote
    )
)

:init
echo [Step 2/6] Initializing Git repository...
git init
if errorlevel 1 (
    echo [❌ ERROR] Failed to initialize Git repository
    pause
    exit /b 1
)
echo [✓] Repository initialized
echo.

echo [Step 3/6] Adding all files to Git...
git add .
if errorlevel 1 (
    echo [❌ ERROR] Failed to add files
    pause
    exit /b 1
)
echo [✓] Files added
echo.

echo [Step 4/6] Creating initial commit...
git commit -m "Initial commit: Creality Farm Manager v1.0.0"
if errorlevel 1 (
    echo [!] Commit might already exist or no changes to commit
    echo Continuing...
)
echo [✓] Commit created
echo.

:check_remote
echo [Step 5/6] Setting up GitHub remote...

REM Check if remote already exists
git remote | findstr "origin" >nul
if not errorlevel 1 (
    echo [!] Remote 'origin' already exists
    for /f "delims=" %%i in ('git remote get-url origin') do set EXISTING_URL=%%i
    echo Current remote: !EXISTING_URL!
    echo.
    set /p CHANGE_REMOTE="🔄 Do you want to change it to github.com/akali997/Creality_Farm.git? (y/n): "
    if /i "!CHANGE_REMOTE!"=="y" (
        git remote remove origin
        git remote add origin https://github.com/akali997/Creality_Farm.git
        echo [✓] Remote updated
    )
) else (
    git remote add origin https://github.com/akali997/Creality_Farm.git
    if errorlevel 1 (
        echo [❌ ERROR] Failed to add remote
        pause
        exit /b 1
    )
    echo [✓] Remote added: https://github.com/akali997/Creality_Farm.git
)
echo.

echo [Step 6/6] Preparing to push...
git branch -M main
echo [✓] Branch set to 'main'
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║                   📤 Ready to Push!                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ⚠️  IMPORTANT NOTES:
echo.
echo 1. Make sure you have created the repository on GitHub:
echo    https://github.com/akali997/Creality_Farm
echo.
echo 2. The repository should be EMPTY (no README, no .gitignore, no license)
echo.
echo 3. When prompted for credentials:
echo    - Username: akali997
echo    - Password: Use a Personal Access Token (NOT your GitHub password)
echo.
echo    📝 To create a Personal Access Token:
echo    1. Go to: https://github.com/settings/tokens
echo    2. Click "Generate new token" ^> "Generate new token (classic)"
echo    3. Give it a name (e.g., "Creality Farm")
echo    4. Check "repo" scope
echo    5. Click "Generate token"
echo    6. Copy the token and paste it as password
echo.
set /p DO_PUSH="✨ Ready to push to GitHub? (y/n): "

if /i "!DO_PUSH!"=="y" (
    echo.
    echo 📤 Pushing to GitHub...
    echo Please enter your credentials when prompted...
    echo.
    git push -u origin main
    if errorlevel 1 (
        echo.
        echo ╔════════════════════════════════════════════════════════════╗
        echo ║                   ❌ Push Failed                           ║
        echo ╚════════════════════════════════════════════════════════════╝
        echo.
        echo Common issues and solutions:
        echo.
        echo 1️⃣  Authentication Failed
        echo    - Make sure you're using a Personal Access Token, not password
        echo    - Create token at: https://github.com/settings/tokens
        echo.
        echo 2️⃣  Repository doesn't exist
        echo    - Create it at: https://github.com/new
        echo    - Name: Creality_Farm
        echo    - Make it Public
        echo    - DON'T add README, .gitignore, or license
        echo.
        echo 3️⃣  Repository already has content
        echo    - If you want to overwrite: git push -f origin main
        echo    - ⚠️  WARNING: This will delete existing content!
        echo.
        echo To retry manually: git push -u origin main
        echo.
        pause
        exit /b 1
    )
    echo.
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║           🎉 SUCCESS! Your Project is on GitHub! 🎉        ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.
    echo 🌐 View your project at:
    echo    https://github.com/akali997/Creality_Farm
    echo.
    echo 📋 Next steps:
    echo    1. Go to your repository on GitHub
    echo    2. Add a description and topics (Settings)
    echo    3. Enable Discussions (Settings ^> Features)
    echo    4. Create your first release (Releases ^> Create new release)
    echo.
    echo 🎯 Quick links:
    echo    - Repository: https://github.com/akali997/Creality_Farm
    echo    - Settings: https://github.com/akali997/Creality_Farm/settings
    echo    - Releases: https://github.com/akali997/Creality_Farm/releases/new
    echo.
) else (
    echo.
    echo 📝 To push later manually, run:
    echo    git push -u origin main
    echo.
)

pause

